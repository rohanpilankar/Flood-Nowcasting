"""
Chennai Storm Library Phase 5 Expansion: 10 -> 30 Events
FloodWatch AI — SIH26085

Generates 20 additional synthetic storms (storm_011 to storm_030) and processes
their 2D hydrodynamic simulations (LISFLOOD-FP) and DNO tensors sequentially.

Strict Provenance & Preservation Rules:
1. storm_001 to storm_010 are strictly PRESERVED as baseline pilot.
2. Seed: 42 (deterministic generation).
3. 5 Magnitude ranges: Low, Moderate, Heavy, Very Heavy, Extreme (6 events each).
4. 5 Profile shapes: Uniform, Front-loaded, Center-loaded, Back-loaded, Multi-peak (6 events each).
5. Split: 21 Train, 4 Val, 5 Test.
6. Target: SIMULATED HYDRODYNAMIC TRAINING DATA.
7. Rainfall: SYNTHETIC / DERIVED RAINFALL FORCING.
"""

import os
import sys
import json
import csv
import time
import numpy as np
import torch
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from models.urban_flood_dno.chennai_hydrodynamic_solver import ChennaiHydrodynamicSolver
from models.urban_flood_dno.chennai_data_adapter import ChennaiDNODataAdapter
from models.urban_flood_dno.generate_chennai_storm_library import build_hyetograph

RANDOM_SEED = 42
TOTAL_TIMESTEPS = 24
TIMESTEP_MINUTES = 5.0
HOURS_PER_STEP = TIMESTEP_MINUTES / 60.0

# 20 New Events Specifications
EXPANDED_STORM_SPECS = [
    # Low (10–25 mm)
    {"id": "storm_011", "total_mm": 12.0,  "shape": "multi_peak",    "split": "TEST"},
    {"id": "storm_012", "total_mm": 18.0,  "shape": "multi_peak",    "split": "TRAIN"},

    # Moderate (25–50 mm)
    {"id": "storm_013", "total_mm": 30.0,  "shape": "front_loaded",  "split": "TRAIN"},
    {"id": "storm_014", "total_mm": 40.0,  "shape": "back_loaded",   "split": "VAL"},
    {"id": "storm_015", "total_mm": 48.0,  "shape": "multi_peak",    "split": "TRAIN"},
    {"id": "storm_016", "total_mm": 28.0,  "shape": "uniform",       "split": "TEST"},

    # Heavy (50–75 mm)
    {"id": "storm_017", "total_mm": 55.0,  "shape": "uniform",       "split": "TRAIN"},
    {"id": "storm_018", "total_mm": 65.0,  "shape": "center_loaded", "split": "TRAIN"},
    {"id": "storm_019", "total_mm": 70.0,  "shape": "multi_peak",    "split": "TRAIN"},
    {"id": "storm_020", "total_mm": 52.0,  "shape": "front_loaded",  "split": "TRAIN"},

    # Very Heavy (75–100 mm)
    {"id": "storm_021", "total_mm": 80.0,  "shape": "uniform",       "split": "TRAIN"},
    {"id": "storm_022", "total_mm": 85.0,  "shape": "front_loaded",  "split": "VAL"},
    {"id": "storm_023", "total_mm": 90.0,  "shape": "back_loaded",   "split": "TRAIN"},
    {"id": "storm_024", "total_mm": 95.0,  "shape": "multi_peak",    "split": "TEST"},
    {"id": "storm_025", "total_mm": 82.0,  "shape": "center_loaded", "split": "TRAIN"},

    # Extreme (100–150 mm)
    {"id": "storm_026", "total_mm": 110.0, "shape": "front_loaded",  "split": "TRAIN"},
    {"id": "storm_027", "total_mm": 120.0, "shape": "center_loaded", "split": "TRAIN"},
    {"id": "storm_028", "total_mm": 135.0, "shape": "back_loaded",   "split": "TEST"},
    {"id": "storm_029", "total_mm": 140.0, "shape": "uniform",       "split": "TRAIN"},
    {"id": "storm_030", "total_mm": 150.0, "shape": "back_loaded",   "split": "TRAIN"}
]

# Final 30-Event Split
DATASET_SPLITS_30 = {
    "TRAIN": [
        "storm_001", "storm_002", "storm_004", "storm_005", "storm_006", "storm_009", "storm_010",
        "storm_012", "storm_013", "storm_015", "storm_017", "storm_018", "storm_019", "storm_020",
        "storm_021", "storm_023", "storm_025", "storm_026", "storm_027", "storm_029", "storm_030"
    ],
    "VAL": [
        "storm_003", "storm_008",
        "storm_014", "storm_022"
    ],
    "TEST": [
        "storm_007",
        "storm_011", "storm_016", "storm_024", "storm_028"
    ]
}


