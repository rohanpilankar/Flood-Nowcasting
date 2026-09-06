import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';
import { SystemStatusDataProvider } from '../interfaces/system-status-data.provider';
import { AdminSystemOverview } from '../../models/system-status.model';
import { SEED_ADMIN_SYSTEM } from '../../mock/seed-data';

@Injectable({
  providedIn: 'root'
})
export class MockSystemStatusDataProvider extends SystemStatusDataProvider {
  getSystemOverview(): Observable<AdminSystemOverview> {
    return of({ ...SEED_ADMIN_SYSTEM }).pipe(delay(160));
  }
}
