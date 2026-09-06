import { Component, OnInit, AfterViewInit, OnDestroy, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import * as L from 'leaflet';

import { FloodService } from '../../core/services/flood.service';
import { AlertService } from '../../core/services/alert.service';
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
            Monitor simulated flood conditions and AI-powered prototype predictions across the selected urban area.
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
              <span class="pulse-dot"></span> Simulated Stream
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

      <!-- Main Area: Left (Map Overview) & Right (Active Alerts) -->
      <div class="dashboard-main-columns">
        <!-- Left: Live Flood Risk Overview -->
        <div class="card map-preview-card">
          <div class="card-header">
            <div>
              <div class="title-with-badge">
                <h3 class="card-title">Live Flood Risk Overview</h3>
                <span class="badge-prototype">Simulated AI Nowcast</span>
              </div>
              <p class="card-subtitle">
                Prediction horizon: <strong class="text-highlight">{{ currentHorizon }}</strong> (simulated next 3 hours)
              </p>
            </div>
            <app-time-selector
              [selected]="currentHorizon"
              [fullLabels]="true"
              [showLabel]="false"
              (horizonChange)="onHorizonChange($event)"
            ></app-time-selector>
          </div>

          <!-- Leaflet Map Container -->
          <div class="map-wrapper">
            <div #miniMapContainer class="leaflet-map-canvas"></div>
            <div class="map-overlay-legend">
              <app-map-legend></app-map-legend>
            </div>
            <div class="map-actions-bar">
              <span class="map-info-text">Showing Greater Mumbai BMC Grid Sectors (500m Resolution)</span>
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
              <p class="card-subtitle">{{ alerts.length }} alerts logged across jurisdiction</p>
            </div>
            <a routerLink="/alerts" class="view-all-link">
              View All Alerts →
            </a>
          </div>

          <div class="alerts-feed-list">
            @for (alert of alerts.slice(0, 4); track alert.id) {
              <app-alert-card
                [alert]="alert"
                (acknowledge)="onAcknowledgeAlert($event)"
                (viewLocation)="onViewAlertLocation($event)"
              ></app-alert-card>
            }
          </div>
        </div>
      </div>

      <!-- Bottom Section: Recent Predictions & System Status -->
      <div class="dashboard-bottom-columns">
        <!-- Recent Predictions Table -->
        <div class="card predictions-card">
          <div class="card-header">
            <div>
              <div class="title-with-badge">
                <h3 class="card-title">Recent AI Predictions</h3>
                <span class="badge-prototype">Simulated Inference</span>
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
                      <span class="sub-locality">Greater Mumbai (BMC)</span>
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
                        (click)="navigateToLocation(item.location)"
                        title="View Detailed Analysis"
                      >
                        Analyze →
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
                <span class="badge-prototype">Phase 1 Emulation</span>
              </div>
              <p class="card-subtitle">Microservice & data pipeline heartbeats</p>
            </div>
            <a routerLink="/admin" class="view-all-link">Admin Details →</a>
          </div>

          <div class="status-list">
            <div class="status-row">
              <div class="status-name-group">
                <span class="status-icon-dot"></span>
                <span class="service-name">Rainfall Doppler Radar</span>
              </div>
              <span class="badge status-safe font-mono">OPERATIONAL</span>
            </div>

            <div class="status-row">
              <div class="status-name-group">
                <span class="status-icon-dot"></span>
                <span class="service-name">GIS Dem Processing</span>
              </div>
              <span class="badge status-safe font-mono">OPERATIONAL</span>
            </div>

            <div class="status-row">
              <div class="status-name-group">
                <span class="status-icon-dot"></span>
                <span class="service-name">ML Prediction Engine (XGBoost)</span>
              </div>
              <span class="badge status-safe font-mono">OPERATIONAL</span>
            </div>

            <div class="status-row">
              <div class="status-name-group">
                <span class="status-icon-dot"></span>
                <span class="service-name">Flood-Aware Routing Engine</span>
              </div>
              <span class="badge status-safe font-mono">OPERATIONAL</span>
            </div>

            <div class="status-row">
              <div class="status-name-group">
                <span class="status-icon-dot"></span>
                <span class="service-name">PostGIS Spatial Database</span>
              </div>
              <span class="badge status-safe font-mono">OPERATIONAL</span>
            </div>
          </div>

          <div class="status-card-footer">
            <div class="footer-metric">
              <span class="f-label">Inference Latency:</span>
              <span class="f-val font-mono">42ms (Simulated)</span>
            </div>
            <div class="footer-metric">
              <span class="f-label">Grid Resolution:</span>
              <span class="f-val font-mono">500m x 500m</span>
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
      color: #38bdf8;
    }
    .pulse-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background-color: #38bdf8;
      box-shadow: 0 0 6px #38bdf8;
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
      background: rgba(15, 23, 42, 0.9);
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
        background-color: rgba(255, 255, 255, 0.02);
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
    }
    .progress-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, #3b82f6, #10b981);
      border-radius: var(--radius-full);
    }
    .btn-table-action {
      font-size: 0.75rem;
      color: var(--brand-primary);
      font-weight: 600;
      padding: 0.25rem 0.5rem;
      border-radius: var(--radius-sm);
      &:hover {
        background-color: rgba(59, 130, 246, 0.1);
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

  private map?: L.Map;
  private zoneLayersGroup = L.layerGroup();

  constructor(
    private floodService: FloodService,
    public alertService: AlertService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.initGreetingAndDate();
    this.loadKPIs();
    this.loadAlerts();
    this.loadRecentPredictions();
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.initMiniMap();
      this.loadMapZones(this.currentHorizon);
    }, 100);
  }

  ngOnDestroy(): void {
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
    if (!this.miniMapContainer) return;

    // Center on Greater Mumbai (BMC) area (19.0760° N, 72.8777° E)
    this.map = L.map(this.miniMapContainer.nativeElement, {
      center: [19.0760, 72.8777],
      zoom: 11,
      zoomControl: false,
      attributionControl: false
    });

    L.control.zoom({ position: 'topright' }).addTo(this.map);

    // Dark-themed tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      subdomains: ['a', 'b', 'c']
    }).addTo(this.map);

    this.zoneLayersGroup.addTo(this.map);
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
          Simulated Depth: <strong>${zone.waterDepth}m</strong>
        </div>
      `, { sticky: true });

      rect.on('click', () => {
        this.floodService.setSelectedZone(zone);
        this.router.navigate(['/location-risk'], {
          queryParams: { location: zone.name.split(' ')[0] }
        });
      });

      this.zoneLayersGroup.addLayer(rect);
    });
  }

  onHorizonChange(horizon: PredictionTime): void {
    this.currentHorizon = horizon;
    this.floodService.setHorizon(horizon);
    this.loadMapZones(horizon);

    // Update KPI rainfall and high risk count dynamically according to horizon
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

  onViewAlertLocation(alert: FloodAlert): void {
    this.router.navigate(['/flood-map'], {
      queryParams: { lat: alert.coordinates[0], lng: alert.coordinates[1], focus: alert.location }
    });
  }

  navigateToLocation(location: string): void {
    this.router.navigate(['/location-risk'], {
      queryParams: { location }
    });
  }
}