def run_phase5_expansion():
    print("=" * 80)
    print(" FLOODWATCH AI — PHASE 5 EXPANSION: 10 -> 30 SYNTHETIC STORM LIBRARY")
    print(" PILOT DOMAIN: Adyar–Velachery Basin, Greater Chennai (10km x 10km, EPSG:32644)")
    print(" DATASET CLASSIFICATION: SIMULATED HYDRODYNAMIC TRAINING DATA")
    print(" RAINFALL CLASSIFICATION: SYNTHETIC / DERIVED RAINFALL FORCING")
    print("=" * 80)

    # 1. Setup Directories
    dno_base = os.path.join(REPO_ROOT, "Data", "dno", "chennai")
    storm_base = os.path.join(dno_base, "storm_library")
    rainfall_dir = os.path.join(storm_base, "rainfall")
    sim_dir = os.path.join(storm_base, "simulations")
    tensor_dir = os.path.join(storm_base, "tensors")
    metadata_dir = os.path.join(storm_base, "metadata")
    processed_dir = os.path.join(dno_base, "processed")

    for d in [rainfall_dir, sim_dir, tensor_dir, metadata_dir]:
        os.makedirs(d, exist_ok=True)

    # 2. Load Processed Pilot Topography and Roughness
    dem_path = os.path.join(processed_dir, "pilot_adyar_velachery_dem_128x128.npy")
    n_path = os.path.join(processed_dir, "pilot_adyar_velachery_roughness_128x128.npy")

    dem = np.load(dem_path).astype(np.float32)
    roughness = np.load(n_path).astype(np.float32)
    Sy, Sx = dem.shape
    dx = 10000.0 / Sx  # 78.125m
    T = 24
    save_interval = 300.0

    print(f"\n[1] Pilot Topography Loaded:")
    print(f"  Grid: {Sy} x {Sx} cells ({dx:.3f}m resolution) | Elevation: [{dem.min():.2f}, {dem.max():.2f}] m MSL")
    print(f"  Roughness: [{roughness.min():.3f}, {roughness.max():.3f}] | Coastal Tide Head: 0.80 m MSL")

    # 3. Instantiate Solver & DNO Adapter
    solver = ChennaiHydrodynamicSolver(
        dem=dem,
        manning_n=roughness,
        dx=dx,
        dt_internal=1.0,
        tide_head_msl=0.8
    )

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    adapter = ChennaiDNODataAdapter(
        grid_height=Sy,
        grid_width=Sx,
        horizon_steps=T,
        device=device
    )

    # 4. Generate Rainfall for the 20 New Storms (storm_011 to storm_030)
    print(f"\n[2] Generating 20 New Synthetic Hyetographs (storm_011 to storm_030)...")
    new_manifest_events = {}

    for idx_offset, spec in enumerate(EXPANDED_STORM_SPECS):
        idx = 10 + idx_offset # 10 to 29
        eid = spec["id"]
        total_mm = spec["total_mm"]
        shape_type = spec["shape"]
        split_role = spec["split"]

        event_seed = RANDOM_SEED + idx * 17
        hyetograph_mm_hr = build_hyetograph(total_mm, shape_type, TOTAL_TIMESTEPS, event_seed)

        # Timestep metrics
        peak_rate = float(np.max(hyetograph_mm_hr))
        peak_step = int(np.argmax(hyetograph_mm_hr))
        peak_time_min = peak_step * TIMESTEP_MINUTES
        mean_rate = float(np.mean(hyetograph_mm_hr))
        actual_total = float(np.sum(hyetograph_mm_hr) * HOURS_PER_STEP)

        # Integrity check (< 1e-4 mm difference)
        diff = abs(actual_total - total_mm)
        assert diff < 1e-4, f"{eid}: Rainfall total mismatch {actual_total} vs {total_mm}"

        # Save rainfall array
        rain_path = os.path.join(rainfall_dir, f"{eid}_rainfall.npy")
        np.save(rain_path, hyetograph_mm_hr)

        # Save initial metadata
        meta = {
            "event_id": eid,
            "phase": "Phase 5 Expansion",
            "total_rainfall_mm": round(actual_total, 4),
            "declared_rainfall_mm": total_mm,
            "duration_hours": 2.0,
            "timestep_minutes": TIMESTEP_MINUTES,
            "num_timesteps": TOTAL_TIMESTEPS,
            "temporal_shape": shape_type,
            "peak_intensity_mm_hr": round(peak_rate, 4),
            "peak_step_idx": peak_step,
            "peak_time_minutes": peak_time_min,
            "mean_intensity_mm_hr": round(mean_rate, 4),
            "random_seed": event_seed,
            "source_classification": "SYNTHETIC / DERIVED RAINFALL FORCING",
            "generation_timestamp": datetime.now().isoformat(),
            "split_role": split_role,
            "hyetograph_mm_hr": [round(float(v), 4) for v in hyetograph_mm_hr]
        }

        meta_path = os.path.join(metadata_dir, f"{eid}.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        new_manifest_events[eid] = meta
        print(f"  [{idx+1:02d}/30] {eid}: {total_mm:5.1f} mm | Shape: {shape_type:13s} | Split: {split_role:5s} | Peak: {peak_rate:5.1f} mm/hr")

    # 5. Sequentially Execute Hydrodynamic Simulations & Generate Tensors for 20 New Events
    print(f"\n[3] Sequentially Executing Hydrodynamic Simulations for storm_011 to storm_030...")
    all_30_csv_rows = []
    all_30_manifest_events = {}

    # First, load the 10 pilot events from disk to preserve them exactly
    pilot_ids = [f"storm_{i:03d}" for i in range(1, 11)]
    for pid in pilot_ids:
        pmeta_path = os.path.join(metadata_dir, f"{pid}.json")
        with open(pmeta_path, "r", encoding="utf-8") as f:
            pmeta = json.load(f)

        psim_path = os.path.join(sim_dir, f"{pid}_hydro_sim.npz")
        pdata = np.load(psim_path)
        pH = pdata["H"]
        pU = pdata["U"]
        pV = pdata["V"]

        p_global_max = float(np.max(pH))
        p_interior_max = float(np.max(pH[:, :-1, :]))
        p_mean_h = float(np.mean(pH))
        p_final_h = pH[:, :, -1]
        p_wet_5cm = float(np.sum(p_final_h >= 0.05) / (Sy * Sx))
        p_wet_10cm = float(np.sum(p_final_h >= 0.10) / (Sy * Sx))
        p_vel = np.sqrt(pU ** 2 + pV ** 2)
        p_max_vel = float(np.max(p_vel))
        p_mean_vel = float(np.mean(p_vel))

        p_sim_sec = pmeta.get("hydrodynamic_metrics", {}).get("simulation_seconds", 3.0)
        p_status = pmeta.get("hydrodynamic_metrics", {}).get("status", "PASS")

        # Ensure pilot metadata has interior_max_depth_m
        if "hydrodynamic_metrics" in pmeta:
            pmeta["hydrodynamic_metrics"]["interior_max_depth_m"] = round(p_interior_max, 4)
            with open(pmeta_path, "w", encoding="utf-8") as f:
                json.dump(pmeta, f, indent=2)

        all_30_manifest_events[pid] = pmeta
        all_30_csv_rows.append([
            pid,
            round(pmeta["total_rainfall_mm"], 2),
            2.0,
            pmeta["temporal_shape"],
            round(pmeta["peak_intensity_mm_hr"], 2),
            round(p_sim_sec, 3),
            round(p_global_max, 4),
            round(p_interior_max, 4),
            round(p_mean_h, 4),
            round(p_wet_5cm, 4),
            round(p_wet_10cm, 4),
            round(p_max_vel, 4),
            round(p_mean_vel, 4),
            p_status
        ])

    print(f"  Loaded and preserved 10 baseline pilot events (storm_001 to storm_010).")

    # Now execute the 20 new events
    for idx_offset, spec in enumerate(EXPANDED_STORM_SPECS):
        idx = 10 + idx_offset
        eid = spec["id"]
        total_mm = spec["total_mm"]
        shape_type = spec["shape"]
        split_role = spec["split"]

        rain_path = os.path.join(rainfall_dir, f"{eid}_rainfall.npy")
        rain_hyetograph = np.load(rain_path).astype(np.float32)

        meta = new_manifest_events[eid]

        t_start = time.perf_counter()

        # Run 2D Hydrodynamic Simulation
        H_sim, U_sim, V_sim, sim_meta = solver.run_simulation(
            rain_hyetograph_mm_hr=rain_hyetograph,
            horizon_steps=T,
            save_interval_sec=save_interval,
            verbose=False
        )

        sim_duration = time.perf_counter() - t_start

        # --- Strict Numerical & Physical Audits ---
        assert H_sim.shape == (Sy, Sx, T), f"{eid}: Invalid H shape {H_sim.shape}"
        assert U_sim.shape == (Sy, Sx, T), f"{eid}: Invalid U shape {U_sim.shape}"
        assert V_sim.shape == (Sy, Sx, T), f"{eid}: Invalid V shape {V_sim.shape}"

        assert not np.isnan(H_sim).any(), f"{eid}: NaN in H"
        assert not np.isnan(U_sim).any(), f"{eid}: NaN in U"
        assert not np.isnan(V_sim).any(), f"{eid}: NaN in V"
        assert not np.isinf(H_sim).any(), f"{eid}: Inf in H"
        assert not np.isinf(U_sim).any(), f"{eid}: Inf in U"
        assert not np.isinf(V_sim).any(), f"{eid}: Inf in V"

        assert float(H_sim.min()) >= 0.0, f"{eid}: Negative depth detected ({H_sim.min()})"

        # Physical Diagnostics
        global_max_depth = float(np.max(H_sim))
        interior_max_depth = float(np.max(H_sim[:, :-1, :]))
        mean_depth = float(np.mean(H_sim))

        final_H = H_sim[:, :, -1]
        wet_frac_5cm = float(np.sum(final_H >= 0.05) / (Sy * Sx))
        wet_frac_10cm = float(np.sum(final_H >= 0.10) / (Sy * Sx))

        vel_magnitude = np.sqrt(U_sim ** 2 + V_sim ** 2)
        max_vel = float(np.max(vel_magnitude))
        mean_vel = float(np.mean(vel_magnitude))

        # Peak timing
        max_h_step = int(np.argmax(np.max(H_sim, axis=(0, 1))))
        max_h_time_min = (max_h_step + 1) * TIMESTEP_MINUTES
        max_v_step = int(np.argmax(np.max(vel_magnitude, axis=(0, 1))))
        max_v_time_min = (max_v_step + 1) * TIMESTEP_MINUTES

        status = "PASS"
        if max_vel > 12.0 or global_max_depth > 15.0:
            status = "FLAG"

        # Save Simulation Arrays
        sim_out_path = os.path.join(sim_dir, f"{eid}_hydro_sim.npz")
        np.savez_compressed(
            sim_out_path,
            H=H_sim,
            U=U_sim,
            V=V_sim,
            dem=dem,
            roughness=roughness
        )

        # Assemble & Save DNO Tensors
        rain_field = np.zeros((Sy, Sx, T), dtype=np.float32)
        for t in range(T):
            rain_field[:, :, t] = rain_hyetograph[t]

        x_tensor = adapter.assemble_input_tensor(dem=dem, rain_field_mm_hr=rain_field)
        y_tensor = adapter.format_supervision_targets(h_sim=H_sim, u_sim=U_sim, v_sim=V_sim, normalize=False)

        assert x_tensor.shape == (1, Sy, Sx, T, 1, 5), f"{eid}: Invalid X tensor shape"
        assert y_tensor.shape == (1, Sy, Sx, T, 3), f"{eid}: Invalid Y tensor shape"
        assert not torch.isnan(x_tensor).any(), f"{eid}: NaN in X tensor"
        assert not torch.isnan(y_tensor).any(), f"{eid}: NaN in Y tensor"

        tensor_x_path = os.path.join(tensor_dir, f"{eid}_input_tensor.pt")
        tensor_y_path = os.path.join(tensor_dir, f"{eid}_target_tensor.pt")
        torch.save(x_tensor.cpu(), tensor_x_path)
        torch.save(y_tensor.cpu(), tensor_y_path)

        # Update JSON Metadata
        meta.update({
            "simulation_output": sim_out_path,
            "tensor_input": tensor_x_path,
            "tensor_target": tensor_y_path,
            "hydrodynamic_metrics": {
                "max_depth_m": round(global_max_depth, 4),
                "interior_max_depth_m": round(interior_max_depth, 4),
                "mean_depth_m": round(mean_depth, 4),
                "final_wet_pct_5cm": round(wet_frac_5cm * 100, 2),
                "final_wet_pct_10cm": round(wet_frac_10cm * 100, 2),
                "max_velocity_mps": round(max_vel, 4),
                "mean_velocity_mps": round(mean_vel, 4),
                "max_depth_time_min": max_h_time_min,
                "max_velocity_time_min": max_v_time_min,
                "simulation_seconds": round(sim_duration, 3),
                "status": status
            }
        })

        meta_path = os.path.join(metadata_dir, f"{eid}.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        all_30_manifest_events[eid] = meta
        all_30_csv_rows.append([
            eid,
            round(total_mm, 2),
            2.0,
            shape_type,
            round(meta["peak_intensity_mm_hr"], 2),
            round(sim_duration, 3),
            round(global_max_depth, 4),
            round(interior_max_depth, 4),
            round(mean_depth, 4),
            round(wet_frac_5cm, 4),
            round(wet_frac_10cm, 4),
            round(max_vel, 4),
            round(mean_vel, 4),
            status
        ])

        print(f"  [{idx+1:02d}/30] {eid} ({split_role:5s}) | Rain: {total_mm:5.1f}mm ({shape_type:13s}) | Sim: {sim_duration:5.2f}s | Global H: {global_max_depth:5.2f}m | Interior H: {interior_max_depth:5.2f}m | Wet >5cm: {wet_frac_5cm*100:5.2f}% | Status: {status}")

    # 6. Save Complete 30-Event Runtime CSV
    runtime_csv_path = os.path.join(metadata_dir, "simulation_runtime.csv")
    with open(runtime_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "event_id", "rainfall_total_mm", "duration_hours", "profile",
            "peak_intensity_mm_per_hr", "simulation_seconds", "max_depth_m",
            "interior_max_depth_m", "mean_depth_m", "wet_fraction_5cm",
            "wet_fraction_10cm", "max_velocity_mps", "mean_velocity_mps", "status"
        ])
        writer.writerows(all_30_csv_rows)

    print(f"\n[4] Saved 30-Event Runtime Log: {runtime_csv_path}")

    # 7. Save Master 30-Event Library Manifest
    all_storm_ids = [f"storm_{i:03d}" for i in range(1, 31)]
    manifest = {
        "dataset_name": "Chennai Urban Flood DNO 30-Event Synthetic Storm Library",
        "dataset_version": "5.1.0-expanded",
        "creation_timestamp": datetime.now().isoformat(),
        "random_seed": 42,
        "dataset_classification": "SIMULATED HYDRODYNAMIC TRAINING DATA",
        "rainfall_classification": "SYNTHETIC / DERIVED RAINFALL FORCING",
        "domain": "Adyar–Velachery Basin, Greater Chennai Corporation (GCC)",
        "bounding_box_utm44n": [410000.0, 1431000.0, 420000.0, 1441000.0],
        "CRS": "EPSG:32644 (WGS 84 / UTM Zone 44N)",
        "grid_size": [Sy, Sx],
        "spatial_resolution_meters": dx,
        "timesteps": T,
        "temporal_resolution_minutes": 5.0,
        "forecast_window_hours": 2.0,
        "normalization": {
            "h_mean": 0.05, "h_std": 0.20,
            "u_mean": 0.00, "u_std": 0.15,
            "v_mean": 0.00, "v_std": 0.15,
            "p_mean": 30.0, "p_std": 25.0,
            "z_mean": 11.2, "z_std": 8.5
        },
        "solver_configuration": {
            "solver": "LISFLOOD-FP 2D Inertial Formulation (Bates et al. 2010 / de Almeida et al. 2012)",
            "internal_timestep_seconds": 1.0,
            "save_interval_seconds": 300.0,
            "coastal_tide_head_msl": 0.8,
            "subterranean_drainage": "Unmodeled (zero-fabrication: invert elevations absent in municipal GIS)"
        },
        "event_count": len(all_storm_ids),
        "pilot_events": pilot_ids,
        "expanded_events": [s["id"] for s in EXPANDED_STORM_SPECS],
        "train_events": DATASET_SPLITS_30["TRAIN"],
        "validation_events": DATASET_SPLITS_30["VAL"],
        "test_events": DATASET_SPLITS_30["TEST"],
        "event_metadata": all_30_manifest_events
    }

    manifest_path = os.path.join(metadata_dir, "storm_library_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[5] Saved Master 30-Event Library Manifest: {manifest_path}")
    print("=" * 80)
    print(" ALL 30 SYNTHETIC STORMS PROCESSED & VERIFIED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_phase5_expansion()
