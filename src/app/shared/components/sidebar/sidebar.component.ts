import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AlertService } from '../../../core/services/alert.service';
import { AuthService } from '../../../core/auth/auth.service';

interface NavItem {
  path: string;
  label: string;
  badge?: () => number | string | null;
  icon: string;
  role?: string[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  template: `
    <aside class="app-sidebar" [class.collapsed]="collapsed" [class.mobile-open]="mobileOpen">
      <!-- Logo & Branding -->
      <div class="sidebar-brand">
        <div class="brand-logo-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>
            <path d="M12 12v6"></path>
            <path d="M9 15l3-3 3 3"></path>
          </svg>
        </div>
        @if (!collapsed) {
          <div class="brand-text">
            <span class="brand-name">FloodWatch AI</span>
            <span class="brand-sub">Greater Mumbai Nowcasting</span>
          </div>
        }
        <button
          type="button"
          class="sidebar-toggle-btn desktop-only"
          (click)="toggleCollapse.emit()"
          [title]="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            @if (collapsed) {
              <polyline points="9 18 15 12 9 6"></polyline>
            } @else {
              <polyline points="15 18 9 12 15 6"></polyline>
            }
          </svg>
        </button>
      </div>

      <!-- Navigation Links -->
      <nav class="sidebar-nav">
        @for (item of filteredNavItems(); track item.path) {
          <a
            [routerLink]="item.path"
            routerLinkActive="active"
            class="nav-link"
            (click)="onLinkClick()"
            [title]="collapsed ? item.label : ''"
          >
            <div class="nav-icon" [innerHTML]="item.icon"></div>
            @if (!collapsed) {
              <span class="nav-label">{{ item.label }}</span>
              @if (item.badge && item.badge()) {
                <span class="nav-badge font-mono">{{ item.badge() }}</span>
              }
            }
          </a>
        }
      </nav>

      <!-- Sidebar Footer -->
      @if (!collapsed) {
        <div class="sidebar-footer">
          <div class="system-status-indicator">
            <span class="dot-operational"></span>
            <div class="status-texts">
              <span class="status-title">EOC Telemetry Online</span>
              <span class="status-desc">Greater Mumbai Spatial Grid</span>
            </div>
          </div>
          <div class="sih-tag">SIH26085 • BMC Control</div>
        </div>
      }
    </aside>

    <!-- Mobile Backdrop -->
    @if (mobileOpen) {
      <div class="sidebar-backdrop" (click)="closeMobile.emit()"></div>
    }
  `,
  styles: [`
    .app-sidebar {
      width: var(--sidebar-width);
      height: 100vh;
      background-color: var(--bg-dark);
      border-right: 1px solid var(--border-subtle);
      display: flex;
      flex-direction: column;
      position: fixed;
      left: 0;
      top: 0;
      bottom: 0;
      z-index: 1050;
      transition: width var(--transition-normal);
      overflow-y: auto;
      overflow-x: hidden;
    }
    .app-sidebar.collapsed {
      width: var(--sidebar-collapsed-width);
    }
    .sidebar-brand {
      height: var(--header-height);
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0 1.25rem;
      border-bottom: 1px solid var(--border-subtle);
      background-color: rgba(11, 15, 23, 0.4);
    }
    .brand-logo-icon {
      width: 32px;
      height: 32px;
      border-radius: var(--radius-sm);
      background: linear-gradient(135deg, #2563eb, #0284c7);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      flex-shrink: 0;
    }
    .brand-text {
      display: flex;
      flex-direction: column;
      overflow: hidden;
      white-space: nowrap;
    }
    .brand-name {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-main);
      line-height: 1.2;
    }
    .brand-sub {
      font-size: 0.68rem;
      color: var(--text-muted);
    }
    .sidebar-toggle-btn {
      margin-left: auto;
      background: transparent;
      border: none;
      color: var(--text-dim);
      padding: 0.35rem;
      border-radius: var(--radius-xs);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    }
    .sidebar-toggle-btn:hover {
      color: var(--text-main);
      background-color: var(--border-subtle);
    }
    .sidebar-nav {
      flex: 1;
      padding: 1rem 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      overflow-y: auto;
    }
    .nav-link {
      display: flex;
      align-items: center;
      gap: 0.85rem;
      padding: 0.65rem 0.85rem;
      border-radius: var(--radius-md);
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.875rem;
      font-weight: 500;
      transition: all var(--transition-fast);
      white-space: nowrap;
    }
    .nav-link:hover {
      color: var(--text-main);
      background-color: rgba(255, 255, 255, 0.04);
    }
    .nav-link.active {
      color: #ffffff;
      background: linear-gradient(90deg, rgba(37, 99, 235, 0.2), rgba(37, 99, 235, 0.05));
      border-left: 3px solid #3b82f6;
      font-weight: 600;
    }
    .nav-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .nav-label {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .nav-badge {
      background-color: #ef4444;
      color: #ffffff;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.15rem 0.45rem;
      border-radius: var(--radius-full);
    }
    .sidebar-footer {
      padding: 1rem 1.25rem;
      border-top: 1px solid var(--border-subtle);
      background-color: rgba(11, 15, 23, 0.6);
    }
    .system-status-indicator {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      margin-bottom: 0.5rem;
    }
    .dot-operational {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: var(--status-safe);
      box-shadow: 0 0 8px var(--status-safe);
      flex-shrink: 0;
    }
    .status-texts {
      display: flex;
      flex-direction: column;
    }
    .status-title {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-main);
      line-height: 1.2;
    }
    .status-desc {
      font-size: 0.68rem;
      color: var(--text-muted);
    }
    .sih-tag {
      font-size: 0.68rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .sidebar-backdrop {
      position: fixed;
      inset: 0;
      background-color: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(4px);
      z-index: 1040;
    }
  `]
})
export class SidebarComponent {
  @Input() collapsed = false;
  @Input() mobileOpen = false;
  @Output() toggleCollapse = new EventEmitter<void>();
  @Output() closeMobile = new EventEmitter<void>();

