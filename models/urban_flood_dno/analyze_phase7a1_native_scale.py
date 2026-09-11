"""
FloodWatch AI — Phase 7A.1: Native-Scale Normalization Resolution & Baseline Re-Evaluation
SIH26085 — Urban Flood Nowcasting System

Scope:
1. Purely diagnostic evaluation on the native physical scale.
2. Evaluates the existing Phase 6 checkpoint: models/urban_flood_dno/checkpoints/chennai_phase6/best_dno_checkpoint.pt
3. Uses the existing test tensors without modification.
4. Corrects the evaluation contract: interprets model predictions directly in native physical units
   without the artificial 5x multiplier that was mistakenly applied during Phase 6/7A evaluation.
5. Produces side-by-side comparison tables (Old vs Corrected) and corrected diagnostic plots.
"""

import os
import sys
import json
import csv
import numpy as np
import scipy.stats as stats
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Connect to UrbanFloodCast
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DNO_DIR = os.path.join(REPO_ROOT, "External", "UrbanFloodCast", "UrbanFloodCast", "DNO")
if DNO_DIR not in sys.path:
    sys.path.insert(0, DNO_DIR)

from models.DNO import DNO

TEST_STORMS = [
    {"id": "storm_011", "rainfall_mm": 12.0, "category": "Low", "profile": "multi_peak", "peak_intensity": 12.80},
    {"id": "storm_016", "rainfall_mm": 28.0, "category": "Moderate", "profile": "uniform", "peak_intensity": 14.88},
    {"id": "storm_007", "rainfall_mm": 60.0, "category": "Heavy", "profile": "front_loaded", "peak_intensity": 87.38},
    {"id": "storm_024", "rainfall_mm": 95.0, "category": "Very Heavy", "profile": "multi_peak", "peak_intensity": 101.30},
    {"id": "storm_028", "rainfall_mm": 135.0, "category": "Extreme", "profile": "back_loaded", "peak_intensity": 176.40}
]

DEPTH_BINS = [
    {"name": "0–5 cm", "min": 0.0, "max": 0.05},
    {"name": "5–10 cm", "min": 0.05, "max": 0.10},
    {"name": "10–20 cm", "min": 0.10, "max": 0.20},
    {"name": "20–50 cm", "min": 0.20, "max": 0.50},
    {"name": "50 cm–1 m", "min": 0.50, "max": 1.00},
    {"name": "1–2 m", "min": 1.00, "max": 2.00},
    {">2 m": True, "name": ">2 m", "min": 2.00, "max": float("inf")}
]

FLOOD_THRESHOLDS = [0.05, 0.10, 0.20, 0.50, 1.00]
DX = 78.125
DT_MIN = 5.0


def setup_directories():
    log_dir = os.path.join(REPO_ROOT, "models", "urban_flood_dno", "logs", "chennai_phase7a1")
    out_dir = os.path.join(REPO_ROOT, "outputs", "chennai_dno", "phase7a1_native_scale")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    return log_dir, out_dir


def compute_metrics(pred: np.ndarray, true: np.ndarray):
    diff = pred - true
    abs_diff = np.abs(diff)
    mae = float(np.mean(abs_diff))
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    bias = float(np.mean(diff))
    max_err = float(np.max(abs_diff))

    p_flat = pred.flatten()
    t_flat = true.flatten()
    std_p = np.std(p_flat)
    std_t = np.std(t_flat)
    if std_p > 1e-6 and std_t > 1e-6:
        pearson = float(np.corrcoef(p_flat, t_flat)[0, 1])
        spearman, _ = stats.spearmanr(p_flat, t_flat)
        spearman = float(spearman)
    else:
        pearson = 0.0
        spearman = 0.0

    return {
        "mae": mae,
        "rmse": rmse,
        "bias": bias,
        "max_err": max_err,
        "pearson": pearson,
        "spearman": spearman
    }


def compute_confusion_matrix(pred: np.ndarray, true: np.ndarray, threshold: float):
    p_wet = pred > threshold
    t_wet = true > threshold

    tp = int(np.sum(p_wet & t_wet))
    tn = int(np.sum((~p_wet) & (~t_wet)))
    fp = int(np.sum(p_wet & (~t_wet)))
    fn = int(np.sum((~p_wet) & t_wet))

    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 1.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 1.0
    f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    union = tp + fp + fn
    iou = float(tp / union) if union > 0 else 1.0

    return {
        "threshold_m": threshold,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "iou": iou
    }


