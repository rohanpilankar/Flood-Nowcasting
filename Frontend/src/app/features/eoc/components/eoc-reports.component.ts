import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EocDataService } from '../services/eoc-data.service';

@Component({
  selector: 'app-eoc-reports',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="sum-grid">
      <div class="scard"><span>ARCHIVED STORM EVENTS</span><strong>{{ store.archive().length }}</strong></div>
      <div class="scard"><span>BASELINE F1 (TEST)</span><strong>0.511</strong><em>Chennai offline baseline</em></div>
      <div class="scard"><span>BASELINE ROC-AUC</span><strong>0.867</strong><em>TEST 03–10 Dec 2015</em></div>
      <div class="scard ok"><span>VALIDATION STATUS</span><strong class="live">BASELINE AUDITED</strong></div>
    </div>

    <div class="rep-grid">
      <div class="panel">
        <div class="p-head">
          <div><h3>MUNICIPAL POST-EVENT REPORTS & AUDITS</h3><p>Historical flood archives and municipal audit exports · DEMO</p></div>
          <div class="p-actions">
            <button type="button" (click)="exportCsv()">EXPORT CSV</button>
            <button type="button" class="primary" (click)="exportCsv()">GENERATE REPORT</button>
          </div>
        </div>
        <div class="tbl-wrap">
          <table>
            <thead><tr><th>Event</th><th>Date</th><th>Peak rain</th><th>Max depth</th><th>Zones</th><th>Lead time</th></tr></thead>
            <tbody>
              @for (s of store.archive(); track s.id) {
                <tr>
                  <td><strong>{{ s.eventName }}</strong><span class="eid">{{ s.id }}</span></td>
                  <td class="mono">{{ s.eventDate }}</td>
                  <td class="mono">{{ s.peakRainfallMmh }} mm/h</td>
                  <td class="mono">{{ s.maxDepthCm }} cm</td>
                  <td>{{ s.affectedZones.join(' · ') }}</td>
                  <td class="mono">{{ s.leadTimeMin }} min</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <h3>MODEL VALIDATION</h3>
        <p class="sub">Chennai Offline Spatial Flood Susceptibility Baseline · TEST partition 2015-12-03 → 2015-12-10 · threshold 0.84</p>
        <div class="metric-table">
          @for (m of auditedMetrics; track m.label) {
            <div class="mrow"><span>{{ m.label }}</span><b>{{ m.value }}</b></div>
          }
        </div>
        <div class="cm-box">
          <span class="cm-t">CONFUSION MATRIX (TEST)</span>
          <div class="cm-grid">
            <span></span><span class="cm-h">Pred +</span><span class="cm-h">Pred −</span>
            <span class="cm-h">Actual +</span><b>536</b><b>566</b>
            <span class="cm-h">Actual −</span><b>460</b><b>26,179</b>
          </div>
        </div>
        <p class="fine">Source: Models/metadata/chennai_xgboost_baseline_metrics.json. Raw outputs are decision scores without post-hoc calibration (Brier 0.057 reported without asserting calibration). Demo storm archives above are not used as scientific validation.</p>
      </div>
    </div>
  `,
  styles: [`
    .sum-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.6rem; margin-bottom: 0.75rem; }
    .scard { background: rgba(15,23,42,0.75); border: 1px solid rgba(148,163,184,0.16); border-left: 3px solid #38bdf8; border-radius: 8px; padding: 0.6rem 0.8rem; display: flex; flex-direction: column; gap: 0.1rem; }
    .scard.warn { border-left-color: #fbbf24; }
    .scard.ok { border-left-color: #34d399; }
    .scard span { font-size: 0.58rem; font-weight: 800; letter-spacing: 0.12em; color: #64748b; }
    .scard strong { font-family: ui-monospace, monospace; font-size: 1.35rem; color: #f1f5f9; }
    .scard strong.live { font-size: 0.85rem; color: #34d399; font-family: inherit; }
    .scard em { font-style: normal; font-size: 0.6rem; color: #64748b; }
    .rep-grid { display: grid; grid-template-columns: 1.6fr 1fr; gap: 0.75rem; }
    .panel { background: rgba(15,23,42,0.75); border: 1px solid rgba(56,189,248,0.18); border-radius: 12px; padding: 1rem 1.1rem; }
    .p-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 0.6rem; margin-bottom: 0.7rem; }
    h3 { margin: 0; font-size: 0.85rem; letter-spacing: 0.1em; color: #f1f5f9; }
    .p-head p, .sub { font-size: 0.66rem; color: #64748b; margin: 0.15rem 0 0; }
    .p-actions { display: flex; gap: 0.4rem; flex: none; }
    .p-actions button { background: transparent; border: 1px solid #334155; color: #94a3b8; border-radius: 7px; padding: 0.45rem 0.75rem; font-size: 0.62rem; font-weight: 800; cursor: pointer; }
    .p-actions button.primary { background: rgba(14,165,233,0.15); border-color: #0ea5e9; color: #7dd3fc; }
    .tbl-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.7rem; }
    th { text-align: left; font-size: 0.58rem; letter-spacing: 0.1em; color: #64748b; padding: 0.4rem 0.5rem; border-bottom: 1px solid rgba(148,163,184,0.2); white-space: nowrap; }
    td { padding: 0.45rem 0.5rem; border-bottom: 1px solid rgba(148,163,184,0.08); color: #cbd5e1; vertical-align: top; }
    td strong { color: #f1f5f9; display: block; font-size: 0.7rem; }
    .eid { font-family: ui-monospace, monospace; font-size: 0.58rem; color: #475569; }
    .mono { font-family: ui-monospace, monospace; white-space: nowrap; }
    .await-box { background: rgba(251,191,36,0.06); border: 1px solid rgba(251,191,36,0.3); border-radius: 8px; padding: 0.75rem 0.85rem; margin: 0.6rem 0; }
    .await-box strong { font-size: 0.75rem; color: #fbbf24; }
    .await-box p { font-size: 0.68rem; color: #cbd5e1; margin: 0.3rem 0 0; line-height: 1.5; }
    .metric-table { display: flex; flex-direction: column; }
    .mrow { display: flex; justify-content: space-between; font-size: 0.68rem; color: #94a3b8; padding: 0.35rem 0; border-bottom: 1px solid rgba(148,163,184,0.08); }
    .mrow b { color: #e2e8f0; font-family: ui-monospace, monospace; }
    .cm-box { margin-top: 0.6rem; background: rgba(2,6,16,0.5); border-radius: 8px; padding: 0.6rem 0.7rem; }
    .cm-t { font-size: 0.56rem; font-weight: 800; letter-spacing: 0.14em; color: #64748b; }
    .cm-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.25rem; margin-top: 0.4rem; text-align: center; }
    .cm-grid .cm-h { font-size: 0.6rem; color: #64748b; }
    .cm-grid b { font-family: ui-monospace, monospace; font-size: 0.78rem; color: #f1f5f9; background: rgba(148,163,184,0.07); border-radius: 5px; padding: 0.3rem 0; }
    .fine { font-size: 0.62rem; color: #64748b; margin: 0.6rem 0 0; line-height: 1.5; }
    @media (max-width: 1000px) { .sum-grid { grid-template-columns: repeat(2, 1fr); } .rep-grid { grid-template-columns: 1fr; } }
  `]
})
export class EocReportsComponent {
  readonly store = inject(EocDataService);
  /** Audited project evaluation — chennai_xgboost_baseline_metrics.json (TEST). */
  readonly auditedMetrics = [
    { label: 'ROC-AUC', value: '0.867' },
    { label: 'PR-AUC', value: '0.425' },
    { label: 'Precision', value: '0.538' },
    { label: 'Recall', value: '0.486' },
    { label: 'F1 score', value: '0.511' },
    { label: 'Brier score', value: '0.057' },
    { label: 'Positives (actual / predicted)', value: '1,102 / 996' },
  ];

  exportCsv(): void {
    const rows = ['event,date,peak_rain_mmh,max_depth_cm,zones,lead_time_min',
      ...this.store.archive().map((s) =>
        [s.eventName, s.eventDate, s.peakRainfallMmh, s.maxDepthCm, `"${s.affectedZones.join('; ')}"`, s.leadTimeMin].join(','))];
    const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'gcc-eoc-storm-archive-demo.csv';
    a.click();
    URL.revokeObjectURL(a.href);
  }
}
