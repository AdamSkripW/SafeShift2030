export type UserRole = 'nurse' | 'doctor' | 'student';

export interface User {
  UserId?: number;
  Email: string;
  FirstName: string;
  LastName: string;
  Role: UserRole;
  Department: string;
  Hospital: string;
  HospitalId?: number;
  ProfilePictureUrl?: string;
  CreatedAt?: string;
  UpdatedAt?: string;
  IsActive?: boolean;
}

export interface AuthResponse {
  User: User;
  Token: string;
  ExpiresAt: string;
}
