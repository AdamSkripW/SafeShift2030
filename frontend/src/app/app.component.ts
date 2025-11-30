import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ChatModalComponent } from './components/chat-modal/chat-modal.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ChatModalComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'SafeShift2030';
}
