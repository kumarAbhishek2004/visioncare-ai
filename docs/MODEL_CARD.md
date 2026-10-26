# VisionCare AI: Model Card & Clinical Validation Summary

## 1. Model Details
- **Model Name:** VisionCare NIH-14 Frontal Chest Radiograph Classifier & Feature Attribution Engine
- **Architecture:** DenseNet-121 (`torchvision.models.densenet121`) with 14-disease multi-label linear projection head
- **Target Modality:** Frontal Chest Radiographs (Posteroanterior [PA] & Anteroposterior [AP] views)
- **Input Resolution:** $224 \times 224 \times 3$ (Baseline V1) / $384 \times 384 \times 3$ (High-Performance V2)
- **Primary Task:** Multi-label thoracic pathology detection across 14 non-mutually exclusive disease classes
- **Explainability Technique:** Grad-CAM++ with Otsu connected component boundary extraction and 5-zone anatomical mapping

---

## 2. Intended Clinical Use & Regulatory Gating
- **Intended Use:** Assistive Clinical Decision Support (CDS) for radiologists, triage prioritization in emergency departments, and visual feature attribution auditing.
- **Regulatory Framework:** Software as a Medical Device (SaMD) Class II / EU AI Act High-Risk Healthcare AI compliance.
- **Safety Rule:** VisionCare AI is an **assistive** decision-support system; it does NOT make autonomous diagnoses. Output predictions are categorized into:
  - `ASSISTED_REVIEW_READY`: Mean calibrated confidence exceeds uncertainty threshold ($T_i$ scaling verified).
  - `MANUAL_REVIEW_MANDATORY`: High diagnostic entropy or borderline probabilities trigger immediate mandatory radiologist review.

---

## 3. Training & Evaluation Dataset
- **Primary Source:** NIH Clinical Center ChestX-ray14 (112,120 frontal chest radiographs across 30,805 unique patients).
- **Disease Pathologies (14):**
  1. Atelectasis
  2. Cardiomegaly
  3. Effusion
  4. Infiltration
  5. Mass
  6. Nodule
  7. Pneumonia
  8. Pneumothorax
  9. Consolidation
  10. Edema
  11. Emphysema
  12. Fibrosis
  13. Pleural Thickening
  14. Hernia

### Patient-Isolated Stratification & Curation
- Over $54\%$ ($60,412$ scans) in NIH-14 represent "No Finding" cases with extensive longitudinal patient repeat scans.
- Stratification randomly partitioned unique patients into non-overlapping groups ($85\%$ Train / $15\%$ Validation) to prevent patient-level data leakage across split boundaries.
- A dedicated holdout cohort ($880$ patient scans with ground-truth radiologist bounding boxes from `BBox_List_2017.csv`) was isolated strictly for quantitative explainability evaluation ($IoBB$ and $IoU$).

---

## 4. Mathematical Formulations

### 4.1 Multi-Label Objective with Positive Weight Balancing
Chest radiographs feature severe class imbalance (e.g. Hernia $\approx 0.2\%$, Infiltration $\approx 18\%$). The loss per pathology $c$ is:
$$\mathcal{L}_{BCE}(y_c, \hat{y}_c) = - \left[ w_c \cdot y_c \log(\sigma(z_c)) + (1 - y_c) \log(1 - \sigma(z_c)) \right]$$
where $w_c = \frac{N_{neg, c}}{N_{pos, c}}$ balances gradient contribution across under-represented classes.

### 4.2 Post-Hoc Temperature Scaling Calibration
Raw neural network logits $z_c$ systematically suffer from overconfidence. Post-hoc Platt/Temperature scaling optimizes a per-class temperature parameter $T_c > 0$ on the validation set:
$$\hat{p}_c = \sigma\left(\frac{z_c}{T_c}\right)$$
This preserves rank ordering (AUROC remains identical) while substantially reducing the **Expected Calibration Error (ECE)**:
$$ECE = \sum_{m=1}^{M} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$

