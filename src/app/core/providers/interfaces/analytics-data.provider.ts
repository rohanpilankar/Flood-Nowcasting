import { Observable } from 'rxjs';
import { AnalyticsSummary } from '../../models/analytics.model';

export abstract class AnalyticsDataProvider {
  abstract getAnalyticsSummary(): Observable<AnalyticsSummary>;
}
