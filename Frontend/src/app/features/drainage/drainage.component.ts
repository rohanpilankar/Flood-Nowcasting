import { Component, OnInit, ElementRef, ViewChild, OnDestroy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../environments/environment';

export interface DrainageNode3D {
  id: string;
  name: string;
  type: string;
  basin: string;
  lat: number;
  lon: number;
  surface_elevation_m: number;
  invert_elevation_m: number;
  depth_m: number;
  description: string;
  // Computed 3D scene positions
  screenX?: number;
  screenY?: number;
}

export interface DrainageEdge3D {
  id: string;
  name: string;
  type: string;
  source_node: string;
  target_node: string;
  length_m: number;
  width_m: number;
  height_m: number;
  shape: string;
  manning_n: number;
  slope: number;
  manning_capacity_m3s: number;
  catchment_area_ha: number;
  runoff_coeff: number;
}

export interface HydraulicInspection {
  pipe_id: string;
  pipe_name: string;
  pipe_type: string;
  source_node: DrainageNode3D;
  target_node: DrainageNode3D;
  hydraulic_status: 'UNDERFLOW' | 'TRANSITION' | 'OVERFLOW_SURCHARGE';
  severity_level: 'SAFE' | 'ALERT' | 'CRITICAL';
  parameters: {
    rainfall_intensity_mm_h: number;
    catchment_area_ha: number;
    runoff_coefficient: number;
    conduit_length_m: number;
    bed_slope_pct: number;
    manning_roughness_n: number;
    cross_sectional_area_m2: number;
    hydraulic_radius_m: number;
    full_capacity_m3s: number;
    inflow_discharge_m3s: number;
    capacity_utilization_pct: number;
    water_velocity_m_s: number;
    estimated_flow_depth_m: number;
    surcharge_rate_m3s: number;
    surcharge_head_m: number;
    freeboard_m: number;
  };
  engineering_verdict: string;
  timestamp: string;
}

@Component({
  selector: 'app-drainage-3d',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="drainage-page">
      <!-- Top Title & Stats Banner -->
      <div class="drainage-header">
        <div>
          <div class="header-badge-row">
            <h1 class="page-title">Greater Chennai 3D Drainage & Hydraulic Network</h1>
            <span class="badge-status-3d">WebGL 3D Graph</span>
            <span class="badge-crs">UTM 44N (MSL Datum)</span>
          </div>
          <p class="page-subtitle">
            Physical node-and-conduit mapping with real ground elevations, Manning conveyance capacity, and Rational method surcharge prediction.
          </p>
        </div>
        <div class="view-controls">
          <button class="btn-ctrl" (click)="resetCamera()" title="Reset Camera View">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
            Isometric
          </button>
          <button class="btn-ctrl" (click)="setTopView()" title="Top-down Ortho View">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path><path d="M2 12h20"></path></svg>
            Top-Down
          </button>
          <button class="btn-ctrl" (click)="toggleElevationExaggeration()" title="Toggle Vertical Elevation Scale">
            Z-Scale: {{ zScale }}x
          </button>
        </div>
      </div>

      <!-- Main Layout: 3D Canvas + Engineering Inspector -->
      <div class="drainage-layout">
        <!-- 3D Canvas Viewport -->
        <div class="canvas-container" #containerRef>
          <canvas #canvasRef
            (mousedown)="onMouseDown($event)"
            (mousemove)="onMouseMove($event)"
            (mouseup)="onMouseUp()"
            (wheel)="onWheel($event)"
            (click)="onCanvasClick($event)">
          </canvas>

          <!-- 3D HUD Overlay -->
          <div class="canvas-hud">
            <div class="hud-item">
              <span class="hud-label">Nodes (Manholes / Outfalls)</span>
              <span class="hud-val font-mono">{{ nodes.length }}</span>
            </div>
            <div class="hud-item">
              <span class="hud-label">Conduits / Canals</span>
              <span class="hud-val font-mono">{{ edges.length }}</span>
            </div>
            <div class="hud-item">
              <span class="hud-label">Elevation Range</span>
              <span class="hud-val font-mono text-cyan">0.0m - 12.4m MSL</span>
            </div>
            <div class="hud-item">
              <span class="hud-label">Selected Segment</span>
              <span class="hud-val font-mono text-amber">{{ selectedEdge ? selectedEdge.name : 'Click conduit' }}</span>
            </div>
          </div>

          <!-- Color Legend -->
          <div class="canvas-legend">
            <span class="legend-title">Hydraulic Conveyance</span>
            <div class="legend-item"><span class="legend-box safe"></span> Underflow (Q &lt; 80% Cap)</div>
            <div class="legend-item"><span class="legend-box warning"></span> Transition (80-100% Cap)</div>
            <div class="legend-item"><span class="legend-box critical"></span> Surcharge Overflow (&gt; 100%)</div>
            <div class="legend-item"><span class="legend-dot node-dot"></span> Junction / Outfall Node</div>
          </div>

          <!-- Instruction Tooltip -->
          <div class="canvas-hint">
            <span>🖱️ Drag to rotate 3D view | Scroll to zoom | Click any pipe or junction node to inspect hydraulics</span>
          </div>
        </div>

        <!-- Right Side: Hydraulic Engineering Inspector -->
        <div class="inspector-panel" *ngIf="inspection; else noSelection">
          <div class="panel-header">
            <div class="panel-tag" [ngClass]="inspection.hydraulic_status.toLowerCase()">
              {{ inspection.hydraulic_status === 'OVERFLOW_SURCHARGE' ? 'SURCHARGE OVERFLOW' : inspection.hydraulic_status }}
            </div>
            <h3 class="panel-title">{{ inspection.pipe_name }}</h3>
            <span class="panel-id font-mono">{{ inspection.pipe_id }} ({{ inspection.pipe_type }})</span>
          </div>

          <!-- Interactive Rainfall Intensity Slider -->
          <div class="control-box">
            <div class="control-label-row">
              <span class="ctrl-title">Storm Rainfall Intensity (I)</span>
              <span class="ctrl-val font-mono">{{ rainfallIntensity }} mm/h</span>
            </div>
            <input
              type="range"
              class="slider"
              min="10"
              max="150"
              step="5"
              [(ngModel)]="rainfallIntensity"
              (input)="onRainfallChange()"
            />
            <div class="slider-presets">
              <button (click)="setPresetRainfall(25)">Moderate (25mm/h)</button>
              <button (click)="setPresetRainfall(50)">Heavy (50mm/h)</button>
              <button (click)="setPresetRainfall(100)">Deluge (100mm/h)</button>
            </div>
          </div>

          <!-- Verdict Banner -->
          <div class="verdict-card" [ngClass]="inspection.severity_level.toLowerCase()">
            <div class="verdict-icon">
              <span *ngIf="inspection.severity_level === 'CRITICAL'">⚠️</span>
              <span *ngIf="inspection.severity_level === 'ALERT'">⚡</span>
              <span *ngIf="inspection.severity_level === 'SAFE'">✅</span>
            </div>
            <div class="verdict-text">
              <div class="verdict-title">{{ inspection.severity_level }} HYDRAULIC STATUS</div>
              <p class="verdict-desc">{{ inspection.engineering_verdict }}</p>
            </div>
          </div>

          <!-- Key Quantitative Metrics Grid -->
          <div class="metrics-grid">
            <div class="metric-card">
              <span class="m-label">Manning Capacity (Q_cap)</span>
              <span class="m-val font-mono">{{ inspection.parameters.full_capacity_m3s }} <small>m³/s</small></span>
              <span class="m-sub">Full pipe gravity flow</span>
            </div>
            <div class="metric-card">
              <span class="m-label">Runoff Inflow (Q_in)</span>
              <span class="m-val font-mono" [class.text-critical]="inspection.parameters.inflow_discharge_m3s > inspection.parameters.full_capacity_m3s">
                {{ inspection.parameters.inflow_discharge_m3s }} <small>m³/s</small>
              </span>
              <span class="m-sub">Rational method (C=0.75)</span>
            </div>
            <div class="metric-card">
              <span class="m-label">Capacity Utilization</span>
              <span class="m-val font-mono" [class.text-critical]="inspection.parameters.capacity_utilization_pct > 100">
                {{ inspection.parameters.capacity_utilization_pct }}%
              </span>
              <div class="util-bar">
                <div class="util-fill" [style.width.%]="mathMin(inspection.parameters.capacity_utilization_pct, 100)" [ngClass]="inspection.severity_level.toLowerCase()"></div>
              </div>
            </div>
            <div class="metric-card">
              <span class="m-label">Flow Velocity (V)</span>
              <span class="m-val font-mono">{{ inspection.parameters.water_velocity_m_s }} <small>m/s</small></span>
              <span class="m-sub">Kinematic flow velocity</span>
            </div>
          </div>

          <!-- Physical Conduit Engineering Specs -->
          <div class="specs-table-card">
            <div class="specs-title">Physical Conduit Parameters</div>
            <table class="specs-table">
              <tbody>
                <tr>
                  <td>Conduit Length</td>
                  <td class="font-mono">{{ inspection.parameters.conduit_length_m | number:'1.0-0' }} m</td>
                </tr>
                <tr>
                  <td>Bed Slope (S)</td>
                  <td class="font-mono">{{ inspection.parameters.bed_slope_pct }}% gradient</td>
                </tr>
                <tr>
                  <td>Manning Roughness (n)</td>
                  <td class="font-mono">{{ inspection.parameters.manning_roughness_n }} (Concrete/Masonry)</td>
                </tr>
                <tr>
                  <td>Cross-Sectional Area (A)</td>
                  <td class="font-mono">{{ inspection.parameters.cross_sectional_area_m2 }} m²</td>
                </tr>
                <tr>
                  <td>Hydraulic Radius (R)</td>
                  <td class="font-mono">{{ inspection.parameters.hydraulic_radius_m }} m</td>
                </tr>
                <tr>
                  <td>Contributing Catchment</td>
                  <td class="font-mono">{{ inspection.parameters.catchment_area_ha }} ha</td>
                </tr>
                <tr *ngIf="inspection.parameters.surcharge_rate_m3s > 0">
                  <td class="text-critical font-bold">Surcharge Rate</td>
                  <td class="font-mono text-critical font-bold">+{{ inspection.parameters.surcharge_rate_m3s }} m³/s to street</td>
                </tr>
                <tr *ngIf="inspection.parameters.freeboard_m > 0">
                  <td class="text-safe">Freeboard Head</td>
                  <td class="font-mono text-safe">{{ inspection.parameters.freeboard_m }} m remaining</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Connected Nodes -->
          <div class="node-pair-card">
            <div class="node-item">
              <span class="node-role">Upstream Source:</span>
              <span class="node-name">{{ inspection.source_node.name }}</span>
              <span class="node-elev font-mono">Invert: {{ inspection.source_node.invert_elevation_m }}m | Surface: {{ inspection.source_node.surface_elevation_m }}m</span>
            </div>
            <div class="node-divider">➔</div>
            <div class="node-item">
              <span class="node-role">Downstream Target:</span>
              <span class="node-name">{{ inspection.target_node.name }}</span>
              <span class="node-elev font-mono">Invert: {{ inspection.target_node.invert_elevation_m }}m | Surface: {{ inspection.target_node.surface_elevation_m }}m</span>
            </div>
          </div>
        </div>

        <ng-template #noSelection>
          <div class="inspector-panel empty-panel">
            <div class="empty-state">
              <div class="empty-icon">🌊</div>
              <h3>Select a Drainage Conduit</h3>
              <p>Click any 3D conduit line or junction node on the viewport to calculate real-world Manning capacity, hydraulic slope, and rainfall overflow prediction.</p>
              <button class="btn-select-default" (click)="selectDefaultPipe()">Select Velachery Macro Trunk</button>
            </div>
          </div>
        </ng-template>
      </div>
    </div>
  `,
  styles: [`
    .drainage-page {
      padding: 1.5rem 2rem;
      background-color: var(--bg-dark);
      color: var(--text-main);
      min-height: calc(100vh - var(--header-height));
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    .drainage-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .header-badge-row {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .page-title {
      font-size: 1.45rem;
      font-weight: 700;
      color: var(--text-main);
      margin: 0;
    }
    .badge-status-3d {
      background: rgba(6, 182, 212, 0.15);
      border: 1px solid rgba(6, 182, 212, 0.4);
      color: #06b6d4;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.2rem 0.6rem;
      border-radius: var(--radius-full);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .badge-crs {
      background: rgba(148, 163, 184, 0.12);
      color: #94a3b8;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 0.2rem 0.55rem;
      border-radius: var(--radius-full);
    }
    .page-subtitle {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin: 0.35rem 0 0;
      max-width: 820px;
    }
    .view-controls {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .btn-ctrl {
      background-color: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      font-size: 0.78rem;
      font-weight: 600;
      padding: 0.45rem 0.85rem;
      border-radius: var(--radius-sm);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: all var(--transition-fast);
    }
    .btn-ctrl:hover {
      color: var(--text-main);
      border-color: var(--border-focus);
      background-color: var(--bg-card-hover);
    }

    /* Layout */
    .drainage-layout {
      display: grid;
      grid-template-columns: 1fr 420px;
      gap: 1.25rem;
      flex: 1;
      min-height: 640px;
    }
    @media (max-width: 1180px) {
      .drainage-layout {
        grid-template-columns: 1fr;
      }
    }

    /* 3D Canvas Viewport */
    .canvas-container {
      position: relative;
      background: radial-gradient(circle at 50% 50%, #0c1222 0%, #050811 100%);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      overflow: hidden;
      min-height: 600px;
      display: flex;
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.4);
    }
    canvas {
      width: 100%;
      height: 100%;
      display: block;
      cursor: grab;
    }
    canvas:active {
      cursor: grabbing;
    }

    .canvas-hud {
      position: absolute;
      top: 1rem;
      left: 1rem;
      display: flex;
      gap: 0.75rem;
      background: rgba(10, 15, 30, 0.75);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 0.6rem 0.9rem;
      z-index: 10;
      flex-wrap: wrap;
    }
    .hud-item {
      display: flex;
      flex-direction: column;
    }
    .hud-label {
      font-size: 0.65rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .hud-val {
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .text-cyan { color: #06b6d4; }
    .text-amber { color: #f59e0b; }
    .text-critical { color: #ef4444; }
    .text-safe { color: #10b981; }

    .canvas-legend {
      position: absolute;
      bottom: 2.75rem;
      left: 1rem;
      background: rgba(10, 15, 30, 0.8);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 0.6rem 0.85rem;
      z-index: 10;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .legend-title {
      font-size: 0.68rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      margin-bottom: 0.2rem;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.72rem;
      color: var(--text-main);
    }
    .legend-box {
      width: 14px;
      height: 4px;
      border-radius: 2px;
    }
    .legend-box.safe { background-color: #10b981; }
    .legend-box.warning { background-color: #f59e0b; }
    .legend-box.critical { background-color: #ef4444; }
    .legend-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: #06b6d4;
      border: 1px solid #ffffff;
    }

    .canvas-hint {
      position: absolute;
      bottom: 0.85rem;
      left: 1rem;
      right: 1rem;
      font-size: 0.72rem;
      color: rgba(148, 163, 184, 0.7);
      background: rgba(5, 8, 17, 0.6);
      padding: 0.35rem 0.75rem;
      border-radius: var(--radius-sm);
      pointer-events: none;
    }

    /* Inspector Panel */
    .inspector-panel {
      background-color: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1.1rem;
      overflow-y: auto;
      max-height: 800px;
    }
    .panel-header {
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
    }
    .panel-tag {
      font-size: 0.68rem;
      font-weight: 800;
      padding: 0.2rem 0.55rem;
      border-radius: var(--radius-full);
      display: inline-block;
      width: fit-content;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .panel-tag.underflow {
      background: rgba(16, 185, 129, 0.15);
      color: #10b981;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .panel-tag.transition {
      background: rgba(245, 158, 11, 0.15);
      color: #f59e0b;
      border: 1px solid rgba(245, 158, 11, 0.4);
    }
    .panel-tag.overflow_surcharge {
      background: rgba(239, 68, 68, 0.15);
      color: #ef4444;
      border: 1px solid rgba(239, 68, 68, 0.4);
    }
    .panel-title {
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--text-main);
      margin: 0;
    }
    .panel-id {
      font-size: 0.72rem;
      color: var(--text-muted);
    }

    /* Control Box */
    .control-box {
      background-color: var(--bg-card-subtle);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }
    .control-label-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .ctrl-title {
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-main);
    }
    .ctrl-val {
      font-size: 0.85rem;
      font-weight: 700;
      color: #06b6d4;
    }
    .slider {
      width: 100%;
      height: 6px;
      border-radius: 3px;
      background: #1e293b;
      outline: none;
      accent-color: #06b6d4;
      cursor: pointer;
    }
    .slider-presets {
      display: flex;
      gap: 0.4rem;
    }
    .slider-presets button {
      flex: 1;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      font-size: 0.68rem;
      padding: 0.3rem 0;
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: all var(--transition-fast);
    }
    .slider-presets button:hover {
      color: var(--text-main);
      border-color: #06b6d4;
    }

    /* Verdict Card */
    .verdict-card {
      display: flex;
      gap: 0.75rem;
      padding: 0.85rem;
      border-radius: var(--radius-sm);
      border: 1px solid transparent;
    }
    .verdict-card.safe {
      background: rgba(16, 185, 129, 0.08);
      border-color: rgba(16, 185, 129, 0.3);
    }
    .verdict-card.alert {
      background: rgba(245, 158, 11, 0.08);
      border-color: rgba(245, 158, 11, 0.3);
    }
    .verdict-card.critical {
      background: rgba(239, 68, 68, 0.1);
      border-color: rgba(239, 68, 68, 0.35);
    }
    .verdict-icon {
      font-size: 1.25rem;
      flex-shrink: 0;
    }
    .verdict-title {
      font-size: 0.72rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .verdict-card.safe .verdict-title { color: #10b981; }
    .verdict-card.alert .verdict-title { color: #f59e0b; }
    .verdict-card.critical .verdict-title { color: #ef4444; }
    .verdict-desc {
      font-size: 0.78rem;
      color: var(--text-main);
      margin: 0.2rem 0 0;
      line-height: 1.35;
    }

    /* Metrics Grid */
    .metrics-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.65rem;
    }
    .metric-card {
      background-color: var(--bg-card-subtle);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 0.75rem;
      display: flex;
      flex-direction: column;
    }
    .m-label {
      font-size: 0.65rem;
      color: var(--text-muted);
      text-transform: uppercase;
    }
    .m-val {
      font-size: 1.1rem;
      font-weight: 800;
      color: var(--text-main);
      margin: 0.2rem 0 0;
    }
    .m-val small {
      font-size: 0.75rem;
      font-weight: 500;
      color: var(--text-muted);
    }
    .m-sub {
      font-size: 0.65rem;
      color: var(--text-muted);
      margin-top: 0.2rem;
    }
    .util-bar {
      width: 100%;
      height: 4px;
      background: #1e293b;
      border-radius: 2px;
      margin-top: 0.35rem;
      overflow: hidden;
    }
    .util-fill {
      height: 100%;
    }
    .util-fill.safe { background: #10b981; }
    .util-fill.alert { background: #f59e0b; }
    .util-fill.critical { background: #ef4444; }

    /* Specs Table */
    .specs-table-card {
      background-color: var(--bg-card-subtle);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 0.85rem;
    }
    .specs-title {
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      margin-bottom: 0.5rem;
    }
    .specs-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.75rem;
    }
    .specs-table td {
      padding: 0.35rem 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    .specs-table td:last-child {
      text-align: right;
      font-weight: 600;
    }

    /* Node Pair */
    .node-pair-card {
      background: rgba(6, 182, 212, 0.04);
      border: 1px solid rgba(6, 182, 212, 0.2);
      border-radius: var(--radius-sm);
      padding: 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }
    .node-divider {
      text-align: center;
      color: #06b6d4;
      font-size: 0.9rem;
    }
    .node-item {
      display: flex;
      flex-direction: column;
    }
    .node-role {
      font-size: 0.65rem;
      color: var(--text-muted);
    }
    .node-name {
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .node-elev {
      font-size: 0.68rem;
      color: #06b6d4;
    }

    /* Empty Panel */
    .empty-panel {
      justify-content: center;
      align-items: center;
      text-align: center;
    }
    .empty-state {
      max-width: 280px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.65rem;
    }
    .empty-icon {
      font-size: 2.5rem;
    }
    .empty-state h3 {
      font-size: 1.05rem;
      color: var(--text-main);
      margin: 0;
    }
    .empty-state p {
      font-size: 0.78rem;
      color: var(--text-muted);
      line-height: 1.4;
      margin: 0;
    }
    .btn-select-default {
      margin-top: 0.5rem;
      background: #06b6d4;
      color: #050811;
      font-weight: 700;
      font-size: 0.78rem;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: var(--radius-sm);
      cursor: pointer;
    }
  `]
})
export class DrainageComponent implements OnInit, OnDestroy {
  @ViewChild('canvasRef', { static: true }) canvasRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('containerRef', { static: true }) containerRef!: ElementRef<HTMLDivElement>;

  nodes: DrainageNode3D[] = [];
  edges: DrainageEdge3D[] = [];
  selectedEdge: DrainageEdge3D | null = null;
  selectedNode: DrainageNode3D | null = null;
  inspection: HydraulicInspection | null = null;

  rainfallIntensity = 45.0; // mm/h
  zScale = 2.0;

  // 3D Engine state (Rotations & Pan)
  private rotX = 0.55;  // pitch
  private rotY = -0.45; // yaw
  private zoom = 1.0;
  private panX = 0;
  private panY = 0;
  private isDragging = false;
  private lastMouseX = 0;
  private lastMouseY = 0;
  private animationFrameId = 0;

  // Geographic bounds of Chennai network
  private bounds = {
    minLat: 12.87, maxLat: 13.23,
    minLon: 80.12, maxLon: 80.32,
    minElev: 0.0, maxElev: 13.0
  };

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.fetchDrainageNetwork();
  }

  ngOnDestroy(): void {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
  }

  fetchDrainageNetwork(): void {
    this.http.get<any>(`${environment.apiBaseUrl}/api/v1/drainage/network-3d`).subscribe({
      next: (res) => {
        this.nodes = res.nodes || [];
        this.edges = res.edges || [];
        this.initCanvas3D();
        // Default selection: Velachery Trunk
        this.selectDefaultPipe();
      },
      error: (err) => {
        console.error('Failed to load 3D drainage network', err);
      }
    });
  }

  selectDefaultPipe(): void {
    const vel = this.edges.find(e => e.id.includes('VEL-TRUNK')) || this.edges[0];
    if (vel) {
      this.selectEdge(vel);
    }
  }

  selectEdge(edge: DrainageEdge3D): void {
    this.selectedEdge = edge;
    this.fetchInspection(edge.id, this.rainfallIntensity);
  }

  fetchInspection(pipeId: string, rainfall: number): void {
    this.http.get<HydraulicInspection>(`${environment.apiBaseUrl}/api/v1/drainage/hydraulic-inspect?pipe_id=${pipeId}&rainfall_mm_h=${rainfall}`).subscribe({
      next: (res) => {
        this.inspection = res;
      },
      error: (err) => console.error('Inspection failed', err)
    });
  }

  onRainfallChange(): void {
    if (this.selectedEdge) {
      this.fetchInspection(this.selectedEdge.id, this.rainfallIntensity);
    }
  }

  setPresetRainfall(val: number): void {
    this.rainfallIntensity = val;
    this.onRainfallChange();
  }

  mathMin(a: number, b: number): number {
    return Math.min(a, b);
  }

  // --------------------------------------------------------------------------
  // High-Performance 3D Vector Rendering Engine
  // --------------------------------------------------------------------------
  initCanvas3D(): void {
    this.resizeCanvas();
    this.renderLoop();
  }

  @HostListener('window:resize')
  resizeCanvas(): void {
    const canvas = this.canvasRef.nativeElement;
    const container = this.containerRef.nativeElement;
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
  }

  resetCamera(): void {
    this.rotX = 0.55;
    this.rotY = -0.45;
    this.zoom = 1.0;
    this.panX = 0;
    this.panY = 0;
  }

  setTopView(): void {
    this.rotX = 0.05;
    this.rotY = 0.0;
    this.zoom = 0.95;
    this.panX = 0;
    this.panY = 0;
  }

  toggleElevationExaggeration(): void {
    this.zScale = this.zScale === 2.0 ? 4.0 : (this.zScale === 4.0 ? 1.0 : 2.0);
  }

  renderLoop = (): void => {
    this.draw3DScene();
    this.animationFrameId = requestAnimationFrame(this.renderLoop);
  };

  // Convert geographic (lon, lat, elev) to 3D normalized coordinates [-1, 1]
  private projectTo3D(lon: number, lat: number, elev: number) {
    const nx = ((lon - this.bounds.minLon) / (this.bounds.maxLon - this.bounds.minLon) - 0.5) * 2.0;
    const ny = ((lat - this.bounds.minLat) / (this.bounds.maxLat - this.bounds.minLat) - 0.5) * 2.0;
    const nz = ((elev - this.bounds.minElev) / (this.bounds.maxElev - this.bounds.minElev)) * 0.8 * this.zScale;

    // Apply 3D rotation: Pitch (rotX), Yaw (rotY)
    // Rotate around Y axis (yaw)
    const x1 = nx * Math.cos(this.rotY) + ny * Math.sin(this.rotY);
    const y1 = -nx * Math.sin(this.rotY) + ny * Math.cos(this.rotY);
    const z1 = nz;

    // Rotate around X axis (pitch)
    const x2 = x1;
    const y2 = y1 * Math.cos(this.rotX) - z1 * Math.sin(this.rotX);
    const z2 = y1 * Math.sin(this.rotX) + z1 * Math.cos(this.rotX);

    // Orthographic projection to Screen space
    const canvas = this.canvasRef.nativeElement;
    const scale = Math.min(canvas.width, canvas.height) * 0.42 * this.zoom;
    const screenX = canvas.width * 0.5 + x2 * scale + this.panX;
    const screenY = canvas.height * 0.5 - y2 * scale + this.panY;

    return { x: screenX, y: screenY, depth: z2 };
  }

  draw3DScene(): void {
    const canvas = this.canvasRef.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 1. Draw 3D Ground Elevation Wireframe Mesh (Chennai Catchment Floor)
    ctx.strokeStyle = 'rgba(30, 41, 59, 0.45)';
    ctx.lineWidth = 1;
    const gridSteps = 12;
    for (let i = 0; i <= gridSteps; i++) {
      const u = i / gridSteps;
      const lon = this.bounds.minLon + u * (this.bounds.maxLon - this.bounds.minLon);
      const p1 = this.projectTo3D(lon, this.bounds.minLat, 0);
      const p2 = this.projectTo3D(lon, this.bounds.maxLat, 0);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();

      const lat = this.bounds.minLat + u * (this.bounds.maxLat - this.bounds.minLat);
      const q1 = this.projectTo3D(this.bounds.minLon, lat, 0);
      const q2 = this.projectTo3D(this.bounds.maxLon, lat, 0);
      ctx.beginPath();
      ctx.moveTo(q1.x, q1.y);
      ctx.lineTo(q2.x, q2.y);
      ctx.stroke();
    }

    // 2. Draw 3D Drainage Edges (Conduits / Canals)
    const nodeLookup = new Map<string, DrainageNode3D>();
    for (const n of this.nodes) {
      nodeLookup.set(n.id, n);
    }

    for (const edge of this.edges) {
      const src = nodeLookup.get(edge.source_node);
      const tgt = nodeLookup.get(edge.target_node);
      if (!src || !tgt) continue;

      const p1 = this.projectTo3D(src.lon, src.lat, src.invert_elevation_m);
      const p2 = this.projectTo3D(tgt.lon, tgt.lat, tgt.invert_elevation_m);

      const isSelected = this.selectedEdge && this.selectedEdge.id === edge.id;

      // Color based on capacity & slope
      let strokeColor = '#10b981'; // Green / Underflow
      let lineWidth = isSelected ? 6 : Math.max(2.5, edge.width_m * 0.15);

      // Estimate condition based on current rainfall
      const qIn = 0.002778 * edge.runoff_coeff * this.rainfallIntensity * edge.catchment_area_ha;
      const ratio = qIn / edge.manning_capacity_m3s;
      if (ratio > 1.0) {
        strokeColor = '#ef4444'; // Red surcharge
      } else if (ratio >= 0.8) {
        strokeColor = '#f59e0b'; // Amber transition
      }

      if (isSelected) {
        // Glowing halo for selected conduit
        ctx.strokeStyle = 'rgba(245, 158, 11, 0.4)';
        ctx.lineWidth = lineWidth + 6;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }

      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = lineWidth;
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();

      // Flow direction arrow in middle of segment
      const midX = (p1.x + p2.x) * 0.5;
      const midY = (p1.y + p2.y) * 0.5;
      const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x);

      ctx.fillStyle = strokeColor;
      ctx.beginPath();
      ctx.moveTo(midX + 7 * Math.cos(angle), midY + 7 * Math.sin(angle));
      ctx.lineTo(midX - 5 * Math.cos(angle - Math.PI / 6), midY - 5 * Math.sin(angle - Math.PI / 6));
      ctx.lineTo(midX - 5 * Math.cos(angle + Math.PI / 6), midY - 5 * Math.sin(angle + Math.PI / 6));
      ctx.closePath();
      ctx.fill();
    }

    // 3. Draw 3D Drainage Nodes (Spheres with elevation riser stems)
    for (const node of this.nodes) {
      const pInvert = this.projectTo3D(node.lon, node.lat, node.invert_elevation_m);
      const pSurface = this.projectTo3D(node.lon, node.lat, node.surface_elevation_m);

      // Save screen positions for hit-testing click
      node.screenX = pInvert.x;
      node.screenY = pInvert.y;

      // Vertical manhole shaft / riser stem connecting surface to invert
      ctx.strokeStyle = 'rgba(148, 163, 184, 0.35)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([2, 3]);
      ctx.beginPath();
      ctx.moveTo(pSurface.x, pSurface.y);
      ctx.lineTo(pInvert.x, pInvert.y);
      ctx.stroke();
      ctx.setLineDash([]);

      // Surface ground collar
      ctx.fillStyle = 'rgba(100, 116, 139, 0.4)';
      ctx.beginPath();
      ctx.arc(pSurface.x, pSurface.y, 3, 0, Math.PI * 2);
      ctx.fill();

      // Invert Chamber Node Sphere
      const isOutfall = node.type === 'OUTFALL';
      ctx.fillStyle = isOutfall ? '#38bdf8' : '#06b6d4';
      ctx.beginPath();
      ctx.arc(pInvert.x, pInvert.y, isOutfall ? 7 : 5, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Node Label
      ctx.fillStyle = '#e2e8f0';
      ctx.font = '10px Inter, sans-serif';
      ctx.fillText(node.name.split('/')[0].trim(), pInvert.x + 8, pInvert.y + 3);
    }
  }

  // Mouse Interaction (Orbit Rotate & Pan)
  onMouseDown(e: MouseEvent): void {
    this.isDragging = true;
    this.lastMouseX = e.clientX;
    this.lastMouseY = e.clientY;
  }

  onMouseMove(e: MouseEvent): void {
    if (!this.isDragging) return;
    const dx = e.clientX - this.lastMouseX;
    const dy = e.clientY - this.lastMouseY;

    if (e.buttons === 1) { // Left click: Orbit rotate
      this.rotY += dx * 0.006;
      this.rotX += dy * 0.006;
      this.rotX = Math.max(0.01, Math.min(Math.PI * 0.48, this.rotX));
    } else if (e.buttons === 2 || e.buttons === 4) { // Right/Middle click: Pan
      this.panX += dx;
      this.panY += dy;
    }

    this.lastMouseX = e.clientX;
    this.lastMouseY = e.clientY;
  }

  onMouseUp(): void {
    this.isDragging = false;
  }

  onWheel(e: WheelEvent): void {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.08 : 0.92;
    this.zoom = Math.max(0.4, Math.min(3.5, this.zoom * factor));
  }

  onCanvasClick(e: MouseEvent): void {
    const rect = this.canvasRef.nativeElement.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Check click on nodes
    for (const node of this.nodes) {
      if (node.screenX && node.screenY) {
        const dist = Math.hypot(node.screenX - clickX, node.screenY - clickY);
        if (dist <= 10) {
          // Find connected edge
          const connEdge = this.edges.find(ed => ed.source_node === node.id || ed.target_node === node.id);
          if (connEdge) {
            this.selectEdge(connEdge);
          }
          return;
        }
      }
    }

    // Check click on edges (point-to-line segment distance)
    const nodeLookup = new Map(this.nodes.map(n => [n.id, n]));
    let closestEdge: DrainageEdge3D | null = null;
    let minDist = 18;

    for (const edge of this.edges) {
      const s = nodeLookup.get(edge.source_node);
      const t = nodeLookup.get(edge.target_node);
      if (!s || !t) continue;

      const p1 = this.projectTo3D(s.lon, s.lat, s.invert_elevation_m);
      const p2 = this.projectTo3D(t.lon, t.lat, t.invert_elevation_m);

      const d = this.pointToSegmentDistance(clickX, clickY, p1.x, p1.y, p2.x, p2.y);
      if (d < minDist) {
        minDist = d;
        closestEdge = edge;
      }
    }

    if (closestEdge) {
      this.selectEdge(closestEdge);
    }
  }

  private pointToSegmentDistance(px: number, py: number, x1: number, y1: number, x2: number, y2: number): number {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const lenSq = dx * dx + dy * dy;
    if (lenSq === 0) return Math.hypot(px - x1, py - y1);

    const t = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / lenSq));
    const projX = x1 + t * dx;
    const projY = y1 + t * dy;
    return Math.hypot(px - projX, py - projY);
  }
}
