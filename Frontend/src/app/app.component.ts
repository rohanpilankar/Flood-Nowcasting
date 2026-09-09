import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { NavigationEnd, NavigationStart, Router, RouterOutlet, Event } from '@angular/router';
import { filter } from 'rxjs/operators';
import { HeaderComponent } from './shared/components/header/header.component';
import { SidebarComponent } from './shared/components/sidebar/sidebar.component';
import { ThemeService } from './core/services/theme.service';

/** Routes on which the sidebar/header shell is hidden. */
const SHELL_HIDDEN_ROUTES = ['/home', '/', '', '/login', '/register'];

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    HeaderComponent,
    SidebarComponent
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  readonly sidebarCollapsed = signal(false);
  readonly mobileMenuOpen = signal(false);

  /** True when the current route is a standalone page (landing/hero/auth). */
  readonly isShellHidden = signal(this.detectInitialShellState());

  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  private readonly themeService = inject(ThemeService); // Eagerly initializes theme

  constructor() {
    this.router.events
      .pipe(
        filter((e): e is NavigationStart | NavigationEnd => 
          e instanceof NavigationStart || e instanceof NavigationEnd
        ),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe((e) => {
        const targetUrl = e.url.split('?')[0];
        const isHidden = SHELL_HIDDEN_ROUTES.includes(targetUrl);
        if (this.isShellHidden() !== isHidden) {
          this.isShellHidden.set(isHidden);
        }
      });
  }

  private detectInitialShellState(): boolean {
    if (typeof window !== 'undefined') {
      const pathname = window.location.pathname.replace(/\/$/, '') || '/';
      return SHELL_HIDDEN_ROUTES.includes(pathname);
    }
    return true; // Default to hidden on SSR / initial paint to avoid dashboard flash
  }

  toggleSidebarCollapse(): void {
    this.sidebarCollapsed.update(v => !v);
  }

  toggleMobileMenu(): void {
    this.mobileMenuOpen.update(v => !v);
  }

  closeMobileMenu(): void {
    this.mobileMenuOpen.set(false);
  }
}
