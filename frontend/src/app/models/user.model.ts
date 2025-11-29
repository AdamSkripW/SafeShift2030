export type UserRole = 'nurse' | 'doctor' | 'student';

export interface User {
  userId?: number;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  department: string;
  hospital: string;
  hospitalId?: number;
  profilePictureUrl?: string;
  createdAt?: string;
  updatedAt?: string;
  isActive?: boolean;
}

export interface AuthResponse {
  user: User;
  token: string;
  expiresAt: string;
}
