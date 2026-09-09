import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AnalyticsDataProvider } from '../interfaces/analytics-data.provider';
import { AnalyticsSummary } from '../../models/analytics.model';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FastApiAnalyticsDataProvider extends AnalyticsDataProvider {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {
    super();
  }

  getAnalyticsSummary(): Observable<AnalyticsSummary> {
    return this.http.get<AnalyticsSummary>(`${this.baseUrl}/api/v1/analytics/summary`);
  }
}
