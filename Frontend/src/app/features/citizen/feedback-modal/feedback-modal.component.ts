import { Component, EventEmitter, Input, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FeedbackService, CitizenFloodReportPayload } from '../../../core/services/feedback.service';
import { CitizenLocationService } from '../../../core/services/citizen-location.service';

@Component({
  selector: 'app-feedback-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="modal-backdrop" (click)="close()">
      <div class="modal-dialog" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <div class="header-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
          </div>
          <div class="header-titles">
            <h3>Report Waterlogging Observation</h3>
            <p>Help validate FloodWatch AI models with ground-truth data</p>
          </div>
          <button class="btn-close" (click)="close()">✕</button>
        </div>

        @if (submittedSuccess()) {
          <div class="success-state">
            <div class="success-icon">✓</div>
            <h4>Observation Submitted Successfully!</h4>
            <p>
              Report Code: <strong class="font-mono">{{ reportCode() }}</strong><br />
              Status: <span class="badge-unverified">UNVERIFIED (Under EOC Review)</span>
            </p>
            <p class="sub">Thank you for contributing to Greater Mumbai's crowd-sourced flood resilience.</p>
            <button class="btn btn-primary" (click)="close()">Close</button>
          </div>
        } @else {
          <form (ngSubmit)="submitReport()" class="modal-body">
            @if (errorMessage()) {
              <div class="alert error">{{ errorMessage() }}</div>
            }

            <div class="form-group">
              <label>Location / Landmark</label>
              <input
                type="text"
                [(ngModel)]="payload.location_name"
                name="location_name"
                placeholder="e.g. Hindmata Flyover Underpass, Dadar East"
                class="form-control"
                required
              />
              <span class="hint">GPS Coords: {{ payload.latitude.toFixed(4) }}, {{ payload.longitude.toFixed(4) }}</span>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Water Depth Level</label>
                <select [(ngModel)]="payload.water_depth_level" name="water_depth_level" class="form-control" (change)="onDepthChange()">
                  <option value="ANKLE_DEEP">Ankle Deep (5 - 15 cm)</option>
                  <option value="KNEE_DEEP">Knee Deep (15 - 40 cm)</option>
                  <option value="WAIST_DEEP">Waist Deep (40 - 80 cm)</option>
                  <option value="SUBMERGED">Submerged / Severe (> 80 cm)</option>
                </select>
              </div>

              <div class="form-group">
                <label>Estimated Depth (cm)</label>
                <input
                  type="number"
                  [(ngModel)]="payload.water_depth_cm"
                  name="water_depth_cm"
                  class="form-control"
                  placeholder="e.g. 25"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Traffic Disruption</label>
                <select [(ngModel)]="payload.traffic_disruption" name="traffic_disruption" class="form-control">
                  <option value="NORMAL">Normal Traffic</option>
                  <option value="SLOW">Slow / Crawling Traffic</option>
                  <option value="HALTED">Completely Halted / Waterlogged</option>
                  <option value="DIVERSIFIED">Police Diversion in Place</option>
                </select>
              </div>

              <div class="form-group">
                <label>Rainfall Intensity</label>
                <select [(ngModel)]="payload.rainfall_intensity" name="rainfall_intensity" class="form-control">
                  <option value="NO_RAIN">No Rain</option>
                  <option value="LIGHT">Light Drizzle</option>
                  <option value="MODERATE">Moderate Rain</option>
                  <option value="HEAVY">Heavy Downpour</option>
                  <option value="TORRENTIAL">Torrential Rain (>50mm/hr)</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label>Field Notes / Description (Optional)</label>
              <textarea
                [(ngModel)]="payload.description"
                name="description"
                rows="2"
                placeholder="e.g. Water accumulation rising fast on northbound carriageway, buses taking service lane."
                class="form-control"
              ></textarea>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn btn-ghost" (click)="close()">Cancel</button>
              <button type="submit" class="btn btn-primary" [disabled]="isSubmitting()">
                @if (isSubmitting()) {
                  <span>Submitting...</span>
                } @else {
                  <span>Submit Ground Truth Report</span>
                }
              </button>
            </div>
          </form>
        }
      </div>
    </div>
  `,
  styles: [`
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(6px);
      z-index: 2000;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }
    .modal-dialog {
      width: 100%;
      max-width: 520px;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
      overflow: hidden;
      animation: fadeIn 0.2s ease-out;
    }
    .modal-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1.2rem 1.5rem;
      border-bottom: 1px solid var(--border-subtle);
      position: relative;
    }
    .header-icon {
      color: #38bdf8;
      background: rgba(56, 189, 248, 0.12);
      padding: 0.5rem;
      border-radius: 10px;
    }
    .header-titles h3 {
      font-size: 1.1rem;
      margin: 0 0 0.15rem 0;
    }
    .header-titles p {
      font-size: 0.78rem;
      color: var(--text-dim);
      margin: 0;
    }
    .btn-close {
      position: absolute;
      right: 1.2rem;
      top: 1.2rem;
      font-size: 1.1rem;
      color: var(--text-dim);
    }
    .modal-body {
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .form-group label {
      font-size: 0.8rem;
      font-weight: 500;
      color: var(--text-muted);
    }
    .hint {
      font-size: 0.72rem;
      color: var(--text-dim);
      font-family: 'JetBrains Mono', monospace;
    }
    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }
    .form-control {
      background: rgba(11, 17, 26, 0.8);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 0.6rem 0.8rem;
      color: var(--text-main);
      font-size: 0.86rem;
    }
    .form-control:focus {
      outline: none;
      border-color: #3b82f6;
    }
    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 0.8rem;
      margin-top: 0.5rem;
    }
    .alert.error {
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #fca5a5;
      padding: 0.6rem 0.8rem;
      border-radius: 6px;
      font-size: 0.82rem;
    }
    .success-state {
      padding: 2.5rem 1.5rem;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.8rem;
    }
    .success-icon {
      width: 50px;
      height: 50px;
      border-radius: 50%;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      font-size: 1.5rem;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
    }
    .badge-unverified {
      font-size: 0.72rem;
      background: rgba(245, 158, 11, 0.2);
      color: #f59e0b;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-weight: 600;
    }
    .sub {
      font-size: 0.82rem;
      color: var(--text-dim);
      margin: 0;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: scale(0.96); }
      to { opacity: 1; transform: scale(1); }
    }
  `]
})
export class FeedbackModalComponent {
  @Input() initialArea: string = 'Dadar TT / Hindmata Junction';
  @Output() closed = new EventEmitter<void>();

  isSubmitting = signal<boolean>(false);
  submittedSuccess = signal<boolean>(false);
  reportCode = signal<string>('');
  errorMessage = signal<string | null>(null);

  payload: CitizenFloodReportPayload = {
    latitude: 19.0178,
    longitude: 72.8478,
    location_name: this.initialArea,
    water_depth_level: 'KNEE_DEEP',
    water_depth_cm: 25,
    traffic_disruption: 'SLOW',
    rainfall_intensity: 'HEAVY',
    description: ''
  };

  constructor(
    private feedbackService: FeedbackService,
    private locationService: CitizenLocationService
  ) {
    const pos = this.locationService.currentPosition();
    if (pos) {
      this.payload.latitude = pos.lat;
      this.payload.longitude = pos.lon;
    }
  }

  onDepthChange(): void {
    if (this.payload.water_depth_level === 'ANKLE_DEEP') this.payload.water_depth_cm = 10;
    else if (this.payload.water_depth_level === 'KNEE_DEEP') this.payload.water_depth_cm = 25;
    else if (this.payload.water_depth_level === 'WAIST_DEEP') this.payload.water_depth_cm = 50;
    else if (this.payload.water_depth_level === 'SUBMERGED') this.payload.water_depth_cm = 90;
  }

  submitReport(): void {
    this.isSubmitting.set(true);
    this.errorMessage.set(null);

    this.feedbackService.submitReport(this.payload).subscribe({
      next: (res) => {
        this.isSubmitting.set(false);
        this.submittedSuccess.set(true);
        this.reportCode.set(res.report_code);
      },
      error: (err) => {
        this.isSubmitting.set(false);
        this.errorMessage.set(err?.error?.detail || 'Failed to submit report. Please try again.');
      }
    });
  }

  close(): void {
    this.closed.emit();
  }
}
