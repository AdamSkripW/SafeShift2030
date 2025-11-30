import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { AuthService } from './auth.service';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatResponse {
  success: boolean;
  response: string;
  suggestions?: string[];
  crisis_detected?: boolean;
  requires_escalation?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = `${environment.apiUrl}/chat`;
  private conversationHistory: ChatMessage[] = [];
  private conversationSubject = new BehaviorSubject<ChatMessage[]>([]);
  public conversation$ = this.conversationSubject.asObservable();

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {
    this.initializeConversation();
  }

  private initializeConversation() {
    const currentUser = this.authService.getCurrentUser();
    if (currentUser) {
      this.addWelcomeMessage(currentUser.FirstName);
    }
  }

  sendMessage(message: string): Observable<ChatResponse> {
    const currentUser = this.authService.getCurrentUser();
    
    console.log('[CHAT SERVICE] Sending message:', message);
    console.log('[CHAT SERVICE] API URL:', this.apiUrl);
    console.log('[CHAT SERVICE] User ID:', currentUser?.UserId);
    
    if (!currentUser) {
      throw new Error('User not authenticated');
    }

    // Add user message to history
    const userMessage: ChatMessage = {
      role: 'user',
      content: message
    };
    this.conversationHistory.push(userMessage);

    const payload = {
      message: message,
      userId: currentUser.UserId,
      history: this.conversationHistory
    };

    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    console.log('[CHAT SERVICE] Request payload:', payload);

    return this.http.post<ChatResponse>(this.apiUrl, payload, { headers }).pipe(
      tap(response => {
        console.log('[CHAT SERVICE] Response received:', response);
        
        if (response.success && response.response) {
          // Add bot response to history
          const botMessage: ChatMessage = {
            role: 'assistant',
            content: response.response
          };
          this.conversationHistory.push(botMessage);
          this.conversationSubject.next([...this.conversationHistory]);
        }
      })
    );
  }

  addWelcomeMessage(firstName: string) {
    const welcomeMessage: ChatMessage = {
      role: 'assistant',
      content: `Ahoj ${firstName}! 👋 Som SafeShift AI asistent. Môžem ti pomôcť s:

• Vysvetlením SafeShift indexu
• Recovery radami
• Manažmentom stresu
• Navigáciou v aplikácii

Čím ti môžem pomôcť?`
    };
    
    this.conversationHistory = [welcomeMessage];
    this.conversationSubject.next([...this.conversationHistory]);
  }

  clearHistory() {
    this.conversationHistory = [];
    this.conversationSubject.next([]);
  }

  getConversationHistory(): ChatMessage[] {
    return [...this.conversationHistory];
  }
}
