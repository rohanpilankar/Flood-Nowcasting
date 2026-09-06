import { Injectable, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { AlertDataProvider } from '../providers/interfaces/alert-data.provider';
import { FloodAlert } from '../models/alert.model';

@Injectable({
  providedIn: 'root'
})
export class AlertService {
  readonly activeAlertsCount = signal<number>(5);
  readonly highPriorityCount = signal<number>(2);

  constructor(private alertProvider: AlertDataProvider) {}

  getAlerts(): Observable<FloodAlert[]> {
    return this.alertProvider.getAlerts().pipe(
      tap(alerts => {
        const active = alerts.filter(a => !a.acknowledged);
        this.activeAlertsCount.set(active.length);
        this.highPriorityCount.set(active.filter(a => a.severity === 'HIGH').length);
      })
    );
  }

  acknowledgeAlert(id: string): Observable<FloodAlert> {
    return this.alertProvider.acknowledgeAlert(id).pipe(
      tap(() => {
        // Re-fetch or adjust counts reactively
        this.getAlerts().subscribe();
      })
    );
  }
}
