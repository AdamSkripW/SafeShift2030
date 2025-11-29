import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { NavbarComponent } from '../../components/navbar/navbar.component';
import { ShiftService } from '../../services/shift.service';
import { UserProfileService } from '../../services/user-profile.service';
import { Shift, Zone } from '../../models/shift.model';
import { UserProfile } from '../../models/user-profile.model';

interface StressDataPoint {
  date: string;
  stressLevel: number;
  zone: Zone;
  displayDate: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  userProfile: UserProfile | null = null;
  recentShifts: Shift[] = [];
  stressData: StressDataPoint[] = [];
  loading = true;
  errorMessage = '';

  // Stats
  totalShifts = 0;
  averageStress = 0;
  averageSleep = 0;
  currentZone: Zone = 'green';
  latestShift: Shift | null = null;

  constructor(
    private shiftService: ShiftService,
    private userProfileService: UserProfileService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.userProfile = this.userProfileService.getUserProfile();
    
    // If no user profile, redirect to start page
    if (!this.userProfile) {
      this.loading = false; // Stop loading before redirect
      this.router.navigate(['/start']);
      return;
    }
    
    this.loadDashboardData();
  }

  /**
   * Load all dashboard data
   */
  loadDashboardData(): void {
    this.loading = true;
    this.errorMessage = '';

    console.log('Loading dashboard data...');
    this.shiftService.getUserShifts().subscribe({
      next: (shifts) => {
        console.log('Received shifts:', shifts.length);
        this.recentShifts = shifts
          .sort((a, b) => new Date(b.shiftDate).getTime() - new Date(a.shiftDate).getTime())
          .slice(0, 7); // Last 7 shifts

        this.calculateStats(shifts);
        this.prepareStressData(this.recentShifts);
        this.latestShift = this.recentShifts.length > 0 ? this.recentShifts[0] : null;
        this.loading = false;
        console.log('Dashboard loaded, loading =', this.loading);
        this.cdr.detectChanges(); // Manually trigger change detection
      },
      error: (error) => {
        console.error('Error loading dashboard data:', error);
        this.errorMessage = 'Failed to load dashboard data.';
        this.loading = false;
      }
    });
  }

  /**
   * Calculate statistics from shifts
   */
  calculateStats(shifts: Shift[]): void {
    this.totalShifts = shifts.length;

    if (shifts.length === 0) {
      this.averageStress = 0;
      this.averageSleep = 0;
      this.currentZone = 'green';
      return;
    }

    const totalStress = shifts.reduce((sum, shift) => sum + shift.stressLevel, 0);
    const totalSleep = shifts.reduce((sum, shift) => sum + shift.hoursSleptBefore, 0);

    this.averageStress = Math.round(totalStress / shifts.length);
    this.averageSleep = Math.round((totalSleep / shifts.length) * 10) / 10;

    // Get current zone from latest shift
    if (shifts.length > 0 && shifts[0].zone) {
      this.currentZone = shifts[0].zone;
    }
  }

  /**
   * Prepare stress data for graph
   */
  prepareStressData(shifts: Shift[]): void {
    this.stressData = shifts
      .reverse() // Oldest to newest for graph
      .map(shift => ({
        date: shift.shiftDate,
        stressLevel: shift.stressLevel,
        zone: shift.zone || 'green',
        displayDate: this.formatShortDate(shift.shiftDate)
      }));
  }

  /**
   * Format date for display
   */
  formatShortDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  /**
   * Get zone color class
   */
  getZoneClass(zone?: Zone): string {
    if (!zone) return 'zone-unknown';
    return `zone-${zone}`;
  }

  /**
   * Get stress level color
   */
  getStressColor(level: number): string {
    if (level <= 3) return '#48bb78'; // Green
    if (level <= 6) return '#ecc94b'; // Yellow
    return '#f56565'; // Red
  }

  /**
   * Calculate bar height percentage
   */
  getBarHeight(stressLevel: number): number {
    return (stressLevel / 10) * 100;
  }

  /**
   * Navigate to create new shift
   */
  createNewShift(): void {
    this.router.navigate(['/shift/new']);
  }

  /**
   * Navigate to all shifts
   */
  viewAllShifts(): void {
    this.router.navigate(['/shifts']);
  }

  /**
   * Get greeting based on time of day
   */
  getGreeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  }
}
