# Chennai DNO Data Specification
**FloodWatch AI — Deep Neural Operator (DNO) Data Contract**  
**Document Reference:** `docs/CHENNAI_DNO_DATA_SPEC.md`  
**Standard:** Conforms to HydroPML/UrbanFloodCast DNO Architecture  
**Target Domain:** Greater Chennai Corporation (GCC), Tamil Nadu  
**Projection:** EPSG:32644 (WGS 84 / UTM Zone 44N)  
**Dataset Provenance:** `SIMULATED HYDRODYNAMIC TRAINING DATA`  

---

## 1. Mathematical Formulation & Tensor Shapes

The Deep Neural Operator (DNO) learns a continuous mapping $\mathcal{G}_\theta: \mathcal{A} \to \mathcal{U}$ from input physical forcings to dynamic hydrodynamic field evolutions.

### 1.1 Model Input Tensor ($X$)
$$\mathbf{X} \in \mathbb{R}^{B \times S_y \times S_x \times T \times T_{in} \times C_{in}}$$

| Dimension | Name | Value (Pilot Profile) | Physical Description |
| :---: | :--- | :---: | :--- |
| **$B$** | Batch Size | $1$ | Number of storm patches per training iteration (RTX 3050 6GB safe) |
| **$S_y$** | Grid Height (Northing) | $128$ | Discrete spatial lattice along UTM-Y axis |
| **$S_x$** | Grid Width (Easting) | $128$ | Discrete spatial lattice along UTM-X axis |
| **$T$** | Prediction Horizon | $24$ | Total forecast steps ($2.0\text{ hours}$ at $\Delta t = 300\text{ s}$) |
| **$T_{in}$** | Input Lead Steps | $1$ | Initial condition temporal slice |
| **$C_{in}$** | Input Channels | $5$ | Channel features: $[H_0, U_0, V_0, P, Z]$ |

#### Input Channel Ordering ($C_{in} = 5$):
1. **Channel 0 — $H_0$:** Initial water depth at $t=0$ [meters]. Default: $0.0\text{ m}$ (dry bed).
2. **Channel 1 — $U_0$:** Initial flow velocity in $X$-direction (Easting) at $t=0$ [$\text{m/s}$]. Default: $0.0\text{ m/s}$.
3. **Channel 2 — $V_0$:** Initial flow velocity in $Y$-direction (Northing) at $t=0$ [$\text{m/s}$]. Default: $0.0\text{ m/s}$.
4. **Channel 3 — $P(t)$:** Spatiotemporal precipitation rate at step $t$ [$\text{mm/hr}$].
5. **Channel 4 — $Z$:** Digital Elevation Model elevation above MSL [meters].

---

### 1.2 Model Target Supervision Tensor ($Y$)
$$\mathbf{Y} \in \mathbb{R}^{B \times S_y \times S_x \times T \times C_{out}}$$

| Dimension | Name | Value (Pilot Profile) | Physical Description |
| :---: | :--- | :---: | :--- |
| **$B$** | Batch Size | $1$ | Number of storm patches per training iteration |
| **$S_y$** | Grid Height (Northing) | $128$ | Spatial lattice along UTM-Y axis |
| **$S_x$** | Grid Width (Easting) | $128$ | Spatial lattice along UTM-X axis |
| **$T$** | Simulation Timesteps | $24$ | Sequence of predicted hydrodynamic steps |
| **$C_{out}$** | Target Channels | $3$ | Output physical variables: $[H, U, V]$ |

#### Target Channel Ordering ($C_{out} = 3$):
1. **Channel 0 — $H(x, y, t)$:** Overland continuous water depth [meters].
2. **Channel 1 — $U(x, y, t)$:** Overland flow velocity component in $X$-direction [$\text{m/s}$].
3. **Channel 2 — $V(x, y, t)$:** Overland flow velocity component in $Y$-direction [$\text{m/s}$].

---

## 2. Spatial & Temporal Discretization

* **Coordinate System:** EPSG:32644 (UTM Zone 44N, units in meters).
* **Pilot Bounding Box:**
  * Easting ($X$): $[410000.0, 420000.0]\text{ m}$
  * Northing ($Y$): $[1431000.0, 1441000.0]\text{ m}$
