# Ground Truth Label Methodology — Mumbai Flood Nowcasting

## 1. Problem Formulation
- **Task**: Binary classification of localized urban inundation / flood hazard per spatial grid sector.
- **Unit of Analysis**: One 500m × 500m spatial grid cell ($i$) at one observation timestamp ($t$).
- **Target Variable**: $y_{i,t} \in \{0, 1\}$
  - $0$: No waterlogging / Normal gravity drainage capacity.
  - $1$: Active urban flood / waterlogging threshold exceeded.

---

## 2. Label Construction Rules
Ground truth labels are synthesized from two complementary hydrological and observational streams:

1. **Topographic-Hydrological Runoff Exceedance Rule**:
   $$\text{Runoff Index}_{i,t} = \frac{(0.45 \cdot R_{1h} + 0.35 \cdot \frac{R_{3h}}{3} + 0.20 \cdot \frac{R_{24h}}{24}) \times \text{BuiltUpRatio}_i}{\max(0.20, \; 0.08 \cdot \ln(1 + d_{\text{drain}}) + \frac{\text{Elev}_i}{12.0})} + 1.8 \cdot \text{HotspotScore}_i$$
   - A cell is labeled as flooded ($y = 1$) if $\text{Runoff Index}_{i,t} \ge 3.8$ or intense cloudburst occurs in low-lying saucer terrain ($R_{1h} \ge 38\text{ mm/hr} \land \text{LowLyingScore}_i \ge 0.70$).

2. **BMC Chronic Hotspot Spatial-Temporal Coincidence**:
   - Ground truth records from BMC 386 Chronic Waterlogging spots (Hindmata, Milan Subway, Andheri Subway, Kurla Kamani, King's Circle, Chunabhatti, Sakinaka, Dahisar) are intersected with grid sectors.
   - When station precipitation in the ward exceeds $25\text{ mm/hr}$, sectors enclosing chronic underpass spots transition to positive flood state.

---

## 3. Multi-Horizon Nowcasting Targets
- `target_now`: Flood condition at observation time $T$.
- `target_plus_1h`: Forward-looking flood state at $T + 1\text{ hour}$.
- `target_plus_3h`: Extended forward recession / surge state at $T + 3\text{ hours}$.

---

## 4. Prevention of Data Leakage
- **No Target Leakage**: Dynamic rainfall features $R_{1h}, R_{3h}, R_{6h}, R_{24h}$ utilize **strictly antecedent and current** observation windows relative to $T$. Future precipitation is only used for verifying the forward target labels, never as model features.
- **Time-Aware Split**: All train/validation/test splits are chronological. Model evaluation is conducted on held-out subsequent storm intervals to evaluate real forward nowcasting generalization.
