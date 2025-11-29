import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly STORAGE_KEY = 'theme';
  private darkModeSubject = new BehaviorSubject<boolean>(false);
  public darkMode$ = this.darkModeSubject.asObservable();

  constructor() {
    this.initializeTheme();
  }

  /**
   * Initialize theme from localStorage or system preference
   */
  private initializeTheme(): void {
    const savedTheme = localStorage.getItem(this.STORAGE_KEY);
    
    if (savedTheme) {
      // Use saved preference
      const isDark = savedTheme === 'dark';
      this.setTheme(isDark);
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.setTheme(prefersDark);
    }
  }

  /**
   * Toggle between light and dark mode
   */
  toggleTheme(): void {
    const newTheme = !this.darkModeSubject.value;
    this.setTheme(newTheme);
  }

  /**
   * Set theme explicitly
   */
  setTheme(isDark: boolean): void {
    this.darkModeSubject.next(isDark);
    
    if (isDark) {
      document.documentElement.classList.add('dark-mode');
      localStorage.setItem(this.STORAGE_KEY, 'dark');
    } else {
      document.documentElement.classList.remove('dark-mode');
      localStorage.setItem(this.STORAGE_KEY, 'light');
    }
  }

  /**
   * Get current theme state
   */
  isDarkMode(): boolean {
    return this.darkModeSubject.value;
  }
}
