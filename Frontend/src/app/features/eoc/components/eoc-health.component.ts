import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EocDataService } from '../services/eoc-data.service';

@Component({
  selector: 'app-eoc-health',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="health-grid">
      <div class="panel">
        <h3>SYSTEM HEALTH</h3>
        <p class="sub">Sensors · models · APIs · {{ store.dataMode() }}</p>
        @for (c of store.health(); track c.id) {
          <div class="check">
            <span class="cdot" [class]="c.status.toLowerCase()"></span>
            <span class="clabel"><strong>{{ c.label }}</strong><em>{{ c.detail }}</em></span>
            <span class="cstat" [class]="c.status.toLowerCase()">{{ c.status }}</span>
          </div>
        }
      </div>
      <div class="panel">
        <h3>OPERATIONAL TELEMETRY</h3>
        <p class="sub">Pipeline timing</p>
        <div class="tgrid">
          <div><em>Last model update</em><b>{{ store.now() | date:'HH:mm:ss' }}</b></div>
          <div><em>Data latency</em><b>42 s</b></div>
          <div><em>Model inference</em><b>38 ms</b></div>
          <div><em>API health</em><b>{{ store.dataMode() === 'LIVE' ? 'OK' : 'SIM (offline)' }}</b></div>
          <div><em>Radar sweep</em><b>6 min cycle</b></div>
          <div><em>AWS stations</em><b>64 reporting</b></div>
        </div>
        <p class="fine">Inference timing reflects the surrogate nowcaster baseline. Values marked SIM are illustrative until live feeds connect.</p>
      </div>
    </div>
  `,
  styles: [`
    .health-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 0.75rem; }
    .panel { background: rgba(15,23,42,0.75); border: 1px solid rgba(56,189,248,0.18); border-radius: 12px; padding: 1rem 1.1rem; }
    h3 { margin: 0; font-size: 0.85rem; letter-spacing: 0.1em; color: #f1f5f9; }
    .sub, .fine { font-size: 0.66rem; color: #64748b; margin: 0.15rem 0 0.7rem; }
    .check { display: flex; align-items: center; gap: 0.7rem; padding: 0.55rem 0; border-bottom: 1px solid rgba(148,163,184,0.08); }
    .cdot { width: 10px; height: 10px; border-radius: 50%; flex: none; }
    .cdot.online { background: #34d399; box-shadow: 0 0 8px #34d399; }
    .cdot.degraded { background: #fbbf24; box-shadow: 0 0 8px #fbbf24; }
    .cdot.offline { background: #f87171; box-shadow: 0 0 8px #f87171; }
    .clabel { display: flex; flex-direction: column; flex: 1; }
    .clabel strong { font-size: 0.76rem; color: #f1f5f9; }
    .clabel em { font-style: normal; font-size: 0.64rem; color: #94a3b8; }
    .cstat { font-size: 0.6rem; font-weight: 800; letter-spacing: 0.1em; }
    .cstat.online { color: #34d399; } .cstat.degraded { color: #fbbf24; } .cstat.offline { color: #f87171; }
    .tgrid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
    .tgrid div { background: rgba(2,6,16,0.5); border-radius: 7px; padding: 0.55rem 0.65rem; display: flex; flex-direction: column; }
    .tgrid em { font-style: normal; font-size: 0.56rem; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; }
    .tgrid b { font-family: ui-monospace, monospace; font-size: 0.85rem; color: #f1f5f9; }
    @media (max-width: 1000px) { .health-grid { grid-template-columns: 1fr; } }
  `]
})
export class EocHealthComponent {
  readonly store = inject(EocDataService);
}
