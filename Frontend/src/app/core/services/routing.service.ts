import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { RoutingDataProvider } from '../providers/interfaces/routing-data.provider';
import { RoutePlanResult, PresetRoute } from '../models/route.model';

@Injectable({
  providedIn: 'root'
})
export class RoutingService {
  constructor(private routingProvider: RoutingDataProvider) {}

  getPresetRoutes(): Observable<PresetRoute[]> {
    return this.routingProvider.getPresetRoutes();
  }

  calculateSafeRoute(source: string, destination: string, vehicle_type: string = 'car'): Observable<RoutePlanResult> {
    return this.routingProvider.calculateSafeRoute(source, destination, vehicle_type);
  }
}
