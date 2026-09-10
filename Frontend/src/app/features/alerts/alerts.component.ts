import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AlertService } from '../../core/services/alert.service';
import { FloodAlert } from '../../core/models/alert.model';
import { AlertCardComponent } from '../../shared/components/alert-card/alert-card.component';

import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state.component';

@Component({
  selector: 'app-alerts',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    AlertCardComponent,
    EmptyStateComponent
  ],
  template: `
    <div class="alerts-page">
      <!-- Header Summary Bar -->
      <div class="alerts-header card">
        <div class="header-text-block">
          <div class="title-with-badge">
            <h2 class="page-title">Emergency Alert Operations</h2>
          </div>
          <p class="page-sub">Real-time incident warnings and AI risk surge notifications</p>
        </div>

        <div class="alert-counts-grid">
          <div class="count-pill">
            <span class="c-label">Total Active</span>
            <span class="c-val font-mono">{{ activeCount }}</span>
          </div>
          <div class="count-pill border-high">
            <span class="c-label">High Priority</span>
            <span class="c-val font-mono text-danger">{{ highCount }}</span>
          </div>
          <div class="count-pill border-medium">
            <span class="c-label">Medium Priority</span>
            <span class="c-val font-mono text-warning">{{ mediumCount }}</span>
          </div>
          <div class="count-pill border-low">
            <span class="c-label">Acknowledged</span>
            <span class="c-val font-mono text-safe">{{ acknowledgedCount }}</span>
          </div>
        </div>
      </div>

      <!-- Filter Controls Bar -->
      <div class="card filter-bar">
        <div class="filter-pills">
          @for (f of filters; track f.key) {
            <button
              type="button"
              class="filter-pill-btn"
              [class.active]="activeFilter === f.key"
              (click)="setFilter(f.key)"
            >
              {{ f.label }}
              <span class="pill-count font-mono">{{ f.count() }}</span>
            </button>
          }
        </div>

        <div class="search-wrap">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            type="text"
            placeholder="Filter by locality or road (e.g. Velachery, Subway)..."
            [(ngModel)]="searchQuery"
            class="filter-search-input"
          />
          @if (searchQuery) {
            <button type="button" class="clear-btn" (click)="searchQuery = ''">✕</button>
          }
        </div>
      </div>

      <!-- Alerts Feed List -->
      @if (filteredAlerts.length > 0) {
        <div class="alerts-grid">
          @for (alert of filteredAlerts; track alert.id) {
            <app-alert-card
              [alert]="alert"
              (acknowledge)="onAcknowledgeAlert($event)"
              (viewLocation)="onViewAlertLocation($event)"
            ></app-alert-card>
          }
        </div>
      } @else {
        <app-empty-state
          title="No alerts found"
          description="There are no flood warnings matching the selected filter criteria."
          actionLabel="Reset Filters"
          (action)="resetFilters()"
        ></app-empty-state>
      }
    </div>
  `,
  styles: [`
    .alerts-page {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }

    .title-with-badge {
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }
    .page-title {
      font-size: 1.45rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .page-sub {
      font-size: 0.825rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
    }

    .alerts-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .alert-counts-grid {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .count-pill {
      display: flex;
      flex-direction: column;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.4rem 0.85rem;
      min-width: 95px;
    }
    .c-label {
      font-size: 0.68rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .c-val {
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text-main);
      line-height: 1.2;
    }
    .border-high {
      border-color: rgba(239, 68, 68, 0.4);
    }
    .border-medium {
      border-color: rgba(245, 158, 11, 0.4);
    }
    .border-low {
      border-color: rgba(16, 185, 129, 0.4);
    }
    .text-danger { color: var(--status-critical); }
    .text-warning { color: var(--status-caution); }
    .text-safe { color: var(--status-safe); }

    // Filter Bar
    .filter-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
      padding: 0.75rem 1.25rem;
    }
    .filter-pills {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      flex-wrap: wrap;
    }
    .filter-pill-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.35rem 0.75rem;
      font-size: 0.78rem;
      font-weight: 600;
      border-radius: var(--radius-full);
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      transition: all var(--transition-fast);

      &:hover {
        color: var(--text-main);
        border-color: var(--text-dim);
      }
      &.active {
        background-color: var(--brand-primary);
        border-color: var(--brand-primary);
        color: #ffffff;
      }
    }
    .pill-count {
      background-color: rgba(0, 0, 0, 0.25);
      font-size: 0.7rem;
      padding: 0.1rem 0.4rem;
      border-radius: var(--radius-full);
    }

    .search-wrap {
      position: relative;
      display: flex;
      align-items: center;
      width: 280px;

      svg {
        position: absolute;
        left: 0.75rem;
        color: var(--text-dim);
      }
    }
    .filter-search-input {
      width: 100%;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 0.45rem 1.8rem 0.45rem 2.2rem;
      color: var(--text-main);
      font-size: 0.8125rem;
      outline: none;
      transition: border-color var(--transition-fast);

      &:focus {
        border-color: var(--brand-primary);
      }
    }
    .clear-btn {
      position: absolute;
      right: 0.6rem;
      color: var(--text-dim);
      font-size: 0.75rem;
      &:hover { color: var(--text-main); }
    }

    // Alerts Grid
    .alerts-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 1.25rem;
      @media (max-width: 640px) {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class AlertsComponent implements OnInit {
  allAlerts: FloodAlert[] = [];
  searchQuery = '';
  activeFilter: 'ALL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'ACKNOWLEDGED' = 'ALL';

  readonly filters = [
    { key: 'ALL' as const, label: 'All Alerts', count: () => this.allAlerts.length },
    { key: 'HIGH' as const, label: 'High Priority', count: () => this.allAlerts.filter(a => a.severity === 'HIGH' && !a.acknowledged).length },
    { key: 'MEDIUM' as const, label: 'Medium', count: () => this.allAlerts.filter(a => a.severity === 'MEDIUM' && !a.acknowledged).length },
    { key: 'LOW' as const, label: 'Low', count: () => this.allAlerts.filter(a => a.severity === 'LOW' && !a.acknowledged).length },
    { key: 'ACKNOWLEDGED' as const, label: 'Acknowledged', count: () => this.allAlerts.filter(a => a.acknowledged).length }
  ];

  constructor(
    public alertService: AlertService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadAlerts();
  }

  loadAlerts(): void {
    this.alertService.getAlerts().subscribe(alerts => {
      this.allAlerts = alerts;
    });
  }

  get activeCount(): number {
    return this.allAlerts.filter(a => !a.acknowledged).length;
  }

  get highCount(): number {
    return this.allAlerts.filter(a => a.severity === 'HIGH' && !a.acknowledged).length;
  }

  get mediumCount(): number {
    return this.allAlerts.filter(a => a.severity === 'MEDIUM' && !a.acknowledged).length;
  }

  get acknowledgedCount(): number {
    return this.allAlerts.filter(a => a.acknowledged).length;
  }

  get filteredAlerts(): FloodAlert[] {
    return this.allAlerts.filter(alert => {
      // Filter by severity or state
      if (this.activeFilter === 'HIGH' && (alert.severity !== 'HIGH' || alert.acknowledged)) return false;
      if (this.activeFilter === 'MEDIUM' && (alert.severity !== 'MEDIUM' || alert.acknowledged)) return false;
      if (this.activeFilter === 'LOW' && (alert.severity !== 'LOW' || alert.acknowledged)) return false;
      if (this.activeFilter === 'ACKNOWLEDGED' && !alert.acknowledged) return false;

      // Filter by search query
      if (this.searchQuery.trim()) {
        const q = this.searchQuery.toLowerCase();
        const matchLoc = alert.location.toLowerCase().includes(q);
        const matchDesc = alert.description.toLowerCase().includes(q);
        const matchId = alert.id.toLowerCase().includes(q);
        return matchLoc || matchDesc || matchId;
      }

      return true;
    });
  }

  setFilter(filter: 'ALL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'ACKNOWLEDGED'): void {
    this.activeFilter = filter;
  }

  resetFilters(): void {
    this.activeFilter = 'ALL';
    this.searchQuery = '';
  }

  onAcknowledgeAlert(id: string): void {
    this.alertService.acknowledgeAlert(id).subscribe(() => {
      this.loadAlerts();
    });
  }

  onViewAlertLocation(alert: FloodAlert): void {
    this.router.navigate(['/flood-map'], {
      queryParams: { lat: alert.coordinates[0], lng: alert.coordinates[1], focus: alert.location }
    });
  }
}
