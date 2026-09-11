"""
Chennai Storm Library Simulation & Tensor Pipeline (Phase 5B & 5C)
FloodWatch AI — SIH26085

Sequentially executes 2D hydrodynamic shallow-water simulations (LISFLOOD-FP inertial formulation)
and assembles DNO spatiotemporal input/target tensors for the 10-event synthetic storm pilot.

Zero Fabrication & Physics Integrity Rules:
1. Reuses verified Chennai DEM (128x128, dx=78.125m) and Manning roughness matrix
2. Solves Bates/de Almeida inertial shallow water equations at dt=1.0s internal timestep
3. Boundary: 0.8m MSL coastal tidal backwater on east edge
4. All outputs explicitly classified as: SIMULATED HYDRODYNAMIC TRAINING DATA
5. Strictly sequential execution to maintain safe low memory footprint
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

# Stratified Dataset Partitioning
DATASET_SPLITS = {
    "TRAIN": [
        "storm_001",  # 10 mm (Uniform)
        "storm_002",  # 15 mm (Front-loaded)
        "storm_004",  # 25 mm (Back-loaded)
        "storm_005",  # 35 mm (Uniform)
        "storm_006",  # 45 mm (Center-loaded)
        "storm_009",  # 100 mm (Center-loaded)
        "storm_010"   # 125 mm (Multi-peak)
    ],
    "VAL": [
        "storm_003",  # 20 mm (Center-loaded)
        "storm_008"   # 75 mm (Back-loaded)
    ],
    "TEST": [
        "storm_007"   # 60 mm (Front-loaded)
    ]
}


def run_storm_library():
    print("=" * 80)
    print(" FLOODWATCH AI — PHASE 5B & 5C: 10-EVENT HYDRODYNAMIC & DNO TENSOR PIPELINE")
    print(" PILOT DOMAIN: Adyar–Velachery Basin (10 km x 10 km, EPSG:32644)")
    print(" DATASET CLASSIFICATION: SIMULATED HYDRODYNAMIC TRAINING DATA")
    print("=" * 80)

    # 1. Paths Setup
    dno_base = os.path.join(REPO_ROOT, "Data", "dno", "chennai")
    storm_base = os.path.join(dno_base, "storm_library")
    rainfall_dir = os.path.join(storm_base, "rainfall")
    sim_dir = os.path.join(storm_base, "simulations")
    tensor_dir = os.path.join(storm_base, "tensors")
    metadata_dir = os.path.join(storm_base, "metadata")
    processed_dir = os.path.join(dno_base, "processed")

    for d in [sim_dir, tensor_dir, metadata_dir]:
        os.makedirs(d, exist_ok=True)

    # 2. Load Processed Pilot Terrain and Roughness
    dem_path = os.path.join(processed_dir, "pilot_adyar_velachery_dem_128x128.npy")
    n_path = os.path.join(processed_dir, "pilot_adyar_velachery_roughness_128x128.npy")

    if not os.path.exists(dem_path) or not os.path.exists(n_path):
        raise FileNotFoundError(f"Missing terrain arrays in {processed_dir}. Run Phase 4 prep scripts first.")

    dem = np.load(dem_path).astype(np.float32)
    roughness = np.load(n_path).astype(np.float32)
    Sy, Sx = dem.shape
    dx = 10000.0 / Sx  # 78.125m
    T = 24             # 24 steps = 2.0 hours at 5-min intervals
    save_interval = 300.0

    print(f"\n[1] Pilot Topography Loaded:")
    print(f"  Dimensions: {Sy} x {Sx} cells ({dx:.3f}m resolution)")
    print(f"  Elevation: min={dem.min():.2f}m, max={dem.max():.2f}m, mean={dem.mean():.2f}m MSL")
    print(f"  Manning n: min={roughness.min():.3f}, max={roughness.max():.3f}, mean={roughness.mean():.3f}")

    # 3. Instantiate Solver and DNO Adapter
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

    # 4. Prepare Runtime CSV Log
    runtime_csv_path = os.path.join(metadata_dir, "simulation_runtime.csv")
    csv_rows = []
    manifest_events = {}

    storm_ids = [f"storm_{i:03d}" for i in range(1, 11)]

    print(f"\n[2] Executing Hydrodynamic Simulations Sequentially (10 Storms)...")

    for idx, eid in enumerate(storm_ids):
        t_start = time.perf_counter()

        # Load Rainfall
        rain_path = os.path.join(rainfall_dir, f"{eid}_rainfall.npy")
        meta_json_path = os.path.join(metadata_dir, f"{eid}.json")

        if not os.path.exists(rain_path) or not os.path.exists(meta_json_path):
            raise FileNotFoundError(f"Missing rainfall files for {eid}. Run Phase 5A generator first.")

        rain_hyetograph = np.load(rain_path).astype(np.float32)
        with open(meta_json_path, "r", encoding="utf-8") as f:
            storm_meta = json.load(f)

        total_mm = storm_meta["total_rainfall_mm"]
        shape_type = storm_meta["temporal_shape"]
        peak_rate = storm_meta["peak_intensity_mm_hr"]

        # Determine split role
        split_role = "TRAIN"
        if eid in DATASET_SPLITS["VAL"]:
            split_role = "VAL"
        elif eid in DATASET_SPLITS["TEST"]:
            split_role = "TEST"

        # Execute 2D Hydrodynamic Simulation
        H_sim, U_sim, V_sim, sim_meta = solver.run_simulation(
            rain_hyetograph_mm_hr=rain_hyetograph,
            horizon_steps=T,
            save_interval_sec=save_interval,
            verbose=False
        )

        sim_duration = time.perf_counter() - t_start

        # --- Strict Numerical & Shape Checks ---
        assert H_sim.shape == (Sy, Sx, T), f"{eid}: Invalid H shape {H_sim.shape}"
        assert U_sim.shape == (Sy, Sx, T), f"{eid}: Invalid U shape {U_sim.shape}"
        assert V_sim.shape == (Sy, Sx, T), f"{eid}: Invalid V shape {V_sim.shape}"

        assert not np.isnan(H_sim).any(), f"{eid}: NaN detected in H"
        assert not np.isnan(U_sim).any(), f"{eid}: NaN detected in U"
        assert not np.isnan(V_sim).any(), f"{eid}: NaN detected in V"
        assert not np.isinf(H_sim).any(), f"{eid}: Inf detected in H"
        assert not np.isinf(U_sim).any(), f"{eid}: Inf detected in U"
        assert not np.isinf(V_sim).any(), f"{eid}: Inf detected in V"

        assert float(H_sim.min()) >= 0.0, f"{eid}: Negative depth detected ({H_sim.min()})"

        # Physical Diagnostics
        final_H = H_sim[:, :, -1]
        max_depth = float(np.max(H_sim))
        mean_depth = float(np.mean(H_sim))
        wet_cells_5cm = np.sum(final_H >= 0.05)
        wet_cells_10cm = np.sum(final_H >= 0.10)
        total_cells = Sy * Sx
        wet_frac_5cm = float(wet_cells_5cm / total_cells)
        wet_frac_10cm = float(wet_cells_10cm / total_cells)

        vel_magnitude = np.sqrt(U_sim ** 2 + V_sim ** 2)
        max_vel = float(np.max(vel_magnitude))
        mean_vel = float(np.mean(vel_magnitude))

        # Status evaluation
        status = "PASS"
        if max_vel > 10.0 or max_depth > 15.0:
            status = "FLAG"

        # Save Raw Simulation Arrays
        sim_out_path = os.path.join(sim_dir, f"{eid}_hydro_sim.npz")
        np.savez_compressed(
            sim_out_path,
            H=H_sim,
            U=U_sim,
            V=V_sim,
            dem=dem,
            roughness=roughness
        )

        # --- Phase 5C: Assemble & Save DNO Tensors ---
        # Generate 3D rainfall field [Sy, Sx, T]
        rain_field = np.zeros((Sy, Sx, T), dtype=np.float32)
        for t in range(T):
            rain_field[:, :, t] = rain_hyetograph[t]

        x_tensor = adapter.assemble_input_tensor(dem=dem, rain_field_mm_hr=rain_field)
        y_tensor = adapter.format_supervision_targets(h_sim=H_sim, u_sim=U_sim, v_sim=V_sim, normalize=False)

        # Tensor verification
        assert x_tensor.shape == (1, Sy, Sx, T, 1, 5), f"{eid}: Invalid X tensor shape {x_tensor.shape}"
        assert y_tensor.shape == (1, Sy, Sx, T, 3), f"{eid}: Invalid Y tensor shape {y_tensor.shape}"
        assert not torch.isnan(x_tensor).any(), f"{eid}: NaN in X tensor"
        assert not torch.isnan(y_tensor).any(), f"{eid}: NaN in Y tensor"

        tensor_x_path = os.path.join(tensor_dir, f"{eid}_input_tensor.pt")
        tensor_y_path = os.path.join(tensor_dir, f"{eid}_target_tensor.pt")
        torch.save(x_tensor.cpu(), tensor_x_path)
        torch.save(y_tensor.cpu(), tensor_y_path)

        # Update per-event JSON metadata
        storm_meta.update({
            "simulation_output": sim_out_path,
            "tensor_input": tensor_x_path,
            "tensor_target": tensor_y_path,
            "split_role": split_role,
            "hydrodynamic_metrics": {
                "max_depth_m": round(max_depth, 4),
                "mean_depth_m": round(mean_depth, 4),
                "final_wet_pct_5cm": round(wet_frac_5cm * 100, 2),
                "final_wet_pct_10cm": round(wet_frac_10cm * 100, 2),
                "max_velocity_mps": round(max_vel, 4),
                "mean_velocity_mps": round(mean_vel, 4),
                "simulation_seconds": round(sim_duration, 3),
                "status": status
            }
        })

        with open(meta_json_path, "w", encoding="utf-8") as f:
            json.dump(storm_meta, f, indent=2)

        manifest_events[eid] = storm_meta

        # Record CSV Row
        csv_rows.append([
            eid,
            round(total_mm, 2),
            2.0,
            shape_type,
            round(peak_rate, 2),
            round(sim_duration, 3),
            round(max_depth, 4),
            round(mean_depth, 4),
            round(wet_frac_5cm, 4),
            round(wet_frac_10cm, 4),
            round(max_vel, 4),
            round(mean_vel, 4),
            status
        ])

        print(f"[{idx+1:02d}/10] {eid:9s} ({split_role:5s}) | Rain: {total_mm:5.1f}mm ({shape_type:13s}) | Sim: {sim_duration:5.2f}s | Max H: {max_depth:5.2f}m | Mean H: {mean_depth:6.4f}m | Wet >5cm: {wet_frac_5cm*100:5.2f}% | Status: {status}")

    # Write runtime CSV
    with open(runtime_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "event_id", "rainfall_total_mm", "duration_hours", "profile",
            "peak_intensity_mm_per_hr", "simulation_seconds", "max_depth_m",
            "mean_depth_m", "wet_fraction_5cm", "wet_fraction_10cm",
            "max_velocity_mps", "mean_velocity_mps", "status"
        ])
        writer.writerows(csv_rows)

    print(f"\n[3] Saved Simulation Runtime Log: {runtime_csv_path}")

    # 5. Build Master Library Manifest
    manifest = {
        "dataset_name": "Chennai Urban Flood DNO 10-Event Synthetic Storm Pilot",
        "dataset_version": "5.0.0-pilot",
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
        "event_count": len(storm_ids),
        "train_events": DATASET_SPLITS["TRAIN"],
        "validation_events": DATASET_SPLITS["VAL"],
        "test_events": DATASET_SPLITS["TEST"],
        "event_metadata": manifest_events
    }

    manifest_path = os.path.join(metadata_dir, "storm_library_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[4] Saved Master Library Manifest: {manifest_path}")
    print("=" * 80)
    print(" ALL 10 SYNTHETIC HYDRODYNAMIC SIMULATIONS & DNO TENSORS GENERATED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_storm_library()
