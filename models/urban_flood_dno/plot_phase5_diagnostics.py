"""
Phase 5 Pilot Visual Diagnostics Plotter
FloodWatch AI — SIH26085

Generates all 8 required diagnostic plots for the 10-event synthetic storm pilot:
1. rainfall_distribution.png
2. rainfall_profiles.png
3. rainfall_vs_peak_depth.png
4. rainfall_vs_wet_fraction.png
5. max_depth_distribution.png
6. velocity_distribution.png
7. simulation_runtime.png
8. dataset_split.png
"""

import os
import json
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def generate_all_plots():
    storm_lib = os.path.join(REPO_ROOT, "Data", "dno", "chennai", "storm_library")
    meta_dir = os.path.join(storm_lib, "metadata")
    rainfall_dir = os.path.join(storm_lib, "rainfall")
    sim_dir = os.path.join(storm_lib, "simulations")
    out_dir = os.path.join(REPO_ROOT, "outputs", "chennai_dno", "phase5_pilot")
    os.makedirs(out_dir, exist_ok=True)

    # Load manifest and runtime CSV
    manifest_path = os.path.join(meta_dir, "storm_library_manifest.json")
    runtime_csv_path = os.path.join(meta_dir, "simulation_runtime.csv")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    runtime_data = []
    with open(runtime_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            runtime_data.append(r)

    storm_ids = [r["event_id"] for r in runtime_data]
    totals = [float(r["rainfall_total_mm"]) for r in runtime_data]
    profiles = [r["profile"] for r in runtime_data]
    max_depths = [float(r["max_depth_m"]) for r in runtime_data]
    mean_depths = [float(r["mean_depth_m"]) for r in runtime_data]
    wet_5cm = [float(r["wet_fraction_5cm"]) * 100 for r in runtime_data]
    wet_10cm = [float(r["wet_fraction_10cm"]) * 100 for r in runtime_data]
    max_vels = [float(r["max_velocity_mps"]) for r in runtime_data]
    mean_vels = [float(r["mean_velocity_mps"]) for r in runtime_data]
    runtimes = [float(r["simulation_seconds"]) for r in runtime_data]

    # Assign colors by temporal profile
    palette = {
        "uniform": "#2b5c8f",
        "front_loaded": "#d95f02",
        "center_loaded": "#7570b3",
        "back_loaded": "#1b9e77",
        "multi_peak": "#e7298a"
    }

    # 1. rainfall_distribution.png
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(storm_ids, totals, color=[palette[p] for p in profiles], edgecolor="black", alpha=0.85)
    ax.set_ylabel("Total Rainfall Accumulation (mm)", fontsize=11)
    ax.set_title("Phase 5 Pilot: Synthetic Rainfall Total Distribution Across 10 Events", fontsize=12, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:.0f} mm",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9, fontweight="bold")
    plt.xticks(rotation=45)
    plt.tight_layout()
    p1 = os.path.join(out_dir, "rainfall_distribution.png")
    plt.savefig(p1, dpi=180)
    plt.close()

    # 2. rainfall_profiles.png (Hyetographs across 24 steps)
    fig, ax = plt.subplots(figsize=(11, 6))
    time_min = np.arange(1, 25) * 5.0
    for idx, eid in enumerate(storm_ids):
        rf = np.load(os.path.join(rainfall_dir, f"{eid}_rainfall.npy"))
        ax.plot(time_min, rf, label=f"{eid} ({totals[idx]:.0f}mm, {profiles[idx]})",
                color=palette[profiles[idx]], linewidth=2, alpha=0.85,
                linestyle="-" if "loaded" in profiles[idx] else ("--" if profiles[idx] == "uniform" else "-."))
    ax.set_xlabel("Elapsed Time (minutes)", fontsize=11)
    ax.set_ylabel("Rainfall Intensity (mm/hr)", fontsize=11)
    ax.set_title("Temporal Hyetographs: 10 Synthetic Storms (Adyar–Velachery Domain)", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", fontsize=8, ncol=2)
    plt.tight_layout()
    p2 = os.path.join(out_dir, "rainfall_profiles.png")
    plt.savefig(p2, dpi=180)
    plt.close()

    # 3. rainfall_vs_peak_depth.png
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, eid in enumerate(storm_ids):
        ax.scatter(totals[i], max_depths[i], s=90, color=palette[profiles[i]], edgecolors="black", zorder=3)
        ax.annotate(f"{eid} ({max_depths[i]:.2f}m)", (totals[i] + 1.5, max_depths[i] - 0.04), fontsize=8.5)
    # Monotonic trend fit
    z = np.polyfit(totals, max_depths, 2)
    p = np.poly1d(z)
    x_curve = np.linspace(10, 125, 100)
    ax.plot(x_curve, p(x_curve), "k--", alpha=0.5, label="2nd-Order Polynomial Trend")
    ax.set_xlabel("Total Rainfall (mm)", fontsize=11)
    ax.set_ylabel("Maximum Overland Flow Depth H (m)", fontsize=11)
    ax.set_title("Physical Response: Rainfall Total vs Maximum Water Depth", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")
    plt.tight_layout()
    p3 = os.path.join(out_dir, "rainfall_vs_peak_depth.png")
    plt.savefig(p3, dpi=180)
    plt.close()

    # 4. rainfall_vs_wet_fraction.png
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(totals, wet_5cm, "b-o", label="Inundated Cells > 5 cm (%)", linewidth=2)
    ax.plot(totals, wet_10cm, "r--s", label="Inundated Cells > 10 cm (%)", linewidth=2)
    ax.set_xlabel("Total Rainfall (mm)", fontsize=11)
    ax.set_ylabel("Domain Wet Surface Fraction (%)", fontsize=11)
    ax.set_title("Spatial Inundation Scaling: Rainfall Total vs Flooded Area", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")
    plt.tight_layout()
    p4 = os.path.join(out_dir, "rainfall_vs_wet_fraction.png")
    plt.savefig(p4, dpi=180)
    plt.close()

    # 5. max_depth_distribution.png
    fig, ax = plt.subplots(figsize=(9, 5))
    x_pos = np.arange(len(storm_ids))
    w = 0.35
    ax.bar(x_pos - w/2, max_depths, w, label="Maximum Depth H (m)", color="#1f77b4", edgecolor="black", alpha=0.85)
    ax.bar(x_pos + w/2, [m * 10 for m in mean_depths], w, label="Mean Depth H (cm x10)", color="#aec7e8", edgecolor="black", alpha=0.85)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(storm_ids, rotation=45)
    ax.set_ylabel("Depth (m)", fontsize=11)
    ax.set_title("Maximum & Mean Depth Response by Synthetic Event", fontsize=12, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")
    plt.tight_layout()
    p5 = os.path.join(out_dir, "max_depth_distribution.png")
    plt.savefig(p5, dpi=180)
    plt.close()

    # 6. velocity_distribution.png
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(storm_ids, max_vels, color="#2ca02c", edgecolor="black", alpha=0.85, label="Max Flow Velocity (m/s)")
    ax.plot(storm_ids, mean_vels, "k-o", label="Mean Flow Velocity (m/s)", linewidth=2)
    ax.set_ylabel("Velocity Magnitude (m/s)", fontsize=11)
    ax.set_title("Overland Flow Velocity Dynamics by Event", fontsize=12, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")
    plt.xticks(rotation=45)
    plt.tight_layout()
    p6 = os.path.join(out_dir, "velocity_distribution.png")
    plt.savefig(p6, dpi=180)
    plt.close()

    # 7. simulation_runtime.png
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(storm_ids, runtimes, color="#9467bd", edgecolor="black", alpha=0.85)
    ax.axhline(np.mean(runtimes), color="red", linestyle="--", label=f"Mean Runtime: {np.mean(runtimes):.2f}s")
    ax.set_ylabel("LISFLOOD-FP 2D Solver Runtime (seconds)", fontsize=11)
    ax.set_title("Numerical Hydrodynamic Execution Speed Across 10 Events", fontsize=12, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")
    plt.xticks(rotation=45)
    plt.tight_layout()
    p7 = os.path.join(out_dir, "simulation_runtime.png")
    plt.savefig(p7, dpi=180)
    plt.close()

    # 8. dataset_split.png
    fig, ax = plt.subplots(figsize=(8, 5))
    split_colors = {"TRAIN": "#31a354", "VAL": "#feb24c", "TEST": "#f03b20"}
    split_counts = {
        "TRAIN (70%)": len(manifest["train_events"]),
        "VALIDATION (20%)": len(manifest["validation_events"]),
        "TEST (10%)": len(manifest["test_events"])
    }
    ax.bar(list(split_counts.keys()), list(split_counts.values()),
           color=["#31a354", "#feb24c", "#f03b20"], edgecolor="black", alpha=0.85, width=0.5)
    ax.set_ylabel("Number of Storm Events", fontsize=11)
    ax.set_title("Stratified Train / Validation / Test Event Partitions", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 8)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for idx, (k, v) in enumerate(split_counts.items()):
        ax.annotate(f"{v} Storms", xy=(idx, v), xytext=(0, 4),
                    textcoords="offset points", ha="center", fontweight="bold")
    plt.tight_layout()
    p8 = os.path.join(out_dir, "dataset_split.png")
    plt.savefig(p8, dpi=180)
    plt.close()

    print("=" * 70)
    print(" ALL 8 DIAGNOSTIC PLOTS SUCCESSFULLY GENERATED:")
    for p in [p1, p2, p3, p4, p5, p6, p7, p8]:
        print(f"  --> {os.path.basename(p)}")
    print(f" Saved in directory: {out_dir}")
    print("=" * 70)


if __name__ == "__main__":
    generate_all_plots()
