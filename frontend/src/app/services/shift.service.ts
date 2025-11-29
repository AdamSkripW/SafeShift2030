import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, delay } from 'rxjs';
import { Shift, ShiftFormData } from '../models/shift.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ShiftService {
  private apiUrl = `${environment.apiUrl}/shifts`;
  private useMockData = true; // Toggle this to switch between mock and real API
  private mockShifts: Shift[] = [];
  private nextId = 1;

  constructor(private http: HttpClient) {
    this.initializeMockData();
  }

  /**
   * Initialize mock data
   */
  private initializeMockData(): void {
    const today = new Date();
    
    this.mockShifts = [
      {
        shiftId: this.nextId++,
        userId: 1,
        shiftDate: this.getDateString(today, -7),
        hoursSleptBefore: 7,
        shiftType: 'day',
        shiftLengthHours: 8,
        patientsCount: 12,
        stressLevel: 4,
        shiftNote: 'Smooth day, good team coordination',
        safeShiftIndex: 35,
        zone: 'green',
        aiExplanation: 'Your SafeShift Index is in the green zone. You had adequate sleep (7 hours) and moderate workload. Keep maintaining this healthy balance.',
        aiTips: '• Continue prioritizing 7-8 hours of sleep\n• Stay hydrated throughout your shift\n• Take regular breaks when possible',
        createdAt: this.getDateString(today, -7),
        updatedAt: this.getDateString(today, -7)
      },
      {
        shiftId: this.nextId++,
        userId: 1,
        shiftDate: this.getDateString(today, -6),
        hoursSleptBefore: 6,
        shiftType: 'day',
        shiftLengthHours: 10,
        patientsCount: 15,
        stressLevel: 6,
        shiftNote: 'Busy day, short-staffed',
        safeShiftIndex: 52,
        zone: 'yellow',
        aiExplanation: 'Your SafeShift Index is in the yellow zone. You had less sleep than ideal (6 hours) combined with a longer shift and higher patient load.',
        aiTips: '• Try to get at least 7-8 hours of sleep tonight\n• Consider a 20-minute power nap if possible\n• Practice stress-relief techniques during breaks',
        createdAt: this.getDateString(today, -6),
        updatedAt: this.getDateString(today, -6)
      },
      {
        shiftId: this.nextId++,
        userId: 1,
        shiftDate: this.getDateString(today, -5),
        hoursSleptBefore: 8,
        shiftType: 'day',
        shiftLengthHours: 8,
        patientsCount: 10,
        stressLevel: 3,
        shiftNote: 'Great day, well-rested',
        safeShiftIndex: 22,
        zone: 'green',
        aiExplanation: 'Excellent! Your SafeShift Index is in the green zone. You had great sleep (8 hours) and a manageable workload.',
        aiTips: '• Maintain this sleep schedule\n• Keep up the good work-life balance\n• Share your wellness strategies with colleagues',
        createdAt: this.getDateString(today, -5),
        updatedAt: this.getDateString(today, -5)
      },
      {
        shiftId: this.nextId++,
        userId: 1,
        shiftDate: this.getDateString(today, -4),
        hoursSleptBefore: 5,
        shiftType: 'night',
        shiftLengthHours: 12,
        patientsCount: 18,
        stressLevel: 8,
        shiftNote: 'Difficult night shift, two critical patients',
        safeShiftIndex: 73,
        zone: 'red',
        aiExplanation: 'Your SafeShift Index is in the red zone. You had insufficient sleep (5 hours) before a demanding 12-hour night shift with high stress levels.',
        aiTips: '• Prioritize recovery sleep as soon as possible\n• Consider requesting time off if fatigue persists\n• Speak with your supervisor about workload concerns\n• Practice deep breathing exercises',
        createdAt: this.getDateString(today, -4),
        updatedAt: this.getDateString(today, -4)
      },
      {
        shiftId: this.nextId++,
        userId: 1,
        shiftDate: this.getDateString(today, -3),
        hoursSleptBefore: 6.5,
        shiftType: 'day',
        shiftLengthHours: 9,
        patientsCount: 14,
        stressLevel: 5,
        shiftNote: 'Recovery day after night shift',
        safeShiftIndex: 48,
        zone: 'yellow',
        aiExplanation: 'Your SafeShift Index is in the yellow zone. You\'re recovering from the previous demanding shift, but still showing some fatigue.',
        aiTips: '• Focus on quality sleep tonight\n• Eat nutritious meals to support recovery\n• Light exercise can help regulate your sleep cycle',
        createdAt: this.getDateString(today, -3),
        updatedAt: this.getDateString(today, -3)
      },
      {
        shiftId: this.nextId++,
        userId: 1,
        shiftDate: this.getDateString(today, -2),
        hoursSleptBefore: 7.5,
        shiftType: 'day',
        shiftLengthHours: 8,
        patientsCount: 11,
        stressLevel: 4,
        shiftNote: 'Feeling better, good sleep',
        safeShiftIndex: 38,
        zone: 'green',
        aiExplanation: 'Back in the green zone! Your recovery sleep helped, and you had a more manageable shift.',
        aiTips: '• Continue this positive trend\n• Maintain consistent sleep schedule\n• Stay connected with your support network',
        createdAt: this.getDateString(today, -2),
        updatedAt: this.getDateString(today, -2)
      },
      {
        shiftId: this.nextId++,
        userId: 1,
        shiftDate: this.getDateString(today, -1),
        hoursSleptBefore: 7,
        shiftType: 'day',
        shiftLengthHours: 8,
        patientsCount: 13,
        stressLevel: 5,
        shiftNote: 'Normal day',
        safeShiftIndex: 42,
        zone: 'yellow',
        aiExplanation: 'Your SafeShift Index is in the yellow zone. Adequate sleep but moderate stress levels.',
        aiTips: '• Monitor your stress levels\n• Practice mindfulness during breaks\n• Ensure you\'re taking all scheduled breaks',
        createdAt: this.getDateString(today, -1),
        updatedAt: this.getDateString(today, -1)
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
    if (shift.hoursSleptBefore < 5) index += 30;
    else if (shift.hoursSleptBefore < 6) index += 20;
    else if (shift.hoursSleptBefore < 7) index += 10;
    else index += 5;
    
    // Shift length factor (0-20 points)
    if (shift.shiftLengthHours > 10) index += 20;
    else if (shift.shiftLengthHours > 8) index += 10;
    else index += 5;
    
    // Night shift factor (0-15 points)
    if (shift.shiftType === 'night') index += 15;
    
    // Stress factor (0-25 points)
    index += Math.round((shift.stressLevel / 10) * 25);
    
    // Patient load factor (0-10 points)
    if (shift.patientsCount > 15) index += 10;
    else if (shift.patientsCount > 10) index += 5;
    
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
    const sleepQuality = shift.hoursSleptBefore >= 7 ? 'adequate' : shift.hoursSleptBefore >= 6 ? 'moderate' : 'insufficient';
    const stressLevel = shift.stressLevel >= 7 ? 'high' : shift.stressLevel >= 4 ? 'moderate' : 'low';
    
    return `Your SafeShift Index is in the ${zone} zone (${index}/100). You had ${sleepQuality} sleep (${shift.hoursSleptBefore} hours) before a ${shift.shiftLengthHours}-hour ${shift.shiftType} shift with ${stressLevel} stress levels.`;
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
        shiftId: this.nextId++,
        userId: 1,
        ...shiftData,
        safeShiftIndex: index,
        zone: zone,
        aiExplanation: this.generateAIExplanation(shiftData, index, zone),
        aiTips: this.generateAITips(zone),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      this.mockShifts.unshift(newShift);
      return of(newShift).pipe(delay(500)); // Simulate network delay
    }
    return this.http.post<Shift>(this.apiUrl, shiftData);
  }

  /**
   * Get all shifts for the current user
   */
  getUserShifts(): Observable<Shift[]> {
    if (this.useMockData) {
      return of([...this.mockShifts]).pipe(delay(300));
    }
    return this.http.get<Shift[]>(this.apiUrl);
  }

  /**
   * Get a specific shift by ID
   */
  getShiftById(shiftId: number): Observable<Shift> {
    if (this.useMockData) {
      const shift = this.mockShifts.find(s => s.shiftId === shiftId);
      return of(shift!).pipe(delay(200));
    }
    return this.http.get<Shift>(`${this.apiUrl}/${shiftId}`);
  }

  /**
   * Update an existing shift
   */
  updateShift(shiftId: number, shiftData: Partial<ShiftFormData>): Observable<Shift> {
    if (this.useMockData) {
      const index = this.mockShifts.findIndex(s => s.shiftId === shiftId);
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
      const index = this.mockShifts.findIndex(s => s.shiftId === shiftId);
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
        return shift.shiftDate >= startDate && shift.shiftDate <= endDate;
      });
      return of(filtered).pipe(delay(300));
    }
    return this.http.get<Shift[]>(`${this.apiUrl}/range`, {
      params: { startDate, endDate }
    });
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
