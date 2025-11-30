import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-chat-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-modal.component.html',
  styleUrl: './chat-modal.component.css'
})
export class ChatModalComponent {
  isOpen = false;
  message = '';
  messages: { text: string; sender: 'user' | 'bot'; timestamp: Date }[] = [];

  toggleChat() {
    this.isOpen = !this.isOpen;
  }

  sendMessage() {
    if (this.message.trim()) {
      this.messages.push({
        text: this.message,
        sender: 'user',
        timestamp: new Date()
      });
      
      // Placeholder for backend integration
      // TODO: Send message to backend and receive response
      
      this.message = '';
    }
  }

  closeChat() {
    this.isOpen = false;
  }
}
