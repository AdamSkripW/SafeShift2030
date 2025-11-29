export type TimeOffReason = 'rest_recovery' | 'burnout_risk' | 'personal' | 'admin_assigned';
export type TimeOffStatus = 'pending' | 'approved' | 'rejected' | 'taken';

export interface TimeOffRequest {
  TimeOffId?: number;
  UserId: number;
  StartDate: string;
  EndDate: string;
  Reason: TimeOffReason;
  AssignedBy?: number;
  Status: TimeOffStatus;
  Notes?: string;
  CreatedAt?: string;
  UpdatedAt?: string;
}
