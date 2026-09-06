import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { AnalyticsDataProvider } from '../providers/interfaces/analytics-data.provider';
import { AnalyticsSummary } from '../models/analytics.model';

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  constructor(private analyticsProvider: AnalyticsDataProvider) {}

  getAnalyticsSummary(): Observable<AnalyticsSummary> {
    return this.analyticsProvider.getAnalyticsSummary();
  }
}
