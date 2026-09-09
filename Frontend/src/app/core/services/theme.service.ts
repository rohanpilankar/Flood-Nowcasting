import { Injectable, signal, effect } from '@angular/core';

export type AppTheme = 'dark' | 'light';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly storageKey = 'floodwatch_theme';
  readonly currentTheme = signal<AppTheme>(this.getInitialTheme());

  constructor() {
    this.applyTheme(this.currentTheme());
  }

  private getInitialTheme(): AppTheme {
    if (typeof window !== 'undefined' && window.localStorage) {
      const saved = localStorage.getItem(this.storageKey) as AppTheme | null;
      if (saved === 'light' || saved === 'dark') {
        return saved;
      }
      // Check system preference
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
        return 'light';
      }
    }
    return 'dark'; // Default dark for operations center feel
  }

  toggleTheme(): void {
    const nextTheme: AppTheme = this.currentTheme() === 'dark' ? 'light' : 'dark';
    this.setTheme(nextTheme);
  }

  setTheme(theme: AppTheme): void {
    this.currentTheme.set(theme);
    this.applyTheme(theme);
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.setItem(this.storageKey, theme);
    }
  }

  private applyTheme(theme: AppTheme): void {
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme);
      if (theme === 'light') {
        document.documentElement.classList.add('theme-light');
        document.documentElement.classList.remove('theme-dark');
      } else {
        document.documentElement.classList.add('theme-dark');
        document.documentElement.classList.remove('theme-light');
      }
    }
  }
}
