#!/usr/bin/env python3
"""
Chennai Offline Spatial Flood Susceptibility Baseline — Model Training & Evaluation
Model Name: Chennai Offline Spatial Flood Susceptibility Baseline
Strict boundary: This is an offline daily-scale susceptibility baseline, NOT a real-time nowcasting model.
"""

import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss,
    confusion_matrix
)

CANONICAL_PARQUET = "Data/final/chennai_flood_training.parquet"
EXPECTED_SHA256 = "ce2bcd5766c26ec6ef152f518f73dd72facfaf00906bc4399cc6dc2c66a2c7b5"

AUDITED_PREDICTOR_ALLOWLIST = [
    "rainfall_daily_mm",
    "rainfall_cum_2d_mm",
    "rainfall_cum_3d_mm",
    "rainfall_cum_7d_mm",
    "rainfall_delta_mm",
    "elevation_m",
    "slope_deg",
    "low_lying_score",
    "built_up_ratio",
    "water_ratio",
    "vegetation_ratio",
    "worldcover_class",
    "soil_clay_0_5cm",
    "dist_to_swd_m",
    "dist_to_macro_drain_m",
    "dist_to_micro_drain_m",
    "dist_to_river_stream_m",
    "dist_to_buckingham_canal_m",
    "drainage_density_m_per_km2",
    "building_count",
    "building_area_m2",
    "dist_to_hospital_m",
    "hospital_count_1km",
    "dist_to_fire_station_m",
    "dist_to_police_m"
]

TARGET = "flood_occurred"
RANDOM_STATE = 42

