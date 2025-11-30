import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { NavbarComponent } from '../../components/navbar/navbar.component';
import { ShiftService } from '../../services/shift.service';
import { Shift, Zone } from '../../models/shift.model';

@Component({
  selector: 'app-shifts-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent],
  templateUrl: './shifts-dashboard.component.html',
  styleUrls: ['./shifts-dashboard.component.css']
})
export class ShiftsDashboardComponent implements OnInit {
  shifts: Shift[] = [];
  loading = true;
  errorMessage = '';
  latestShift: Shift | null = null;
  selectedShiftId: number | null = null;

  constructor(
    private shiftService: ShiftService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    // Redirect managers to employees page
    const userJson = localStorage.getItem('currentUser');
    if (userJson) {
      const user = JSON.parse(userJson);
      if (user.Department === 'Management') {
        this.router.navigate(['/employees']);
        return;
      }
    }
    this.loadShifts();
  }

  /**
   * Load all user shifts
   */
  loadShifts(): void {
    this.loading = true;
    this.errorMessage = '';

    this.shiftService.getUserShifts().subscribe({
      next: (shifts) => {
        console.log('Received shifts:', shifts);

        // Ensure shifts is an array
        if (!Array.isArray(shifts)) {
          console.error('Shifts is not an array:', shifts);
          this.errorMessage = 'Invalid data format received from server.';
          this.loading = false;
          this.cdr.detectChanges();
          return;
        }

        this.shifts = shifts.sort((a, b) => {
          return new Date(b.ShiftDate).getTime() - new Date(a.ShiftDate).getTime();
        });
        this.latestShift = this.shifts.length > 0 ? this.shifts[0] : null;
        this.selectedShiftId = this.latestShift?.ShiftId || null;
        this.loading = false;
        this.cdr.detectChanges(); // Manually trigger change detection
      },
      error: (error) => {
        console.error('Error loading shifts:', error);
        this.errorMessage = error.error?.message || 'Failed to load shifts. Please try again.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  /**
   * Navigate to create new shift
   */
  createNewShift(): void {
    this.router.navigate(['/shift/new']);
  }

  /**
   * Get zone color class
   */
  getZoneClass(zone?: Zone): string {
    if (!zone) return 'zone-unknown';
    return `zone-${zone}`;
  }

  /**
   * Get zone display text
   */
  getZoneText(zone?: Zone): string {
    if (!zone) return 'Not Calculated';
    return zone.charAt(0).toUpperCase() + zone.slice(1) + ' Zone';
  }

  /**
   * Format date for display
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  /**
   * Get shift type icon
   */
  getShiftTypeIcon(shiftType: string): string {
    return shiftType === 'night' ? '🌙' : '☀️';
  }

  /**
   * Delete a shift
   */
  deleteShift(shiftId: number | undefined, event: Event): void {
    event.stopPropagation();

    if (!shiftId) return;

    if (confirm('Are you sure you want to delete this shift?')) {
      this.shiftService.deleteShift(shiftId).subscribe({
        next: () => {
          this.loadShifts();
        },
        error: (error) => {
          console.error('Error deleting shift:', error);
          alert('Failed to delete shift. Please try again.');
        }
      });
    }
  }

  /**
   * View shift details
   */
  viewShiftDetails(shift: Shift): void {
    this.latestShift = shift;
    this.selectedShiftId = shift.ShiftId || null;
  }
}
