import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EocDataService } from '../services/eoc-data.service';
import { DrainageStatus } from '../models/eoc-models';

@Component({
  selector: 'app-eoc-drainage',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="drain-grid">
      <div class="panel">
        <div class="p-head">
          <div><h3>DRAINAGE DIGITAL TWIN</h3><p>Hydraulic node load · {{ store.horizon() }} · {{ store.dataMode() }}</p></div>
          <div class="filter">
            @for (f of filters; track f) {
              <button type="button" [class.on]="filter() === f" (click)="filter.set(f)">{{ f }}</button>
            }
          </div>
        </div>
        <div class="node-list">
          @for (n of visibleNodes(); track n.id) {
            <button type="button" class="node" [class.sel]="store.selectedNodeId() === n.id" (click)="select(n.id)">
              <span class="n-id" [class]="statusClass(store.nodeSlice(n).status)">{{ n.id }}</span>
              <span class="n-main"><strong>{{ n.name }}</strong><em>{{ n.nodeType }} · {{ n.flowM3s.toFixed(1) }} m³/s · Lvl {{ n.waterLevelM.toFixed(1) }} m</em></span>
              <span class="n-load"><b>{{ store.nodeSlice(n).surchargePct }}%</b><i class="bar"><i [style.width.%]="loadWidth(store.nodeSlice(n).surchargePct)" [class]="statusClass(store.nodeSlice(n).status)"></i></i></span>
              @if (n.isDemo) { <span class="demo-tag">DEMO</span> }
            </button>
          }
        </div>
        <p class="fine">Nodes marked DEMO are illustrative simulation geometry — not confirmed GCC infrastructure.</p>
      </div>

      <div class="panel inspector">
        @if (store.selectedNode(); as n) {
          <span class="insp-id">{{ n.id }} · {{ n.nodeType }}</span>
          <h3>{{ n.name }}</h3>
          @if (n.isDemo) { <span class="demo-tag">DEMO NODE — illustrative only</span> }
          <div class="insp-grid">
            <div><em>Flow rate</em><b>{{ n.flowM3s.toFixed(1) }} m³/s</b></div>
            <div><em>Hydraulic load</em><b>{{ n.hydraulicLoadPct }}%</b></div>
            <div><em>Water level</em><b>{{ n.waterLevelM.toFixed(1) }} m</b></div>
            <div><em>Surcharge ({{ store.horizon() }})</em><b>{{ store.nodeSlice(n).surchargePct }}%</b></div>
          </div>
          <span class="insp-status" [class]="statusClass(store.nodeSlice(n).status)">{{ store.nodeSlice(n).status }}</span>
          <span class="insp-chart-t">SURCHARGE FORECAST</span>
          <div class="spark">
            @for (s of n.series; track s.horizon) {
              <div class="spark-bar" [style.height.%]="Math.min(100, s.surchargePct / 2.8)" [class]="statusClass(s.status)" [title]="s.horizon + ': ' + s.surchargePct + '%'">
                <span>{{ s.horizon.replace('T+', 'T') }}</span>
              </div>
            }
          </div>
          <button type="button" class="btn-locate" (click)="store.requestMapFocus(n.lat, n.lng, 14)">LOCATE ON MAP</button>
        } @else {
          <div class="empty">Select a drainage node to open the inspector.</div>
        }
      </div>
    </div>
  `,
  styles: [`
    .drain-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 0.75rem; }
    .panel { background: rgba(15,23,42,0.75); border: 1px solid rgba(56,189,248,0.18); border-radius: 12px; padding: 1rem 1.1rem; }
    .p-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 0.6rem; margin-bottom: 0.7rem; }
    h3 { margin: 0; font-size: 0.85rem; letter-spacing: 0.1em; color: #f1f5f9; }
    .p-head p, .fine { font-size: 0.66rem; color: #64748b; margin: 0.15rem 0 0; }
    .filter { display: flex; gap: 0.3rem; }
    .filter button { background: transparent; border: 1px solid #334155; color: #94a3b8; font-size: 0.6rem; font-weight: 700; border-radius: 6px; padding: 0.25rem 0.55rem; cursor: pointer; }
    .filter button.on { color: #22d3ee; border-color: #0ea5e9; }
    .node-list { display: flex; flex-direction: column; gap: 0.45rem; max-height: 430px; overflow-y: auto; }
    .node { display: flex; align-items: center; gap: 0.7rem; background: rgba(2,6,16,0.5); border: 1px solid rgba(148,163,184,0.14); border-radius: 8px; padding: 0.6rem 0.7rem; cursor: pointer; color: #e2e8f0; text-align: left; width: 100%; }
    .node:hover { border-color: rgba(56,189,248,0.4); }
    .node.sel { border-color: #0ea5e9; background: rgba(14,165,233,0.08); }
    .n-id { font-family: ui-monospace, monospace; font-size: 0.66rem; font-weight: 800; padding: 0.25rem 0.45rem; border-radius: 6px; flex: none; }
    .n-main { display: flex; flex-direction: column; min-width: 0; flex: 1; }
    .n-main strong { font-size: 0.74rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .n-main em { font-style: normal; font-size: 0.62rem; color: #94a3b8; }
    .n-load { display: flex; flex-direction: column; align-items: flex-end; gap: 0.2rem; min-width: 86px; }
    .n-load b { font-family: ui-monospace, monospace; font-size: 0.8rem; }
    .bar { width: 86px; height: 5px; background: #1e293b; border-radius: 3px; display: block; overflow: hidden; }
    .bar i { display: block; height: 100%; }
    .NOMINAL, .nominal { background: rgba(52,211,153,0.15); color: #34d399; }
    i.NOMINAL { background: #34d399; }
    .WARNING, .warning { background: rgba(251,191,36,0.15); color: #fbbf24; }
    i.WARNING { background: #fbbf24; }
    .CRITICAL, .critical { background: rgba(239,68,68,0.15); color: #f87171; }
    i.CRITICAL { background: #ef4444; }
    .demo-tag { font-size: 0.54rem; font-weight: 800; letter-spacing: 0.1em; color: #fbbf24; border: 1px solid rgba(251,191,36,0.4); padding: 0.12rem 0.35rem; border-radius: 4px; flex: none; }
    .inspector { display: flex; flex-direction: column; gap: 0.5rem; }
    .insp-id { font-family: ui-monospace, monospace; font-size: 0.62rem; color: #38bdf8; letter-spacing: 0.1em; }
    .insp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
    .insp-grid div { background: rgba(2,6,16,0.5); border-radius: 7px; padding: 0.5rem 0.6rem; display: flex; flex-direction: column; }
    .insp-grid em { font-style: normal; font-size: 0.56rem; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; }
    .insp-grid b { font-family: ui-monospace, monospace; font-size: 0.85rem; color: #f1f5f9; }
    .insp-status { align-self: flex-start; font-size: 0.62rem; font-weight: 800; letter-spacing: 0.12em; padding: 0.25rem 0.6rem; border-radius: 6px; }
    .insp-chart-t { font-size: 0.58rem; font-weight: 800; letter-spacing: 0.14em; color: #64748b; }
    .spark { display: flex; align-items: flex-end; gap: 6px; height: 92px; background: rgba(2,6,16,0.5); border-radius: 7px; padding: 0.5rem; }
    .spark-bar { flex: 1; border-radius: 3px 3px 0 0; min-height: 8px; position: relative; display: flex; justify-content: center; }
    .spark-bar span { position: absolute; bottom: -16px; font-size: 0.52rem; color: #64748b; }
    .spark { padding-bottom: 1.1rem; }
    .btn-locate { margin-top: 0.4rem; background: rgba(14,165,233,0.14); border: 1px solid #0ea5e9; color: #7dd3fc; border-radius: 7px; padding: 0.55rem; font-size: 0.66rem; font-weight: 800; letter-spacing: 0.08em; cursor: pointer; }
    .empty { color: #64748b; font-size: 0.75rem; padding: 2rem 0; text-align: center; }
    @media (max-width: 1000px) { .drain-grid { grid-template-columns: 1fr; } }
  `]
})
export class EocDrainageComponent {
  readonly store = inject(EocDataService);
  readonly filter = signal<'ALL' | 'NOMINAL' | 'WARNING' | 'CRITICAL'>('ALL');
  readonly filters = ['ALL', 'NOMINAL', 'WARNING', 'CRITICAL'] as const;
  readonly Math = Math;

  visibleNodes() {
    const f = this.filter();
    return this.store.nodes().filter((n) => f === 'ALL' || this.store.nodeSlice(n).status === f);
  }
  statusClass(s: DrainageStatus): string { return s; }
  loadWidth(pct: number): number { return Math.min(100, pct / 2.8); }
  select(id: string): void {
    this.store.selectNode(this.store.selectedNodeId() === id ? null : id);
  }
}
