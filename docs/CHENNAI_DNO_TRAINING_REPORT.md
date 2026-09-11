# Greater Chennai Corporation (GCC) UrbanFloodCast DNO Training Report
**FloodWatch AI — Phase 4: First Experimental Deep Neural Operator Training Run**  
**Document Reference:** `docs/CHENNAI_DNO_TRAINING_REPORT.md`  
**Execution Date:** September 11, 2026  
**Target Domain:** Adyar–Velachery Basin, Greater Chennai Corporation (GCC), Tamil Nadu  
**Coordinate Reference System:** EPSG:32644 (WGS 84 / UTM Zone 44N)  
**Hardware Profile:** NVIDIA GeForce RTX 3050 Laptop GPU (6.0 GB VRAM)  
**Dataset Classification:** `SIMULATED HYDRODYNAMIC TRAINING DATA`  

---

## 1. Executive Objective

Following the successful completion of the Chennai 2D hydrodynamic simulation proof-of-concept and strict scientific provenance verification, Phase 4 executed the **first controlled experimental training run of the Deep Neural Operator (DNO)** for Greater Chennai.

The core objective was to establish whether a Fourier-based neural operator initialized completely from scratch can learn the non-linear spatio-temporal mapping from terrain elevation ($Z$), rainfall forcing ($P$), and pre-storm initial conditions ($H_0, U_0, V_0$) to dynamic flood depths ($H$) and velocity vectors ($U, V$).

**Mandatory Governance Rules Maintained:**
1. **Zero Berlin Weights:** Initialized randomly from scratch with seed 42.
2. **Untouched External Core:** `External/UrbanFloodCast/UrbanFloodCast/` remained unmodified.
3. **Untouched Production Pipeline:** The operational XGBoost sector model (`models/trained/chennai_xgboost_baseline.json`) and FastAPI backend remain isolated and operational.
4. **Target Classification:** All ground-truth outputs remain explicitly designated as **`SIMULATED HYDRODYNAMIC TRAINING DATA`**.
5. **No False Production Claims:** The DNO is strictly evaluated as an experimental research surrogate.

---

## 2. Dataset & Event Partitioning

The experimental dataset conforms to the verified event-based partition designed to eliminate spatial and temporal auto-correlation:

| Partition | Event Identifier | Historical Scenario | 2h Rainfall Total | Role in Experiment |
| :--- | :--- | :--- | :---: | :--- |
| **TRAIN** | `event_01_2015_deluge` | Dec 1, 2015 Historic Deluge Peak Wave | $75.33\text{ mm}$ | Optimization gradient descent |
| **VAL** | `event_02_michaung_surge` | Dec 4, 2023 Cyclone Michaung Surge | $77.25\text{ mm}$ | Checkpoint selection & early stopping |
| **TEST** | `event_03_monsoon_moderate`| Representative Northeast Monsoon Wave | $27.50\text{ mm}$ | Out-of-sample physical evaluation |

* **Discretization:** $128 \times 128$ Cartesian grid ($\Delta x = 78.125\text{ m}$), $T = 24$ timesteps ($\Delta t = 300\text{ s} = 5.0\text{ min}$, total window $2.0\text{ hours}$).
* **Input Tensor Shape ($X$):** `[1, 128, 128, 24, 1, 5]`
  * Channel 0: $H_0$ (Pre-storm water depth, normalized)
  * Channel 1: $U_0$ (Pre-storm X-velocity, normalized)
  * Channel 2: $V_0$ (Pre-storm Y-velocity, normalized)
  * Channel 3: $P(t)$ (Spatiotemporal precipitation forcing [$\text{mm/hr}$], normalized)
  * Channel 4: $Z$ (Digital Elevation Model topography [$\text{m MSL}$], normalized)
* **Target Tensor Shape ($Y$):** `[1, 128, 128, 24, 3]`
  * Channel 0: $H(x, y, t)$ — Water depth [$\text{meters}$]
  * Channel 1: $U(x, y, t)$ — X-velocity [$\text{m/s}$]
  * Channel 2: $V(x, y, t)$ — Y-velocity [$\text{m/s}$]

---

## 3. Model Architecture & Hyperparameters

* **Model Class:** `DNO` (UrbanFloodCast 3D Integral Operator Network)
* **Channel Configuration:** `num_channels = 5`, `initial_step = 1`, `width = 10`, `factor = 1`, `pad = 0`
* **Total Parameters:** **`4,470,437`** (all trainable, initialized from scratch)
* **Optimizer:** Adam ($\beta_1 = 0.9, \beta_2 = 0.999$, weight decay $= 10^{-4}$)
* **Learning Rate:** $1.0 \times 10^{-3}$
* **Batch Size:** $1$ (Single storm spatiotemporal patch)
* **Loss Formulation:** Relative $L_2$ Loss ($L_p$-norm with $p=2$) conforming to UrbanFloodCast:
  $$\mathcal{L}_{rel} = \frac{1}{3} \sum_{c \in \{H, U, V\}} \frac{\|\hat{\mathbf{y}}_c - \mathbf{y}_c\|_2}{\|\mathbf{y}_c\|_2 + \epsilon}$$
