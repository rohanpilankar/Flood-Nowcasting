import { Observable } from 'rxjs';
import { FloodAlert } from '../../models/alert.model';

export abstract class AlertDataProvider {
  abstract getAlerts(): Observable<FloodAlert[]>;
  abstract acknowledgeAlert(id: string): Observable<FloodAlert>;
}
