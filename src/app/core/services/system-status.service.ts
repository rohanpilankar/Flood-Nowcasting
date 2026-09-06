import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { SystemStatusDataProvider } from '../providers/interfaces/system-status-data.provider';
import { AdminSystemOverview } from '../models/system-status.model';

@Injectable({
  providedIn: 'root'
})
export class SystemStatusService {
  constructor(private statusProvider: SystemStatusDataProvider) {}

  getSystemOverview(): Observable<AdminSystemOverview> {
    return this.statusProvider.getSystemOverview();
  }
}
