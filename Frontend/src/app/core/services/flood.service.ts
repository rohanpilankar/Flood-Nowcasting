import { Injectable, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { FloodDataProvider } from '../providers/interfaces/flood-data.provider';
import { FloodZone, SystemKPIs, RecentPrediction, PredictionTime } from '../models/flood-risk.model';

@Injectable({
  providedIn: 'root'
})
export class FloodService {
  readonly selectedHorizon = signal<PredictionTime>('NOW');
  readonly selectedZone = signal<FloodZone | null>(null);

  constructor(private floodProvider: FloodDataProvider) {}

  setHorizon(horizon: PredictionTime): void {
    this.selectedHorizon.set(horizon);
  }

  setSelectedZone(zone: FloodZone | null): void {
    this.selectedZone.set(zone);
  }

  getKPIs(): Observable<SystemKPIs> {
    return this.floodProvider.getKPIs();
  }

  getFloodZones(horizon?: PredictionTime): Observable<FloodZone[]> {
    return this.floodProvider.getFloodZones(horizon || this.selectedHorizon());
  }

  getZoneById(gridId: string): Observable<FloodZone | undefined> {
    return this.floodProvider.getZoneById(gridId);
  }

  getRecentPredictions(): Observable<RecentPrediction[]> {
    return this.floodProvider.getRecentPredictions();
  }

  getLocationRisk(locationName: string): Observable<FloodZone | undefined> {
    return this.floodProvider.getLocationRisk(locationName);
  }
}
