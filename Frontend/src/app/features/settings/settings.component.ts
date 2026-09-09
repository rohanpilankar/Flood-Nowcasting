import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SettingsService } from '../../core/services/settings.service';
import { AppSettings } from '../../core/models/settings.model';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  template: `
    <div class="settings-page">
      <!-- Header -->
      <div class="card settings-header">
        <div>
          <div class="title-with-badge">
            <h2 class="page-title">Application Settings</h2>
            <span class="badge-role">Local Configuration</span>
          </div>
          <p class="page-sub">Tune AI prediction thresholds, alert broadcast rules, and GIS visual layers</p>
        </div>

        <div class="header-actions">
          <button type="button" class="btn btn-secondary btn-sm" (click)="resetDefaults()">
            Reset Defaults
          </button>
          <button type="button" class="btn btn-primary btn-sm" (click)="save()">
            Save Configuration
          </button>
        </div>
      </div>

      <!-- Save Toast Notice -->
      @if (showToast) {
        <div class="toast-banner animate-fade">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span>Preferences saved to browser LocalStorage and applied reactively.</span>
        </div>
      }

      <div class="settings-grid">
        <!-- Card 1: Prediction & AI Parameters -->
        <div class="card setting-section-card">
          <div class="card-header">
            <div>
              <h3 class="card-title">Prediction & Nowcasting Model</h3>
              <p class="card-subtitle">Tune AI spatial resolution and risk categorization boundaries</p>
            </div>
          </div>

          <div class="form-fields-list">
            <!-- Grid Size -->
            <div class="form-group">
              <label class="form-label" for="gridRes">Spatial Grid Resolution</label>
              <select id="gridRes" class="form-select" [(ngModel)]="formSettings.gridResolution">
                <option value="FINE">Fine Grid (250m × 250m Catchment Cells)</option>
                <option value="MEDIUM">Medium Grid (500m × 500m - Default)</option>
                <option value="COARSE">Coarse Grid (1km × 1km Basin Overview)</option>
              </select>
              <span class="field-hint">Defines the granularity of hydrodynamic flood polygon meshes.</span>
            </div>

            <!-- High Risk Threshold -->
            <div class="form-group">
              <div class="label-with-val">
                <label class="form-label" for="highThresh">High-Risk Threshold</label>
                <span class="val-display font-mono text-danger">{{ formSettings.highRiskThreshold }}%</span>
              </div>
              <input
                id="highThresh"
                type="range"
                min="60"
                max="95"
                step="1"
                class="form-range"
                [(ngModel)]="formSettings.highRiskThreshold"
              />
              <span class="field-hint">Grid sectors at or above this score trigger emergency priority alerts.</span>
            </div>

            <!-- Medium Risk Threshold -->
            <div class="form-group">
              <div class="label-with-val">
                <label class="form-label" for="medThresh">Medium-Risk Threshold</label>
                <span class="val-display font-mono text-warning">{{ formSettings.mediumRiskThreshold }}%</span>
              </div>
              <input
                id="medThresh"
                type="range"
                min="30"
                max="75"
                step="1"
                class="form-range"
                [(ngModel)]="formSettings.mediumRiskThreshold"
              />
              <span class="field-hint">Sectors triggering precautionary advisory status.</span>
            </div>

            <!-- Prediction Horizon -->
            <div class="form-group">
              <label class="form-label" for="predHorizon">Default Prediction Horizon</label>
              <select id="predHorizon" class="form-select" [(ngModel)]="formSettings.predictionHorizon">
                <option value="NOW">NOW (Real-time current radar state)</option>
                <option value="+30M">+30 Minutes (Short-term convective burst)</option>
                <option value="+1H">+1 Hour (Primary nowcasting window - Default)</option>
                <option value="+2H">+2 Hours (Medium forecast)</option>
                <option value="+3H">+3 Hours (Extended recession trajectory)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Card 2: Emergency Alert Rules -->
        <div class="card setting-section-card">
          <div class="card-header">
            <div>
              <h3 class="card-title">Emergency Alert Rules</h3>
              <p class="card-subtitle">Configure broadcast thresholds and auto-refresh intervals</p>
            </div>
          </div>

          <div class="form-fields-list">
            <!-- Toggle: High-Risk Alerts -->
            <div class="toggle-group">
              <div class="toggle-info">
                <span class="toggle-title">Enable High-Risk Alerts</span>
                <span class="toggle-desc">Automatically surface urgent incident cards for severe waterlogging.</span>
              </div>
              <label class="switch">
                <input type="checkbox" [(ngModel)]="formSettings.enableHighRiskAlerts" />
                <span class="slider"></span>
              </label>
            </div>

            <!-- Alert Threshold -->
            <div class="form-group">
              <div class="label-with-val">
                <label class="form-label" for="alertThresh">Dispatch Alert Trigger Threshold</label>
                <span class="val-display font-mono text-brand">{{ formSettings.alertThreshold }}%</span>
              </div>
              <input
                id="alertThresh"
                type="range"
                min="50"
                max="95"
                step="1"
                class="form-range"
                [(ngModel)]="formSettings.alertThreshold"
              />
            </div>

            <!-- Auto-Refresh Interval -->
            <div class="form-group">
              <label class="form-label" for="refreshInt">Auto-Refresh Ingestion Interval</label>
              <select id="refreshInt" class="form-select" [(ngModel)]="formSettings.autoRefreshIntervalSec">
                <option [ngValue]="15">Every 15 Seconds (Rapid EOC polling)</option>
                <option [ngValue]="30">Every 30 Seconds (Default Standard)</option>
                <option [ngValue]="60">Every 60 Seconds (Low bandwidth)</option>
              </select>
              <span class="field-hint">Frequency of sensor and telemetry refresh requests.</span>
            </div>

            <!-- Sound Alerts -->
            <div class="toggle-group">
              <div class="toggle-info">
                <span class="toggle-title">Audio Siren Feedback</span>
                <span class="toggle-desc">Play audible chime on high-priority flood alert generation.</span>
              </div>
              <label class="switch">
                <input type="checkbox" [(ngModel)]="formSettings.soundAlerts" />
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </div>

        <!-- Card 3: GIS Map Visual Overlays -->
        <div class="card setting-section-card">
          <div class="card-header">
            <div>
              <h3 class="card-title">GIS Map Display Layers</h3>
              <p class="card-subtitle">Set default visual layers and overlays on startup</p>
            </div>
          </div>

          <div class="form-fields-list">
            <!-- Default Layer -->
            <div class="form-group">
              <label class="form-label" for="defLayer">Default Active GIS Layer</label>
              <select id="defLayer" class="form-select" [(ngModel)]="formSettings.defaultMapLayer">
                <option value="ALL">All Layers Composite (Flood + Roads + Rainfall + Drainage)</option>
                <option value="RISK">Flood Risk Polygons Only</option>
                <option value="ROADS">Road Network & Arterials</option>
                <option value="RAINFALL">Radar Rainfall Intensity</option>
              </select>
            </div>

            <!-- Flood Grid Visibility -->
            <div class="toggle-group">
              <div class="toggle-info">
                <span class="toggle-title">Flood Risk Grid Polygons</span>
                <span class="toggle-desc">Render color-coded semantic risk boundary rectangles.</span>
              </div>
              <label class="switch">
                <input type="checkbox" [(ngModel)]="formSettings.mapGridVisibility" />
                <span class="slider"></span>
              </label>
            </div>

            <!-- Road Layer Visibility -->
            <div class="toggle-group">
              <div class="toggle-info">
                <span class="toggle-title">Road Corridors & Blockages</span>
                <span class="toggle-desc">Highlight affected arterial transit paths.</span>
              </div>
              <label class="switch">
                <input type="checkbox" [(ngModel)]="formSettings.roadLayerVisibility" />
                <span class="slider"></span>
              </label>
            </div>

            <!-- Rainfall Radar Visibility -->
            <div class="toggle-group">
              <div class="toggle-info">
                <span class="toggle-title">Precipitation Radar Overlay</span>
                <span class="toggle-desc">Display convective storm cell overlay.</span>
              </div>
              <label class="switch">
                <input type="checkbox" [(ngModel)]="formSettings.rainfallOverlayVisibility" />
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </div>

        <!-- Card 4: Prototype & Local Storage Info -->
        <div class="card setting-section-card">
          <div class="card-header">
            <div>
              <h3 class="card-title">Local Storage & State</h3>
              <p class="card-subtitle">Configuration persistence details</p>
            </div>
          </div>

          <div class="storage-info-box">
            <p>
              Settings are stored client-side in browser <strong>LocalStorage</strong> under key:
              <code class="font-mono">floodwatch_ai_settings_v1</code>.
            </p>
            <p style="margin-top: 0.5rem;">
              These settings sync with your active browser profile and the backend API.
            </p>
          </div>

          <button type="button" class="btn btn-outline btn-sm" (click)="resetDefaults()" style="align-self: flex-start; margin-top: 1rem;">
            Restore All System Defaults
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .settings-page {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
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

    .settings-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .toast-banner {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      background-color: rgba(16, 185, 129, 0.15);
      border: 1px solid var(--status-safe);
      color: #6ee7b7;
      padding: 0.75rem 1rem;
      border-radius: var(--radius-md);
      font-size: 0.825rem;
      font-weight: 500;
    }

    .settings-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.25rem;
      @media (max-width: 990px) {
        grid-template-columns: 1fr;
      }
    }

    .setting-section-card {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .form-fields-list {
      display: flex;
      flex-direction: column;
      gap: 1.1rem;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .form-label {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-main);
    }
    .label-with-val {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .val-display {
      font-size: 0.85rem;
      font-weight: 700;
    }
    .form-select {
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 0.55rem 0.85rem;
      color: var(--text-main);
      font-size: 0.825rem;
      outline: none;

      &:focus {
        border-color: var(--brand-primary);
      }
    }
    .form-range {
      width: 100%;
      accent-color: var(--brand-primary);
      cursor: pointer;
    }
    .field-hint {
      font-size: 0.72rem;
      color: var(--text-dim);
    }

    .toggle-group {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 0.4rem 0;
    }
    .toggle-info {
      display: flex;
      flex-direction: column;
    }
    .toggle-title {
      font-size: 0.825rem;
      font-weight: 600;
      color: var(--text-main);
    }
    .toggle-desc {
      font-size: 0.72rem;
      color: var(--text-muted);
    }

    // Toggle Switch
    .switch {
      position: relative;
      display: inline-block;
      width: 44px;
      height: 24px;
      flex-shrink: 0;

      input {
        opacity: 0;
        width: 0;
        height: 0;
      }
    }
    .slider {
      position: absolute;
      cursor: pointer;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
      transition: .25s;
      border-radius: 24px;

      &:before {
        position: absolute;
        content: "";
        height: 16px;
        width: 16px;
        left: 3px;
        bottom: 3px;
        background-color: var(--text-dim);
        transition: .25s;
        border-radius: 50%;
      }
    }
    input:checked + .slider {
      background-color: var(--brand-primary);
      border-color: var(--brand-primary);
    }
    input:checked + .slider:before {
      transform: translateX(20px);
      background-color: #ffffff;
    }

    .storage-info-box {
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.85rem;
      font-size: 0.8rem;
      color: var(--text-muted);
      line-height: 1.45;

      code {
        color: #93c5fd;
      }
    }
  `]
})
export class SettingsComponent implements OnInit {
  formSettings!: AppSettings;
  showToast = false;

  constructor(private settingsService: SettingsService) {}

  ngOnInit(): void {
    this.formSettings = { ...this.settingsService.settings() };
  }

  save(): void {
    this.settingsService.saveSettings(this.formSettings);
    this.showToast = true;
    setTimeout(() => {
      this.showToast = false;
    }, 3500);
  }

  resetDefaults(): void {
    this.settingsService.resetToDefaults();
    this.formSettings = { ...this.settingsService.settings() };
    this.showToast = true;
    setTimeout(() => {
      this.showToast = false;
    }, 3500);
  }
}
