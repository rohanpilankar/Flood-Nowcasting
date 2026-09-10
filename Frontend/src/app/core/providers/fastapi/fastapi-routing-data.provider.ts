import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { RoutingDataProvider } from '../interfaces/routing-data.provider';
import { RoutePlanResult, PresetRoute } from '../../models/route.model';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FastApiRoutingDataProvider extends RoutingDataProvider {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {
    super();
  }

  getPresetRoutes(): Observable<PresetRoute[]> {
    return this.http.get<PresetRoute[]>(`${this.baseUrl}/api/v1/safe-route/presets`);
  }

  calculateSafeRoute(source: string, destination: string, vehicle_type: string = 'car'): Observable<RoutePlanResult> {
    return this.http.post<RoutePlanResult>(`${this.baseUrl}/api/v1/safe-route`, {
      source,
      destination,
      vehicle_type
    });
  }
}
