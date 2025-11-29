export type AlertType = 'chronic_low_sleep' | 'consecutive_nights' | 'high_stress_pattern' | 'declining_health';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface BurnoutAlert {
  alertId?: number;
  userId: number;
  alertType: AlertType;
  severity: AlertSeverity;
  description?: string;
  isResolved: boolean;
  createdAt?: string;
  resolvedAt?: string;
}
