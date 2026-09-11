"""
FloodWatch AI — Phase 6: Experimental Chennai DNO Training, Validation & Final Testing Engine
SIH26085 — Urban Flood Nowcasting System

Strict Rules:
1. Initialize from scratch (num_channels=5, width=10, initial_step=1, pad=0, factor=1).
2. NO Berlin weights loaded.
3. External/UrbanFloodCast repository is READ-ONLY.
4. models/trained/chennai_xgboost_baseline.json is NOT modified.
5. Production FastAPI and frontend remain UNTOUCHED.
6. Phase 4 artifacts and Phase 5 pilot events are PROTECTED.
7. Event-based split: 21 Train, 4 Validation, 5 Test.
8. Test set is strictly isolated and only evaluated after training is finalized.
"""

import os
import sys
import time
import json
import csv
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Connect to UrbanFloodCast without altering external repository
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DNO_DIR = os.path.join(REPO_ROOT, "External", "UrbanFloodCast", "UrbanFloodCast", "DNO")
if DNO_DIR not in sys.path:
    sys.path.insert(0, DNO_DIR)

from models.DNO import DNO

# Dataset Partitions (from Phase 5 Master Manifest)
TRAIN_EVENTS = [
    "storm_001", "storm_002", "storm_004", "storm_005", "storm_006",
    "storm_009", "storm_010", "storm_012", "storm_013", "storm_015",
    "storm_017", "storm_018", "storm_019", "storm_020", "storm_021",
    "storm_023", "storm_025", "storm_026", "storm_027", "storm_029",
    "storm_030"
]

VAL_EVENTS = [
    "storm_003", "storm_008", "storm_014", "storm_022"
]

TEST_EVENTS = [
    "storm_007", "storm_011", "storm_016", "storm_024", "storm_028"
]


class ChannelMSELoss(nn.Module):
    """
    Computes separate MSE loss for H, U, V and their average total loss.
    Input/Target shape: [B, Sy, Sx, T, C] where C = 3 (H, U, V).
    """
    def __init__(self):
        super().__init__()

    def forward(self, pred: torch.Tensor, target: torch.Tensor):
        loss_h = F.mse_loss(pred[..., 0], target[..., 0])
        loss_u = F.mse_loss(pred[..., 1], target[..., 1])
        loss_v = F.mse_loss(pred[..., 2], target[..., 2])
        total_loss = (loss_h + loss_u + loss_v) / 3.0
        return total_loss, loss_h, loss_u, loss_v


def setup_directories():
    ckpt_dir = os.path.join(REPO_ROOT, "models", "urban_flood_dno", "checkpoints", "chennai_phase6")
    log_dir = os.path.join(REPO_ROOT, "models", "urban_flood_dno", "logs", "chennai_phase6")
    out_dir = os.path.join(REPO_ROOT, "outputs", "chennai_dno", "phase6")
    for d in [ckpt_dir, log_dir, out_dir]:
        os.makedirs(d, exist_ok=True)
    return ckpt_dir, log_dir, out_dir


def evaluate_physical_metrics(pred: np.ndarray, true: np.ndarray):
    """Computes physical error metrics for a single variable [Sy, Sx, T]."""
    diff = pred - true
    abs_diff = np.abs(diff)
    mae = float(np.mean(abs_diff))
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    max_err = float(np.max(abs_diff))

    p_flat = pred.flatten()
    t_flat = true.flatten()
    std_p = np.std(p_flat)
    std_t = np.std(t_flat)
    if std_p > 1e-6 and std_t > 1e-6:
        corr = float(np.corrcoef(p_flat, t_flat)[0, 1])
    else:
        corr = 0.0

    return {"mae": mae, "rmse": rmse, "max_err": max_err, "corr": corr}


