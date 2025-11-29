import { Injectable } from '@angular/core';
import { UserProfile } from '../models/user-profile.model';

@Injectable({
  providedIn: 'root'
})
export class UserProfileService {
  private readonly STORAGE_KEY = 'userProfile';

  constructor() {}

  /**
   * Retrieves the user profile from localStorage
   * @returns UserProfile object or null if not found
   */
  getUserProfile(): UserProfile | null {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      if (data) {
        return JSON.parse(data) as UserProfile;
      }
      return null;
    } catch (error) {
      console.error('Error reading user profile from localStorage:', error);
      return null;
    }
  }

  /**
   * Saves the user profile to localStorage
   * @param profile UserProfile object to save
   */
  saveUserProfile(profile: UserProfile): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(profile));
    } catch (error) {
      console.error('Error saving user profile to localStorage:', error);
      throw error;
    }
  }

  /**
   * Clears the user profile from localStorage
   */
  clearUserProfile(): void {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
    } catch (error) {
      console.error('Error clearing user profile from localStorage:', error);
    }
  }
}
