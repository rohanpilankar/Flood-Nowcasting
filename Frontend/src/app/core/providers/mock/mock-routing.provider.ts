import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';
import { RoutingDataProvider } from '../interfaces/routing-data.provider';
import { RoutePlanResult, PresetRoute } from '../../models/route.model';
import { SEED_PRESET_ROUTES, SEED_ROUTE_PLANS } from '../../mock/seed-data';

@Injectable({
  providedIn: 'root'
})
export class MockRoutingDataProvider extends RoutingDataProvider {
  getPresetRoutes(): Observable<PresetRoute[]> {
    return of([...SEED_PRESET_ROUTES]).pipe(delay(80));
  }

  calculateSafeRoute(source: string, destination: string): Observable<RoutePlanResult> {
    const key = `${source.trim()}_${destination.trim()}`;
    const reverseKey = `${destination.trim()}_${source.trim()}`;

    if (SEED_ROUTE_PLANS[key]) {
      return of(SEED_ROUTE_PLANS[key]).pipe(delay(300));
    }

    if (SEED_ROUTE_PLANS[reverseKey]) {
      return of(SEED_ROUTE_PLANS[reverseKey]).pipe(delay(300));
    }

    // Default fallback to Katraj -> Shivajinagar plan with updated labels
    const base = SEED_ROUTE_PLANS['Katraj_Shivajinagar'];
    return of({
      ...base,
      source,
      destination
    }).pipe(delay(300));
  }
}
