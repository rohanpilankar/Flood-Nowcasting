import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { SystemStatusDataProvider } from '../interfaces/system-status-data.provider';
import { AdminSystemOverview } from '../../models/system-status.model';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FastApiSystemStatusDataProvider extends SystemStatusDataProvider {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {
    super();
  }

  getSystemOverview(): Observable<AdminSystemOverview> {
    return this.http.get<AdminSystemOverview>(`${this.baseUrl}/api/v1/health/system-overview`);
  }
}
