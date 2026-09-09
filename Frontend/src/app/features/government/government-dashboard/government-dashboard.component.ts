import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { GovernmentService, EmergencyOverview } from '../../../core/services/government.service';
import { AuthService } from '../../../core/auth/auth.service';
import { BroadcastModalComponent } from '../broadcast-modal/broadcast-modal.component';

@Component({
  selector: 'app-government-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, BroadcastModalComponent],
  template: `
    <div class="gov-dashboard">
      <!-- Command Header -->
      <div class="command-banner">
        <div class="banner-left">
          <div class="gov-badge-group">
            <span class="gov-badge">GOVERNMENT EOC CONSOLE</span>
            <span class="status-verified">VERIFIED AUTHORITY</span>
          </div>
          <h1>BMC Emergency Operations Command</h1>
          <p class="subtitle">
            Municipal Corporation of Greater Mumbai • Real-Time Spatial Inundation & Alert Broadcast System
          </p>
        </div>

        <div class="banner-actions">
          <button class="btn btn-danger btn-broadcast" (click)="showBroadcastModal.set(true)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
            </svg>
            Broadcast Emergency Warning
          </button>
        </div>
      </div>

      <!-- Overview Stats Grid -->
      <div class="metrics-grid">
        <div class="metric-card">
          <span class="metric-label">Active Warning Zones</span>
          <div class="metric-val text-primary">{{ overview()?.active_alerts_count || 3 }}</div>
          <span class="metric-sub">Monitored BMC flood zones</span>
        </div>

        <div class="metric-card">
          <span class="metric-label">Critical Inundation Hotspots</span>
          <div class="metric-val text-danger">{{ overview()?.critical_zones_count || 1 }}</div>
          <span class="metric-sub">>20cm accumulation</span>
        </div>

        <div class="metric-card">
          <span class="metric-label">Opted-In Citizens (In-Zone)</span>
          <div class="metric-val text-info">{{ overview()?.total_citizens_opted_in || 125 }}</div>
          <span class="metric-sub">Privacy-preserving aggregate</span>
        </div>

        <div class="metric-card">
          <span class="metric-label">Dispatched Notifications</span>
          <div class="metric-val text-success">{{ overview()?.total_notifications_dispatched || 112 }}</div>
          <span class="metric-sub">Push / SMS alert delivery</span>
        </div>
      </div>

      <!-- Privacy-Preserving Aggregate Citizen Inundation Table -->
      <div class="glass-card section-table-card">
        <div class="card-header-flex">
          <div>
            <h3>Zone Inundation & Aggregate Citizen Counts</h3>
            <p>Spatial proximity aggregation. Exact citizen coordinates are strictly protected.</p>
          </div>
          <button class="btn btn-sm btn-outline" (click)="refreshOverview()">Refresh Data</button>
        </div>

        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Zone / Corridor</th>
                <th>Ward</th>
                <th>Risk Level</th>
                <th>Water Depth</th>
                <th>Opted-In Citizens</th>
                <th>Dispatched Alerts</th>
                <th>Delivery Rate</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              @for (zone of overview()?.zones_summary || defaultZones; track zone.zone_name) {
                <tr>
                  <td>
                    <strong>{{ zone.zone_name }}</strong>
                  </td>
                  <td><span class="ward-tag">{{ zone.ward }}</span></td>
                  <td>
                    <span class="risk-tag" [class]="zone.risk_level.toLowerCase()">
                      {{ zone.risk_level }}
                    </span>
                  </td>
                  <td class="font-mono">{{ zone.water_depth_cm }} cm</td>
                  <td>
                    <strong class="count-bold">{{ zone.opted_in_citizens }}</strong> citizens
                  </td>
                  <td class="font-mono">{{ zone.notified_citizens }}</td>
                  <td>
                    <div class="progress-bar-wrap">
                      <div
                        class="progress-bar-fill"
                        [style.width.%]="(zone.notified_citizens / (zone.opted_in_citizens || 1)) * 100"
                      ></div>
                    </div>
                  </td>
                  <td>
                    <span class="pulse-indicator-inline">
                      <span class="pulse-dot"></span>
                      ACTIVE
                    </span>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

      <!-- Bottom Split: Active Alerts & EOC Directory -->
      <div class="bottom-split-grid">
        <!-- Active Alerts Broadcasted -->
        <div class="glass-card">
          <div class="card-header-flex">
            <h3>Active EOC Warning Broadcasts</h3>
            <a routerLink="/alerts" class="link-view-all">View All →</a>
          </div>

          <div class="broadcasts-stack">
            @for (alert of activeAlerts(); track alert.id) {
              <div class="broadcast-item" [class.critical]="alert.severity === 'CRITICAL'">
                <div class="item-top">
                  <span class="sev-tag" [class]="alert.severity.toLowerCase()">{{ alert.severity }}</span>
                  <span class="ward">{{ alert.affected_ward }}</span>
                  <span class="time">{{ alert.issued_at | date:'shortTime' }}</span>
                </div>
                <h4>{{ alert.title }}</h4>
                <p>{{ alert.message }}</p>
                <div class="target-stat">
                  <span>Targeted Citizens: <strong>{{ alert.opted_in_target_count || 125 }}</strong></span>
                  <span>Delivered: <strong>{{ alert.delivered_count || 112 }}</strong></span>
                </div>
              </div>
            }
          </div>
        </div>

        <!-- Verified Authority Directory -->
        <div class="glass-card">
          <div class="card-header-flex">
            <h3>Verified Ward Authorities</h3>
          </div>

          <div class="officers-list">
            @for (officer of verifiedOfficers(); track officer.id) {
              <div class="officer-entry">
                <div class="officer-avatar">🏛️</div>
                <div class="officer-details">
                  <strong>{{ officer.full_name }}</strong>
                  <span class="designation">{{ officer.designation }} • {{ officer.department }}</span>
                  <span class="ward-jurisdiction">Jurisdiction: {{ officer.jurisdiction_ward }}</span>
                </div>
                <span class="badge-active">ONLINE</span>
              </div>
            }
          </div>
        </div>
      </div>
    </div>

    <!-- Broadcast Modal -->
    @if (showBroadcastModal()) {
      <app-broadcast-modal
        (closed)="onBroadcastClosed($event)"
      ></app-broadcast-modal>
    }
  `,
  styles: [`
    .gov-dashboard {
      padding: 1.5rem;
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .command-banner {
      background: linear-gradient(135deg, #0b1f38, #112744);
      border: 1px solid rgba(59, 130, 246, 0.3);
      border-radius: 16px;
      padding: 1.6rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .gov-badge-group {
      display: flex;
      gap: 0.6rem;
      margin-bottom: 0.3rem;
    }
    .gov-badge {
      font-size: 0.68rem;
      font-weight: 700;
      color: #60a5fa;
      background: rgba(37, 99, 235, 0.15);
      border: 1px solid rgba(59, 130, 246, 0.3);
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
    }
    .status-verified {
      font-size: 0.68rem;
      font-weight: 700;
      color: #34d399;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
    }
    .command-banner h1 {
      font-size: 1.7rem;
      margin: 0 0 0.25rem 0;
    }
    .subtitle {
      font-size: 0.88rem;
      color: var(--text-muted);
      margin: 0;
    }
    .btn-broadcast {
      padding: 0.75rem 1.25rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: #dc2626;
      border-radius: 10px;
      box-shadow: 0 4px 14px rgba(220, 38, 38, 0.4);
    }
    .btn-broadcast:hover {
      background: #b91c1c;
    }
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
    }
    @media (max-width: 900px) {
      .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }
    .metric-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .metric-label {
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .metric-val {
      font-size: 1.9rem;
      font-weight: 700;
      font-family: 'Outfit', sans-serif;
    }
    .metric-sub {
      font-size: 0.74rem;
      color: var(--text-dim);
    }
    .text-primary { color: #60a5fa; }
    .text-danger { color: #f87171; }
    .text-info { color: #38bdf8; }
    .text-success { color: #34d399; }
    .glass-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      padding: 1.5rem;
    }
    .card-header-flex {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.2rem;
    }
    .card-header-flex h3 {
      font-size: 1.15rem;
      margin: 0 0 0.2rem 0;
    }
    .card-header-flex p {
      font-size: 0.8rem;
      color: var(--text-dim);
      margin: 0;
    }
    .table-container {
      overflow-x: auto;
    }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.86rem;
    }
    .data-table th {
      padding: 0.75rem 1rem;
      color: var(--text-dim);
      font-size: 0.74rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .data-table td {
      padding: 0.85rem 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    .ward-tag {
      font-size: 0.74rem;
      background: rgba(255, 255, 255, 0.04);
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      color: var(--text-dim);
    }
    .risk-tag {
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      text-transform: uppercase;
    }
    .risk-tag.critical { background: #ef4444; color: white; }
    .risk-tag.high { background: #f59e0b; color: #1e1e1e; }
    .risk-tag.caution { background: #eab308; color: #1e1e1e; }
    .risk-tag.safe { background: #10b981; color: white; }
    .count-bold {
      color: #60a5fa;
    }
    .progress-bar-wrap {
      width: 80px;
      height: 6px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 9999px;
      overflow: hidden;
    }
    .progress-bar-fill {
      height: 100%;
      background: #10b981;
    }
    .pulse-indicator-inline {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.75rem;
      font-weight: 600;
      color: #10b981;
    }
    .bottom-split-grid {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 1.5rem;
    }
    @media (max-width: 900px) {
      .bottom-split-grid {
        grid-template-columns: 1fr;
      }
    }
    .broadcasts-stack {
      display: flex;
      flex-direction: column;
      gap: 0.8rem;
    }
    .broadcast-item {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }
    .broadcast-item.critical {
      border-color: rgba(239, 68, 68, 0.4);
      background: rgba(239, 68, 68, 0.04);
    }
    .item-top {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      font-size: 0.72rem;
    }
    .sev-tag {
      font-weight: 700;
      padding: 0.1rem 0.4rem;
      border-radius: 4px;
    }
    .sev-tag.critical { background: #ef4444; color: white; }
    .sev-tag.high { background: #f59e0b; color: #1e1e1e; }
    .time {
      margin-left: auto;
      color: var(--text-dim);
    }
    .broadcast-item h4 {
      font-size: 0.94rem;
      margin: 0;
    }
    .broadcast-item p {
      font-size: 0.82rem;
      color: var(--text-muted);
      margin: 0;
    }
    .target-stat {
      display: flex;
      gap: 1rem;
      font-size: 0.76rem;
      color: var(--text-dim);
      margin-top: 0.2rem;
    }
    .target-stat strong {
      color: var(--text-main);
    }
    .officers-list {
      display: flex;
      flex-direction: column;
      gap: 0.8rem;
    }
    .officer-entry {
      display: flex;
      align-items: center;
      gap: 0.8rem;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.06);
      padding: 0.75rem 0.9rem;
      border-radius: 8px;
    }
    .officer-avatar {
      font-size: 1.4rem;
    }
    .officer-details {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 0.1rem;
    }
    .officer-details strong {
      font-size: 0.88rem;
    }
    .designation {
      font-size: 0.76rem;
      color: var(--text-muted);
    }
    .ward-jurisdiction {
      font-size: 0.72rem;
      color: var(--text-dim);
    }
    .badge-active {
      font-size: 0.68rem;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      font-weight: 600;
    }
  `]
})
export class GovernmentDashboardComponent implements OnInit {
  overview = signal<EmergencyOverview | null>(null);
  activeAlerts = signal<any[]>([]);
  verifiedOfficers = signal<any[]>([]);
  showBroadcastModal = signal<boolean>(false);

