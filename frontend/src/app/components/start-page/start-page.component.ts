import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { UserProfileService } from '../../services/user-profile.service';
import { UserProfile } from '../../models/user-profile.model';

@Component({
  selector: 'app-start-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './start-page.component.html',
  styleUrls: ['./start-page.component.css']
})
export class StartPageComponent implements OnInit {
  profileForm: FormGroup;
  submitted = false;

  roles: Array<'Nurse' | 'Doctor' | 'Medical Student'> = [
    'Nurse',
    'Doctor',
    'Medical Student'
  ];

  departments: string[] = [
    'ICU',
    'Internal Medicine',
    'Surgery',
    'Emergency Department',
    'Pediatrics',
    'Cardiology',
    'Oncology',
    'Neurology',
    'Psychiatry',
    'Other'
  ];

  constructor(
    private fb: FormBuilder,
    private userProfileService: UserProfileService,
    private router: Router
  ) {
    this.profileForm = this.fb.group({
      fullName: ['', [Validators.required, Validators.minLength(2)]],
      role: ['', Validators.required],
      department: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    // Pre-fill form if profile already exists
    const existingProfile = this.userProfileService.getUserProfile();
    if (existingProfile) {
      this.profileForm.patchValue(existingProfile);
    }
  }

  /**
   * Getter for easy access to form controls in template
   */
  get f() {
    return this.profileForm.controls;
  }

  /**
   * Handles form submission
   */
  onSubmit(): void {
    this.submitted = true;

    // Stop if form is invalid
    if (this.profileForm.invalid) {
      return;
    }

    try {
      const profile: UserProfile = {
        fullName: this.profileForm.value.fullName.trim(),
        role: this.profileForm.value.role,
        department: this.profileForm.value.department
      };

      // Save to localStorage
      this.userProfileService.saveUserProfile(profile);

      // Navigate to dashboard
      this.router.navigate(['/dashboard']);
    } catch (error) {
      console.error('Error saving profile:', error);
      alert('Failed to save profile. Please try again.');
    }
  }
}