### 4.3 Optimal Operating Thresholds (Youden's J-Statistic)
Rather than applying an arbitrary $0.50$ cutoff, optimal operating cutoffs $\tau_c^*$ are calibrated by maximizing Youden's Index on validation ROC curves:
$$J(\tau) = \text{Sensitivity}(\tau) + \text{Specificity}(\tau) - 1$$
$$\tau_c^* = \arg\max_{\tau} J(\tau)$$

### 4.4 Grad-CAM++ Attribution Formulation
Grad-CAM++ captures multiple occurrences of a disease by computing positive partial derivatives of class score $Y^c$ with respect to activation map $A^k$:
$$w_k^c = \sum_{i} \sum_{j} \alpha_{ij}^{kc} \cdot \text{ReLU}\left(\frac{\partial Y^c}{\partial A_{ij}^k}\right)$$
$$\alpha_{ij}^{kc} = \frac{\left(\frac{\partial^2 Y^c}{\partial A_{ij}^k{}^2}\right)}{2 \left(\frac{\partial^2 Y^c}{\partial A_{ij}^k{}^2}\right) + \sum_{a,b} A_{ab}^k \left(\frac{\partial^3 Y^c}{\partial A_{ij}^k{}^3}\right)}$$
$$L_{\text{Grad-CAM++}}^c = \text{ReLU}\left(\sum_k w_k^c A^k\right)$$

---

## 5. Quantitative Validation Metrics (Baseline Model)

| Pathology | Validation AUROC | Optimal Cutoff ($\tau^*$) | Temperature ($T$) |
| :--- | :---: | :---: | :---: |
| **Edema** | **0.8410** | 0.2454 | 0.6140 |
| **Pneumothorax** | **0.8165** | 0.1780 | 0.6100 |
| **Emphysema** | **0.8087** | 0.1000 | 0.5673 |
| **Effusion** | **0.8045** | 0.4680 | 0.9939 |
| **Atelectasis** | 0.7406 | 0.5615 | 1.1517 |
| **Mass** | 0.7370 | 0.5641 | 1.2282 |
| **Fibrosis** | 0.7365 | 0.4000 | 0.3401 |
| **Cardiomegaly** | 0.7357 | 0.1370 | 0.5168 |
| **Consolidation** | 0.6986 | 0.1462 | 0.6631 |
| **Infiltration** | 0.6925 | 0.4430 | 0.6521 |
| **Pleural Thickening** | 0.6905 | 0.2000 | 0.4320 |
| **Pneumonia** | 0.6834 | 0.1000 | 0.3731 |
| **Hernia** | 0.6671 | 0.1000 | 0.4050 |
| **Nodule** | 0.6178 | 0.5580 | 1.3762 |
| **OVERALL MEAN AUROC** | **0.7336** | — | — |

---

## 6. Explainability & Anatomical Zoning Validation
- **Intersection over Bounding Box ($IoBB$):**
  - $\ge 10\%$ overlap: $58.2\%$
  - $\ge 25\%$ overlap: $32.4\%$
- **5-Zone Anatomical Mapping Distribution:**
  - Partitions segmented lung parenchyma into Right Upper (RUZ), Right Middle (RMZ), Right Lower (RLZ), Left Upper (LUZ), Left Lower (LLZ), and Mediastinal fields.
  - Generates spatial percentage contribution verifying that focal heatmaps align anatomically with clinical lesion sites.

---

## 7. Ethical Considerations & Limitations
1. **Covariate Shift:** The classification engine ingests the original, non-masked radiograph to prevent artificial edge artifacts. Masks are used solely for UI visualization and bounding envelope constraints.
2. **False Diagnostic Claims:** NIH-14 does NOT contain Tuberculosis; automated systems must not fabricate TB classification labels.
3. **Clinical Verification Required:** VisionCare AI does not replace a board-certified radiologist; all findings require clinical correlation and secondary review.
