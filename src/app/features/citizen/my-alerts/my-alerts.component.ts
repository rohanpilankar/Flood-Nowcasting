import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CitizenAlertService, TargetedAlert } from '../../../core/services/citizen-alert.service';

@Component({
  selector: 'app-my-alerts',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="my-alerts-page">
      <div class="page-header">
        <div>
          <span class="sub-tag">CITIZEN SAFETY ADVISORY</span>
          <h1>My Warning Alerts</h1>
          <p>Personalized notifications targeted to your registered and live location in Greater Mumbai</p>
        </div>
        <button class="btn btn-outline" (click)="refreshAlerts()">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6M1 20v-6h6"></path>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
          Refresh Feed
        </button>
      </div>

      <!-- Filters & Counter -->
      <div class="filter-strip">
        <div class="count-pill">
          <strong>{{ alertService.alerts().length }}</strong> Total Alerts
          @if (alertService.unreadCount() > 0) {
            <span class="unread-pill">{{ alertService.unreadCount() }} Pending</span>
          }
        </div>
      </div>

      <!-- Alerts List -->
      @if (alertService.alerts().length === 0) {
        <div class="glass-card empty-container">
          <div class="check-icon">✓</div>
          <h3>All Clear in Your Area</h3>
          <p>No high-risk flash flood warnings have been issued for your immediate vicinity at this time.</p>
        </div>
      } @else {
        <div class="alerts-stack">
          @for (alert of alertService.alerts(); track alert.id) {
            <div
              class="glass-card alert-entry"
              [class.critical]="alert.severity === 'CRITICAL'"
              [class.high]="alert.severity === 'HIGH'"
              [class.acknowledged]="!!alert.acknowledged_at"
            >
              <div class="entry-header">
                <div class="header-left">
                  <span class="severity-badge" [class]="alert.severity.toLowerCase()">{{ alert.severity }}</span>
                  <span class="ward-badge">{{ alert.affected_ward }}</span>
                  <span class="category-badge">{{ alert.flood_category }}</span>
                </div>
                <div class="header-right">
                  <span class="timestamp">{{ alert.issued_at | date:'medium' }}</span>
                </div>
              </div>

              <div class="entry-body">
                <h3>{{ alert.title }}</h3>
                <p class="message">{{ alert.message }}</p>

                @if (alert.safety_instructions) {
                  <div class="instructions-box">
                    <span class="box-title">Safety Instructions:</span>
                    <p>{{ alert.safety_instructions }}</p>
                  </div>
                }

                @if (alert.affected_landmarks && alert.affected_landmarks.length > 0) {
                  <div class="landmarks-row">
                    <span class="landmarks-label">Affected Landmarks:</span>
                    <div class="landmark-tags">
                      @for (lm of alert.affected_landmarks; track lm) {
                        <span class="landmark-tag">{{ lm }}</span>
                      }
                    </div>
                  </div>
                }
              </div>

              <div class="entry-footer">
                <div class="footer-left">
                  @if (alert.acknowledged_at) {
                    <span class="ack-label">✓ Acknowledged on {{ alert.acknowledged_at | date:'shortTime' }}</span>
                  } @else {
                    <button class="btn btn-sm btn-outline" (click)="acknowledge(alert.id)">
                      Acknowledge Warning
                    </button>
                  }
                </div>

                <div class="footer-right">
                  <a routerLink="/safe-route" class="btn btn-sm btn-primary">
                    Find Flood-Safe Route →
                  </a>
                </div>
              </div>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .my-alerts-page {
      padding: 1.5rem;
      max-width: 1100px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .sub-tag {
      font-size: 0.72rem;
      font-weight: 700;
      color: #60a5fa;
      letter-spacing: 0.08em;
    }
    .page-header h1 {
      font-size: 1.7rem;
      margin: 0.2rem 0;
    }
    .page-header p {
      font-size: 0.88rem;
      color: var(--text-muted);
      margin: 0;
    }
    .filter-strip {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .count-pill {
      font-size: 0.85rem;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .unread-pill {
      font-size: 0.72rem;
      background: #ef4444;
      color: white;
      padding: 0.1rem 0.5rem;
      border-radius: 9999px;
      font-weight: 600;
    }
    .alerts-stack {
      display: flex;
      flex-direction: column;
      gap: 1.2rem;
    }
    .glass-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      padding: 1.5rem;
    }
    .alert-entry {
      border-left: 4px solid var(--border-subtle);
      transition: all 0.2s;
    }
    .alert-entry.critical {
      border-left-color: #ef4444;
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.08), var(--bg-card));
    }
    .alert-entry.high {
      border-left-color: #f59e0b;
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.06), var(--bg-card));
    }
    .entry-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.8rem;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    .header-left {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .severity-badge {
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      text-transform: uppercase;
    }
    .severity-badge.critical { background: #ef4444; color: white; }
    .severity-badge.high { background: #f59e0b; color: #1e1e1e; }
    .severity-badge.medium { background: #eab308; color: #1e1e1e; }
    .severity-badge.low { background: #3b82f6; color: white; }
    .ward-badge, .category-badge {
      font-size: 0.72rem;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      color: var(--text-dim);
    }
    .timestamp {
      font-size: 0.78rem;
      color: var(--text-dim);
    }
    .entry-body h3 {
      font-size: 1.15rem;
      margin: 0 0 0.4rem 0;
    }
    .entry-body .message {
      font-size: 0.88rem;
      color: var(--text-muted);
      line-height: 1.45;
      margin: 0 0 0.8rem 0;
    }
    .instructions-box {
      background: rgba(0, 0, 0, 0.25);
      border-left: 3px solid #3b82f6;
      padding: 0.65rem 0.85rem;
      border-radius: 0 8px 8px 0;
      margin-bottom: 0.8rem;
    }
    .box-title {
      font-size: 0.76rem;
      font-weight: 600;
      color: #93c5fd;
      display: block;
      margin-bottom: 0.2rem;
    }
    .instructions-box p {
      font-size: 0.82rem;
      color: var(--text-main);
      margin: 0;
    }
    .landmarks-row {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      flex-wrap: wrap;
    }
    .landmarks-label {
      font-size: 0.76rem;
      color: var(--text-dim);
    }
    .landmark-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
    }
    .landmark-tag {
      font-size: 0.72rem;
      background: rgba(255, 255, 255, 0.04);
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      color: var(--text-muted);
    }
    .entry-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 1rem;
      padding-top: 0.8rem;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
    }
    .ack-label {
      font-size: 0.78rem;
      color: #10b981;
      font-weight: 600;
    }
    .empty-container {
      text-align: center;
      padding: 3.5rem 1rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.8rem;
    }
    .check-icon {
      width: 52px;
      height: 52px;
      border-radius: 50%;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      font-size: 1.6rem;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
    }
  `]
})
export class MyAlertsComponent implements OnInit {
  constructor(public alertService: CitizenAlertService) {}

  ngOnInit(): void {
    this.alertService.fetchMyAlerts().subscribe();
  }

  refreshAlerts(): void {
    this.alertService.fetchMyAlerts().subscribe();
  }

  acknowledge(alertId: number): void {
    this.alertService.acknowledgeAlert(alertId).subscribe();
  }
}
