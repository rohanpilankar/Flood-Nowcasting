"""
FloodWatch AI — Phase 7A: Chennai DNO Comprehensive Error Analysis & Model Diagnostic Engine
SIH26085 — Urban Flood Nowcasting System

Strict Rules:
1. READ-ONLY on Phase 6 checkpoint: models/urban_flood_dno/checkpoints/chennai_phase6/best_dno_checkpoint.pt
2. Evaluate strictly the 5 protected Phase 6 test storms: storm_007, storm_011, storm_016, storm_024, storm_028.
3. DO NOT modify any production files, XGBoost models, backend APIs, or frontend components.
4. DO NOT retrain or alter the model or dataset.
"""

import os
import sys
import time
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

# Test storms configuration
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
DX = 78.125  # Grid cell spatial resolution in meters
DT_MIN = 5.0  # Timestep in minutes


def setup_directories():
    base_log = os.path.join(REPO_ROOT, "models", "urban_flood_dno", "logs", "chennai_phase7a")
    base_out = os.path.join(REPO_ROOT, "outputs", "chennai_dno", "phase7a_error_analysis")
    subdirs = [
        base_log,
        os.path.join(base_out, "overview"),
        os.path.join(base_out, "per_event"),
        os.path.join(base_out, "depth_bins"),
        os.path.join(base_out, "temporal"),
        os.path.join(base_out, "peak_analysis"),
        os.path.join(base_out, "flood_masks"),
        os.path.join(base_out, "error_maps")
    ]
    for d in subdirs:
        os.makedirs(d, exist_ok=True)
    return base_log, base_out


def compute_metrics(pred: np.ndarray, true: np.ndarray):
    """Computes comprehensive error metrics for array volume or slice."""
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
    """Computes binary flood mask metrics: TP, TN, FP, FN, Precision, Recall, F1, IoU."""
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
    """Extracts a 2D square neighborhood patch centered on (y, x) with boundary padding."""
    pad = size // 2
    padded = np.pad(arr, pad, mode="edge")
    return padded[y : y + size, x : x + size]


