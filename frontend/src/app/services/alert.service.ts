import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface BurnoutAlert {
  AlertId: number;
  UserId: number;
  ShiftId?: number;
  AlertType: string;
  Severity: string;
  Description: string;
  AlertMessage: string;
  IsResolved: boolean;
  ResolvedAt: string | null;
  CreatedAt: string;
}

export interface AlertSummary {
  total_active: number;
  by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  by_type: Record<string, number>;
  has_critical: boolean;
}

export interface AlertsResponse {
  success: boolean;
  alerts: BurnoutAlert[];
  summary: AlertSummary;
}

@Injectable({
  providedIn: 'root'
})
export class AlertService {
  private apiUrl = `${environment.apiUrl}/alerts`;
  private alertsSubject = new BehaviorSubject<BurnoutAlert[]>([]);
  private summarySubject = new BehaviorSubject<AlertSummary | null>(null);
  
  public alerts$ = this.alertsSubject.asObservable();
  public summary$ = this.summarySubject.asObservable();

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('token');
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    });
  }

  getAlerts(userId: number): Observable<AlertsResponse> {
    return this.http.get<AlertsResponse>(`${this.apiUrl}?user_id=${userId}`, {
      headers: this.getHeaders()
    }).pipe(
      tap(response => {
        if (response.success) {
          this.alertsSubject.next(response.alerts);
          this.summarySubject.next(response.summary);
        }
      })
    );
  }

  resolveAlert(alertId: number, action?: string, note?: string): Observable<any> {
    const body = {
      action: action || 'acknowledged',
      note: note || ''
    };
    
    return this.http.post(`${this.apiUrl}/${alertId}/resolve`, body, {
      headers: this.getHeaders()
    }).pipe(
      tap(() => {
        // Update local state by removing the resolved alert
        const currentAlerts = this.alertsSubject.value.filter(a => a.AlertId !== alertId);
        this.alertsSubject.next(currentAlerts);
        
        // Update summary
        const currentSummary = this.summarySubject.value;
        if (currentSummary) {
          currentSummary.total_active--;
          this.summarySubject.next(currentSummary);
        }
      })
    );
  }

  deleteAlert(alertId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${alertId}`, {
      headers: this.getHeaders()
    }).pipe(
      tap(() => {
        // Update local state by removing the deleted alert
        const currentAlerts = this.alertsSubject.value.filter(a => a.AlertId !== alertId);
        this.alertsSubject.next(currentAlerts);
      })
    );
  }

  refreshAlerts(userId: number): void {
    this.getAlerts(userId).subscribe();
  }

  getSeverityClass(severity: string): string {
    const severityMap: Record<string, string> = {
      'critical': 'severity-critical',
      'high': 'severity-high',
      'medium': 'severity-medium',
      'low': 'severity-low'
    };
    return severityMap[severity.toLowerCase()] || 'severity-low';
  }

  getAlertTypeLabel(alertType: string): string {
    const labelMap: Record<string, string> = {
      'consecutive_nights': 'Consecutive Night Shifts',
      'chronic_low_sleep': 'Chronic Low Sleep',
      'high_stress_pattern': 'High Stress Pattern',
      'declining_health': 'Declining Health Trend',
      'comprehensive_analysis': 'Comprehensive Analysis Alert',
      'crisis_detected': 'Crisis Detected',
      'patient_safety_risk': 'Patient Safety Risk',
      'recovery_needed': 'Recovery Period Needed',
      'rising_stress': 'Rising Stress Trend',
      'frequent_high_risk': 'Frequent High-Risk Shifts',
      'frequent_red_zone': 'Frequent Red Zone',
      'extreme_single_shift': 'Extreme Single Shift'
    };
    return labelMap[alertType] || alertType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  getAlertIcon(alertType: string): string {
    const iconMap: Record<string, string> = {
      'consecutive_nights': '🌙',
      'chronic_low_sleep': '😴',
      'high_stress_pattern': '⚡',
      'declining_health': '📉',
      'comprehensive_analysis': '🔍',
      'crisis_detected': '🚨',
      'patient_safety_risk': '⚠️',
      'recovery_needed': '🔋',
      'rising_stress': '📈',
      'frequent_high_risk': '⚠️',
      'frequent_red_zone': '🔴',
      'extreme_single_shift': '💥'
    };
    return iconMap[alertType] || '🔔';
  }
}
