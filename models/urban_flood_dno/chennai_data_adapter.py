"""
Chennai DNO Data Adapter
Converts 2D hydrodynamic simulation outputs (H, U, V), DEM (Z), and rainfall forcing (P)
into standardized PyTorch tensors conforming to the UrbanFloodCast DNO tensor schema:

Model Input Tensor:  [B, Sy, Sx, T, Tin, 5]
  Channels: [H0, U0, V0, P, Z]
Model Target Tensor: [B, Sy, Sx, T, 3]
  Targets:  [H, U, V]

Hardware Safe Profile:
- Batch Size B = 1
- Input Lead Time Tin = 1
- Prediction Horizon T = 24 (e.g. 2 hours at 5-minute intervals)
- Spatial Resolution Sy = 128, Sx = 128 (RTX 3050 6GB safe memory footprint)
"""

import os
import json
from typing import Dict, Any, Tuple, Optional
import numpy as np
import torch


class ChennaiDNODataAdapter:
    def __init__(
        self,
        grid_height: int = 128,
        grid_width: int = 128,
        horizon_steps: int = 24,
        device: str = "cpu"
    ):
        self.Sy = grid_height
        self.Sx = grid_width
        self.T = horizon_steps
        self.device = torch.device(device)

        # Standard normalization statistics (calibrated from Chennai pilot domain)
        self.norm_params = {
            "h_mean": 0.05, "h_std": 0.20,
            "u_mean": 0.00, "u_std": 0.15,
            "v_mean": 0.00, "v_std": 0.15,
            "p_mean": 30.0, "p_std": 25.0,  # mm/hr
            "z_mean": 11.2, "z_std": 8.5    # meters MSL
        }

    def process_dem(self, dem: np.ndarray) -> torch.Tensor:
        """Processes and normalizes DEM array to [1, Sy, Sx, 1, 1, 1]."""
        assert dem.shape == (self.Sy, self.Sx), f"DEM shape {dem.shape} != ({self.Sy}, {self.Sx})"
        z_norm = (dem - self.norm_params["z_mean"]) / max(self.norm_params["z_std"], 1e-6)
        z_t = torch.from_numpy(z_norm.astype(np.float32)).to(self.device)
        return z_t.view(1, self.Sy, self.Sx, 1, 1, 1)

    def process_rainfall(self, rain_field_mm_hr: np.ndarray) -> torch.Tensor:
        """Processes 3D rainfall field [Sy, Sx, T] to [1, Sy, Sx, T, 1, 1]."""
        assert rain_field_mm_hr.shape == (self.Sy, self.Sx, self.T), (
            f"Rain shape {rain_field_mm_hr.shape} != ({self.Sy}, {self.Sx}, {self.T})"
        )
        p_norm = (rain_field_mm_hr - self.norm_params["p_mean"]) / max(self.norm_params["p_std"], 1e-6)
        p_t = torch.from_numpy(p_norm.astype(np.float32)).to(self.device)
        return p_t.view(1, self.Sy, self.Sx, self.T, 1, 1)

    def assemble_input_tensor(
        self,
        dem: np.ndarray,
        rain_field_mm_hr: np.ndarray,
        h0: Optional[np.ndarray] = None,
        u0: Optional[np.ndarray] = None,
        v0: Optional[np.ndarray] = None
    ) -> torch.Tensor:
        """
        Assembles model input tensor [B=1, Sy, Sx, T, Tin=1, C=5]
        Channel order: [H0, U0, V0, P, Z]
        """
        # Initial conditions: default to dry bed (pre-storm state)
        if h0 is None:
            h0 = np.zeros((self.Sy, self.Sx), dtype=np.float32)
        if u0 is None:
            u0 = np.zeros((self.Sy, self.Sx), dtype=np.float32)
        if v0 is None:
            v0 = np.zeros((self.Sy, self.Sx), dtype=np.float32)

        # Normalize H0, U0, V0
        h0_norm = (h0 - self.norm_params["h_mean"]) / max(self.norm_params["h_std"], 1e-6)
        u0_norm = (u0 - self.norm_params["u_mean"]) / max(self.norm_params["u_std"], 1e-6)
        v0_norm = (v0 - self.norm_params["v_mean"]) / max(self.norm_params["v_std"], 1e-6)

        h0_t = torch.from_numpy(h0_norm.astype(np.float32)).to(self.device).view(1, self.Sy, self.Sx, 1, 1, 1).repeat(1, 1, 1, self.T, 1, 1)
        u0_t = torch.from_numpy(u0_norm.astype(np.float32)).to(self.device).view(1, self.Sy, self.Sx, 1, 1, 1).repeat(1, 1, 1, self.T, 1, 1)
        v0_t = torch.from_numpy(v0_norm.astype(np.float32)).to(self.device).view(1, self.Sy, self.Sx, 1, 1, 1).repeat(1, 1, 1, self.T, 1, 1)

        z_t = self.process_dem(dem).repeat(1, 1, 1, self.T, 1, 1)
        p_t = self.process_rainfall(rain_field_mm_hr)

        # Concatenate along channel dimension (last axis)
        input_tensor = torch.cat([h0_t, u0_t, v0_t, p_t, z_t], dim=-1)
        assert input_tensor.shape == (1, self.Sy, self.Sx, self.T, 1, 5), (
            f"Assembled input shape {input_tensor.shape} != (1, {self.Sy}, {self.Sx}, {self.T}, 1, 5)"
        )
        return input_tensor

    def format_supervision_targets(
        self,
        h_sim: np.ndarray,
        u_sim: np.ndarray,
        v_sim: np.ndarray,
        normalize: bool = False
    ) -> torch.Tensor:
        """
        Formats hydrodynamic simulation ground truth into model target tensor [B=1, Sy, Sx, T, 3]
        Target channels: [H, U, V]
        """
        assert h_sim.shape == (self.Sy, self.Sx, self.T)
        assert u_sim.shape == (self.Sy, self.Sx, self.T)
        assert v_sim.shape == (self.Sy, self.Sx, self.T)

        if normalize:
            h_out = (h_sim - self.norm_params["h_mean"]) / max(self.norm_params["h_std"], 1e-6)
            u_out = (u_sim - self.norm_params["u_mean"]) / max(self.norm_params["u_std"], 1e-6)
            v_out = (v_sim - self.norm_params["v_mean"]) / max(self.norm_params["v_std"], 1e-6)
        else:
            h_out = h_sim
            u_out = u_sim
            v_out = v_sim

        h_t = torch.from_numpy(h_out.astype(np.float32)).to(self.device).unsqueeze(0).unsqueeze(-1)
        u_t = torch.from_numpy(u_out.astype(np.float32)).to(self.device).unsqueeze(0).unsqueeze(-1)
        v_t = torch.from_numpy(v_out.astype(np.float32)).to(self.device).unsqueeze(0).unsqueeze(-1)

        target_tensor = torch.cat([h_t, u_t, v_t], dim=-1)
        assert target_tensor.shape == (1, self.Sy, self.Sx, self.T, 3), (
            f"Target tensor shape {target_tensor.shape} != (1, {self.Sy}, {self.Sx}, {self.T}, 3)"
        )
        return target_tensor
