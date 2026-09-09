import { Injectable } from '@angular/core';
import { Observable, of, BehaviorSubject } from 'rxjs';
import { delay, map } from 'rxjs/operators';
import { AlertDataProvider } from '../interfaces/alert-data.provider';
import { FloodAlert } from '../../models/alert.model';
import { SEED_ALERTS } from '../../mock/seed-data';

@Injectable({
  providedIn: 'root'
})
export class MockAlertDataProvider extends AlertDataProvider {
  private alertsSubject = new BehaviorSubject<FloodAlert[]>([...SEED_ALERTS]);

  getAlerts(): Observable<FloodAlert[]> {
    return this.alertsSubject.asObservable().pipe(delay(100));
  }

  acknowledgeAlert(id: string): Observable<FloodAlert> {
    const current = this.alertsSubject.getValue();
    const index = current.findIndex(a => a.id === id);
    if (index !== -1) {
      const updated = { ...current[index], acknowledged: !current[index].acknowledged };
      const updatedList = [...current];
      updatedList[index] = updated;
      this.alertsSubject.next(updatedList);
      return of(updated).pipe(delay(80));
    }
    return of(current[0]);
  }
}
