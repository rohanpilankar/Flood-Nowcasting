import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';
import { AnalyticsDataProvider } from '../interfaces/analytics-data.provider';
import { AnalyticsSummary } from '../../models/analytics.model';
import { SEED_ANALYTICS } from '../../mock/seed-data';

@Injectable({
  providedIn: 'root'
})
export class MockAnalyticsDataProvider extends AnalyticsDataProvider {
  getAnalyticsSummary(): Observable<AnalyticsSummary> {
    return of({ ...SEED_ANALYTICS }).pipe(delay(220));
  }
}
