import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FloodAlert } from '../../../core/models/alert.model';
import { RiskBadgeComponent } from '../risk-badge/risk-badge.component';

@Component({
  selector: 'app-alert-card',
  standalone: true,
  imports: [CommonModule, RiskBadgeComponent],
  template: `
    <div class="alert-card" [class.acknowledged]="alert.acknowledged" [ngClass]="severityClass">
      <div class="alert-top">
        <div class="alert-header-left">
          <app-risk-badge [level]="alert.severity" [customText]="alert.severity + ' PRIORITY'"></app-risk-badge>
          <span class="alert-id font-mono">#{{ alert.id }}</span>
          @if (alert.acknowledged) {
            <span class="badge status-safe">Acknowledged</span>
          }
        <div class="alert-top-right">
          <span class="alert-time">{{ alert.generatedTime }}</span>
          <button
            type="button"
            class="alert-dismiss-btn"
            (click)="dismiss.emit(alert.id)"
            title="Dismiss alert"
            aria-label="Dismiss alert"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>

      <h4 class="alert-location">{{ alert.location }}</h4>
      <p class="alert-desc">{{ alert.description }}</p>

      <div class="alert-meta-grid">
        <div class="meta-col">
          <span class="meta-label">Prototype Risk</span>
          <span class="meta-val font-mono" [style.color]="scoreColor">{{ alert.riskScore }}%</span>
        </div>
        <div class="meta-col">
          <span class="meta-label">Horizon</span>
          <span class="meta-val">{{ alert.predictionHorizon }}</span>
        </div>
        <div class="meta-col">
          <span class="meta-label">AI Confidence</span>
          <span class="meta-val">{{ alert.aiConfidence }}%</span>
        </div>
      </div>

      @if (alert.recommendedAction) {
        <div class="action-advisory">
          <span class="advisory-title">Recommended Action:</span>
          <span class="advisory-text">{{ alert.recommendedAction }}</span>
        </div>
      }

      <div class="alert-actions">
        <button type="button" class="btn btn-secondary btn-sm" (click)="viewLocation.emit(alert)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
            <circle cx="12" cy="10" r="3"></circle>
          </svg>
          View Location
        </button>
        <button
          type="button"
          class="btn btn-sm"
          [class.btn-outline]="alert.acknowledged"
          [class.btn-primary]="!alert.acknowledged"
          (click)="acknowledge.emit(alert.id)"
        >
          {{ alert.acknowledged ? 'Re-open Alert' : 'Acknowledge' }}
        </button>
      </div>
    </div>
  `,
  styles: [`
    .alert-card {
      background-color: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 1rem;
      box-shadow: var(--shadow-sm);
      display: flex;
      flex-direction: column;
      gap: 0.65rem;
      transition: all var(--transition-fast);

      &:hover {
        border-color: rgba(148, 163, 184, 0.3);
      }
      &.acknowledged {
        opacity: 0.72;
        background-color: rgba(30, 41, 59, 0.4);
      }
    }
    .alert-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
    }
    .alert-top-right {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .alert-dismiss-btn {
      width: 22px;
      height: 22px;
      border-radius: var(--radius-sm);
      color: var(--text-dim);
      background: transparent;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all var(--transition-fast);
      &:hover {
        color: var(--status-critical);
        background-color: rgba(239, 68, 68, 0.12);
      }
    }
    .alert-header-left {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .alert-id {
      font-size: 0.75rem;
      color: var(--text-dim);
    }
    .alert-time {
      font-size: 0.72rem;
      color: var(--text-muted);
    }
    .alert-location {
      font-size: 1.05rem;
      font-weight: 600;
      color: var(--text-main);
      margin: 0;
    }
    .alert-desc {
      font-size: 0.835rem;
      color: var(--text-muted);
      line-height: 1.45;
      margin: 0;
    }
    .alert-meta-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.5rem 0.65rem;
      gap: 0.5rem;
    }
    .meta-col {
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
      font-size: 0.875rem;
      font-weight: 600;
      color: var(--text-main);
    }
    .action-advisory {
      font-size: 0.78rem;
      background-color: rgba(59, 130, 246, 0.08);
      border-left: 3px solid var(--brand-primary);
      padding: 0.4rem 0.6rem;
      border-radius: 2px;
      line-height: 1.4;
    }
    .advisory-title {
      font-weight: 600;
      color: #93c5fd;
      margin-right: 0.35rem;
    }
    .advisory-text {
      color: var(--text-main);
    }
    .alert-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-top: 0.2rem;
    }
  `]
})
export class AlertCardComponent {
  @Input() alert!: FloodAlert;
  @Output() viewLocation = new EventEmitter<FloodAlert>();
  @Output() acknowledge = new EventEmitter<string>();
  @Output() dismiss = new EventEmitter<string>();

  get severityClass(): string {
    if (this.alert.severity === 'HIGH') return 'border-high';
    if (this.alert.severity === 'MEDIUM') return 'border-medium';
    return 'border-low';
  }

  get scoreColor(): string {
    if (this.alert.riskScore >= 80) return '#ef4444';
    if (this.alert.riskScore >= 50) return '#f59e0b';
    return '#10b981';
  }
}
