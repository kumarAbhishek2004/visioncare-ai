# 🫁 VisionCare AI (Work in Progress)

An Explainable AI-assisted radiology assistant and clinical decision support system for frontal chest radiographs.

> **Current Status:** Core ML engine, preprocessing modules, and cloud training pipelines are implemented and verified. Full-stack API and workstation interface are in active development.

---

## 📌 Implementation Progress

- [x] **System Architecture & Clinical Design**
  - Clinical decision support (CDS) workflow defined.
  - 14-disease multi-label classification structure using patient-isolated stratification.
- [x] **Phase 1: Kaggle Cloud Training Pipeline**
  - Standalone Jupyter Notebook: [`kaggle/visioncare_training.ipynb`](kaggle/visioncare_training.ipynb).
  - Multi-label transfer learning (DenseNet121) on 25k stratified NIH ChestX-ray14 subset.
  - Confidence calibration via Post-Hoc Temperature Scaling (minimizing ECE).
  - Optimal operational decision thresholds via Youden's J-statistic.
  - Localization benchmarking against 1,600 NIH radiologist bounding boxes (`BBox_List_2017.csv`).
- [x] **Phase 2: Local Core AI Engine**
  - **Module 1 (IQA):** `ml/quality/iqa_analyzer.py` — OpenCV-based Laplacian sharpness, exposure clipping, and Michelson contrast scoring.
  - **Module 2 (Image Optimization):** `ml/enhancement/clahe_processor.py` — Non-generative CLAHE and Window/Level presets (`LUNG`, `MEDIASTINUM`, `BONE`).
  - **Module 3 (Pulmonary Extraction):** `ml/segmentation/monai_unet.py` — Pulmonary parenchyma mask, thoracic bounding envelope, and frontal scan validation.
  - **Module 4 (Classification & Safety):** `ml/classification/inference.py` — DenseNet-121 inference, independent calibrated probabilities, and Clinical Safety Triage gating.
- [x] **Phase 3: Explainability Engine & LLM Synthesizer**
  - **Module 5A (Grad-CAM++):** `ml/explainability/gradcam_engine.py` — Activation-tensor hooks, $1024 \times 1024$ continuous heatmaps, Otsu bounding boxes with metric sizing ($cm$).
  - **Module 5B (Zone Mapper):** `ml/explainability/zone_mapper.py` — 5-zone anatomical localization (RUZ, RMZ, RLZ, LUZ, LLZ, Mediastinum) with spatial percentage attribution.
  - **Module 5C (Decision Trace):** `ml/explainability/decision_trace.py` — 7-step FDA SaMD auditable decision trace.
  - **Module 6 (Clinical Synthesizer):** `ml/llm/synthesizer.py` — Gemini 2.5 Flash structured reporting client with deterministic ACR clinical fallback.
- [ ] **Phase 4: Unified Backend API** *(In Progress)*
  - FastAPI orchestration endpoint (`POST /api/v1/studies/analyze`).
  - ReportLab clinical PDF export service.
- [ ] **Phase 5: Radiology Workstation Frontend** *(Upcoming)*
  - Next.js 14, Tailwind CSS, and shadcn/ui clinical workstation.
  - Synchronized dual-viewports with interactive heatmap opacity sliders.

---

## 📂 Current Repository Layout

```
x_ray/
├── ml/
│   ├── quality/             # Module 1: Image Quality Assessment (IQA)
│   ├── enhancement/         # Module 2: CLAHE & Window/Level Presets
│   ├── segmentation/        # Module 3: Pulmonary Region Extractor
│   └── classification/      # Module 4: DenseNet-121 Inference & Calibration
├── kaggle/
│   ├── visioncare_training.ipynb  # Notebook for Kaggle GPU training
│   └── README.md                  # Kaggle execution instructions
├── pretrained/              # Learned thresholds & temperature parameters
├── backend/                 # FastAPI service scaffolding
├── frontend/                # Workstation UI scaffolding
└── requirements.txt
```

---

## 🛠️ Testing the Current ML Engine

You can verify the currently implemented modules locally:

```bash
# Verify Module 1 (IQA)
python -c "from ml.quality.iqa_analyzer import ImageQualityAnalyzer; print('Module 1 (IQA): Ready')"

# Verify Module 2 (Enhancement)
python -c "from ml.enhancement.clahe_processor import ImageOptimizer; print('Module 2 (Optimization): Ready')"

# Verify Module 3 (Pulmonary Extractor)
python -c "from ml.segmentation.monai_unet import PulmonaryRegionExtractor; print('Module 3 (Segmentation): Ready')"

# Verify Module 4 (Classification Engine)
python -c "from ml.classification.inference import DiseaseClassifier; print('Module 4 (Classifier): Ready')"
```

---

## 📄 Note & Disclaimer

This is an investigational decision-support research project in active development. It is not an FDA-cleared medical device and is intended solely for research and educational purposes.
