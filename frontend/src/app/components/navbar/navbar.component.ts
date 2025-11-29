import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { UserProfileService } from '../../services/user-profile.service';
import { UserProfile } from '../../models/user-profile.model';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.css']
})
export class NavbarComponent implements OnInit {
  userProfile: UserProfile | null = null;
  mobileMenuOpen = false;

  constructor(
    private userProfileService: UserProfileService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.userProfile = this.userProfileService.getUserProfile();
  }

  toggleMobileMenu(): void {
    this.mobileMenuOpen = !this.mobileMenuOpen;
  }

  logout(): void {
    if (confirm('Are you sure you want to logout?')) {
      this.userProfileService.clearUserProfile();
      this.router.navigate(['/start']);
    }
  }
}
