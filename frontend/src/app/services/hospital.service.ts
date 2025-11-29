import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Hospital } from '../models/hospital.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class HospitalService {
  private apiUrl = `${environment.apiUrl}/hospitals`;

  constructor(private http: HttpClient) {}

  /**
   * Get all hospitals
   */
  getHospitals(): Observable<Hospital[]> {
    return this.http.get<any>(this.apiUrl).pipe(
      map(response => {
        if (response.success && response.data) {
          return response.data;
        }
        return [];
      })
    );
  }

  /**
   * Get a specific hospital by ID
   */
  getHospitalById(hospitalId: number): Observable<Hospital> {
    return this.http.get<any>(`${this.apiUrl}/${hospitalId}`).pipe(
      map(response => {
        if (response.success && response.data) {
          return response.data;
        }
        throw new Error('Hospital not found');
      })
    );
  }
}
