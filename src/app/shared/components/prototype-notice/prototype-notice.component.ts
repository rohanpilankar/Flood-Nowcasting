import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-prototype-notice',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div [class]="expanded ? 'prototype-banner-expanded' : 'prototype-banner-compact'">
      <div class="notice-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
      </div>
      <div class="notice-content">
        @if (expanded) {
          <h4 class="notice-title">SIH26085 Prototype Notice & Disclaimer</h4>
          <p class="notice-desc">
            FloodWatch AI Phase 1 uses simulated data streams and mock AI predictions for system evaluation. 
            All rainfall figures, water depths, elevation indices, and ML confidence scores are prototype values for demonstration. 
            This is not an official municipal or emergency flood warning system. Phase 2 introduces verified IMD radar feeds, 
            IoT telemetry, and trained XGBoost models.
          </p>
        } @else {
          <p class="notice-compact-text">
            <strong>Prototype Notice:</strong> Phase 1 simulated data for demonstration only. Not an official flood alert system.
          </p>
        }
      </div>
    </div>
  `,
  styles: [`
    .prototype-banner-compact {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      padding: 0.35rem 0.85rem;
      background-color: rgba(99, 102, 241, 0.1);
      border: 1px solid rgba(99, 102, 241, 0.25);
      border-radius: var(--radius-sm);
      font-size: 0.76rem;
      color: #c7d2fe;
    }
    .prototype-banner-expanded {
      display: flex;
      gap: 1rem;
      padding: 1.1rem 1.3rem;
      background-color: rgba(30, 41, 59, 0.8);
      border: 1px solid rgba(99, 102, 241, 0.35);
      border-left: 4px solid #6366f1;
      border-radius: var(--radius-md);
      color: var(--text-main);
    }
    .notice-icon {
      color: #818cf8;
      display: flex;
      align-items: center;
      flex-shrink: 0;
    }
    .notice-title {
      font-size: 0.95rem;
      font-weight: 600;
      color: #e0e7ff;
      margin-bottom: 0.35rem;
    }
    .notice-desc {
      font-size: 0.825rem;
      color: #94a3b8;
      line-height: 1.5;
    }
    .notice-compact-text {
      margin: 0;
      line-height: 1.3;
    }
  `]
})
export class PrototypeNoticeComponent {
  @Input() expanded = false;
}
