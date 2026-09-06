import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-state',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="loading-container">
      <div class="spinner"></div>
      <p class="loading-message">{{ message }}</p>
      <span class="badge-prototype">Retrieving Prototype Stream...</span>
    </div>
  `,
  styles: [`
    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem 1.5rem;
      gap: 0.85rem;
      text-align: center;
    }
    .spinner {
      width: 38px;
      height: 38px;
      border: 3px solid rgba(59, 130, 246, 0.2);
      border-top-color: var(--brand-primary);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    .loading-message {
      font-size: 0.9rem;
      color: var(--text-muted);
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `]
})
export class LoadingStateComponent {
  @Input() message = 'Loading real-time flood intelligence...';
}
