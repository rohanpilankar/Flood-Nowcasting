import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ThemeService } from '../../../core/services/theme.service';

@Component({
  selector: 'app-landing-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './landing-navbar.component.html',
  styleUrl: './landing-navbar.component.scss'
})
export class LandingNavbarComponent {
  readonly themeService = inject(ThemeService);
  readonly mobileMenuOpen = signal(false);

  toggleMobileMenu(): void {
    this.mobileMenuOpen.update(v => !v);
  }

  closeMobileMenu(): void {
    this.mobileMenuOpen.set(false);
  }

  scrollToSection(sectionId: string): void {
    this.closeMobileMenu();
    if (typeof document !== 'undefined') {
      const el = document.getElementById(sectionId);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }
}
