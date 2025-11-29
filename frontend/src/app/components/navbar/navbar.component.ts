import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { UserProfileService } from '../../services/user-profile.service';
import { ThemeService } from '../../services/theme.service';
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
  isDarkMode = false;

  constructor(
    private userProfileService: UserProfileService,
    private themeService: ThemeService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.userProfile = this.userProfileService.getUserProfile();
    
    // Subscribe to theme changes
    this.themeService.darkMode$.subscribe(isDark => {
      this.isDarkMode = isDark;
    });
  }

  toggleMobileMenu(): void {
    this.mobileMenuOpen = !this.mobileMenuOpen;
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }

  logout(): void {
    if (confirm('Are you sure you want to logout?')) {
      this.userProfileService.clearUserProfile();
      this.router.navigate(['/start']);
    }
  }
}
