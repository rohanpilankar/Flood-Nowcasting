import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { FloodDataProvider } from '../interfaces/flood-data.provider';
import { FloodZone, SystemKPIs, RecentPrediction, PredictionTime } from '../../models/flood-risk.model';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FastApiFloodDataProvider extends FloodDataProvider {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {
    super();
  }

  getKPIs(): Observable<SystemKPIs> {
    return this.http.get<SystemKPIs>(`${this.baseUrl}/api/v1/current-risk/kpis`);
  }

  getFloodZones(predictionTime: PredictionTime = 'NOW'): Observable<FloodZone[]> {
    return this.http.get<FloodZone[]>(`${this.baseUrl}/api/v1/forecast-risk`, {
      params: { horizon: predictionTime }
    });
  }

  getZoneById(gridId: string): Observable<FloodZone | undefined> {
    return this.http.get<FloodZone>(`${this.baseUrl}/api/v1/map-data/zones/${gridId}`);
  }

  getRecentPredictions(): Observable<RecentPrediction[]> {
    return this.http.get<RecentPrediction[]>(`${this.baseUrl}/api/v1/forecast-risk/recent`);
  }

  getLocationRisk(locationName: string): Observable<FloodZone | undefined> {
    return this.http.get<FloodZone>(`${this.baseUrl}/api/v1/location-risk`, {
      params: { location: locationName }
    });
  }
}
