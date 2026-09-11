"""
Phase 5 Expanded Visual Diagnostics Plotter (30 Events)
FloodWatch AI — SIH26085

Generates all 10 required diagnostic plots for the 30-event expanded synthetic storm library:
1. rainfall_distribution.png
2. rainfall_profiles.png
3. rainfall_vs_global_peak_depth.png
4. rainfall_vs_interior_peak_depth.png
5. rainfall_vs_wet_fraction.png
6. rainfall_vs_peak_velocity.png
7. max_depth_distribution.png
8. velocity_distribution.png
9. simulation_runtime.png
10. dataset_split.png
"""

import os
import json
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def generate_expanded_plots():
    storm_lib = os.path.join(REPO_ROOT, "Data", "dno", "chennai", "storm_library")
    meta_dir = os.path.join(storm_lib, "metadata")
    rainfall_dir = os.path.join(storm_lib, "rainfall")
    sim_dir = os.path.join(storm_lib, "simulations")
    out_dir = os.path.join(REPO_ROOT, "outputs", "chennai_dno", "phase5_expanded")
    os.makedirs(out_dir, exist_ok=True)

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
    global_max_depths = [float(r["max_depth_m"]) for r in runtime_data]
    interior_max_depths = [float(r["interior_max_depth_m"]) for r in runtime_data]
    mean_depths = [float(r["mean_depth_m"]) for r in runtime_data]
    wet_5cm = [float(r["wet_fraction_5cm"]) * 100 for r in runtime_data]
    wet_10cm = [float(r["wet_fraction_10cm"]) * 100 for r in runtime_data]
    max_vels = [float(r["max_velocity_mps"]) for r in runtime_data]
    mean_vels = [float(r["mean_velocity_mps"]) for r in runtime_data]
    runtimes = [float(r["simulation_seconds"]) for r in runtime_data]

    # Assign colors by temporal profile
    palette = {
        "uniform": "#2563eb",
        "front_loaded": "#d97706",
        "center_loaded": "#7c3aed",
        "back_loaded": "#059669",
        "multi_peak": "#db2777"
    }

    # Helper function to style plots cleanly
    def apply_plot_style(ax, title, xlabel, ylabel):
        ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
        ax.set_xlabel(xlabel, fontsize=10, fontweight="bold")
        ax.set_ylabel(ylabel, fontsize=10, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.5)

    # 1. rainfall_distribution.png
    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(storm_ids, totals, color=[palette[p] for p in profiles], edgecolor="black", linewidth=0.7, alpha=0.85)
    apply_plot_style(ax, "Chennai DNO Phase 5 Expansion: Total Rainfall Distribution Across 30 Events", "Storm Event ID", "Total Rainfall (mm)")
    plt.xticks(rotation=45, ha="right", fontsize=9)
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 2), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "rainfall_distribution.png"), dpi=200)
    plt.close()

    # 2. rainfall_profiles.png
    fig, ax = plt.subplots(figsize=(13, 7))
    time_min = np.arange(1, 25) * 5.0
    for idx, eid in enumerate(storm_ids):
        rf = np.load(os.path.join(rainfall_dir, f"{eid}_rainfall.npy"))
        ax.plot(time_min, rf, label=f"{eid} ({totals[idx]:.0f}mm, {profiles[idx]})" if idx < 12 or idx in [15, 20, 25, 29] else None,
                color=palette[profiles[idx]], linewidth=1.8, alpha=0.75)
    apply_plot_style(ax, "Temporal Hyetographs: 30 Synthetic Storms (Adyar–Velachery Domain)", "Elapsed Simulation Time (minutes)", "Rainfall Intensity (mm/hr)")
    ax.legend(loc="upper right", fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "rainfall_profiles.png"), dpi=200)
    plt.close()

    # 3. rainfall_vs_global_peak_depth.png
    fig, ax = plt.subplots(figsize=(9, 6))
    for p in palette:
        mask = [i for i, prof in enumerate(profiles) if prof == p]
        ax.scatter([totals[i] for i in mask], [global_max_depths[i] for i in mask],
                   color=palette[p], s=80, edgecolors="black", linewidth=0.7, label=p.replace("_", " ").title(), alpha=0.85)
    apply_plot_style(ax, "Total Rainfall vs. Global Maximum Depth (Includes 0.8m MSL East Tide Boundary)", "Total Rainfall (mm)", "Global Maximum Water Depth H (m)")
    ax.axhline(0.80, color="red", linestyle=":", linewidth=1.5, label="Tidal Boundary Stage (0.80m MSL)")
    ax.legend(loc="upper left", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "rainfall_vs_global_peak_depth.png"), dpi=200)
    plt.close()

    # 4. rainfall_vs_interior_peak_depth.png
    fig, ax = plt.subplots(figsize=(9, 6))
    for p in palette:
        mask = [i for i, prof in enumerate(profiles) if prof == p]
        ax.scatter([totals[i] for i in mask], [interior_max_depths[i] for i in mask],
                   color=palette[p], s=80, edgecolors="black", linewidth=0.7, label=p.replace("_", " ").title(), alpha=0.85)
    # Trendline
    z = np.polyfit(totals, interior_max_depths, 2)
    p_fit = np.poly1d(z)
    x_line = np.linspace(min(totals), max(totals), 100)
    ax.plot(x_line, p_fit(x_line), "k--", alpha=0.6, label="Polynomial Trendline")
    apply_plot_style(ax, "Total Rainfall vs. Interior Maximum Depth (Excludes East Boundary Col 127)", "Total Rainfall (mm)", "Interior Maximum Water Depth H (m)")
    ax.legend(loc="upper left", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "rainfall_vs_interior_peak_depth.png"), dpi=200)
    plt.close()

    # 5. rainfall_vs_wet_fraction.png
    fig, ax = plt.subplots(figsize=(9, 6))
    for p in palette:
        mask = [i for i, prof in enumerate(profiles) if prof == p]
        ax.scatter([totals[i] for i in mask], [wet_5cm[i] for i in mask],
                   color=palette[p], s=80, marker="o", edgecolors="black", linewidth=0.7, label=f"{p.title()} (>5cm)", alpha=0.85)
    apply_plot_style(ax, "Total Rainfall vs. Final Inundated Cell Fraction (>5cm Depth)", "Total Rainfall (mm)", "Inundated Grid Cell Fraction (%)")
    ax.legend(loc="upper left", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "rainfall_vs_wet_fraction.png"), dpi=200)
    plt.close()

    # 6. rainfall_vs_peak_velocity.png
    fig, ax = plt.subplots(figsize=(9, 6))
    for p in palette:
        mask = [i for i, prof in enumerate(profiles) if prof == p]
        ax.scatter([totals[i] for i in mask], [max_vels[i] for i in mask],
                   color=palette[p], s=80, edgecolors="black", linewidth=0.7, label=p.replace("_", " ").title(), alpha=0.85)
    apply_plot_style(ax, "Total Rainfall vs. Peak Flow Velocity (m/s)", "Total Rainfall (mm)", "Peak Horizontal Flow Velocity (m/s)")
    ax.legend(loc="upper left", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "rainfall_vs_peak_velocity.png"), dpi=200)
    plt.close()

    # 7. max_depth_distribution.png
    fig, ax = plt.subplots(figsize=(14, 6))
    x_indices = np.arange(len(storm_ids))
    w = 0.38
    ax.bar(x_indices - w/2, global_max_depths, width=w, label="Global Max Depth (Includes Coast)", color="#3b82f6", alpha=0.85)
    ax.bar(x_indices + w/2, interior_max_depths, width=w, label="Interior Max Depth (Excludes Coast)", color="#10b981", alpha=0.85)
    ax.set_xticks(x_indices)
    ax.set_xticklabels(storm_ids, rotation=45, ha="right", fontsize=9)
    apply_plot_style(ax, "Comparison of Global vs. Interior Peak Depths Across All 30 Storms", "Storm Event ID", "Water Depth (m)")
    ax.legend(loc="upper left", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "max_depth_distribution.png"), dpi=200)
    plt.close()

    # 8. velocity_distribution.png
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(storm_ids, max_vels, color="#f59e0b", edgecolor="black", linewidth=0.7, alpha=0.85)
    apply_plot_style(ax, "Peak Hydrodynamic Flow Velocity Across 30 Storm Events", "Storm Event ID", "Peak Velocity (m/s)")
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "velocity_distribution.png"), dpi=200)
    plt.close()

    # 9. simulation_runtime.png
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(storm_ids, runtimes, color="#6366f1", edgecolor="black", linewidth=0.7, alpha=0.85)
    ax.axhline(np.mean(runtimes), color="red", linestyle="--", label=f"Mean Runtime: {np.mean(runtimes):.2f}s")
    apply_plot_style(ax, "LISFLOOD-FP 2D Hydrodynamic Simulation Execution Time per Event", "Storm Event ID", "Execution Time (seconds)")
    plt.xticks(rotation=45, ha="right", fontsize=9)
    ax.legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "simulation_runtime.png"), dpi=200)
    plt.close()

    # 10. dataset_split.png
    fig, ax = plt.subplots(figsize=(8, 6))
    split_counts = {
        "TRAIN (21 Events, 70.0%)": len(manifest["train_events"]),
        "VALIDATION (4 Events, 13.3%)": len(manifest["validation_events"]),
        "TEST (5 Events, 16.7%)": len(manifest["test_events"])
    }
    colors = ["#2563eb", "#f59e0b", "#10b981"]
    wedges, texts, autotexts = ax.pie(
        split_counts.values(),
        labels=split_counts.keys(),
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        textprops=dict(color="black", fontweight="bold")
    )
    ax.set_title("Chennai DNO 30-Event Dataset Stratified Partitioning", fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "dataset_split.png"), dpi=200)
    plt.close()

    print(f"[PLOTTER] Generated all 10 visual diagnostic figures in: {out_dir}")

if __name__ == "__main__":
    generate_expanded_plots()
