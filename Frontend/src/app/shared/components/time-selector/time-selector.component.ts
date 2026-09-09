import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PredictionTime } from '../../../core/models/flood-risk.model';

@Component({
  selector: 'app-time-selector',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="time-selector-container">
      <span class="selector-label" *ngIf="showLabel">AI Forecast Horizon:</span>
      <div class="pill-group" role="group" aria-label="Prediction Time Horizon">
        @for (opt of options; track opt.value) {
          <button
            type="button"
            class="pill-btn"
            [class.active]="selected === opt.value"
            (click)="select(opt.value)"
            [attr.aria-pressed]="selected === opt.value"
          >
            {{ opt.label }}
          </button>
        }
      </div>
    </div>
  `,
  styles: [`
    .time-selector-container {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .selector-label {
      font-size: 0.75rem;
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .pill-group {
      display: inline-flex;
      background-color: var(--bg-darkest);
      padding: 3px;
      border-radius: var(--radius-full);
      border: 1px solid var(--border-subtle);
    }
    .pill-btn {
      padding: 0.32rem 0.85rem;
      font-size: 0.75rem;
      font-weight: 600;
      border-radius: var(--radius-full);
      color: var(--text-muted);
      letter-spacing: 0.04em;
      transition: all var(--transition-fast);

      &:hover {
        color: var(--text-main);
      }
      &.active {
        background-color: var(--brand-primary);
        color: #ffffff;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
      }
    }
  `]
})
export class TimeSelectorComponent {
  @Input() selected: PredictionTime = 'NOW';
  @Input() showLabel = true;
  @Input() fullLabels = false;
  @Output() horizonChange = new EventEmitter<PredictionTime>();

  get options(): { value: PredictionTime; label: string }[] {
    if (this.fullLabels) {
      return [
        { value: 'NOW', label: 'NOW' },
        { value: '+30M', label: '+30 MIN' },
        { value: '+1H', label: '+1 HOUR' },
        { value: '+2H', label: '+2 HOURS' },
        { value: '+3H', label: '+3 HOURS' }
      ];
    }
    return [
      { value: 'NOW', label: 'NOW' },
      { value: '+30M', label: '+30M' },
      { value: '+1H', label: '+1H' },
      { value: '+2H', label: '+2H' },
      { value: '+3H', label: '+3H' }
    ];
  }

  select(value: PredictionTime): void {
    if (this.selected !== value) {
      this.selected = value;
      this.horizonChange.emit(value);
    }
  }
}
