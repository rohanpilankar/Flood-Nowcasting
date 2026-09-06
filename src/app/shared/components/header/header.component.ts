import { Component, EventEmitter, OnInit, OnDestroy, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AlertService } from '../../../core/services/alert.service';
import { AuthService } from '../../../core/auth/auth.service';
import { PrototypeNoticeComponent } from '../prototype-notice/prototype-notice.component';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterLink, PrototypeNoticeComponent],
  template: `
    <header class="app-header">
      <div class="header-left">
        <button
          type="button"
          class="btn-icon mobile-menu-toggle"
          (click)="toggleMobileMenu.emit()"
          aria-label="Toggle navigation menu"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>

        <div class="brand-badge-group">
          <span class="project-tag">SIH26085</span>
          <span class="location-tag">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
              <circle cx="12" cy="10" r="3"></circle>
            </svg>
            BMC Disaster Management (Mumbai)
          </span>
        </div>
      </div>

      <div class="header-center">
        <app-prototype-notice [expanded]="false"></app-prototype-notice>
      </div>

      <div class="header-right">
        <!-- Live EOC Clock -->
        <div class="live-clock-pill">
          <span class="pulse-dot"></span>
          <span class="clock-time font-mono">{{ currentTime }}</span>
        </div>

        <!-- Active Alerts Trigger -->
        <a routerLink="/alerts" class="alert-trigger-btn" aria-label="View Active Alerts">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          </svg>
          @if (alertService.activeAlertsCount() > 0) {
            <span class="alert-counter-badge">{{ alertService.activeAlertsCount() }}</span>
          }
        </a>

        <!-- Dynamic User Profile / Login Link -->
        @if (authService.currentUser(); as user) {
          <div class="user-profile-menu">
            <div class="user-avatar">
              <span>{{ user.full_name ? user.full_name.substring(0, 2).toUpperCase() : 'US' }}</span>
            </div>
            <div class="user-details">
              <span class="user-name">{{ user.full_name }}</span>
              <span class="user-role">{{ user.role }}</span>
            </div>
            <button class="btn-logout" (click)="authService.logout()" title="Sign Out">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
            </button>
          </div>
        } @else {
          <div class="guest-auth-actions">
            <a routerLink="/login" class="btn btn-sm btn-outline">Sign In</a>
            <a routerLink="/register" class="btn btn-sm btn-primary">Citizen Signup</a>
          </div>
        }
      </div>
    </header>
  `,
  styles: [`
    .app-header {
      height: var(--header-height);
      background-color: var(--bg-dark);
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 1.5rem;
      position: sticky;
      top: 0;
      z-index: 1000;
      backdrop-filter: blur(10px);
    }
    .header-left {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .mobile-menu-toggle {
      display: none;
      color: var(--text-main);
      padding: 0.4rem;
      border-radius: var(--radius-sm);
      @media (max-width: 1024px) {
        display: flex;
      }
    }
    .brand-badge-group {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .project-tag {
      font-size: 0.72rem;
      font-weight: 700;
      color: #93c5fd;
      background-color: rgba(59, 130, 246, 0.15);
      border: 1px solid rgba(59, 130, 246, 0.3);
      padding: 0.2rem 0.5rem;
      border-radius: var(--radius-sm);
      letter-spacing: 0.04em;
    }
    .location-tag {
      display: flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.78rem;
      color: var(--text-muted);
      font-weight: 500;
      @media (max-width: 640px) {
        display: none;
      }
    }
    .header-center {
      @media (max-width: 900px) {
        display: none;
      }
    }
    .header-right {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .live-clock-pill {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
      padding: 0.3rem 0.75rem;
      border-radius: var(--radius-full);
      font-size: 0.8rem;
      color: var(--text-main);
      @media (max-width: 640px) {
        display: none;
      }
    }
    .pulse-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background-color: var(--status-safe);
      box-shadow: 0 0 8px var(--status-safe);
      animation: pulse 1.8s infinite;
    }
    .alert-trigger-btn {
      position: relative;
      color: var(--text-muted);
      padding: 0.45rem;
      border-radius: var(--radius-md);
      background-color: var(--bg-card);
      border: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: center;
      text-decoration: none;
      transition: all var(--transition-fast);

      &:hover {
        color: var(--text-main);
        background-color: var(--bg-card-hover);
        border-color: var(--brand-primary);
      }
    }
    .alert-counter-badge {
      position: absolute;
      top: -4px;
      right: -4px;
      background-color: var(--status-critical);
      color: #ffffff;
      font-size: 0.68rem;
      font-weight: 700;
      min-width: 18px;
      height: 18px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 8px rgba(239, 68, 68, 0.6);
    }
    .user-profile-menu {
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }
    .user-avatar {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      background: linear-gradient(135deg, #3b82f6, #6366f1);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.78rem;
      font-weight: 700;
      color: #ffffff;
      box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
    }
    .user-details {
      display: flex;
      flex-direction: column;
      @media (max-width: 768px) {
        display: none;
      }
    }
    .user-name {
      font-size: 0.8125rem;
      font-weight: 600;
      color: var(--text-main);
      line-height: 1.2;
    }
    .btn-logout {
      background: transparent;
      border: none;
      color: var(--text-dim);
      padding: 0.35rem;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .btn-logout:hover {
      color: #ef4444;
      background: rgba(239, 68, 68, 0.1);
    }
    .guest-auth-actions {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(0.9); }
    }
  `]
})
export class HeaderComponent implements OnInit, OnDestroy {
  @Output() toggleMobileMenu = new EventEmitter<void>();

  currentTime = '';
  private timer: any;

  constructor(
    public alertService: AlertService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.updateClock();
    this.timer = setInterval(() => this.updateClock(), 1000);
    // Initialize alerts count
    this.alertService.getAlerts().subscribe();
  }

  ngOnDestroy(): void {
    if (this.timer) clearInterval(this.timer);
  }

  private updateClock(): void {
    const now = new Date();
    this.currentTime = now.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    });
  }
}
