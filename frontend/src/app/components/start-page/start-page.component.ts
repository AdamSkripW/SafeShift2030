import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { HospitalService } from '../../services/hospital.service';
import { Hospital } from '../../models/hospital.model';

@Component({
  selector: 'app-start-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './start-page.component.html',
  styleUrls: ['./start-page.component.css']
})
export class StartPageComponent implements OnInit {
  loginForm: FormGroup;
  registerForm: FormGroup;
  loginSubmitted = false;
  registerSubmitted = false;
  hospitals: Hospital[] = [];
  loadingHospitals = true;
  showModal = false;
  modalMode: 'login' | 'register' = 'login';

  roles: Array<{label: string, value: 'nurse' | 'doctor' | 'student'}> = [
    { label: 'Nurse', value: 'nurse' },
    { label: 'Doctor', value: 'doctor' },
    { label: 'Medical Student', value: 'student' }
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
    private authService: AuthService,
    private hospitalService: HospitalService,
    private router: Router
  ) {
    // Login form
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });

    // Register form
    this.registerForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      firstName: ['', [Validators.required, Validators.minLength(2)]],
      lastName: ['', [Validators.required, Validators.minLength(2)]],
      role: ['', Validators.required],
      department: ['', Validators.required],
      hospitalId: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    // Check if user is already authenticated
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/dashboard']);
      return;
    }

    // Load hospitals for registration
    this.loadHospitals();
  }

  /**
   * Load hospitals from API
   */
  loadHospitals(): void {
    this.loadingHospitals = true;
    this.hospitalService.getHospitals().subscribe({
      next: (hospitals) => {
        this.hospitals = hospitals;
        this.loadingHospitals = false;
      },
      error: (error) => {
        console.error('Error loading hospitals:', error);
        this.loadingHospitals = false;
        alert('Failed to load hospitals. Please refresh the page.');
      }
    });
  }

  /**
   * Getters for easy access to form controls in template
   */
  get lf() {
    return this.loginForm.controls;
  }

  get rf() {
    return this.registerForm.controls;
  }

  /**
   * Open modal
   */
  openModal(mode: 'login' | 'register'): void {
    this.modalMode = mode;
    this.showModal = true;
    this.loginSubmitted = false;
    this.registerSubmitted = false;
  }

  /**
   * Close modal
   */
  closeModal(): void {
    this.showModal = false;
    this.loginForm.reset();
    this.registerForm.reset();
    this.loginSubmitted = false;
    this.registerSubmitted = false;
  }

  /**
   * Switch between login and register
   */
  switchMode(mode: 'login' | 'register'): void {
    this.modalMode = mode;
    this.loginSubmitted = false;
    this.registerSubmitted = false;
  }

  /**
   * Handle login form submission
   */
  onLogin(): void {
    this.loginSubmitted = true;

    if (this.loginForm.invalid) {
      return;
    }

    const { email, password } = this.loginForm.value;

    this.authService.login(email, password).subscribe({
      next: (response) => {
        console.log('Login successful:', response);
        this.closeModal();
        this.router.navigate(['/dashboard']);
      },
      error: (error) => {
        console.error('Login error:', error);
        alert(error.error?.error || error.message);
      }
    });
  }

  /**
   * Handle register form submission
   */
  onRegister(): void {
    this.registerSubmitted = true;

    if (this.registerForm.invalid) {
      return;
    }

    // Find selected hospital
    const selectedHospital = this.hospitals.find(
      h => h.HospitalId === Number(this.registerForm.value.hospitalId)
    );

    if (!selectedHospital) {
      alert('Please select a valid hospital');
      return;
    }

    const userData = {
      Email: this.registerForm.value.email.trim(),
      Password: this.registerForm.value.password,
      FirstName: this.registerForm.value.firstName.trim(),
      LastName: this.registerForm.value.lastName.trim(),
      Role: this.registerForm.value.role,
      Department: this.registerForm.value.department,
      Hospital: selectedHospital.Name,
      HospitalId: selectedHospital.HospitalId
    };

    this.authService.register(userData).subscribe({
      next: (response) => {
        console.log('Registration successful:', response);
        this.closeModal();
        this.router.navigate(['/dashboard']);
      },
      error: (error) => {
        console.error('Registration error:', error);
        alert(error.error?.error || 'Failed to register. Please try again.');
      }
    });
  }
}
