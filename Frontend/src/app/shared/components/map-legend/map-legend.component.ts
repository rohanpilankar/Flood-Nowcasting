import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-map-legend',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="map-legend-card">
      <div class="legend-header">
        <span class="legend-title">Flood Risk Legend</span>
      </div>
      <div class="legend-items">
        <div class="legend-item">
          <span class="color-dot risk-safe"></span>
          <div class="legend-meta">
            <span class="legend-name">Safe / Minimal</span>
            <span class="legend-depth">&lt; 0.05m depth</span>
          </div>
        </div>
        <div class="legend-item">
          <span class="color-dot risk-low"></span>
          <div class="legend-meta">
            <span class="legend-name">Low Risk</span>
            <span class="legend-depth">0.05 - 0.15m depth</span>
          </div>
        </div>
        <div class="legend-item">
          <span class="color-dot risk-medium"></span>
          <div class="legend-meta">
            <span class="legend-name">Medium / Caution</span>
            <span class="legend-depth">0.15 - 0.30m depth</span>
          </div>
        </div>
        <div class="legend-item">
          <span class="color-dot risk-high"></span>
          <div class="legend-meta">
            <span class="legend-name">High Flood Danger</span>
            <span class="legend-depth">0.30 - 0.50m depth</span>
          </div>
        </div>
        <div class="legend-item">
          <span class="color-dot risk-critical"></span>
          <div class="legend-meta">
            <span class="legend-name">Unsafe / Impassable</span>
            <span class="legend-depth">&gt; 0.50m depth</span>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .map-legend-card {
      background-color: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 0.85rem;
      box-shadow: var(--shadow-md);
      font-size: 0.78rem;
    }
    .legend-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 0.6rem;
      padding-bottom: 0.4rem;
      border-bottom: 1px solid var(--border-light);
    }
    .legend-title {
      font-weight: 600;
      color: var(--text-main);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .legend-items {
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }
    .color-dot {
      width: 14px;
      height: 14px;
      border-radius: 3px;
      flex-shrink: 0;
    }
    .legend-meta {
      display: flex;
      justify-content: space-between;
      width: 100%;
      gap: 0.5rem;
    }
    .legend-name {
      color: var(--text-main);
      font-weight: 500;
    }
    .legend-depth {
      color: var(--text-muted);
      font-size: 0.72rem;
    }
  `]
})
export class MapLegendComponent {}
