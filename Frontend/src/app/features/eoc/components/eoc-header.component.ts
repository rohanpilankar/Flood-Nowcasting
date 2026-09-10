import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EocDataService } from '../services/eoc-data.service';

@Component({
  selector: 'app-eoc-header',
  standalone: true,
  imports: [CommonModule],
  template: `
    <header class="eoc-header">
      <div class="h-left">
        <div class="brand-mark">FW</div>
        <div class="brand-text">
          <strong>FloodWatch AI</strong>
          <span>EOC COMMAND CENTER</span>
        </div>
        <span class="sys-online"><span class="dot"></span>SYSTEM ONLINE</span>
      </div>

      <div class="h-pills">
        <span class="pill">RADAR NOWCAST <b class="live">· LIVE</b></span>
        <span class="pill">DRAINAGE GRAPH <b class="live">· SYNC</b></span>
        <span class="pill">AI FLOOD ENGINE <b class="live">· ONLINE</b></span>
      </div>

      <div class="h-right">
        <span class="mode-flag" [class.sim]="store.dataMode() === 'SIMULATION'">
          {{ store.dataMode() === 'LIVE' ? '● LIVE DATA' : '◐ DEMO SIMULATION' }}
        </span>
        <span class="clock">{{ store.now() | date:'HH:mm:ss' }} IST</span>
        <span class="loc">📍 CHENNAI<span>Greater Chennai Corporation</span></span>
      </div>
    </header>
  `,
  styles: [`
    .eoc-header {
      display: flex; align-items: center; gap: 1.25rem;
      padding: 0.6rem 1.25rem;
      background: linear-gradient(180deg, #0a1428, #070d1d);
      border-bottom: 1px solid rgba(56,189,248,0.18);
      position: sticky; top: 0; z-index: 1200;
      font-family: inherit;
    }
    .h-left { display: flex; align-items: center; gap: 0.7rem; min-width: 0; }
    .brand-mark {
      width: 34px; height: 34px; border-radius: 8px; flex: none;
      background: linear-gradient(135deg, #0369a1, #0ea5e9);
      display: flex; align-items: center; justify-content: center;
      font-weight: 800; font-size: 0.8rem; color: #fff;
      box-shadow: 0 0 14px rgba(14,165,233,0.45);
    }
    .brand-text { display: flex; flex-direction: column; line-height: 1.1; }
    .brand-text strong { font-size: 0.95rem; color: #f1f5f9; letter-spacing: 0.01em; }
    .brand-text span { font-size: 0.62rem; color: #38bdf8; letter-spacing: 0.18em; font-weight: 700; }
    .sys-online {
      display: flex; align-items: center; gap: 0.35rem;
      font-size: 0.62rem; font-weight: 700; letter-spacing: 0.12em; color: #34d399;
      background: rgba(16,185,129,0.1); border: 1px solid rgba(52,211,153,0.35);
      padding: 0.25rem 0.6rem; border-radius: 999px; white-space: nowrap;
    }
    .sys-online .dot { width: 7px; height: 7px; border-radius: 50%; background: #34d399; box-shadow: 0 0 8px #34d399; animation: pulse 2s infinite; }
    @keyframes pulse { 50% { opacity: 0.5; } }
    .h-pills { display: flex; gap: 0.5rem; margin: 0 auto; }
    .pill {
      font-size: 0.62rem; font-weight: 700; letter-spacing: 0.1em; color: #94a3b8;
      background: rgba(148,163,184,0.07); border: 1px solid rgba(148,163,184,0.18);
      padding: 0.3rem 0.7rem; border-radius: 6px; white-space: nowrap;
    }
    .pill .live { color: #22d3ee; }
    .h-right { display: flex; align-items: center; gap: 0.9rem; margin-left: auto; }
    .mode-flag {
      font-size: 0.62rem; font-weight: 800; letter-spacing: 0.12em; color: #34d399;
      border: 1px solid rgba(52,211,153,0.4); background: rgba(16,185,129,0.08);
      padding: 0.3rem 0.7rem; border-radius: 6px; white-space: nowrap;
    }
    .mode-flag.sim { color: #fbbf24; border-color: rgba(251,191,36,0.45); background: rgba(251,191,36,0.08); }
    .clock { font-family: ui-monospace, monospace; font-size: 0.8rem; color: #e2e8f0; white-space: nowrap; }
    .loc { display: flex; flex-direction: column; font-size: 0.72rem; font-weight: 800; color: #f1f5f9; line-height: 1.15; text-align: right; }
    .loc span { font-size: 0.6rem; font-weight: 600; color: #64748b; }
    @media (max-width: 1100px) { .h-pills { display: none; } }
    @media (max-width: 760px) { .loc, .clock { display: none; } }
  `]
})
export class EocHeaderComponent {
  readonly store = inject(EocDataService);
}
