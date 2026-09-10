import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EocDataService } from '../services/eoc-data.service';
import { Severity } from '../models/eoc-models';

@Component({
  selector: 'app-eoc-incidents',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="sum-grid">
      <div class="scard"><span>TOTAL ACTIVE INCIDENTS</span><strong>{{ store.incidents().length }}</strong></div>
      <div class="scard bad"><span>CRITICAL FLASH FLOODS</span><strong>{{ count('CRITICAL') }}</strong></div>
      <div class="scard warn"><span>EARLY WARNINGS</span><strong>{{ count('WARNING') }}</strong></div>
      <div class="scard ok"><span>ACOUSTIC SIREN GRID</span><strong>STANDBY</strong></div>
    </div>

    <div class="panel">
      <div class="p-head">
        <div><h3>LIVE INCIDENT CHRONOLOGY</h3><p>Newest first · {{ store.dataMode() }} data</p></div>
        <div class="filter">
          @for (f of filters; track f) {
            <button type="button" [class.on]="filter() === f" (click)="filter.set(f)">{{ f }}</button>
          }
        </div>
      </div>
      <div class="chron">
        @for (i of visible(); track i.id) {
          <div class="inc" [class]="i.severity.toLowerCase()">
            <div class="inc-top">
              <span class="sev">{{ i.severity }}</span>
              <span class="iid">{{ i.id }}</span>
              <span class="time">{{ i.issuedAt | date:'HH:mm' }}</span>
              <span class="st">{{ i.status }}</span>
            </div>
            <strong>{{ i.location }}</strong>
            <span class="ward">{{ i.ward }}</span>
            <p>{{ i.description }}</p>
            <div class="inc-meta">Depth <b>{{ i.waterDepthCm }} cm</b> · Expected <b>{{ i.expectedAt }}</b></div>
            <div class="inc-actions">
              @if (!store.acknowledgedIds().has(i.id)) {
                <button type="button" class="btn-ack" (click)="store.acknowledgeIncident(i.id)">{{ i.actionLabel | uppercase }}</button>
              } @else {
                <span class="acked">✓ ACKNOWLEDGED</span>
              }
              <button type="button" class="btn-loc" (click)="locate(i.id)">VIEW LOCATION</button>
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .sum-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.6rem; margin-bottom: 0.75rem; }
    .scard { background: rgba(15,23,42,0.75); border: 1px solid rgba(148,163,184,0.16); border-left: 3px solid #38bdf8; border-radius: 8px; padding: 0.6rem 0.8rem; display: flex; flex-direction: column; gap: 0.15rem; }
    .scard.bad { border-left-color: #f87171; } .scard.warn { border-left-color: #fbbf24; } .scard.ok { border-left-color: #34d399; }
    .scard span { font-size: 0.58rem; font-weight: 800; letter-spacing: 0.12em; color: #64748b; }
    .scard strong { font-family: ui-monospace, monospace; font-size: 1.4rem; color: #f1f5f9; }
    .panel { background: rgba(15,23,42,0.75); border: 1px solid rgba(56,189,248,0.18); border-radius: 12px; padding: 1rem 1.1rem; }
    .p-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.7rem; }
    h3 { margin: 0; font-size: 0.85rem; letter-spacing: 0.1em; color: #f1f5f9; }
    .p-head p { font-size: 0.66rem; color: #64748b; margin: 0.15rem 0 0; }
    .filter { display: flex; gap: 0.3rem; }
    .filter button { background: transparent; border: 1px solid #334155; color: #94a3b8; font-size: 0.6rem; font-weight: 700; border-radius: 6px; padding: 0.25rem 0.55rem; cursor: pointer; }
    .filter button.on { color: #22d3ee; border-color: #0ea5e9; }
    .chron { display: flex; flex-direction: column; gap: 0.55rem; max-height: 480px; overflow-y: auto; }
    .inc { background: rgba(2,6,16,0.5); border: 1px solid rgba(148,163,184,0.14); border-left: 3px solid #38bdf8; border-radius: 8px; padding: 0.7rem 0.85rem; display: flex; flex-direction: column; gap: 0.25rem; }
    .inc.critical { border-left-color: #ef4444; } .inc.warning { border-left-color: #f59e0b; } .inc.caution { border-left-color: #22d3ee; }
    .inc-top { display: flex; align-items: center; gap: 0.6rem; font-size: 0.62rem; }
    .sev { font-weight: 800; letter-spacing: 0.1em; }
    .critical .sev { color: #f87171; } .warning .sev { color: #fbbf24; } .caution .sev { color: #22d3ee; }
    .iid { font-family: ui-monospace, monospace; color: #64748b; }
    .time { margin-left: auto; color: #64748b; font-family: ui-monospace, monospace; }
    .st { color: #38bdf8; font-weight: 700; }
    .inc strong { font-size: 0.85rem; color: #fff; }
    .ward { font-size: 0.64rem; color: #64748b; }
    .inc p { font-size: 0.74rem; color: #cbd5e1; margin: 0; }
    .inc-meta { font-size: 0.68rem; color: #94a3b8; }
    .inc-meta b { color: #e2e8f0; }
    .inc-actions { display: flex; gap: 0.5rem; margin-top: 0.25rem; }
    .btn-ack { background: rgba(220,38,38,0.85); color: #fff; border: none; border-radius: 6px; padding: 0.45rem 0.8rem; font-size: 0.62rem; font-weight: 800; cursor: pointer; }
    .btn-loc { background: transparent; border: 1px solid #334155; color: #94a3b8; border-radius: 6px; padding: 0.45rem 0.8rem; font-size: 0.62rem; font-weight: 800; cursor: pointer; }
    .acked { font-size: 0.62rem; font-weight: 800; color: #34d399; align-self: center; }
    @media (max-width: 1000px) { .sum-grid { grid-template-columns: repeat(2, 1fr); } }
  `]
})
export class EocIncidentsComponent {
  readonly store = inject(EocDataService);
  readonly filter = signal<'ALL' | Severity>('ALL');
  readonly filters = ['ALL', 'CRITICAL', 'WARNING', 'CAUTION'] as const;

  count(s: Severity): number {
    return this.store.incidents().filter((i) => i.severity === s).length;
  }
  visible() {
    const f = this.filter();
    return this.store.incidents().filter((i) => f === 'ALL' || i.severity === f);
  }
  locate(id: string): void {
    const inc = this.store.incidents().find((i) => i.id === id);
    if (!inc) return;
    const zone = this.store.zones().find((z) => z.zoneName.split(' ')[0] === inc.location.split(' ')[0]);
    if (zone) this.store.requestMapFocus(zone.lat, zone.lng, 13);
    this.store.selectIncident(id);
  }
}