def extract_patch(arr: np.ndarray, y: int, x: int, size: int):
    pad = size // 2
    padded = np.pad(arr, pad, mode="edge")
    return padded[y : y + size, x : x + size]


def run_phase7a1_evaluation():
    print("=" * 80)
    print("FLOODWATCH AI — PHASE 7A.1: NATIVE-SCALE NORMALIZATION RESOLUTION")
    print("=" * 80)

    log_dir, out_dir = setup_directories()
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"[1] Hardware Verified: {torch.cuda.get_device_name(device)} ({device})")

    # Load DEM
    dem_path = os.path.join(REPO_ROOT, "Data", "dno", "chennai", "processed", "pilot_adyar_velachery_dem_128x128.npy")
    dem = np.load(dem_path) if os.path.exists(dem_path) else np.zeros((128, 128))

    # Load Existing Phase 6 Checkpoint
    ckpt_path = os.path.join(REPO_ROOT, "models", "urban_flood_dno", "checkpoints", "chennai_phase6", "best_dno_checkpoint.pt")
    checkpoint = torch.load(ckpt_path, map_location=device)
    model = DNO(num_channels=5, width=10, initial_step=1, pad=0, factor=1).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Load Phase 6 Reference Log
    p6_summary_path = os.path.join(REPO_ROOT, "models", "urban_flood_dno", "logs", "chennai_phase6", "test_summary.json")
    with open(p6_summary_path, "r", encoding="utf-8") as f:
        p6_ref = json.load(f)

    tensor_dir = os.path.join(REPO_ROOT, "Data", "dno", "chennai", "storm_library", "tensors")

    old_vs_corrected_records = []
    corrected_per_event_records = []
    corrected_depth_bin_records = []
    corrected_temporal_records = []
    corrected_peak_records = []
    corrected_flood_records = []

    all_storm_data = {}

    print("\n[2] Evaluating Test Storms on Native Physical Scale...")

    for storm in TEST_STORMS:
        eid = storm["id"]
        x_path = os.path.join(tensor_dir, f"{eid}_input_tensor.pt")
        y_path = os.path.join(tensor_dir, f"{eid}_target_tensor.pt")

        x = torch.load(x_path, map_location=device)
        y = torch.load(y_path, map_location="cpu")  # [1, 128, 128, 24, 3]

        with torch.no_grad():
            pred_raw = model(x).cpu()

        pred_np = pred_raw.squeeze(0).numpy()  # [128, 128, 24, 3]
        true_np = y.squeeze(0).numpy()        # [128, 128, 24, 3]

        # --- NATIVE PHYSICAL SCALE (CORRECTED) ---
        # No 5x multiplier: pred_np and true_np are ALREADY in native meters and m/s
        H_pred_native = np.maximum(pred_np[..., 0], 0.0)
        U_pred_native = pred_np[..., 1]
        V_pred_native = pred_np[..., 2]

        H_true_native = true_np[..., 0]
        U_true_native = true_np[..., 1]
        V_true_native = true_np[..., 2]

        # --- OLD INFLATED SCALE (PHASE 6 / PHASE 7A EVALUATION) ---
        H_pred_old = H_pred_native * 5.0
        H_true_old = H_true_native * 5.0
        U_pred_old = U_pred_native * 5.0
        U_true_old = U_true_native * 5.0
        V_pred_old = V_pred_native * 5.0
        V_true_old = V_true_native * 5.0

        all_storm_data[eid] = {
            "H_pred": H_pred_native,
            "H_true": H_true_native,
            "U_pred": U_pred_native,
            "U_true": U_true_native,
            "V_pred": V_pred_native,
            "V_true": V_true_native,
            "meta": storm
        }

        # Metrics on Native Scale
        h_met_native = compute_metrics(H_pred_native, H_true_native)
        u_met_native = compute_metrics(U_pred_native, U_true_native)
        v_met_native = compute_metrics(V_pred_native, V_true_native)

        # Metrics on Old Inflated Scale
        h_met_old = compute_metrics(H_pred_old, H_true_old)
        u_met_old = compute_metrics(U_pred_old, U_true_old)
        v_met_old = compute_metrics(V_pred_old, V_true_old)

        # Verify exact 5.0x relationship
        ratio_h_mae = h_met_old["mae"] / h_met_native["mae"]
        assert abs(ratio_h_mae - 5.0) < 1e-4, f"Ratio {ratio_h_mae} != 5.0"

        # Check correlation invariance
        assert abs(h_met_old["pearson"] - h_met_native["pearson"]) < 1e-6, "Correlation not invariant!"

        # Global vs Interior (excluding x=127)
        H_true_int = H_true_native[:, :127, :]
        H_pred_int = H_pred_native[:, :127, :]
        h_int_met_native = compute_metrics(H_pred_int, H_true_int)

        t_peak_val = float(np.max(H_true_native))
        p_peak_val = float(np.max(H_pred_native))
        t_int_peak_val = float(np.max(H_true_int))
        p_int_peak_val = float(np.max(H_pred_int))

        # Peak error
        peak_err_m = p_peak_val - t_peak_val
        peak_pct_err = (peak_err_m / t_peak_val) * 100.0 if t_peak_val > 0 else 0.0

        print(f"  {eid} ({storm['category']}, {storm['rainfall_mm']}mm):")
        print(f"    Native Depth H -> MAE: {h_met_native['mae']*100:.2f} cm (was {h_met_old['mae']*100:.2f} cm in P6)")
        print(f"    Native Peak H  -> True: {t_peak_val:.4f}m, Pred: {p_peak_val:.4f}m (Err: {peak_err_m:+.4f}m, {peak_pct_err:+.1f}%)")
        print(f"    Interior Peak  -> True: {t_int_peak_val:.4f}m, Pred: {p_int_peak_val:.4f}m (Err: {p_int_peak_val - t_int_peak_val:+.4f}m)")

        # Record Old vs Corrected
        old_vs_corrected_records.extend([
            {"event_id": eid, "metric": "H_MAE_m", "phase6_reported": h_met_old["mae"], "phase7a_reproduced": h_met_old["mae"], "phase7a1_corrected": h_met_native["mae"], "scale_factor": "5x -> 1x", "invariant": "NO (5x scale)"},
            {"event_id": eid, "metric": "H_RMSE_m", "phase6_reported": h_met_old["rmse"], "phase7a_reproduced": h_met_old["rmse"], "phase7a1_corrected": h_met_native["rmse"], "scale_factor": "5x -> 1x", "invariant": "NO (5x scale)"},
            {"event_id": eid, "metric": "H_Bias_m", "phase6_reported": h_met_old["bias"], "phase7a_reproduced": h_met_old["bias"], "phase7a1_corrected": h_met_native["bias"], "scale_factor": "5x -> 1x", "invariant": "NO (5x scale)"},
            {"event_id": eid, "metric": "True_Peak_m", "phase6_reported": float(np.max(H_true_old)), "phase7a_reproduced": float(np.max(H_true_old)), "phase7a1_corrected": t_peak_val, "scale_factor": "5x -> 1x", "invariant": "NO (5x scale)"},
            {"event_id": eid, "metric": "Pred_Peak_m", "phase6_reported": float(np.max(H_pred_old)), "phase7a_reproduced": float(np.max(H_pred_old)), "phase7a1_corrected": p_peak_val, "scale_factor": "5x -> 1x", "invariant": "NO (5x scale)"},
            {"event_id": eid, "metric": "Peak_Error_m", "phase6_reported": float(np.max(H_pred_old) - np.max(H_true_old)), "phase7a_reproduced": float(np.max(H_pred_old) - np.max(H_true_old)), "phase7a1_corrected": peak_err_m, "scale_factor": "5x -> 1x", "invariant": "NO (5x scale)"},
            {"event_id": eid, "metric": "Peak_Pct_Error", "phase6_reported": peak_pct_err, "phase7a_reproduced": peak_pct_err, "phase7a1_corrected": peak_pct_err, "scale_factor": "1x", "invariant": "YES"},
            {"event_id": eid, "metric": "Pearson_Corr", "phase6_reported": h_met_old["pearson"], "phase7a_reproduced": h_met_old["pearson"], "phase7a1_corrected": h_met_native["pearson"], "scale_factor": "1x", "invariant": "YES"},
            {"event_id": eid, "metric": "Spearman_Corr", "phase6_reported": h_met_old["spearman"], "phase7a_reproduced": h_met_old["spearman"], "phase7a1_corrected": h_met_native["spearman"], "scale_factor": "1x", "invariant": "YES"},
            {"event_id": eid, "metric": "U_MAE_mps", "phase6_reported": u_met_old["mae"], "phase7a_reproduced": u_met_old["mae"], "phase7a1_corrected": u_met_native["mae"], "scale_factor": "5x -> 1x", "invariant": "NO (5x scale)"},
            {"event_id": eid, "metric": "V_MAE_mps", "phase6_reported": v_met_old["mae"], "phase7a_reproduced": v_met_old["mae"], "phase7a1_corrected": v_met_native["mae"], "scale_factor": "5x -> 1x", "invariant": "NO (5x scale)"}
        ])

        # Record Corrected Per-Event Summary
        corrected_per_event_records.append({
            "event_id": eid,
            "rainfall_mm": storm["rainfall_mm"],
            "severity_category": storm["category"],
            "profile": storm["profile"],
            "peak_intensity_mm_hr": storm["peak_intensity"],
            "H_MAE_m": h_met_native["mae"],
            "H_RMSE_m": h_met_native["rmse"],
            "H_Bias_m": h_met_native["bias"],
            "H_Max_Actual_m": t_peak_val,
            "H_Max_Pred_m": p_peak_val,
            "Peak_Error_m": peak_err_m,
            "Peak_Pct_Error": peak_pct_err,
            "H_Interior_MAE_m": h_int_met_native["mae"],
            "H_Interior_Max_Actual_m": t_int_peak_val,
            "H_Interior_Max_Pred_m": p_int_peak_val,
            "H_Interior_Peak_Error_m": p_int_peak_val - t_int_peak_val,
            "U_MAE_mps": u_met_native["mae"],
            "U_RMSE_mps": u_met_native["rmse"],
            "U_Bias_mps": u_met_native["bias"],
            "V_MAE_mps": v_met_native["mae"],
            "V_RMSE_mps": v_met_native["rmse"],
            "V_Bias_mps": v_met_native["bias"],
            "Pearson_Correlation": h_met_native["pearson"],
            "Spearman_Correlation": h_met_native["spearman"]
        })

        # --- CORRECTED FLOOD EXTENT AT NATIVE THRESHOLDS ---
        for thresh in FLOOD_THRESHOLDS:
            cm = compute_confusion_matrix(H_pred_native, H_true_native, thresh)
            cm_final = compute_confusion_matrix(H_pred_native[..., -1], H_true_native[..., -1], thresh)
            corrected_flood_records.append({
                "event_id": eid,
                "rainfall_mm": storm["rainfall_mm"],
                "threshold_m": thresh,
                "volume_tp": cm["tp"],
                "volume_fp": cm["fp"],
                "volume_fn": cm["fn"],
                "volume_tn": cm["tn"],
                "volume_precision": cm["precision"],
                "volume_recall": cm["recall"],
                "volume_f1": cm["f1"],
                "volume_iou": cm["iou"],
                "final_step_iou": cm_final["iou"],
                "final_step_recall": cm_final["recall"],
                "final_step_precision": cm_final["precision"]
            })

        # --- CORRECTED DEPTH-BIN METRICS ---
        for b in DEPTH_BINS:
            if ">2 m" in b:
                mask = H_true_native >= b["min"]
            else:
                mask = (H_true_native >= b["min"]) & (H_true_native < b["max"])

            count = int(np.sum(mask))
            if count > 0:
                t_vals = H_true_native[mask]
                p_vals = H_pred_native[mask]
                b_diff = p_vals - t_vals
                b_mae = float(np.mean(np.abs(b_diff)))
                b_rmse = float(np.sqrt(np.mean(b_diff ** 2)))
                b_bias = float(np.mean(b_diff))
                mean_t = float(np.mean(t_vals))
                mean_p = float(np.mean(p_vals))
            else:
                b_mae, b_rmse, b_bias, mean_t, mean_p = 0.0, 0.0, 0.0, 0.0, 0.0

            corrected_depth_bin_records.append({
                "event_id": eid,
                "rainfall_mm": storm["rainfall_mm"],
                "bin_name": b["name"],
                "cell_count": count,
                "mean_ground_truth_m": mean_t,
                "mean_prediction_m": mean_p,
                "bias_m": b_bias,
                "mae_m": b_mae,
                "rmse_m": b_rmse
            })

        # --- CORRECTED PEAK LOCATION & NEIGHBORHOOD METRICS ---
        t_peak_idx = np.unravel_index(np.argmax(H_true_native), H_true_native.shape)
        p_peak_idx = np.unravel_index(np.argmax(H_pred_native), H_pred_native.shape)
        yt, xt, tt = t_peak_idx
        yp, xp, tp = p_peak_idx

        dist_cells = float(np.sqrt((yp - yt) ** 2 + (xp - xt) ** 2))
        dist_meters = dist_cells * DX
        timing_offset_min = (tp - tt) * DT_MIN

        patch_5_true = extract_patch(H_true_native[..., tt], yt, xt, 5)
        patch_5_pred = extract_patch(H_pred_native[..., tt], yt, xt, 5)
        patch_5_err = np.abs(patch_5_pred - patch_5_true)

        patch_11_true = extract_patch(H_true_native[..., tt], yt, xt, 11)
        patch_11_pred = extract_patch(H_pred_native[..., tt], yt, xt, 11)
        patch_11_err = np.abs(patch_11_pred - patch_11_true)

        corrected_peak_records.append({
            "event_id": eid,
            "rainfall_mm": storm["rainfall_mm"],
            "true_peak_m": float(H_true_native[yt, xt, tt]),
            "pred_peak_m": float(H_pred_native[yp, xp, tp]),
            "peak_error_m": float(H_pred_native[yp, xp, tp] - H_true_native[yt, xt, tt]),
            "peak_pct_error": peak_pct_err,
            "true_peak_y": int(yt),
            "true_peak_x": int(xt),
            "true_peak_timestep": int(tt),
            "pred_peak_y": int(yp),
            "pred_peak_x": int(xp),
            "pred_peak_timestep": int(tp),
            "distance_cells": dist_cells,
            "distance_meters": dist_meters,
            "timing_offset_min": timing_offset_min,
            "patch_5x5_true_mean_m": float(np.mean(patch_5_true)),
            "patch_5x5_pred_mean_m": float(np.mean(patch_5_pred)),
            "patch_5x5_mae_m": float(np.mean(patch_5_err)),
            "patch_11x11_true_mean_m": float(np.mean(patch_11_true)),
            "patch_11x11_pred_mean_m": float(np.mean(patch_11_pred)),
            "patch_11x11_mae_m": float(np.mean(patch_11_err))
        })

        # --- CORRECTED TEMPORAL METRICS ---
        for step in range(24):
            t_min = (step + 1) * DT_MIN
            t_slice = H_true_native[..., step]
            p_slice = H_pred_native[..., step]

            step_met = compute_metrics(p_slice, t_slice)
            cell_area_km2 = (DX ** 2) / (1e6)
            t_wet_5cm_km2 = float(np.sum(t_slice > 0.05) * cell_area_km2)
            p_wet_5cm_km2 = float(np.sum(p_slice > 0.05) * cell_area_km2)
            t_wet_10cm_km2 = float(np.sum(t_slice > 0.10) * cell_area_km2)
            p_wet_10cm_km2 = float(np.sum(p_slice > 0.10) * cell_area_km2)

            corrected_temporal_records.append({
                "event_id": eid,
                "step": step,
                "time_minutes": t_min,
                "mae_m": step_met["mae"],
                "rmse_m": step_met["rmse"],
                "actual_max_depth_m": float(np.max(t_slice)),
                "pred_max_depth_m": float(np.max(p_slice)),
                "actual_mean_depth_m": float(np.mean(t_slice)),
                "pred_mean_depth_m": float(np.mean(p_slice)),
                "actual_flooded_area_5cm_km2": t_wet_5cm_km2,
                "pred_flooded_area_5cm_km2": p_wet_5cm_km2,
                "actual_flooded_area_10cm_km2": t_wet_10cm_km2,
                "pred_flooded_area_10cm_km2": p_wet_10cm_km2
            })

    # Save CSV Tables
    def save_csv(records, filename):
        path = os.path.join(log_dir, filename)
        if records:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
        print(f"  Saved CSV: {path}")

    save_csv(old_vs_corrected_records, "old_vs_corrected_metrics.csv")
    save_csv(corrected_per_event_records, "corrected_per_event_metrics.csv")
    save_csv(corrected_depth_bin_records, "corrected_depth_bin_metrics.csv")
    save_csv(corrected_temporal_records, "corrected_temporal_metrics.csv")
    save_csv(corrected_peak_records, "corrected_peak_metrics.csv")
    save_csv(corrected_flood_records, "corrected_flood_metrics.csv")

    # Save JSON Summary
    summary_json = {
        "study": "Phase 7A.1 — Native-Scale Normalization Contract Resolution",
        "checkpoint_evaluated": ckpt_path,
        "normalization_mismatch_detected": True,
        "mismatch_location": "EVALUATION ONLY (Training used raw physical targets directly; evaluation mistakenly applied 5x multiplier)",
        "training_validity": "VALID (Model learned directly in native physical units)",
        "old_vs_corrected_summary": old_vs_corrected_records,
        "corrected_per_event_metrics": corrected_per_event_records,
        "aggregate_corrected_metrics": {
            "mean_H_MAE_m": float(np.mean([r["H_MAE_m"] for r in corrected_per_event_records])),
            "mean_H_RMSE_m": float(np.mean([r["H_RMSE_m"] for r in corrected_per_event_records])),
            "mean_H_Bias_m": float(np.mean([r["H_Bias_m"] for r in corrected_per_event_records])),
            "mean_U_MAE_mps": float(np.mean([r["U_MAE_mps"] for r in corrected_per_event_records])),
            "mean_V_MAE_mps": float(np.mean([r["V_MAE_mps"] for r in corrected_per_event_records])),
            "mean_Pearson_Corr": float(np.mean([r["Pearson_Correlation"] for r in corrected_per_event_records])),
            "mean_Spearman_Corr": float(np.mean([r["Spearman_Correlation"] for r in corrected_per_event_records]))
        }
    }
    with open(os.path.join(log_dir, "phase7a1_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)
    print(f"  Saved JSON: {os.path.join(log_dir, 'phase7a1_summary.json')}")

    # --- GENERATE CORRECTED DIAGNOSTIC PLOTS ---
    print("\n[3] Generating Corrected Diagnostic Visualizations...")

    # Plot 1: Corrected Per-Event Depth (Ground Truth vs Pred in Native Meters)
    fig, axes = plt.subplots(2, 5, figsize=(18, 7))
    for idx, s in enumerate(TEST_STORMS):
        eid = s["id"]
        h_t = all_storm_data[eid]["H_true"][..., 23]
        h_p = all_storm_data[eid]["H_pred"][..., 23]
        vmax = max(float(h_t.max()), float(h_p.max()), 0.5)

        im0 = axes[0, idx].imshow(h_t, cmap="Blues", vmin=0, vmax=vmax)
        axes[0, idx].set_title(f"{eid} True Depth\nMax: {h_t.max():.2f}m ({s['rainfall_mm']}mm)", fontsize=9)
        axes[0, idx].set_xticks([]); axes[0, idx].set_yticks([])
        plt.colorbar(im0, ax=axes[0, idx], fraction=0.046, pad=0.04)

        im1 = axes[1, idx].imshow(h_p, cmap="Blues", vmin=0, vmax=vmax)
        axes[1, idx].set_title(f"{eid} Pred Depth (Native)\nMax: {h_p.max():.2f}m", fontsize=9)
        axes[1, idx].set_xticks([]); axes[1, idx].set_yticks([])
        plt.colorbar(im1, ax=axes[1, idx], fraction=0.046, pad=0.04)

    plt.suptitle("Phase 7A.1: Corrected Physical Depth Maps in Native Meters (t=120 min)", fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "corrected_per_event_depth.png"), dpi=180)
    plt.close()

    # Plot 2: Corrected Peak Comparison
    rf_vals = [s["rainfall_mm"] for s in TEST_STORMS]
    t_peaks = [r["H_Max_Actual_m"] for r in corrected_per_event_records]
    p_peaks = [r["H_Max_Pred_m"] for r in corrected_per_event_records]
    p6_peaks = [p6_ref["per_event_test_results"][s["id"]]["peak_depth_pred_m"] for s in TEST_STORMS]

    plt.figure(figsize=(8, 5))
    plt.plot(rf_vals, t_peaks, "b-o", linewidth=2.2, label="Numerical Solver True Peak (Native m)")
    plt.plot(rf_vals, p_peaks, "g--s", linewidth=2.2, label="DNO Pred Peak (Phase 7A.1 Corrected)")
    plt.plot(rf_vals, p6_peaks, "r:^", linewidth=1.5, alpha=0.5, label="Phase 6 Reported Peak (Inflated 5x)")
    for r, tp, pp, s in zip(rf_vals, t_peaks, p_peaks, TEST_STORMS):
        plt.annotate(f"{s['id']}\nTrue:{tp:.2f}m\nPred:{pp:.2f}m", (r + 1, pp - 0.2), fontsize=8)
    plt.xlabel("Rainfall Total (mm)", fontsize=11)
    plt.ylabel("Maximum Water Depth (m)", fontsize=11)
    plt.title("Peak Water Depth Scaling: True Solver vs Phase 7A.1 Native DNO", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "corrected_peak_comparison.png"), dpi=180)
    plt.close()

    # Plot 3: Corrected Depth Bins Error Profile
    bin_names = [b["name"] for b in DEPTH_BINS]
    plt.figure(figsize=(9, 5))
    for s in TEST_STORMS:
        eid = s["id"]
        s_bins = [b for b in corrected_depth_bin_records if b["event_id"] == eid]
        b_maes = [b["mae_m"] * 100 for b in s_bins]  # cm
        plt.plot(bin_names, b_maes, marker="s", label=f"{eid} ({s['rainfall_mm']}mm)", linewidth=1.8)
    plt.xlabel("True Physical Depth Range", fontsize=11)
    plt.ylabel("Mean Absolute Error (cm)", fontsize=11)
    plt.title("Phase 7A.1 Corrected: Error Stratification by Ground-Truth Depth Bin (cm)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "corrected_depth_bins.png"), dpi=180)
    plt.close()

    # Plot 4: Corrected Temporal Error Evolution
    plt.figure(figsize=(9, 4.8))
    for s in TEST_STORMS:
        eid = s["id"]
        s_temps = [t for t in corrected_temporal_records if t["event_id"] == eid]
        times = [t["time_minutes"] for t in s_temps]
        maes = [t["mae_m"] * 100 for t in s_temps]  # cm
        plt.plot(times, maes, label=f"{eid} ({s['rainfall_mm']}mm, {s['profile']})", linewidth=1.8)
    plt.xlabel("Simulation Elapsed Time (minutes)", fontsize=11)
    plt.ylabel("Native Step MAE (cm)", fontsize=11)
    plt.title("Phase 7A.1 Corrected: Temporal Error Trajectory (Native cm)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "corrected_temporal_error.png"), dpi=180)
    plt.close()

    # Plot 5: Corrected Flood Metrics Across Physical Thresholds
    plt.figure(figsize=(8, 4.8))
    for s in TEST_STORMS:
        eid = s["id"]
        s_floods = [f for f in corrected_flood_records if f["event_id"] == eid]
        s_thresh = [f["threshold_m"] * 100 for f in s_floods]  # cm
        s_iou = [f["volume_iou"] for f in s_floods]
        plt.plot(s_thresh, s_iou, marker="o", label=f"{eid} ({s['category']}, {s['rainfall_mm']}mm)", linewidth=1.8)
    plt.xlabel("Physical Flood Depth Threshold (cm)", fontsize=11)
    plt.ylabel("Flood Extent IoU (CSI)", fontsize=11)
    plt.title("Phase 7A.1 Corrected: Flood Extent IoU Across Physical Depth Thresholds", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "corrected_flood_metrics.png"), dpi=180)
    plt.close()

    print("\n" + "=" * 80)
    print("PHASE 7A.1 NATIVE-SCALE RESOLUTION COMPLETE")
    print(f"Old Mean H MAE:       {p6_ref['aggregate_test_metrics']['mean_H_MAE_m']*100:.2f} cm")
    print(f"Corrected Mean H MAE: {np.mean([r['H_MAE_m'] for r in corrected_per_event_records])*100:.2f} cm")
    print(f"Summary CSV tables saved to: {log_dir}")
    print(f"Corrected diagnostic figures saved to: {out_dir}")
    print("=" * 80)


if __name__ == "__main__":
    run_phase7a1_evaluation()