def compute_flood_extent_metrics(pred_h: np.ndarray, true_h: np.ndarray, threshold: float):
    """
    Calculates Intersection, Union, IoU (CSI), Precision, and Recall
    for water depth threshold (meters) at final timestep or across full volume.
    """
    p_wet = pred_h > threshold
    t_wet = true_h > threshold

    intersection = int(np.sum(p_wet & t_wet))
    union = int(np.sum(p_wet | t_wet))
    pred_pos = int(np.sum(p_wet))
    true_pos = int(np.sum(t_wet))

    iou = float(intersection / union) if union > 0 else 1.0
    precision = float(intersection / pred_pos) if pred_pos > 0 else 1.0
    recall = float(intersection / true_pos) if true_pos > 0 else 1.0

    return {
        "threshold_m": threshold,
        "intersection": intersection,
        "union": union,
        "iou": iou,
        "precision": precision,
        "recall": recall
    }


def plot_training_curves(csv_log_path: str, out_dir: str):
    """Generates all 6 required Phase 6 training curves from the training CSV log."""
    epochs, train_tot, val_tot = [], [], []
    train_h, val_h = [], []
    train_u, val_u = [], []
    train_v, val_v = [], []
    lrs, alloc_mb, res_mb = [], [], []

    with open(csv_log_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            epochs.append(int(row["epoch"]))
            train_tot.append(float(row["train_total_loss"]))
            val_tot.append(float(row["val_total_loss"]))
            train_h.append(float(row["train_H_loss"]))
            val_h.append(float(row["val_H_loss"]))
            train_u.append(float(row["train_U_loss"]))
            val_u.append(float(row["val_U_loss"]))
            train_v.append(float(row["train_V_loss"]))
            val_v.append(float(row["val_V_loss"]))
            lrs.append(float(row["learning_rate"]))
            alloc_mb.append(float(row["gpu_memory_allocated_mb"]))
            res_mb.append(float(row["gpu_memory_reserved_mb"]))

    # 1. Total Loss Curve
    plt.figure(figsize=(8, 5))
    plt.plot(epochs, train_tot, "b-o", label="Train Total Loss (MSE)", linewidth=1.8)
    plt.plot(epochs, val_tot, "r--s", label="Val Total Loss (MSE)", linewidth=1.8)
    plt.xlabel("Epoch", fontsize=11)
    plt.ylabel("MSE Loss (Normalized Units)", fontsize=11)
    plt.title("Phase 6 DNO — Total Loss Evolution", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "training_total_loss.png"), dpi=180)
    plt.close()

    # 2. H Loss Curve
    plt.figure(figsize=(8, 5))
    plt.plot(epochs, train_h, "b-o", label="Train H Loss (MSE)", linewidth=1.8)
    plt.plot(epochs, val_h, "r--s", label="Val H Loss (MSE)", linewidth=1.8)
    plt.xlabel("Epoch", fontsize=11)
    plt.ylabel("Water Depth H MSE Loss", fontsize=11)
    plt.title("Phase 6 DNO — Water Depth (H) Loss Evolution", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "training_H_loss.png"), dpi=180)
    plt.close()

    # 3. U Loss Curve
    plt.figure(figsize=(8, 5))
    plt.plot(epochs, train_u, "b-o", label="Train U Loss (MSE)", linewidth=1.8)
    plt.plot(epochs, val_u, "r--s", label="Val U Loss (MSE)", linewidth=1.8)
    plt.xlabel("Epoch", fontsize=11)
    plt.ylabel("Velocity U MSE Loss", fontsize=11)
    plt.title("Phase 6 DNO — X-Velocity (U) Loss Evolution", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "training_U_loss.png"), dpi=180)
    plt.close()

    # 4. V Loss Curve
    plt.figure(figsize=(8, 5))
    plt.plot(epochs, train_v, "b-o", label="Train V Loss (MSE)", linewidth=1.8)
    plt.plot(epochs, val_v, "r--s", label="Val V Loss (MSE)", linewidth=1.8)
    plt.xlabel("Epoch", fontsize=11)
    plt.ylabel("Velocity V MSE Loss", fontsize=11)
    plt.title("Phase 6 DNO — Y-Velocity (V) Loss Evolution", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "training_V_loss.png"), dpi=180)
    plt.close()

    # 5. Learning Rate Curve
    plt.figure(figsize=(8, 4))
    plt.plot(epochs, lrs, "g-^", label="Learning Rate", linewidth=1.8)
    plt.xlabel("Epoch", fontsize=11)
    plt.ylabel("Learning Rate", fontsize=11)
    plt.yscale("log")
    plt.title("Phase 6 DNO — Learning Rate Schedule", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "learning_rate.png"), dpi=180)
    plt.close()

    # 6. GPU Memory Curve
    plt.figure(figsize=(8, 4))
    plt.plot(epochs, alloc_mb, "m-o", label="Allocated VRAM (MB)", linewidth=1.8)
    plt.plot(epochs, res_mb, "c--s", label="Reserved VRAM (MB)", linewidth=1.8)
    plt.xlabel("Epoch", fontsize=11)
    plt.ylabel("GPU Memory (MB)", fontsize=11)
    plt.title("Phase 6 DNO — RTX 3050 VRAM Utilization", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "gpu_memory.png"), dpi=180)
    plt.close()


