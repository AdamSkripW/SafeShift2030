"""
LLM Service - OpenAI Integration
Generate AI explanations, tips, anomaly warnings, predictions, and emotion analysis
"""

import os
from openai import OpenAI
import json

class LLMService:
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    SYSTEM_MESSAGE = """You are a supportive and empathetic wellness assistant for healthcare workers.
Your role is to help them understand their burnout risk based on their shift data.

TONE: Supportive, empathetic, non-judgmental, focused on well-being and patient safety.

CONSTRAINTS:
- NO medical diagnosis (do not say "you have depression", "you have burnout disorder", etc.)
- NO medication suggestions or dosages
- NO "you must take sick leave" statements
- NO scary or alarming language
- DO focus on practical self-care and rest
- Keep responses SHORT and CONCISE
- Use simple language anyone can understand after a 12-hour shift"""
    
    # ============================================
    # Prompt 1: AI Explanation (why this zone?)
    # ============================================
    def generate_explanation(self, first_name, role, index, zone, hours_slept, shift_type, shift_length, patients_count, stress_level, shift_note=""):
        """Generate AI explanation for SafeShift Index"""
        
        prompt = f"""Generate a SHORT explanation (2-4 sentences) for why {first_name}'s SafeShift Index is in the {zone.upper()} zone.

SafeShift Index: {index} ({zone.upper()} ZONE)

Factors from this shift:
- Slept {hours_slept} hours before the shift (very low if < 4)
- {shift_type.capitalize()} shift
- {shift_length}-hour shift
- {patients_count} patients cared for
- Stress level: {stress_level}/10
- Role: {role}
- Shift note: "{shift_note if shift_note else 'N/A'}"

Task:
1. Explain which factors contributed MOST to the {zone} zone
2. Keep it personal and empathetic (address {first_name} directly)
3. Do NOT use scary language
4. Help them understand what it means for their performance

Example tone:
"{first_name}, your SafeShift Index is in the {zone} zone because..."
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"LLM Error in generate_explanation: {str(e)}")
            return f"Your SafeShift Index is {index} ({zone} zone). Please prioritize rest and recovery."
    
    # ============================================
    # Prompt 2: AI Tips (what to do?)
    # ============================================
    def generate_tips(self, first_name, role, zone, hours_slept, shift_type, shift_length, patients_count, stress_level, shift_note=""):
        """Generate personalized recovery tips"""
        
        prompt = f"""Generate 3-5 SHORT recovery tips (bullet points) for {first_name} after this {zone.upper()} zone shift.

Context:
- Role: {role}
- Just completed: {shift_length}-hour {shift_type} shift with {patients_count} patients, stress level {stress_level}/10
- Slept {hours_slept} hours before shift
- Shift note: "{shift_note if shift_note else 'Normal shift'}"

Focus on:
1. Immediate recovery (today/tonight)
2. Sleep prioritization
3. Emotional processing (if they experienced difficult moments)
4. Simple self-care
5. Support/communication

Constraints:
- Each tip should be 1-2 sentences MAX
- Make them DOABLE today (not "exercise for 2 hours")
- NO medical advice
- NO medications

Format as bullet points starting with action verbs.
Example:
• **Prioritize sleep TODAY** – aim for at least 7 hours...
• **Process the difficult moments** – talk to a colleague...
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"LLM Error in generate_tips: {str(e)}")
            return "• Rest and recover\n• Stay hydrated\n• Reach out for support"
    
    # ============================================
    # Prompt 3: Weekly Summary
    # ============================================
    def generate_weekly_summary(self, first_name, shifts_data):
        """Generate weekly summary with patterns and suggestions"""
        
        shifts_summary = "\n".join([
            f"- {s['date']}: {s['shift_type']}, {s['hours_slept']}h sleep, index {s['index']} ({s['zone']})"
            for s in shifts_data
        ])
        
        red_count = sum(1 for s in shifts_data if s['zone'] == 'red')
        avg_index = sum(s['index'] for s in shifts_data) / len(shifts_data) if shifts_data else 0
        
        prompt = f"""Analyze the last 7 shifts and generate a SHORT weekly summary with patterns and suggestions.

Shifts summary:
{shifts_summary}

Statistics:
- Total shifts: {len(shifts_data)}
- Red zone: {red_count}
- Average index: {avg_index:.0f}

Pattern analysis:
1. Identify the main burnout risk factors
2. Write a SHORT summary (4-6 sentences) in a supportive tone
3. Suggest 2-3 concrete changes for NEXT week

Do NOT provide medical advice or diagnosis.
Keep it encouraging and actionable.

Format your response as JSON:
{{
    "summary": "...",
    "suggestions": ["suggestion1", "suggestion2", "suggestion3"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "summary": content,
                    "suggestions": ["Rest well", "Maintain healthy sleep", "Support colleagues"]
                }
        
        except Exception as e:
            print(f"LLM Error in generate_weekly_summary: {str(e)}")
            return {
                "summary": "This week was busy. Remember to prioritize your health and well-being.",
                "suggestions": ["Rest well", "Stay hydrated", "Reach out for support"]
            }
    
    # ============================================
    # NEW: Emotion Analysis from Shift Note
    # ============================================
    def analyze_emotion_from_note(self, shift_note):
        """
        Analyze emotional tone from shift note
        
        Args:
            shift_note: Free text note from shift
        
        Returns:
            {
                'dominant_emotion': str,
                'emotional_score': int (-10 to +10),
                'key_phrases': list,
                'ai_insight': str
            }
        """
        
        if not shift_note or len(shift_note.strip()) < 5:
            return {
                'dominant_emotion': 'neutral',
                'emotional_score': 0,
                'key_phrases': [],
                'ai_insight': 'No note provided.'
            }
        
        prompt = f"""Analyze the emotional tone of this shift note and respond in JSON format.

Shift Note: "{shift_note}"

Respond ONLY with valid JSON (no other text):
{{
    "dominant_emotion": "one of: fear, frustration, sadness, exhaustion, satisfaction, hope, neutral",
    "emotional_score": -10 to +10 where -10 is very negative and +10 is very positive,
    "key_phrases": ["list", "of", "emotional", "phrases"],
    "ai_insight": "1-2 sentence insight about recovery needs based on this emotion"
}}

Be concise. Focus on real emotions detected."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                return {
                    'dominant_emotion': 'unknown',
                    'emotional_score': 0,
                    'key_phrases': [],
                    'ai_insight': content
                }
        
        except Exception as e:
            print(f"LLM Error in analyze_emotion_from_note: {str(e)}")
            return {
                'dominant_emotion': 'neutral',
                'emotional_score': 0,
                'key_phrases': [],
                'ai_insight': 'Could not analyze emotion.'
            }
