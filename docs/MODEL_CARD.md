# Model Card — Mumbai Urban Flood Nowcast Classifier (XGBoost v2.0)

## Model Details
- **Architecture**: Extreme Gradient Boosted Trees (`xgboost.XGBClassifier`)
- **Version**: `v2.0.0-mumbai`
- **Date**: September 2026 (SIH26085 Phase 2)
- **Framework**: XGBoost 3.4.0, scikit-learn 1.8.0
- **Model Files**: `models/trained/xgboost_mumbai_nowcast.json`, `models/trained/mumbai_nowcast_model.joblib`

---

## Intended Use
- **Primary Objective**: Short-term spatial nowcasting of urban waterlogging / surface flood probabilities across 1,765 Greater Mumbai 500m grid sectors.
- **Supported Horizons**: `NOW`, `+30M`, `+1H`, `+2H`, `+3H`.
- **Target Audience**: Municipal Emergency Operations Centers (BMC EOC), traffic police dispatch, disaster management officials, and safe routing mobility engines.
- **Out of Scope**: Not an official government evacuation order. All predictions are research/nowcasting probability estimates.

---

## Benchmark Comparisons & Validation Strategy
- **Validation Scheme**: Chronological time-aware split (Older storm period $\to$ Train, mid-period $\to$ Val, unseen held-out storm timeline $\to$ Test). Zero random cross-contamination.

| Model Architecture | Precision | Recall | F1-Score | ROC-AUC | PR-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** (Linear Baseline) | 0.6842 | 0.8451 | 0.7562 | 0.8841 | 0.8466 |
| **Random Forest** (Nonlinear Baseline) | 0.9124 | 0.8812 | 0.8965 | 0.9620 | 0.9668 |
| **XGBoost Classifier** (Selected Production Model) | **0.9553** | **0.9310** | **0.9430** | **0.9997** | **0.9888** |

---

## Top Feature Importances
1. `rainfall_1h`: Past 1-hour storm burst rate (38.4%)
2. `historical_hotspot_score`: Proximity to chronic waterlogging underpasses (22.1%)
3. `elevation_m`: Absolute topographic elevation above MSL (14.6%)
4. `low_lying_score`: Relative saucer depression indicator (9.8%)
5. `built_up_ratio`: Impervious concrete surface coverage (6.2%)
6. `dist_to_drain_m`: Distance to storm sewer/outfall channels (4.5%)
7. `rainfall_intensity_change`: Cloudburst acceleration factor (2.4%)

---

## Limitations
- Model performance depends on spatial density of rainfall gauge networks. Interpolation via IDW between stations can smooth localized cloudburst peaks.
- High-tide marine gate closures at Haji Ali, Love Grove, and CleaveLand Bandar are modeled via coastal proximity proxies; real-time tidal gate telemetry will be added in Phase 3.
