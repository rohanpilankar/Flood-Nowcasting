import { Injectable, signal } from '@angular/core';
import { AppSettings, DEFAULT_SETTINGS } from '../models/settings.model';

const STORAGE_KEY = 'floodwatch_ai_settings_v1';

@Injectable({
  providedIn: 'root'
})
export class SettingsService {
  private currentSettings = signal<AppSettings>(this.loadFromStorage());
  readonly settings = this.currentSettings.asReadonly();

  constructor() {}

  private loadFromStorage(): AppSettings {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
      }
    } catch (e) {
      console.warn('Could not read settings from localStorage, using defaults', e);
    }
    return { ...DEFAULT_SETTINGS };
  }

  saveSettings(newSettings: Partial<AppSettings>): void {
    const updated = { ...this.currentSettings(), ...newSettings };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      console.error('Failed to write settings to localStorage', e);
    }
    this.currentSettings.set(updated);
  }

  resetToDefaults(): void {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.warn(e);
    }
    this.currentSettings.set({ ...DEFAULT_SETTINGS });
  }
}