def compute_sha256(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def select_threshold_f1(y_true, y_prob):
    """
    Deterministic validation-only threshold selection rule:
    1. Scan candidate thresholds in [0.01, 0.99] with step 0.01.
    2. Select threshold that maximizes F1 score.
    3. If multiple thresholds tie on F1, select the one with higher recall.
    4. If still tied, select the lowest threshold.
    """
    thresholds = np.linspace(0.01, 0.99, 99)
    best_f1 = -1.0
    best_recall = -1.0
    best_thresh = 0.5

    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        if f1 > best_f1:
            best_f1 = f1
            best_recall = rec
            best_thresh = t
        elif np.isclose(f1, best_f1):
            if rec > best_recall:
                best_recall = rec
                best_thresh = t
            elif np.isclose(rec, best_recall):
                if t < best_thresh:
                    best_thresh = t

    return float(best_thresh), float(best_f1), float(best_recall)

def train_and_evaluate():
    print("=" * 80)
    print("TRAINING: Chennai Offline Spatial Flood Susceptibility Baseline")
    print("=" * 80)

    # 1. Verify Dataset SHA-256
    actual_sha = compute_sha256(CANONICAL_PARQUET)
    if actual_sha != EXPECTED_SHA256:
        raise ValueError(f"FATAL: Dataset hash mismatch! Expected {EXPECTED_SHA256}, got {actual_sha}")
    print(f"[OK] Canonical Parquet verified intact: {actual_sha}")

    # 2. Load dataset
    df = pd.read_parquet(CANONICAL_PARQUET)
    df["date_str"] = df["date"].astype(str)

    # 3. Partition datasets strictly by chronological boundaries
    train_mask = (df["date_str"] >= "2015-10-01") & (df["date_str"] <= "2015-11-17")
    val_mask = (df["date_str"] >= "2015-11-30") & (df["date_str"] <= "2015-12-02")
    test_mask = (df["date_str"] >= "2015-12-03") & (df["date_str"] <= "2015-12-10")
    excl_mask = (df["date_str"] >= "2015-11-18") & (df["date_str"] <= "2015-11-29")

    df_train = df[train_mask].copy()
    df_val = df[val_mask].copy()
    df_test = df[test_mask].copy()
    df_excl = df[excl_mask].copy()

    print(f"Partitions: TRAIN={len(df_train)}, VAL={len(df_val)}, TEST={len(df_test)}, EXCLUDED={len(df_excl)}")

    # 4. Feature and Target matrices (enforcing exact 25 audited predictors)
    X_train = df_train[AUDITED_PREDICTOR_ALLOWLIST].copy()
    y_train = df_train[TARGET].values

    X_val = df_val[AUDITED_PREDICTOR_ALLOWLIST].copy()
    y_val = df_val[TARGET].values

    X_test = df_test[AUDITED_PREDICTOR_ALLOWLIST].copy()
    y_test = df_test[TARGET].values

    # 5. Dynamic class weighting computed strictly from TRAIN
    train_pos = int((y_train == 1).sum())
    train_neg = int((y_train == 0).sum())
    scale_pos_weight = float(train_neg / train_pos)
    print(f"TRAIN class counts: Positives={train_pos}, Negatives={train_neg}")
    print(f"Dynamically calculated scale_pos_weight = {train_neg} / {train_pos} = {scale_pos_weight:.4f}")

    # 6. Hyperparameters and model configuration
    hyperparameters = {
        "n_estimators": 500,
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "scale_pos_weight": scale_pos_weight,
        "eval_metric": "aucpr",
        "early_stopping_rounds": 25,
        "random_state": RANDOM_STATE,
        "n_jobs": -1
    }

    model = xgb.XGBClassifier(**hyperparameters)

    # 7. Model fitting on TRAIN with early stopping on VALIDATION
    print("\nFitting XGBoost model on TRAIN with early stopping on VALIDATION (eval_metric='aucpr')...")
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=50
    )

    best_iteration = model.best_iteration if hasattr(model, "best_iteration") else model.n_estimators
    print(f"Optimal boosting iteration: {best_iteration}")

    # 8. Validation threshold selection (TEST IS NOT TOUCHED)
    val_probs = model.predict_proba(X_val)[:, 1]
    selected_threshold, val_best_f1, val_best_rec = select_threshold_f1(y_val, val_probs)
    print(f"\nValidation-only threshold selected: {selected_threshold:.4f} (Val F1: {val_best_f1:.4f}, Val Recall: {val_best_rec:.4f})")

    # 9. Final one-time evaluation on frozen TEST set
    print("\nEvaluating frozen model and threshold on held-out TEST set...")
    test_probs = model.predict_proba(X_test)[:, 1]
    test_preds = (test_probs >= selected_threshold).astype(int)

    roc_auc = float(roc_auc_score(y_test, test_probs))
    pr_auc = float(average_precision_score(y_test, test_probs))
    prec = float(precision_score(y_test, test_preds, zero_division=0))
    rec = float(recall_score(y_test, test_preds, zero_division=0))
    f1 = float(f1_score(y_test, test_preds, zero_division=0))
    brier = float(brier_score_loss(y_test, test_probs))

    cm = confusion_matrix(y_test, test_preds)
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]

    test_positives = int((y_test == 1).sum())
    test_negatives = int((y_test == 0).sum())
    pred_positives = int((test_preds == 1).sum())
    pred_negatives = int((test_preds == 0).sum())

    print("\n" + "=" * 50)
    print("TEST EVALUATION METRICS (Frozen Baseline):")
    print("=" * 50)
    print(f"ROC-AUC:           {roc_auc:.4f}")
    print(f"PR-AUC:            {pr_auc:.4f}  <-- Primary Metric (Imbalanced Positive Class)")
    print(f"Precision:         {prec:.4f}")
    print(f"Recall:            {rec:.4f}  <-- Primary Operational Metric")
    print(f"F1-Score:          {f1:.4f}")
    print(f"Brier Score:       {brier:.4f} (estimated scores; not calibrated probabilities)")
    print("-" * 50)
    print(f"Actual Positives:  {test_positives}")
    print(f"Actual Negatives:  {test_negatives}")
    print(f"Predicted Pos:     {pred_positives}")
    print(f"Predicted Neg:     {pred_negatives}")
    print(f"Confusion Matrix:  TP={tp}, FP={fp}, FN={fn}, TN={tn}")
    print("=" * 50)

    # 10. Extract Feature Importance
    booster = model.get_booster()
    score_gain = booster.get_score(importance_type="gain")
    score_weight = booster.get_score(importance_type="weight")
    score_cover = booster.get_score(importance_type="cover")

    feature_importance = {}
    for feat in AUDITED_PREDICTOR_ALLOWLIST:
        feature_importance[feat] = {
            "gain": float(score_gain.get(feat, 0.0)),
            "weight": float(score_weight.get(feat, 0.0)),
            "cover": float(score_cover.get(feat, 0.0))
        }

    # 11. Save model and metadata artifacts
    os.makedirs("Models/trained", exist_ok=True)
    os.makedirs("Models/metadata", exist_ok=True)

    model_path = "Models/trained/chennai_xgboost_baseline.json"
    metadata_path = "Models/metadata/chennai_xgboost_baseline_metadata.json"
    metrics_path = "Models/metadata/chennai_xgboost_baseline_metrics.json"
    feat_imp_path = "Models/metadata/chennai_xgboost_baseline_feature_importance.json"

    # Save model binary/json
    model.save_model(model_path)
    print(f"[SAVED] Trained model: {model_path}")

    # Metrics dictionary
    metrics_dict = {
        "model_name": "Chennai Offline Spatial Flood Susceptibility Baseline",
        "evaluation_partition": "TEST",
        "date_range": "2015-12-03 to 2015-12-10",
        "threshold": selected_threshold,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "brier_score": brier,
        "confusion_matrix": {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "true_negative": tn
        },
        "counts": {
            "actual_positives": test_positives,
            "actual_negatives": test_negatives,
            "predicted_positives": pred_positives,
            "predicted_negatives": pred_negatives
        },
        "probability_statement": "Raw outputs represent estimated decision scores / probabilities and have not undergone post-hoc empirical calibration. Brier score is reported without asserting calibration."
    }
    with open(metrics_path, "w") as f:
        json.dump(metrics_dict, f, indent=2)
    print(f"[SAVED] Metrics JSON: {metrics_path}")

    # Feature importance dictionary
    feat_imp_payload = {
        "disclaimer": "Feature importance represents model reliance and does not establish physical causality. Do not claim that a highly important feature physically causes flooding.",
        "feature_importance": feature_importance
    }
    with open(feat_imp_path, "w") as f:
        json.dump(feat_imp_payload, f, indent=2)
    print(f"[SAVED] Feature Importance JSON: {feat_imp_path}")

    # Comprehensive metadata dictionary
    metadata_dict = {
        "model_name": "Chennai Offline Spatial Flood Susceptibility Baseline",
        "scientific_boundary": "Offline daily-scale 500m spatial susceptibility model. NOT a 0-3 hour nowcasting model.",
        "dataset_path": CANONICAL_PARQUET,
        "dataset_sha256": actual_sha,
        "dataset_row_count": len(df),
        "dataset_column_count": 32,
        "target": TARGET,
        "predictor_allowlist": AUDITED_PREDICTOR_ALLOWLIST,
        "split_definition": {
            "strategy": "event_aware_chronological_split",
            "train_dates": "2015-10-01 to 2015-11-17 (14 dates)",
            "validation_dates": "2015-11-30 to 2015-12-02 (3 dates)",
            "test_dates": "2015-12-03 to 2015-12-10 (7 dates)",
            "excluded_dates": "2015-11-18 to 2015-11-29 (8 dates)"
        },
        "split_counts": {
            "train": {"rows": len(df_train), "positives": train_pos, "negatives": train_neg},
            "validation": {"rows": len(df_val), "positives": int((y_val == 1).sum()), "negatives": int((y_val == 0).sum())},
            "test": {"rows": len(df_test), "positives": test_positives, "negatives": test_negatives},
            "excluded": {"rows": len(df_excl), "positives": 0, "negatives": len(df_excl)}
        },
        "class_weight": {
            "scale_pos_weight": scale_pos_weight,
            "formula": "TRAIN negative count / TRAIN positive count",
            "train_negatives": train_neg,
            "train_positives": train_pos
        },
        "hyperparameters": {k: v for k, v in hyperparameters.items() if k != "scale_pos_weight"},
        "hyperparameters_scale_pos_weight": scale_pos_weight,
        "random_seed": RANDOM_STATE,
        "xgboost_version": xgb.__version__,
        "python_version": sys.version,
        "early_stopping_configuration": {
            "eval_metric": "aucpr",
            "early_stopping_rounds": 25,
            "eval_set": "VALIDATION set (Nov 30 - Dec 02)",
            "best_iteration": int(best_iteration)
        },
        "threshold_selection_method": "Validation-only deterministic grid search [0.01, 0.99] maximizing F1 score with recall and lower-bound tie-breakers.",
        "selected_threshold": selected_threshold,
        "test_metrics": metrics_dict
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata_dict, f, indent=2)
    print(f"[SAVED] Metadata JSON: {metadata_path}")

    # Re-verify Parquet hash after training
    post_sha = compute_sha256(CANONICAL_PARQUET)
    if post_sha != EXPECTED_SHA256:
        raise ValueError(f"CRITICAL ERROR: Parquet hash altered during training! Expected {EXPECTED_SHA256}, got {post_sha}")
    print(f"[OK] Re-verified Parquet SHA-256 post-training: {post_sha}")

if __name__ == "__main__":
    train_and_evaluate()
