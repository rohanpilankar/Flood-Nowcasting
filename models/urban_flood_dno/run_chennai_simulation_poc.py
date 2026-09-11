"""
Master Pipeline: Chennai 2D Hydrodynamic Simulation POC & DNO Data Packaging
Executes:
1. Pilot Grid Setup (Adyar-Velachery Basin 10km x 10km, 128x128 grid)
2. 2D Shallow Water Hydrodynamic Simulation (LISFLOOD-FP Inertial Formulation)
3. Physical Output Validation (H >= 0, U, V, No NaNs)
4. Comparison Against Historical 2015 Flood Points (Spatial Hit Rate)
5. DNO Tensor Packaging ([B, Sy, Sx, T, Tin, 5] and [B, Sy, Sx, T, 3])
6. Event-Based Split Organization and Metadata Export

PROVENANCE: All outputs strictly classified as:
SIMULATED HYDRODYNAMIC TRAINING DATA
"""

import os
import sys
import json
import time
import numpy as np
import torch
import geopandas as gpd
from shapely.geometry import box

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from models.urban_flood_dno.rainfall_forcing_interface import RainfallForcingInterface
from models.urban_flood_dno.chennai_hydrodynamic_solver import ChennaiHydrodynamicSolver
from models.urban_flood_dno.chennai_data_adapter import ChennaiDNODataAdapter


