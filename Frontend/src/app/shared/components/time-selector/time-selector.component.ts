import { Component, EventEmitter, Input, Output, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PredictionTime } from '../../../core/models/flood-risk.model';

@Component({
  selector: 'app-time-selector',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="time-selector-wrapper">
      <div class="time-selector-container">
        <span class="selector-label" *ngIf="showLabel">Nowcast Horizon:</span>
        <div class="pill-group" role="group" aria-label="Prediction Time Horizon">
          @for (opt of options; track opt.value) {
            <button
              type="button"
              class="pill-btn"
              [class.active]="selected === opt.value"
              (click)="select(opt.value)"
              [attr.aria-pressed]="selected === opt.value"
            >
              {{ opt.label }}
            </button>
          }
        </div>

        <!-- Playback Controls -->
        <div class="playback-controls">
          <button
            type="button"
            class="play-btn"
            (click)="togglePlay()"
            [title]="isPlaying ? 'Pause timeline playback' : 'Play timeline progression'"
          >
            @if (isPlaying) {
              <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                <rect x="6" y="4" width="4" height="16"></rect>
                <rect x="14" y="4" width="4" height="16"></rect>
              </svg>
            } @else {
              <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
              </svg>
            }
          </button>
          <button
            type="button"
            class="speed-btn"
            (click)="cycleSpeed()"
            title="Playback speed"
          >
            {{ speedMultiplier }}x
          </button>
        </div>
      </div>

      <!-- Honest Data Badge when looking at future horizons -->
      @if (selected !== 'NOW') {
        <div class="forecast-notice" role="status">
          <svg viewBox="0 0 24 24" fill="currentColor" width="13" height="13">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
          </svg>
          <span>Horizon {{ selected }}: Forecast awaiting radar extrapolation (live Doppler connection pending)</span>
        </div>
      }
    </div>
  `,
  styles: [`
    .time-selector-wrapper {
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }
    .time-selector-container {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .selector-label {
      font-size: 0.75rem;
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .pill-group {
      display: inline-flex;
      background-color: var(--bg-darkest);
      padding: 3px;
      border-radius: var(--radius-full);
      border: 1px solid var(--border-subtle);
    }
    .pill-btn {
      padding: 0.32rem 0.85rem;
      font-size: 0.75rem;
      font-weight: 600;
      border-radius: var(--radius-full);
      color: var(--text-muted);
      letter-spacing: 0.04em;
      transition: all var(--transition-fast);
      background: transparent;
      border: none;
      cursor: pointer;

      &:hover {
        color: var(--text-main);
      }
      &.active {
        background-color: var(--brand-primary);
        color: #ffffff;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
      }
    }
    .playback-controls {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      background-color: var(--bg-darkest);
      padding: 3px;
      border-radius: var(--radius-full);
      border: 1px solid var(--border-subtle);
    }
    .play-btn, .speed-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0.3rem 0.55rem;
      border-radius: var(--radius-full);
      font-size: 0.7rem;
      font-weight: 700;
      transition: all var(--transition-fast);

      &:hover {
        color: #ffffff;
        background-color: rgba(255, 255, 255, 0.1);
      }
    }
    .play-btn {
      color: var(--brand-primary);
    }
    .forecast-notice {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.72rem;
      color: #fbbf24;
      background: rgba(245, 158, 11, 0.12);
      border: 1px solid rgba(245, 158, 11, 0.3);
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      animation: fadeIn 0.2s ease-in;

      svg {
        flex-shrink: 0;
      }
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(-2px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `]
})
export class TimeSelectorComponent implements OnDestroy {
  @Input() selected: PredictionTime = 'NOW';
  @Input() showLabel = true;
  @Input() fullLabels = false;
  @Output() horizonChange = new EventEmitter<PredictionTime>();

  isPlaying = false;
  speedMultiplier = 1;
  private playbackTimer: any = null;

  private horizonOrder: PredictionTime[] = ['NOW', '+30M', '+1H', '+2H', '+3H'];

  get options(): { value: PredictionTime; label: string }[] {
    if (this.fullLabels) {
      return [
        { value: 'NOW', label: 'NOW' },
        { value: '+30M', label: '+30 MIN' },
        { value: '+1H', label: '+1 HOUR' },
        { value: '+2H', label: '+2 HOURS' },
        { value: '+3H', label: '+3 HOURS' }
      ];
    }
    return [
      { value: 'NOW', label: 'NOW' },
      { value: '+30M', label: '+30M' },
      { value: '+1H', label: '+1H' },
      { value: '+2H', label: '+2H' },
      { value: '+3H', label: '+3H' }
    ];
  }

  select(value: PredictionTime): void {
    if (this.selected !== value) {
      this.selected = value;
      this.horizonChange.emit(value);
    }
  }

  togglePlay(): void {
    if (this.isPlaying) {
      this.stopPlayback();
    } else {
      this.startPlayback();
    }
  }

  cycleSpeed(): void {
    const speeds = [1, 2, 4];
    const currIdx = speeds.indexOf(this.speedMultiplier);
    this.speedMultiplier = speeds[(currIdx + 1) % speeds.length];
    if (this.isPlaying) {
      this.stopPlayback();
      this.startPlayback();
    }
  }

  private startPlayback(): void {
    this.isPlaying = true;
    const intervalMs = Math.max(800, 2400 / this.speedMultiplier);
    this.playbackTimer = setInterval(() => {
      const idx = this.horizonOrder.indexOf(this.selected);
      const nextIdx = (idx + 1) % this.horizonOrder.length;
      this.select(this.horizonOrder[nextIdx]);
    }, intervalMs);
  }

  private stopPlayback(): void {
    this.isPlaying = false;
    if (this.playbackTimer) {
      clearInterval(this.playbackTimer);
      this.playbackTimer = null;
    }
  }

  ngOnDestroy(): void {
    this.stopPlayback();
  }
}
