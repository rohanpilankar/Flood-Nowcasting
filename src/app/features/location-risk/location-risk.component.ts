import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { FloodService } from '../../core/services/flood.service';
import { FloodZone } from '../../core/models/flood-risk.model';
import { RiskGaugeComponent } from '../../shared/components/risk-gauge/risk-gauge.component';
import { RiskBadgeComponent } from '../../shared/components/risk-badge/risk-badge.component';
import { PrototypeNoticeComponent } from '../../shared/components/prototype-notice/prototype-notice.component';
import { LoadingStateComponent } from '../../shared/components/loading-state/loading-state.component';
import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state.component';

interface ForecastTimelineStep {
  time: string;
  level: string;
  score: number;
  waterDepth: number;
}

@Component({
  selector: 'app-location-risk',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    RiskGaugeComponent,
    RiskBadgeComponent,
    LoadingStateComponent,
    EmptyStateComponent
  ],
  template: `
    <div class="location-risk-page">
      <!-- Search & Locality Selection Bar -->
      <div class="card search-card">
        <div class="search-header">
          <div>
            <h2 class="page-title">Location Risk Analysis</h2>
            <p class="page-sub">Comprehensive urban catchment risk profile & multi-horizon forecast</p>
          </div>
          <span class="badge-prototype">AI Vulnerability Index</span>
        </div>

        <div class="search-input-row">
          <div class="input-with-icon">
            <svg class="icon-search" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input
              type="text"
              class="location-input"
              placeholder="Enter location, area, or coordinates (e.g. Katraj, Baner)..."
              [(ngModel)]="searchQuery"
              (keyup.enter)="onSearch()"
            />
          </div>
          <button type="button" class="btn btn-primary" (click)="onSearch()">
            Analyze Risk
          </button>
        </div>

        <!-- Quick Locality Chips -->
        <div class="quick-chips-row">
          <span class="chips-label">Quick Analyze:</span>
          <div class="chips-list">
            @for (loc of quickLocations; track loc) {
              <button
                type="button"
                class="chip-btn"
                [class.active]="selectedLocalityName.toLowerCase() === loc.toLowerCase()"
                (click)="selectQuickLocation(loc)"
              >
                {{ loc }}
              </button>
            }
          </div>
        </div>
      </div>

      <!-- Main Analysis Results -->
      @if (loading) {
        <app-loading-state message="Running AI hydrodynamic nowcasting for location..."></app-loading-state>
      } @else if (zoneData) {
        <div class="analysis-content-grid">
          <!-- Left: Risk Score Gauge Card -->
          <div class="card risk-score-card">
            <div class="card-header">
              <div>
                <span class="locality-sector font-mono">{{ zoneData.gridId }}</span>
                <h3 class="locality-title">{{ zoneData.name }}</h3>
              </div>
              <app-risk-badge [level]="zoneData.riskLevel"></app-risk-badge>
            </div>

            <div class="gauge-display-section">
              <app-risk-gauge [score]="zoneData.riskScore"></app-risk-gauge>
            </div>

            <div class="score-meta-box">
              <div class="s-meta-item">
                <span class="s-label">Simulated Water Depth</span>
                <span class="s-val font-mono">{{ zoneData.waterDepth }} m</span>
              </div>
              <div class="s-meta-divider"></div>
              <div class="s-meta-item">
                <span class="s-label">AI Model Confidence</span>
                <span class="s-val font-mono">89%</span>
              </div>
            </div>

            <p class="zone-summary-text">{{ zoneData.summary }}</p>

            <div class="card-footer-action">
              <a [routerLink]="['/safe-route']" [queryParams]="{ from: selectedLocalityName, to: 'Shivajinagar' }" class="btn btn-secondary btn-sm" style="width: 100%;">
                Find Safe Evacuation Route from {{ selectedLocalityName }} →
              </a>
            </div>
          </div>

          <!-- Right: Forecast Timeline & Risk Factors -->
          <div class="right-details-column">
            <!-- Forecast Timeline Card -->
            <div class="card timeline-card">
              <div class="card-header">
                <div>
                  <div class="title-with-badge">
                    <h3 class="card-title">Forecast Risk Timeline</h3>
                    <span class="badge-prototype">Multi-Horizon Nowcast</span>
                  </div>
                  <p class="card-subtitle">AI-simulated risk progression over the next 3 hours</p>
                </div>
              </div>

              <div class="timeline-stepper">
                @for (step of forecastTimeline; track step.time) {
                  <div class="timeline-node">
                    <span class="node-time">{{ step.time }}</span>
                    <div class="node-indicator" [ngClass]="getStepClass(step.level)">
                      <span class="node-score font-mono">{{ step.score }}%</span>
                    </div>
                    <span class="node-level">{{ step.level }}</span>
                    <span class="node-depth font-mono">{{ step.waterDepth }}m</span>
                  </div>
                }
              </div>
            </div>

            <!-- Risk Factors Matrix -->
            <div class="card factors-card">
              <div class="card-header">
                <div>
                  <div class="title-with-badge">
                    <h3 class="card-title">Key Flood Risk Factors</h3>
                    <span class="badge-prototype">GIS & Hydrology Metrics</span>
                  </div>
                  <p class="card-subtitle">Simulated contributing parameters to urban inundation</p>
                </div>
              </div>

              <div class="factors-grid">
                <!-- Factor 1: Rainfall Intensity -->
                <div class="factor-item">
                  <div class="factor-top">
                    <span class="f-name">Rainfall Intensity</span>
                    <span class="badge status-unsafe">High</span>
                  </div>
                  <div class="f-value font-mono">{{ zoneData.rainfall }} mm/hr</div>
                  <p class="f-desc">
                    Intense precipitation exceeding the local soil percolation threshold, generating immediate surface runoff.
                  </p>
                </div>

                <!-- Factor 2: Elevation -->
                <div class="factor-item">
                  <div class="factor-top">
                    <span class="f-name">Topographic Elevation</span>
                    <span class="badge status-caution">{{ zoneData.elevation < 20 ? 'Low-Lying' : 'Moderate' }}</span>
                  </div>
                  <div class="f-value font-mono">{{ zoneData.elevation }} meters</div>
                  <p class="f-desc">
                    Catchment basin sits at low relative contour, naturally collecting gravity-driven overland flows.
                  </p>
                </div>

                <!-- Factor 3: Built-up Density -->
                <div class="factor-item">
                  <div class="factor-top">
                    <span class="f-name">Built-up Density</span>
                    <span class="badge status-unsafe">High Runoff</span>
                  </div>
                  <div class="f-value font-mono">{{ zoneData.builtUpDensity }}% Impermeable</div>
                  <p class="f-desc">
                    High urban footprint with concrete pavements and asphalt road surfaces impedes natural water absorption.
                  </p>
                </div>

                <!-- Factor 4: Historical Flooding -->
                <div class="factor-item">
                  <div class="factor-top">
                    <span class="f-name">Historical Inundation</span>
                    <span class="badge status-unsafe">{{ zoneData.historicalFlooding }}</span>
                  </div>
                  <div class="f-value font-mono">Frequent Events</div>
                  <p class="f-desc">
                    Simulated historical records indicate recurring waterlogging episodes during intense monsoon seasons.
                  </p>
                </div>

                <!-- Factor 5: Drainage Network -->
                <div class="factor-item">
                  <div class="factor-top">
                    <span class="f-name">Drainage Network</span>
                    <span class="badge" [ngClass]="zoneData.drainageStatus === 'Critical' ? 'status-critical' : 'status-caution'">
                      {{ zoneData.drainageStatus }}
                    </span>
                  </div>
                  <div class="f-value font-mono">Culvert Capacity</div>
                  <p class="f-desc">
                    Stormwater outlets require continuous monitoring against debris accumulation and downstream tailwater backup.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      } @else {
        <app-empty-state
          title="Location Not Found"
          description="We could not find flood analysis data for the specified query. Try searching for Katraj, Shivajinagar, Baner, or Hadapsar."
          actionLabel="Reset to Katraj"
          (action)="selectQuickLocation('Katraj')"
        ></app-empty-state>
      }
    </div>
  `,
  styles: [`
    .location-risk-page {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .search-card {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .search-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    .page-title {
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .page-sub {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
    }

    .search-input-row {
      display: flex;
      gap: 0.75rem;
      align-items: center;
      @media (max-width: 640px) {
        flex-direction: column;
        align-items: stretch;
      }
    }
    .input-with-icon {
      position: relative;
      flex: 1;
      display: flex;
      align-items: center;
    }
    .icon-search {
      position: absolute;
      left: 0.85rem;
      color: var(--text-dim);
      pointer-events: none;
    }
    .location-input {
      width: 100%;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 0.65rem 1rem 0.65rem 2.4rem;
      color: var(--text-main);
      font-size: 0.925rem;
      outline: none;
      transition: border-color var(--transition-fast);

      &:focus {
        border-color: var(--brand-primary);
        box-shadow: 0 0 0 2px var(--brand-primary-glow);
      }
    }

    .quick-chips-row {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .chips-label {
      font-size: 0.75rem;
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .chips-list {
      display: flex;
      align-items: center;
      gap: 0.45rem;
      flex-wrap: wrap;
    }
    .chip-btn {
      padding: 0.28rem 0.75rem;
      font-size: 0.76rem;
      font-weight: 500;
      border-radius: var(--radius-full);
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      transition: all var(--transition-fast);

      &:hover {
        color: var(--text-main);
        border-color: var(--text-dim);
      }
      &.active {
        background-color: var(--brand-primary);
        color: #ffffff;
        border-color: var(--brand-primary);
        box-shadow: 0 2px 6px rgba(59, 130, 246, 0.35);
      }
    }

    // Grid Layout
    .analysis-content-grid {
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 1.5rem;
      @media (max-width: 1100px) {
        grid-template-columns: 1fr;
      }
    }

    // Risk Score Card
    .risk-score-card {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .locality-sector {
      font-size: 0.75rem;
      color: #93c5fd;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .locality-title {
      font-size: 1.35rem;
      font-weight: 700;
      color: var(--text-main);
      margin-top: 0.15rem;
    }
    .gauge-display-section {
      padding: 1rem 0 0.5rem 0;
    }
    .score-meta-box {
      display: flex;
      align-items: center;
      justify-content: space-around;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-md);
      padding: 0.75rem;
    }
    .s-meta-item {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .s-label {
      font-size: 0.7rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .s-val {
      font-size: 1rem;
      font-weight: 700;
      color: var(--text-main);
      margin-top: 0.2rem;
    }
    .s-meta-divider {
      width: 1px;
      height: 28px;
      background-color: var(--border-subtle);
    }
    .zone-summary-text {
      font-size: 0.85rem;
      color: var(--text-muted);
      line-height: 1.5;
    }
    .card-footer-action {
      margin-top: auto;
      padding-top: 0.5rem;
    }

    // Right Column
    .right-details-column {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    // Forecast Timeline Stepper
    .timeline-card {
      display: flex;
      flex-direction: column;
    }
    .timeline-stepper {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 0.75rem;
      margin-top: 0.5rem;
      @media (max-width: 640px) {
        grid-template-columns: 1fr;
      }
    }
    .timeline-node {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-md);
      padding: 0.85rem 0.5rem;
      gap: 0.35rem;
      transition: all var(--transition-fast);

      &:hover {
        border-color: var(--border-subtle);
        transform: translateY(-2px);
      }
    }
    .node-time {
      font-size: 0.74rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .node-indicator {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0.2rem 0;
      border: 2px solid currentColor;
    }
    .node-score {
      font-size: 0.825rem;
      font-weight: 700;
    }
    .node-level {
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: uppercase;
    }
    .node-depth {
      font-size: 0.75rem;
      color: var(--text-dim);
    }

    // Factors Grid
    .factors-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
      margin-top: 0.5rem;
    }
    .factor-item {
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-md);
      padding: 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .factor-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .f-name {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .f-value {
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text-main);
      margin: 0.15rem 0;
    }
    .f-desc {
      font-size: 0.78rem;
      color: var(--text-muted);
      line-height: 1.4;
    }
  `]
})
export class LocationRiskComponent implements OnInit {
  searchQuery = 'Katraj';
  selectedLocalityName = 'Katraj';
  loading = false;
  zoneData: FloodZone | null = null;

