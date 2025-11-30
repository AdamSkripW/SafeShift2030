import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AlertService, BurnoutAlert, AlertSummary } from '../../services/alert.service';
import { AuthService } from '../../services/auth.service';
import { AlertResolutionModalComponent } from '../alert-resolution-modal/alert-resolution-modal.component';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-alert-banner',
  standalone: true,
  imports: [CommonModule, AlertResolutionModalComponent],
  templateUrl: './alert-banner.component.html',
  styleUrls: ['./alert-banner.component.css']
})
export class AlertBannerComponent implements OnInit, OnDestroy {
  alerts: BurnoutAlert[] = [];
  summary: AlertSummary | null = null;
  isCollapsed = false;
  isModalOpen = false;
  selectedAlert: BurnoutAlert | null = null;
  loading = true;
  private subscriptions: Subscription[] = [];

  constructor(
    private alertService: AlertService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // Subscribe to alerts
    this.subscriptions.push(
      this.alertService.alerts$.subscribe(alerts => {
        console.log('[AlertBanner] Received alerts:', alerts);
        this.alerts = alerts.filter(a => !a.IsResolved);
        console.log('[AlertBanner] Filtered unresolved alerts:', this.alerts);
        this.loading = false;
      })
    );

    // Subscribe to summary
    this.subscriptions.push(
      this.alertService.summary$.subscribe(summary => {
        console.log('[AlertBanner] Received summary:', summary);
        this.summary = summary;
      })
    );

    // Load alerts immediately if user is already authenticated
    const currentUser = this.authService.getCurrentUser();
    console.log('[AlertBanner] Initial current user:', currentUser);
    if (currentUser && currentUser.UserId) {
      console.log('[AlertBanner] Loading alerts immediately for userId:', currentUser.UserId);
      this.alertService.refreshAlerts(currentUser.UserId);
    }

    // Subscribe to current user changes and reload alerts when user changes
    this.subscriptions.push(
      this.authService.currentUser$.subscribe(user => {
        console.log('[AlertBanner] Current user changed:', user);
        if (user && user.UserId) {
          console.log('[AlertBanner] Fetching alerts for userId:', user.UserId);
          this.alertService.refreshAlerts(user.UserId);
        } else {
          console.warn('[AlertBanner] No authenticated user');
          // Clear alerts when no user
          this.alerts = [];
          this.summary = null;
        }
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  toggleCollapse(): void {
    this.isCollapsed = !this.isCollapsed;
  }

  resolveAlert(alertId: number, event: Event): void {
    event.stopPropagation();
    const alert = this.alerts.find(a => a.Id === alertId);
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
        console.log('Alert resolved successfully');
        // Close modal immediately
        this.closeModal();
        // Refresh alerts from current user
        const user = this.authService.getCurrentUser();
        if (user && user.UserId) {
          this.alertService.refreshAlerts(user.UserId);
        }
      },
      error: (error) => {
        console.error('Error resolving alert:', error);
        this.closeModal();
      }
    });
  }

  getSeverityClass(severity: string): string {
    return this.alertService.getSeverityClass(severity);
  }

  getAlertTypeLabel(alertType: string): string {
    return this.alertService.getAlertTypeLabel(alertType);
  }

  getAlertIcon(alertType: string): string {
    return this.alertService.getAlertIcon(alertType);
  }

  getCriticalAndHighAlerts(): BurnoutAlert[] {
    return this.alerts.filter(a => 
      a.Severity.toLowerCase() === 'critical' || a.Severity.toLowerCase() === 'high'
    );
  }

  getBannerClass(): string {
    if (!this.summary) return 'alert-banner-info';
    
    if (this.summary.by_severity.critical > 0) {
      return 'alert-banner-critical';
    } else if (this.summary.by_severity.high > 0) {
      return 'alert-banner-high';
    } else if (this.summary.by_severity.medium > 0) {
      return 'alert-banner-medium';
    }
    return 'alert-banner-info';
  }

  formatDate(dateString: string): string {
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
