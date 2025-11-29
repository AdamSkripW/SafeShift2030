import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import {map, tap} from 'rxjs/operators';
import { User, AuthResponse } from '../models/user.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = `${environment.apiUrl}/auth`;
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor(private http: HttpClient) {
    this.loadUserFromStorage();
  }

  /**
   * Login user
   */
  login(email: string, password: string): Observable<AuthResponse> {
    return this.http.post<any>(`${this.apiUrl}/login`, { email: email, password: password })
      .pipe(
        map(response => {
          // Backend returns flat structure with user fields and token
          if (response.token && response.userId) {
            // Construct User object from flat response
            const user: User = {
              UserId: response.userId,
              Email: response.email,
              FirstName: response.firstName,
              LastName: response.lastName,
              Role: response.role,
              Department: response.department,
              Hospital: response.hospital,
              IsActive: response.isActive
            };

            // Calculate expiration date
            const expiresAt = new Date();
            expiresAt.setSeconds(expiresAt.getSeconds() + (response.expiresIn || 86400));

            const authResponse: AuthResponse = {
              User: user,
              Token: response.token,
              ExpiresAt: expiresAt.toISOString()
            };
            
            this.handleAuthResponse(authResponse);
            return authResponse;
          }
          throw new Error(response.error || 'Login failed');
        })
      );
  }

  /**
   * Register new user (using /api/users endpoint since /auth/register doesn't exist on cloud)
   */
  register(userData: {
    Email: string;
    Password: string;
    FirstName: string;
    LastName: string;
    Role: 'nurse' | 'doctor' | 'student';
    Department: string;
    Hospital: string;
    HospitalId: number;
  }): Observable<AuthResponse> {
    // Use the /api/users endpoint (cloud backend doesn't have /auth/register yet)
    return this.http.post<any>(`${environment.apiUrl}/users`, userData)
      .pipe(
        map(response => {
          // Transform the response to match AuthResponse format
          if (response.success && response.data) {
            // Create a mock token for now (until cloud backend has auth endpoints)
            const authResponse: AuthResponse = {
              User: response.data,
              Token: 'temp-token-' + Date.now(), // Temporary token
              ExpiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
            };
            this.handleAuthResponse(authResponse);
            return authResponse;
          }
          throw new Error(response.error || 'Registration failed');
        })
      );
  }

  /**
   * Logout user
   */
  logout(): void {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    this.currentUserSubject.next(null);
  }

  /**
   * Get current user
   */
  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('authToken');
    return !!token;
  }

  /**
   * Get auth token
   */
  getToken(): string | null {
    return localStorage.getItem('authToken');
  }

  /**
   * Handle authentication response
   */
  private handleAuthResponse(response: AuthResponse): void {
    localStorage.setItem('authToken', response.Token);
    localStorage.setItem('currentUser', JSON.stringify(response.User));
    this.currentUserSubject.next(response.User);
  }

  /**
   * Load user from localStorage on init
   */
  private loadUserFromStorage(): void {
    const userJson = localStorage.getItem('currentUser');
    if (userJson) {
      try {
        const user = JSON.parse(userJson) as User;
        this.currentUserSubject.next(user);
      } catch (error) {
        console.error('Error loading user from storage:', error);
      }
    }
  }
}
