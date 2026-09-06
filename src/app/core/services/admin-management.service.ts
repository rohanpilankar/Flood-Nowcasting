import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface AdminUser {
  id: number;
  full_name: string;
  email: string;
  mobile: string;
  role: string;
  status: string;
  email_verified: boolean;
  mobile_verified: boolean;
  created_at: string;
}

export interface PendingAuthority {
  profile_id: number;
  user_id: number;
  full_name: string;
  email: string;
  department: string;
  designation: string;
  jurisdiction_ward: string;
  employee_id: string;
  official_email: string;
  status: string;
  created_at: string;
}

export interface PendingFloodReport {
  id: number;
  report_code: string;
  user_name: string;
  location_name: string;
  latitude: number;
  longitude: number;
  water_depth_level: string;
  water_depth_cm?: number;
  traffic_disruption: string;
  rainfall_intensity: string;
  description?: string;
  status: string;
  created_at: string;
}

export interface GroundTruthMetrics {
  total_reports: number;
  validated_reports: number;
  rejected_reports: number;
  unverified_reports: number;
  model_concordance_rate: number;
  confusion_matrix: {
    true_positive: number;
    false_positive: number;
    true_negative: number;
    false_negative: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class AdminManagementService {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getUsers(): Observable<AdminUser[]> {
    return this.http.get<AdminUser[]>(`${this.baseUrl}/api/v1/admin-users/users`);
  }

  updateUserRoleStatus(userId: number, payload: { role?: string; status?: string }): Observable<any> {
    return this.http.patch(`${this.baseUrl}/api/v1/admin-users/users/${userId}`, payload);
  }

  getPendingAuthorities(): Observable<PendingAuthority[]> {
    return this.http.get<PendingAuthority[]>(`${this.baseUrl}/api/v1/admin-users/authorities/pending`);
  }

  reviewAuthority(profileId: number, approved: boolean, notes?: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/api/v1/admin-users/authorities/${profileId}/verify`, {
      approved,
      notes
    });
  }

  getFloodReports(): Observable<PendingFloodReport[]> {
    return this.http.get<PendingFloodReport[]>(`${this.baseUrl}/api/v1/admin-users/feedback`);
  }

  reviewFloodReport(reportId: number, approved: boolean, notes?: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/api/v1/admin-users/feedback/${reportId}/review`, {
      status: approved ? 'VALIDATED' : 'REJECTED',
      review_notes: notes
    });
  }

  getGroundTruthEvaluation(): Observable<GroundTruthMetrics> {
    return this.http.get<GroundTruthMetrics>(`${this.baseUrl}/api/v1/admin-users/ground-truth-evaluation`);
  }
}
