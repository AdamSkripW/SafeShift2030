export type ShiftType = 'day' | 'night' | 'rest';
export type Zone = 'green' | 'yellow' | 'red';

export interface AgentInsight {
  category: 'crisis' | 'burnout' | 'patient_safety' | 'wellness' | 'trend';
  message: string;
  supporting_data: string;
  priority: number;
}

export interface Recommendation {
  action: string;
  timing: 'immediate' | 'today' | 'this_week' | 'ongoing';
  expected_benefit: string;
  source_agents: string[];
}

export interface AgentInsights {
  summary: string;
  urgency_level: 'routine' | 'attention_needed' | 'urgent' | 'critical';
  primary_insights: AgentInsight[];
  recommendations: Recommendation[];
  nurse_message?: string;
  supervisor_message?: string;
  connections?: Array<{
    insight: string;
    agents_involved: string[];
    implication: string;
  }>;
  confidence?: number;
}

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
  IsRecommended?: boolean; // AI-generated recommended shift
  
  // Computed by backend
  SafeShiftIndex?: number; // 0-100
  Zone?: Zone;
  AiExplanation?: string;
  AiTips?: string;
  AgentInsights?: AgentInsights;
  
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
