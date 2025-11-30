import { Component, OnInit, OnDestroy, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { ChatService, ChatMessage } from '../../services/chat.service';
import { AuthService } from '../../services/auth.service';

interface DisplayMessage {
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isTyping?: boolean;
}

@Component({
  selector: 'app-chat-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-modal.component.html',
  styleUrl: './chat-modal.component.css'
})
export class ChatModalComponent implements OnInit, OnDestroy {
  isOpen = false;
  message = '';
  messages: DisplayMessage[] = [];
  suggestions: string[] = [];
  previousSuggestions: string[] = [];
  askedQuestions: string[] = [];
  isLoading = false;
  isCrisis = false;
  
  quickStartQuestions: string[] = [
    '🔍 Čo znamená môj SafeShift Index?',
    '📊 Ako vyplniť formulár po zmene?',
    '💡 Ukáž mi moje recovery tips',
    '⚠️ Prečo mám vysoký burnout risk?',
    '😓 Som vyčerpaný - čo mám robiť?',
    '📈 Ako sa porovnávam s tímom?'
  ];

  constructor(
    private chatService: ChatService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef,
    private ngZone: NgZone
  ) {}

  ngOnInit() {
    const currentUser = this.authService.getCurrentUser();
    if (currentUser) {
      this.chatService.addWelcomeMessage(currentUser.FirstName);
    }
  }

  ngOnDestroy() {
  }

  toggleChat() {
    this.isOpen = !this.isOpen;
  }

  sendMessage() {
    if (!this.message.trim() || this.isLoading) {
      return;
    }

    const currentUser = this.authService.getCurrentUser();
      
    if (!currentUser) {
      console.error('[CHAT MODAL] No authenticated user found!');
      alert('Musíš byť prihlásený aby si mohol používať chat.');
      return;
    }
      
    const userMessage = this.message;
    this.message = '';
    this.isLoading = true;
    this.isCrisis = false;
      
    this.askedQuestions.push(userMessage.toLowerCase().trim());
    this.suggestions = [];
      
    console.log('[CHAT MODAL] Sending message:', userMessage);
    console.log('[CHAT MODAL] Current messages count:', this.messages.length);
    console.log('[CHAT MODAL] User:', currentUser);
      
    this.messages.push({
      text: userMessage,
      sender: 'user',
      timestamp: new Date()
    });
      
    this.messages = [...this.messages];
    this.cdr.markForCheck();
    this.cdr.detectChanges();
      
    setTimeout(() => this.scrollToBottom(), 50);
      
    this.chatService.sendMessage(userMessage).subscribe({
      next: (response) => {
        console.log('[CHAT MODAL] Response received:', response);
        this.isLoading = false;
          
        if (response.success && response.response) {
          this.messages.push({
            text: response.response,
            sender: 'bot',
            timestamp: new Date()
          });
            
          this.messages = [...this.messages];
          this.cdr.markForCheck();
          this.cdr.detectChanges();
            
          setTimeout(() => this.scrollToBottom(), 50);
        }
          
        setTimeout(() => {
          if (response.suggestions && response.suggestions.length > 0) {
            let filteredSuggestions = response.suggestions.filter(s => 
              !this.askedQuestions.some(q => 
                this.isSimilarQuestion(q, s.toLowerCase())
              )
            );
              
            const suggestionsChanged = JSON.stringify(filteredSuggestions) !== JSON.stringify(this.previousSuggestions);
              
            if (filteredSuggestions.length >= 2 && suggestionsChanged) {
              this.suggestions = [...filteredSuggestions];
              this.previousSuggestions = [...filteredSuggestions];
              console.log('[CHAT MODAL] New suggestions from backend:', this.suggestions);
            } else {
              this.suggestions = this.generateSmartSuggestions();
              this.previousSuggestions = [...this.suggestions];
              console.log('[CHAT MODAL] Generated smart random suggestions:', this.suggestions);
            }
              
            this.cdr.markForCheck();
            this.cdr.detectChanges();
          } else {
            this.suggestions = [];
            this.previousSuggestions = [];
            console.log('[CHAT MODAL] No suggestions provided, clearing');
          }
        }, 100);
          
        if (response.crisis_detected || response.requires_escalation) {
          this.isCrisis = true;
          console.warn('[CHAT] Crisis detected - escalation required');
        }
          
        console.log('[CHAT MODAL] Messages after response:', this.messages.length);
      },
      error: (error) => {
        this.isLoading = false;
        console.error('[CHAT MODAL] Error sending message:', error);
          
        this.messages.push({
          text: 'Prepáč, vyskytla sa chyba. Skús to prosím znovu.',
          sender: 'bot',
          timestamp: new Date()
        });
      }
    });
  }

  sendSuggestion(suggestion: string) {
    this.message = suggestion;
    this.sendMessage();
    this.suggestions = [];
  }

  closeChat() {
    this.isOpen = false;
  }

  clearHistory() {
    if (confirm('Naozaj chceš vymazať históriu konverzácie?')) {
      this.chatService.clearHistory();
      this.messages = [];
      this.suggestions = [];
      this.askedQuestions = [];
      this.previousSuggestions = [];
      
      const currentUser = this.authService.getCurrentUser();
      if (currentUser) {
        this.chatService.addWelcomeMessage(currentUser.FirstName);
      }
    }
  }

  private isSimilarQuestion(asked: string, suggestion: string): boolean {
    const normalize = (str: string) => str
      .toLowerCase()
      .replace(/[?!.,:;]/g, '')
      .trim();
    
    const askedNorm = normalize(asked);
    const suggNorm = normalize(suggestion);
    
    const askedWords = askedNorm.split(' ').filter(w => w.length > 2);
    const suggWords = suggNorm.split(' ').filter(w => w.length > 2);
    
    if (askedWords.length === 0 || suggWords.length === 0) return false;
    
    const matches = askedWords.filter(w => suggWords.includes(w)).length;
    const similarity = matches / Math.max(askedWords.length, suggWords.length);
    
    return similarity > 0.6;
  }

  private generateSmartSuggestions(): string[] {
    const allSuggestions = [
      "Ako vyplniť formulár po zmene?",
      "Čo znamená môj SafeShift Index?",
      "Vysvetli mi emotion analysis",
      "Prečo mám high burnout prediction?",
      "Ukáž mi recovery tips",
      "Ako sa porovnávam s kolegami?",
      "Čo robiť pri red zone?",
      "Ako zlepšiť môj wellness skóre?",
      "Čo vidí správca v dashboarde?",
      "Ako funguje AI analýza?",
      "Prečo je dôležitý spánok?",
      "Ako znížiť úroveň stresu?",
      "Čo sú to AI insights?",
      "Kedy idem do červenej zóny?"
    ];
    
    const available = allSuggestions.filter(s => 
      !this.askedQuestions.some(q => this.isSimilarQuestion(q, s.toLowerCase())) &&
      !this.previousSuggestions.includes(s)
    );
    
    const finalPool = available.length >= 3 ? available : 
      allSuggestions.filter(s => 
        !this.askedQuestions.some(q => this.isSimilarQuestion(q, s.toLowerCase()))
      );
    
    return finalPool
      .sort(() => Math.random() - 0.5)
      .slice(0, 3);
  }

  private scrollToBottom(): void {
    try {
      const chatBody = document.querySelector('.chat-body');
      if (chatBody) {
        chatBody.scrollTop = chatBody.scrollHeight;
      }
    } catch (err) {
      console.error('Scroll error:', err);
    }
  }
}
