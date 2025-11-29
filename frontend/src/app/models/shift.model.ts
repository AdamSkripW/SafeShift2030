export type ShiftType = 'day' | 'night';
export type Zone = 'green' | 'yellow' | 'red';

export interface Shift {
  shiftId?: number;
  userId?: number;
  shiftDate: string; // ISO date string
  hoursSleptBefore: number; // 0-24
  shiftType: ShiftType;
  shiftLengthHours: number; // 1-24
  patientsCount: number; // >= 0
  stressLevel: number; // 1-10
  shiftNote?: string;
  
  // Computed by backend
  safeShiftIndex?: number; // 0-100
  zone?: Zone;
  aiExplanation?: string;
  aiTips?: string;
  
  createdAt?: string;
  updatedAt?: string;
}

export interface ShiftFormData {
  shiftDate: string;
  hoursSleptBefore: number;
  shiftType: ShiftType;
  shiftLengthHours: number;
  patientsCount: number;
  stressLevel: number;
  shiftNote?: string;
}
