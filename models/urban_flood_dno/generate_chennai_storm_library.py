"""
Chennai Synthetic Storm Library Generator (Phase 5A)
FloodWatch AI — SIH26085

Generates a controlled 10-event synthetic storm pilot covering:
- Magnitudes: 10 mm to 125 mm total rainfall
- Temporal shapes: Uniform, Front-loaded, Center-loaded, Back-loaded, Multi-peak
- Fixed 2-hour duration (24 timesteps at 5-minute intervals)
- Spatially uniform across the 10km x 10km pilot domain (Adyar–Velachery Basin)

Classification: SYNTHETIC / DERIVED RAINFALL FORCING
Seed: 42 (Fully deterministic and reproducible)
"""

import os
import json
import numpy as np
from datetime import datetime

RANDOM_SEED = 42
TIMESTEP_MINUTES = 5.0
TOTAL_TIMESTEPS = 24  # 24 * 5 min = 120 min = 2.0 hours
HOURS_PER_STEP = TIMESTEP_MINUTES / 60.0  # 5/60 = 1/12 hour

# Exact 10-Event Pilot Matrix
STORM_SPECS = [
    {"id": "storm_001", "total_mm": 10.0,  "shape": "uniform"},
    {"id": "storm_002", "total_mm": 15.0,  "shape": "front_loaded"},
    {"id": "storm_003", "total_mm": 20.0,  "shape": "center_loaded"},
    {"id": "storm_004", "total_mm": 25.0,  "shape": "back_loaded"},
    {"id": "storm_005", "total_mm": 35.0,  "shape": "uniform"},
    {"id": "storm_006", "total_mm": 45.0,  "shape": "center_loaded"},
    {"id": "storm_007", "total_mm": 60.0,  "shape": "front_loaded"},
    {"id": "storm_008", "total_mm": 75.0,  "shape": "back_loaded"},
    {"id": "storm_009", "total_mm": 100.0, "shape": "center_loaded"},
    {"id": "storm_010", "total_mm": 125.0, "shape": "multi_peak"},
]


def generate_shape_weights(shape_type: str, n_steps: int = 24, seed: int = 42) -> np.ndarray:
    """
    Generates relative weight curve across n_steps for the given temporal distribution shape.
    """
    t = np.linspace(0, 1, n_steps)
    rng = np.random.default_rng(seed)

    if shape_type == "uniform":
        # Base uniform with very gentle natural variability (+/- 5%)
        noise = rng.uniform(0.95, 1.05, size=n_steps)
        weights = np.ones(n_steps) * noise

    elif shape_type == "front_loaded":
        # Convective burst early (peak at t ~ 0.2, e.g. min 25), decaying exponentially
        # Gamma-like distribution peak around step 4-6
        alpha, beta = 2.0, 8.0
        weights = (t ** (alpha - 1)) * np.exp(-beta * t)
        # Ensure non-zero tail for steady recession
        weights = weights / weights.max()
        weights = np.maximum(weights, 0.08)

    elif shape_type == "center_loaded":
        # Symmetrical Gaussian convective cell centered at t ~ 0.5 (1 hour in)
        mu = 0.48
        sigma = 0.18
        weights = np.exp(-0.5 * ((t - mu) / sigma) ** 2)
        weights = np.maximum(weights, 0.05)

    elif shape_type == "back_loaded":
        # Convective intensification toward the second half (peak at t ~ 0.8)
        # Inverted gamma profile
        t_rev = 1.0 - t
        alpha, beta = 2.0, 7.0
        weights = (t_rev ** (alpha - 1)) * np.exp(-beta * t_rev)
        weights = weights[::-1]
        weights = weights / weights.max()
        weights = np.maximum(weights, 0.08)

    elif shape_type == "multi_peak":
        # Two distinct rainfall pulses: Peak 1 at t ~ 0.25 (30m), Peak 2 at t ~ 0.75 (90m)
        pulse1 = 0.85 * np.exp(-0.5 * ((t - 0.25) / 0.10) ** 2)
        pulse2 = 1.00 * np.exp(-0.5 * ((t - 0.75) / 0.11) ** 2)
        weights = pulse1 + pulse2
        weights = np.maximum(weights, 0.05)

    else:
        raise ValueError(f"Unknown shape type: {shape_type}")

    return weights.astype(np.float64)


