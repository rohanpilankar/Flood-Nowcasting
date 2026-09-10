import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EocDataService } from '../services/eoc-data.service';

@Component({
  selector: 'app-eoc-telemetry-strip',
  standalone: true,
  imports: [CommonModule],
  template: `
    <section class="strip" aria-label="Live telemetry">
      @for (card of cards(); track card.label) {
        <div class="tcard" [class]="card.tone">
          <span class="tl">{{ card.label }}</span>
          <strong class="tv">{{ card.value }}</strong>
          <span class="ts">{{ card.sub }}</span>
        </div>
      }
    </section>
  `,
  styles: [`
    .strip {
      display: grid; grid-template-columns: repeat(6, 1fr); gap: 0.6rem;
      padding: 0.7rem 1.25rem 0;
    }
    .tcard {
      background: rgba(15,23,42,0.75); border: 1px solid rgba(148,163,184,0.16);
      border-left: 3px solid #38bdf8; border-radius: 8px; padding: 0.55rem 0.75rem;
      display: flex; flex-direction: column; gap: 0.1rem; backdrop-filter: blur(8px);
    }
    .tcard.warn { border-left-color: #fbbf24; }
    .tcard.bad { border-left-color: #f87171; }
    .tcard.ok { border-left-color: #34d399; }
    .tl { font-size: 0.58rem; font-weight: 800; letter-spacing: 0.14em; color: #64748b; }
    .tv { font-family: ui-monospace, SFMono-Regular, monospace; font-size: 1.25rem; color: #f1f5f9; line-height: 1.1; }
    .ts { font-size: 0.62rem; color: #94a3b8; }
    @media (max-width: 1100px) { .strip { grid-template-columns: repeat(3, 1fr); } }
    @media (max-width: 640px) { .strip { grid-template-columns: repeat(2, 1fr); } }
  `]
})
export class EocTelemetryStripComponent {
  readonly store = inject(EocDataService);

  cards() {
    const t = this.store.telemetry();
    return [
      { label: 'RADAR NOWCAST', value: `${t.radarNowcastMmh.toFixed(1)} mm/h`, sub: 'Current intensity', tone: '' },
      { label: 'PEAK NOWCAST', value: `${t.peakNowcastMmh.toFixed(1)} mm/h`, sub: `Predicted peak ${t.predictedPeakAt}`, tone: 'warn' },
      { label: 'DRAINAGE LOAD', value: `${t.drainageLoadPct}%`, sub: `${t.surchargeNodes} / ${t.totalNodes} surcharged`, tone: 'bad' },
      { label: 'SURCHARGE NODES', value: `${t.surchargeNodes} / ${t.totalNodes}`, sub: 'Hydraulic overload', tone: 'bad' },
      { label: 'FLOODED ROAD SEGMENTS', value: `${t.floodedRoads}`, sub: 'Closed + restricted', tone: 'warn' },
      { label: 'ACTIVE INCIDENTS', value: `${t.activeIncidents}`, sub: 'Open + responding', tone: 'ok' },
    ];
  }
}
