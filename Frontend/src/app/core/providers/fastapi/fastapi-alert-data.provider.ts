import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AlertDataProvider } from '../interfaces/alert-data.provider';
import { FloodAlert } from '../../models/alert.model';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FastApiAlertDataProvider extends AlertDataProvider {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {
    super();
  }

  getAlerts(): Observable<FloodAlert[]> {
    return this.http.get<FloodAlert[]>(`${this.baseUrl}/api/v1/alerts`);
  }

  acknowledgeAlert(id: string): Observable<FloodAlert> {
    return this.http.patch<FloodAlert>(`${this.baseUrl}/api/v1/alerts/${id}/acknowledge`, {});
  }
}
