import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { NavbarComponent } from '../../components/navbar/navbar.component';
import { ShiftService } from '../../services/shift.service';
import { ShiftFormData, ShiftType } from '../../models/shift.model';

@Component({
  selector: 'app-new-shift',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, NavbarComponent],
  templateUrl: './new-shift.component.html',
  styleUrls: ['./new-shift.component.css']
})
export class NewShiftComponent implements OnInit {
  shiftForm: FormGroup;
  submitted = false;
  loading = false;
  errorMessage = '';

  shiftTypes: ShiftType[] = ['day', 'night'];
  stressLevels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  constructor(
    private fb: FormBuilder,
    private shiftService: ShiftService,
    private router: Router
  ) {
    this.shiftForm = this.fb.group({
      shiftDate: [this.getTodayDate(), Validators.required],
      hoursSleptBefore: [7, [Validators.required, Validators.min(0), Validators.max(24)]],
      shiftType: ['day', Validators.required],
      shiftLengthHours: [8, [Validators.required, Validators.min(1), Validators.max(24)]],
      patientsCount: [0, [Validators.required, Validators.min(0)]],
      stressLevel: [5, [Validators.required, Validators.min(1), Validators.max(10)]],
      shiftNote: ['']
    });
  }

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
  }

  /**
   * Get today's date in YYYY-MM-DD format
   */
  private getTodayDate(): string {
    const today = new Date();
    return today.toISOString().split('T')[0];
  }

  /**
   * Getter for easy access to form controls
   */
  get f() {
    return this.shiftForm.controls;
  }

  /**
   * Handle form submission
   */
  onSubmit(): void {
    this.submitted = true;
    this.errorMessage = '';

    if (this.shiftForm.invalid) {
      return;
    }

    this.loading = true;

    const shiftData: ShiftFormData = {
      ShiftDate: this.shiftForm.value.shiftDate,
      HoursSleptBefore: Number(this.shiftForm.value.hoursSleptBefore),
      ShiftType: this.shiftForm.value.shiftType,
      ShiftLengthHours: Number(this.shiftForm.value.shiftLengthHours),
      PatientsCount: Number(this.shiftForm.value.patientsCount),
      StressLevel: Number(this.shiftForm.value.stressLevel),
      ShiftNote: this.shiftForm.value.shiftNote?.trim() || undefined
    };

    this.shiftService.createShift(shiftData).subscribe({
      next: (shift) => {
        console.log('Shift created successfully:', shift);
        // Navigate to shift detail or dashboard
        this.router.navigate(['/shifts']);
      },
      error: (error) => {
        console.error('Error creating shift:', error);
        this.errorMessage = error.error?.message || 'Failed to create shift. Please try again.';
        this.loading = false;
      },
      complete: () => {
        this.loading = false;
      }
    });
  }

  /**
   * Cancel and go back
   */
  onCancel(): void {
    this.router.navigate(['/shifts']);
  }
}
