"""
LLM Service - OpenAI Integration
Generate AI explanations and tips using GPT
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
    
    def generate_explanation(self, first_name, role, index, zone, hours_slept, shift_type, shift_length, patients_count, stress_level, shift_note=""):
        """Generate AI explanation for SafeShift Index"""
        
        prompt = f"""Generate a SHORT explanation (2-4 sentences) for why {first_name}'s SafeShift Index is in the {zone.upper()} zone.

SafeShift Index: {index} ({zone.upper()} ZONE)

Factors:
- Slept {hours_slept} hours before the shift
- {shift_type.capitalize()} shift, {shift_length} hours
- {patients_count} patients
- Stress level: {stress_level}/10
- Role: {role}
- Note: "{shift_note if shift_note else 'N/A'}"

Keep it SHORT, empathetic, and address {first_name} directly."""
        
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
            print(f"LLM Error: {str(e)}")
            return f"Your SafeShift Index is {index} ({zone} zone). Please prioritize rest and recovery."
    
    def generate_tips(self, first_name, role, zone, hours_slept, shift_type, shift_length, patients_count, stress_level, shift_note=""):
        """Generate personalized recovery tips"""
        
        prompt = f"""Generate 3-5 SHORT recovery tips (bullet points) for {first_name} after this {zone.upper()} zone shift.

Context:
- Role: {role}
- {shift_length}-hour {shift_type} shift with {patients_count} patients, stress {stress_level}/10
- Slept {hours_slept} hours before shift
- Note: "{shift_note if shift_note else 'Normal shift'}"

Each tip: 1-2 sentences MAX. No medical advice. Format as bullet points."""
        
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
            print(f"LLM Error: {str(e)}")
            return "• Rest and recover\n• Stay hydrated\n• Reach out for support"
    
    def generate_weekly_summary(self, first_name, shifts_data):
        """Generate weekly summary"""
        
        shifts_summary = "\n".join([
            f"- {s['date']}: {s['shift_type']}, {s['hours_slept']}h sleep, index {s['index']} ({s['zone']})"
            for s in shifts_data
        ])
        
        red_count = sum(1 for s in shifts_data if s['zone'] == 'red')
        avg_index = sum(s['index'] for s in shifts_data) / len(shifts_data) if shifts_data else 0
        
        prompt = f"""Analyze the last 7 shifts and generate a SHORT summary with suggestions.

Shifts:
{shifts_summary}

Stats: {len(shifts_data)} shifts, avg index {avg_index:.0f}, {red_count} red zone

Generate JSON:
{{
    "summary": "4-6 sentence summary...",
    "suggestions": ["suggestion1", "suggestion2", "suggestion3"]
}}"""
        
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
            print(f"LLM Error: {str(e)}")
            return {
                "summary": "This week was busy. Prioritize health and well-being.",
                "suggestions": ["Rest", "Stay hydrated", "Reach out for support"]
            }
