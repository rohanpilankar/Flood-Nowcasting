import { Observable } from 'rxjs';
import { RoutePlanResult, PresetRoute } from '../../models/route.model';

export abstract class RoutingDataProvider {
  abstract getPresetRoutes(): Observable<PresetRoute[]>;
  abstract calculateSafeRoute(source: string, destination: string): Observable<RoutePlanResult>;
}
