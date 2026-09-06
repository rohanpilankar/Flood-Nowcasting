import { Component, OnInit, AfterViewInit, OnDestroy, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import * as L from 'leaflet';

import { FloodService } from '../../core/services/flood.service';
import { FloodZone, PredictionTime } from '../../core/models/flood-risk.model';
import { TimeSelectorComponent } from '../../shared/components/time-selector/time-selector.component';
import { RiskBadgeComponent } from '../../shared/components/risk-badge/risk-badge.component';
import { MapLegendComponent } from '../../shared/components/map-legend/map-legend.component';
import { PrototypeNoticeComponent } from '../../shared/components/prototype-notice/prototype-notice.component';

@Component({
  selector: 'app-flood-map',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TimeSelectorComponent,
    RiskBadgeComponent,
    MapLegendComponent,
    PrototypeNoticeComponent
  ],
  template: `
    <div class="flood-map-page">
      <!-- Top Control Bar -->
      <div class="map-control-bar card">
        <div class="control-header-col">
          <div class="title-row">
            <h2 class="page-title">Flood Risk Map</h2>
            <span class="badge-prototype">GIS Ingestion Layer</span>
          </div>
          <p class="page-sub">Real-time and AI-predicted flood risk monitoring across urban catchments</p>
        </div>

        <div class="control-actions-row">
          <!-- Search input -->
          <div class="search-box">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input
              type="text"
              placeholder="Search locality (e.g. Katraj, Baner)..."
              [(ngModel)]="searchQuery"
              (keyup.enter)="searchLocality()"
              class="search-input"
            />
            @if (searchQuery) {
              <button type="button" class="btn-clear" (click)="clearSearch()">✕</button>
            }
          </div>

          <!-- Prediction Time Selector -->
          <app-time-selector
            [selected]="currentHorizon"
            [showLabel]="false"
            (horizonChange)="onHorizonChange($event)"
          ></app-time-selector>

          <!-- Layer Toggles -->
          <div class="layer-toggle-group">
            <button
              type="button"
              class="layer-toggle-btn"
              [class.active]="layers.floodRisk"
              (click)="toggleLayer('floodRisk')"
              title="Toggle Flood Risk Zones"
            >
              <span class="dot-layer" [style.background-color]="layers.floodRisk ? '#ef4444' : '#64748b'"></span>
              Flood Risk
            </button>

            <button
              type="button"
              class="layer-toggle-btn"
              [class.active]="layers.roads"
              (click)="toggleLayer('roads')"
              title="Toggle Road Network"
            >
              <span class="dot-layer" [style.background-color]="layers.roads ? '#f59e0b' : '#64748b'"></span>
              Roads
            </button>

            <button
              type="button"
              class="layer-toggle-btn"
              [class.active]="layers.rainfall"
              (click)="toggleLayer('rainfall')"
              title="Toggle Simulated Radar"
            >
              <span class="dot-layer" [style.background-color]="layers.rainfall ? '#38bdf8' : '#64748b'"></span>
              Rainfall
            </button>

            <button
              type="button"
              class="layer-toggle-btn"
              [class.active]="layers.drainage"
              (click)="toggleLayer('drainage')"
              title="Toggle Stormwater Culverts"
            >
              <span class="dot-layer" [style.background-color]="layers.drainage ? '#10b981' : '#64748b'"></span>
              Drainage
            </button>
          </div>
        </div>
      </div>

      <!-- Main GIS Map Viewport -->
      <div class="gis-map-container">
        <div #mapCanvas class="leaflet-full-canvas"></div>

        <!-- Float Map Legend -->
        <div class="floating-legend">
          <app-map-legend></app-map-legend>
        </div>

        <!-- Floating Notice -->
        <div class="floating-notice">
          <app-prototype-notice [expanded]="false"></app-prototype-notice>
        </div>

        <!-- Zone Detail Side Drawer -->
        @if (selectedZone) {
          <div class="zone-detail-drawer animate-slide-in">
            <div class="drawer-header">
              <div>
                <span class="drawer-grid-id font-mono">{{ selectedZone.gridId }}</span>
                <h3 class="drawer-zone-name">{{ selectedZone.name }}</h3>
              </div>
              <button type="button" class="btn-close-drawer" (click)="closeDrawer()">✕</button>
            </div>

            <div class="drawer-risk-banner">
              <app-risk-badge [level]="selectedZone.riskLevel"></app-risk-badge>
              <span class="drawer-risk-score font-mono">
                Prototype Score: <strong>{{ selectedZone.riskScore }}%</strong>
              </span>
            </div>

            <div class="drawer-summary">
              <p>{{ selectedZone.summary }}</p>
            </div>

            <div class="drawer-metrics-grid">
              <div class="metric-card">
                <span class="m-label">Simulated Rainfall</span>
                <span class="m-val font-mono">{{ selectedZone.rainfall }} mm/hr</span>
              </div>
              <div class="metric-card">
                <span class="m-label">Prototype Elevation</span>
                <span class="m-val font-mono">{{ selectedZone.elevation }} m</span>
              </div>
              <div class="metric-card">
                <span class="m-label">Runoff Coeff (C)</span>
                <span class="m-val font-mono">{{ selectedZone.runoffCoefficient }}</span>
              </div>
              <div class="metric-card">
                <span class="m-label">Simulated Water Depth</span>
                <span class="m-val font-mono">{{ selectedZone.waterDepth }} m</span>
              </div>
              <div class="metric-card">
                <span class="m-label">Topographic Slope</span>
                <span class="m-val">{{ selectedZone.slope }}</span>
              </div>
              <div class="metric-card">
                <span class="m-label">Drainage Network</span>
                <span class="m-val" [class.text-danger]="selectedZone.drainageStatus === 'Critical'">
                  {{ selectedZone.drainageStatus }}
                </span>
              </div>
            </div>

            <div class="drawer-prediction-notice">
              <span class="pred-title">AI Nowcast Prediction ({{ currentHorizon }}):</span>
              <p class="pred-text">
                @if (selectedZone.riskScore >= 80) {
                  High probability of severe water accumulation exceeding 0.4m depth within the next hour.
                } @else if (selectedZone.riskScore >= 50) {
                  Moderate runoff ponding expected along curb inverts; light vehicles advise caution.
                } @else {
                  Normal stormwater discharge rates; zero critical roadway inundation expected.
                }
              </p>
            </div>

            <div class="drawer-actions">
              <button
                type="button"
                class="btn btn-primary"
                style="width: 100%;"
                (click)="navigateToDetailedAnalysis(selectedZone)"
              >
                View Detailed Location Analysis →
              </button>
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .flood-map-page {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      height: calc(100vh - var(--header-height) - 3rem);
    }

    .map-control-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
      padding: 0.85rem 1.25rem;
    }
    .page-title {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .page-sub {
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-top: 0.1rem;
    }
    .title-row {
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }
    .control-actions-row {
      display: flex;
      align-items: center;
      gap: 0.85rem;
      flex-wrap: wrap;
    }

    .search-box {
      position: relative;
      display: flex;
      align-items: center;
      width: 240px;
    }
    .search-icon {
      position: absolute;
      left: 0.65rem;
      color: var(--text-dim);
      pointer-events: none;
    }
    .search-input {
      width: 100%;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 0.4rem 1.8rem 0.4rem 2rem;
      color: var(--text-main);
      font-size: 0.8125rem;
      outline: none;
      transition: border-color var(--transition-fast);

      &:focus {
        border-color: var(--brand-primary);
      }
    }
    .btn-clear {
      position: absolute;
      right: 0.6rem;
      color: var(--text-dim);
      font-size: 0.75rem;
      &:hover {
        color: var(--text-main);
      }
    }

    .layer-toggle-group {
      display: flex;
      align-items: center;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 2px;
      gap: 2px;
      @media (max-width: 768px) {
        flex-wrap: wrap;
      }
    }
    .layer-toggle-btn {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.35rem 0.65rem;
      font-size: 0.74rem;
      font-weight: 600;
      color: var(--text-muted);
      border-radius: var(--radius-sm);
      transition: all var(--transition-fast);

      &:hover {
        color: var(--text-main);
      }
      &.active {
        background-color: var(--bg-card);
        color: var(--text-main);
      }
    }
    .dot-layer {
      width: 7px;
      height: 7px;
      border-radius: 50%;
    }

    // GIS Map Canvas
    .gis-map-container {
      position: relative;
      flex: 1;
      border-radius: var(--radius-lg);
      overflow: hidden;
      border: 1px solid var(--border-subtle);
      min-height: 480px;
    }
    .leaflet-full-canvas {
      width: 100%;
      height: 100%;
    }

    .floating-legend {
      position: absolute;
      bottom: 20px;
      left: 20px;
      z-index: 500;
      max-width: 240px;
      @media (max-width: 640px) {
        display: none;
      }
    }
    .floating-notice {
      position: absolute;
      top: 20px;
      left: 20px;
      z-index: 500;
      @media (max-width: 900px) {
        display: none;
      }
    }

    // Zone Detail Drawer
    .zone-detail-drawer {
      position: absolute;
      top: 15px;
      right: 15px;
      bottom: 15px;
      width: 360px;
      background-color: rgba(15, 23, 42, 0.94);
      backdrop-filter: blur(14px);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 1.25rem;
      z-index: 1000;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
      overflow-y: auto;
      box-shadow: var(--shadow-lg);

      @media (max-width: 640px) {
        width: calc(100% - 30px);
      }
    }
    .drawer-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
    }
    .drawer-grid-id {
      font-size: 0.72rem;
      color: #93c5fd;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .drawer-zone-name {
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text-main);
      margin-top: 0.15rem;
    }
    .btn-close-drawer {
      color: var(--text-muted);
      font-size: 1.1rem;
      padding: 0.2rem 0.4rem;
      border-radius: var(--radius-sm);
      &:hover {
        color: var(--text-main);
        background-color: var(--bg-card);
      }
    }
    .drawer-risk-banner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.5rem 0.75rem;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
    }
    .drawer-risk-score {
      font-size: 0.8125rem;
      color: var(--text-muted);
      strong {
        color: var(--text-main);
      }
    }
    .drawer-summary {
      font-size: 0.825rem;
      color: var(--text-muted);
      line-height: 1.45;
    }
    .drawer-metrics-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.5rem;
    }
    .metric-card {
      background-color: var(--bg-card);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.5rem 0.65rem;
      display: flex;
      flex-direction: column;
    }
    .m-label {
      font-size: 0.68rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    .m-val {
      font-size: 0.875rem;
      font-weight: 600;
      color: var(--text-main);
      margin-top: 0.15rem;
    }
    .text-danger {
      color: var(--status-critical);
    }
    .drawer-prediction-notice {
      background-color: rgba(59, 130, 246, 0.08);
      border-left: 3px solid var(--brand-primary);
      border-radius: var(--radius-sm);
      padding: 0.65rem;
      font-size: 0.8rem;
      line-height: 1.4;
    }
    .pred-title {
      font-weight: 600;
      color: #93c5fd;
      display: block;
      margin-bottom: 0.25rem;
    }
    .pred-text {
      color: var(--text-main);
      margin: 0;
    }
    .drawer-actions {
      margin-top: auto;
      padding-top: 0.5rem;
    }
  `]
})
export class FloodMapComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('mapCanvas') mapCanvas!: ElementRef;

  currentHorizon: PredictionTime = 'NOW';
  searchQuery = '';
  selectedZone: FloodZone | null = null;
  floodZones: FloodZone[] = [];

  layers = {
    floodRisk: true,
    roads: true,
    rainfall: true,
    drainage: true
  };

  private map?: L.Map;
  private riskGroup = L.layerGroup();
  private roadGroup = L.layerGroup();
  private drainageGroup = L.layerGroup();
  private rainfallGroup = L.layerGroup();

  constructor(
    private floodService: FloodService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.currentHorizon = this.floodService.selectedHorizon();
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.initMap();
      this.loadZonesAndLayers(this.currentHorizon);
      this.checkRouteQueryParams();
    }, 120);
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
  }

  private initMap(): void {
    if (!this.mapCanvas) return;

    this.map = L.map(this.mapCanvas.nativeElement, {
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

    this.riskGroup.addTo(this.map);
    this.roadGroup.addTo(this.map);
    this.drainageGroup.addTo(this.map);
    this.rainfallGroup.addTo(this.map);
  }

  private loadZonesAndLayers(horizon: PredictionTime): void {
    this.floodService.getFloodZones(horizon).subscribe(zones => {
      this.floodZones = zones;
      this.renderFloodRiskLayer(zones);
      this.renderRoadsLayer();
      this.renderDrainageLayer();
      this.renderRainfallLayer();
    });
  }

  private renderFloodRiskLayer(zones: FloodZone[]): void {
    this.riskGroup.clearLayers();
    if (!this.layers.floodRisk) return;

    zones.forEach(zone => {
      let fillColor = '#10b981';
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
        fillOpacity: 0.38
      });

      rect.bindTooltip(`
        <div style="font-family: inherit;">
          <strong style="color: #60a5fa;">${zone.gridId}</strong>: ${zone.name}<br/>
          Risk Score: <strong>${zone.riskScore}%</strong> (${zone.riskLevel})<br/>
          Simulated Depth: <strong>${zone.waterDepth}m</strong><br/>
          <em>Click for detailed telemetry</em>
        </div>
      `, { sticky: true });

      rect.on('click', () => {
        this.selectedZone = zone;
        this.floodService.setSelectedZone(zone);
      });

      this.riskGroup.addLayer(rect);
    });
  }

  private renderRoadsLayer(): void {
    this.roadGroup.clearLayers();
    if (!this.layers.roads) return;

    // Mumbai Arterial Road Network
    const roadLines = [
      { coords: [[19.010, 72.841], [19.013, 72.843], [19.016, 72.845]], status: 'UNSAFE', label: 'Dr. Ambedkar Road (Hindmata Basin Choke)' },
      { coords: [[19.081, 72.840], [19.083, 72.841], [19.085, 72.842]], status: 'BLOCKED', label: 'Milan Subway (-3.0m Underpass Inundation)' },
      { coords: [[19.118, 72.843], [19.120, 72.844], [19.122, 72.845]], status: 'BLOCKED', label: 'Andheri Subway (Mogra Nallah Choke)' },
      { coords: [[19.065, 72.874], [19.068, 72.876], [19.072, 72.879]], status: 'CAUTION', label: 'LBS Marg (Kurla Kamani SCLR Link)' },
      { coords: [[18.910, 72.820], [18.960, 72.835], [19.020, 72.850], [19.065, 72.855], [19.120, 72.848], [19.230, 72.855]], status: 'SAFE', label: 'Western Express Highway (Elevated Flyover Corridor)' }
    ];

    roadLines.forEach(r => {
      const color = r.status === 'BLOCKED' || r.status === 'UNSAFE' ? '#ef4444' : r.status === 'CAUTION' ? '#f59e0b' : '#10b981';
      const polyline = L.polyline(r.coords as any, {
        color,
        weight: 4,
        dashArray: r.status === 'BLOCKED' || r.status === 'UNSAFE' ? '6, 6' : undefined,
        opacity: 0.85
      });
      polyline.bindTooltip(`${r.label} — Status: ${r.status}`);
      this.roadGroup.addLayer(polyline);
    });
  }

  private renderDrainageLayer(): void {
    this.drainageGroup.clearLayers();
    if (!this.layers.drainage) return;

    // Mumbai Mithi River, Poisar & Mahim Creek Drainage System
    const drainageLines = [
      [[19.128, 72.905], [19.095, 72.885], [19.068, 72.868], [19.045, 72.845]],
      [[19.210, 72.865], [19.200, 72.845], [19.195, 72.825]],
      [[19.160, 72.860], [19.150, 72.840], [19.145, 72.825]]
    ];

    drainageLines.forEach(coords => {
      const line = L.polyline(coords as any, {
        color: '#06b6d4',
        weight: 3,
        opacity: 0.7
      });
      line.bindTooltip('Mithi River / Municipal Stormwater Channel (BMC GIS)');
      this.drainageGroup.addLayer(line);
    });
  }

  private renderRainfallLayer(): void {
    this.rainfallGroup.clearLayers();
    if (!this.layers.rainfall) return;

    // Real BMC AWS / IMD Radar Cells
    const radarCells = [
      { center: [19.0832, 72.8415], radius: 3200, color: '#ef4444', label: 'Santacruz AWS Heavy Cell (54.0 mm/hr)' },
      { center: [19.0125, 72.8428], radius: 2800, color: '#f97316', label: 'Dadar-Hindmata Intense Cell (48.6 mm/hr)' },
      { center: [19.0682, 72.8765], radius: 2400, color: '#f59e0b', label: 'Kurla AWS Cell (44.2 mm/hr)' }
    ];

    radarCells.forEach(c => {
      const circle = L.circle(c.center as any, {
        radius: c.radius,
        fillColor: c.color,
        fillOpacity: 0.18,
        stroke: false
      });
      circle.bindTooltip(c.label);
      this.rainfallGroup.addLayer(circle);
    });
  }

  private checkRouteQueryParams(): void {
    this.route.queryParams.subscribe(params => {
      if (params['lat'] && params['lng']) {
        const lat = parseFloat(params['lat']);
        const lng = parseFloat(params['lng']);
        this.map?.flyTo([lat, lng], 14, { duration: 1.2 });

        // Highlight matching zone
        const match = this.floodZones.find(z => 
          Math.abs(z.latitude - lat) < 0.02 && Math.abs(z.longitude - lng) < 0.02
        );
        if (match) {
          this.selectedZone = match;
        }
      }
    });
  }

  onHorizonChange(horizon: PredictionTime): void {
    this.currentHorizon = horizon;
    this.floodService.setHorizon(horizon);
    this.loadZonesAndLayers(horizon);

    if (this.selectedZone) {
      // Refresh selected zone with new prediction values
      const updated = this.floodZones.find(z => z.gridId === this.selectedZone?.gridId);
      if (updated) this.selectedZone = updated;
    }
  }

  toggleLayer(layerName: keyof typeof this.layers): void {
    this.layers[layerName] = !this.layers[layerName];
    if (layerName === 'floodRisk') this.renderFloodRiskLayer(this.floodZones);
    if (layerName === 'roads') this.renderRoadsLayer();
    if (layerName === 'drainage') this.renderDrainageLayer();
    if (layerName === 'rainfall') this.renderRainfallLayer();
  }

  searchLocality(): void {
    if (!this.searchQuery.trim()) return;
    const term = this.searchQuery.toLowerCase();
    const found = this.floodZones.find(z => 
      z.name.toLowerCase().includes(term) || z.gridId.toLowerCase().includes(term)
    );

    if (found && this.map) {
      this.map.flyTo([found.latitude, found.longitude], 14, { duration: 1.0 });
      this.selectedZone = found;
    }
  }

  clearSearch(): void {
    this.searchQuery = '';
  }

  closeDrawer(): void {
    this.selectedZone = null;
  }

  navigateToDetailedAnalysis(zone: FloodZone): void {
    this.router.navigate(['/location-risk'], {
      queryParams: { location: zone.name.split(' ')[0] }
    });
  }
}
