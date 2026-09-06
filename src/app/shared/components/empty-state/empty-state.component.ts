import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="empty-container">
      <div class="empty-icon-wrap">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="8" y1="12" x2="16" y2="12"></line>
        </svg>
      </div>
      <h4 class="empty-title">{{ title }}</h4>
      <p class="empty-desc">{{ description }}</p>
      @if (actionLabel) {
        <button type="button" class="btn btn-secondary btn-sm" (click)="action.emit()">
          {{ actionLabel }}
        </button>
      }
    </div>
  `,
  styles: [`
    .empty-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem 1.5rem;
      gap: 0.65rem;
      text-align: center;
      background-color: var(--bg-card);
      border: 1px dashed var(--border-subtle);
      border-radius: var(--radius-lg);
    }
    .empty-icon-wrap {
      color: var(--text-dim);
      margin-bottom: 0.25rem;
    }
    .empty-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-main);
    }
    .empty-desc {
      font-size: 0.85rem;
      color: var(--text-muted);
      max-width: 380px;
      line-height: 1.45;
    }
  `]
})
export class EmptyStateComponent {
  @Input() title = 'No data available';
  @Input() description = 'No active records match the current criteria.';
  @Input() actionLabel?: string;
  @Output() action = new EventEmitter<void>();
}
