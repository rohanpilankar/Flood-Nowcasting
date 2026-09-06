import { Component, EventEmitter, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GovernmentService, BroadcastAlertPayload } from '../../../core/services/government.service';

@Component({
  selector: 'app-broadcast-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="modal-backdrop" (click)="close()">
      <div class="modal-dialog" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <div class="header-icon">📢</div>
          <div class="header-titles">
            <h3>Broadcast Emergency Warning Alert</h3>
            <p>EOC Officer Dispatch • Greater Mumbai Ward Command</p>
          </div>
          <button class="btn-close" (click)="close()">✕</button>
        </div>

        @if (successMessage()) {
          <div class="success-state">
            <div class="check-icon">✓</div>
            <h4>Emergency Alert Dispatched!</h4>
            <p>{{ successMessage() }}</p>
            <button class="btn btn-primary" (click)="close(true)">Done</button>
          </div>
        } @else {
          <form (ngSubmit)="sendBroadcast()" class="modal-body">
            @if (errorMessage()) {
              <div class="alert error">{{ errorMessage() }}</div>
            }

            <div class="form-group">
              <label>Alert Title</label>
              <input
                type="text"
                [(ngModel)]="payload.title"
                name="title"
                placeholder="e.g. Flash Flood Warning: Hindmata - Dadar Corridor"
                class="form-control"
                required
              />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Severity Level</label>
                <select [(ngModel)]="payload.severity" name="severity" class="form-control">
                  <option value="CRITICAL">CRITICAL (Imminent Inundation > 30cm)</option>
                  <option value="HIGH">HIGH (Severe Waterlogging)</option>
                  <option value="MEDIUM">MEDIUM (Caution - Water Stagnation)</option>
                  <option value="LOW">LOW (Advisory)</option>
                </select>
              </div>

              <div class="form-group">
                <label>Affected Ward</label>
                <select [(ngModel)]="payload.affected_ward" name="affected_ward" class="form-control" (change)="onWardChange()">
                  <option value="Ward F/North (Dadar / Hindmata)">Ward F/North (Dadar / Hindmata)</option>
                  <option value="Ward L (Kurla West / LBS Marg)">Ward L (Kurla West / LBS Marg)</option>
                  <option value="Ward K/West (Andheri Subway)">Ward K/West (Andheri Subway)</option>
                  <option value="Ward H/East (Bandra / Kalanagar)">Ward H/East (Bandra / Kalanagar)</option>
                  <option value="Ward G/South (Lower Parel)">Ward G/South (Lower Parel)</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label>Detailed Emergency Warning</label>
              <textarea
                [(ngModel)]="payload.message"
                name="message"
                rows="2"
                placeholder="Explain the flood situation and rising water levels..."
                class="form-control"
                required
              ></textarea>
            </div>

            <div class="form-group">
              <label>Public Safety Instructions</label>
              <input
                type="text"
                [(ngModel)]="payload.safety_instructions"
                name="safety_instructions"
                placeholder="e.g. Evacuate low-lying underpasses. Divert light motor vehicles to elevated flyover."
                class="form-control"
                required
              />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Proximity Radius (Meters)</label>
                <input
                  type="number"
                  [(ngModel)]="payload.radius_meters"
                  name="radius_meters"
                  class="form-control"
                  placeholder="500"
                />
              </div>

              <div class="form-group">
                <label>Recommended Diversion Route</label>
                <input
                  type="text"
                  [(ngModel)]="recommendedRoute"
                  name="recommendedRoute"
                  placeholder="e.g. Dr. B.A. Road Flyover"
                  class="form-control"
                />
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn btn-ghost" (click)="close()">Cancel</button>
              <button type="submit" class="btn btn-danger" [disabled]="isSending()">
                @if (isSending()) {
                  <span>Dispatching to Opted-in Citizens...</span>
                } @else {
                  <span>Broadcast Warning to Citizens</span>
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
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(6px);
      z-index: 2000;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }
    .modal-dialog {
      width: 100%;
      max-width: 580px;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
      overflow: hidden;
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
      font-size: 1.5rem;
    }
    .header-titles h3 {
      font-size: 1.15rem;
      margin: 0 0 0.2rem 0;
    }
    .header-titles p {
      font-size: 0.8rem;
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
    .btn-danger {
      background: #dc2626;
      color: white;
      padding: 0.6rem 1.2rem;
      border-radius: 8px;
      font-weight: 600;
    }
    .btn-danger:hover {
      background: #b91c1c;
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
    .check-icon {
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
  `]
})
export class BroadcastModalComponent {
  @Output() closed = new EventEmitter<boolean>();

  isSending = signal<boolean>(false);
  successMessage = signal<string | null>(null);
  errorMessage = signal<string | null>(null);
  recommendedRoute = 'Dr. B.A. Road Flyover';

  payload: BroadcastAlertPayload = {
    title: 'Flash Flood Warning: Hindmata - Dadar Corridor',
    severity: 'CRITICAL',
    flood_category: 'FLASH_FLOOD',
    affected_ward: 'Ward F/North (Dadar / Hindmata)',
    affected_landmarks: ['Hindmata Junction', 'Dadar TT Circle', 'Parel TT'],
    message: 'Rapid storm runoff accumulation exceeding 25cm. Surface drainage overwhelmed.',
    safety_instructions: 'Avoid ground-level transit. Divert to Eastern Freeway or elevated corridor.',
    recommended_safe_routes: ['Eastern Freeway via Wadala'],
    target_latitude: 19.0178,
    target_longitude: 72.8478,
    radius_meters: 500
  };

  constructor(private govService: GovernmentService) {}

  onWardChange(): void {
    if (this.payload.affected_ward.includes('Kurla')) {
      this.payload.target_latitude = 19.0688;
      this.payload.target_longitude = 72.8797;
      this.payload.affected_landmarks = ['Kurla Station West', 'LBS Marg', 'Sheetal Cinema Junction'];
    } else if (this.payload.affected_ward.includes('Andheri')) {
      this.payload.target_latitude = 19.1197;
      this.payload.target_longitude = 72.8464;
      this.payload.affected_landmarks = ['Andheri Subway', 'SV Road Junction', 'Gokhale Bridge Approach'];
    } else if (this.payload.affected_ward.includes('Bandra')) {
      this.payload.target_latitude = 19.0596;
      this.payload.target_longitude = 72.8656;
      this.payload.affected_landmarks = ['BKC Connector', 'Kalanagar Junction'];
    } else {
      this.payload.target_latitude = 19.0178;
      this.payload.target_longitude = 72.8478;
      this.payload.affected_landmarks = ['Hindmata Junction', 'Dadar TT Circle'];
    }
  }

  sendBroadcast(): void {
    this.isSending.set(true);
    this.errorMessage.set(null);

    this.payload.recommended_safe_routes = [this.recommendedRoute];

    this.govService.broadcastAlert(this.payload).subscribe({
      next: (res) => {
        this.isSending.set(false);
        this.successMessage.set(`Targeted delivery completed to ${res.citizens_notified_count || 1} registered citizens in geofence.`);
      },
      error: (err) => {
        this.isSending.set(false);
        this.errorMessage.set(err?.error?.detail || 'Failed to dispatch broadcast warning.');
      }
    });
  }

  close(refreshed: boolean = false): void {
    this.closed.emit(refreshed);
  }
}