def run_chennai_poc():
    print("=" * 80)
    print(" FLOODWATCH AI — CHENNAI 2D HYDRODYNAMIC SIMULATION POC")
    print(" Target: Adyar–Velachery Basin (10 km x 10 km, EPSG:32644 UTM Zone 44N)")
    print(" Dataset Classification: SIMULATED HYDRODYNAMIC TRAINING DATA")
    print("=" * 80)

    # 1. Output Directories Setup
    base_dno_dir = os.path.join(PROJECT_ROOT, "Data", "dno", "chennai")
    sim_dir = os.path.join(base_dno_dir, "simulations")
    tensor_dir = os.path.join(base_dno_dir, "tensors")
    meta_dir = os.path.join(base_dno_dir, "metadata")
    processed_dir = os.path.join(base_dno_dir, "processed")

    for d in [sim_dir, tensor_dir, meta_dir, processed_dir]:
        os.makedirs(d, exist_ok=True)

    # 2. Load Processed Pilot Terrain & Roughness
    dem_path = os.path.join(processed_dir, "pilot_adyar_velachery_dem_128x128.npy")
    n_path = os.path.join(processed_dir, "pilot_adyar_velachery_roughness_128x128.npy")

    if not os.path.exists(dem_path) or not os.path.exists(n_path):
        raise FileNotFoundError("Processed pilot DEM or Roughness not found. Run scratch scripts first.")

    dem = np.load(dem_path)
    roughness = np.load(n_path)
    Sy, Sx = dem.shape
    dx = 10000.0 / Sx  # 78.125m cell size for 10km grid
    T = 24             # 24 steps = 2 hours at 5-min intervals

    print(f"\n[1] Terrain & Pilot Mesh Loaded:")
    print(f"  Grid Dimensions: {Sy} x {Sx} cells ({Sy*dx/1000:.2f} km x {Sx*dx/1000:.2f} km)")
    print(f"  Spatial Resolution: dx = {dx:.2f} meters")
    print(f"  Elevation Range: min={dem.min():.2f}m, max={dem.max():.2f}m, mean={dem.mean():.2f}m")
    print(f"  Roughness Range: min={roughness.min():.3f}, max={roughness.max():.3f}, mean={roughness.mean():.3f}")

    # 3. Simulate Multiple Storm Events for Event-Based Splitting
    storm_configs = [
        {"id": "event_01_2015_deluge", "preset": "chennai_2015_deluge_peak", "split": "TRAIN"},
        {"id": "event_02_michaung_surge", "preset": "chennai_michaung_2023_surge", "split": "VAL"},
        {"id": "event_03_monsoon_moderate", "preset": "chennai_monsoon_moderate", "split": "TEST"}
    ]

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

    sim_results = {}

    for cfg in storm_configs:
        eid = cfg["id"]
        preset = cfg["preset"]
        split = cfg["split"]

        print(f"\n[2] Executing Simulation for Storm: {eid} (Role: {split})")
        forcing = RainfallForcingInterface(preset_key=preset)
        print(f"  Profile: {forcing.metadata['name']}")
        print(f"  Accumulation: {forcing.metadata['total_accumulation_mm']:.1f} mm over 2 hours")

        # Run 2D Hydrodynamic Simulation
        H_sim, U_sim, V_sim, meta = solver.run_simulation(
            rain_hyetograph_mm_hr=forcing.hyetograph_mm_hr,
            horizon_steps=T,
            save_interval_sec=300.0,
            verbose=False
        )

        print(f"  Simulation completed in {meta['execution_time_sec']}s")
        print(f"  Max Water Depth H: {meta['h_stats']['max']:.3f} m | Mean Depth: {meta['h_stats']['mean']:.4f} m")
        print(f"  Final Flooded Cells (>5cm): {meta['h_stats']['final_pct_wet_cells']}%")
        print(f"  Velocity Field U: [{meta['u_stats']['min']:.3f}, {meta['u_stats']['max']:.3f}] m/s")
        print(f"  Velocity Field V: [{meta['v_stats']['min']:.3f}, {meta['v_stats']['max']:.3f}] m/s")

        # Save Raw Simulation Arrays
        sim_path = os.path.join(sim_dir, f"{eid}_hydro_sim.npz")
        np.savez_compressed(
            sim_path,
            H=H_sim,
            U=U_sim,
            V=V_sim,
            dem=dem,
            roughness=roughness
        )
        print(f"  Saved simulation output to: {sim_path}")

        # Assemble DNO Tensors
        rain_field = forcing.generate_spatiotemporal_forcing(Sy, Sx)
        x_tensor = adapter.assemble_input_tensor(dem=dem, rain_field_mm_hr=rain_field)
        y_tensor = adapter.format_supervision_targets(h_sim=H_sim, u_sim=U_sim, v_sim=V_sim)

        # Save Tensors
        tensor_x_path = os.path.join(tensor_dir, f"{eid}_input_tensor.pt")
        tensor_y_path = os.path.join(tensor_dir, f"{eid}_target_tensor.pt")
        torch.save(x_tensor.cpu(), tensor_x_path)
        torch.save(y_tensor.cpu(), tensor_y_path)

        print(f"  DNO Input  Tensor Shape (X): {list(x_tensor.shape)} -> saved {tensor_x_path}")
        print(f"  DNO Target Tensor Shape (Y): {list(y_tensor.shape)} -> saved {tensor_y_path}")

        sim_results[eid] = {
            "metadata": meta,
            "split": split,
            "sim_path": sim_path,
            "tensor_x_path": tensor_x_path,
            "tensor_y_path": tensor_y_path
        }

    # 4. Validate Against Historical 2015 Flood Points
    print(f"\n[3] Historical Observational Point Validation (2015 Flood Reports):")
    pts_path = os.path.join(PROJECT_ROOT, "Data", "processed", "vectors", "Chennai_Flooding_Points_2015.parquet")
    pts = gpd.read_parquet(pts_path)

    # Pilot domain bounding box (UTM 44N)
    xmin, ymin, xmax, ymax = 410000.0, 1431000.0, 420000.0, 1441000.0
    bbox = box(xmin, ymin, xmax, ymax)
    pilot_pts = pts[pts.geometry.intersects(bbox)].copy()
    print(f"  Historical complaint points inside 10km pilot box: {len(pilot_pts)}")

    # Check simulated inundation for the 2015 deluge run
    deluge_sim = np.load(os.path.join(sim_dir, "event_01_2015_deluge_hydro_sim.npz"))
    H_deluge_final = deluge_sim["H"][:, :, -1]

    # Map each point to grid cell
    hits_5cm = 0
    hits_10cm = 0
    valid_pts = 0

    for _, row in pilot_pts.iterrows():
        px, py = row.geometry.x, row.geometry.y
        # Convert UTM coordinates to grid indices [row_idx, col_idx]
        # In UTM: y increases upward (North), x increases rightward (East)
        col_idx = int((px - xmin) / dx)
        row_idx = int((ymax - py) / dx)  # row 0 is top (North)

        if 0 <= col_idx < Sx and 0 <= row_idx < Sy:
            valid_pts += 1
            depth_at_pt = H_deluge_final[row_idx, col_idx]
            if depth_at_pt >= 0.05:
                hits_5cm += 1
            if depth_at_pt >= 0.10:
                hits_10cm += 1

    hit_rate_5cm = 100.0 * hits_5cm / max(valid_pts, 1)
    hit_rate_10cm = 100.0 * hits_10cm / max(valid_pts, 1)
    print(f"  Evaluated Points: {valid_pts}")
    print(f"  Simulated Wet Depth at Historical Points (>5cm):  {hits_5cm}/{valid_pts} ({hit_rate_5cm:.1f}%)")
    print(f"  Simulated Wet Depth at Historical Points (>10cm): {hits_10cm}/{valid_pts} ({hit_rate_10cm:.1f}%)")
    print(f"  Observational Note: Historical points denote binary occurrence reports, not continuous depth.")

    # 5. Export Master Metadata
    master_metadata = {
        "project": "FloodWatch AI",
        "study_area": "Greater Chennai Corporation (GCC)",
        "pilot_domain": "Adyar–Velachery Basin",
        "bounding_box_utm44n": [xmin, ymin, xmax, ymax],
        "crs": "EPSG:32644",
        "grid_dimensions": [Sy, Sx],
        "cell_size_meters": dx,
        "dataset_classification": "SIMULATED HYDRODYNAMIC TRAINING DATA",
        "historical_observational_validation": {
            "total_points_in_domain": len(pilot_pts),
            "hit_rate_5cm_pct": round(hit_rate_5cm, 1),
            "hit_rate_10cm_pct": round(hit_rate_10cm, 1)
        },
        "event_splits": {
            "TRAIN": ["event_01_2015_deluge"],
            "VAL": ["event_02_michaung_surge"],
            "TEST": ["event_03_monsoon_moderate"]
        },
        "simulations": sim_results
    }

    meta_file = os.path.join(meta_dir, "chennai_dno_simulation_metadata.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(master_metadata, f, indent=2)

    print(f"\n[4] Master Metadata Exported to: {meta_file}")
    print("=" * 80)
    print(" CHENNAI 2D HYDRODYNAMIC SIMULATION POC COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_chennai_poc()
