import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EocDataService, EocView } from '../services/eoc-data.service';

interface NavItem { id: EocView; label: string; desc: string; icon: string; }

const NAV: NavItem[] = [
  { id: 'overview', label: 'Command Overview', desc: 'Live Nowcast & Hotspots', icon: '◈' },
  { id: 'radar', label: 'Rainfall Radar', desc: 'Doppler / Rain Intelligence', icon: '◎' },
  { id: 'drainage', label: 'Drainage Network', desc: 'Hydraulic Digital Twin', icon: '⬡' },
  { id: 'flood', label: 'Flood Risk Map', desc: 'Street-Level Inundation', icon: '▦' },
  { id: 'routes', label: 'Route Advisory', desc: 'Emergency Clearance', icon: '➤' },
  { id: 'alerts', label: 'Alerts & Dispatch', desc: 'Early Warning Center', icon: '⚠' },
  { id: 'timeline', label: 'Incident Timeline', desc: 'Live Event Stream', icon: '◷' },
  { id: 'reports', label: 'Municipal Reports', desc: 'Post-Event Validation', icon: '▤' },
  { id: 'health', label: 'System Health', desc: 'Sensors / Models / APIs', icon: '✚' },
];

@Component({
  selector: 'app-eoc-nav-rail',
  standalone: true,
  imports: [CommonModule],
  template: `
    <nav class="rail">
      @for (item of nav; track item.id) {
        <button
          type="button"
          class="rail-item"
          [class.active]="store.activeView() === item.id"
          (click)="store.activeView.set(item.id)"
          [title]="item.label"
        >
          <span class="ri">{{ item.icon }}</span>
          <span class="rt"><strong>{{ item.label }}</strong><em>{{ item.desc }}</em></span>
        </button>
      }
      <div class="rail-foot">
        <span>GCC EOC</span>
        <span>Ripon Building</span>
      </div>
    </nav>
  `,
  styles: [`
    .rail {
      display: flex; flex-direction: column; gap: 2px;
      background: #080f22; border-right: 1px solid rgba(56,189,248,0.14);
      padding: 0.6rem 0.5rem; width: 212px; flex: none;
      overflow-y: auto; max-height: calc(100vh - 52px); position: sticky; top: 52px;
    }
    .rail-item {
      display: flex; gap: 0.65rem; align-items: center; text-align: left;
      background: transparent; border: 1px solid transparent; border-radius: 8px;
      padding: 0.55rem 0.6rem; cursor: pointer; color: #94a3b8; width: 100%;
    }
    .rail-item:hover { background: rgba(56,189,248,0.07); color: #e2e8f0; }
    .rail-item.active {
      background: rgba(14,165,233,0.12); border-color: rgba(56,189,248,0.35); color: #f1f5f9;
      box-shadow: inset 2px 0 0 #22d3ee;
    }
    .ri { font-size: 1rem; width: 22px; text-align: center; color: #38bdf8; flex: none; }
    .rail-item.active .ri { color: #22d3ee; }
    .rt { display: flex; flex-direction: column; line-height: 1.2; min-width: 0; }
    .rt strong { font-size: 0.72rem; font-weight: 700; }
    .rt em { font-style: normal; font-size: 0.6rem; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .rail-foot { margin-top: auto; padding: 0.6rem; font-size: 0.58rem; letter-spacing: 0.14em; color: #475569; display: flex; flex-direction: column; }
    @media (max-width: 900px) {
      .rail { width: 56px; }
      .rt, .rail-foot { display: none; }
    }
  `]
})
export class EocNavRailComponent {
  readonly store = inject(EocDataService);
  readonly nav = NAV;
}
