# Kaggle Training & Calibration Guide for VisionCare AI

This directory contains two formats of the pipeline ready for Kaggle:
1. **`visioncare_training.ipynb`**: **Jupyter Notebook (Recommended)** — You can directly upload this file to Kaggle. It is organized into 10 structured Markdown + Code steps.
2. **`visioncare_kaggle_training.py`**: Standalone Python script.

---

## 1. 1-Click Upload to Kaggle

1. Go to [kaggle.com](https://www.kaggle.com) and click **"Create" $\to$ "New Notebook"** (or open [kaggle.com/datasets/nih-chest-xrays/data](https://www.kaggle.com/datasets/nih-chest-xrays/data) and click **"New Notebook"**).
2. If creating from scratch, in the right sidebar under **Data**, click **"+ Add Data"** and search for `nih-chest-xrays/data`.
3. In the notebook top menu, click **File $\to$ Import Notebook** and upload:
   ```
   x_ray/kaggle/visioncare_training.ipynb
   ```
4. In the right sidebar under **Notebook options**:
   - **Accelerator:** Select **GPU T4 x2** (or **GPU P100**).
   - **Internet:** Turn **ON** (needed to load ImageNet pretrained weights).
5. Click **"Run All"** (or run cell by cell).

---

## 2. What the Script Does Automatically

1. **Auto-Detects Paths:** Scans `/kaggle/input/data` or `/kaggle/input/nih-chest-xrays/data` across all 12 zipped image folders in under 15 seconds.
2. **Patient-Isolated Stratification:**
   - Isolates the 983 images from `BBox_List_2017.csv` strictly as an unseen **Explainability Holdout Set**.
   - Stratifies 25,000 images ensuring no patient is shared between Train and Val.
3. **2-Stage Transfer Learning (DenseNet121):**
   - Stage 1: Warmup linear head (2 epochs).
   - Stage 2: Fine-tuning `denseblock4` + `norm5` (6 epochs, cosine annealing, weighted BCE loss).
4. **Post-Hoc Confidence Calibration (Temperature Scaling):**
   - Uses L-BFGS to learn optimal per-disease scaling temperatures $T_i$ to minimize ECE.
5. **Operating Thresholds:**
   - Calculates Youden's J-statistic optimal sensitivity/specificity threshold for each disease.
6. **Explainability Localization Benchmark:**
   - Evaluates Grad-CAM++ bounding boxes against the 1,600 radiologist boxes in `BBox_List_2017.csv` (reporting $IoBB$ and $IoU$).

---

## 3. Artifacts Produced in `/kaggle/working/`

Once the script completes (~90–120 minutes on Kaggle T4 GPU), the following files will be ready in the `/kaggle/working/` panel:

* `densenet121_nih14_best.pth` (~28 MB)
* `temperature_scaler.json`
* `optimal_thresholds.json`
* `validation_metrics.json`

Download these 4 files and place them into your local `visioncare-ai/pretrained/` directory.
