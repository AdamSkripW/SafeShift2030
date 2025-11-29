import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, delay } from 'rxjs';
import { map } from 'rxjs/operators';
import { Shift, ShiftFormData } from '../models/shift.model';
import { User } from '../models/user.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ShiftService {
  private apiUrl = `${environment.apiUrl}/shifts`;
  private useMockData = false; // Toggle this to switch between mock and real API
  private mockShifts: Shift[] = [];
  private nextId = 1;

  constructor(private http: HttpClient) {
    if (this.useMockData && this.mockShifts.length === 0) {
      this.initializeMockData();
    }
  }

  /**
   * Get current user from localStorage
   */
  private getCurrentUser(): User | null {
    const userJson = localStorage.getItem('currentUser');
    if (userJson) {
      try {
        return JSON.parse(userJson) as User;
      } catch (error) {
        console.error('Error parsing user from localStorage:', error);
        return null;
      }
    }
    return null;
  }

  /**
   * Initialize mock data
   */
  private initializeMockData(): void {
    const today = new Date();

    this.mockShifts = [
      {
        ShiftId: this.nextId++,
        UserId: 1,
        ShiftDate: this.getDateString(today, -7),
        HoursSleptBefore: 7,
        ShiftType: 'day',
        ShiftLengthHours: 8,
        PatientsCount: 12,
        StressLevel: 4,
        ShiftNote: 'Smooth day, good team coordination',
        SafeShiftIndex: 35,
        Zone: 'green',
        AiExplanation: 'Your SafeShift Index is in the green zone. You had adequate sleep (7 hours) and moderate workload. Keep maintaining this healthy balance.',
        AiTips: '• Continue prioritizing 7-8 hours of sleep\n• Stay hydrated throughout your shift\n• Take regular breaks when possible',
        CreatedAt: this.getDateString(today, -7),
        UpdatedAt: this.getDateString(today, -7)
      },
      {
        ShiftId: this.nextId++,
        UserId: 1,
        ShiftDate: this.getDateString(today, -6),
        HoursSleptBefore: 6,
        ShiftType: 'day',
        ShiftLengthHours: 10,
        PatientsCount: 15,
        StressLevel: 6,
        ShiftNote: 'Busy day, short-staffed',
        SafeShiftIndex: 52,
        Zone: 'yellow',
        AiExplanation: 'Your SafeShift Index is in the yellow zone. You had less sleep than ideal (6 hours) combined with a longer shift and higher patient load.',
        AiTips: '• Try to get at least 7-8 hours of sleep tonight\n• Consider a 20-minute power nap if possible\n• Practice stress-relief techniques during breaks',
        CreatedAt: this.getDateString(today, -6),
        UpdatedAt: this.getDateString(today, -6)
      },
      {
        ShiftId: this.nextId++,
        UserId: 1,
        ShiftDate: this.getDateString(today, -5),
        HoursSleptBefore: 8,
        ShiftType: 'day',
        ShiftLengthHours: 8,
        PatientsCount: 10,
        StressLevel: 3,
        ShiftNote: 'Great day, well-rested',
        SafeShiftIndex: 22,
        Zone: 'green',
        AiExplanation: 'Excellent! Your SafeShift Index is in the green zone. You had great sleep (8 hours) and a manageable workload.',
        AiTips: '• Maintain this sleep schedule\n• Keep up the good work-life balance\n• Share your wellness strategies with colleagues',
        CreatedAt: this.getDateString(today, -5),
        UpdatedAt: this.getDateString(today, -5)
      },
      {
        ShiftId: this.nextId++,
        UserId: 1,
        ShiftDate: this.getDateString(today, -4),
        HoursSleptBefore: 5,
        ShiftType: 'night',
        ShiftLengthHours: 12,
        PatientsCount: 18,
        StressLevel: 8,
        ShiftNote: 'Difficult night shift, two critical patients',
        SafeShiftIndex: 73,
        Zone: 'red',
        AiExplanation: 'Your SafeShift Index is in the red zone. You had insufficient sleep (5 hours) before a demanding 12-hour night shift with high stress levels.',
        AiTips: '• Prioritize recovery sleep as soon as possible\n• Consider requesting time off if fatigue persists\n• Speak with your supervisor about workload concerns\n• Practice deep breathing exercises',
        CreatedAt: this.getDateString(today, -4),
        UpdatedAt: this.getDateString(today, -4)
      },
      {
        ShiftId: this.nextId++,
        UserId: 1,
        ShiftDate: this.getDateString(today, -3),
        HoursSleptBefore: 6.5,
        ShiftType: 'day',
        ShiftLengthHours: 9,
        PatientsCount: 14,
        StressLevel: 5,
        ShiftNote: 'Recovery day after night shift',
        SafeShiftIndex: 48,
        Zone: 'yellow',
        AiExplanation: 'Your SafeShift Index is in the yellow zone. You\'re recovering from the previous demanding shift, but still showing some fatigue.',
        AiTips: '• Focus on quality sleep tonight\n• Eat nutritious meals to support recovery\n• Light exercise can help regulate your sleep cycle',
        CreatedAt: this.getDateString(today, -3),
        UpdatedAt: this.getDateString(today, -3)
      },
      {
        ShiftId: this.nextId++,
        UserId: 1,
        ShiftDate: this.getDateString(today, -2),
        HoursSleptBefore: 7.5,
        ShiftType: 'day',
        ShiftLengthHours: 8,
        PatientsCount: 11,
        StressLevel: 4,
        ShiftNote: 'Feeling better, good sleep',
        SafeShiftIndex: 38,
        Zone: 'green',
        AiExplanation: 'Back in the green zone! Your recovery sleep helped, and you had a more manageable shift.',
        AiTips: '• Continue this positive trend\n• Maintain consistent sleep schedule\n• Stay connected with your support network',
        CreatedAt: this.getDateString(today, -2),
        UpdatedAt: this.getDateString(today, -2)
      },
      {
        ShiftId: this.nextId++,
        UserId: 1,
        ShiftDate: this.getDateString(today, -1),
        HoursSleptBefore: 7,
        ShiftType: 'day',
        ShiftLengthHours: 8,
        PatientsCount: 13,
        StressLevel: 5,
        ShiftNote: 'Normal day',
        SafeShiftIndex: 42,
        Zone: 'yellow',
        AiExplanation: 'Your SafeShift Index is in the yellow zone. Adequate sleep but moderate stress levels.',
        AiTips: '• Monitor your stress levels\n• Practice mindfulness during breaks\n• Ensure you\'re taking all scheduled breaks',
        CreatedAt: this.getDateString(today, -1),
        UpdatedAt: this.getDateString(today, -1)
      }
    ];
  }

  /**
   * Helper to get date string
   */
  private getDateString(date: Date, daysOffset: number = 0): string {
    const newDate = new Date(date);
    newDate.setDate(newDate.getDate() + daysOffset);
    return newDate.toISOString().split('T')[0];
  }

  /**
   * Calculate SafeShift Index (mock calculation)
   */
  private calculateSafeShiftIndex(shift: ShiftFormData): { index: number; zone: 'green' | 'yellow' | 'red' } {
    let index = 0;

    // Sleep factor (0-30 points)
    if (shift.HoursSleptBefore < 5) index += 30;
    else if (shift.HoursSleptBefore < 6) index += 20;
    else if (shift.HoursSleptBefore < 7) index += 10;
    else index += 5;

    // Shift length factor (0-20 points)
    if (shift.ShiftLengthHours > 10) index += 20;
    else if (shift.ShiftLengthHours > 8) index += 10;
    else index += 5;

    // Night shift factor (0-15 points)
    if (shift.ShiftType === 'night') index += 15;

    // Stress factor (0-25 points)
    index += Math.round((shift.StressLevel / 10) * 25);

    // Patient load factor (0-10 points)
    if (shift.PatientsCount > 15) index += 10;
    else if (shift.PatientsCount > 10) index += 5;

    // Determine zone
    let zone: 'green' | 'yellow' | 'red';
    if (index < 40) zone = 'green';
    else if (index < 60) zone = 'yellow';
    else zone = 'red';

    return { index, zone };
  }

  /**
   * Generate AI explanation (mock)
   */
  private generateAIExplanation(shift: ShiftFormData, index: number, zone: string): string {
    const sleepQuality = shift.HoursSleptBefore >= 7 ? 'adequate' : shift.HoursSleptBefore >= 6 ? 'moderate' : 'insufficient';
    const stressLevel = shift.StressLevel >= 7 ? 'high' : shift.StressLevel >= 4 ? 'moderate' : 'low';

    return `Your SafeShift Index is in the ${zone} zone (${index}/100). You had ${sleepQuality} sleep (${shift.HoursSleptBefore} hours) before a ${shift.ShiftLengthHours}-hour ${shift.ShiftType} shift with ${stressLevel} stress levels.`;
  }

  /**
   * Generate AI tips (mock)
   */
  private generateAITips(zone: string): string {
    if (zone === 'green') {
      return '• Maintain your current sleep schedule\n• Continue healthy habits\n• Stay hydrated and take breaks';
    } else if (zone === 'yellow') {
      return '• Prioritize 7-8 hours of sleep tonight\n• Take all scheduled breaks\n• Practice stress management techniques\n• Monitor your energy levels';
    } else {
      return '• Get recovery sleep as soon as possible\n• Consider requesting time off\n• Speak with supervisor about workload\n• Practice self-care and seek support\n• Avoid consecutive demanding shifts';
    }
  }

  /**
   * Create a new shift
   */
  createShift(shiftData: ShiftFormData): Observable<Shift> {
    if (this.useMockData) {
      const { index, zone } = this.calculateSafeShiftIndex(shiftData);

      const newShift: Shift = {
        ShiftId: this.nextId++,
        UserId: 1,
        ...shiftData,
        SafeShiftIndex: index,
        Zone: zone,
        AiExplanation: this.generateAIExplanation(shiftData, index, zone),
        AiTips: this.generateAITips(zone),
        CreatedAt: new Date().toISOString(),
        UpdatedAt: new Date().toISOString()
      };

      this.mockShifts.unshift(newShift);
      return of(newShift).pipe(delay(500)); // Simulate network delay
    }

    // Get current user ID from localStorage
    const currentUser = this.getCurrentUser();
    if (!currentUser || !currentUser.UserId) {
      throw new Error('No authenticated user found');
    }

    // Add UserId to shift data
    const shiftWithUserId = {
      ...shiftData,
      UserId: currentUser.UserId
    };

    return this.http.post<Shift>(this.apiUrl, shiftWithUserId);
  }

  /**
   * Get all shifts for the current user
   */
  getUserShifts(): Observable<Shift[]> {
    if (this.useMockData) {
      return of([...this.mockShifts]).pipe(delay(300));
    }

    // Get current user ID from localStorage
    const currentUser = this.getCurrentUser();
    if (!currentUser || !currentUser.UserId) {
      console.warn('No authenticated user found');
      return of([]);
    }

    // Add user_id query parameter
    return this.http.get<any>(this.apiUrl, {
      params: { user_id: currentUser.UserId.toString() }
    }).pipe(
      map(response => {
        // Handle both array and object responses
        if (Array.isArray(response)) {
          return response;
        }
        // If response is an object with a shifts property
        if (response && response.shifts && Array.isArray(response.shifts)) {
          return response.shifts;
        }
        // If response is an object with a data property
        if (response && response.data && Array.isArray(response.data)) {
          return response.data;
        }
        // Fallback to empty array
        console.warn('Unexpected API response format:', response);
        return [];
      })
    );
  }

  /**
   * Get a specific shift by ID
   */
  getShiftById(shiftId: number): Observable<Shift> {
    if (this.useMockData) {
      const shift = this.mockShifts.find(s => s.ShiftId === shiftId);
      return of(shift!).pipe(delay(200));
    }
    return this.http.get<Shift>(`${this.apiUrl}/${shiftId}`);
  }

  /**
   * Update an existing shift
   */
  updateShift(shiftId: number, shiftData: Partial<ShiftFormData>): Observable<Shift> {
    if (this.useMockData) {
      const index = this.mockShifts.findIndex(s => s.ShiftId === shiftId);
      if (index !== -1) {
        this.mockShifts[index] = { ...this.mockShifts[index], ...shiftData };
        return of(this.mockShifts[index]).pipe(delay(300));
      }
    }
    return this.http.put<Shift>(`${this.apiUrl}/${shiftId}`, shiftData);
  }

  /**
   * Delete a shift
   */
  deleteShift(shiftId: number): Observable<void> {
    if (this.useMockData) {
      const index = this.mockShifts.findIndex(s => s.ShiftId === shiftId);
      if (index !== -1) {
        this.mockShifts.splice(index, 1);
      }
      return of(void 0).pipe(delay(200));
    }
    return this.http.delete<void>(`${this.apiUrl}/${shiftId}`);
  }

  /**
   * Get shifts within a date range
   */
  getShiftsByDateRange(startDate: string, endDate: string): Observable<Shift[]> {
    if (this.useMockData) {
      const filtered = this.mockShifts.filter(shift => {
        return shift.ShiftDate >= startDate && shift.ShiftDate <= endDate;
      });
      return of(filtered).pipe(delay(300));
    }
    return this.http.get<any>(`${this.apiUrl}/range`, {
      params: { startDate, endDate }
    }).pipe(
      map(response => {
        // Handle both array and object responses
        if (Array.isArray(response)) {
          return response;
        }
        if (response && response.shifts && Array.isArray(response.shifts)) {
          return response.shifts;
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
   * Get latest shift for the user
   */
  getLatestShift(): Observable<Shift> {
    if (this.useMockData) {
      const latest = this.mockShifts[0];
      return of(latest).pipe(delay(200));
    }
    return this.http.get<Shift>(`${this.apiUrl}/latest`);
  }
}
