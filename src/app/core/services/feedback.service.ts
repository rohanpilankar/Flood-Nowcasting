import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface CitizenFloodReportPayload {
  latitude: number;
  longitude: number;
  location_name: string;
  water_depth_level: 'ANKLE_DEEP' | 'KNEE_DEEP' | 'WAIST_DEEP' | 'SUBMERGED';
  water_depth_cm?: number;
  traffic_disruption: 'NORMAL' | 'SLOW' | 'HALTED' | 'DIVERSIFIED';
  rainfall_intensity: 'NO_RAIN' | 'LIGHT' | 'MODERATE' | 'HEAVY' | 'TORRENTIAL';
  description?: string;
  image_url?: string;
}

export interface CitizenFloodReportResponse {
  id: number;
  report_code: string;
  location_name: string;
  water_depth_level: string;
  water_depth_cm?: number;
  status: 'UNVERIFIED' | 'VALIDATED' | 'REJECTED';
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class FeedbackService {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  submitReport(payload: CitizenFloodReportPayload): Observable<CitizenFloodReportResponse> {
    return this.http.post<CitizenFloodReportResponse>(`${this.baseUrl}/api/v1/feedback/submit`, payload);
  }

  getMyReports(): Observable<CitizenFloodReportResponse[]> {
    return this.http.get<CitizenFloodReportResponse[]>(`${this.baseUrl}/api/v1/feedback/my-reports`);
  }
}
