"""
Chat Service - AI Assistant for Healthcare Workers
Context-aware chatbot with safety filters and crisis detection
"""

import os
from openai import OpenAI
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import re


class ChatService:
    """
    SafeShift AI Assistant - Wellness chatbot for healthcare workers
    
    Features:
    - Context-aware responses (user profile, shifts, alerts)
    - Safety filters (no medical diagnosis, medications)
    - Crisis detection and escalation
    - Multi-language support (Slovak/English)
    - Conversation history management
    """
    
    # Crisis keywords for escalation
    CRISIS_KEYWORDS_SK = [
        'chcem umrieť', 'chcem zomrieť', 'spáchať samovraždu', 
        'ukončiť svoj život', 'nechcem žiť', 'mám samovražedné myšlienky'
    ]
    
    CRISIS_KEYWORDS_EN = [
        'want to die', 'kill myself', 'suicide', 'end my life',
        'ending it all', 'suicidal thoughts', 'not worth living'
    ]
    
    # Forbidden topics (out of scope)
    FORBIDDEN_TOPICS = [
        'medication dosage', 'prescription', 'medical diagnosis',
        'drug recommendation', 'treatment plan', 'medical procedure',
        'antidepressant', 'antipsychotic', 'benzodiazepine'
    ]
    
    # System prompt for the AI assistant
    SYSTEM_PROMPT = """Si SafeShift AI Assistant - wellness chatbot pre zdravotníckych pracovníkov aplikácie SafeShift2030.

TVOJA ROLA:
- Pomáhať rozumieť SafeShift indexu a burnout riziku
- Odporúčať recovery stratégie a self-care praktiky
- Vysvetľovať AI insights a predikcie
- Poskytovať emotional support v rámci wellness kontextu
- Navigovať používateľov v aplikácii
- Odpovedať v SLOVENČINE alebo ANGLIČTINE podľa užívateľa

ČO MÔŽEŠ ROBIŤ:
✅ Vysvetliť SafeShift Index a zóny (green/yellow/red)
✅ Odporúčať recovery: spánok, prestávky, self-care
✅ Vysvetliť burnout riziko a varovania
✅ Pomôcť s navigáciou v aplikácii
✅ Podporiť emocionálne (v rámci wellness)
✅ Vysvetliť AI agent insights

ČO NIKDY NESMIEŠ ROBIŤ:
❌ Diagnostikovať choroby ("máš depresiu", "máš burnout syndróm")
❌ Predpisovať lieky alebo dávkovanie ("vezmi si Xanax 2mg")
❌ Nahrádzať lekára alebo psychológa
❌ Riešiť závažné mental health problémy
❌ Dávať právne alebo medicínske rady
❌ Strašiť alebo používať alarmistický jazyk

AK NEVIEŠ ALEBO JE TO MIMO ROZSAHU:
"To je mimo mojej kompetencie. Odporúčam kontaktovať [lekára/psychológa/supervízora]."

ŠTÝL ODPOVEDÍ:
- Krátke odpovede (2-4 vety MAX, unless complex explanation needed)
- Empatický, podporný tón
- Bez strašenia, realistický
- Konkrétne, praktické rady
- Používaj emojis opatrne (1-2 max)

FORMÁTOVANIE:
- Používaj bullet points (•) pre zoznamy
- Krátke odseky
- Jasná štruktúra"""

    def __init__(self):
        """Initialize OpenAI client and configuration"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            self.enabled = True
            print(f"[CHAT] ✓ OpenAI initialized with model: {self.model}")
        else:
            self.client = None
            self.model = None
            self.enabled = False
            print("[CHAT] ✗ Warning: OPENAI_API_KEY not set. Chat features disabled.")
    
    def check_safety(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Check if message is safe to process
        
        Args:
            message: User message to check
        
        Returns:
            Tuple[bool, Optional[str]]: (is_safe, error_message)
        """
        message_lower = message.lower()
        
        # Check for crisis keywords
        all_crisis_keywords = self.CRISIS_KEYWORDS_SK + self.CRISIS_KEYWORDS_EN
        if any(keyword in message_lower for keyword in all_crisis_keywords):
            return False, "CRISIS_DETECTED"
        
        # Check for forbidden topics
        if any(topic in message_lower for topic in self.FORBIDDEN_TOPICS):
            return False, "OUT_OF_SCOPE"
        
        # OpenAI Moderation API (optional, adds latency)
        if self.enabled:
            try:
                moderation = self.client.moderations.create(input=message)
                if moderation.results[0].flagged:
                    return False, "CONTENT_VIOLATION"
            except Exception as e:
                print(f"[CHAT] Moderation API error: {e}")
                # Continue anyway if moderation fails
        
        return True, None
    
    def build_context_summary(self, user_context: Dict[str, Any]) -> str:
        """
        Build context summary from user data
        
        Args:
            user_context: Dictionary with user data (name, role, shifts, alerts, etc.)
        
        Returns:
            str: Formatted context summary
        """
        summary = f"""KONTEXT POUŽÍVATEĽA:
Meno: {user_context.get('user_name', 'Neznáme')}
Rola: {user_context.get('role', 'Neznáma')}
Oddelenie: {user_context.get('department', 'Neznáme')}
Nemocnica: {user_context.get('hospital', 'Neznáma')}

AKTUÁLNY STAV:"""
        
        # Current zone and index
        if user_context.get('current_zone') and user_context.get('current_zone') != 'unknown':
            summary += f"\nAktuálna zóna: {user_context['current_zone'].upper()}"
            summary += f"\nSafeShift Index: {user_context.get('safeshift_index', 'N/A')}"
        
        # Latest shift info
        if user_context.get('latest_shift'):
            shift = user_context['latest_shift']
            summary += f"\n\n📅 POSLEDNÁ ZMENA:"
            summary += f"\n- Dátum: {shift.get('date', 'N/A')}"
            summary += f"\n- Spánok: {shift.get('hours_slept', 'N/A')}h"
            summary += f"\n- Typ: {shift.get('shift_type', 'N/A')}"
            summary += f"\n- Dĺžka: {shift.get('shift_length', 'N/A')}h"
            summary += f"\n- Stres: {shift.get('stress_level', 'N/A')}/10"
        
        # Alerts
        unresolved_alerts = user_context.get('unresolved_alerts', 0)
        if unresolved_alerts > 0:
            summary += f"\n\n⚠️ Nevyriešené alerty: {unresolved_alerts}"
        
        # Recent patterns
        if user_context.get('recent_zones'):
            zones = ', '.join(user_context['recent_zones'][:5])
            summary += f"\nNedávne zóny: {zones}"
        
        # Consecutive shifts
        if user_context.get('consecutive_shifts', 0) > 3:
            summary += f"\n🔴 Po sebe: {user_context['consecutive_shifts']} zmien!"
        
        # Agent insights (if available)
        if user_context.get('agent_insights'):
            insights = user_context['agent_insights']
            if insights.get('urgency_level') in ['urgent', 'critical']:
                summary += f"\n⚠️ AI Detection: {insights.get('urgency_level').upper()}"
        
        return summary
    
    def generate_crisis_response(self, user_name: str) -> Dict[str, Any]:
        """
        Generate crisis response with immediate help resources
        
        Args:
            user_name: User's first name
        
        Returns:
            Dict with crisis response and escalation flag
        """
        response = f"""⚠️ {user_name}, vidím že sa cítiš veľmi zle. Tvoje pocity beriem vážne.

PROSÍM kontaktuj OKAMŽITE:

☎️ **Krízová linka dôvery**: 0800 000 000 (24/7, zadarmo)
📞 **Linka dôvery pre zdravotníkov**: 0800 199 199
🏥 **Lekárska pohotovosť**: 155
👨‍⚕️ **Tvoj supervízor/vedúci**

Nie si sám/sama. Profesionálna pomoc je tu pre teba. Tvoj život má hodnotu.

[Tvoj supervízor bol automaticky upozornený]"""
        
        return {
            'response': response,
            'crisis_detected': True,
            'requires_escalation': True,
            'urgent': True
        }
    
    def generate_out_of_scope_response(self) -> str:
        """Generate response for out-of-scope questions"""
        return """To je mimo môjho rozsahu pôsobnosti. Som wellness asistent pre SafeShift aplikáciu.

Môžem ti pomôcť s:
• SafeShift indexom a burnout rizikom
• Recovery radami a self-care
• Navigáciou v aplikácii
• Vysvetlením AI insights

Pre medicínske otázky odporúčam kontaktovať:
👨‍⚕️ Lekára alebo psychológa
🏥 Zdravotnícke zariadenie"""
    
    def generate_response(
        self,
        user_message: str,
        user_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate AI response with context and safety checks
        
        Args:
            user_message: User's message
            user_context: Context dictionary with user data
            conversation_history: Previous messages in conversation
        
        Returns:
            Dict with response, safety flags, and suggestions
        """
        # Safety check
        is_safe, safety_issue = self.check_safety(user_message)
        
        # Handle crisis
        if safety_issue == "CRISIS_DETECTED":
            return self.generate_crisis_response(user_context.get('user_name', 'Používateľ'))
        
        # Handle out of scope
        if safety_issue == "OUT_OF_SCOPE":
            return {
                'response': self.generate_out_of_scope_response(),
                'out_of_scope': True,
                'requires_escalation': False
            }
        
        # Handle content violation
        if safety_issue == "CONTENT_VIOLATION":
            return {
                'response': "Prepáč, ale nemôžem odpovedať na túto správu. Zostávame prosím pri témach týkajúcich sa wellness a SafeShift aplikácie.",
                'content_filtered': True,
                'requires_escalation': False
            }
        
        # If LLM not enabled, return fallback
        if not self.enabled:
            return {
                'response': "Chatbot momentálne nie je dostupný. Skús to prosím neskôr.",
                'error': True,
                'requires_escalation': False
            }
        
        try:
            # Build context summary
            context_summary = self.build_context_summary(user_context)
            
            # Prepare messages
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "system", "content": context_summary}
            ]
            
            # Add conversation history (last 10 messages)
            if conversation_history:
                messages.extend(conversation_history[-10:])
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            print(f"[CHAT] Sending request to OpenAI (model: {self.model})")
            print(f"[CHAT] Message count: {len(messages)}, User message: {user_message[:50]}...")
            
            # Call OpenAI with timeout
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=400,
                temperature=0.7,
                timeout=30  # 30 second timeout
            )
            
            bot_response = response.choices[0].message.content
            print(f"[CHAT] ✓ Response received ({response.usage.total_tokens} tokens)")
            
            # Generate quick suggestions based on context
            suggestions = self._generate_suggestions(user_context, user_message)
            
            return {
                'response': bot_response,
                'suggestions': suggestions,
                'crisis_detected': False,
                'requires_escalation': False,
                'context_used': True,
                'tokens_used': response.usage.total_tokens
            }
        
        except Exception as e:
            print(f"[CHAT] ✗ Error generating response: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return helpful error message
            error_msg = str(e)
            if "model" in error_msg.lower():
                return {
                    'response': f"Prepáč, vyskytol sa problém s AI modelom. Skontroluj prosím nastavenia. (Model: {self.model})",
                    'error': True,
                    'error_message': error_msg,
                    'requires_escalation': False
                }
            
            return {
                'response': "Prepáč, vyskytla sa chyba. Skús to prosím znovu o chvíľu.",
                'error': True,
                'error_message': error_msg,
                'requires_escalation': False
            }
    
    def _generate_suggestions(self, user_context: Dict[str, Any], user_message: str) -> List[str]:
        """
        Generate quick reply suggestions based on context
        
        Args:
            user_context: User context data
            user_message: Current user message
        
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        # If in red zone, suggest recovery
        if user_context.get('current_zone') == 'red':
            suggestions.append("Ako môžem zlepšiť môj index?")
            suggestions.append("Potrebujem tipy na recovery")
        
        # If high stress
        latest_shift = user_context.get('latest_shift', {})
        if latest_shift.get('stress_level', 0) >= 7:
            suggestions.append("Pomôž mi s manažmentom stresu")
        
        # If low sleep
        if latest_shift.get('hours_slept', 8) < 6:
            suggestions.append("Rady pre lepší spánok")
        
        # If unresolved alerts
        if user_context.get('unresolved_alerts', 0) > 0:
            suggestions.append("Čo znamenajú moje alerty?")
        
        # General helpful suggestions
        if not suggestions:
            suggestions = [
                "Vysvetli mi môj SafeShift index",
                "Ako používať aplikáciu?",
                "Potrebujem podporu"
            ]
        
        return suggestions[:3]  # Return max 3 suggestions
    
    def detect_language(self, message: str) -> str:
        """
        Detect if message is in Slovak or English
        
        Args:
            message: User message
        
        Returns:
            'sk' or 'en'
        """
        # Simple heuristic - check for Slovak-specific characters/words
        slovak_indicators = ['ž', 'š', 'č', 'ť', 'ľ', 'ň', 'ý', 'á', 'í', 'é', 'ú', 
                            'ako', 'prečo', 'môj', 'moja', 'som', 'potrebujem']
        
        message_lower = message.lower()
        
        if any(ind in message_lower for ind in slovak_indicators):
            return 'sk'
        
        return 'en'
