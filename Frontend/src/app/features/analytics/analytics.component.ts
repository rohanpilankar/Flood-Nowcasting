import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { AnalyticsService } from '../../core/services/analytics.service';
import { AnalyticsSummary, AreaRiskRank, RainfallTrendPoint } from '../../core/models/analytics.model';
import { LoadingStateComponent } from '../../shared/components/loading-state/loading-state.component';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    LoadingStateComponent
  ],
  template: `
    <div class="analytics-page">
      <!-- Header -->
      <div class="card analytics-header">
        <div class="header-left">
          <div class="title-with-badge">
            <h2 class="page-title">AI Inundation Analytics</h2>
            <span class="badge-role">Predictive Hydrology</span>
          </div>
          <p class="page-sub">Historical storm hydrographs, sector risk distributions, and urban runoff trends</p>
        </div>
        <div class="header-summary-chips">
          <div class="chip-item">
            <span class="c-sub">Peak Rainfall</span>
            <span class="c-val font-mono">Katraj (42 mm/hr)</span>
          </div>
          <div class="chip-item">
            <span class="c-sub">Vulnerable Population</span>
            <span class="c-val font-mono">~184,000</span>
          </div>
        </div>
      </div>

      @if (loading) {
        <app-loading-state message="Synthesizing rainfall telemetry and catchment runoff analytics..."></app-loading-state>
      } @else if (summary) {
        <!-- Top Row: Rainfall Trend Line Chart & Risk Distribution -->
        <div class="analytics-grid-top">
          <!-- Rainfall Intensity Hydrograph Chart -->
          <div class="card chart-card">
            <div class="card-header">
              <div>
                <div class="title-with-badge">
                  <h3 class="card-title">Rainfall Intensity Trend (mm/hr)</h3>
                  <span class="badge-role">Doppler Radar</span>
                </div>
                <p class="card-subtitle">Hourly precipitation curve across Greater Mumbai (BMC) catchment</p>
              </div>
            </div>

            <!-- Responsive SVG Line Chart -->
            <div class="svg-chart-container">
              <svg viewBox="0 0 700 240" class="responsive-svg">
                <!-- Grid Lines -->
                <line x1="50" y1="30" x2="670" y2="30" stroke="rgba(255, 255, 255, 0.06)" stroke-width="1" />
                <line x1="50" y1="80" x2="670" y2="80" stroke="rgba(255, 255, 255, 0.06)" stroke-width="1" />
                <line x1="50" y1="130" x2="670" y2="130" stroke="rgba(255, 255, 255, 0.06)" stroke-width="1" />
                <line x1="50" y1="180" x2="670" y2="180" stroke="rgba(255, 255, 255, 0.06)" stroke-width="1" />

                <!-- Y-Axis Labels -->
                <text x="40" y="34" fill="#64748b" font-size="11" text-anchor="end">45</text>
                <text x="40" y="84" fill="#64748b" font-size="11" text-anchor="end">30</text>
                <text x="40" y="134" fill="#64748b" font-size="11" text-anchor="end">15</text>
                <text x="40" y="184" fill="#64748b" font-size="11" text-anchor="end">0</text>

                <!-- Gradient Definition -->
                <defs>
                  <linearGradient id="rainGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.45" />
                    <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.0" />
                  </linearGradient>
                </defs>

                <!-- Area Fill -->
                <path
                  d="M 60 166 L 125 150 L 190 138 L 255 102 L 320 54 L 385 36 L 450 116 L 515 90 L 580 128 L 645 158 L 645 180 L 60 180 Z"
                  fill="url(#rainGradient)"
                />

                <!-- Line Path -->
                <path
                  d="M 60 166 L 125 150 L 190 138 L 255 102 L 320 54 L 385 36 L 450 116 L 515 90 L 580 128 L 645 158"
                  fill="none"
                  stroke="#3b82f6"
                  stroke-width="3"
                  stroke-linecap="round"
                />

                <!-- Data Points & Labels -->
                @for (pt of rainfallPointsWithCoords; track pt.time) {
                  <circle [attr.cx]="pt.x" [attr.cy]="pt.y" r="4.5" fill="#60a5fa" stroke="#0f172a" stroke-width="2" />
                  <text [attr.x]="pt.x" y="206" fill="#94a3b8" font-size="10.5" text-anchor="middle">
                    {{ pt.time }}
                  </text>
                }

                <!-- Peak Annotation -->
                <g transform="translate(385, 20)">
                  <rect x="-42" y="-12" width="84" height="20" rx="4" fill="#ef4444" opacity="0.9" />
                  <text x="0" y="2" fill="#ffffff" font-size="10" font-weight="bold" text-anchor="middle">
                    PEAK 42 mm/hr
                  </text>
                </g>
              </svg>
            </div>
            <div class="chart-footer">
              <span class="footer-note">Precipitation curve based on convective nowcasting model.</span>
            </div>
          </div>

          <!-- Flood Risk Distribution -->
          <div class="card distribution-card">
            <div class="card-header">
              <div>
                <h3 class="card-title">Risk Zone Distribution</h3>
                <p class="card-subtitle">Grid classification breakdown across 70 mapped sectors</p>
              </div>
            </div>

            <div class="dist-bars-list">
              <!-- Safe / No Risk -->
              <div class="dist-row">
                <div class="dist-label-col">
                  <span class="dist-title">Safe / No Risk</span>
                  <span class="dist-count font-mono">{{ summary.riskDistribution.noRisk }} sectors (20%)</span>
                </div>
                <div class="dist-bar-track">
                  <div class="dist-bar-fill risk-safe" [style.width.%]="20"></div>
                </div>
              </div>

              <!-- Low Risk -->
              <div class="dist-row">
                <div class="dist-label-col">
                  <span class="dist-title">Low Risk</span>
                  <span class="dist-count font-mono">{{ summary.riskDistribution.low }} sectors (40%)</span>
                </div>
                <div class="dist-bar-track">
                  <div class="dist-bar-fill risk-low" [style.width.%]="40"></div>
                </div>
              </div>

              <!-- Medium Risk -->
              <div class="dist-row">
                <div class="dist-label-col">
                  <span class="dist-title">Medium / Caution</span>
                  <span class="dist-count font-mono">{{ summary.riskDistribution.medium }} sectors (23%)</span>
                </div>
                <div class="dist-bar-track">
                  <div class="dist-bar-fill risk-medium" [style.width.%]="23"></div>
                </div>
              </div>

              <!-- High Risk -->
              <div class="dist-row">
                <div class="dist-label-col">
                  <span class="dist-title">High Flood Risk</span>
                  <span class="dist-count font-mono text-danger">{{ summary.riskDistribution.high }} sectors (13%)</span>
                </div>
                <div class="dist-bar-track">
                  <div class="dist-bar-fill risk-high" [style.width.%]="13"></div>
                </div>
              </div>

              <!-- Critical Risk -->
              <div class="dist-row">
                <div class="dist-label-col">
                  <span class="dist-title">Critical / Impassable</span>
                  <span class="dist-count font-mono text-danger">{{ summary.riskDistribution.critical }} sectors (4%)</span>
                </div>
                <div class="dist-bar-track">
                  <div class="dist-bar-fill risk-critical" [style.width.%]="4"></div>
                </div>
              </div>
            </div>

            <div class="dist-summary-box">
              <span class="d-icon">⚠</span>
              <span class="d-text">
                <strong>17% of mapped city sectors</strong> currently require heightened emergency dispatch readiness.
              </span>
            </div>
          </div>
        </div>

        <!-- Bottom Row: High Risk Leaderboard & 24h Inundation Profile -->
        <div class="analytics-grid-bottom">
          <!-- High Risk Areas Leaderboard Table -->
          <div class="card leaderboard-card">
            <div class="card-header">
              <div>
                <h3 class="card-title">Vulnerability Leaderboard</h3>
                <p class="card-subtitle">Ranked by AI risk score & precipitation accumulation</p>
              </div>
              <a routerLink="/location-risk" class="btn btn-secondary btn-sm">
                Examine All Areas →
              </a>
            </div>

            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Locality / Sector</th>
                    <th>Risk Score</th>
                    <th>Trend</th>
                    <th>Rainfall</th>
                    <th>Elevation</th>
                  </tr>
                </thead>
                <tbody>
                  @for (area of summary.areaRankings; track area.rank) {
                    <tr>
                      <td class="rank-cell font-mono">#{{ area.rank }}</td>
                      <td class="area-name">
                        <strong>{{ area.area }}</strong>
                      </td>
                      <td>
                        <div class="score-pill font-mono" [ngClass]="getScoreClass(area.riskScore)">
                          {{ area.riskScore }}%
                        </div>
                      </td>
                      <td>
                        <span class="trend-badge" [ngClass]="getTrendClass(area.trend)">
                          @if (area.trend === 'INCREASING') { ↑ Increasing }
                          @else if (area.trend === 'DECREASING') { ↓ Decreasing }
                          @else { ● Stable }
                        </span>
                      </td>
                      <td class="font-mono">{{ area.rainfall }} mm/hr</td>
                      <td class="font-mono text-muted">{{ area.elevation }} m</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          </div>

          <!-- 24-Hour Inundation Curve -->
          <div class="card inundation-card">
            <div class="card-header">
              <div>
                <h3 class="card-title">24-Hour Water Depth Profile</h3>
                <p class="card-subtitle">Average catchment ponding depth & impacted road segments</p>
              </div>
            </div>

            <div class="inundation-bars-grid">
              @for (point of summary.inundationHistory; track point.hour) {
                <div class="inundation-col">
                  <div class="inundation-bar-wrap">
                    <div
                      class="inundation-bar"
                      [style.height.%]="(point.avgWaterDepthCm / 50) * 100"
                      [ngClass]="point.avgWaterDepthCm > 30 ? 'bg-danger' : point.avgWaterDepthCm > 15 ? 'bg-warning' : 'bg-safe'"
                    >
                      <span class="bar-top-value font-mono">{{ point.avgWaterDepthCm }}cm</span>
                    </div>
                  </div>
                  <span class="inundation-hour font-mono">{{ point.hour }}</span>
                  <span class="roads-affected font-mono">{{ point.affectedRoadsCount }} rds</span>
                </div>
              }
            </div>

            <div class="inundation-footer">
              <span class="info-tag">Road Impact:</span>
              <span class="info-text">Peak blockage reached at +1h with 11 primary underpasses inundated.</span>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .analytics-page {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .title-with-badge {
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }
    .page-title {
      font-size: 1.45rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .page-sub {
      font-size: 0.825rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
    }

    .analytics-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .header-summary-chips {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .chip-item {
      display: flex;
      flex-direction: column;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.4rem 0.85rem;
    }
    .c-sub {
      font-size: 0.68rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .c-val {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-main);
    }

    // Top Grid
    .analytics-grid-top {
      display: grid;
      grid-template-columns: 1.7fr 1.1fr;
      gap: 1.25rem;
      @media (max-width: 1100px) {
        grid-template-columns: 1fr;
      }
    }

    .chart-card {
      display: flex;
      flex-direction: column;
    }
    .svg-chart-container {
      width: 100%;
      padding: 0.5rem 0;
    }
    .responsive-svg {
      width: 100%;
      height: auto;
      display: block;
    }
    .chart-footer {
      border-top: 1px solid var(--border-light);
      padding-top: 0.65rem;
      margin-top: 0.5rem;
      font-size: 0.75rem;
      color: var(--text-muted);
    }

    // Distribution Card
    .distribution-card {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .dist-bars-list {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .dist-row {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }
    .dist-label-col {
      display: flex;
      justify-content: space-between;
      font-size: 0.78rem;
    }
    .dist-title {
      color: var(--text-main);
      font-weight: 500;
    }
    .dist-count {
      color: var(--text-muted);
    }
    .dist-bar-track {
      height: 8px;
      background-color: var(--bg-darkest);
      border-radius: var(--radius-full);
      overflow: hidden;
    }
    .dist-bar-fill {
      height: 100%;
      border-radius: var(--radius-full);
    }
    .dist-summary-box {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      background-color: rgba(239, 68, 68, 0.08);
      border: 1px solid rgba(239, 68, 68, 0.2);
      border-radius: var(--radius-sm);
      padding: 0.65rem 0.85rem;
      font-size: 0.78rem;
      color: #fca5a5;
    }

    // Bottom Grid
    .analytics-grid-bottom {
      display: grid;
      grid-template-columns: 1.5fr 1fr;
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
      font-size: 0.825rem;

      th {
        padding: 0.65rem 0.85rem;
        background-color: var(--bg-darkest);
        color: var(--text-muted);
        text-transform: uppercase;
        font-size: 0.68rem;
        letter-spacing: 0.04em;
        border-bottom: 1px solid var(--border-subtle);
      }
      td {
        padding: 0.65rem 0.85rem;
        border-bottom: 1px solid var(--border-light);
        color: var(--text-main);
      }
    }
    .rank-cell {
      color: #93c5fd;
      font-weight: 600;
    }
    .score-pill {
      display: inline-block;
      padding: 0.15rem 0.5rem;
      border-radius: var(--radius-sm);
      font-weight: 700;
      font-size: 0.75rem;
    }
    .trend-badge {
      font-size: 0.72rem;
      font-weight: 600;
      padding: 0.1rem 0.4rem;
      border-radius: var(--radius-sm);
    }
    .trend-increasing {
      color: var(--status-critical);
      background-color: rgba(239, 68, 68, 0.12);
    }
    .trend-decreasing {
      color: var(--status-safe);
      background-color: rgba(16, 185, 129, 0.12);
    }
    .trend-stable {
      color: var(--status-caution);
      background-color: rgba(245, 158, 11, 0.12);
    }

    // Inundation Bars
    .inundation-card {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .inundation-bars-grid {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 0.45rem;
      height: 200px;
      align-items: flex-end;
      padding: 1rem 0 0.5rem 0;
    }
    .inundation-col {
      display: flex;
      flex-direction: column;
      align-items: center;
      height: 100%;
      justify-content: flex-end;
      gap: 0.35rem;
    }
    .inundation-bar-wrap {
      width: 100%;
      height: 130px;
      display: flex;
      align-items: flex-end;
      justify-content: center;
    }
    .inundation-bar {
      width: 70%;
      border-radius: 4px 4px 0 0;
      position: relative;
      transition: height 0.6s ease;
      min-height: 4px;
    }
    .bar-top-value {
      position: absolute;
      top: -18px;
      left: 50%;
      transform: translateX(-50%);
      font-size: 0.65rem;
      font-weight: 600;
      color: var(--text-main);
      white-space: nowrap;
    }
    .bg-danger { background-color: #ef4444; }
    .bg-warning { background-color: #f59e0b; }
    .bg-safe { background-color: #10b981; }

    .inundation-hour {
      font-size: 0.68rem;
      color: var(--text-muted);
    }
    .roads-affected {
      font-size: 0.65rem;
      color: var(--text-dim);
    }
    .inundation-footer {
      border-top: 1px solid var(--border-light);
      padding-top: 0.65rem;
      font-size: 0.75rem;
      display: flex;
      gap: 0.4rem;
    }
    .info-tag {
      font-weight: 600;
      color: #93c5fd;
    }
    .info-text {
      color: var(--text-muted);
    }
  `]
})
export class AnalyticsComponent implements OnInit {
  summary: AnalyticsSummary | null = null;
  loading = false;

  readonly rainfallPointsWithCoords = [
    { time: '08:00', x: 60, y: 166 },
    { time: '09:00', x: 125, y: 150 },
    { time: '10:00', x: 190, y: 138 },
    { time: '11:00', x: 255, y: 102 },
    { time: '12:00', x: 320, y: 54 },
    { time: '13:00', x: 385, y: 36 },
    { time: '14:00 (NOW)', x: 450, y: 116 },
    { time: '15:00', x: 515, y: 90 },
    { time: '16:00', x: 580, y: 128 },
    { time: '17:00', x: 645, y: 158 }
  ];

  constructor(private analyticsService: AnalyticsService) {}

  ngOnInit(): void {
    this.loading = true;
    this.analyticsService.getAnalyticsSummary().subscribe({
      next: data => {
        this.summary = data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  getScoreClass(score: number): string {
    if (score >= 80) return 'status-unsafe';
    if (score >= 50) return 'status-caution';
    return 'status-safe';
  }

  getTrendClass(trend: string): string {
    if (trend === 'INCREASING') return 'trend-increasing';
    if (trend === 'DECREASING') return 'trend-decreasing';
    return 'trend-stable';
  }
}
