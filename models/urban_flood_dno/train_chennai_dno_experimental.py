"""
Chennai UrbanFloodCast DNO Experimental Training & Physical Validation Engine
Phase 4: First Experimental Deep Neural Operator Training Run

Strict Boundary Rules:
1. Berlin weights loaded = FALSE (Initialized from scratch with fixed seed)
2. External/UrbanFloodCast repository is NOT modified
3. models/trained/chennai_xgboost_baseline.json is NOT modified
4. Isolated under models/urban_flood_dno/
5. All target data explicitly labeled: SIMULATED HYDRODYNAMIC TRAINING DATA
6. Event-based split: Train=2015 Deluge, Val=2023 Michaung, Test=Monsoon Moderate
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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Connect to UrbanFloodCast without altering the external repository
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DNO_DIR = os.path.join(REPO_ROOT, "External", "UrbanFloodCast", "UrbanFloodCast", "DNO")
if DNO_DIR not in sys.path:
    sys.path.insert(0, DNO_DIR)

from models.DNO import DNO


class RelativeLpLoss(nn.Module):
    """
    Relative L2 loss conforming to UrbanFloodCast / FNO specifications:
    rel_loss = ||y - y_hat||_2 / ||y||_2
    Evaluated per-channel across spatial-temporal domain and averaged.
    """
    def __init__(self, eps: float = 1e-5):
        super().__init__()
        self.eps = eps

    def forward(self, pred: torch.Tensor, target: torch.Tensor):
        # pred and target shape: [B, Sy, Sx, T, C] -> flatten to [B, Sy*Sx*T, C]
        b, sy, sx, t, c = pred.shape
        p_flat = pred.reshape(b, -1, c)
        t_flat = target.reshape(b, -1, c)

        diff_norm = torch.norm(p_flat - t_flat, p=2, dim=1)  # [B, C]
        target_norm = torch.norm(t_flat, p=2, dim=1)         # [B, C]

        channel_rel_losses = diff_norm / (target_norm + self.eps)  # [B, C]
        mean_channel_loss = channel_rel_losses.mean(dim=0)         # [C] (H, U, V)
        total_loss = mean_channel_loss.mean()

        return total_loss, mean_channel_loss[0], mean_channel_loss[1], mean_channel_loss[2]


def setup_directories():
    base = os.path.join(REPO_ROOT, "models", "urban_flood_dno")
    ckpt_dir = os.path.join(base, "checkpoints", "chennai_dno")
    log_dir = os.path.join(base, "logs")
    out_dir = os.path.join(REPO_ROOT, "outputs", "chennai_dno")
    for d in [ckpt_dir, log_dir, out_dir]:
        os.makedirs(d, exist_ok=True)
    return ckpt_dir, log_dir, out_dir


def evaluate_metrics(pred: np.ndarray, true: np.ndarray):
    """Computes comprehensive physical error metrics for a single variable [Sy, Sx, T]."""
    diff = pred - true
    abs_diff = np.abs(diff)
    mae = float(np.mean(abs_diff))
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    max_err = float(np.max(abs_diff))

    # Pearson Correlation across all active spatial-temporal points
    p_flat = pred.flatten()
    t_flat = true.flatten()
    std_p = np.std(p_flat)
    std_t = np.std(t_flat)
    if std_p > 1e-6 and std_t > 1e-6:
        corr = float(np.corrcoef(p_flat, t_flat)[0, 1])
    else:
        corr = 0.0

    return {"mae": mae, "rmse": rmse, "max_err": max_err, "corr": corr}


def compute_wet_overlap(pred_h: np.ndarray, true_h: np.ndarray, threshold: float = 0.05):
    """Critical Success Index (CSI) / Intersection-over-Union for inundation > threshold (meters)."""
    p_wet = pred_h > threshold
    t_wet = true_h > threshold
    hits = np.sum(p_wet & t_wet)
    misses = np.sum((~p_wet) & t_wet)
    false_alarms = np.sum(p_wet & (~t_wet))
    denom = hits + misses + false_alarms
    csi = float(hits / denom) if denom > 0 else 1.0
    return csi, int(hits), int(misses), int(false_alarms)


def run_experiment(smoke_only: bool = False, epochs: int = 30, lr: float = 1e-3, patience: int = 10):
    print("=" * 80)
    print("FLOODWATCH AI — PHASE 4: EXPERIMENTAL CHENNAI URBANFLOODCAST DNO TRAINING")
    print("DATASET CLASSIFICATION: SIMULATED HYDRODYNAMIC TRAINING DATA")
    print("=" * 80)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"[1] Compute Hardware: {torch.cuda.get_device_name(device)} ({device})")
    if device.type != "cuda":
        raise RuntimeError("CUDA is required for DNO training on RTX 3050.")

    ckpt_dir, log_dir, out_dir = setup_directories()
    csv_log_path = os.path.join(log_dir, "chennai_dno_training.csv")

    # 1. Load Data
    tensor_dir = os.path.join(REPO_ROOT, "Data", "dno", "chennai", "tensors")
    print("\n[2] Loading Pre-Packaged Event Tensors:")
    x_train = torch.load(os.path.join(tensor_dir, "event_01_2015_deluge_input_tensor.pt")).to(device)
    y_train = torch.load(os.path.join(tensor_dir, "event_01_2015_deluge_target_tensor.pt")).to(device)
    x_val = torch.load(os.path.join(tensor_dir, "event_02_michaung_surge_input_tensor.pt")).to(device)
    y_val = torch.load(os.path.join(tensor_dir, "event_02_michaung_surge_target_tensor.pt")).to(device)
    x_test = torch.load(os.path.join(tensor_dir, "event_03_monsoon_moderate_input_tensor.pt")).to(device)
    y_test = torch.load(os.path.join(tensor_dir, "event_03_monsoon_moderate_target_tensor.pt")).to(device)

    print(f"  TRAIN: Event 01 (2015 Deluge)   -> X: {list(x_train.shape)}, Y: {list(y_train.shape)}")
    print(f"  VAL:   Event 02 (2023 Michaung) -> X: {list(x_val.shape)}, Y: {list(y_val.shape)}")
    print(f"  TEST:  Event 03 (Monsoon Mod)  -> X: {list(x_test.shape)}, Y: {list(y_test.shape)}")

    # 2. Model Initialization (From Scratch)
    print("\n[3] Model Instantiation & Initialization Audit:")
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    np.random.seed(42)

    model_config = {
        "num_channels": 5,
        "width": 10,
        "initial_step": 1,
        "pad": 0,
        "factor": 1,
        "input_channels": ["H0", "U0", "V0", "P", "Z"],
        "target_channels": ["H", "U", "V"],
        "berlin_weights_loaded": False
    }

    model = DNO(
        num_channels=model_config["num_channels"],
        width=model_config["width"],
        initial_step=model_config["initial_step"],
        pad=model_config["pad"],
        factor=model_config["factor"]
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Berlin weights loaded: {model_config['berlin_weights_loaded']}")
    print(f"  Total Parameters: {total_params:,} (Expected: ~4,470,437)")
    assert total_params == 4470437, f"Unexpected parameter count: {total_params}"

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = RelativeLpLoss(eps=1e-5)

    # 3. Experiment 0: Smoke Training Test
    if smoke_only:
        print("\n" + "=" * 60)
        print("EXECUTING EXPERIMENT 0 (1-Epoch Smoke Training & Memory Profiling)")
        print("=" * 60)
        torch.cuda.reset_peak_memory_stats(device)
        model.train()
        optimizer.zero_grad()

        t0 = time.perf_counter()
        pred_train = model(x_train)
        torch.cuda.synchronize()
        t_fwd = time.perf_counter() - t0

        loss_train, h_loss_tr, u_loss_tr, v_loss_tr = loss_fn(pred_train, y_train)

        t1 = time.perf_counter()
        loss_train.backward()
        torch.cuda.synchronize()
        t_bwd = time.perf_counter() - t1

        optimizer.step()
        torch.cuda.synchronize()
        t_total = time.perf_counter() - t0

        # Validation step
        model.eval()
        with torch.no_grad():
            pred_val = model(x_val)
            loss_val, h_loss_v, u_loss_v, v_loss_v = loss_fn(pred_val, y_val)

        peak_alloc = torch.cuda.max_memory_allocated(device) / (1024 ** 2)
        peak_res = torch.cuda.max_memory_reserved(device) / (1024 ** 2)

        print(f"  Forward Pass Time:   {t_fwd * 1000:.2f} ms")
        print(f"  Backward Pass Time:  {t_bwd * 1000:.2f} ms")
        print(f"  Total Step Time:     {t_total * 1000:.2f} ms")
        print(f"  Train Relative Loss: {loss_train.item():.6f} (H: {h_loss_tr.item():.4f}, U: {u_loss_tr.item():.4f}, V: {v_loss_tr.item():.4f})")
        print(f"  Val Relative Loss:   {loss_val.item():.6f} (H: {h_loss_v.item():.4f}, U: {u_loss_v.item():.4f}, V: {v_loss_v.item():.4f})")
        print(f"  Peak Allocated VRAM: {peak_alloc:.2f} MB ({peak_alloc / 1024:.3f} GB)")
        print(f"  Peak Reserved VRAM:  {peak_res:.2f} MB ({peak_res / 1024:.3f} GB)")
        print(f"  CUDA OOM:            NO (Success)")
        print("=" * 60)
        return

    # 4. Experiment 1: Controlled Training (Max 30 Epochs, Early Stopping)
    print("\n" + "=" * 60)
    print(f"EXECUTING EXPERIMENT 1 (Max {epochs} Epochs, Early Stopping Patience={patience})")
    print("=" * 60)

    with open(csv_log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "epoch", "train_loss", "val_loss", "H_loss", "U_loss", "V_loss",
            "learning_rate", "epoch_time_sec", "GPU_allocated_MB", "GPU_reserved_MB"
        ])

    best_val_loss = float("inf")
    best_epoch = -1
    patience_counter = 0
    best_checkpoint_path = os.path.join(ckpt_dir, "best_dno_checkpoint.pt")
    final_checkpoint_path = os.path.join(ckpt_dir, "final_dno_checkpoint.pt")

    for epoch in range(1, epochs + 1):
        t_ep_start = time.perf_counter()
        torch.cuda.reset_peak_memory_stats(device)

        # Train Step
        model.train()
        optimizer.zero_grad()
        pred_train = model(x_train)
        loss_train, h_tr, u_tr, v_tr = loss_fn(pred_train, y_train)
        loss_train.backward()
        optimizer.step()

        # Validation Step
        model.eval()
        with torch.no_grad():
            pred_val = model(x_val)
            loss_val, h_val, u_val, v_val = loss_fn(pred_val, y_val)

        torch.cuda.synchronize()
        ep_time = time.perf_counter() - t_ep_start
        peak_alloc = torch.cuda.max_memory_allocated(device) / (1024 ** 2)
        peak_res = torch.cuda.max_memory_reserved(device) / (1024 ** 2)

        # Log to CSV
        with open(csv_log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                epoch, f"{loss_train.item():.6f}", f"{loss_val.item():.6f}",
                f"{h_val.item():.6f}", f"{u_val.item():.6f}", f"{v_val.item():.6f}",
                lr, f"{ep_time:.3f}", f"{peak_alloc:.2f}", f"{peak_res:.2f}"
            ])

        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Rel Loss: {loss_train.item():.5f} | Val Rel Loss: {loss_val.item():.5f} (H:{h_val.item():.4f}, U:{u_val.item():.4f}, V:{v_val.item():.4f}) | Time: {ep_time:.2f}s | VRAM: {peak_alloc:.1f}MB")

        # Checkpoint Saving & Early Stopping Check
        if loss_val.item() < best_val_loss:
            best_val_loss = loss_val.item()
            best_epoch = epoch
            patience_counter = 0

            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "train_loss": loss_train.item(),
                "val_loss": loss_val.item(),
                "val_h_loss": h_val.item(),
                "val_u_loss": u_val.item(),
                "val_v_loss": v_val.item(),
                "model_config": model_config,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }, best_checkpoint_path)
            print(f"  --> Saved new best checkpoint at epoch {epoch:02d} (Val Loss: {best_val_loss:.5f})")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\n[!] Early stopping triggered at epoch {epoch:02d} (patience={patience} exhausted).")
                break

    # Save Final Checkpoint
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "train_loss": loss_train.item(),
        "val_loss": loss_val.item(),
        "model_config": model_config,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }, final_checkpoint_path)
    print(f"\nTraining completed. Best validation epoch: {best_epoch:02d} with Val Loss: {best_val_loss:.5f}")

    # 5. Out-of-Sample Test Evaluation on Event 03 (Monsoon Moderate)
    print("\n" + "=" * 60)
    print("EVALUATING BEST CHECKPOINT ON UNSEEN TEST EVENT (event_03_monsoon_moderate)")
    print("=" * 60)

    best_ckpt = torch.load(best_checkpoint_path)
    model.load_state_dict(best_ckpt["model_state_dict"])
    model.eval()

    # Benchmark DNO inference speed
    torch.cuda.synchronize()
    t_inf_start = time.perf_counter()
    with torch.no_grad():
        pred_test = model(x_test)
    torch.cuda.synchronize()
    dno_inf_sec = time.perf_counter() - t_inf_start

    pred_test_np = pred_test.squeeze(0).cpu().numpy()  # [Sy=128, Sx=128, T=24, C=3]
    y_test_np = y_test.squeeze(0).cpu().numpy()        # [Sy=128, Sx=128, T=24, C=3]

    H_pred, U_pred, V_pred = pred_test_np[..., 0], pred_test_np[..., 1], pred_test_np[..., 2]
    H_true, U_true, V_true = y_test_np[..., 0], y_test_np[..., 1], y_test_np[..., 2]

    # Compute Physical Metrics
    h_metrics = evaluate_metrics(H_pred, H_true)
    u_metrics = evaluate_metrics(U_pred, U_true)
    v_metrics = evaluate_metrics(V_pred, V_true)

    # Inundation CSI / IoU
    csi_5cm, hits, misses, fas = compute_wet_overlap(H_pred[:, :, -1], H_true[:, :, -1], threshold=0.05)

    # Peak depth and peak timing error
    # Domain max depth over time
    true_peak_series = np.max(H_true, axis=(0, 1))  # [T=24]
    pred_peak_series = np.max(H_pred, axis=(0, 1))  # [T=24]

    t_peak_true_idx = int(np.argmax(true_peak_series))
    t_peak_pred_idx = int(np.argmax(pred_peak_series))
    true_peak_val = float(true_peak_series[t_peak_true_idx])
    pred_peak_val = float(pred_peak_series[t_peak_pred_idx])
    peak_depth_err = pred_peak_val - true_peak_val
    timing_err_minutes = (t_peak_pred_idx - t_peak_true_idx) * 5.0  # 5 min timesteps

    print("\n--- TEST EVALUATION METRICS (Event 03: Northeast Monsoon Moderate) ---")
    print(f"Water Depth (H):")
    print(f"  MAE:              {h_metrics['mae']:.4f} m ({h_metrics['mae'] * 100:.2f} cm)")
    print(f"  RMSE:             {h_metrics['rmse']:.4f} m ({h_metrics['rmse'] * 100:.2f} cm)")
    print(f"  Max Absolute Err: {h_metrics['max_err']:.4f} m")
    print(f"  Spatial Corr:     {h_metrics['corr']:.4f}")
    print(f"  Wet Cell CSI:     {csi_5cm:.4f} (Hits: {hits}, Misses: {misses}, False Alarms: {fas})")
    print(f"  True Peak Depth:  {true_peak_val:.4f} m (at t={t_peak_true_idx * 5} min)")
    print(f"  Pred Peak Depth:  {pred_peak_val:.4f} m (at t={t_peak_pred_idx * 5} min)")
    print(f"  Peak Depth Error: {peak_depth_err:+.4f} m | Timing Error: {timing_err_minutes:+.1f} min")

    print(f"\nX Velocity (U):")
    print(f"  MAE:              {u_metrics['mae']:.4f} m/s")
    print(f"  RMSE:             {u_metrics['rmse']:.4f} m/s")
    print(f"  Max Absolute Err: {u_metrics['max_err']:.4f} m/s")
    print(f"  Correlation:      {u_metrics['corr']:.4f}")

    print(f"\nY Velocity (V):")
    print(f"  MAE:              {v_metrics['mae']:.4f} m/s")
    print(f"  RMSE:             {v_metrics['rmse']:.4f} m/s")
    print(f"  Max Absolute Err: {v_metrics['max_err']:.4f} m/s")
    print(f"  Correlation:      {v_metrics['corr']:.4f}")

    # Speed Comparison
    hydro_sim_sec = 3.004  # Measured execution time of LISFLOOD solver for event 03
    speedup = hydro_sim_sec / dno_inf_sec
    print(f"\n--- SPEED BENCHMARK ---")
    print(f"  2D Hydrodynamic Solver Runtime: {hydro_sim_sec:.3f} s")
    print(f"  DNO Neural Surrogate Runtime:   {dno_inf_sec:.4f} s ({dno_inf_sec * 1000:.1f} ms)")
    print(f"  Measured Acceleration:          {speedup:.1f}x faster than numerical solver")

    # 6. Generate Diagnostic Plots (Spatial & Temporal Validation)
    print("\n[6] Generating Diagnostic Physical Validation Plots...")
    fig, axes = plt.subplots(3, 3, figsize=(15, 13))

    # Time slice for spatial visualization: final step (t = 24, 2 hours)
    t_plot = 23

    # H Plots
    vmax_h = max(float(H_true[:, :, t_plot].max()), 0.5)
    im0 = axes[0, 0].imshow(H_true[:, :, t_plot], cmap="Blues", vmin=0, vmax=vmax_h)
    axes[0, 0].set_title(f"True Depth H (t=120m)\nMax: {H_true[:, :, t_plot].max():.2f}m")
    plt.colorbar(im0, ax=axes[0, 0], fraction=0.046, pad=0.04)

    im1 = axes[0, 1].imshow(H_pred[:, :, t_plot], cmap="Blues", vmin=0, vmax=vmax_h)
    axes[0, 1].set_title(f"DNO Predicted H (t=120m)\nMax: {H_pred[:, :, t_plot].max():.2f}m")
    plt.colorbar(im1, ax=axes[0, 1], fraction=0.046, pad=0.04)

    err_h = np.abs(H_pred[:, :, t_plot] - H_true[:, :, t_plot])
    im2 = axes[0, 2].imshow(err_h, cmap="Reds", vmin=0, vmax=max(err_h.max(), 0.1))
    axes[0, 2].set_title(f"Absolute Error |H - H_true|\nMAE: {err_h.mean():.3f}m | Max: {err_h.max():.2f}m")
    plt.colorbar(im2, ax=axes[0, 2], fraction=0.046, pad=0.04)

    # U Plots
    vlim_u = max(abs(float(U_true[:, :, t_plot].min())), abs(float(U_true[:, :, t_plot].max())), 0.5)
    im3 = axes[1, 0].imshow(U_true[:, :, t_plot], cmap="coolwarm", vmin=-vlim_u, vmax=vlim_u)
    axes[1, 0].set_title(f"True Velocity U (t=120m)\nRange: [{U_true[:, :, t_plot].min():.2f}, {U_true[:, :, t_plot].max():.2f}] m/s")
    plt.colorbar(im3, ax=axes[1, 0], fraction=0.046, pad=0.04)

    im4 = axes[1, 1].imshow(U_pred[:, :, t_plot], cmap="coolwarm", vmin=-vlim_u, vmax=vlim_u)
    axes[1, 1].set_title(f"DNO Predicted U (t=120m)\nRange: [{U_pred[:, :, t_plot].min():.2f}, {U_pred[:, :, t_plot].max():.2f}] m/s")
    plt.colorbar(im4, ax=axes[1, 1], fraction=0.046, pad=0.04)

    err_u = np.abs(U_pred[:, :, t_plot] - U_true[:, :, t_plot])
    im5 = axes[1, 2].imshow(err_u, cmap="Oranges", vmin=0, vmax=max(err_u.max(), 0.2))
    axes[1, 2].set_title(f"Absolute Error |U - U_true|\nMAE: {err_u.mean():.3f}m/s")
    plt.colorbar(im5, ax=axes[1, 2], fraction=0.046, pad=0.04)

    # V Plots
    vlim_v = max(abs(float(V_true[:, :, t_plot].min())), abs(float(V_true[:, :, t_plot].max())), 0.5)
    im6 = axes[2, 0].imshow(V_true[:, :, t_plot], cmap="coolwarm", vmin=-vlim_v, vmax=vlim_v)
    axes[2, 0].set_title(f"True Velocity V (t=120m)\nRange: [{V_true[:, :, t_plot].min():.2f}, {V_true[:, :, t_plot].max():.2f}] m/s")
    plt.colorbar(im6, ax=axes[2, 0], fraction=0.046, pad=0.04)

    im7 = axes[2, 1].imshow(V_pred[:, :, t_plot], cmap="coolwarm", vmin=-vlim_v, vmax=vlim_v)
    axes[2, 1].set_title(f"DNO Predicted V (t=120m)\nRange: [{V_pred[:, :, t_plot].min():.2f}, {V_pred[:, :, t_plot].max():.2f}] m/s")
    plt.colorbar(im7, ax=axes[2, 1], fraction=0.046, pad=0.04)

    err_v = np.abs(V_pred[:, :, t_plot] - V_true[:, :, t_plot])
    im8 = axes[2, 2].imshow(err_v, cmap="Oranges", vmin=0, vmax=max(err_v.max(), 0.2))
    axes[2, 2].set_title(f"Absolute Error |V - V_true|\nMAE: {err_v.mean():.3f}m/s")
    plt.colorbar(im8, ax=axes[2, 2], fraction=0.046, pad=0.04)

    for ax in axes.flat:
        ax.set_xticks([])
        ax.set_yticks([])

    plt.tight_layout()
    plot_spatial_path = os.path.join(out_dir, "chennai_dno_test_spatial_comparison.png")
    plt.savefig(plot_spatial_path, dpi=180)
    plt.close()
    print(f"  Saved spatial comparison plot: {plot_spatial_path}")

    # Temporal Hydrograph Plot
    time_minutes = np.arange(1, 25) * 5.0  # 5, 10, ..., 120 min
    domain_mean_true = np.mean(H_true, axis=(0, 1))
    domain_mean_pred = np.mean(H_pred, axis=(0, 1))

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(time_minutes, true_peak_series, "b-o", label="True Domain Max Depth (m)", linewidth=2)
    ax1.plot(time_minutes, pred_peak_series, "b--s", label="DNO Pred Max Depth (m)", linewidth=2)
    ax1.plot(time_minutes, domain_mean_true, "g-^", label="True Domain Mean Depth (m)", linewidth=1.5)
    ax1.plot(time_minutes, domain_mean_pred, "g--v", label="DNO Pred Mean Depth (m)", linewidth=1.5)

    ax1.set_xlabel("Elapsed Simulation Time (minutes)", fontsize=11)
    ax1.set_ylabel("Water Depth (meters)", fontsize=11)
    ax1.set_title("Test Event 03 (Northeast Monsoon): Hydrodynamic Target vs DNO Surrogate Evolution", fontsize=12)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="upper left")

    plot_temporal_path = os.path.join(out_dir, "chennai_dno_test_temporal_hydrograph.png")
    plt.savefig(plot_temporal_path, dpi=180)
    plt.close()
    print(f"  Saved temporal hydrograph plot: {plot_temporal_path}")

    # 7. Summary Metrics Export
    summary_dict = {
        "experiment": "Experiment 1 — Controlled DNO Training",
        "dataset_classification": "SIMULATED HYDRODYNAMIC TRAINING DATA",
        "model_parameters": total_params,
        "epochs_completed": epoch,
        "best_epoch": best_epoch,
        "best_val_loss": float(best_val_loss),
        "final_train_loss": float(loss_train.item()),
        "test_metrics_event_03": {
            "water_depth_H": h_metrics,
            "velocity_U": u_metrics,
            "velocity_V": v_metrics,
            "wet_cell_csi_5cm": csi_5cm,
            "peak_depth_true_m": true_peak_val,
            "peak_depth_pred_m": pred_peak_val,
            "peak_depth_error_m": peak_depth_err,
            "timing_error_minutes": timing_err_minutes
        },
        "speed_benchmark": {
            "hydrodynamic_simulation_sec": hydro_sim_sec,
            "dno_inference_sec": dno_inf_sec,
            "speedup_factor": speedup
        },
        "checkpoints": {
            "best": best_checkpoint_path,
            "final": final_checkpoint_path
        },
        "plots": {
            "spatial": plot_spatial_path,
            "temporal": plot_temporal_path
        }
    }

    metrics_json_path = os.path.join(log_dir, "chennai_dno_test_summary.json")
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2)
    print(f"  Saved summary metrics JSON: {metrics_json_path}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke_only", action="store_true", help="Run 1-epoch smoke test only")
    parser.add_argument("--epochs", type=int, default=30, help="Maximum epochs")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    args = parser.parse_args()

    run_experiment(
        smoke_only=args.smoke_only,
        epochs=args.epochs,
        lr=args.lr,
        patience=args.patience
    )
