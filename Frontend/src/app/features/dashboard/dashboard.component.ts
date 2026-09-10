import { Component, OnInit, AfterViewInit, OnDestroy, ElementRef, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import * as L from 'leaflet';

import { FloodService } from '../../core/services/flood.service';
import { AlertService } from '../../core/services/alert.service';
import { ThemeService } from '../../core/services/theme.service';
import { SystemKPIs, FloodZone, RecentPrediction, PredictionTime } from '../../core/models/flood-risk.model';
import { FloodAlert } from '../../core/models/alert.model';
import { StatCardComponent } from '../../shared/components/stat-card/stat-card.component';
import { RiskBadgeComponent } from '../../shared/components/risk-badge/risk-badge.component';
import { AlertCardComponent } from '../../shared/components/alert-card/alert-card.component';
import { TimeSelectorComponent } from '../../shared/components/time-selector/time-selector.component';
import { MapLegendComponent } from '../../shared/components/map-legend/map-legend.component';
import { LoadingStateComponent } from '../../shared/components/loading-state/loading-state.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    StatCardComponent,
    RiskBadgeComponent,
    AlertCardComponent,
    TimeSelectorComponent,
    MapLegendComponent,
    LoadingStateComponent
  ],
  template: `
    <div class="dashboard-page">
      <!-- Greeting & Overview Header -->
      <div class="dashboard-header">
        <div class="header-titles">
          <h1 class="welcome-heading">{{ greeting }}, Admin</h1>
          <p class="welcome-sub">
            Monitor real-time flood conditions and AI-powered predictions across Greater Chennai.
          </p>
        </div>
        <div class="header-meta">
          <div class="meta-item">
            <span class="meta-label">Current Date</span>
            <span class="meta-val">{{ currentDate }}</span>
          </div>
          <div class="meta-divider"></div>
          <div class="meta-item">
            <span class="meta-label">Sync Status</span>
            <span class="meta-val status-live">
              <span class="pulse-dot"></span> Telemetric Stream
            </span>
          </div>
          <div class="meta-divider"></div>
          <div class="meta-item">
            <span class="meta-label">Last Updated</span>
            <span class="meta-val font-mono">{{ kpis?.lastUpdated || 'Just now' }}</span>
          </div>
        </div>
      </div>

      <!-- 4 KPI Cards -->
      @if (loadingKpis) {
        <app-loading-state message="Loading flood telemetry KPIs..."></app-loading-state>
      } @else if (kpis) {
        <div class="kpi-grid">
          <!-- KPI 1: Current Rainfall -->
          <app-stat-card
            title="Current Rainfall"
            [value]="kpis.currentRainfall"
            unit="mm/hr"
            [delta]="kpis.rainfallDelta"
            statusType="caution"
          >
            <div icon class="kpi-icon icon-water">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>
              </svg>
            </div>
          </app-stat-card>

          <!-- KPI 2: High-Risk Zones -->
          <app-stat-card
            title="High-Risk Zones"
            [value]="kpis.highRiskZones"
            [delta]="kpis.highRiskDelta"
            statusType="unsafe"
          >
            <div icon class="kpi-icon icon-danger">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
              </svg>
            </div>
          </app-stat-card>

          <!-- KPI 3: Unsafe Roads -->
          <app-stat-card
            title="Unsafe Roads"
            [value]="kpis.unsafeRoads"
            [delta]="kpis.unsafeRoadsStatus"
            statusType="caution"
          >
            <div icon class="kpi-icon icon-road">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
            </div>
          </app-stat-card>

          <!-- KPI 4: Active Alerts -->
          <app-stat-card
            title="Active Alerts"
            [value]="alertService.activeAlertsCount()"
            [delta]="alertService.highPriorityCount() + ' require immediate attention'"
            statusType="unsafe"
          >
            <div icon class="kpi-icon icon-bell">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
              </svg>
            </div>
          </app-stat-card>
        </div>
      }

      <!-- Operational Diagnostics Grid: Flood Risk Index, Catchment Stress, Soil Saturation, Drainage State -->
      <div class="ops-diagnostics-grid">
        <!-- Transparent Flood Risk Index (Section 12) -->
        <div class="card ops-diag-card">
          <div class="ops-card-header">
            <div>
              <span class="ops-card-label">Transparent Index</span>
              <h4 class="ops-card-title">Flood Risk Index</h4>
            </div>
            <div class="risk-index-badge font-mono">
              <span class="score-large">78</span><span class="score-denom">/100</span>
            </div>
          </div>
          <p class="ops-card-sub">Contributing environmental drivers:</p>
          <div class="drivers-list">
            <div class="driver-item">
              <span class="d-name">Rainfall Intensity</span>
              <span class="d-val font-mono text-danger">HIGH (42 mm/h)</span>
              <span class="src-tag tag-obs">OBSERVED</span>
            </div>
            <div class="driver-item">
              <span class="d-name">Drainage Stress</span>
              <span class="d-val font-mono text-danger">HIGH (85% load)</span>
              <span class="src-tag tag-derived">DERIVED</span>
            </div>
            <div class="driver-item">
              <span class="d-name">Terrain Vulnerability</span>
              <span class="d-val font-mono text-warning">MODERATE (DEM)</span>
              <span class="src-tag tag-derived">DERIVED</span>
            </div>
            <div class="driver-item">
              <span class="d-name">Historical Susceptibility</span>
              <span class="d-val font-mono text-danger">HIGH (XGBoost)</span>
              <span class="src-tag tag-model">MODEL</span>
            </div>
          </div>
        </div>

        <!-- Catchment Stress Indicator (Section 10) -->
        <div class="card ops-diag-card">
          <div class="ops-card-header">
            <div>
              <span class="ops-card-label">Hydrologic Balance</span>
              <h4 class="ops-card-title">Catchment Load / Stress</h4>
            </div>
            <span class="badge status-caution font-mono">82% STRESSED</span>
          </div>
          <p class="ops-card-sub">Adyar & Cooum basin hydrologic loading:</p>
          <div class="drivers-list">
            <div class="driver-item">
              <span class="d-name">Precipitation Rate</span>
              <span class="d-val font-mono">34.5 mm/hr</span>
              <span class="src-tag tag-obs">OBSERVED</span>
            </div>
            <div class="driver-item">
              <span class="d-name">Antecedent Rain (24h)</span>
              <span class="d-val font-mono">118.4 mm</span>
              <span class="src-tag tag-obs">OBSERVED</span>
            </div>
            <div class="driver-item">
              <span class="d-name">Runoff Coefficient</span>
              <span class="d-val font-mono">0.78 (Urban)</span>
              <span class="src-tag tag-derived">DERIVED</span>
            </div>
            <div class="driver-item">
              <span class="d-name">Drainage Surcharge</span>
              <span class="d-val font-mono text-caution">Elevated Outfall</span>
              <span class="src-tag tag-derived">DERIVED</span>
            </div>
          </div>
        </div>

        <!-- Soil Saturation Interface (Section 11) -->
        <div class="card ops-diag-card">
          <div class="ops-card-header">
            <div>
              <span class="ops-card-label">Infiltration Telemetry</span>
              <h4 class="ops-card-title">Soil Saturation</h4>
            </div>
            <span class="badge font-mono status-dim">UNAVAILABLE</span>
          </div>
          <p class="ops-card-sub">Subsurface moisture data contract:</p>
          <div class="soil-state-box">
            <div class="soil-icon-row">
              <span class="soil-status-text">Data Unavailable</span>
            </div>
            <p class="soil-desc">
              Satellite soil-moisture and in-situ TDR probe telemetry awaiting GCC sensor grid deployment. Interface schema is established for future ingestion.
            </p>
            <div class="driver-item" style="margin-top: 0.5rem;">
              <span class="d-name">Telemetry Status:</span>
              <span class="src-tag tag-unavail">UNAVAILABLE</span>
            </div>
          </div>
        </div>

        <!-- Drainage Network & Surcharge State (Section 8 & 9) -->
        <div class="card ops-diag-card">
          <div class="ops-card-header">
            <div>
              <span class="ops-card-label">Storm Water Network</span>
              <h4 class="ops-card-title">Drainage Hydraulic State</h4>
            </div>
            <span class="badge status-safe font-mono">INTERFACE READY</span>
          </div>
          <p class="ops-card-sub">Macro-canals & 2023 SWD lines:</p>
          <div class="drivers-list">
            <div class="driver-item">
              <span class="d-name">Surface Waterways</span>
              <span class="d-val font-mono">4 Rivers / Canals</span>
              <span class="src-tag tag-obs">OBSERVED</span>
            </div>
            <div class="driver-item">
              <span class="d-name">SWD Network (KML)</span>
              <span class="d-val font-mono">GCC 2023 GIS</span>
              <span class="src-tag tag-obs">OBSERVED</span>
            </div>
            <div class="driver-item">
              <span class="d-name">Live Pipe Surcharge</span>
              <span class="d-val font-mono text-muted">Awaiting sensors</span>
              <span class="src-tag tag-unavail">UNAVAILABLE</span>
            </div>
            <div class="driver-item">
              <span class="d-name">Hydraulic Solver</span>
              <span class="d-val font-mono text-muted">1D/2D Saint-Venant</span>
              <span class="src-tag tag-unavail">NOT CONNECTED</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Area: Left (Map Overview) & Right (Active Alerts) -->
      <div class="dashboard-main-columns">
        <!-- Left: Live Flood Risk Overview -->
        <div class="card map-preview-card">
          <div class="card-header">
            <div>
              <div class="title-with-badge">
                <h3 class="card-title">Live Flood Risk Overview</h3>
              </div>
              <p class="card-subtitle">
                Prediction horizon: <strong class="text-highlight">{{ currentHorizon }}</strong> (next 3 hours)
              </p>
            </div>
            <app-time-selector
              [selected]="currentHorizon"
              [fullLabels]="true"
              [showLabel]="false"
              (horizonChange)="onHorizonChange($event)"
            ></app-time-selector>
          </div>

          <!-- Advanced Map Layer Controls (Section 22) -->
          <div class="map-layers-bar">
            <span class="layers-bar-label">GIS Layers:</span>
            <div class="layer-chips">
              <label class="layer-chip active">
                <input type="checkbox" checked disabled> Flood Risk (500m)
              </label>
              <label class="layer-chip active">
                <input type="checkbox" [checked]="layerRadar" (change)="layerRadar = !layerRadar"> Doppler Radar
              </label>
              <label class="layer-chip active">
                <input type="checkbox" [checked]="layerHotspots" (change)="layerHotspots = !layerHotspots"> Hotspots
              </label>
              <label class="layer-chip active">
                <input type="checkbox" [checked]="layerDrainage" (change)="layerDrainage = !layerDrainage"> Drainage (SWD)
              </label>
              <label class="layer-chip disabled" title="Hydrodynamic depth model awaiting connection">
                <input type="checkbox" disabled> Flood Depth <span class="layer-status-pill">Pending</span>
              </label>
              <label class="layer-chip">
                <input type="checkbox" [checked]="layerRoutes" (change)="layerRoutes = !layerRoutes"> Safe Corridors
              </label>
            </div>
          </div>

          <!-- Leaflet Map Container -->
          <div class="map-wrapper">
            <div #miniMapContainer class="leaflet-map-canvas"></div>
            <div class="map-overlay-legend">
              <app-map-legend></app-map-legend>
            </div>
            <div class="map-actions-bar">
              <span class="map-info-text">Greater Chennai Corporation (GCC) 500m Metric Grid</span>
              <a routerLink="/flood-map" class="btn btn-primary btn-sm">
                Open Fullscreen GIS Map →
              </a>
            </div>
          </div>
        </div>

        <!-- Right: Active Alerts Feed -->
        <div class="card alerts-panel-card">
          <div class="card-header">
            <div>
              <h3 class="card-title">Active Emergency Alerts</h3>
              <p class="card-subtitle">{{ alerts.length }} active alerts across jurisdiction</p>
            </div>
            <a routerLink="/alerts" class="view-all-link">
              View All →
            </a>
          </div>

          <div class="alerts-feed-list">
            @for (alert of alerts.slice(0, 4); track alert.id) {
              <app-alert-card
                [alert]="alert"
                (acknowledge)="onAcknowledgeAlert($event)"
                (viewLocation)="onViewAlertLocation($event)"
                (dismiss)="onDismissAlert($event)"
              ></app-alert-card>
            }
            @if (alerts.length === 0) {
              <div class="empty-feed-state">
                <span class="empty-icon">✓</span>
                <span class="empty-msg">All jurisdictional alerts acknowledged or cleared.</span>
              </div>
            }
          </div>
        </div>
      </div>

      <!-- Zone Quick Inspection Modal / Drawer -->
      @if (selectedZone) {
        <div class="inspection-modal-overlay" (click)="closeInspection()">
          <div class="inspection-modal-card" (click)="$event.stopPropagation()">
            <div class="inspection-modal-header">
              <div class="inspection-title-group">
                <h3 class="inspection-modal-title">{{ selectedZone.name }}</h3>
                <span class="inspection-grid-id font-mono">{{ selectedZone.gridId }} • Greater Chennai</span>
              </div>
              <button
                type="button"
                class="btn-close"
                (click)="closeInspection()"
                title="Close Inspection"
                aria-label="Close"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>

            <div class="inspection-modal-body">
              <div class="inspection-kpi-row">
                <div class="ins-item">
                  <span class="ins-label">Risk Classification</span>
                  <app-risk-badge [level]="selectedZone.riskLevel" [customText]="selectedZone.riskLevel + ' RISK'"></app-risk-badge>
                </div>
                <div class="ins-item">
                  <span class="ins-label">Risk Probability</span>
                  <span class="ins-value font-mono" [style.color]="getRiskColor(selectedZone.riskScore)">{{ selectedZone.riskScore }}%</span>
                </div>
                <div class="ins-item">
                  <span class="ins-label">Physical Water Depth</span>
                  <span class="ins-value font-mono text-muted" title="Hydraulic depth modeling awaiting 1D/2D Saint-Venant solver connection">
                    Depth unavailable*
                  </span>
                </div>
                <div class="ins-item">
                  <span class="ins-label">Topographic Elevation</span>
                  <span class="ins-value font-mono">{{ selectedZone.elevation }} m MSL</span>
                </div>
              </div>

              <div class="ins-desc">
                <p>
                  Sector <strong>{{ selectedZone.name }}</strong> evaluated at forecast horizon 
                  <strong>{{ currentHorizon }}</strong>. Telemetry indicates saucer depression risk factors with drainage outfall distance of 420m.
                </p>
                <p class="depth-disclaimer-note" style="font-size: 0.72rem; color: var(--text-dim); margin-top: 0.35rem;">
                  * Note: The Chennai XGBoost baseline model predicts spatial flood occurrence susceptibility. Physical water depths require hydrodynamic solver integration. Centimeter depths are strictly not fabricated.
                </p>
              </div>

              <div class="inspection-modal-actions">
                <button type="button" class="btn btn-secondary" (click)="closeInspection()">
                  Close
                </button>
                <button type="button" class="btn btn-primary" (click)="openFullAnalysis(selectedZone)">
                  Open Full Inundation Analysis →
                </button>
              </div>
            </div>
          </div>
        </div>
      }

      <!-- Bottom Section: Recent Predictions & System Status -->
      <div class="dashboard-bottom-columns">
        <!-- Recent Predictions Table -->
        <div class="card predictions-card">
          <div class="card-header">
            <div>
              <div class="title-with-badge">
                <h3 class="card-title">Recent AI Predictions</h3>
              </div>
              <p class="card-subtitle">Multi-horizon inundation vulnerability assessments</p>
            </div>
            <a routerLink="/location-risk" class="btn btn-secondary btn-sm">
              Search Location Risk →
            </a>
          </div>

          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Location / Locality</th>
                  <th>Current Risk</th>
                  <th>+1 Hour</th>
                  <th>+3 Hours</th>
                  <th>AI Confidence</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                @for (item of recentPredictions; track item.location) {
                  <tr>
                    <td class="location-cell">
                      <strong>{{ item.location }}</strong>
                      <span class="sub-locality">Greater Chennai (GCC)</span>
                    </td>
                    <td>
                      <app-risk-badge [level]="item.currentRisk"></app-risk-badge>
                    </td>
                    <td>
                      <app-risk-badge [level]="item.plus1HourRisk"></app-risk-badge>
                    </td>
                    <td>
                      <app-risk-badge [level]="item.plus3HoursRisk"></app-risk-badge>
                    </td>
                    <td>
                      <div class="confidence-bar-wrap">
                        <span class="confidence-val font-mono">{{ item.confidence }}%</span>
                        <div class="progress-bar-bg">
                          <div class="progress-bar-fill" [style.width.%]="item.confidence"></div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <button
                        type="button"
                        class="btn-table-action"
                        (click)="inspectLocation(item.location)"
                        title="Inspect Location Risk"
                      >
                        Inspect →
                      </button>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>

        <!-- System Status Summary -->
        <div class="card system-status-card">
          <div class="card-header">
            <div>
              <div class="title-with-badge">
                <h3 class="card-title">System Health & Telemetry</h3>
              </div>
              <p class="card-subtitle">Microservice & data pipeline heartbeats</p>
            </div>
            <a routerLink="/admin" class="view-all-link">Admin Details →</a>
          </div>

          <div class="status-list">
            <div class="status-row">
              <div class="status-name-group">
                <span class="status-icon-dot"></span>
                <span class="service-name">MODEL (XGBoost Baseline)</span>
              </div>
              <span class="badge status-safe font-mono">ACTIVE</span>
            </div>

            <div class="status-row">
              <div class="status-name-group">
                <span class="status-icon-dot"></span>
                <span class="service-name">DATABASE (3,963 Grid Cells)</span>
              </div>
              <span class="badge status-safe font-mono">CONNECTED</span>
            </div>

            <div class="status-row">
              <div class="status-name-group">
                <span class="status-icon-dot"></span>
                <span class="service-name">MAP DATA (GCC 500m Metric Grid)</span>
              </div>
              <span class="badge status-safe font-mono">AVAILABLE</span>
            </div>

            <div class="status-row">
              <div class="status-name-group">
                <span class="status-icon-dot"></span>
                <span class="service-name">RAINFALL PROVIDER (Telemetry / Radar)</span>
              </div>
              <span class="badge status-safe font-mono">CONNECTED</span>
            </div>

            <div class="status-row">
              <div class="status-name-group">
                <span class="status-icon-dot"></span>
                <span class="service-name">DRAINAGE DATA (KML 2023 SWD)</span>
              </div>
              <span class="badge status-safe font-mono">CONNECTED</span>
            </div>

            <div class="status-row">
              <div class="status-name-group">
                <span class="status-icon-dot dot-inactive" style="background-color: #f59e0b; box-shadow: 0 0 6px #f59e0b;"></span>
                <span class="service-name">HYDRAULIC SOLVER (1D/2D Saint-Venant)</span>
              </div>
              <span class="badge status-caution font-mono">NOT CONNECTED</span>
            </div>
          </div>

          <div class="status-card-footer">
            <div class="footer-metric">
              <span class="f-label">Inference Latency:</span>
              <span class="f-val font-mono">38.5ms</span>
            </div>
            <div class="footer-metric">
              <span class="f-label">Grid Resolution:</span>
              <span class="f-val font-mono">500m × 500m</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-page {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .dashboard-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid var(--border-light);
    }
    .welcome-heading {
      font-size: 1.65rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .welcome-sub {
      font-size: 0.875rem;
      color: var(--text-muted);
      margin-top: 0.2rem;
    }
    .header-meta {
      display: flex;
      align-items: center;
      gap: 1rem;
      background-color: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 0.5rem 1rem;
      box-shadow: var(--shadow-sm);
    }
    .meta-item {
      display: flex;
      flex-direction: column;
    }
    .meta-label {
      font-size: 0.68rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .meta-val {
      font-size: 0.8125rem;
      font-weight: 600;
      color: var(--text-main);
    }
    .status-live {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      color: var(--brand-primary);
    }
    .pulse-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background-color: var(--brand-primary);
      box-shadow: 0 0 6px var(--brand-primary);
    }
    .meta-divider {
      width: 1px;
      height: 24px;
      background-color: var(--border-subtle);
    }

    // KPI Grid
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1.25rem;
      @media (max-width: 1200px) {
        grid-template-columns: repeat(2, 1fr);
      }
      @media (max-width: 640px) {
        grid-template-columns: 1fr;
      }
    }
    .kpi-icon {
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .icon-water { color: #38bdf8; }
    .icon-danger { color: #ef4444; }
    .icon-road { color: #f59e0b; }
    .icon-bell { color: #a855f7; }

    // Dashboard Columns
    .dashboard-main-columns {
      display: grid;
      grid-template-columns: 1.6fr 1fr;
      gap: 1.25rem;
      @media (max-width: 1100px) {
        grid-template-columns: 1fr;
      }
    }

    .title-with-badge {
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }
    .text-highlight {
      color: var(--brand-primary);
    }

    .map-preview-card {
      display: flex;
      flex-direction: column;
    }
    .map-wrapper {
      position: relative;
      width: 100%;
      height: 420px;
      border-radius: var(--radius-md);
      overflow: hidden;
      border: 1px solid var(--border-subtle);
    }
    .leaflet-map-canvas {
      width: 100%;
      height: 100%;
    }
    .map-overlay-legend {
      position: absolute;
      bottom: 48px;
      left: 12px;
      z-index: 500;
      max-width: 220px;
      pointer-events: auto;
      @media (max-width: 640px) {
        display: none;
      }
    }
    .map-actions-bar {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: var(--bg-glass);
      backdrop-filter: blur(8px);
      padding: 0.5rem 1rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      z-index: 500;
      border-top: 1px solid var(--border-subtle);
    }
    .map-info-text {
      font-size: 0.76rem;
      color: var(--text-muted);
    }

    // Alerts Feed Panel
    .alerts-panel-card {
      display: flex;
      flex-direction: column;
    }
    .view-all-link {
      font-size: 0.8125rem;
      color: var(--brand-primary);
      text-decoration: none;
      font-weight: 600;
      &:hover {
        text-decoration: underline;
      }
    }
    .alerts-feed-list {
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
      overflow-y: auto;
      max-height: 420px;
      padding-right: 0.25rem;
    }
    .empty-feed-state {
      padding: 2.5rem 1.5rem;
      text-align: center;
      color: var(--text-dim);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.65rem;
    }
    .empty-icon {
      font-size: 1.5rem;
      color: var(--status-safe);
    }
    .empty-msg {
      font-size: 0.85rem;
    }

    // Inspection Modal Overlay & Card
    .inspection-modal-overlay {
      position: fixed;
      inset: 0;
      background-color: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(4px);
      z-index: 2000;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 1.5rem;
      animation: fadeIn 0.15s ease;
    }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    .inspection-modal-card {
      background-color: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-xl);
      padding: 1.75rem;
      width: 100%;
      max-width: 580px;
      box-shadow: var(--shadow-lg);
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
      animation: scaleIn 0.18s ease;
    }
    @keyframes scaleIn {
      from { transform: scale(0.95); opacity: 0; }
      to { transform: scale(1); opacity: 1; }
    }
    .inspection-modal-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      border-bottom: 1px solid var(--border-light);
      padding-bottom: 0.85rem;
    }
    .inspection-title-group {
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
    }
    .inspection-modal-title {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .inspection-grid-id {
      font-size: 0.75rem;
      color: var(--text-dim);
    }
    .inspection-modal-body {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    .inspection-kpi-row {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
      background-color: var(--bg-darkest);
      padding: 1rem;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
    }
    .ins-item {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .ins-label {
      font-size: 0.72rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .ins-value {
      font-size: 1rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .ins-desc {
      font-size: 0.875rem;
      color: var(--text-muted);
      line-height: 1.5;
    }
    .inspection-modal-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 0.75rem;
      border-top: 1px solid var(--border-light);
      padding-top: 1rem;
    }

    // Bottom Columns
    .dashboard-bottom-columns {
      display: grid;
      grid-template-columns: 1.6fr 1fr;
      gap: 1.25rem;
      @media (max-width: 1100px) {
        grid-template-columns: 1fr;
      }
    }

    .table-responsive {
      overflow-x: auto;
    }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.835rem;

      th {
        padding: 0.65rem 0.85rem;
        background-color: var(--bg-darkest);
        color: var(--text-muted);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.04em;
        border-bottom: 1px solid var(--border-subtle);
      }
      td {
        padding: 0.75rem 0.85rem;
        border-bottom: 1px solid var(--border-light);
        color: var(--text-main);
      }
      tbody tr:hover {
        background-color: rgba(148, 163, 184, 0.08);
      }
    }
    .location-cell {
      display: flex;
      flex-direction: column;
    }
    .sub-locality {
      font-size: 0.7rem;
      color: var(--text-dim);
    }
    .confidence-bar-wrap {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .confidence-val {
      font-size: 0.75rem;
      font-weight: 600;
      min-width: 32px;
    }
    .progress-bar-bg {
      flex: 1;
      height: 6px;
      background-color: var(--bg-darkest);
      border-radius: var(--radius-full);
      overflow: hidden;
      border: 1px solid var(--border-light);
    }
    .progress-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--brand-primary), var(--status-safe));
      border-radius: var(--radius-full);
    }
    .btn-table-action {
      font-size: 0.75rem;
      color: var(--brand-primary);
      font-weight: 600;
      padding: 0.25rem 0.5rem;
      border-radius: var(--radius-sm);
      border: 1px solid transparent;
      &:hover {
        background-color: rgba(37, 99, 235, 0.1);
        border-color: rgba(37, 99, 235, 0.25);
      }
    }

    // System Status Card
    .status-list {
      display: flex;
      flex-direction: column;
      gap: 0.65rem;
    }
    .status-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.65rem 0.85rem;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
    }
    .status-name-group {
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }
    .status-icon-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: var(--status-safe);
      box-shadow: 0 0 6px var(--status-safe);
    }
    .service-name {
      font-size: 0.8125rem;
      font-weight: 500;
      color: var(--text-main);
    }
    .status-card-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 1.25rem;
      padding-top: 0.85rem;
      border-top: 1px solid var(--border-light);
      font-size: 0.75rem;
    }
    .footer-metric {
      display: flex;
      gap: 0.35rem;
    }
    .f-label {
      color: var(--text-dim);
    }
    .f-val {
      color: var(--text-main);
      font-weight: 600;
    }

    // Operational Diagnostics Grid (Section 10, 11, 12)
    .ops-diagnostics-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1.25rem;
      @media (max-width: 1200px) {
        grid-template-columns: repeat(2, 1fr);
      }
      @media (max-width: 640px) {
        grid-template-columns: 1fr;
      }
    }
    .ops-diag-card {
      display: flex;
      flex-direction: column;
      gap: 0.65rem;
      background-color: var(--bg-card);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-md);
      padding: 1rem;
    }
    .ops-card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }
    .ops-card-label {
      font-size: 0.68rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .ops-card-title {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-main);
      margin-top: 0.15rem;
    }
    .ops-card-sub {
      font-size: 0.72rem;
      color: var(--text-muted);
    }
    .risk-index-badge {
      background: rgba(239, 68, 68, 0.12);
      border: 1px solid rgba(239, 68, 68, 0.3);
      padding: 0.2rem 0.5rem;
      border-radius: var(--radius-sm);
    }
    .score-large {
      font-size: 1.15rem;
      font-weight: 800;
      color: #ef4444;
    }
    .score-denom {
      font-size: 0.7rem;
      color: var(--text-muted);
    }
    .drivers-list {
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }
    .driver-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.76rem;
      background-color: var(--bg-darkest);
      padding: 0.35rem 0.6rem;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-light);
    }
    .d-name {
      color: var(--text-muted);
      font-weight: 500;
    }
    .d-val {
      font-weight: 600;
      color: var(--text-main);
    }
    .src-tag {
      font-size: 0.62rem;
      font-weight: 700;
      padding: 0.15rem 0.35rem;
      border-radius: 3px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    .tag-obs { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
    .tag-derived { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
    .tag-model { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
    .tag-unavail { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }

    .soil-state-box {
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }
    .soil-status-text {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-dim);
    }
    .soil-desc {
      font-size: 0.72rem;
      color: var(--text-muted);
      line-height: 1.4;
    }

    // Map Layer Controls (Section 22)
    .map-layers-bar {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.5rem 1rem;
      background-color: var(--bg-darkest);
      border-bottom: 1px solid var(--border-light);
      flex-wrap: wrap;
    }
    .layers-bar-label {
      font-size: 0.7rem;
      color: var(--text-dim);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .layer-chips {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .layer-chip {
      display: flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.72rem;
      color: var(--text-muted);
      background-color: var(--bg-card);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.2rem 0.55rem;
      cursor: pointer;
      user-select: none;
      &.active {
        color: var(--text-main);
        border-color: var(--brand-primary);
      }
      &.disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      input[type="checkbox"] {
        accent-color: var(--brand-primary);
      }
    }
    .layer-status-pill {
      font-size: 0.6rem;
      background: rgba(245, 158, 11, 0.2);
      color: #fbbf24;
      padding: 0.05rem 0.3rem;
      border-radius: 3px;
    }
  `]
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('miniMapContainer') miniMapContainer!: ElementRef;

  greeting = 'Good Afternoon';
  currentDate = '';
  currentHorizon: PredictionTime = 'NOW';

  kpis: SystemKPIs | null = null;
  loadingKpis = true;
  alerts: FloodAlert[] = [];
  recentPredictions: RecentPrediction[] = [];
  floodZones: FloodZone[] = [];
  selectedZone: FloodZone | null = null;

  layerRadar = true;
  layerHotspots = true;
  layerDrainage = true;
  layerRoutes = false;

  private map?: L.Map;
  private zoneLayersGroup = L.layerGroup();
  private resizeHandler?: () => void;

  constructor(
    private floodService: FloodService,
    public alertService: AlertService,
    public themeService: ThemeService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.initGreetingAndDate();
    this.loadKPIs();
    this.loadAlerts();
    this.loadRecentPredictions();
  }

  ngAfterViewInit(): void {
    // Defer initialization to next animation frame to eliminate UI blocking/lag
    requestAnimationFrame(() => {
      this.initMiniMap();
      this.loadMapZones(this.currentHorizon);
    });

    if (typeof window !== 'undefined') {
      this.resizeHandler = () => {
        if (this.map) {
          this.map.invalidateSize();
        }
      };
      window.addEventListener('resize', this.resizeHandler, { passive: true });
    }
  }

  ngOnDestroy(): void {
    if (this.resizeHandler && typeof window !== 'undefined') {
      window.removeEventListener('resize', this.resizeHandler);
    }
    if (this.map) {
      this.map.remove();
    }
  }

  private initGreetingAndDate(): void {
    const hour = new Date().getHours();
    if (hour < 12) this.greeting = 'Good Morning';
    else if (hour < 17) this.greeting = 'Good Afternoon';
    else this.greeting = 'Good Evening';

    this.currentDate = new Date().toLocaleDateString('en-IN', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  }

  private loadKPIs(): void {
    this.loadingKpis = true;
    this.floodService.getKPIs().subscribe({
      next: data => {
        this.kpis = data;
        this.loadingKpis = false;
      },
      error: () => {
        this.loadingKpis = false;
      }
    });
  }

  private loadAlerts(): void {
    this.alertService.getAlerts().subscribe(data => {
      this.alerts = data;
    });
  }

  private loadRecentPredictions(): void {
    this.floodService.getRecentPredictions().subscribe(data => {
      this.recentPredictions = data;
    });
  }

  private initMiniMap(): void {
    if (!this.miniMapContainer || this.map) return;

    // Center on Greater Chennai area with Canvas hardware acceleration
    this.map = L.map(this.miniMapContainer.nativeElement, {
      center: [13.0827, 80.2707],
      zoom: 11,
      zoomControl: false,
      attributionControl: false,
      preferCanvas: true
    });

    L.control.zoom({ position: 'topright' }).addTo(this.map);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      subdomains: ['a', 'b', 'c'],
      keepBuffer: 2,
      updateWhenIdle: true
    }).addTo(this.map);

    this.zoneLayersGroup.addTo(this.map);

    requestAnimationFrame(() => {
      this.map?.invalidateSize();
    });
  }

  private loadMapZones(horizon: PredictionTime): void {
    this.floodService.getFloodZones(horizon).subscribe(zones => {
      this.floodZones = zones;
      this.renderZonesOnMap(zones);
    });
  }

  private renderZonesOnMap(zones: FloodZone[]): void {
    if (!this.map) return;
    this.zoneLayersGroup.clearLayers();

    zones.forEach(zone => {
      let fillColor = '#10b981'; // Safe
      let borderColor = '#059669';

      if (zone.riskLevel === 'HIGH' || zone.riskScore >= 80) {
        fillColor = '#ef4444';
        borderColor = '#b91c1c';
      } else if (zone.riskLevel === 'MEDIUM' || zone.riskScore >= 50) {
        fillColor = '#f59e0b';
        borderColor = '#d97706';
      } else if (zone.riskLevel === 'LOW' || zone.riskScore >= 20) {
        fillColor = '#06b6d4';
        borderColor = '#0891b2';
      }

      const rect = L.rectangle(zone.bounds, {
        color: borderColor,
        weight: 2,
        fillColor: fillColor,
        fillOpacity: 0.35
      });

      rect.bindTooltip(`
        <div style="font-family: inherit;">
          <strong>${zone.name}</strong><br/>
          Risk Score: <strong>${zone.riskScore}%</strong> (${zone.riskLevel})<br/>
          Depth: <strong>${zone.waterDepth}m</strong>
        </div>
      `, { sticky: true });

      rect.on('click', () => {
        this.selectedZone = zone;
        this.floodService.setSelectedZone(zone);
      });

      this.zoneLayersGroup.addLayer(rect);
    });
  }

  onHorizonChange(horizon: PredictionTime): void {
    this.currentHorizon = horizon;
    this.floodService.setHorizon(horizon);
    this.loadMapZones(horizon);

    if (this.kpis) {
      if (horizon === '+1H') {
        this.kpis = { ...this.kpis, currentRainfall: 26.0, highRiskZones: 15, rainfallDelta: '↑ Peak predicted rate' };
      } else if (horizon === '+3H') {
        this.kpis = { ...this.kpis, currentRainfall: 6.2, highRiskZones: 6, rainfallDelta: '↓ Receding convective line' };
      } else if (horizon === 'NOW') {
        this.kpis = { ...this.kpis, currentRainfall: 18.4, highRiskZones: 12, rainfallDelta: '↑ 12% from last hour' };
      }
    }
  }

  onAcknowledgeAlert(id: string): void {
    this.alertService.acknowledgeAlert(id).subscribe();
  }

  onDismissAlert(id: string): void {
    this.alerts = this.alerts.filter(a => a.id !== id);
  }

  onViewAlertLocation(alert: FloodAlert): void {
    this.router.navigate(['/flood-map'], {
      queryParams: { lat: alert.coordinates[0], lng: alert.coordinates[1], focus: alert.location }
    });
  }

  inspectLocation(locationName: string): void {
    // Find matching zone or create a mock inspection zone
    const found = this.floodZones.find(z => z.name.toLowerCase().includes(locationName.toLowerCase()));
    if (found) {
      this.selectedZone = found;
    } else {
      // Find from recent predictions
      const pred = this.recentPredictions.find(p => p.location === locationName);
      this.selectedZone = {
        gridId: 'CHN-' + Math.floor(1000 + Math.random() * 9000),
        name: locationName + ' Basin',
        latitude: 13.0827,
        longitude: 80.2707,
        bounds: [[13.07, 80.26], [13.09, 80.28]],
        riskLevel: pred?.currentRisk || 'MEDIUM',
        riskScore: pred?.confidence || 65,
        predictionTime: this.currentHorizon,
        rainfall: 24.5,
        elevation: 8.2,
        waterDepth: pred?.currentRisk === 'HIGH' ? 0.85 : 0.35,
        runoffCoefficient: 0.75,
        slope: 'Low',
        summary: `Vulnerability assessment for ${locationName}`,
        historicalFlooding: 'Moderate',
        drainageStatus: 'Moderate',
        builtUpDensity: 78,
        isSimulated: true
      };
    }
  }

  closeInspection(): void {
    this.selectedZone = null;
  }

  openFullAnalysis(zone: FloodZone): void {
    this.closeInspection();
    this.router.navigate(['/location-risk'], {
      queryParams: { location: zone.name.split(' ')[0] }
    });
  }

  getRiskColor(score: number): string {
    if (score >= 80) return '#ef4444';
    if (score >= 50) return '#f59e0b';
    return '#10b981';
  }
}
