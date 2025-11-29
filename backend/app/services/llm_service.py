"""
LLM Service - OpenAI Integration for AI-powered insights
Generates: explanations, tips, emotion analysis from shift data
"""

import os
from openai import OpenAI
import json


class LLMService:
    """OpenAI-powered wellness assistant for healthcare workers"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            self.enabled = True
        else:
            self.client = None
            self.model = None
            self.enabled = False
            print("[LLM] Warning: OPENAI_API_KEY not set. LLM features disabled.")
    
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
    # Generate Combined Insights (Explanation + Tips)
    # ============================================
    
    @staticmethod
    def generate_insights(shift_data, index, zone):
        """
        Generate combined AI insights (explanation + tips) for a shift
        Static method for easy use in routes
        
        Args:
            shift_data: dict with keys: hours_slept, shift_type, shift_length, 
                        patients_count, stress_level, shift_note
            index: SafeShift Index (0-100)
            zone: Risk zone (green, yellow, red)
        
        Returns:
            dict: {'explanation': str, 'tips': str}
        """
        llm = LLMService()
        
        if not llm.enabled:
            return {
                'explanation': f"SafeShift Index: {index} ({zone} zone). Please prioritize rest.",
                'tips': "• Rest and recover\n• Stay hydrated\n• Reach out for support"
            }
        
        # Generate both explanation and tips
        explanation = llm._generate_simple_explanation(
            index=index,
            zone=zone,
            hours_slept=shift_data.get('hours_slept', 0),
            shift_type=shift_data.get('shift_type', 'day'),
            shift_length=shift_data.get('shift_length', 8),
            patients_count=shift_data.get('patients_count', 0),
            stress_level=shift_data.get('stress_level', 5),
            shift_note=shift_data.get('shift_note', '')
        )
        
        tips = llm._generate_simple_tips(
            zone=zone,
            hours_slept=shift_data.get('hours_slept', 0),
            shift_type=shift_data.get('shift_type', 'day'),
            shift_length=shift_data.get('shift_length', 8),
            stress_level=shift_data.get('stress_level', 5)
        )
        
        return {
            'explanation': explanation,
            'tips': tips
        }
    
    def _generate_simple_explanation(self, index, zone, hours_slept, shift_type, shift_length, patients_count, stress_level, shift_note=""):
        """Internal method to generate explanation without user info"""
        if not self.enabled:
            return f"SafeShift Index: {index} ({zone} zone). Please prioritize rest."
        
        prompt = f"""Generate a SHORT explanation (2-3 sentences) for why this SafeShift Index is in the {zone.upper()} zone.

SafeShift Index: {index} ({zone.upper()} ZONE)

Shift factors:
- Slept {hours_slept} hours before shift
- {shift_type.capitalize()} shift, {shift_length} hours
- {patients_count} patients
- Stress level: {stress_level}/10
- Note: "{shift_note if shift_note else 'N/A'}"

Explain the key risk factors briefly."""
        
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
            print(f"[LLM] Error in generate explanation: {str(e)}")
            return f"SafeShift Index: {index} ({zone} zone). Key factors: {hours_slept}h sleep, {shift_length}h {shift_type} shift."
    
    def _generate_simple_tips(self, zone, hours_slept, shift_type, shift_length, stress_level):
        """Internal method to generate tips without user info"""
        if not self.enabled:
            return "• Rest and recover\n• Stay hydrated\n• Reach out for support"
        
        prompt = f"""Generate 3-4 SHORT recovery tips (bullet points) for a healthcare worker after this {zone.upper()} zone shift.

Context:
- {shift_length}-hour {shift_type} shift
- Slept {hours_slept} hours before
- Stress level {stress_level}/10