  constructor(
    private alertService: AlertService,
    public authService: AuthService
  ) {}

  readonly allNavItems: NavItem[] = [
    // Citizen Dedicated Section
    {
      path: '/citizen/dashboard',
      label: 'Citizen Safety',
      role: ['CITIZEN', 'ADMIN'],
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>`
    },
    {
      path: '/citizen/my-alerts',
      label: 'My Warnings',
      role: ['CITIZEN', 'ADMIN'],
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>`
    },
    {
      path: '/citizen/privacy',
      label: 'Privacy & Places',
      role: ['CITIZEN', 'ADMIN'],
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`
    },

    // Government Dedicated Section
    {
      path: '/government/dashboard',
      label: 'EOC Command',
      role: ['GOVERNMENT_VIEWER', 'GOVERNMENT_OPERATOR', 'GOVERNMENT_SUPERVISOR', 'ADMIN'],
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>`
    },

    // Shared / Core Tools
    {
      path: '/dashboard',
      label: 'Regional Overview',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>`
    },
    {
      path: '/flood-map',
      label: 'Flood Risk Map',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg>`
    },
    {
      path: '/safe-route',
      label: 'Safe Route',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="19" r="3"></circle><path d="M9 19h8.5a4.5 4.5 0 0 0 0-9H7a4 4 0 0 1 0-8h11"></path><polyline points="18 5 21 2 18 -1"></polyline></svg>`
    },
    {
      path: '/alerts',
      label: 'Public Alerts',
      badge: () => this.alertService.activeAlertsCount() || null,
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`
    },
    {
      path: '/analytics',
      label: 'AI Analytics',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>`
    },
    {
      path: '/admin',
      label: 'Admin Command',
      role: ['ADMIN'],
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>`
    },
    {
      path: '/settings',
      label: 'Settings',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`
    }
  ];

  filteredNavItems(): NavItem[] {
    const role = this.authService.userRole();
    return this.allNavItems.filter(item => {
      if (!item.role) return true;
      if (!role) return false;
      return item.role.includes(role);
    });
  }

  onLinkClick(): void {
    this.closeMobile.emit();
  }
}
