import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BurnoutAlert } from '../../services/alert.service';

@Component({
  selector: 'app-alert-resolution-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './alert-resolution-modal.component.html',
  styleUrls: ['./alert-resolution-modal.component.css']
})
export class AlertResolutionModalComponent {
  @Input() alert: BurnoutAlert | null = null;
  @Input() isOpen = false;
  @Output() close = new EventEmitter<void>();
  @Output() resolve = new EventEmitter<{ action: string; note: string }>();

  selectedAction: string = 'acknowledged';
  resolutionNote: string = '';

  actionOptions = [
    {
      value: 'acknowledged',
      label: '✓ Acknowledged',
      description: 'I have seen this alert and am aware of the concern'
    },
    {
      value: 'time_off_requested',
      label: '🏖️ Request Time Off',
      description: 'Create a time off request for recovery (3 days recommended)'
    },
    {
      value: 'will_monitor',
      label: '👁️ Will Monitor',
      description: 'I will keep an eye on this and take action if it worsens'
    },
    {
      value: 'action_taken',
      label: '⚡ Action Taken',
      description: 'I have already taken steps to address this concern'
    }
  ];

  closeModal(): void {
    this.close.emit();
    this.resetForm();
  }

  onResolve(): void {
    if (!this.alert) return;
    
    this.resolve.emit({
      action: this.selectedAction,
      note: this.resolutionNote.trim()
    });
    
    this.closeModal();
  }

  resetForm(): void {
    this.selectedAction = 'acknowledged';
    this.resolutionNote = '';
  }

  getActionIcon(action: string): string {
    const icons: Record<string, string> = {
      'acknowledged': '✓',
      'time_off_requested': '🏖️',
      'will_monitor': '👁️',
      'action_taken': '⚡'
    };
    return icons[action] || '✓';
  }
}
