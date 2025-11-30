import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { NavbarComponent } from '../navbar/navbar.component';
import { UserService } from '../../services/user.service';
import { ShiftService } from '../../services/shift.service';
import { AuthService } from '../../services/auth.service';
import { AlertService, BurnoutAlert, AlertSummary } from '../../services/alert.service';
import { AlertResolutionModalComponent } from '../alert-resolution-modal/alert-resolution-modal.component';
import { User } from '../../models/user.model';
import { Shift, Zone } from '../../models/shift.model';

@Component({
  selector: 'app-employees',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent, AlertResolutionModalComponent],
  templateUrl: './employees.component.html',
  styleUrls: ['./employees.component.css']
})
export class EmployeesComponent implements OnInit {
  employees: User[] = [];
  selectedEmployee: User | null = null;
  employeeShifts: Shift[] = [];
  employeeAlerts: BurnoutAlert[] = [];
  alertSummary: AlertSummary | null = null;
  loading = true;
  loadingShifts = false;
  loadingAlerts = false;
  errorMessage = '';
  currentUser: User | null = null;
  latestShift: Shift | null = null;
  selectedShiftId: number | null = null;
  isModalOpen = false;
  selectedAlert: BurnoutAlert | null = null;

  constructor(
    private userService: UserService,
    private shiftService: ShiftService,
    private authService: AuthService,
    private alertService: AlertService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    // Check if current user is a manager
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
      if (!user || user.Department !== 'Management') {
        // Redirect non-managers
        this.router.navigate(['/dashboard']);
        return;
      }
      this.loadEmployees();
    });
  }

  /**
   * Load all employees
   */
  loadEmployees(): void {
    this.loading = true;
    this.errorMessage = '';

    this.userService.getEmployeesByHospital(this.currentUser?.HospitalId).subscribe({
      next: (employees) => {
        this.employees = employees.sort((a, b) => {
          const nameA = `${a.LastName} ${a.FirstName}`.toLowerCase();
          const nameB = `${b.LastName} ${b.FirstName}`.toLowerCase();
          return nameA.localeCompare(nameB);
        });
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error loading employees:', error);
        this.errorMessage = error.error?.message || 'Failed to load employees. Please try again.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  /**
   * Select an employee and load their shifts
   */
  selectEmployee(employee: User): void {
    this.selectedEmployee = employee;
    this.loadEmployeeShifts(employee.UserId!);
    this.loadEmployeeAlerts(employee.UserId!);
  }

  /**
   * Load shifts for selected employee
   */
  loadEmployeeShifts(userId: number): void {
    this.loadingShifts = true;
    this.employeeShifts = [];
    this.latestShift = null;

    this.shiftService.getShiftsByUserId(userId).subscribe({
      next: (shifts) => {
        this.employeeShifts = shifts.sort((a, b) => {
          return new Date(b.ShiftDate).getTime() - new Date(a.ShiftDate).getTime();
        });
        
        this.latestShift = this.employeeShifts.length > 0 ? this.employeeShifts[0] : null;
        this.selectedShiftId = this.latestShift?.ShiftId || null;
        this.loadingShifts = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error loading employee shifts:', error);
        this.loadingShifts = false;
        this.cdr.detectChanges();
      }
    });
  }

  /**
   * View shift details
   */
  viewShiftDetails(shift: Shift): void {
    this.latestShift = shift;
    this.selectedShiftId = shift.ShiftId || null;
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
   * Get department icon
   */
  getDepartmentIcon(department: string): string {
    const icons: { [key: string]: string } = {
      'Emergency': '🚑',
      'ICU': '🏥',
      'Surgery': '⚕️',
      'Pediatrics': '👶',
      'Cardiology': '❤️',
      'Neurology': '🧠',
      'Oncology': '🎗️',
      'Radiology': '📡',
      'Laboratory': '🔬',
      'Pharmacy': '💊'
    };
    return icons[department] || '🏥';
  }

  /**
   * Get role badge class
   */
  getRoleBadgeClass(role: string): string {
    const classes: { [key: string]: string } = {
      'nurse': 'role-nurse',
      'doctor': 'role-doctor',
      'student': 'role-student'
    };
    return classes[role] || 'role-default';
  }

  /**
   * Calculate average SafeShift Index for employee
   */
  getAverageSafeShiftIndex(): number {
    if (this.employeeShifts.length === 0) return 0;
    const sum = this.employeeShifts.reduce((acc, shift) => acc + (shift.SafeShiftIndex || 0), 0);
    return Math.round(sum / this.employeeShifts.length);
  }

  /**
   * Get zone distribution for employee
   */
  getZoneDistribution(): { green: number; yellow: number; red: number } {
    const distribution = { green: 0, yellow: 0, red: 0 };
    this.employeeShifts.forEach(shift => {
      if (shift.Zone === 'green') distribution.green++;
      else if (shift.Zone === 'yellow') distribution.yellow++;
      else if (shift.Zone === 'red') distribution.red++;
    });
    return distribution;
  }

  /**
   * Get zone percentage for zone
   */
  getZonePercentage(zone: 'green' | 'yellow' | 'red'): number {
    if (this.employeeShifts.length === 0) return 0;
    const distribution = this.getZoneDistribution();
    return Math.round((distribution[zone] / this.employeeShifts.length) * 100);
  }

  /**
   * Load alerts for selected employee
   */
  loadEmployeeAlerts(userId: number): void {
    this.loadingAlerts = true;
    this.employeeAlerts = [];
    this.alertSummary = null;

    this.alertService.getAlerts(userId).subscribe({
      next: (response) => {
        if (response.success) {
          this.employeeAlerts = response.alerts.filter(a => !a.IsResolved);
          this.alertSummary = response.summary;
        }
        this.loadingAlerts = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error loading employee alerts:', error);
        this.loadingAlerts = false;
        this.cdr.detectChanges();
      }
    });
  }

  /**
   * Resolve an alert
   */
  resolveEmployeeAlert(alertId: number): void {
    const alert = this.employeeAlerts.find(a => a.Id === alertId);
    if (alert) {
      this.selectedAlert = alert;
      this.isModalOpen = true;
    }
  }

  closeModal(): void {
    this.isModalOpen = false;
    this.selectedAlert = null;
  }

  onResolveAlert(data: { action: string; note: string }): void {
    if (!this.selectedAlert) return;

    this.alertService.resolveAlert(this.selectedAlert.Id, data.action, data.note).subscribe({
      next: () => {
        // Close modal immediately
        this.closeModal();
        // Refresh alerts after resolving
        if (this.selectedEmployee?.UserId) {
          this.loadEmployeeAlerts(this.selectedEmployee.UserId);
        }
      },
      error: (error) => {
        console.error('Error resolving alert:', error);
        this.closeModal();
      }
    });
  }

  /**
   * Get alert severity class
   */
  getSeverityClass(severity: string): string {
    return this.alertService.getSeverityClass(severity);
  }

  /**
   * Get alert type label
   */
  getAlertTypeLabel(alertType: string): string {
    return this.alertService.getAlertTypeLabel(alertType);
  }

  /**
   * Get alert icon
   */
  getAlertIcon(alertType: string): string {
    return this.alertService.getAlertIcon(alertType);
  }

  /**
   * Format alert date
   */
  formatAlertDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  }
}