def build_hyetograph(total_mm: float, shape_type: str, n_steps: int = 24, seed: int = 42) -> np.ndarray:
    """
    Computes rainfall rate in mm/hr at each of the 24 steps so that:
    sum(rate * dt) == total_mm exactly (within 1e-6 mm).
    """
    weights = generate_shape_weights(shape_type, n_steps, seed)

    # Accumulation = sum(rate_i * (5/60)) = (5/60) * sum(rate_i)
    # We want (5/60) * sum(rate_i) = total_mm
    # So sum(rate_i) = total_mm / (5/60) = total_mm * 12.0
    # Let rate_i = weights_i * scale
    target_sum_rates = total_mm / HOURS_PER_STEP
    scale = target_sum_rates / np.sum(weights)
    rates_mm_hr = weights * scale

    # Precise verification
    calc_total = float(np.sum(rates_mm_hr) * HOURS_PER_STEP)
    diff = abs(calc_total - total_mm)
    assert diff < 1e-4, f"Rainfall total mismatch: expected {total_mm}, got {calc_total} (diff: {diff})"

    return rates_mm_hr.astype(np.float32)


def generate_library(output_base_dir: str):
    os.makedirs(output_base_dir, exist_ok=True)
    rainfall_dir = os.path.join(output_base_dir, "rainfall")
    metadata_dir = os.path.join(output_base_dir, "metadata")
    os.makedirs(rainfall_dir, exist_ok=True)
    os.makedirs(metadata_dir, exist_ok=True)

    print("=" * 75)
    print(" FLOODWATCH AI — PHASE 5A: 10-EVENT SYNTHETIC STORM LIBRARY GENERATION")
    print(" CLASSIFICATION: SYNTHETIC / DERIVED RAINFALL FORCING")
    print(f" BASE SEED: {RANDOM_SEED} | DURATION: 2.0 HOURS (24 STEPS @ 5 MIN)")
    print("=" * 75)

    generated_manifest = []

    for idx, spec in enumerate(STORM_SPECS):
        eid = spec["id"]
        total_mm = spec["total_mm"]
        shape_type = spec["shape"]

        # Derive reproducible event-specific seed from base seed
        event_seed = RANDOM_SEED + idx * 17
        hyetograph_mm_hr = build_hyetograph(total_mm, shape_type, TOTAL_TIMESTEPS, event_seed)

        # Timestep metrics
        peak_rate = float(np.max(hyetograph_mm_hr))
        peak_step = int(np.argmax(hyetograph_mm_hr))
        peak_time_min = peak_step * TIMESTEP_MINUTES
        mean_rate = float(np.mean(hyetograph_mm_hr))
        actual_total = float(np.sum(hyetograph_mm_hr) * HOURS_PER_STEP)

        # Save binary array
        rain_path = os.path.join(rainfall_dir, f"{eid}_rainfall.npy")
        np.save(rain_path, hyetograph_mm_hr)

        # Per-event metadata
        meta = {
            "event_id": eid,
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
            "hyetograph_mm_hr": [round(float(v), 4) for v in hyetograph_mm_hr]
        }

        meta_path = os.path.join(metadata_dir, f"{eid}.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        generated_manifest.append(meta)

        print(f"[{idx+1:02d}/10] {eid}: {total_mm:5.1f} mm | Shape: {shape_type:13s} | Peak: {peak_rate:5.1f} mm/hr (@ {peak_time_min:4.1f}m) | Verified: {actual_total:5.1f} mm")

    print("=" * 75)
    print(f" Successfully generated 10 reproducible synthetic storm profiles in:")
    print(f"   Rainfall: {rainfall_dir}")
    print(f"   Metadata: {metadata_dir}")
    print("=" * 75)
    return generated_manifest


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out_dir = os.path.join(project_root, "Data", "dno", "chennai", "storm_library")
    generate_library(out_dir)