* **Grid Spacing:** $\Delta x = \Delta y = 78.125\text{ m}$ ($10,000\text{ m} / 128$).
* **Temporal Interval:** $\Delta t_{output} = 300.0\text{ s}$ ($5.0\text{ minutes}$).
* **Total Forecast Window:** $2.0\text{ hours}$ ($24\text{ steps} \times 300\text{ s} = 7,200\text{ s}$).

---

## 3. Normalization Parameters

Standard z-score normalization transforms inputs into zero-mean, unit-variance distributions:
$$x_{norm} = \frac{x - \mu}{\sigma}$$

| Variable | Symbol | Calibration Mean ($\mu$) | Calibration Std ($\sigma$) | Physical Units |
| :--- | :---: | :---: | :---: | :---: |
| **Water Depth** | $H, H_0$ | $0.050\text{ m}$ | $0.200\text{ m}$ | meters |
| **X Velocity** | $U, U_0$ | $0.000\text{ m/s}$ | $0.150\text{ m/s}$ | $\text{m/s}$ |
| **Y Velocity** | $V, V_0$ | $0.000\text{ m/s}$ | $0.150\text{ m/s}$ | $\text{m/s}$ |
| **Precipitation** | $P$ | $30.00\text{ mm/hr}$ | $25.00\text{ mm/hr}$ | $\text{mm/hr}$ |
| **Topography** | $Z$ | $11.20\text{ m}$ | $8.53\text{ m}$ | meters MSL |

---

## 4. Event-Based Dataset Partitions

To prevent serial autocorrelation and data leakage across storm evolutions, dataset partitioning is executed strictly across **discrete meteorological storm events**:

| Split Role | Event Identifier | Meteorological Profile | Total Rain | Tensor Files |
| :--- | :--- | :--- | :---: | :--- |
| **TRAIN** | `event_01_2015_deluge` | Dec 1, 2015 Historic Deluge Peak (65 mm/hr peak) | $75.33\text{ mm}$ | `event_01_2015_deluge_input_tensor.pt`<br>`event_01_2015_deluge_target_tensor.pt` |
| **VALIDATION** | `event_02_michaung_surge` | Dec 4, 2023 Cyclone Michaung Surge (60 mm/hr) | $77.25\text{ mm}$ | `event_02_michaung_surge_input_tensor.pt`<br>`event_02_michaung_surge_target_tensor.pt` |
| **TEST** | `event_03_monsoon_moderate` | Standard Northeast Monsoon Convective Wave | $27.50\text{ mm}$ | `event_03_monsoon_moderate_input_tensor.pt`<br>`event_03_monsoon_moderate_target_tensor.pt` |

---

## 5. Storage Directory Structure

```
Data/dno/chennai/
├── processed/
│   ├── pilot_adyar_velachery_dem_128x128.npy        [Float32 DEM 128x128]
│   └── pilot_adyar_velachery_roughness_128x128.npy  [Float32 Manning 128x128]
├── simulations/
│   ├── event_01_2015_deluge_hydro_sim.npz           [Simulated H, U, V arrays (Train)]
│   ├── event_02_michaung_surge_hydro_sim.npz        [Simulated H, U, V arrays (Val)]
│   └── event_03_monsoon_moderate_hydro_sim.npz      [Simulated H, U, V arrays (Test)]
├── tensors/
│   ├── event_01_2015_deluge_input_tensor.pt         [torch.Size([1, 128, 128, 24, 1, 5])]
│   ├── event_01_2015_deluge_target_tensor.pt        [torch.Size([1, 128, 128, 24, 3])]
│   ├── event_02_michaung_surge_input_tensor.pt      [torch.Size([1, 128, 128, 24, 1, 5])]
│   ├── event_02_michaung_surge_target_tensor.pt     [torch.Size([1, 128, 128, 24, 3])]
│   ├── event_03_monsoon_moderate_input_tensor.pt    [torch.Size([1, 128, 128, 24, 1, 5])]
│   └── event_03_monsoon_moderate_target_tensor.pt   [torch.Size([1, 128, 128, 24, 3])]
└── metadata/
    └── chennai_dno_simulation_metadata.json         [Run metadata & validation metrics]
```
