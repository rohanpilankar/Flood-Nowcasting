import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="login-wrapper">
      <div class="login-bg-overlay"></div>
      
      <div class="login-container">
        <!-- Brand Header -->
        <div class="login-brand">
          <div class="brand-logo-badge">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
              <path d="M2 17l10 5 10-5"></path>
              <path d="M2 12l10 5 10-5"></path>
            </svg>
          </div>
          <h1 class="brand-title">FloodWatch AI</h1>
          <p class="brand-subtitle">Urban Flood Nowcasting & Safe Mobility System — Greater Mumbai</p>
          <div class="sih-tag">SIH26085 • BMC Disaster Management</div>
        </div>

        <!-- Login Card -->
        <div class="glass-card login-card">
          <div class="card-header">
            <h2>Portal Sign In</h2>
            <p>Access citizen safety services, authority controls, or system admin</p>
          </div>

          @if (errorMessage()) {
            <div class="alert-banner error">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <span>{{ errorMessage() }}</span>
            </div>
          }

          <form (ngSubmit)="onSubmit()" class="login-form">
            <div class="form-group">
              <label for="loginId">Email Address or Mobile Number</label>
              <div class="input-icon-wrap">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
                <input
                  id="loginId"
                  name="loginId"
                  type="text"
                  [(ngModel)]="loginId"
                  placeholder="e.g. rohan.citizen@gmail.com or 9820112233"
                  required
                  autocomplete="username"
                  class="form-control"
                />
              </div>
            </div>

            <div class="form-group">
              <div class="label-row">
                <label for="password">Password</label>
              </div>
              <div class="input-icon-wrap">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
                <input
                  id="password"
                  name="password"
                  [type]="showPassword() ? 'text' : 'password'"
                  [(ngModel)]="password"
                  placeholder="Enter your password"
                  required
                  autocomplete="current-password"
                  class="form-control"
                />
                <button
                  type="button"
                  class="btn-toggle-pwd"
                  (click)="showPassword.set(!showPassword())"
                  aria-label="Toggle password visibility"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    @if (showPassword()) {
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                      <line x1="1" y1="1" x2="23" y2="23"></line>
                    } @else {
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="10" r="3"></circle>
                    }
                  </svg>
                </button>
              </div>
            </div>

            <div class="form-options">
              <label class="checkbox-label">
                <input type="checkbox" [(ngModel)]="rememberMe" name="rememberMe" />
                <span>Keep me signed in</span>
              </label>
            </div>

            <button type="submit" class="btn btn-primary btn-block btn-lg" [disabled]="isLoading()">
              @if (isLoading()) {
                <span class="spinner"></span>
                <span>Authenticating...</span>
              } @else {
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
                  <polyline points="10 17 15 12 10 7"></polyline>
                  <line x1="15" y1="12" x2="3" y2="12"></line>
                </svg>
                <span>Sign In to FloodWatch</span>
              }
            </button>
          </form>

          <!-- Quick Switcher for Evaluation -->
          <div class="quick-demo-section">
            <div class="divider">
              <span>OR TEST WITH DEMO ROLES</span>
            </div>
            <div class="quick-role-buttons">
              <button type="button" class="btn-demo citizen" (click)="fillDemo('citizen')">
                <span class="role-icon">👤</span>
                <span class="role-text">Citizen</span>
              </button>
              <button type="button" class="btn-demo gov" (click)="fillDemo('gov')">
                <span class="role-icon">🏛️</span>
                <span class="role-text">EOC Officer</span>
              </button>
              <button type="button" class="btn-demo admin" (click)="fillDemo('admin')">
                <span class="role-icon">🛡️</span>
                <span class="role-text">System Admin</span>
              </button>
            </div>
          </div>

          <div class="card-footer">
            <p>New to FloodWatch Mumbai? <a routerLink="/register" class="link-register">Register as Citizen</a></p>
          </div>
        </div>

        <div class="disclaimer-note">
          <span>🔒 Government of Maharashtra & BMC Disaster Management Cell. Consent-gated spatial warning system.</span>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .login-wrapper {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: radial-gradient(circle at 50% 20%, #0d2238 0%, var(--bg-darkest) 75%);
      position: relative;
      padding: 2rem 1rem;
    }
    .login-bg-overlay {
      position: absolute;
      inset: 0;
      background-image: 
        radial-gradient(rgba(59, 130, 246, 0.08) 1px, transparent 1px),
        radial-gradient(rgba(14, 165, 233, 0.05) 1px, transparent 1px);
      background-size: 32px 32px, 16px 16px;
      pointer-events: none;
    }
    .login-container {
      width: 100%;
      max-width: 460px;
      position: relative;
      z-index: 10;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .login-brand {
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .brand-logo-badge {
      width: 52px;
      height: 52px;
      border-radius: 14px;
      background: linear-gradient(135deg, #2563eb, #0284c7);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      box-shadow: 0 8px 24px rgba(37, 99, 235, 0.35);
      margin-bottom: 0.8rem;
    }
    .brand-title {
      font-size: 1.85rem;
      font-weight: 700;
      color: var(--text-main);
      margin: 0;
      letter-spacing: -0.02em;
    }
    .brand-subtitle {
      font-size: 0.88rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
      line-height: 1.4;
    }
    .sih-tag {
      margin-top: 0.5rem;
      font-size: 0.72rem;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      color: #60a5fa;
      background: rgba(37, 99, 235, 0.12);
      border: 1px solid rgba(96, 165, 250, 0.25);
      padding: 0.2rem 0.65rem;
      border-radius: 9999px;
    }
    .login-card {
      background: rgba(18, 26, 38, 0.85);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 2rem;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4);
    }
    .card-header {
      margin-bottom: 1.5rem;
    }
    .card-header h2 {
      font-size: 1.28rem;
      font-weight: 600;
      color: var(--text-main);
      margin: 0 0 0.3rem 0;
    }
    .card-header p {
      font-size: 0.82rem;
      color: var(--text-dim);
      margin: 0;
    }
    .alert-banner.error {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      background: rgba(239, 68, 68, 0.12);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #fca5a5;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      font-size: 0.84rem;
      margin-bottom: 1.25rem;
    }
    .login-form {
      display: flex;
      flex-direction: column;
      gap: 1.2rem;
    }
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }
    .form-group label {
      font-size: 0.82rem;
      font-weight: 500;
      color: var(--text-muted);
    }
    .input-icon-wrap {
      position: relative;
      display: flex;
      align-items: center;
    }
    .input-icon-wrap svg {
      position: absolute;
      left: 12px;
      color: var(--text-dim);
      pointer-events: none;
    }
    .form-control {
      width: 100%;
      background: rgba(11, 17, 26, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 0.72rem 1rem 0.72rem 2.4rem;
      color: var(--text-main);
      font-size: 0.9rem;
      transition: all 0.2s ease;
    }
    .form-control:focus {
      outline: none;
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }
    .btn-toggle-pwd {
      position: absolute;
      right: 12px;
      color: var(--text-dim);
      padding: 4px;
    }
    .btn-toggle-pwd:hover {
      color: var(--text-main);
    }
    .form-options {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.82rem;
    }
    .checkbox-label {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--text-dim);
      cursor: pointer;
    }
    .btn-block {
      width: 100%;
      justify-content: center;
      gap: 0.5rem;
      padding: 0.78rem;
      font-weight: 600;
      border-radius: 8px;
      background: linear-gradient(135deg, #2563eb, #1d4ed8);
      color: white;
      border: none;
    }
    .btn-block:hover:not(:disabled) {
      background: linear-gradient(135deg, #1d4ed8, #1e40af);
      box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
    }
    .quick-demo-section {
      margin-top: 1.5rem;
    }
    .divider {
      display: flex;
      align-items: center;
      text-align: center;
      color: var(--text-dim);
      font-size: 0.68rem;
      letter-spacing: 0.05em;
      margin-bottom: 0.9rem;
    }
    .divider::before, .divider::after {
      content: '';
      flex: 1;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .divider span {
      padding: 0 0.65rem;
    }
    .quick-role-buttons {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.5rem;
    }
    .btn-demo {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.25rem;
      padding: 0.6rem 0.4rem;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 8px;
      color: var(--text-muted);
      font-size: 0.75rem;
      transition: all 0.2s ease;
    }
    .btn-demo:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.2);
      color: var(--text-main);
    }
    .btn-demo.citizen:hover { border-color: #3b82f6; }
    .btn-demo.gov:hover { border-color: #10b981; }
    .btn-demo.admin:hover { border-color: #f59e0b; }
    .card-footer {
      margin-top: 1.5rem;
      text-align: center;
      font-size: 0.84rem;
      color: var(--text-dim);
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      padding-top: 1.2rem;
    }
    .link-register {
      color: #60a5fa;
      text-decoration: none;
      font-weight: 500;
    }
    .link-register:hover {
      text-decoration: underline;
    }
    .disclaimer-note {
      text-align: center;
      font-size: 0.72rem;
      color: var(--text-dim);
    }
    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      border-top-color: white;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `]
})
export class LoginComponent {
  loginId = '';
  password = '';
  rememberMe = true;
  showPassword = signal(false);
  isLoading = signal(false);
  errorMessage = signal<string | null>(null);

  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  fillDemo(role: 'citizen' | 'gov' | 'admin'): void {
    this.errorMessage.set(null);
    if (role === 'citizen') {
      this.loginId = 'rohan.citizen@gmail.com';
      this.password = 'Citizen@2026';
    } else if (role === 'gov') {
      this.loginId = 'eoc.officer@mcgm.gov.in';
      this.password = 'Gov@Mumbai2026';
    } else if (role === 'admin') {
      this.loginId = 'admin@floodwatch.mumbai.gov.in';
      this.password = 'Admin@Mumbai2026';
    }
  }

  onSubmit(): void {
    if (!this.loginId || !this.password) {
      this.errorMessage.set('Please enter both your login ID and password.');
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.authService.login({
      login_id: this.loginId,
      password: this.password,
      remember_me: this.rememberMe
    }).subscribe({
      next: () => {
        this.isLoading.set(false);
        const returnUrl = this.route.snapshot.queryParams['returnUrl'];
        if (returnUrl) {
          this.router.navigateByUrl(returnUrl);
        } else {
          this.authService.navigatePostLogin();
        }
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err?.error?.detail || 'Authentication failed. Please verify credentials.');
      }
    });
  }
}
