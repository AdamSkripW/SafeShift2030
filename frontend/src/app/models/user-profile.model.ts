export interface UserProfile {
  fullName: string;
  role: 'Nurse' | 'Doctor' | 'Medical Student';
  department: string;
}
