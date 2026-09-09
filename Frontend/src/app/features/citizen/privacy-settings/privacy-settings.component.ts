import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CitizenLocationService, SavedLocation, EmergencyContact } from '../../../core/services/citizen-location.service';
import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-privacy-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="privacy-page">
      <div class="page-header">
        <div>
          <span class="sub-tag">DATA PRIVACY & CITIZEN SAFETY</span>
          <h1>Privacy Controls & Saved Locations</h1>
          <p>Full control over your location sharing, historical tracking data, and emergency contacts</p>
        </div>
      </div>

      @if (statusMessage()) {
        <div class="toast-banner" [class.success]="isSuccess()">
          <span>{{ statusMessage() }}</span>
        </div>
      }

      <div class="settings-grid">
        <!-- 1. Explicit Consent & Geolocation -->
        <div class="glass-card section-card">
          <div class="card-header">
            <div class="header-icon">🔒</div>
            <div>
              <h3>Location Sharing Consent</h3>
              <p>Consent-gated spatial warning architecture</p>
            </div>
          </div>

          <div class="consent-toggle-row">
            <div class="toggle-desc">
              <strong>Active Location Sharing</strong>
              <span>When enabled, your device transmits coordinates solely to evaluate proximity to flood hazard zones. Coordinates are never public.</span>
            </div>
            <label class="switch">
              <input type="checkbox" [checked]="locationService.consentStatus()" (change)="toggleConsent($event)" />
              <span class="slider"></span>
            </label>
          </div>

          <div class="purge-actions">
            <span class="section-subtitle">Data Erasure & Self-Service Privacy</span>
            <div class="btn-action-group">
              <button class="btn btn-outline-danger" (click)="purgeCurrentSession()">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
                Purge Active Session
              </button>
              <button class="btn btn-danger" (click)="deleteCompleteHistory()">
                Delete Complete Location History
              </button>
            </div>
          </div>
        </div>

        <!-- 2. Saved Locations (Home / Work) -->
        <div class="glass-card section-card">
          <div class="card-header">
            <div class="header-icon">📍</div>
            <div class="header-text-flex">
              <div>
                <h3>Monitored Places</h3>
                <p>Receive flood alerts for your residence or workplace even when offline</p>
              </div>
              <button class="btn btn-sm btn-primary" (click)="showAddLocation.set(true)">
                + Add Place
              </button>
            </div>
          </div>

          <!-- Add Location Form -->
          @if (showAddLocation()) {
            <div class="inline-form-card">
              <h4>Add Monitored Place</h4>
              <div class="form-row">
                <input type="text" [(ngModel)]="newPlace.label" placeholder="Label (e.g. Home, Office)" class="form-control" />
                <select [(ngModel)]="newPlace.wardPreset" (change)="applyWardPreset()" class="form-control">
                  <option value="">-- Select Mumbai Ward Preset --</option>
                  <option value="Dadar">Ward F/N: Dadar / Hindmata (19.0178, 72.8478)</option>
                  <option value="Kurla">Ward L: Kurla West / LBS (19.0688, 72.8797)</option>
                  <option value="Andheri">Ward K/W: Andheri Subway (19.1197, 72.8464)</option>
                  <option value="Bandra">Ward H/E: Bandra BKC (19.0596, 72.8656)</option>
                </select>
              </div>
              <div class="form-row">
                <input type="number" step="0.0001" [(ngModel)]="newPlace.latitude" placeholder="Latitude" class="form-control" />
                <input type="number" step="0.0001" [(ngModel)]="newPlace.longitude" placeholder="Longitude" class="form-control" />
              </div>
              <div class="form-actions right">
                <button class="btn btn-sm btn-ghost" (click)="showAddLocation.set(false)">Cancel</button>
                <button class="btn btn-sm btn-primary" (click)="saveLocation()">Save Place</button>
              </div>
            </div>
          }

          <div class="places-list">
            @if (savedLocations().length === 0) {
              <div class="empty-list">No monitored places saved yet. Add your home or office above.</div>
            } @else {
              @for (loc of savedLocations(); track loc.id) {
                <div class="place-item">
                  <div class="place-icon">🏢</div>
                  <div class="place-info">
                    <strong>{{ loc.label }}</strong>
                    <span>{{ loc.latitude.toFixed(4) }}, {{ loc.longitude.toFixed(4) }}</span>
                  </div>
                  <button class="btn-delete" (click)="deleteLocation(loc.id!)">✕</button>
                </div>
              }
            }
          </div>
        </div>

        <!-- 3. Emergency Contacts -->
        <div class="glass-card section-card full-span">
          <div class="card-header">
            <div class="header-icon">👥</div>
            <div class="header-text-flex">
              <div>
                <h3>Emergency Contacts</h3>
                <p>Notified if you are inside a critical flood zone during torrential rain</p>
              </div>
              <button class="btn btn-sm btn-primary" (click)="showAddContact.set(true)">
                + Add Contact
              </button>
            </div>
          </div>

          <!-- Add Contact Form -->
          @if (showAddContact()) {
            <div class="inline-form-card">
              <h4>Add Emergency Contact</h4>
              <div class="form-row">
                <input type="text" [(ngModel)]="newContact.contact_name" placeholder="Full Name" class="form-control" />
                <select [(ngModel)]="newContact.relationship" class="form-control">
                  <option value="Parent">Parent</option>
                  <option value="Spouse">Spouse</option>
                  <option value="Sibling">Sibling</option>
                  <option value="Relative">Relative</option>
                  <option value="Friend">Friend</option>
                </select>
                <input type="tel" [(ngModel)]="newContact.mobile_number" placeholder="10-digit Mobile" class="form-control" />
              </div>
              <div class="form-actions right">
                <button class="btn btn-sm btn-ghost" (click)="showAddContact.set(false)">Cancel</button>
                <button class="btn btn-sm btn-primary" (click)="saveContact()">Save Contact</button>
              </div>
            </div>
          }

          <div class="contacts-grid">
            @if (emergencyContacts().length === 0) {
              <div class="empty-list">No emergency contacts registered yet.</div>
            } @else {
              @for (contact of emergencyContacts(); track contact.id) {
                <div class="contact-card">
                  <div class="contact-top">
                    <strong>{{ contact.contact_name }}</strong>
                    <span class="rel-badge">{{ contact.relationship }}</span>
                  </div>
                  <div class="contact-mobile font-mono">+91 {{ contact.mobile_number }}</div>
                  <div class="contact-footer">
                    <span class="sms-status">SMS Alerts: {{ contact.notify_on_critical_alert ? 'ENABLED' : 'DISABLED' }}</span>
                    <button class="btn-delete" (click)="deleteContact(contact.id!)">Delete</button>
                  </div>
                </div>
              }
            }
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .privacy-page {
      padding: 1.5rem;
      max-width: 1100px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .sub-tag {
      font-size: 0.72rem;
      font-weight: 700;
      color: #60a5fa;
      letter-spacing: 0.08em;
    }
    .page-header h1 {
      font-size: 1.7rem;
      margin: 0.2rem 0;
    }
    .page-header p {
      font-size: 0.88rem;
      color: var(--text-muted);
      margin: 0;
    }
    .toast-banner {
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.4);
      color: #34d399;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      font-size: 0.86rem;
    }
    .settings-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }
    @media (max-width: 850px) {
      .settings-grid {
        grid-template-columns: 1fr;
      }
    }
    .section-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.2rem;
    }
    .section-card.full-span {
      grid-column: span 2;
      @media (max-width: 850px) {
        grid-column: span 1;
      }
    }
    .card-header {
      display: flex;
      align-items: flex-start;
      gap: 0.8rem;
    }
    .header-icon {
      font-size: 1.4rem;
    }
    .header-text-flex {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex: 1;
    }
    .card-header h3 {
      font-size: 1.15rem;
      margin: 0 0 0.2rem 0;
    }
    .card-header p {
      font-size: 0.8rem;
      color: var(--text-dim);
      margin: 0;
    }
    .consent-toggle-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(255, 255, 255, 0.03);
      padding: 1rem;
      border-radius: 10px;
      gap: 1rem;
    }
    .toggle-desc strong {
      display: block;
      font-size: 0.9rem;
      margin-bottom: 0.2rem;
    }
    .toggle-desc span {
      font-size: 0.78rem;
      color: var(--text-dim);
    }
    .switch {
      position: relative;
      display: inline-block;
      width: 48px;
      height: 26px;
      flex-shrink: 0;
    }
    .switch input {
      opacity: 0;
      width: 0;
      height: 0;
    }
    .slider {
      position: absolute;
      cursor: pointer;
      inset: 0;
      background-color: rgba(255, 255, 255, 0.15);
      transition: .3s;
      border-radius: 26px;
    }
    .slider:before {
      position: absolute;
      content: "";
      height: 18px;
      width: 18px;
      left: 4px;
      bottom: 4px;
      background-color: white;
      transition: .3s;
      border-radius: 50%;
    }
    input:checked + .slider {
      background-color: #2563eb;
    }
    input:checked + .slider:before {
      transform: translateX(22px);
    }
    .purge-actions {
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      padding-top: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.8rem;
    }
    .section-subtitle {
      font-size: 0.76rem;
      font-weight: 600;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .btn-action-group {
      display: flex;
      flex-wrap: wrap;
      gap: 0.6rem;
    }
    .btn-outline-danger {
      border: 1px solid rgba(239, 68, 68, 0.5);
      color: #f87171;
      padding: 0.5rem 0.8rem;
      border-radius: 6px;
      font-size: 0.82rem;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }
    .btn-outline-danger:hover {
      background: rgba(239, 68, 68, 0.1);
    }
    .btn-danger {
      background: #dc2626;
      color: white;
      padding: 0.5rem 0.8rem;
      border-radius: 6px;
      font-size: 0.82rem;
    }
    .btn-danger:hover {
      background: #b91c1c;
    }
    .inline-form-card {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 10px;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.8rem;
    }
    .inline-form-card h4 {
      font-size: 0.95rem;
      margin: 0;
    }
    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.6rem;
    }
    .form-control {
      background: rgba(11, 17, 26, 0.8);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 0.55rem 0.75rem;
      color: var(--text-main);
      font-size: 0.85rem;
    }
    .form-actions {
      display: flex;
      gap: 0.5rem;
    }
    .form-actions.right {
      justify-content: flex-end;
    }
    .places-list {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }
    .place-item {
      display: flex;
      align-items: center;
      gap: 0.8rem;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.06);
      padding: 0.7rem 0.9rem;
      border-radius: 8px;
    }
    .place-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
    }
    .place-info strong {
      font-size: 0.88rem;
    }
    .place-info span {
      font-size: 0.75rem;
      color: var(--text-dim);
      font-family: 'JetBrains Mono', monospace;
    }
    .btn-delete {
      color: var(--text-dim);
      font-size: 0.8rem;
      padding: 0.3rem 0.5rem;
    }
    .btn-delete:hover {
      color: #ef4444;
    }
    .contacts-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
    }
    .contact-card {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .contact-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .rel-badge {
      font-size: 0.7rem;
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      padding: 0.1rem 0.4rem;
      border-radius: 4px;
    }
    .contact-mobile {
      font-size: 0.9rem;
      color: var(--text-main);
    }
    .contact-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 0.4rem;
      font-size: 0.75rem;
      color: var(--text-dim);
    }
    .sms-status {
      color: #10b981;
    }
    .empty-list {
      font-size: 0.84rem;
      color: var(--text-dim);
      padding: 1rem 0;
      text-align: center;
    }
  `]
})
export class PrivacySettingsComponent implements OnInit {
  statusMessage = signal<string | null>(null);
  isSuccess = signal<boolean>(true);

  savedLocations = signal<SavedLocation[]>([]);
  emergencyContacts = signal<EmergencyContact[]>([]);

  showAddLocation = signal<boolean>(false);
  showAddContact = signal<boolean>(false);

  newPlace = {
    label: '',
    wardPreset: '',
    latitude: 19.0178,
    longitude: 72.8478
  };

  newContact: EmergencyContact = {
    contact_name: '',
    relationship: 'Parent',
    mobile_number: '',
    notify_on_critical_alert: true
  };

  constructor(
    public locationService: CitizenLocationService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.locationService.getSavedLocations().subscribe(locs => this.savedLocations.set(locs));
    this.locationService.getEmergencyContacts().subscribe(contacts => this.emergencyContacts.set(contacts));
  }

  toggleConsent(event: any): void {
    const checked = event.target.checked;
    this.locationService.updateConsent(checked).subscribe({
      next: () => {
        this.notify(checked ? 'Explicit location consent granted.' : 'Location consent revoked.');
      }
    });
  }

  purgeCurrentSession(): void {
    this.locationService.purgeCurrentSession().subscribe({
      next: () => {
        this.notify('Current device location session purged immediately.');
      }
    });
  }

  deleteCompleteHistory(): void {
    if (confirm('Are you sure you want to permanently delete your entire location history?')) {
      this.locationService.deleteLocationHistory().subscribe({
        next: () => {
          this.notify('Complete location history permanently erased.');
        }
      });
    }
  }

  applyWardPreset(): void {
    if (this.newPlace.wardPreset === 'Dadar') {
      this.newPlace.latitude = 19.0178;
      this.newPlace.longitude = 72.8478;
    } else if (this.newPlace.wardPreset === 'Kurla') {
      this.newPlace.latitude = 19.0688;
      this.newPlace.longitude = 72.8797;
    } else if (this.newPlace.wardPreset === 'Andheri') {
      this.newPlace.latitude = 19.1197;
      this.newPlace.longitude = 72.8464;
    } else if (this.newPlace.wardPreset === 'Bandra') {
      this.newPlace.latitude = 19.0596;
      this.newPlace.longitude = 72.8656;
    }
  }

  saveLocation(): void {
    if (!this.newPlace.label) return;
    this.locationService.addSavedLocation({
      label: this.newPlace.label,
      latitude: this.newPlace.latitude,
      longitude: this.newPlace.longitude,
      radius_meters: 500
    }).subscribe({
      next: () => {
        this.showAddLocation.set(false);
        this.newPlace.label = '';
        this.loadData();
        this.notify('Monitored location saved.');
      }
    });
  }

  deleteLocation(id: number): void {
    this.locationService.deleteSavedLocation(id).subscribe({
      next: () => {
        this.loadData();
        this.notify('Location removed.');
      }
    });
  }

  saveContact(): void {
    if (!this.newContact.contact_name || !this.newContact.mobile_number) return;
    this.locationService.addEmergencyContact(this.newContact).subscribe({
      next: () => {
        this.showAddContact.set(false);
        this.newContact = { contact_name: '', relationship: 'Parent', mobile_number: '', notify_on_critical_alert: true };
        this.loadData();
        this.notify('Emergency contact added.');
      }
    });
  }

  deleteContact(id: number): void {
    this.locationService.deleteEmergencyContact(id).subscribe({
      next: () => {
        this.loadData();
        this.notify('Emergency contact removed.');
      }
    });
  }

  private notify(msg: string): void {
    this.statusMessage.set(msg);
    setTimeout(() => this.statusMessage.set(null), 4000);
  }
}
