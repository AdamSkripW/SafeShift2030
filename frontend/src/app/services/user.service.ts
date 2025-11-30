import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { User } from '../models/user.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private apiUrl = `${environment.apiUrl}/users`;

  constructor(private http: HttpClient) {}

  /**
   * Get all users
   */
  getAllUsers(): Observable<User[]> {
    return this.http.get<any>(this.apiUrl).pipe(
      map(response => {
        if (Array.isArray(response)) {
          return response;
        }
        if (response && response.data && Array.isArray(response.data)) {
          return response.data;
        }
        console.warn('Unexpected API response format:', response);
        return [];
      })
    );
  }

  /**
   * Get a specific user by ID
   */
  getUserById(userId: number): Observable<User> {
    return this.http.get<any>(`${this.apiUrl}/${userId}`).pipe(
      map(response => {
        if (response && response.data) {
          return response.data;
        }
        return response;
      })
    );
  }

  /**
   * Get employees by hospital (filters out Management department)
   */
  getEmployeesByHospital(hospitalId?: number): Observable<User[]> {
    return this.getAllUsers().pipe(
      map(users => {
        // Filter out Management department users
        let employees = users.filter(user => user.Department !== 'Management');
        
        // If hospitalId is provided, filter by hospital
        if (hospitalId) {
          employees = employees.filter(user => user.HospitalId === hospitalId);
        }
        
        return employees;
      })
    );
  }
}
