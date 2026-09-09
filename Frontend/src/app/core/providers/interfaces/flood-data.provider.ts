import { Observable } from 'rxjs';
import { FloodZone, SystemKPIs, RecentPrediction, PredictionTime } from '../../models/flood-risk.model';

export abstract class FloodDataProvider {
  abstract getKPIs(): Observable<SystemKPIs>;
  abstract getFloodZones(predictionTime?: PredictionTime): Observable<FloodZone[]>;
  abstract getZoneById(gridId: string): Observable<FloodZone | undefined>;
  abstract getRecentPredictions(): Observable<RecentPrediction[]>;
  abstract getLocationRisk(locationName: string): Observable<FloodZone | undefined>;
}