Focus on immediate, practical actions. Each tip: 1 sentence. Make them DOABLE today."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[LLM] Error in generate tips: {str(e)}")
            return "• Rest and recover\n• Stay hydrated\n• Reach out for support"
    
    # ============================================
    # Generate AI Explanation (Original method with user info)
    # ============================================
    
    def generate_explanation(self, first_name, role, index, zone, hours_slept, shift_type, shift_length, patients_count, stress_level, shift_note=""):
        """
        Generate AI explanation for SafeShift Index
        
        Args:
            first_name: User's first name
            role: User's role (nurse, doctor, etc.)
            index: SafeShift Index (0-100)
            zone: Risk zone (green, yellow, red)
            hours_slept: Hours slept before shift
            shift_type: 'day' or 'night'
            shift_length: Shift length in hours
            patients_count: Number of patients
            stress_level: Stress level (1-10)
            shift_note: Optional shift note
        
        Returns:
            str: AI-generated explanation
        """
        
        if not self.enabled:
            return f"Your SafeShift Index is {index} ({zone} zone). Please prioritize rest and recovery."
        
        prompt = f"""Generate a SHORT explanation (2-4 sentences) for why {first_name}'s SafeShift Index is in the {zone.upper()} zone.

SafeShift Index: {index} ({zone.upper()} ZONE)

Factors from this shift:
- Slept {hours_slept} hours before the shift
- {shift_type.capitalize()} shift
- {shift_length}-hour shift
- {patients_count} patients cared for
- Stress level: {stress_level}/10
- Role: {role}
- Note: "{shift_note if shift_note else 'N/A'}"

Task:
1. Explain which factors contributed MOST to the {zone} zone
2. Keep it personal and empathetic (address {first_name} directly)
3. Do NOT use scary language
4. Help them understand what it means for their performance"""
        
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
            print(f"[LLM] Error in generate_explanation: {str(e)}")
            return f"Your SafeShift Index is {index} ({zone} zone). Please prioritize rest and recovery."
    
    # ============================================
    # Generate Recovery Tips
    # ============================================
    
    def generate_tips(self, first_name, role, zone, hours_slept, shift_type, shift_length, patients_count, stress_level, shift_note=""):
        """
        Generate personalized recovery tips
        
        Args:
            first_name: User's first name
            role: User's role
            zone: Risk zone (green, yellow, red)
            hours_slept: Hours slept before shift
            shift_type: 'day' or 'night'
            shift_length: Shift length in hours
            patients_count: Number of patients
            stress_level: Stress level (1-10)
            shift_note: Optional shift note
        
        Returns:
            str: AI-generated recovery tips (bullet points)
        """
        
        if not self.enabled:
            return "• Rest and recover\n• Stay hydrated\n• Reach out for support"
        
        prompt = f"""Generate 3-5 SHORT recovery tips (bullet points) for {first_name} after this {zone.upper()} zone shift.

Context:
- Role: {role}
- Just completed: {shift_length}-hour {shift_type} shift with {patients_count} patients, stress level {stress_level}/10
- Slept {hours_slept} hours before shift
- Note: "{shift_note if shift_note else 'Normal shift'}"

Focus on immediate recovery, sleep, emotional processing, self-care, and support.
Each tip: 1-2 sentences MAX. Make them DOABLE today.
No medical advice or medications."""
        
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
            print(f"[LLM] Error in generate_tips: {str(e)}")
            return "• Rest and recover\n• Stay hydrated\n• Reach out for support"
    
    # ============================================
    # Emotion Analysis
    # ============================================
    
    def analyze_emotion_from_note(self, shift_note):
        """
        Analyze emotional tone from shift note
        
        Args:
            shift_note: Free text note from shift
        
        Returns:
            dict: {
                'dominant_emotion': str,
                'emotional_score': int (-10 to +10),
                'key_phrases': list,
                'ai_insight': str
            }
        """
        
        if not self.enabled or not shift_note or len(shift_note.strip()) < 5:
            return {
                'dominant_emotion': 'neutral',
                'emotional_score': 0,
                'key_phrases': [],
                'ai_insight': 'No note provided.' if not shift_note else 'LLM disabled.'
            }
        
        prompt = f"""Analyze the emotional tone and respond in JSON format.

Shift Note: "{shift_note}"

Respond ONLY with valid JSON:
{{
    "dominant_emotion": "fear, frustration, sadness, exhaustion, satisfaction, hope, or neutral",
    "emotional_score": -10 to +10,
    "key_phrases": ["list", "of", "emotional", "phrases"],
    "ai_insight": "1-2 sentence insight"
}}"""
        
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
            print(f"[LLM] Error in analyze_emotion_from_note: {str(e)}")
            return {
                'dominant_emotion': 'neutral',
                'emotional_score': 0,
                'key_phrases': [],
                'ai_insight': 'Could not analyze emotion.'
            }
    
    # ============================================
    # Generate Anomaly Warning
    # ============================================
    
    def generate_anomaly_warning(self, user_first_name, anomalies):
        """
        Generate AI warning message for detected anomalies
        
        Args:
            user_first_name: User's first name
            anomalies: List of detected anomalies
        
        Returns:
            str: AI-generated warning message or None
        """
        
        if not self.enabled or not anomalies:
            return None
        
        anomaly_summaries = "\n".join([
            f"- {a['type']}: {a['description']}"
            for a in anomalies
        ])
        
        severity_levels = [a['severity'] for a in anomalies]
        max_severity = 'high' if 'high' in severity_levels else 'medium'
        
        prompt = f"""Generate a SHORT, URGENT warning message for {user_first_name} about detected anomalies.

Detected Anomalies:
{anomaly_summaries}

Max Severity: {max_severity}

Task:
1. Be direct and clear
2. DO NOT be scary, but be honest
3. Suggest 2-3 IMMEDIATE actions
4. Keep it SHORT (2-3 sentences max)

Tone: Urgent but supportive."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"[LLM] Error in generate_anomaly_warning: {str(e)}")
            return "⚠️ Multiple concerning patterns detected. Please prioritize rest and recovery."
    
    # ============================================
    # Generate Prediction Message
    # ============================================
    
    def generate_prediction_message(self, user_first_name, prediction_data):
        """
        Generate AI message about burnout prediction
        
        Args:
            user_first_name: User's first name
            prediction_data: Prediction data from PredictionService
        
        Returns:
            str: AI-generated prediction message
        """
        
        if not self.enabled:
            return prediction_data.get('reasoning', 'Prediction unavailable.')
        
        if prediction_data['prediction'] == 'insufficient_data':
            return prediction_data['reasoning']
        
        pred_index = prediction_data['predicted_index']
        pred_level = prediction_data['prediction']
        days_until = prediction_data['days_until_critical']
        confidence = prediction_data['confidence']
        
        prompt = f"""Generate a SHORT prediction warning for {user_first_name} about their burnout risk in the next 14 days.

Prediction Data:
- Predicted SafeShift Index: {pred_index} (out of 100)
- Risk Level: {pred_level}
- Days until critical zone (70+): {days_until if days_until else 'N/A'}
- Confidence: {confidence * 100:.0f}%
- Reasoning: {prediction_data['reasoning']}

Task:
1. Be honest about the prediction
2. Suggest 2-3 PREVENTIVE actions they can take NOW
3. Keep it SHORT (2-3 sentences)
4. NOT scary, but realistic

Tone: Forward-looking and supportive."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"[LLM] Error in generate_prediction_message: {str(e)}")
            return f"Based on current trends, your burnout risk may increase in the next 2 weeks. Consider preventive measures now."