def run_phase7a_diagnostic():
    print("=" * 80)
    print("FLOODWATCH AI — PHASE 7A: CHENNAI DNO COMPREHENSIVE ERROR ANALYSIS")
    print("=" * 80)

    log_dir, out_dir = setup_directories()
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"[1] Hardware Verified: {torch.cuda.get_device_name(device)} ({device})")

    # Load DEM
    dem_path = os.path.join(REPO_ROOT, "Data", "dno", "chennai", "processed", "pilot_adyar_velachery_dem_128x128.npy")
    dem = np.load(dem_path) if os.path.exists(dem_path) else np.zeros((128, 128))

    # Load Model Checkpoint
    ckpt_path = os.path.join(REPO_ROOT, "models", "urban_flood_dno", "checkpoints", "chennai_phase6", "best_dno_checkpoint.pt")
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Missing Phase 6 checkpoint: {ckpt_path}")

    print(f"[2] Loading Phase 6 Checkpoint: {ckpt_path}")
    checkpoint = torch.load(ckpt_path, map_location=device)
    model = DNO(
        num_channels=5,
        width=10,
        initial_step=1,
        pad=0,
        factor=1
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Load Phase 6 Reference Summary for Reproduction Check
    p6_summary_path = os.path.join(REPO_ROOT, "models", "urban_flood_dno", "logs", "chennai_phase6", "test_summary.json")
    with open(p6_summary_path, "r", encoding="utf-8") as f:
        p6_ref = json.load(f)

    tensor_dir = os.path.join(REPO_ROOT, "Data", "dno", "chennai", "storm_library", "tensors")

    print("\n[3] Running Reproduction Check & In-Depth Diagnostics...")
    reproduction_ok = True
    per_event_records = []
    depth_bin_records = []
    temporal_records = []
    peak_records = []
    flood_records = []
    normalization_checks = []

    all_storm_data = {}

    for storm in TEST_STORMS:
        eid = storm["id"]
        x_path = os.path.join(tensor_dir, f"{eid}_input_tensor.pt")
        y_path = os.path.join(tensor_dir, f"{eid}_target_tensor.pt")

        x_raw = torch.load(x_path, map_location=device)
        y_raw = torch.load(y_path, map_location=device)

        # Normalization range checks
        norm_info = {
            "event_id": eid,
            "x_min": float(x_raw.min()),
            "x_max": float(x_raw.max()),
            "y_min": float(y_raw.min()),
            "y_max": float(y_raw.max()),
            "p_channel_min": float(x_raw[..., 3].min()),
            "p_channel_max": float(x_raw[..., 3].max()),
            "z_channel_min": float(x_raw[..., 4].min()),
            "z_channel_max": float(x_raw[..., 4].max())
        }

        # Model Inference
        with torch.no_grad():
            pred_raw = model(x_raw)

        norm_info["pred_raw_min"] = float(pred_raw.min())
        norm_info["pred_raw_max"] = float(pred_raw.max())
        norm_info["pred_h_raw_min"] = float(pred_raw[..., 0].min())
        norm_info["pred_h_raw_max"] = float(pred_raw[..., 0].max())
        normalization_checks.append(norm_info)

        # Denormalize to Physical Units
        # Channels: 0:H (scale 5.0m), 1:U (scale 5.0m/s), 2:V (scale 5.0m/s)
        pred_np = pred_raw.squeeze(0).cpu().numpy()
        true_np = y_raw.squeeze(0).cpu().numpy()

        H_pred = np.maximum(pred_np[..., 0] * 5.0, 0.0)  # Physical depth [128, 128, 24]
        U_pred = pred_np[..., 1] * 5.0                   # U velocity [128, 128, 24]
        V_pred = pred_np[..., 2] * 5.0                   # V velocity [128, 128, 24]

        H_true = true_np[..., 0] * 5.0                   # True depth [128, 128, 24]
        U_true = true_np[..., 1] * 5.0                   # True U [128, 128, 24]
        V_true = true_np[..., 2] * 5.0                   # True V [128, 128, 24]

        all_storm_data[eid] = {
            "H_pred": H_pred,
            "H_true": H_true,
            "U_pred": U_pred,
            "U_true": U_true,
            "V_pred": V_pred,
            "V_true": V_true,
            "meta": storm
        }

        # --- A. REPRODUCTION VERIFICATION ---
        h_met = compute_metrics(H_pred, H_true)
        ref_h_mae = p6_ref["per_event_test_results"][eid]["H_metrics"]["mae"]
        ref_h_rmse = p6_ref["per_event_test_results"][eid]["H_metrics"]["rmse"]
        ref_h_corr = p6_ref["per_event_test_results"][eid]["H_metrics"]["corr"]

        mae_diff = abs(h_met["mae"] - ref_h_mae)
        rmse_diff = abs(h_met["rmse"] - ref_h_rmse)
        corr_diff = abs(h_met["pearson"] - ref_h_corr)

        if mae_diff > 1e-4 or rmse_diff > 1e-4 or corr_diff > 1e-4:
            reproduction_ok = False
            print(f"  [WARNING] Reproduction mismatch on {eid}: diff_mae={mae_diff:.6f}, diff_corr={corr_diff:.6f}")
        else:
            print(f"  [PASS] {eid} reproduced: H MAE={h_met['mae']:.4f}m, RMSE={h_met['rmse']:.4f}m, r={h_met['pearson']:.4f}")

        # --- B. PER-EVENT IN-DEPTH METRICS ---
        u_met = compute_metrics(U_pred, U_true)
        v_met = compute_metrics(V_pred, V_true)

        # Global vs Interior Metrics
        H_true_interior = H_true[:, :127, :]
        H_pred_interior = H_pred[:, :127, :]
        h_int_met = compute_metrics(H_pred_interior, H_true_interior)

        true_global_peak = float(np.max(H_true))
        pred_global_peak = float(np.max(H_pred))
        true_interior_peak = float(np.max(H_true_interior))
        pred_interior_peak = float(np.max(H_pred_interior))

        per_event_records.append({
            "event_id": eid,
            "rainfall_mm": storm["rainfall_mm"],
            "severity_category": storm["category"],
            "profile": storm["profile"],
            "peak_intensity_mm_hr": storm["peak_intensity"],
            "H_MAE_m": h_met["mae"],
            "H_RMSE_m": h_met["rmse"],
            "H_Bias_m": h_met["bias"],
            "H_Max_Actual_m": true_global_peak,
            "H_Max_Pred_m": pred_global_peak,
            "Peak_Error_m": pred_global_peak - true_global_peak,
            "Peak_Pct_Error": (pred_global_peak - true_global_peak) / true_global_peak * 100.0,
            "H_Interior_MAE_m": h_int_met["mae"],
            "H_Interior_Max_Actual_m": true_interior_peak,
            "H_Interior_Max_Pred_m": pred_interior_peak,
            "H_Interior_Peak_Error_m": pred_interior_peak - true_interior_peak,
            "U_MAE_mps": u_met["mae"],
            "U_RMSE_mps": u_met["rmse"],
            "U_Bias_mps": u_met["bias"],
            "V_MAE_mps": v_met["mae"],
            "V_RMSE_mps": v_met["rmse"],
            "V_Bias_mps": v_met["bias"],
            "Pearson_Correlation": h_met["pearson"],
            "Spearman_Correlation": h_met["spearman"]
        })

        # --- C. FLOOD EXTENT ACROSS THRESHOLDS ---
        for thresh in FLOOD_THRESHOLDS:
            cm = compute_confusion_matrix(H_pred, H_true, thresh)
            cm_final = compute_confusion_matrix(H_pred[..., -1], H_true[..., -1], thresh)
            flood_records.append({
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

        # --- D. DEPTH-BIN ERROR ANALYSIS ---
        for b in DEPTH_BINS:
            if ">2 m" in b:
                mask = H_true >= b["min"]
            else:
                mask = (H_true >= b["min"]) & (H_true < b["max"])

            count = int(np.sum(mask))
            if count > 0:
                t_vals = H_true[mask]
                p_vals = H_pred[mask]
                b_diff = p_vals - t_vals
                b_mae = float(np.mean(np.abs(b_diff)))
                b_rmse = float(np.sqrt(np.mean(b_diff ** 2)))
                b_bias = float(np.mean(b_diff))
                mean_t = float(np.mean(t_vals))
                mean_p = float(np.mean(p_vals))
            else:
                b_mae = 0.0
                b_rmse = 0.0
                b_bias = 0.0
                mean_t = 0.0
                mean_p = 0.0

            depth_bin_records.append({
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

        # --- E. PEAK LOCATION & NEIGHBORHOOD ANALYSIS ---
        # Peak across full volume and at final step
        # True Peak
        t_peak_idx = np.unravel_index(np.argmax(H_true), H_true.shape)
        # Pred Peak
        p_peak_idx = np.unravel_index(np.argmax(H_pred), H_pred.shape)

        y_t, x_t, t_t = t_peak_idx
        y_p, x_p, t_p = p_peak_idx

        dist_cells = float(np.sqrt((y_p - y_t) ** 2 + (x_p - x_t) ** 2))
        dist_meters = dist_cells * DX
        timing_offset_min = (t_p - t_t) * DT_MIN

        # Neighborhood analysis around True Peak at t_t
        patch_5_true = extract_patch(H_true[..., t_t], y_t, x_t, 5)
        patch_5_pred = extract_patch(H_pred[..., t_t], y_t, x_t, 5)
        patch_5_err = np.abs(patch_5_pred - patch_5_true)

        patch_11_true = extract_patch(H_true[..., t_t], y_t, x_t, 11)
        patch_11_pred = extract_patch(H_pred[..., t_t], y_t, x_t, 11)
        patch_11_err = np.abs(patch_11_pred - patch_11_true)

        # Hotspot Analysis: Top error coordinates at final timestep (t=23)
        final_err = np.abs(H_pred[..., 23] - H_true[..., 23])
        top_err_indices = np.argsort(final_err.flatten())[::-1][:3]
        hotspots = []
        for idx in top_err_indices:
            hy, hx = np.unravel_index(idx, (128, 128))
            hotspots.append({
                "y": int(hy),
                "x": int(hx),
                "err": float(final_err[hy, hx]),
                "true_h": float(H_true[hy, hx, 23]),
                "pred_h": float(H_pred[hy, hx, 23]),
                "dem_z": float(dem[hy, hx])
            })

        peak_records.append({
            "event_id": eid,
            "rainfall_mm": storm["rainfall_mm"],
            "true_peak_m": float(H_true[y_t, x_t, t_t]),
            "pred_peak_m": float(H_pred[y_p, x_p, t_p]),
            "peak_error_m": float(H_pred[y_p, x_p, t_p] - H_true[y_t, x_t, t_t]),
            "true_peak_y": int(y_t),
            "true_peak_x": int(x_t),
            "true_peak_timestep": int(t_t),
            "pred_peak_y": int(y_p),
            "pred_peak_x": int(x_p),
            "pred_peak_timestep": int(t_p),
            "distance_cells": dist_cells,
            "distance_meters": dist_meters,
            "timing_offset_min": timing_offset_min,
            "patch_5x5_true_mean_m": float(np.mean(patch_5_true)),
            "patch_5x5_pred_mean_m": float(np.mean(patch_5_pred)),
            "patch_5x5_mae_m": float(np.mean(patch_5_err)),
            "patch_11x11_true_mean_m": float(np.mean(patch_11_true)),
            "patch_11x11_pred_mean_m": float(np.mean(patch_11_pred)),
            "patch_11x11_mae_m": float(np.mean(patch_11_err)),
            "top_hotspot_y": hotspots[0]["y"],
            "top_hotspot_x": hotspots[0]["x"],
            "top_hotspot_err_m": hotspots[0]["err"],
            "top_hotspot_true_m": hotspots[0]["true_h"],
            "top_hotspot_pred_m": hotspots[0]["pred_h"],
            "top_hotspot_dem_m": hotspots[0]["dem_z"]
        })

        # --- F. TEMPORAL DYNAMICS ---
        for step in range(24):
            t_min = (step + 1) * DT_MIN
            t_slice = H_true[..., step]
            p_slice = H_pred[..., step]

            step_met = compute_metrics(p_slice, t_slice)
            t_max_step = float(np.max(t_slice))
            p_max_step = float(np.max(p_slice))
            t_mean_step = float(np.mean(t_slice))
            p_mean_step = float(np.mean(p_slice))

            # Flooded area in km2
            cell_area_km2 = (DX ** 2) / (1e6)
            t_wet_5cm_km2 = float(np.sum(t_slice > 0.05) * cell_area_km2)
            p_wet_5cm_km2 = float(np.sum(p_slice > 0.05) * cell_area_km2)
            t_wet_10cm_km2 = float(np.sum(t_slice > 0.10) * cell_area_km2)
            p_wet_10cm_km2 = float(np.sum(p_slice > 0.10) * cell_area_km2)

            temporal_records.append({
                "event_id": eid,
                "step": step,
                "time_minutes": t_min,
                "mae_m": step_met["mae"],
                "rmse_m": step_met["rmse"],
                "actual_max_depth_m": t_max_step,
                "pred_max_depth_m": p_max_step,
                "actual_mean_depth_m": t_mean_step,
                "pred_mean_depth_m": p_mean_step,
                "actual_flooded_area_5cm_km2": t_wet_5cm_km2,
                "pred_flooded_area_5cm_km2": p_wet_5cm_km2,
                "actual_flooded_area_10cm_km2": t_wet_10cm_km2,
                "pred_flooded_area_10cm_km2": p_wet_10cm_km2
            })

    # --- SAVE CSV TABLES ---
    def save_csv(records, filename):
        path = os.path.join(log_dir, filename)
        if records:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
        print(f"  Saved CSV: {path}")

    save_csv(per_event_records, "per_event_metrics.csv")
    save_csv(depth_bin_records, "depth_bin_metrics.csv")
    save_csv(temporal_records, "temporal_metrics.csv")
    save_csv(peak_records, "peak_metrics.csv")
    save_csv(flood_records, "flood_metrics.csv")

    # --- SAVE JSON SUMMARY ---
    summary_json = {
        "experiment": "Phase 7A — Comprehensive DNO Error Analysis",
        "phase6_reproduction": "PASS" if reproduction_ok else "DISCREPANCY_DETECTED",
        "reproduction_verified": reproduction_ok,
        "normalization_checks": normalization_checks,
        "per_event_summary": per_event_records,
        "depth_bins_summary": depth_bin_records,
        "peak_summary": peak_records,
        "flood_extent_summary": flood_records
    }
    json_path = os.path.join(log_dir, "phase7a_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)
    print(f"  Saved Summary JSON: {json_path}")

    # --- GENERATE COMPREHENSIVE VISUAL DIAGNOSTIC PACKAGE ---
    print("\n[4] Generating Phase 7A Visual Diagnostic Package...")

    # 1. Per-Storm Maps & Figures
    for storm in TEST_STORMS:
        eid = storm["id"]
        data = all_storm_data[eid]
        H_true = data["H_true"]
        H_pred = data["H_pred"]

        # Final timestep (t=23)
        t_idx = 23
        h_t = H_true[..., t_idx]
        h_p = H_pred[..., t_idx]
        abs_err = np.abs(h_p - h_t)
        signed_err = h_p - h_t

        vmax_depth = max(float(h_t.max()), float(h_p.max()), 0.5)

        # 1A. Ground Truth Depth
        plt.figure(figsize=(6, 5))
        plt.imshow(h_t, cmap="Blues", vmin=0, vmax=vmax_depth)
        plt.title(f"{eid.upper()} — Ground Truth Depth (t=120m)\nMax: {h_t.max():.2f}m | Rainfall: {storm['rainfall_mm']}mm", fontsize=10)
        plt.colorbar(label="Water Depth (m)", fraction=0.046, pad=0.04)
        plt.xticks([]); plt.yticks([])
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "per_event", f"ground_truth_depth_{eid}.png"), dpi=180)
        plt.close()

        # 1B. DNO Prediction
        plt.figure(figsize=(6, 5))
        plt.imshow(h_p, cmap="Blues", vmin=0, vmax=vmax_depth)
        plt.title(f"{eid.upper()} — DNO Prediction (t=120m)\nMax: {h_p.max():.2f}m", fontsize=10)
        plt.colorbar(label="Water Depth (m)", fraction=0.046, pad=0.04)
        plt.xticks([]); plt.yticks([])
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "per_event", f"dno_prediction_{eid}.png"), dpi=180)
        plt.close()

        # 1C. Absolute Error Map
        plt.figure(figsize=(6, 5))
        plt.imshow(abs_err, cmap="Reds", vmin=0, vmax=max(float(abs_err.max()), 0.1))
        plt.title(f"{eid.upper()} — Absolute Error |H_pred - H_true|\nMAE: {abs_err.mean():.3f}m | Max: {abs_err.max():.2f}m", fontsize=10)
        plt.colorbar(label="Absolute Error (m)", fraction=0.046, pad=0.04)
        plt.xticks([]); plt.yticks([])
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "per_event", f"absolute_error_{eid}.png"), dpi=180)
        plt.savefig(os.path.join(out_dir, "error_maps", f"error_map_{eid}.png"), dpi=180)
        plt.close()

        # 1D. Signed Error Map
        vlim_signed = max(float(np.abs(signed_err).max()), 0.2)
        plt.figure(figsize=(6, 5))
        plt.imshow(signed_err, cmap="coolwarm", vmin=-vlim_signed, vmax=vlim_signed)
        plt.title(f"{eid.upper()} — Signed Error (H_pred - H_true)\nBlue = Underpredict, Red = Overpredict", fontsize=10)
        plt.colorbar(label="Signed Error (m)", fraction=0.046, pad=0.04)
        plt.xticks([]); plt.yticks([])
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "per_event", f"signed_error_{eid}.png"), dpi=180)
        plt.close()

        # 1E. Flood Mask 5cm
        fig, axes = plt.subplots(1, 3, figsize=(13, 4))
        axes[0].imshow(h_t > 0.05, cmap="Blues")
        axes[0].set_title(f"True Mask >5cm ({np.sum(h_t>0.05)} cells)")
        axes[1].imshow(h_p > 0.05, cmap="Blues")
        axes[1].set_title(f"Pred Mask >5cm ({np.sum(h_p>0.05)} cells)")
        # Overlap mask: Green=TP, Red=FP, Blue=FN
        overlap_rgb = np.ones((128, 128, 3))
        tp_mask = (h_p > 0.05) & (h_t > 0.05)
        fp_mask = (h_p > 0.05) & (~(h_t > 0.05))
        fn_mask = (~(h_p > 0.05)) & (h_t > 0.05)
        overlap_rgb[tp_mask] = [0.1, 0.8, 0.2]   # Green (Hit)
        overlap_rgb[fp_mask] = [0.9, 0.2, 0.2]   # Red (False Alarm)
        overlap_rgb[fn_mask] = [0.2, 0.4, 0.9]   # Blue (Miss)
        axes[2].imshow(overlap_rgb)
        axes[2].set_title(f"Overlap (Green:TP, Red:FP, Blue:FN)\nIoU: {np.sum(tp_mask)/(np.sum(tp_mask|fp_mask|fn_mask)):.3f}")
        for ax in axes: ax.set_xticks([]); ax.set_yticks([])
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "per_event", f"flood_mask_5cm_{eid}.png"), dpi=180)
        plt.savefig(os.path.join(out_dir, "flood_masks", f"flood_mask_5cm_{eid}.png"), dpi=180)
        plt.close()

        # 1F. Flood Mask 10cm
        fig, axes = plt.subplots(1, 3, figsize=(13, 4))
        axes[0].imshow(h_t > 0.10, cmap="Blues")
        axes[0].set_title(f"True Mask >10cm ({np.sum(h_t>0.10)} cells)")
        axes[1].imshow(h_p > 0.10, cmap="Blues")
        axes[1].set_title(f"Pred Mask >10cm ({np.sum(h_p>0.10)} cells)")
        overlap_rgb10 = np.ones((128, 128, 3))
        tp_mask10 = (h_p > 0.10) & (h_t > 0.10)
        fp_mask10 = (h_p > 0.10) & (~(h_t > 0.10))
        fn_mask10 = (~(h_p > 0.10)) & (h_t > 0.10)
        overlap_rgb10[tp_mask10] = [0.1, 0.8, 0.2]
        overlap_rgb10[fp_mask10] = [0.9, 0.2, 0.2]
        overlap_rgb10[fn_mask10] = [0.2, 0.4, 0.9]
        axes[2].imshow(overlap_rgb10)
        axes[2].set_title(f"Overlap >10cm (Green:TP, Red:FP, Blue:FN)\nIoU: {np.sum(tp_mask10)/(np.sum(tp_mask10|fp_mask10|fn_mask10)):.3f}")
        for ax in axes: ax.set_xticks([]); ax.set_yticks([])
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "per_event", f"flood_mask_10cm_{eid}.png"), dpi=180)
        plt.savefig(os.path.join(out_dir, "flood_masks", f"flood_mask_10cm_{eid}.png"), dpi=180)
        plt.close()

        # 1G. Peak Comparison Spatial Zoom
        p_rec = [p for p in peak_records if p["event_id"] == eid][0]
        yt, xt = p_rec["true_peak_y"], p_rec["true_peak_x"]
        yp, xp = p_rec["pred_peak_y"], p_rec["pred_peak_x"]

        fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
        axes[0].imshow(h_t, cmap="Blues", vmin=0, vmax=vmax_depth)
        axes[0].scatter([xt], [yt], color="red", marker="x", s=100, label=f"True Peak: ({yt},{xt})\n{p_rec['true_peak_m']:.2f}m")
        axes[0].legend(loc="upper left", fontsize=9)
        axes[0].set_title(f"True Depth & Peak Location")

        axes[1].imshow(h_p, cmap="Blues", vmin=0, vmax=vmax_depth)
        axes[1].scatter([xp], [yp], color="orange", marker="o", s=80, label=f"Pred Peak: ({yp},{xp})\n{p_rec['pred_peak_m']:.2f}m")
        axes[1].scatter([xt], [yt], color="red", marker="x", s=100, label="True Peak Loc")
        axes[1].legend(loc="upper left", fontsize=9)
        axes[1].set_title(f"Pred Depth & Peak Offset\nOffset: {p_rec['distance_meters']:.1f} m")

        for ax in axes: ax.set_xticks([]); ax.set_yticks([])
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "per_event", f"peak_comparison_{eid}.png"), dpi=180)
        plt.close()

        # 1H. Comprehensive Hydrograph
        time_arr = np.arange(1, 25) * DT_MIN
        t_max_s = np.max(H_true, axis=(0, 1))
        p_max_s = np.max(H_pred, axis=(0, 1))
        t_mean_s = np.mean(H_true, axis=(0, 1))
        p_mean_s = np.mean(H_pred, axis=(0, 1))

        fig, ax1 = plt.subplots(figsize=(9, 4.8))
        ax1.plot(time_arr, t_max_s, "b-o", label="True Domain Max H (m)", linewidth=2)
        ax1.plot(time_arr, p_max_s, "b--s", label="DNO Pred Max H (m)", linewidth=2)
        ax1.plot(time_arr, t_mean_s, "g-^", label="True Domain Mean H (m)", linewidth=1.5)
        ax1.plot(time_arr, p_mean_s, "g--v", label="DNO Pred Mean H (m)", linewidth=1.5)
        ax1.set_xlabel("Forecast Time (minutes)", fontsize=10)
        ax1.set_ylabel("Water Depth (m)", fontsize=10)
        ax1.set_title(f"{eid.upper()} ({storm['category']}, {storm['rainfall_mm']}mm) — Temporal Hydrograph\nPeak Err: {p_rec['peak_error_m']:+.2f}m ({p_rec['peak_error_m']/p_rec['true_peak_m']*100:+.1f}%)", fontsize=11)
        ax1.grid(True, linestyle="--", alpha=0.6)
        ax1.legend(loc="upper left")
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "per_event", f"hydrograph_{eid}.png"), dpi=180)
        plt.close()

    # 2. Overview Diagnostic Plots
    rf_vals = [s["rainfall_mm"] for s in TEST_STORMS]
    mae_vals = [p["H_MAE_m"] * 100.0 for p in per_event_records]  # cm
    corr_vals = [p["Pearson_Correlation"] for p in per_event_records]
    peak_err_vals = [p["Peak_Error_m"] for p in per_event_records]

    # 2A. MAE vs Rainfall
    plt.figure(figsize=(7, 4.5))
    plt.plot(rf_vals, mae_vals, "ro-", linewidth=2, markersize=8)
    for r, m, s in zip(rf_vals, mae_vals, TEST_STORMS):
        plt.annotate(f"{s['id']} ({m:.1f}cm)", (r + 1.5, m - 0.5), fontsize=9)
    plt.xlabel("Rainfall Total (mm)", fontsize=11)
    plt.ylabel("Water Depth MAE (cm)", fontsize=11)
    plt.title("Water Depth Error Scaling vs Rainfall Magnitude", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "overview", "mae_vs_rainfall.png"), dpi=180)
    plt.close()

    # 2B. Spatial Correlation vs Rainfall
    plt.figure(figsize=(7, 4.5))
    plt.plot(rf_vals, corr_vals, "bo-", linewidth=2, markersize=8)
    for r, c, s in zip(rf_vals, corr_vals, TEST_STORMS):
        plt.annotate(f"{s['id']} (r={c:.3f})", (r + 1.5, c - 0.015), fontsize=9)
    plt.xlabel("Rainfall Total (mm)", fontsize=11)
    plt.ylabel("Spatial Pearson Correlation (r)", fontsize=11)
    plt.title("Spatial Correlation Structure vs Rainfall Magnitude", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "overview", "spatial_correlation_vs_rainfall.png"), dpi=180)
    plt.close()

    # 2C. IoU Across Flood Thresholds
    plt.figure(figsize=(8, 4.8))
    for s in TEST_STORMS:
        eid = s["id"]
        s_floods = [f for f in flood_records if f["event_id"] == eid]
        s_thresh = [f["threshold_m"] * 100 for f in s_floods]  # cm
        s_iou = [f["volume_iou"] for f in s_floods]
        plt.plot(s_thresh, s_iou, marker="o", label=f"{eid} ({s['category']}, {s['rainfall_mm']}mm)", linewidth=1.8)
    plt.xlabel("Flood Threshold (cm)", fontsize=11)
    plt.ylabel("Flood Extent IoU (Critical Success Index)", fontsize=11)
    plt.title("Flood Extent IoU Degradation Across Inundation Thresholds", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "overview", "iou_across_thresholds.png"), dpi=180)
    plt.close()

    # 2D. Depth-Bin MAE across bins
    bin_names = [b["name"] for b in DEPTH_BINS]
    plt.figure(figsize=(9, 5))
    for s in TEST_STORMS:
        eid = s["id"]
        s_bins = [b for b in depth_bin_records if b["event_id"] == eid]
        b_maes = [b["mae_m"] for b in s_bins]
        plt.plot(bin_names, b_maes, marker="s", label=f"{eid} ({s['rainfall_mm']}mm)", linewidth=1.8)
    plt.xlabel("Ground-Truth Depth Range", fontsize=11)
    plt.ylabel("Mean Absolute Error (m)", fontsize=11)
    plt.title("Phase 7A: Error Stratification by Ground-Truth Water Depth Bin", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "overview", "depth_bin_mae.png"), dpi=180)
    plt.savefig(os.path.join(out_dir, "depth_bins", "binned_error_profiles.png"), dpi=180)
    plt.close()

    # 2E. Temporal MAE Evolution
    plt.figure(figsize=(9, 4.8))
    for s in TEST_STORMS:
        eid = s["id"]
        s_temps = [t for t in temporal_records if t["event_id"] == eid]
        times = [t["time_minutes"] for t in s_temps]
        maes = [t["mae_m"] * 100 for t in s_temps]
        plt.plot(times, maes, label=f"{eid} ({s['rainfall_mm']}mm, {s['profile']})", linewidth=1.8)
    plt.xlabel("Simulation Elapsed Time (minutes)", fontsize=11)
    plt.ylabel("Step MAE (cm)", fontsize=11)
    plt.title("Temporal Error Progression Across Forecast Horizon (T+0 to T+120 min)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "temporal", "temporal_mae_evolution.png"), dpi=180)
    plt.close()

    # 2F. Temporal Flooded Area Evolution (>5cm)
    plt.figure(figsize=(9, 4.8))
    for s in TEST_STORMS:
        eid = s["id"]
        s_temps = [t for t in temporal_records if t["event_id"] == eid]
        times = [t["time_minutes"] for t in s_temps]
        act_areas = [t["actual_flooded_area_5cm_km2"] for t in s_temps]
        pred_areas = [t["pred_flooded_area_5cm_km2"] for t in s_temps]
        line, = plt.plot(times, act_areas, linewidth=1.8, label=f"{eid} True Area")
        plt.plot(times, pred_areas, linestyle="--", color=line.get_color(), label=f"{eid} Pred Area")
    plt.xlabel("Simulation Elapsed Time (minutes)", fontsize=11)
    plt.ylabel("Inundated Domain Area >5cm (km²)", fontsize=11)
    plt.title("Temporal Inundated Area Progression (True vs Predicted)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "temporal", "temporal_area_evolution.png"), dpi=180)
    plt.close()

    # 2G. Peak Patch Comparison
    fig, axes = plt.subplots(2, 5, figsize=(15, 6))
    for idx, s in enumerate(TEST_STORMS):
        eid = s["id"]
        p_rec = [p for p in peak_records if p["event_id"] == eid][0]
        yt, xt, tt = p_rec["true_peak_y"], p_rec["true_peak_x"], p_rec["true_peak_timestep"]
        p5_t = extract_patch(all_storm_data[eid]["H_true"][..., tt], yt, xt, 5)
        p5_p = extract_patch(all_storm_data[eid]["H_pred"][..., tt], yt, xt, 5)
        vmax_p = max(float(p5_t.max()), float(p5_p.max()), 0.5)

        axes[0, idx].imshow(p5_t, cmap="Blues", vmin=0, vmax=vmax_p)
        axes[0, idx].set_title(f"{eid} True 5x5\nMax: {p5_t.max():.2f}m", fontsize=9)
        axes[0, idx].set_xticks([]); axes[0, idx].set_yticks([])

        axes[1, idx].imshow(p5_p, cmap="Blues", vmin=0, vmax=vmax_p)
        axes[1, idx].set_title(f"{eid} Pred 5x5\nMax: {p5_p.max():.2f}m\nDiff: {p5_p.max()-p5_t.max():+.2f}m", fontsize=9)
        axes[1, idx].set_xticks([]); axes[1, idx].set_yticks([])

    plt.suptitle("Peak Local Neighborhood Analysis (5x5 Grid Cells Around True Max)", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "peak_analysis", "peak_patch_comparison.png"), dpi=180)
    plt.close()

    print("\n" + "=" * 80)
    print("PHASE 7A ERROR ANALYSIS COMPLETE")
    print(f"Reproduction Check: {'PASS' if reproduction_ok else 'FAIL'}")
    print(f"Summary CSV tables saved to: {log_dir}")
    print(f"Diagnostic plots saved to:   {out_dir}")
    print("=" * 80)


if __name__ == "__main__":
    run_phase7a_diagnostic()
