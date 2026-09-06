import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-stat-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="card stat-card" [ngClass]="semanticClass">
      <div class="stat-top">
        <span class="stat-title">{{ title }}</span>
        <div class="stat-icon-wrap" [ngClass]="semanticClass">
          <ng-content select="[icon]"></ng-content>
        </div>
      </div>
      
      <div class="stat-value-row">
        <span class="stat-value">{{ value }}</span>
        @if (unit) {
          <span class="stat-unit">{{ unit }}</span>
        }
      </div>

      <div class="stat-footer">
        @if (delta) {
          <span class="stat-delta">{{ delta }}</span>
        }
        <span class="badge-prototype">Simulated</span>
      </div>
    </div>
  `,
  styles: [`
    .stat-card {
      position: relative;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 140px;
    }
    .stat-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 0.5rem;
    }
    .stat-title {
      font-size: 0.8125rem;
      font-weight: 500;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .stat-icon-wrap {
      width: 36px;
      height: 36px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
    }
    .stat-value-row {
      display: flex;
      align-items: baseline;
      gap: 0.35rem;
      margin: 0.75rem 0 0.4rem 0;
    }
    .stat-value {
      font-family: 'Outfit', sans-serif;
      font-size: 2rem;
      font-weight: 700;
      color: var(--text-main);
      line-height: 1;
    }
    .stat-unit {
      font-size: 0.95rem;
      color: var(--text-muted);
      font-weight: 500;
    }
    .stat-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      margin-top: 0.25rem;
    }
    .stat-delta {
      font-size: 0.75rem;
      color: var(--text-muted);
      font-weight: 500;
    }
  `]
})
export class StatCardComponent {
  @Input() title!: string;
  @Input() value!: string | number;
  @Input() unit?: string;
  @Input() delta?: string;
  @Input() statusType: 'safe' | 'caution' | 'unsafe' | 'info' = 'info';

  get semanticClass(): string {
    switch (this.statusType) {
      case 'safe': return 'status-safe';
      case 'caution': return 'status-caution';
      case 'unsafe': return 'status-unsafe';
      default: return 'status-info';
    }
  }
}
