import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { NavbarComponent } from '../navbar/navbar.component';
import { AlertBannerComponent } from '../alert-banner/alert-banner.component';
import { ShiftService } from '../../services/shift.service';
import { AuthService } from '../../services/auth.service';
import { Shift, Zone } from '../../models/shift.model';
import { User } from '../../models/user.model';

interface StressDataPoint {
  date: string;
  stressLevel: number;
  zone: Zone;
  displayDate: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent, AlertBannerComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  currentUser: User | null = null;
  shifts: Shift[] = []; // All shifts (finished + recommended)
  recentShifts: Shift[] = []; // Only finished shifts for display
  stressData: StressDataPoint[] = [];
  loading = true;
  errorMessage = '';
  generatingShifts = false;

  // Shift Recommendations
  recommendations: any = null;
  loadingRecommendations = false;
  recommendationsError = '';
  showRecommendations = false;

  // Stats
  totalShifts = 0;
  averageStress = 0;
  averageSleep = 0;
  currentZone: Zone = 'green';
  latestShift: Shift | null = null;

  constructor(
    private shiftService: ShiftService,
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    // Subscribe to current user
    this.authService.currentUser$.subscribe(user => {
      if (user && user.Department === 'Management') {
        this.router.navigate(['/employees']);
        return;
      }
      this.currentUser = user;
    });

    // If no authenticated user, redirect to start page
    if (!this.authService.isAuthenticated()) {
      this.loading = false;
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

    this.shiftService.getUserShifts().subscribe({
      next: (shifts) => {
        // Ensure shifts is an array
        if (!Array.isArray(shifts)) {
          this.errorMessage = 'Invalid data format received from server.';
          this.loading = false;
          return;
        }

        // Separate finished shifts from recommended/future shifts
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Start of today

        const finishedShifts = shifts.filter(shift => {
          // Filter out recommended shifts AND future shifts
          if (shift.IsRecommended) return false;
          const shiftDate = new Date(shift.ShiftDate);
          shiftDate.setHours(0, 0, 0, 0);
          return shiftDate <= today; // Only include shifts up to today
        });
        const recommendedShifts = shifts.filter(shift => shift.IsRecommended);

        // Only use finished shifts for stats and charts
        this.recentShifts = finishedShifts
          .sort((a, b) => {
            // First sort by ShiftDate
            const dateCompare = new Date(b.ShiftDate).getTime() - new Date(a.ShiftDate).getTime();
            if (dateCompare !== 0) return dateCompare;
            // If dates are equal, sort by CreatedAt (most recent first)
            return new Date(b.CreatedAt || 0).getTime() - new Date(a.CreatedAt || 0).getTime();
          })
          .slice(0, 7); // Last 7 finished shifts

        this.calculateStats(finishedShifts);
        this.prepareStressData(this.recentShifts);
        this.latestShift = this.recentShifts.length > 0 ? this.recentShifts[0] : null;

        // Store all shifts for the full list view
        this.shifts = shifts;

        // If there are recommended shifts, load the recommendation summary
        if (recommendedShifts.length > 0) {
          this.loadShiftRecommendations();
        }

        this.loading = false;
        this.cdr.detectChanges(); // Manually trigger change detection
      },
      error: (error) => {
        this.errorMessage = error.error?.message || 'Failed to load dashboard data. Please try again.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  /**
   * Calculate statistics from shifts
   */
  calculateStats(shifts: Shift[]): void {
    // Receives only finished shifts (already filtered)
    this.totalShifts = shifts.length;

    if (shifts.length === 0) {
      this.averageStress = 0;
      this.averageSleep = 0;
      this.currentZone = 'green';
      return;
    }

    const totalStress = shifts.reduce((sum, shift) => sum + shift.StressLevel, 0);
    const totalSleep = shifts.reduce((sum, shift) => sum + shift.HoursSleptBefore, 0);

    this.averageStress = Math.round(totalStress / shifts.length);
    this.averageSleep = Math.round((totalSleep / shifts.length) * 10) / 10;

    // Get current zone from latest finished shift
    if (shifts.length > 0 && shifts[0].Zone) {
      this.currentZone = shifts[0].Zone;
    }
  }

  /**
   * Prepare stress data for graph
   * Receives only finished shifts (already filtered)
   */
  prepareStressData(shifts: Shift[]): void {
    this.stressData = shifts
      .reverse() // Oldest to newest for graph
      .map(shift => ({
        date: shift.ShiftDate,
        stressLevel: shift.StressLevel,
        zone: shift.Zone || 'green',
        displayDate: this.formatShortDate(shift.ShiftDate)
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
   * Generate AI-recommended shifts and create them in database
   */
  generateRecommendedShifts(): void {
    if (!this.currentUser?.UserId) {
      alert('Please log in to generate shift recommendations');
      return;
    }

    if (confirm('Generate 7 days of AI-recommended shifts? These will appear as suggested shifts you can review and edit.')) {
      this.generatingShifts = true;
      this.shiftService.generateRecommendedShifts(this.currentUser.UserId, 7)
        .subscribe({
          next: (response) => {
            this.generatingShifts = false;
            if (response.success) {
              alert(`✅ Generated ${response.created_shifts?.length || 0} recommended shifts!`);
              // Reload shifts to show new recommendations
              this.loadDashboardData();
              // Also load and display the recommendation summary
              this.loadShiftRecommendations();
            } else {
              alert('Failed to generate shifts: ' + (response.error || 'Unknown error'));
            }
          },
          error: (error) => {
            this.generatingShifts = false;
            console.error('Error generating shifts:', error);
            alert('Failed to generate AI-recommended shifts. Please try again.');
          }
        });
    }
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

  /**
   * Get urgency badge class
   */
  getUrgencyClass(urgency?: string): string {
    switch(urgency) {
      case 'routine': return 'urgency-routine';
      case 'attention_needed': return 'urgency-attention';
      case 'urgent': return 'urgency-urgent';
      case 'critical': return 'urgency-critical';
      default: return 'urgency-routine';
    }
  }

  /**
   * Get category icon
   */
  getCategoryIcon(category: string): string {
    const icons: { [key: string]: string } = {
      'crisis': '🚨',
      'burnout': '😰',
      'patient_safety': '🏥',
      'wellness': '💚',
      'trend': '📊'
    };
    return icons[category] || '📌';
  }

  /**
   * Get timing badge class
   */
  getTimingClass(timing: string): string {
    switch(timing) {
      case 'immediate': return 'timing-immediate';
      case 'today': return 'timing-today';
      case 'this_week': return 'timing-week';
      case 'ongoing': return 'timing-ongoing';
      default: return 'timing-ongoing';
    }
  }

  /**
   * Format timing text
   */
  formatTiming(timing: string): string {
    return timing.replace('_', ' ').toUpperCase();
  }

  /**
   * Load AI-recommended shifts from database
   * Only called when user clicks "Generate AI Shifts" button
   * Shows summary of recommended schedule
   */
  loadShiftRecommendations(): void {
    if (!this.currentUser) return;

    this.loadingRecommendations = true;
    this.recommendationsError = '';

    this.shiftService.getShiftRecommendations(this.currentUser.UserId!, 7).subscribe({
      next: (response) => {
        if (response.success) {
          this.recommendations = response;
          this.showRecommendations = true;
        } else {
          this.recommendationsError = response.error || 'Failed to load recommendations';
        }
        this.loadingRecommendations = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('[Dashboard] Error loading recommendations:', error);
        this.recommendationsError = 'Could not load recommendation summary';
        this.loadingRecommendations = false;
        this.cdr.detectChanges();
      }
    });
  }

  /**
   * Toggle recommendations visibility
   */
  toggleRecommendations(): void {
    this.showRecommendations = !this.showRecommendations;
  }

  /**
   * Get shift type badge class
   */
  getShiftTypeBadge(shiftType: string): string {
    const classes: { [key: string]: string } = {
      'rest': 'shift-rest',
      'day': 'shift-day',
      'night': 'shift-night'
    };
    return classes[shiftType] || 'shift-day';
  }

  /**
   * Get risk level class
   */
  getRiskLevelClass(riskLevel: string): string {
    const classes: { [key: string]: string } = {
      'low': 'risk-low',
      'medium': 'risk-medium',
      'high': 'risk-high'
    };
    return classes[riskLevel] || 'risk-medium';
  }

  /**
   * Get recovery priority badge
   */
  getRecoveryPriorityBadge(priority: string): string {
    const classes: { [key: string]: string } = {
      'low': 'priority-low',
      'medium': 'priority-medium',
      'high': 'priority-high',
      'urgent': 'priority-urgent'
    };
    return classes[priority] || 'priority-medium';
  }
}
