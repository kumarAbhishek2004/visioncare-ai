# 🫁 VisionCare AI: Explainable Radiology Assistant

An AI-assisted radiology workstation and clinical decision support system for frontal chest radiographs.

---

## 🌟 System Architecture

```
Frontal Chest X-ray
        │
        ▼
[ Module 1: Image Quality Assessment (IQA) ]
- Laplacian Sharpness, Exposure Clipping, Michelson Contrast
        │
        ▼
[ Module 2: Diagnostic Image Optimization ]
- Non-generative CLAHE (Clip Limit 2.0) & Radiologist Window/Level Presets (Lung, Bone, Mediastinum)
        │
        ├──────────────────────────────────────────┐
        ▼                                          ▼
[ Module 3: Pulmonary Region Extraction ]    [ Module 4: Multi-Label Disease Classifier ]
- MONAI Pretrained BasicUNet                 - DenseNet-121 (Trained on 25k Patient-Isolated NIH-14)
- Lung Mask, Overlay & Thoracic Envelope     - 14 Pathologies with Temperature Scaling Calibration
- Sanity Check: Area < 8% Flag for Review    - Youden's J-Statistic Optimal Operating Thresholds
        │                                          │
        └────────────────────┬─────────────────────┘
                             │
                             ▼
[ Module 5: Explainability & Clinical Decision Support (CDS) ]
- Grad-CAM++ Feature Attribution
- Otsu Bounding Box Extraction & 5-Zone Anatomical Localization
- Clinical Safety Gate: Low confidence triggers mandatory manual radiologist review
        │
        ▼
[ Module 6: Structured Clinical Assistant ]
- Gemini 2.5 Flash Structured JSON Reporting (`findings`, `impression`, `recommendation`, `disclaimer`)
        │
        ▼
[ Module 7: Professional Radiology Workstation & PDF ]
- Synced Dual Viewports, Independent Calibrated Probabilities, and Audit Trail (AI Decision Trace)
```

---

## 🚀 Repository Structure

```
visioncare-ai/
├── ml/
│   ├── quality/             # Module 1: OpenCV IQA Analyzer
│   ├── enhancement/         # Module 2: CLAHE & Window/Level Presets
│   ├── segmentation/        # Module 3: Pretrained BasicUNet Pulmonary Extractor
│   ├── classification/      # Module 4: DenseNet-121 Multi-Label Inference & Calibration
│   ├── explainability/      # Module 5: Grad-CAM++ & 5-Zone Anatomical Mapper
│   └── llm/                 # Module 6: Gemini 2.5 Flash Structured Reporting
├── backend/                 # FastAPI Production Service (Unified /analyze endpoint)
├── frontend/                # Next.js 14 + Tailwind + shadcn/ui Radiology Workstation
├── kaggle/                  # Standalone Jupyter Notebook for Cloud GPU Training
├── pretrained/              # Learned Calibration Parameters & Thresholds
└── requirements.txt
```

---

## 🛠️ Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Verify Core Engine
```bash
python -c "from ml.quality.iqa_analyzer import ImageQualityAnalyzer; print('Engine Ready!')"
```

---

## 📄 License & Disclaimer

**VisionCare AI** is an investigational decision-support research platform. It is not an FDA-cleared diagnostic device and is intended for assistive clinical research and educational review only.
