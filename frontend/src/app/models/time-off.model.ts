export type TimeOffReason = 'rest_recovery' | 'burnout_risk' | 'personal' | 'admin_assigned';
export type TimeOffStatus = 'pending' | 'approved' | 'rejected' | 'taken';

export interface TimeOffRequest {
  timeOffId?: number;
  userId: number;
  startDate: string;
  endDate: string;
  reason: TimeOffReason;
  assignedBy?: number;
  status: TimeOffStatus;
  notes?: string;
  createdAt?: string;
  updatedAt?: string;
}
