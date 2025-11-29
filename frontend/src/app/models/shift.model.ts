export type ShiftType = 'day' | 'night';
export type Zone = 'green' | 'yellow' | 'red';

export interface Shift {
  ShiftId?: number;
  UserId?: number;
  ShiftDate: string; // ISO date string
  HoursSleptBefore: number; // 0-24
  ShiftType: ShiftType;
  ShiftLengthHours: number; // 1-24
  PatientsCount: number; // >= 0
  StressLevel: number; // 1-10
  ShiftNote?: string;
  
  // Computed by backend
  SafeShiftIndex?: number; // 0-100
  Zone?: Zone;
  AiExplanation?: string;
  AiTips?: string;
  
  CreatedAt?: string;
  UpdatedAt?: string;
}

export interface ShiftFormData {
  ShiftDate: string;
  HoursSleptBefore: number;
  ShiftType: ShiftType;
  ShiftLengthHours: number;
  PatientsCount: number;
  StressLevel: number;
  ShiftNote?: string;
}
