import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, of, interval, throwError } from 'rxjs';
import {map, tap, catchError, switchMap, filter} from 'rxjs/operators';
import { User, AuthResponse } from '../models/user.model';
import { environment } from '../../environments/environment';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = `${environment.apiUrl}/auth`;
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();
  private sessionCheckInterval: any;

  constructor(private http: HttpClient, private router: Router) {
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
   * Logout user - clears local session and calls backend to delete session record
   */
  logout(): Observable<any> {
    const token = localStorage.getItem('authToken');
    
    // Stop session validation
    this.stopSessionValidation();
    
    // Clear local storage first
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    this.currentUserSubject.next(null);
    
    // Call backend to delete session from database
    if (token) {
      return this.http.post(`${this.apiUrl}/logout`, {}, {
        headers: new HttpHeaders({
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        })
      }).pipe(
        tap(() => console.log('Session deleted from server')),
        catchError(error => {
          console.error('Error calling logout endpoint:', error);
          // Don't fail the logout even if backend call fails
          return of({ success: true });
        })
      );
    } else {
      // No token, just return success
      return of({ success: true });
    }
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
    
    // Start session validation checks
    this.startSessionValidation();
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
        
        // Start session validation if user is loaded
        this.startSessionValidation();
      } catch (error) {
        console.error('Error loading user from storage:', error);
      }
    }
  }

  /**
   * Validate current session with backend
   */
  validateSession(): Observable<any> {
    return this.http.get(`${this.apiUrl}/sessions/validate`).pipe(
      catchError(error => {
        // Session is invalid - logout user
        if (error.status === 401) {
          console.warn('Session invalidated by server - logging out');
          this.forceLogout();
        }
        return throwError(() => error);
      })
    );
  }

  /**
   * Start periodic session validation (every 30 seconds)
   */
  private startSessionValidation(): void {
    // Clear any existing interval
    this.stopSessionValidation();
    
    // Check session every 30 seconds
    this.sessionCheckInterval = setInterval(() => {
      if (this.isAuthenticated()) {
        this.validateSession().subscribe({
          next: (response) => {
            if (!response.valid) {
              console.warn('Session no longer valid');
              this.forceLogout();
            }
          },
          error: (error) => {
            // 401 errors are already handled in validateSession
            if (error.status !== 401) {
              console.error('Session validation error:', error);
            }
          }
        });
      } else {
        this.stopSessionValidation();
      }
    }, 30000); // Check every 30 seconds
  }

  /**
   * Stop session validation checks
   */
  private stopSessionValidation(): void {
    if (this.sessionCheckInterval) {
      clearInterval(this.sessionCheckInterval);
      this.sessionCheckInterval = null;
    }
  }

  /**
   * Force logout (when session is invalidated externally)
   */
  private forceLogout(): void {
    console.warn('🚪 Session invalidated - forcing logout');
    
    // Stop session checks
    this.stopSessionValidation();
    
    // Clear local storage
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    this.currentUserSubject.next(null);
    
    // Navigate to start page
    this.router.navigate(['/start']);
    
    // Show alert to user
    alert('Your session has been invalidated. This may be because you logged in from another device or browser.');
  }
}
