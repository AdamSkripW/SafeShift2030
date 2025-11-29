export type AlertType = 'chronic_low_sleep' | 'consecutive_nights' | 'high_stress_pattern' | 'declining_health';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface BurnoutAlert {
  AlertId?: number;
  UserId: number;
  AlertType: AlertType;
  Severity: AlertSeverity;
  Description?: string;
  IsResolved: boolean;
  CreatedAt?: string;
  ResolvedAt?: string;
}
