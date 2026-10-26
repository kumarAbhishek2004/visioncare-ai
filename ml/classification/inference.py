"""
========================================================================================
VisionCare AI: Module 4 — DenseNet-121 Inference, Calibration & Safety Triage
========================================================================================
Purpose: Multi-label disease classification across the 14 NIH thoracic pathologies.
         Applies post-hoc Temperature Scaling and Youden's J-statistic thresholds.
Critical ML Rule: Ingests ORIGINAL radiograph at 224x224 (preserves training distribution;
                  no covariate shift from artificial mask boundaries).
========================================================================================
"""

import os
import json
from typing import Dict, Any, List, Tuple, Union, Optional
import numpy as np
import cv2
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F

DISEASE_CLASSES = [
    "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass",
    "Nodule", "Pneumonia", "Pneumothorax", "Consolidation", "Edema",
    "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia"
]

NUM_CLASSES = len(DISEASE_CLASSES)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]


class DenseNet121Classifier(nn.Module):
    """
    DenseNet121 architecture for 14-disease multi-label classification.
    Uses torchvision if available, with resilient native PyTorch fallback.
    """
    def __init__(self, num_classes: int = NUM_CLASSES):
        super().__init__()
        try:
            import torchvision.models as models
            try:
                base = models.densenet121(weights=None)
            except AttributeError:
                base = models.densenet121(pretrained=False)
            in_features = base.classifier.in_features
            base.classifier = nn.Linear(in_features, num_classes)
            self.features = base.features
            self.classifier = base.classifier
        except ImportError:
            # Fallback native PyTorch feature extractor
            native = self._build_native_densenet(num_classes)
            self.features = native.features
            self.classifier = native.classifier

    def _build_native_densenet(self, num_classes: int) -> nn.Module:
        class _DenseLayer(nn.Module):
            def __init__(self, in_features: int, growth_rate: int):
                super().__init__()
                self.norm1 = nn.BatchNorm2d(in_features)
                self.relu1 = nn.ReLU(inplace=True)
                self.conv1 = nn.Conv2d(in_features, 4 * growth_rate, kernel_size=1, bias=False)
                self.norm2 = nn.BatchNorm2d(4 * growth_rate)
                self.relu2 = nn.ReLU(inplace=True)
                self.conv2 = nn.Conv2d(4 * growth_rate, growth_rate, kernel_size=3, padding=1, bias=False)

            def forward(self, x):
                out = self.conv1(self.relu1(self.norm1(x)))
                out = self.conv2(self.relu2(self.norm2(out)))
                return torch.cat([x, out], 1)

        class _DenseBlock(nn.Module):
            def __init__(self, num_layers: int, in_features: int, growth_rate: int):
                super().__init__()
                layers = [
                    _DenseLayer(in_features + i * growth_rate, growth_rate)
                    for i in range(num_layers)
                ]
                self.block = nn.Sequential(*layers)

            def forward(self, x):
                return self.block(x)

        class _Transition(nn.Module):
            def __init__(self, in_features: int, out_features: int):
                super().__init__()
                self.norm = nn.BatchNorm2d(in_features)
                self.relu = nn.ReLU(inplace=True)
                self.conv = nn.Conv2d(in_features, out_features, kernel_size=1, bias=False)
                self.pool = nn.AvgPool2d(kernel_size=2, stride=2)

            def forward(self, x):
                return self.pool(self.conv(self.relu(self.norm(x))))

        class NativeDenseNet121(nn.Module):
            def __init__(self, num_classes: int = 14):
                super().__init__()
                self.features = nn.Sequential()
                self.features.add_module("0", nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False))
                self.features.add_module("1", nn.BatchNorm2d(64))
                self.features.add_module("2", nn.ReLU(inplace=True))
                self.features.add_module("3", nn.MaxPool2d(kernel_size=3, stride=2, padding=1))

                num_features = 64
                growth_rate = 32
                block_config = (6, 12, 24, 16)

                for i, num_layers in enumerate(block_config):
                    block = _DenseBlock(num_layers=num_layers, in_features=num_features, growth_rate=growth_rate)
                    self.features.add_module(f"denseblock{i + 1}", block)
                    num_features += num_layers * growth_rate
                    if i != len(block_config) - 1:
                        trans = _Transition(in_features=num_features, out_features=num_features // 2)
                        self.features.add_module(f"transition{i + 1}", trans)
                        num_features = num_features // 2

                self.features.add_module("norm5", nn.BatchNorm2d(num_features))
                self.classifier = nn.Linear(num_features, num_classes)

            def forward(self, x):
                f = self.features(x)
                out = F.relu(f, inplace=True)
                out = F.adaptive_avg_pool2d(out, (1, 1))
                out = torch.flatten(out, 1)
                return self.classifier(out)

        return NativeDenseNet121(num_classes=num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        f = self.features(x)
        out = F.relu(f, inplace=True)
        out = F.adaptive_avg_pool2d(out, (1, 1))
        out = torch.flatten(out, 1)
        return self.classifier(out)


class DiseaseClassifier:
    """
    Clinical Inference Engine:
    - Loads fine-tuned DenseNet121 weights
    - Applies learned Temperature Scaling calibration
    - Applies Youden's J-statistic operating thresholds
    - Evaluates prediction reliability and triggers clinical safety triage
    """

    def __init__(
        self,
        weights_path: str = "./pretrained/densenet121_nih14_best.pth",
        temperature_path: str = "./pretrained/temperature_scaler.json",
        thresholds_path: str = "./pretrained/optimal_thresholds.json",
        device: Optional[str] = None
    ):
        self.device = torch.device(device if device else ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = DenseNet121Classifier(num_classes=NUM_CLASSES).to(self.device)
        self.has_weights = False

        if os.path.exists(weights_path):
            try:
                state_dict = torch.load(weights_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.has_weights = True
                print(f"[+] Loaded DenseNet121 weights from: {weights_path}")
            except Exception as e:
                print(f"[!] Warning: Could not load weights ({e}). Running in fallback mode.")

        self.model.eval()

        # Load temperature scaling parameters
        self.temperatures = {}
        if os.path.exists(temperature_path):
            with open(temperature_path, "r") as f:
                self.temperatures = json.load(f)

        # Load optimal thresholds
        self.thresholds = {}
        if os.path.exists(thresholds_path):
            with open(thresholds_path, "r") as f:
                self.thresholds = json.load(f)

    def preprocess(self, image: Union[np.ndarray, Image.Image]) -> torch.Tensor:
        """Resizes to 224x224 and applies ImageNet normalization."""
        if isinstance(image, Image.Image):
            image = np.array(image)
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

        resized = cv2.resize(image, (224, 224), interpolation=cv2.INTER_LINEAR)
        arr = resized.astype(np.float32) / 255.0

        tensor = torch.from_numpy(arr).permute(2, 0, 1).float()
        for c in range(3):
            tensor[c] = (tensor[c] - IMAGENET_MEAN[c]) / IMAGENET_STD[c]

        return tensor.unsqueeze(0).to(self.device)

    def predict(self, image: Union[np.ndarray, Image.Image]) -> Dict[str, Any]:
        """
        Executes multi-label inference with confidence calibration and safety triage.
        """
        tensor = self.preprocess(image)

        with torch.no_grad():
            raw_logits = self.model(tensor).squeeze(0).cpu()

        # 1. Apply Temperature Scaling calibration
        scaled_logits = torch.zeros_like(raw_logits)
        for i, disease in enumerate(DISEASE_CLASSES):
            t = self.temperatures.get(disease, 1.0)
            t = max(0.1, float(t))
            scaled_logits[i] = raw_logits[i] / t

        # Independent calibrated probabilities (Sigmoid, NOT Softmax)
        calibrated_probs = torch.sigmoid(scaled_logits).numpy()

        # 2. Thresholding and findings classification
        all_findings = []
        primary_findings = []
        associated_findings = []

        for i, disease in enumerate(DISEASE_CLASSES):
            prob = float(calibrated_probs[i])
            thresh = self.thresholds.get(disease, 0.50)
            is_detected = prob >= thresh

            finding_info = {
                "disease": disease,
                "probability": round(prob, 4),
                "probability_pct": round(prob * 100.0, 1),
                "threshold": round(thresh, 4),
                "is_detected": is_detected,
                "confidence_tier": "HIGH" if prob >= 0.70 else ("MODERATE" if prob >= 0.40 else "LOW")
            }
            all_findings.append(finding_info)

            if is_detected:
                primary_findings.append(finding_info)
            elif prob >= (thresh * 0.70):
                associated_findings.append(finding_info)

        # Sort by probability descending
        all_findings.sort(key=lambda x: x["probability"], reverse=True)
        primary_findings.sort(key=lambda x: x["probability"], reverse=True)
        associated_findings.sort(key=lambda x: x["probability"], reverse=True)

        # 3. Clinical Safety Layer & Reliability Gating
        max_prob = float(np.max(calibrated_probs))

        if primary_findings:
            if max_prob >= 0.70:
                reliability = "HIGH"
                safety_triage = "ASSISTED_REVIEW_READY"
                triage_message = "High-confidence findings detected. Preliminary decision support generated."
            else:
                reliability = "MODERATE"
                safety_triage = "ASSISTED_REVIEW_READY"
                triage_message = "Moderate-confidence findings detected. Clinical auscultation correlate advised."
        else:
            if max_prob < 0.25:
                reliability = "HIGH"
                safety_triage = "NO_ACUTE_PATHOLOGY"
                triage_message = "No acute cardiopulmonary findings detected within 14 target classes."
            else:
                reliability = "LOW"
                safety_triage = "MANUAL_REVIEW_MANDATORY"
                triage_message = "Diagnostic uncertainty high. Automated impression suppressed. Radiologist manual review mandatory."

        return {
            "all_predictions": all_findings,
            "primary_findings": primary_findings,
            "associated_findings": associated_findings,
            "prediction_reliability": reliability,
            "safety_triage": safety_triage,
            "triage_message": triage_message,
            "calibrated": bool(self.temperatures),
            "max_probability": round(max_prob, 4)
        }