* **Early Stopping:** Patience $= 10$ epochs monitoring validation loss.

---

## 4. Hardware Profiling on NVIDIA RTX 3050 Laptop GPU (6GB VRAM)

* **Peak Allocated VRAM:** **$745.2\text{ MB}$** ($0.728\text{ GB}$)
* **Peak Reserved VRAM:** **$908.0\text{ MB}$** ($0.887\text{ GB}$)
* **Available VRAM Headroom:** **$5,235.5\text{ MB}$** ($> 5.2\text{ GB}$ unused capacity)
* **Average Epoch Execution Time:** **$0.13\text{–}0.14\text{ seconds}$**
* **CUDA Out-of-Memory:** **NONE** (Zero memory pressure in FP32).

---

## 5. Training & Validation Progression

The training was executed for the full planned 30 epochs:

| Epoch | Train Rel Loss | Val Rel Loss | Val $H$ Loss | Val $U$ Loss | Val $V$ Loss | Time (s) | Best Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | $1.57352$ | $1.47564$ | $1.2347$ | $1.0953$ | $2.0970$ | $0.52$ | Checkpoint saved |
| **05** | $1.31025$ | $1.24826$ | $1.0958$ | $0.9941$ | $1.6548$ | $0.13$ | Checkpoint saved |
| **10** | $1.10220$ | $1.06576$ | $0.9721$ | $0.9651$ | $1.2601$ | $0.13$ | Checkpoint saved |
| **15** | $0.98332$ | $0.96872$ | $0.9259$ | $0.9508$ | $1.0294$ | $0.13$ | Checkpoint saved |
| **20** | $0.95358$ | $0.94958$ | $0.9302$ | $0.9385$ | $0.9801$ | $0.13$ | Checkpoint saved |
| **25** | $0.94837$ | $0.94237$ | $0.9256$ | $0.9241$ | $0.9774$ | $0.13$ | Checkpoint saved |
| **30** | $\mathbf{0.93129}$ | $\mathbf{0.92590}$ | $\mathbf{0.9184}$ | $\mathbf{0.9075}$ | $\mathbf{0.9519}$ | $0.13$ | **Best Model (Epoch 30)** |

### Optimization Dynamics:
* **Training Loss Reduction:** Decreased monotonically from $1.5735 \to 0.9313$ (**$-40.8\%$** reduction).
* **Validation Loss Reduction:** Decreased monotonically from $1.4756 \to 0.9259$ (**$-37.3\%$** reduction).
* **Component Balance:** All three hydrodynamic channels showed stable convergence:
  * $H$ loss decreased from $1.2347 \to 0.9184$ ($-25.6\%$)
  * $U$ loss decreased from $1.0953 \to 0.9075$ ($-17.1\%$)
  * $V$ loss decreased from $2.0970 \to 0.9519$ ($-54.6\%$)

---

## 6. Out-of-Sample Test Evaluation (`event_03_monsoon_moderate`)

The best checkpoint (Epoch 30) was loaded and evaluated against the unseen moderate monsoon storm scenario:

### Physical Performance Metrics:
| Variable | Mean Absolute Error (MAE) | Root Mean Squared Error (RMSE) | Max Absolute Error | Pearson Correlation ($r$) |
| :--- | :---: | :---: | :---: | :---: |
| **Water Depth ($H$)** | **$0.0533\text{ m}$ ($5.33\text{ cm}$)** | **$0.0661\text{ m}$ ($6.61\text{ cm}$)** | $0.9046\text{ m}$ | $+0.1247$ |
| **X Velocity ($U$)** | **$0.0308\text{ m/s}$** | **$0.0434\text{ m/s}$** | $1.2201\text{ m/s}$ | $+0.3241$ |
| **Y Velocity ($V$)** | **$0.0264\text{ m/s}$** | **$0.0407\text{ m/s}$** | $1.3145\text{ m/s}$ | $+0.2636$ |

### Spatial & Inundation Alignment:
* **Wet-Cell Overlap ($H > 5\text{ cm}$):** Critical Success Index (CSI) $= 0.1110$ ($11.1\%$).
  * True wet cells detected (Hits): $1,492$
  * Missed wet cells: $391$
  * False alarm wet cells: $11,559$
* **Peak Depth Metrics:**
  * True Domain Maximum Depth: $0.9607\text{ m}$ (at $t = 115\text{ min}$)
  * DNO Predicted Peak Depth: $0.1660\text{ m}$ (at $t = 35\text{ min}$)
  * Peak Depth Discrepancy: $-0.7947\text{ m}$ | Peak Timing Shift: $-80.0\text{ min}$