  defaultZones = [
    { zone_name: 'Hindmata Junction / Dadar TT', ward: 'Ward F/N', risk_level: 'CRITICAL', water_depth_cm: 28, opted_in_citizens: 125, notified_citizens: 112 },
    { zone_name: 'Kurla West / LBS Marg', ward: 'Ward L', risk_level: 'HIGH', water_depth_cm: 22, opted_in_citizens: 94, notified_citizens: 89 },
    { zone_name: 'Andheri Subway / SV Road', ward: 'Ward K/W', risk_level: 'HIGH', water_depth_cm: 24, opted_in_citizens: 78, notified_citizens: 74 },
    { zone_name: 'Gandhi Market / King’s Circle', ward: 'Ward F/N', risk_level: 'CAUTION', water_depth_cm: 15, opted_in_citizens: 62, notified_citizens: 58 },
    { zone_name: 'Bandra BKC Connector', ward: 'Ward H/E', risk_level: 'SAFE', water_depth_cm: 4, opted_in_citizens: 140, notified_citizens: 140 }
  ];

  constructor(
    private govService: GovernmentService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.refreshOverview();
    this.loadActiveAlerts();
    this.loadOfficers();
  }

  refreshOverview(): void {
    this.govService.getEmergencyOverview().subscribe(data => this.overview.set(data));
  }

  loadActiveAlerts(): void {
    this.govService.getActiveAlerts().subscribe(alerts => this.activeAlerts.set(alerts));
  }

  loadOfficers(): void {
    this.govService.getVerifiedAuthorities().subscribe(officers => this.verifiedOfficers.set(officers));
  }

  onBroadcastClosed(refreshed: boolean): void {
    this.showBroadcastModal.set(false);
    if (refreshed) {
      this.refreshOverview();
      this.loadActiveAlerts();
    }
  }
}
