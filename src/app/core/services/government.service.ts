import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface EmergencyOverview {
  active_alerts_count: number;
  critical_zones_count: number;
  caution_zones_count: number;
  total_citizens_opted_in: number;
  total_notifications_dispatched: number;
  zones_summary: Array<{
    zone_name: string;
    ward: string;
    risk_level: string;
    water_depth_cm: number;
    opted_in_citizens: number;
    notified_citizens: number;
  }>;
  recent_alerts: any[];
}

export interface BroadcastAlertPayload {
  title: string;
  severity: 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  flood_category: string;
  affected_ward: string;
  affected_landmarks: string[];
  message: string;
  safety_instructions: string;
  recommended_safe_routes: string[];
  target_latitude?: number;
  target_longitude?: number;
  radius_meters?: number;
}

@Injectable({
  providedIn: 'root'
})
export class GovernmentService {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getEmergencyOverview(): Observable<EmergencyOverview> {
    return this.http.get<EmergencyOverview>(`${this.baseUrl}/api/v1/government/emergency-overview`);
  }

  broadcastAlert(payload: BroadcastAlertPayload): Observable<any> {
    return this.http.post(`${this.baseUrl}/api/v1/government/broadcast-alert`, payload);
  }

  getActiveAlerts(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/api/v1/government/active-alerts`);
  }

  getVerifiedAuthorities(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/api/v1/government/verified-authorities`);
  }
}