---

## 7. Speed Benchmark: Hydrodynamic Solver vs Neural Surrogate

The central scientific premise of neural operators is replacing compute-intensive PDEs with real-time neural inference:

* **2D Inertial Hydrodynamic Simulation (7,200 numerical sub-steps):** **$3.004\text{ s}$**
* **DNO Neural Surrogate Forward Pass:** **$0.0357\text{ s}$ ($35.7\text{ ms}$)**
* **Measured Acceleration Factor:** **`84.1x faster than numerical solver`**

The DNO computes the entire 2-hour spatio-temporal inundation sequence in sub-50 milliseconds on local hardware.

---

## 8. Physical Validation & Diagnostic Artifacts

Diagnostic graphics have been generated and saved under `outputs/chennai_dno/`:
1. **Spatial 9-Panel Verification (`chennai_dno_test_spatial_comparison.png`):**
   * Compares ground-truth simulation fields ($H, U, V$) against DNO predictions and spatial absolute error heatmaps at the terminal 2-hour timestamp ($t=120\text{ min}$).
2. **Temporal Hydrograph (`chennai_dno_test_temporal_hydrograph.png`):**
   * Traces domain-maximum depth and domain-mean depth evolution across all 24 timesteps ($5\text{ to }120\text{ min}$) between hydrodynamic ground truth and DNO predictions.

---

## 9. Failure Analysis & Scientific Interpretation

Why did the model exhibit low MAE ($5.3\text{ cm}$) but low spatial correlation ($0.12$) and under-predicted peak depth on Test Event 03?
1. **Storm Scale Asymmetry:**
   * Training Event 01: Extreme 2015 Deluge ($75.33\text{ mm}$ rain, $2.37\text{ m}$ max depth).
   * Validation Event 02: Extreme Cyclone Michaung ($77.25\text{ mm}$ rain, $2.45\text{ m}$ max depth).
   * Test Event 03: Moderate Northeast Monsoon shower ($27.50\text{ mm}$ rain, $0.96\text{ m}$ max depth).
   * The neural operator was optimized solely on severe disaster-scale forcing, leading to a tendency to smooth out localized deep depression ponding when forced with low-magnitude precipitation.
2. **Single Training Sample:**
   * With only $N=1$ training storm patch, the model cannot easily generalize the non-linear relationship between rainfall intensity and hydraulic accumulation.
3. **Loss Function Normalization:**
   * Relative $L_2$ loss effectively balanced channel magnitudes, but penalizes large diffuse errors equally to deep localized channel errors.

---

## 10. Model Quality Gates & Final Classifications

In accordance with strict scientific evaluation criteria:

### 1. TRAINING STATUS: **`A — MODEL LEARNS SUCCESSFULLY`**
* The neural operator converged steadily over 30 epochs without divergence, reducing relative training loss by $40.8\%$ and validation loss by $37.3\%$.

### 2. GENERALIZATION STATUS: **`B — PARTIAL GENERALIZATION`**
* The model produces physically bounded overland flow depths (MAE $5.3\text{ cm}$) and realistic flow velocity ranges ($0.03\text{ m/s}$ MAE), but demonstrates weak spatial correlation ($r=0.12$) and temporal lag when generalizing across widely disparate storm intensities.

### 3. PHYSICAL SURROGATE STATUS: **`B — REQUIRES MORE TRAINING/DATA`**
* A three-event dataset is an essential proof-of-concept, but does not constitute an operationally reliable hydrodynamic surrogate.

---

## 11. Important Data Limitation & Boundary Notice

> [!WARNING]
> **Three-event training is an experimental proof-of-concept and does not establish broad operational generalization.**  
> The DNO must NOT be integrated into the FloodWatch AI production API, backend services, or municipal warning feeds. The operational municipal pipeline remains strictly powered by the audited XGBoost sector vulnerability engine (`models/trained/chennai_xgboost_baseline.json`).

---

## 12. Recommended Next Experiment (Phase 5 Roadmap)

1. **Synthetic Hyetograph Augmentation ($N=20\text{–}50$ Storm Events):**
   * Generate an ensemble of parameterized storm scenarios covering rainfall totals from $10\text{ mm}$ to $150\text{ mm}$ and varying storm durations ($1\text{ to }6\text{ hours}$).
2. **Weighted Multi-Scale Depth Loss:**
   * Implement threshold-weighted loss (e.g., higher penalty for wet cells $H > 0.1\text{ m}$) to prevent the model from underpredicting depression ponding.
3. **Longer Horizon Training:**
   * Train for $100\text{ epochs}$ with cosine annealing learning rate scheduling once the augmented storm library is established.
