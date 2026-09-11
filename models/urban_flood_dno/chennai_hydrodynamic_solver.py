"""
Chennai 2D Hydrodynamic Inertial Solver (LISFLOOD-FP Formulation)
Implements the Bates et al. (2010) & de Almeida et al. (2012) inertial shallow water equations
on a 2D Cartesian lattice over Chennai topography.

Governing Equations:
  Momentum (Inertial Formulation):
    dq_x/dt + g*h*d(h+z)/dx + (g*n^2*|q_x|*q_x) / h^(7/3) = 0
    dq_y/dt + g*h*d(h+z)/dy + (g*n^2*|q_y|*q_y) / h^(7/3) = 0
  Continuity (Conservation of Mass):
    dh/dt + dq_x/dx + dq_y/dy = P(t)
  Flow depth at cell interfaces (de Almeida 2012):
    h_flow = max(0, max(WSE_i, WSE_{i+1}) - max(z_i, z_{i+1}))

PROVENANCE:
All outputs from this solver are strictly classified as:
SIMULATED HYDRODYNAMIC TRAINING DATA
"""

import os
import time
from typing import Tuple, Dict, Any, Optional
import numpy as np


class ChennaiHydrodynamicSolver:
    def __init__(
        self,
        dem: np.ndarray,
        manning_n: np.ndarray,
        dx: float = 78.125,
        dt_internal: float = 0.5,
        g: float = 9.80665,
        h_threshold: float = 0.005,
        tide_head_msl: float = 0.8
    ):
        assert dem.ndim == 2, "DEM must be a 2D array"
        assert manning_n.shape == dem.shape, "Manning array must match DEM shape"

        self.dem = dem.astype(np.float32)
        self.manning_n = manning_n.astype(np.float32)
        self.Sy, self.Sx = dem.shape
        self.dx = float(dx)
        self.dt_internal = float(dt_internal)
        self.g = float(g)
        self.h_threshold = float(h_threshold)
        self.tide_head_msl = float(tide_head_msl)

        # Precompute spatial geometric features
        self.z_max_x = np.maximum(self.dem[:, 1:], self.dem[:, :-1])
        self.z_max_y = np.maximum(self.dem[1:, :], self.dem[:-1, :])
        self.n_face_x = 0.5 * (self.manning_n[:, 1:] + self.manning_n[:, :-1])
        self.n_face_y = 0.5 * (self.manning_n[1:, :] + self.manning_n[:-1, :])

    def run_simulation(
        self,
        rain_hyetograph_mm_hr: np.ndarray,
        horizon_steps: int = 24,
        save_interval_sec: float = 300.0,
        verbose: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Executes the 2D hydrodynamic simulation.

        Returns:
        - H_all: [Sy, Sx, T] continuous water depth in meters.
        - U_all: [Sy, Sx, T] flow velocity in X (Easting) direction [m/s].
        - V_all: [Sy, Sx, T] flow velocity in Y (Northing) direction [m/s].
        - metadata: complete physical configuration and validation metrics.
        """
        Sy, Sx = self.Sy, self.Sx
        dx = self.dx
        dt = self.dt_internal
        g = self.g
        h_thresh = self.h_threshold

        H = np.zeros((Sy, Sx), dtype=np.float32)
        qx = np.zeros((Sy, Sx + 1), dtype=np.float32)
        qy = np.zeros((Sy + 1, Sx), dtype=np.float32)

        total_sim_sec = horizon_steps * save_interval_sec
        cur_time = 0.0
        next_save_time = save_interval_sec
        step_idx = 0

        H_snapshots = []
        U_snapshots = []
        V_snapshots = []

        if verbose:
            print(f"[HYDRO-SIM] Starting Chennai 2D Simulation: {Sy}x{Sx} grid, dx={dx:.2f}m")
            print(f"[HYDRO-SIM] Horizon: {horizon_steps} steps ({total_sim_sec/3600:.1f} hrs) | Interval: {save_interval_sec}s")
            print(f"[HYDRO-SIM] Coastal Tide Head (Bay of Bengal East Edge): {self.tide_head_msl:.2f}m MSL")

        t_start = time.time()
        num_hyetograph = len(rain_hyetograph_mm_hr)

        while cur_time < total_sim_sec:
            # Current rainfall rate: match time to hyetograph step
            h_idx = min(int(cur_time // save_interval_sec), num_hyetograph - 1)
            rain_rate_m_s = (float(rain_hyetograph_mm_hr[h_idx]) / 1000.0) / 3600.0

            # 1. Mass addition from precipitation
            H += rain_rate_m_s * dt

            # 2. Water surface elevation (WSE)
            WSE = self.dem + H

            # 3. Flux update in X (Easting) — de Almeida interface flow depth
            wse_max_x = np.maximum(WSE[:, 1:], WSE[:, :-1])
            h_flow_x = np.maximum(0.0, wse_max_x - self.z_max_x)
            dh_dx = (WSE[:, 1:] - WSE[:, :-1]) / dx

            wet_mask_x = h_flow_x > h_thresh
            q_prev_x = qx[:, 1:-1]
            denom_x = 1.0 + g * dt * (self.n_face_x ** 2) * np.abs(q_prev_x) / (np.maximum(h_flow_x, h_thresh) ** (7.0 / 3.0))
            q_new_x = (q_prev_x - g * h_flow_x * dt * dh_dx) / denom_x
            qx[:, 1:-1] = np.where(wet_mask_x, q_new_x, 0.0)

            # 4. Flux update in Y (Northing) — de Almeida interface flow depth
            wse_max_y = np.maximum(WSE[1:, :], WSE[:-1, :])
            h_flow_y = np.maximum(0.0, wse_max_y - self.z_max_y)
            dh_dy = (WSE[1:, :] - WSE[:-1, :]) / dx

            wet_mask_y = h_flow_y > h_thresh
            q_prev_y = qy[1:-1, :]
            denom_y = 1.0 + g * dt * (self.n_face_y ** 2) * np.abs(q_prev_y) / (np.maximum(h_flow_y, h_thresh) ** (7.0 / 3.0))
            q_new_y = (q_prev_y - g * h_flow_y * dt * dh_dy) / denom_y
            qy[1:-1, :] = np.where(wet_mask_y, q_new_y, 0.0)

            # 5. Coastal Boundary Condition: Bay of Bengal Tidal Water Level on East Edge
            WSE[:, -1] = np.maximum(WSE[:, -1], self.tide_head_msl)
            H[:, -1] = np.maximum(0.0, WSE[:, -1] - self.dem[:, -1])

            # 6. Mass conservation update (Continuity)
            dqx = (qx[:, 1:] - qx[:, :-1]) / dx
            dqy = (qy[1:, :] - qy[:-1, :]) / dx
            H = np.maximum(0.0, H - dt * (dqx + dqy))

            cur_time += dt

            # Snapshot recording
            if cur_time >= next_save_time - 1e-5:
                # Recover cell-centered velocity: U = qx / H, V = qy / H
                qx_cell = 0.5 * (qx[:, 1:] + qx[:, :-1])
                qy_cell = 0.5 * (qy[1:, :] + qy[:-1, :])
                U = np.where(H >= h_thresh, np.clip(qx_cell / np.maximum(H, h_thresh), -10.0, 10.0), 0.0).astype(np.float32)
                V = np.where(H >= h_thresh, np.clip(qy_cell / np.maximum(H, h_thresh), -10.0, 10.0), 0.0).astype(np.float32)

                H_snapshots.append(H.copy())
                U_snapshots.append(U)
                V_snapshots.append(V)

                step_idx += 1
                next_save_time += save_interval_sec
                if step_idx >= horizon_steps:
                    break

        elapsed = time.time() - t_start

        # Stack into [Sy, Sx, T]
        H_all = np.stack(H_snapshots, axis=-1).astype(np.float32)
        U_all = np.stack(U_snapshots, axis=-1).astype(np.float32)
        V_all = np.stack(V_snapshots, axis=-1).astype(np.float32)

        wet_mask = H_all[:, :, -1] > 0.05
        pct_wet = 100.0 * np.sum(wet_mask) / (Sy * Sx)

        metadata = {
            "dataset_label": "SIMULATED HYDRODYNAMIC TRAINING DATA",
            "solver": "LISFLOOD-FP 2D Inertial Formulation (Bates et al. 2010 / de Almeida et al. 2012)",
            "grid_dimensions": [Sy, Sx],
            "cell_size_meters": dx,
            "horizon_steps": horizon_steps,
            "save_interval_sec": save_interval_sec,
            "total_duration_sec": total_sim_sec,
            "internal_timestep_sec": dt,
            "execution_time_sec": round(elapsed, 3),
            "h_stats": {
                "min": float(H_all.min()),
                "max": float(H_all.max()),
                "mean": float(H_all.mean()),
                "final_pct_wet_cells": round(float(pct_wet), 2)
            },
            "u_stats": {
                "min": float(U_all.min()),
                "max": float(U_all.max()),
                "mean": float(U_all.mean()),
                "nan_count": int(np.isnan(U_all).sum())
            },
            "v_stats": {
                "min": float(V_all.min()),
                "max": float(V_all.max()),
                "mean": float(V_all.mean()),
                "nan_count": int(np.isnan(V_all).sum())
            }
        }

        if verbose:
            print(f"[HYDRO-SIM] Simulation completed in {elapsed:.2f}s")
            print(f"[HYDRO-SIM] Water Depth H: min={metadata['h_stats']['min']:.4f}m, max={metadata['h_stats']['max']:.3f}m, mean={metadata['h_stats']['mean']:.4f}m")
            print(f"[HYDRO-SIM] Wet cells (>5cm): {metadata['h_stats']['final_pct_wet_cells']:.1f}%")
            print(f"[HYDRO-SIM] Velocity U: [{metadata['u_stats']['min']:.3f}, {metadata['u_stats']['max']:.3f}] m/s")
            print(f"[HYDRO-SIM] Velocity V: [{metadata['v_stats']['min']:.3f}, {metadata['v_stats']['max']:.3f}] m/s")

        return H_all, U_all, V_all, metadata
