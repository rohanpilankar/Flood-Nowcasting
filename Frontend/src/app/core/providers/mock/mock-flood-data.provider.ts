import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { delay, map } from 'rxjs/operators';
import { FloodDataProvider } from '../interfaces/flood-data.provider';
import { FloodZone, SystemKPIs, RecentPrediction, PredictionTime } from '../../models/flood-risk.model';
import { SEED_FLOOD_ZONES, SEED_SYSTEM_KPIS, SEED_RECENT_PREDICTIONS } from '../../mock/seed-data';

@Injectable({
  providedIn: 'root'
})
export class MockFloodDataProvider extends FloodDataProvider {
  private floodZones: FloodZone[] = [...SEED_FLOOD_ZONES];

  getKPIs(): Observable<SystemKPIs> {
    return of({ ...SEED_SYSTEM_KPIS }).pipe(delay(120));
  }

  getFloodZones(predictionTime: PredictionTime = 'NOW'): Observable<FloodZone[]> {
    // Generate simulated dynamic changes across prediction horizons
    return of(this.floodZones).pipe(
      delay(180),
      map(zones => zones.map(zone => {
        let modifier = 1.0;
        let timeLabel: PredictionTime = predictionTime;

        switch (predictionTime) {
          case 'NOW':
            modifier = 1.0;
            break;
          case '+30M':
            modifier = 1.15; // Rain is accumulating
            break;
          case '+1H':
            modifier = 1.28; // Peak ponding
            break;
          case '+2H':
            modifier = 0.95; // Drainage catching up
            break;
          case '+3H':
            modifier = 0.70; // Receding
            break;
        }

        const score = Math.min(99, Math.max(10, Math.round(zone.riskScore * (zone.riskLevel === 'HIGH' ? modifier : (modifier > 1 ? modifier * 0.9 : modifier)))));
        const rain = Math.round(zone.rainfall * modifier * 10) / 10;
        const depth = Math.round(zone.waterDepth * modifier * 100) / 100;

        let riskLevel: FloodZone['riskLevel'] = 'LOW';
        if (score >= 80) riskLevel = 'HIGH';
        else if (score >= 50) riskLevel = 'MEDIUM';
        else if (score >= 20) riskLevel = 'LOW';
        else riskLevel = 'NONE';

        return {
          ...zone,
          riskScore: score,
          riskLevel,
          rainfall: rain,
          waterDepth: depth,
          predictionTime: timeLabel
        };
      }))
    );
  }

  getZoneById(gridId: string): Observable<FloodZone | undefined> {
    const found = this.floodZones.find(z => z.gridId.toLowerCase() === gridId.toLowerCase() || z.name.toLowerCase().includes(gridId.toLowerCase()));
    return of(found ? { ...found } : undefined).pipe(delay(100));
  }

  getRecentPredictions(): Observable<RecentPrediction[]> {
    return of([...SEED_RECENT_PREDICTIONS]).pipe(delay(150));
  }

  getLocationRisk(locationName: string): Observable<FloodZone | undefined> {
    const term = locationName.trim().toLowerCase();
    const match = this.floodZones.find(z => 
      z.name.toLowerCase().includes(term) || 
      term.includes(z.name.toLowerCase().split(' ')[0])
    );

    if (match) {
      return of({ ...match }).pipe(delay(200));
    }

    // Return primary hotspot as safe fallback for demonstration
    const fallback = this.floodZones[0];
    return of({ ...fallback, name: locationName.toUpperCase() + ' (Mumbai Sector Evaluation)' }).pipe(delay(200));
  }
}