  readonly quickLocations = [
    'Katraj',
    'Shivajinagar',
    'Hadapsar',
    'Baner',
    'Wakad',
    'Kothrud',
    'Hinjewadi'
  ];

  forecastTimeline: ForecastTimelineStep[] = [];

  constructor(
    private floodService: FloodService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      if (params['location']) {
        this.searchQuery = params['location'];
        this.selectedLocalityName = params['location'];
      }
      this.loadLocationRisk(this.selectedLocalityName);
    });
  }

  onSearch(): void {
    if (this.searchQuery.trim()) {
      this.selectedLocalityName = this.searchQuery.trim();
      this.loadLocationRisk(this.selectedLocalityName);
    }
  }

  selectQuickLocation(loc: string): void {
    this.searchQuery = loc;
    this.selectedLocalityName = loc;
    this.loadLocationRisk(loc);
  }

  private loadLocationRisk(name: string): void {
    this.loading = true;
    this.floodService.getLocationRisk(name).subscribe({
      next: data => {
        this.zoneData = data || null;
        if (data) {
          this.buildForecastTimeline(data);
        }
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.zoneData = null;
      }
    });
  }

  private buildForecastTimeline(zone: FloodZone): void {
    const base = zone.riskScore;
    const depth = zone.waterDepth;

    this.forecastTimeline = [
      { time: 'NOW', level: zone.riskLevel, score: base, waterDepth: depth },
      { time: '+30 MIN', level: base > 60 ? 'HIGH' : 'MEDIUM', score: Math.min(98, Math.round(base * 1.1)), waterDepth: Math.round(depth * 1.15 * 100) / 100 },
      { time: '+1 HOUR', level: base > 50 ? 'HIGH' : 'MEDIUM', score: Math.min(99, Math.round(base * 1.25)), waterDepth: Math.round(depth * 1.3 * 100) / 100 },
      { time: '+2 HOURS', level: 'MEDIUM', score: Math.round(base * 0.85), waterDepth: Math.round(depth * 0.9 * 100) / 100 },
      { time: '+3 HOURS', level: 'LOW', score: Math.round(base * 0.6), waterDepth: Math.round(depth * 0.6 * 100) / 100 }
    ];
  }

  getStepClass(level: string): string {
    const l = level.toUpperCase();
    if (l === 'HIGH' || l === 'CRITICAL') return 'status-unsafe';
    if (l === 'MEDIUM') return 'status-caution';
    return 'status-safe';
  }
}
