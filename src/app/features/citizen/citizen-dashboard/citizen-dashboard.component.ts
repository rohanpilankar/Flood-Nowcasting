import { Component, OnInit, signal, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/auth/auth.service';
import { CitizenLocationService } from '../../../core/services/citizen-location.service';
import { CitizenAlertService, TargetedAlert } from '../../../core/services/citizen-alert.service';
import { FloodService } from '../../../core/services/flood.service';
import { RiskGaugeComponent } from '../../../shared/components/risk-gauge/risk-gauge.component';
import { StatCardComponent } from '../../../shared/components/stat-card/stat-card.component';
import { FeedbackModalComponent } from '../feedback-modal/feedback-modal.component';

@Component({
  selector: 'app-citizen-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RiskGaugeComponent,
    FeedbackModalComponent
  ],
  template: `
    <div class="citizen-dashboard">
      <!-- Welcome Header -->
      <div class="dashboard-banner">
        <div class="banner-content">
          <div class="banner-title-group">
            <span class="citizen-tag">CITIZEN SAFETY PORTAL</span>
            <h1>Welcome, {{ authService.currentUser()?.full_name || 'Citizen' }}</h1>
            <p class="banner-subtitle">
              Live flood risk advisory for your area:
              <strong>{{ currentAreaName() }}</strong> (Ward F/North — Greater Mumbai)
            </p>
          </div>

          <!-- Location Consent & Status Action -->
          <div class="location-status-badge" [class.active]="locationService.consentStatus()">
            <div class="status-indicator">
              <span class="ping-circle" [class.pulsing]="locationService.consentStatus()"></span>
              <span class="status-text">
                {{ locationService.consentStatus() ? 'Location Sharing: ACTIVE' : 'Location Sharing: PAUSED' }}
              </span>
            </div>
            @if (!locationService.consentStatus()) {
              <button class="btn btn-sm btn-primary-outline" (click)="enableLocationSharing()">
                Enable Live Warning
              </button>
            } @else {
              <button class="btn btn-sm btn-ghost" (click)="refreshLocation()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M23 4v6h-6M1 20v-6h6"></path>
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                </svg>
                Sync GPS
              </button>
            }
          </div>
        </div>
      </div>

      <!-- Critical Hazard Banner if proximity warning exists -->
      @if (activeHazard()) {
        <div class="emergency-warning-card" [class.critical]="activeHazard()?.severity === 'CRITICAL'">
          <div class="warning-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </div>
          <div class="warning-details">
            <div class="warning-badge-row">
              <span class="hazard-level-badge">{{ activeHazard()?.severity }} ALERT</span>
              <span class="hazard-code font-mono">{{ activeHazard()?.alert_code }}</span>
            </div>
            <h3>{{ activeHazard()?.title }}</h3>
            <p>{{ activeHazard()?.message }}</p>
            <div class="safety-advice">
              <strong>Action:</strong> {{ activeHazard()?.safety_instructions }}
            </div>
          </div>
          <div class="warning-actions">
            <a routerLink="/safe-route" class="btn btn-accent">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="3 11 22 2 13 21 11 13 3 11"></polygon>
              </svg>
              Find Safer Route
            </a>
            <a routerLink="/flood-map" class="btn btn-outline">
              View on Map
            </a>
            <button class="btn btn-ghost" (click)="acknowledgeCurrentHazard()">
              Acknowledge
            </button>
          </div>
        </div>
      }

      <!-- Main Overview Grid -->
      <div class="dashboard-grid">
        <!-- Area Risk Gauge -->
        <div class="glass-card risk-summary-card">
          <div class="card-top">
            <h3>Local Flood Risk Gauge</h3>
            <span class="forecast-pill">AI Model Nowcast</span>
          </div>

          <div class="gauge-center">
            <app-risk-gauge [score]="currentRiskScore()"></app-risk-gauge>
          </div>

          <!-- Forecast Horizon Selection -->
          <div class="forecast-horizon-row">
            <span class="horizon-label">Forecast Horizon:</span>
            <div class="horizon-buttons">
              @for (h of horizons; track h.mins) {
                <button
                  type="button"
                  class="btn-horizon"
                  [class.active]="selectedHorizon() === h.mins"
                  (click)="setHorizon(h.mins)"
                >
                  {{ h.label }}
                </button>
              }
            </div>
          </div>

          <div class="card-footer-info">
            <div class="info-item">
              <span class="info-label">Water Inundation Depth:</span>
              <span class="info-val font-mono">{{ waterDepth() }} cm</span>
            </div>
            <div class="info-item">
              <span class="info-label">Rainfall Rate:</span>
              <span class="info-val font-mono">{{ rainRate() }} mm/h</span>
            </div>
            <div class="info-item">
              <span class="info-label">Tide Level:</span>
              <span class="info-val font-mono">3.82 m (Spring Tide)</span>
            </div>
          </div>
        </div>

        <!-- Quick Safety Actions & Location Privacy -->
        <div class="glass-card quick-actions-card">
          <div class="card-top">
            <h3>Citizen Safety Tools</h3>
          </div>

          <div class="tool-list">
            <!-- Safe Routing Action -->
            <a routerLink="/safe-route" class="tool-item safe-route-tool">
              <div class="tool-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
                </svg>
              </div>
              <div class="tool-texts">
                <strong>Flood-Safe Route Navigator</strong>
                <span>Find verified alternative roads that avoid submerged junctions</span>
              </div>
              <span class="arrow">→</span>
            </a>

            <!-- Ground Truth Feedback Action -->
            <button class="tool-item feedback-tool" (click)="showReportModal.set(true)">
              <div class="tool-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
              </div>
              <div class="tool-texts">
                <strong>Report Waterlogging Observation</strong>
                <span>Submit ground-truth water depth to help validate AI predictions</span>
              </div>
              <span class="arrow">+</span>
            </button>

            <!-- Privacy & Contacts -->
            <a routerLink="/citizen/privacy" class="tool-item privacy-tool">
              <div class="tool-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
              </div>
              <div class="tool-texts">
                <strong>Privacy & Emergency Contacts</strong>
                <span>Manage consent, purge location sessions, or add family contacts</span>
              </div>
              <span class="arrow">⚙</span>
            </a>
          </div>

          <!-- Emergency Helplines -->
          <div class="bmc-helplines">
            <span class="helpline-title">Mumbai Emergency Control Rooms</span>
            <div class="helpline-tags">
              <span class="helpline-pill">BMC Disaster: <strong>1916</strong></span>
              <span class="helpline-pill">Mumbai Police: <strong>100</strong></span>
              <span class="helpline-pill">Traffic Police: <strong>8454999999</strong></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Targeted Alerts Section -->
      <div class="alerts-section">
        <div class="section-header">
          <div class="title-wrap">
            <h2>Your Targeted Warning Notifications</h2>
            <p>Geospatially matched alerts based on your location and saved places</p>
          </div>
          <a routerLink="/citizen/my-alerts" class="link-all">View All Alerts ({{ alertService.alerts().length }}) →</a>
        </div>

        @if (alertService.alerts().length === 0) {
          <div class="empty-alerts">
            <div class="shield-check">✓</div>
            <h3>No Active Flood Warnings</h3>
            <p>Your current registered location (Dadar / Ward F/North) currently has normal drainage conditions.</p>
          </div>
        } @else {
          <div class="targeted-alerts-grid">
            @for (alert of alertService.alerts().slice(0, 3); track alert.id) {
              <div class="targeted-alert-card" [class.critical]="alert.severity === 'CRITICAL'" [class.high]="alert.severity === 'HIGH'">
                <div class="alert-top">
                  <span class="severity-badge" [class]="alert.severity.toLowerCase()">{{ alert.severity }}</span>
                  <span class="alert-ward">{{ alert.affected_ward }}</span>
                  <span class="alert-time">{{ alert.issued_at | date:'shortTime' }}</span>
                </div>
                <h4>{{ alert.title }}</h4>
                <p class="alert-msg">{{ alert.message }}</p>
                @if (alert.safety_instructions) {
                  <div class="alert-instructions">
                    <strong>Instructions:</strong> {{ alert.safety_instructions }}
                  </div>
                }
                <div class="alert-card-footer">
                  @if (alert.acknowledged_at) {
                    <span class="ack-status">✓ Acknowledged</span>
                  } @else {
                    <button class="btn btn-xs btn-outline" (click)="acknowledge(alert.id)">Acknowledge</button>
                  }
                  <a routerLink="/safe-route" class="safe-nav-link">Safe Route →</a>
                </div>
              </div>
            }
          </div>
        }
      </div>
    </div>

    <!-- Ground Truth Feedback Modal -->
    @if (showReportModal()) {
      <app-feedback-modal
        [initialArea]="currentAreaName()"
        (closed)="showReportModal.set(false)"
      ></app-feedback-modal>
    }
  `,
  styles: [`
    .citizen-dashboard {
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      max-width: 1400px;
      margin: 0 auto;
    }
    .dashboard-banner {
      background: linear-gradient(135deg, rgba(37, 99, 235, 0.15), rgba(14, 165, 233, 0.08));
      border: 1px solid rgba(59, 130, 246, 0.25);
      border-radius: 16px;
      padding: 1.5rem 2rem;
    }
    .banner-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .citizen-tag {
      font-size: 0.7rem;
      font-weight: 700;
      color: #60a5fa;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      display: block;
      margin-bottom: 0.3rem;
    }
    .banner-title-group h1 {
      font-size: 1.7rem;
      font-weight: 700;
      margin: 0 0 0.3rem 0;
    }
    .banner-subtitle {
      font-size: 0.9rem;
      color: var(--text-muted);
      margin: 0;
    }
    .location-status-badge {
      display: flex;
      align-items: center;
      gap: 1rem;
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 0.65rem 1rem;
      border-radius: 10px;
    }
    .status-indicator {
      display: flex;
      align-items: center;
      gap: 0.55rem;
    }
    .ping-circle {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #94a3b8;
    }
    .ping-circle.pulsing {
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
      animation: pulse 2s infinite;
    }
    .status-text {
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--text-main);
    }
    .emergency-warning-card {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.16), rgba(245, 158, 11, 0.12));
      border: 1px solid rgba(239, 68, 68, 0.4);
      border-radius: 14px;
      padding: 1.4rem 1.6rem;
      display: flex;
      align-items: flex-start;
      gap: 1.4rem;
      box-shadow: 0 8px 24px rgba(239, 68, 68, 0.15);
      flex-wrap: wrap;
    }
    .emergency-warning-card.critical {
      border-color: #ef4444;
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(185, 28, 28, 0.2));
    }
    .warning-icon {
      color: #ef4444;
      background: rgba(239, 68, 68, 0.15);
      padding: 0.75rem;
      border-radius: 12px;
    }
    .warning-details {
      flex: 1;
      min-width: 280px;
    }
    .warning-badge-row {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      margin-bottom: 0.4rem;
    }
    .hazard-level-badge {
      font-size: 0.72rem;
      font-weight: 700;
      background: #ef4444;
      color: white;
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
    }
    .hazard-code {
      font-size: 0.74rem;
      color: var(--text-dim);
    }
    .warning-details h3 {
      font-size: 1.2rem;
      margin: 0 0 0.35rem 0;
      color: #fca5a5;
    }
    .warning-details p {
      font-size: 0.88rem;
      color: var(--text-main);
      margin: 0 0 0.5rem 0;
      line-height: 1.4;
    }
    .safety-advice {
      font-size: 0.82rem;
      color: #fef08a;
      background: rgba(0, 0, 0, 0.25);
      padding: 0.4rem 0.8rem;
      border-radius: 6px;
      display: inline-block;
    }
    .warning-actions {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      min-width: 170px;
    }
    .dashboard-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }
    @media (max-width: 900px) {
      .dashboard-grid {
        grid-template-columns: 1fr;
      }
    }
    .glass-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      padding: 1.5rem;
    }
    .card-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.2rem;
    }
    .card-top h3 {
      font-size: 1.15rem;
      font-weight: 600;
      margin: 0;
    }
    .forecast-pill {
      font-size: 0.7rem;
      font-weight: 600;
      color: #38bdf8;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
    }
    .gauge-center {
      display: flex;
      justify-content: center;
      padding: 0.5rem 0;
    }
    .forecast-horizon-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin: 1.2rem 0;
      padding: 0.6rem 0.8rem;
      background: rgba(0, 0, 0, 0.25);
      border-radius: 8px;
    }
    .horizon-label {
      font-size: 0.82rem;
      color: var(--text-dim);
    }
    .horizon-buttons {
      display: flex;
      gap: 0.4rem;
    }
    .btn-horizon {
      padding: 0.3rem 0.6rem;
      font-size: 0.75rem;
      font-weight: 600;
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.05);
      color: var(--text-muted);
      border: 1px solid rgba(255, 255, 255, 0.08);
      cursor: pointer;
    }
    .btn-horizon.active {
      background: #2563eb;
      color: white;
      border-color: #3b82f6;
    }
    .card-footer-info {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.8rem;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      padding-top: 1rem;
    }
    .info-item {
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
    }
    .info-label {
      font-size: 0.72rem;
      color: var(--text-dim);
    }
    .info-val {
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--text-main);
    }
    .tool-list {
      display: flex;
      flex-direction: column;
      gap: 0.8rem;
      margin-bottom: 1.5rem;
    }
    .tool-item {
      display: flex;
      align-items: center;
      gap: 1rem;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.07);
      padding: 1rem 1.1rem;
      border-radius: 10px;
      text-decoration: none;
      color: var(--text-main);
      text-align: left;
      cursor: pointer;
      transition: all 0.2s;
    }
    .tool-item:hover {
      background: rgba(255, 255, 255, 0.06);
      border-color: rgba(255, 255, 255, 0.15);
      transform: translateY(-1px);
    }
    .tool-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(37, 99, 235, 0.15);
      color: #60a5fa;
    }
    .feedback-tool .tool-icon {
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
    }
    .privacy-tool .tool-icon {
      background: rgba(147, 51, 234, 0.15);
      color: #c084fc;
    }
    .tool-texts {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
    }
    .tool-texts strong {
      font-size: 0.9rem;
    }
    .tool-texts span {
      font-size: 0.78rem;
      color: var(--text-dim);
    }
    .arrow {
      font-size: 1.1rem;
      color: var(--text-dim);
    }
    .bmc-helplines {
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      padding-top: 1rem;
    }
    .helpline-title {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      display: block;
      margin-bottom: 0.5rem;
    }
    .helpline-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    .helpline-pill {
      font-size: 0.78rem;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 0.3rem 0.6rem;
      border-radius: 6px;
      color: var(--text-muted);
    }
    .alerts-section {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      padding: 1.5rem;
    }
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.2rem;
    }
    .section-header h2 {
      font-size: 1.2rem;
      margin: 0 0 0.2rem 0;
    }
    .section-header p {
      font-size: 0.8rem;
      color: var(--text-dim);
      margin: 0;
    }
    .link-all {
      font-size: 0.82rem;
      color: #60a5fa;
      text-decoration: none;
      font-weight: 500;
    }
    .empty-alerts {
      text-align: center;
      padding: 2.5rem 1rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.6rem;
    }
    .shield-check {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      font-size: 1.4rem;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
    }
    .empty-alerts h3 {
      font-size: 1.1rem;
      margin: 0;
    }
    .empty-alerts p {
      font-size: 0.84rem;
      color: var(--text-dim);
      max-width: 460px;
      margin: 0;
    }
    .targeted-alerts-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 1rem;
    }
    .targeted-alert-card {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 10px;
      padding: 1.1rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .targeted-alert-card.high {
      border-color: rgba(245, 158, 11, 0.4);
      background: rgba(245, 158, 11, 0.03);
    }
    .targeted-alert-card.critical {
      border-color: rgba(239, 68, 68, 0.4);
      background: rgba(239, 68, 68, 0.04);
    }
    .alert-top {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.72rem;
    }
    .severity-badge {
      font-weight: 700;
      padding: 0.1rem 0.45rem;
      border-radius: 4px;
      text-transform: uppercase;
    }
    .severity-badge.critical { background: #ef4444; color: white; }
    .severity-badge.high { background: #f59e0b; color: #1e1e1e; }
    .severity-badge.medium { background: #eab308; color: #1e1e1e; }
    .severity-badge.low { background: #3b82f6; color: white; }
    .severity-badge.safe { background: #10b981; color: white; }
    .alert-ward {
      color: var(--text-dim);
    }
    .alert-time {
      margin-left: auto;
      color: var(--text-dim);
    }
    .targeted-alert-card h4 {
      font-size: 0.96rem;
      margin: 0;
    }
    .alert-msg {
      font-size: 0.82rem;
      color: var(--text-muted);
      margin: 0;
      line-height: 1.4;
    }
    .alert-instructions {
      font-size: 0.78rem;
      color: #93c5fd;
      background: rgba(37, 99, 235, 0.08);
      padding: 0.4rem 0.6rem;
      border-radius: 6px;
    }
    .alert-card-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 0.4rem;
      padding-top: 0.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
    }
    .ack-status {
      font-size: 0.75rem;
      color: #10b981;
      font-weight: 600;
    }
    .safe-nav-link {
      font-size: 0.78rem;
      color: #60a5fa;
      text-decoration: none;
      font-weight: 500;
    }
    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
      70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
      100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
  `]
})
export class CitizenDashboardComponent implements OnInit, OnDestroy {
  currentAreaName = signal<string>('Dadar TT / Hindmata Junction');
  currentRiskScore = signal<number>(76);
  currentRiskLevel = signal<string>('HIGH');
  waterDepth = signal<number>(24);
  rainRate = signal<number>(45.2);
  selectedHorizon = signal<number>(15);

