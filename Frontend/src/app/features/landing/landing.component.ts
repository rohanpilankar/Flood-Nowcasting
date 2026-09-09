import { ChangeDetectionStrategy, Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { LandingNavbarComponent } from './navbar/landing-navbar.component';
import { HeroComponent } from './hero/hero.component';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    LandingNavbarComponent,
    HeroComponent
  ],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LandingComponent {
  readonly currentYear = new Date().getFullYear();

  scrollToTop(): void {
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }
}
