import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RiskLevel } from '../../../core/models/flood-risk.model';

@Component({
  selector: 'app-risk-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <span class="badge" [ngClass]="badgeClass">
      <span class="indicator-dot"></span>
      {{ label }}
    </span>
  `,
  styles: [`
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.22rem 0.6rem;
      border-radius: var(--radius-sm);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .indicator-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background-color: currentColor;
    }
  `]
})
export class RiskBadgeComponent {
  @Input() level: RiskLevel | string = 'LOW';
  @Input() customText?: string;

  get badgeClass(): string {
    const l = (this.level || '').toUpperCase();
    if (l === 'NONE' || l === 'SAFE' || l === 'NO_RISK') return 'risk-safe';
    if (l === 'LOW') return 'risk-low';
    if (l === 'MEDIUM' || l === 'CAUTION') return 'risk-medium';
    if (l === 'HIGH' || l === 'UNSAFE') return 'risk-high';
    if (l === 'CRITICAL' || l === 'SEVERE') return 'risk-critical';
    return 'risk-low';
  }

  get label(): string {
    if (this.customText) return this.customText;
    const l = (this.level || '').toUpperCase();
    if (l === 'NONE' || l === 'SAFE' || l === 'NO_RISK') return 'Safe / No Risk';
    if (l === 'LOW') return 'Low Risk';
    if (l === 'MEDIUM' || l === 'CAUTION') return 'Medium Risk';
    if (l === 'HIGH') return 'High Flood Risk';
    if (l === 'CRITICAL' || l === 'UNSAFE') return 'Critical Unsafe';
    return this.level;
  }
}