  horizons = [
    { mins: 0, label: 'Now' },
    { mins: 15, label: '+15 min' },
    { mins: 30, label: '+30 min' },
    { mins: 45, label: '+45 min' },
    { mins: 60, label: '+60 min' }
  ];

  activeHazard = signal<TargetedAlert | null>(null);
  showReportModal = signal<boolean>(false);

  constructor(
    public authService: AuthService,
    public locationService: CitizenLocationService,
    public alertService: CitizenAlertService,
    private floodService: FloodService
  ) {}

  ngOnInit(): void {
    this.alertService.fetchMyAlerts().subscribe(alerts => {
      const hazard = alerts.find(a => (a.severity === 'CRITICAL' || a.severity === 'HIGH') && !a.acknowledged_at);
      this.activeHazard.set(hazard || null);
    });
  }

  ngOnDestroy(): void {}

  enableLocationSharing(): void {
    this.locationService.requestBrowserLocation()
      .then(() => {
        this.locationService.updateConsent(true).subscribe();
        this.alertService.fetchMyAlerts().subscribe();
      })
      .catch(() => {
        // Fallback to update consent anyway
        this.locationService.updateConsent(true).subscribe();
      });
  }

  refreshLocation(): void {
    this.locationService.requestBrowserLocation().then(() => {
      this.alertService.fetchMyAlerts().subscribe();
    });
  }

  setHorizon(mins: number): void {
    this.selectedHorizon.set(mins);
    if (mins === 0) {
      this.currentRiskScore.set(62);
      this.waterDepth.set(16);
      this.currentRiskLevel.set('CAUTION');
    } else if (mins === 15) {
      this.currentRiskScore.set(76);
      this.waterDepth.set(24);
      this.currentRiskLevel.set('HIGH');
    } else if (mins === 30) {
      this.currentRiskScore.set(84);
      this.waterDepth.set(32);
      this.currentRiskLevel.set('HIGH');
    } else if (mins === 45) {
      this.currentRiskScore.set(89);
      this.waterDepth.set(38);
      this.currentRiskLevel.set('CRITICAL');
    } else {
      this.currentRiskScore.set(92);
      this.waterDepth.set(45);
      this.currentRiskLevel.set('CRITICAL');
    }
  }

  acknowledge(alertId: number): void {
    this.alertService.acknowledgeAlert(alertId).subscribe();
  }

  acknowledgeCurrentHazard(): void {
    const hazard = this.activeHazard();
    if (hazard) {
      this.acknowledge(hazard.id);
      this.activeHazard.set(null);
    }
  }
}