def run_phase6(smoke_only: bool = False, epochs: int = 50, lr: float = 1e-3, patience: int = 10):
    print("=" * 80)
    print("FLOODWATCH AI — PHASE 6: EXPERIMENTAL CHENNAI DNO TRAINING & EVALUATION")
    print("DATASET CLASSIFICATION: SIMULATED HYDRODYNAMIC TRAINING DATA")
    print("=" * 80)

    # 1. Device Verification
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for Phase 6 DNO training on RTX 3050.")
    device = torch.device("cuda:0")
    gpu_name = torch.cuda.get_device_name(0)
    print(f"[1] Hardware Verified: {gpu_name} ({device})")

    # Deterministic seeds
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    np.random.seed(42)

    ckpt_dir, log_dir, out_dir = setup_directories()
    csv_log_path = os.path.join(log_dir, "training.csv")
    tensor_dir = os.path.join(REPO_ROOT, "Data", "dno", "chennai", "storm_library", "tensors")

    print(f"[2] Partitions: TRAIN={len(TRAIN_EVENTS)}, VAL={len(VAL_EVENTS)}, TEST={len(TEST_EVENTS)}")

    # 2. Model Initialization (From Scratch)
    print("\n[3] Initializing Chennai DNO Surrogate (from scratch):")
    model_config = {
        "num_channels": 5,
        "width": 10,
        "initial_step": 1,
        "pad": 0,
        "factor": 1,
        "input_channels": ["H0", "U0", "V0", "P", "Z"],
        "target_channels": ["H", "U", "V"],
        "berlin_weights_loaded": False,
        "random_seeds": {"python": 42, "numpy": 42, "torch": 42, "cuda": 42}
    }

    model = DNO(
        num_channels=model_config["num_channels"],
        width=model_config["width"],
        initial_step=model_config["initial_step"],
        pad=model_config["pad"],
        factor=model_config["factor"]
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Architecture: DNO (channels=5, width=10, initial_step=1, pad=0, factor=1)")
    print(f"  Total Parameters: {total_params:,} (Expected: 4,470,437)")
    assert total_params == 4470437, f"Parameter count mismatch: {total_params}"

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5, min_lr=1e-5
    )
    loss_fn = ChannelMSELoss()

    # 3. SMOKE TEST (1 Epoch)
    if smoke_only:
        print("\n" + "=" * 60)
        print("EXECUTING PHASE 6 1-EPOCH SMOKE TEST")
        print("=" * 60)
        torch.cuda.reset_peak_memory_stats(device)
        model.train()

        # Train smoke step using storm_001
        test_eid = TRAIN_EVENTS[0]
        x_path = os.path.join(tensor_dir, f"{test_eid}_input_tensor.pt")
        y_path = os.path.join(tensor_dir, f"{test_eid}_target_tensor.pt")
        x = torch.load(x_path, map_location=device)
        y = torch.load(y_path, map_location=device)

        optimizer.zero_grad()
        t0 = time.perf_counter()
        pred = model(x)
        t_fwd = time.perf_counter() - t0
        loss, lh, lu, lv = loss_fn(pred, y)

        assert not torch.isnan(loss), "NaN detected in training loss!"
        assert not torch.isinf(loss), "Inf detected in training loss!"

        t1 = time.perf_counter()
        loss.backward()
        t_bwd = time.perf_counter() - t1
        optimizer.step()

        del x, y, pred
        torch.cuda.empty_cache()

        # Validation smoke step using storm_003
        model.eval()
        val_eid = VAL_EVENTS[0]
        xv_path = os.path.join(tensor_dir, f"{val_eid}_input_tensor.pt")
        yv_path = os.path.join(tensor_dir, f"{val_eid}_target_tensor.pt")
        xv = torch.load(xv_path, map_location=device)
        yv = torch.load(yv_path, map_location=device)
        with torch.no_grad():
            pred_v = model(xv)
            v_loss, v_lh, v_lu, v_lv = loss_fn(pred_v, yv)

        assert not torch.isnan(v_loss), "NaN detected in validation loss!"
        assert not torch.isinf(v_loss), "Inf detected in validation loss!"
        del xv, yv, pred_v
        torch.cuda.empty_cache()

        peak_alloc = torch.cuda.max_memory_allocated(device) / (1024 ** 2)
        peak_res = torch.cuda.max_memory_reserved(device) / (1024 ** 2)

        print(f"  [PASS] Data Loading: Succeeded for {test_eid} and {val_eid}")
        print(f"  [PASS] Forward Pass Time:  {t_fwd * 1000:.2f} ms")
        print(f"  [PASS] Backward Pass Time: {t_bwd * 1000:.2f} ms")
        print(f"  [PASS] Train MSE Loss: {loss.item():.6f} (H: {lh.item():.6f}, U: {lu.item():.6f}, V: {lv.item():.6f})")
        print(f"  [PASS] Val MSE Loss:   {v_loss.item():.6f} (H: {v_lh.item():.6f}, U: {v_lu.item():.6f}, V: {v_lv.item():.6f})")
        print(f"  [PASS] Peak VRAM Allocated: {peak_alloc:.2f} MB")
        print(f"  [PASS] Peak VRAM Reserved:  {peak_res:.2f} MB")
        print(f"  [PASS] Numerical Safety: Zero NaN, Zero Inf")
        print("=" * 60)
        return True

    # 4. FULL TRAINING
    print("\n" + "=" * 60)
    print(f"STARTING PHASE 6 TRAINING (Max {epochs} Epochs, Early Stopping Patience={patience})")
    print("=" * 60)

    with open(csv_log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "epoch", "train_total_loss", "train_H_loss", "train_U_loss", "train_V_loss",
            "val_total_loss", "val_H_loss", "val_U_loss", "val_V_loss",
            "learning_rate", "epoch_seconds", "gpu_memory_allocated_mb", "gpu_memory_reserved_mb"
        ])

    best_val_loss = float("inf")
    best_epoch = -1
    patience_counter = 0
    best_checkpoint_path = os.path.join(ckpt_dir, "best_dno_checkpoint.pt")
    final_checkpoint_path = os.path.join(ckpt_dir, "final_dno_checkpoint.pt")

    for epoch in range(1, epochs + 1):
        t_ep_start = time.perf_counter()
        torch.cuda.reset_peak_memory_stats(device)

        # A. TRAIN PASS (21 events sequentially)
        model.train()
        train_tot_list, train_h_list, train_u_list, train_v_list = [], [], [], []

        for eid in TRAIN_EVENTS:
            x_path = os.path.join(tensor_dir, f"{eid}_input_tensor.pt")
            y_path = os.path.join(tensor_dir, f"{eid}_target_tensor.pt")
            x = torch.load(x_path, map_location=device)
            y = torch.load(y_path, map_location=device)

            optimizer.zero_grad()
            pred = model(x)
            loss, lh, lu, lv = loss_fn(pred, y)
            loss.backward()
            optimizer.step()

            train_tot_list.append(loss.item())
            train_h_list.append(lh.item())
            train_u_list.append(lu.item())
            train_v_list.append(lv.item())

            del x, y, pred
            torch.cuda.empty_cache()

        ep_tr_tot = float(np.mean(train_tot_list))
        ep_tr_h = float(np.mean(train_h_list))
        ep_tr_u = float(np.mean(train_u_list))
        ep_tr_v = float(np.mean(train_v_list))

        # B. VALIDATION PASS (4 events sequentially)
        model.eval()
        val_tot_list, val_h_list, val_u_list, val_v_list = [], [], [], []

        with torch.no_grad():
            for eid in VAL_EVENTS:
                x_path = os.path.join(tensor_dir, f"{eid}_input_tensor.pt")
                y_path = os.path.join(tensor_dir, f"{eid}_target_tensor.pt")
                x = torch.load(x_path, map_location=device)
                y = torch.load(y_path, map_location=device)

                pred = model(x)
                loss, lh, lu, lv = loss_fn(pred, y)

                val_tot_list.append(loss.item())
                val_h_list.append(lh.item())
                val_u_list.append(lu.item())
                val_v_list.append(lv.item())

                del x, y, pred
                torch.cuda.empty_cache()

        ep_val_tot = float(np.mean(val_tot_list))
        ep_val_h = float(np.mean(val_h_list))
        ep_val_u = float(np.mean(val_u_list))
        ep_val_v = float(np.mean(val_v_list))

        # Step Scheduler
        current_lr = optimizer.param_groups[0]["lr"]
        scheduler.step(ep_val_tot)

        torch.cuda.synchronize()
        ep_time = time.perf_counter() - t_ep_start
        peak_alloc = torch.cuda.max_memory_allocated(device) / (1024 ** 2)
        peak_res = torch.cuda.max_memory_reserved(device) / (1024 ** 2)

        # Log
        with open(csv_log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                epoch, f"{ep_tr_tot:.6f}", f"{ep_tr_h:.6f}", f"{ep_tr_u:.6f}", f"{ep_tr_v:.6f}",
                f"{ep_val_tot:.6f}", f"{ep_val_h:.6f}", f"{ep_val_u:.6f}", f"{ep_val_v:.6f}",
                f"{current_lr:.6e}", f"{ep_time:.2f}", f"{peak_alloc:.2f}", f"{peak_res:.2f}"
            ])

        print(f"Epoch {epoch:02d}/{epochs:02d} | Train MSE: {ep_tr_tot:.5f} (H:{ep_tr_h:.5f}) | Val MSE: {ep_val_tot:.5f} (H:{ep_val_h:.5f}) | LR: {current_lr:.1e} | Time: {ep_time:.1f}s | VRAM: {peak_alloc:.0f}MB")

        # Checkpoint Best Model
        if ep_val_tot < best_val_loss:
            best_val_loss = ep_val_tot
            best_epoch = epoch
            patience_counter = 0

            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "train_total_loss": ep_tr_tot,
                "val_total_loss": ep_val_tot,
                "val_h_loss": ep_val_h,
                "val_u_loss": ep_val_u,
                "val_v_loss": ep_val_v,
                "model_config": model_config,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }, best_checkpoint_path)
            print(f"  --> Saved new best checkpoint at epoch {epoch:02d} (Val Loss: {best_val_loss:.6f})")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\n[!] Early stopping triggered at epoch {epoch:02d} (patience={patience} exhausted).")
                break

    # Save final checkpoint
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "train_total_loss": ep_tr_tot,
        "val_total_loss": ep_val_tot,
        "model_config": model_config,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }, final_checkpoint_path)

    print(f"\nTraining completed. Best Epoch: {best_epoch:02d} | Best Val Loss: {best_val_loss:.6f}")

    # Generate Training Curves
    print("\n[5] Generating Training Curves...")
    plot_training_curves(csv_log_path, out_dir)
    print("  Saved training curves to outputs/chennai_dno/phase6/")

    # 5. OUT-OF-SAMPLE TEST EVALUATION (5 PROTECTED STORMS)
    print("\n" + "=" * 60)
    print("EVALUATING BEST CHECKPOINT ON 5 PROTECTED TEST STORMS")
    print(f"Test Events: {TEST_EVENTS}")
    print("=" * 60)

    best_ckpt = torch.load(best_checkpoint_path, map_location=device)
    model.load_state_dict(best_ckpt["model_state_dict"])
    model.eval()

    # Load hydrodynamic runtimes from simulation_runtime.csv
    hydro_runtimes = {}
    runtime_csv_path = os.path.join(REPO_ROOT, "Data", "dno", "chennai", "storm_library", "metadata", "simulation_runtime.csv")
    if os.path.exists(runtime_csv_path):
        with open(runtime_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                hydro_runtimes[r["event_id"]] = float(r["simulation_seconds"])

    test_results_per_event = {}
    total_hydro_sec = 0.0
    total_dno_inf_sec = 0.0

    for eid in TEST_EVENTS:
        print(f"\n--- Testing on {eid} ---")
        x_path = os.path.join(tensor_dir, f"{eid}_input_tensor.pt")
        y_path = os.path.join(tensor_dir, f"{eid}_target_tensor.pt")
        x = torch.load(x_path, map_location=device)
        y = torch.load(y_path, map_location=device)

        # Benchmark inference time
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.no_grad():
            pred = model(x)
        torch.cuda.synchronize()
        inf_time = time.perf_counter() - t0
        total_dno_inf_sec += inf_time

        hydro_time = hydro_runtimes.get(eid, 12.0)
        total_hydro_sec += hydro_time

        # Denormalize to physical units
        # H, U, V scale = 5.0
        pred_np = pred.squeeze(0).cpu().numpy()  # [128, 128, 24, 3]
        true_np = y.squeeze(0).cpu().numpy()     # [128, 128, 24, 3]

        H_pred = np.maximum(pred_np[..., 0] * 5.0, 0.0)  # Physical non-negative depth (m)
        U_pred = pred_np[..., 1] * 5.0                   # Velocity U (m/s)
        V_pred = pred_np[..., 2] * 5.0                   # Velocity V (m/s)

        H_true = true_np[..., 0] * 5.0                   # True Depth (m)
        U_true = true_np[..., 1] * 5.0                   # True U (m/s)
        V_true = true_np[..., 2] * 5.0                   # True V (m/s)

        # Metrics
        h_met = evaluate_physical_metrics(H_pred, H_true)
        u_met = evaluate_physical_metrics(U_pred, U_true)
        v_met = evaluate_physical_metrics(V_pred, V_true)

        # Extent Metrics at 5cm and 10cm thresholds
        ext_5cm = compute_flood_extent_metrics(H_pred, H_true, threshold=0.05)
        ext_10cm = compute_flood_extent_metrics(H_pred, H_true, threshold=0.10)

        # Peak Depth & Timing Error
        true_max_series = np.max(H_true, axis=(0, 1))  # [T=24]
        pred_max_series = np.max(H_pred, axis=(0, 1))  # [T=24]

        t_peak_true = int(np.argmax(true_max_series))
        t_peak_pred = int(np.argmax(pred_max_series))
        peak_val_true = float(true_max_series[t_peak_true])
        peak_val_pred = float(pred_max_series[t_peak_pred])
        peak_abs_err = peak_val_pred - peak_val_true
        peak_pct_err = (peak_abs_err / peak_val_true) * 100.0 if peak_val_true > 0 else 0.0
        timing_err_min = (t_peak_pred - t_peak_true) * 5.0

        print(f"  Water Depth (H)  -> MAE: {h_met['mae']:.4f}m ({h_met['mae']*100:.2f}cm) | RMSE: {h_met['rmse']:.4f}m | Corr: {h_met['corr']:.4f}")
        print(f"  Velocity (U, V)  -> U MAE: {u_met['mae']:.4f}m/s | V MAE: {v_met['mae']:.4f}m/s")
        print(f"  Flood Extent IoU -> >5cm: {ext_5cm['iou']:.4f} (Prec: {ext_5cm['precision']:.3f}, Rec: {ext_5cm['recall']:.3f}) | >10cm: {ext_10cm['iou']:.4f}")
        print(f"  Peak Depth Error -> True: {peak_val_true:.3f}m vs Pred: {peak_val_pred:.3f}m (Err: {peak_abs_err:+.3f}m, {peak_pct_err:+.1f}%)")
        print(f"  Speed Benchmark  -> Hydrodynamic: {hydro_time:.3f}s | DNO: {inf_time*1000:.1f}ms (Speedup: {hydro_time/inf_time:.1f}x)")

        test_results_per_event[eid] = {
            "H_metrics": h_met,
            "U_metrics": u_met,
            "V_metrics": v_met,
            "extent_5cm": ext_5cm,
            "extent_10cm": ext_10cm,
            "peak_depth_true_m": peak_val_true,
            "peak_depth_pred_m": peak_val_pred,
            "peak_depth_error_m": peak_abs_err,
            "peak_depth_pct_error": peak_pct_err,
            "peak_timing_error_min": timing_err_min,
            "inference_seconds": inf_time,
            "hydrodynamic_seconds": hydro_time,
            "speedup_factor": hydro_time / inf_time
        }

        # Visual Diagnostics
        # 1. Temporal Hydrograph Comparison
        time_min = np.arange(1, 25) * 5.0
        true_mean_series = np.mean(H_true, axis=(0, 1))
        pred_mean_series = np.mean(H_pred, axis=(0, 1))

        fig, ax = plt.subplots(figsize=(9, 5))
        ax.plot(time_min, true_max_series, "b-o", label="Hydro Solver Domain Max (m)", linewidth=2)
        ax.plot(time_min, pred_max_series, "b--s", label="DNO Pred Domain Max (m)", linewidth=2)
        ax.plot(time_min, true_mean_series, "g-^", label="Hydro Solver Mean (m)", linewidth=1.5)
        ax.plot(time_min, pred_mean_series, "g--v", label="DNO Pred Mean (m)", linewidth=1.5)
        ax.set_xlabel("Elapsed Time (minutes)", fontsize=11)
        ax.set_ylabel("Water Depth (m)", fontsize=11)
        ax.set_title(f"Temporal Hydrograph Comparison — {eid.upper()}\nPeak Err: {peak_abs_err:+.3f}m | H MAE: {h_met['mae']*100:.2f}cm", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f"test_temporal_comparison_{eid}.png"), dpi=180)
        plt.close()

        # 2. Spatial Comparison Maps (Final Timestep t=23)
        t_plot = 23
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
        vmax_plot = max(float(H_true[:, :, t_plot].max()), 0.5)

        im0 = axes[0].imshow(H_true[:, :, t_plot], cmap="Blues", vmin=0, vmax=vmax_plot)
        axes[0].set_title(f"Hydrodynamic Ref H (t=120m)\nMax: {H_true[:, :, t_plot].max():.2f} m")
        plt.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

        im1 = axes[1].imshow(H_pred[:, :, t_plot], cmap="Blues", vmin=0, vmax=vmax_plot)
        axes[1].set_title(f"DNO Predicted H (t=120m)\nMax: {H_pred[:, :, t_plot].max():.2f} m")
        plt.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

        err_map = np.abs(H_pred[:, :, t_plot] - H_true[:, :, t_plot])
        im2 = axes[2].imshow(err_map, cmap="Reds", vmin=0, vmax=max(err_map.max(), 0.1))
        axes[2].set_title(f"Absolute Error |H_dno - H_ref|\nMAE: {err_map.mean():.3f} m | Max: {err_map.max():.2f} m")
        plt.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)

        for a in axes:
            a.set_xticks([])
            a.set_yticks([])
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f"test_spatial_comparison_{eid}.png"), dpi=180)
        plt.close()

        del x, y, pred
        torch.cuda.empty_cache()

    # Aggregate Test Summary
    avg_h_mae = float(np.mean([test_results_per_event[e]["H_metrics"]["mae"] for e in TEST_EVENTS]))
    avg_h_rmse = float(np.mean([test_results_per_event[e]["H_metrics"]["rmse"] for e in TEST_EVENTS]))
    avg_u_mae = float(np.mean([test_results_per_event[e]["U_metrics"]["mae"] for e in TEST_EVENTS]))
    avg_u_rmse = float(np.mean([test_results_per_event[e]["U_metrics"]["rmse"] for e in TEST_EVENTS]))
    avg_v_mae = float(np.mean([test_results_per_event[e]["V_metrics"]["mae"] for e in TEST_EVENTS]))
    avg_v_rmse = float(np.mean([test_results_per_event[e]["V_metrics"]["rmse"] for e in TEST_EVENTS]))
    avg_iou_5cm = float(np.mean([test_results_per_event[e]["extent_5cm"]["iou"] for e in TEST_EVENTS]))
    avg_iou_10cm = float(np.mean([test_results_per_event[e]["extent_10cm"]["iou"] for e in TEST_EVENTS]))
    avg_peak_err = float(np.mean([test_results_per_event[e]["peak_depth_error_m"] for e in TEST_EVENTS]))
    overall_speedup = total_hydro_sec / total_dno_inf_sec

    summary_json = {
        "experiment": "Phase 6 — Experimental Chennai DNO Training & Evaluation",
        "dataset": {
            "total_events": 30,
            "train_events": TRAIN_EVENTS,
            "val_events": VAL_EVENTS,
            "test_events": TEST_EVENTS
        },
        "model": {
            "total_params": total_params,
            "config": model_config
        },
        "training": {
            "epochs_completed": epoch,
            "best_epoch": best_epoch,
            "best_val_loss": best_val_loss,
            "final_train_loss": ep_tr_tot,
            "best_checkpoint": best_checkpoint_path
        },
        "aggregate_test_metrics": {
            "mean_H_MAE_m": avg_h_mae,
            "mean_H_RMSE_m": avg_h_rmse,
            "mean_U_MAE_mps": avg_u_mae,
            "mean_U_RMSE_mps": avg_u_rmse,
            "mean_V_MAE_mps": avg_v_mae,
            "mean_V_RMSE_mps": avg_v_rmse,
            "mean_flood_IoU_5cm": avg_iou_5cm,
            "mean_flood_IoU_10cm": avg_iou_10cm,
            "mean_peak_depth_error_m": avg_peak_err,
            "overall_speedup_factor": overall_speedup,
            "total_hydrodynamic_runtime_sec": total_hydro_sec,
            "total_dno_inference_sec": total_dno_inf_sec
        },
        "per_event_test_results": test_results_per_event
    }

    summary_path = os.path.join(log_dir, "test_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)

    print("\n" + "=" * 80)
    print("PHASE 6 EXPERIMENTAL TRAINING & TEST EVALUATION COMPLETE")
    print(f"Best Epoch: {best_epoch:02d} | Best Val Loss: {best_val_loss:.6f}")
    print(f"Aggregate Test H MAE: {avg_h_mae*100:.2f} cm | RMSE: {avg_h_rmse*100:.2f} cm")
    print(f"Flood IoU (>5cm): {avg_iou_5cm:.4f} | Flood IoU (>10cm): {avg_iou_10cm:.4f}")
    print(f"Overall Inference Acceleration: {overall_speedup:.1f}x")
    print(f"Results Summary Saved: {summary_path}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke_only", action="store_true", help="Run 1-epoch smoke test only")
    parser.add_argument("--epochs", type=int, default=50, help="Maximum epochs")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    args = parser.parse_args()

    run_phase6(
        smoke_only=args.smoke_only,
        epochs=args.epochs,
        lr=args.lr,
        patience=args.patience
    )
