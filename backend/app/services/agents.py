"""
AI Agent Wrapper Classes
Handles OpenAI API calls for specialized healthcare AI agents
"""

import os
import yaml
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from openai import OpenAI

from app.models import db, AgentMetric


class BaseAgent:
    """Base class for all AI agents with monitoring and error handling"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Agent config not found: {config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY not set in environment")
        
        self.client = OpenAI(api_key=api_key)
        
        # Handle both flat and nested config structures
        self.agent_name = self.config.get('agent_name', self.config.get('name', 'UnknownAgent'))
        
        # Model config can be nested or flat
        model_config = self.config.get('model', {})
        if isinstance(model_config, dict):
            self.model = model_config.get('name', 'gpt-4o-mini')
            self.temperature = model_config.get('temperature', 0.3)
            self.max_tokens = model_config.get('max_tokens', 1000)
            self.response_format = model_config.get('response_format')
        else:
            # Fallback for old flat structure
            self.model = self.config.get('model', 'gpt-4o-mini')
            self.temperature = self.config.get('temperature', 0.3)
            self.max_tokens = 1000
            self.response_format = self.config.get('response_format')
    
    def _log_metrics(self, user_id: Optional[int], shift_id: Optional[int],
                     request_data: Dict, response_data: Dict, 
                     latency_ms: int, token_usage: Optional[Dict],
                     success: bool, error: Optional[str] = None):
        """Log agent execution metrics to database"""
        try:
            metric = AgentMetric(
                AgentName=self.agent_name,
                ModelVersion=self.model,
                UserId=user_id,
                ShiftId=shift_id,
                InputTokens=token_usage.get('prompt_tokens') if token_usage else None,
                OutputTokens=token_usage.get('completion_tokens') if token_usage else None,
                LatencyMs=latency_ms,
                Severity=response_data.get('severity'),
                ConfidenceScore=response_data.get('confidence_score'),
                CrisisDetected=response_data.get('crisis_detected', False),
                EscalationNeeded=response_data.get('escalation_needed', False),
                Success=success,
                ErrorMessage=error,
                FallbackUsed=response_data.get('_fallback', False),
                RequestPayload=request_data,
                ResponsePayload=response_data if success else None
            )
            db.session.add(metric)
            db.session.commit()
        except Exception as e:
            print(f"[ERROR] Failed to log agent metrics: {e}")
            db.session.rollback()
    
    def _call_openai(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """Make OpenAI API call with error handling"""
        start_time = time.time()
        
        try:
            kwargs = {
                "model": self.model,
                "temperature": self.temperature,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": self.max_tokens
            }
            
            if self.response_format:
                kwargs["response_format"] = {"type": self.response_format}
            
            response = self.client.chat.completions.create(**kwargs)
            
            latency_ms = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content
            
            # Parse JSON if expected
            if self.response_format == 'json_object':
                result = json.loads(content)
            else:
                result = {"response": content}
            
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if hasattr(response, 'usage') else None
            
            return {
                "success": True,
                "data": result,
                "latency_ms": latency_ms,
                "token_usage": token_usage,
                "error": None
            }
            
        except json.JSONDecodeError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "data": None,
                "latency_ms": latency_ms,
                "token_usage": None,
                "error": f"Invalid JSON response: {str(e)}"
            }
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "data": None,
                "latency_ms": latency_ms,
                "token_usage": None,
                "error": str(e)
            }


class CrisisDetectionAgent(BaseAgent):
    """AI agent for detecting acute emotional distress in healthcare workers"""
    
    def __init__(self):
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'agents', 'crisis_detection.yaml'
        )
        super().__init__(config_path)
    
    def detect(self, shift_note: str, user_id: int = None, shift_id: int = None,
               user_name: str = None, recent_shifts: List[str] = None, 
               stress_history: List[int] = None, previous_alerts: int = 0) -> Dict[str, Any]:
        """
        Analyze shift note for crisis indicators
        
        Args:
            shift_note: Text to analyze (required)
            user_id: User ID for metrics logging
            shift_id: Shift ID for metrics logging
            user_name: Personalize response (optional)
            recent_shifts: Last 3 shift zones ["red", "yellow", "green"]
            stress_history: Last 5 stress levels [8, 9, 7, ...]
            previous_alerts: Count of unresolved alerts in last 30 days
        
        Returns:
            {
                "crisis_detected": bool,
                "severity": "none"|"low"|"medium"|"high"|"critical",
                "confidence_score": float,
                "indicators": [str],
                "emotional_state": str,
                "recommended_action": str,
                "show_resources": bool,
                "escalation_needed": bool,
                "context_factors": [str],
                "personalized_note": str,
                "resources": {...} (if show_resources=True)
            }
        """
        if not shift_note or not shift_note.strip():
            return self._safe_fallback("Empty shift note", user_id, shift_id)
        
        # Build context message
        request_data = {
            "shift_note": shift_note,
            "user_name": user_name,
            "recent_shifts": recent_shifts,
            "stress_history": stress_history,
            "previous_alerts": previous_alerts
        }
        
        user_message = self._build_context_message(
            shift_note, user_name, recent_shifts, stress_history, previous_alerts
        )
        
        # Call OpenAI
        api_result = self._call_openai(self.config['system'], user_message)
        
        if not api_result['success']:
            return self._safe_fallback(
                api_result['error'], user_id, shift_id, 
                request_data, api_result['latency_ms']
            )
        
        result = api_result['data']
        
        # Validate required keys
        required_keys = self.config.get('required_keys', [])
        missing_keys = [k for k in required_keys if k not in result]
        if missing_keys:
            return self._safe_fallback(
                f"Missing keys: {missing_keys}", user_id, shift_id,
                request_data, api_result['latency_ms']
            )
        
        # Attach crisis resources if needed
        if result.get('show_resources'):
            result['resources'] = self.config.get('resources', {})
        
        # Log metrics
        self._log_metrics(
            user_id=user_id,
            shift_id=shift_id,
            request_data=request_data,
            response_data=result,
            latency_ms=api_result['latency_ms'],
            token_usage=api_result['token_usage'],
            success=True,
            error=None
        )
        
        return result
    
    def _build_context_message(self, shift_note: str, user_name: Optional[str],
                                recent_shifts: Optional[List[str]], 
                                stress_history: Optional[List[int]], 
                                previous_alerts: int) -> str:
        """Format inputs as structured message for agent"""
        parts = [f"shift_note: {shift_note}"]
        
        if user_name:
            parts.append(f"user_name: {user_name}")
        if recent_shifts:
            parts.append(f"recent_shifts: {json.dumps(recent_shifts)}")
        if stress_history:
            parts.append(f"stress_history: {json.dumps(stress_history)}")
        if previous_alerts:
            parts.append(f"previous_alerts: {previous_alerts}")
        
        return "\n".join(parts)
    
    def _safe_fallback(self, error_msg: str, user_id: Optional[int] = None,
                       shift_id: Optional[int] = None, 
                       request_data: Optional[Dict] = None,
                       latency_ms: int = 0) -> Dict[str, Any]:
        """Return safe critical response if agent fails"""
        fallback_response = {
            "crisis_detected": True,
            "severity": "critical",
            "confidence_score": 0.0,
            "indicators": [],
            "emotional_state": "Unable to analyze due to system error",
            "recommended_action": "Please reach out to crisis hotline or supervisor immediately as a precaution",
            "show_resources": True,
            "escalation_needed": True,
            "context_factors": ["system_error"],
            "personalized_note": None,
            "resources": self.config.get('resources', {}),
            "_error": error_msg,
            "_fallback": True
        }
        
        # Log fallback as failed metric
        if user_id or shift_id:
            self._log_metrics(
                user_id=user_id,
                shift_id=shift_id,
                request_data=request_data or {},
                response_data=fallback_response,
                latency_ms=latency_ms,
                token_usage=None,
                success=False,
                error=error_msg
            )
        
        return fallback


class PatientSafetyCorrelationAgent(BaseAgent):
    """AI agent for correlating healthcare worker burnout with patient safety risks"""
    
    def __init__(self):
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'agents', 'patient_safety_correlation.yaml'
        )
        super().__init__(config_path)
    
    def analyze_correlation(self, stress_level: int, consecutive_shifts: int,
                          red_zone_count: int, sleep_deficit_hours: float,
                          avg_shift_hours: float, days_since_break: int,
                          user_id: int = None, shift_id: int = None,
                          crisis_alert_count: int = 0, team_red_zone_count: int = 0,
                          understaffing_percentage: float = 0, recent_incidents: int = 0,
                          shift_pattern_summary: str = "Standard rotation",
                          recent_anomalies: str = "No significant anomalies detected") -> Dict[str, Any]:
        """
        Analyze correlation between burnout metrics and patient safety risks
        
        Args:
            stress_level: Current stress level (1-10, required)
            consecutive_shifts: Number of consecutive shifts worked (required)
            red_zone_count: Red zone days in last 7 days (required)
            sleep_deficit_hours: Cumulative sleep deficit (required)
            avg_shift_hours: Average shift length in hours (required)
            days_since_break: Days since last day off (required)
            user_id: User ID for metrics logging
            shift_id: Shift ID for metrics logging
            crisis_alert_count: Crisis alerts in last 30 days (optional)
            team_red_zone_count: Other team members in red zone (optional)
            understaffing_percentage: Department understaffing % (optional)
            recent_incidents: Recent patient safety incidents (optional)
            shift_pattern_summary: Summary of recent shift patterns (optional)
            recent_anomalies: Anomaly detection results (optional)
        
        Returns:
            {
                "correlation_score": float (0.0-1.0),
                "risk_level": "low"|"moderate"|"high"|"critical",
                "primary_risk_factors": [str],
                "patient_safety_concerns": [
                    {
                        "type": "medication_errors"|"documentation_gaps"|"response_delays"|"handoff_failures",
                        "likelihood": "low"|"moderate"|"high",
                        "reasoning": str
                    }
                ],
                "high_risk_periods": [
                    {
                        "timeframe": str,
                        "risk_score": float,
                        "contributing_factors": [str]
                    }
                ],
                "recommendations": [
                    {
                        "priority": "immediate"|"urgent"|"recommended",
                        "action": str,
                        "expected_impact": str
                    }
                ],
                "confidence": float (0.0-1.0)
            }
        """
        # Input validation
        if not (1 <= stress_level <= 10):
            return self._safe_fallback_correlation("Invalid stress_level", user_id, shift_id)
        if consecutive_shifts < 0 or red_zone_count < 0 or sleep_deficit_hours < 0:
            return self._safe_fallback_correlation("Invalid negative values", user_id, shift_id)
        
        # Build request data
        request_data = {
            "stress_level": stress_level,
            "consecutive_shifts": consecutive_shifts,
            "red_zone_count": red_zone_count,
            "sleep_deficit_hours": sleep_deficit_hours,
            "crisis_alert_count": crisis_alert_count,
            "avg_shift_hours": avg_shift_hours,
            "days_since_break": days_since_break,
            "team_red_zone_count": team_red_zone_count,
            "understaffing_percentage": understaffing_percentage,
            "recent_incidents": recent_incidents,
            "shift_pattern_summary": shift_pattern_summary,
            "recent_anomalies": recent_anomalies
        }
        
        # Build user prompt from template
        user_prompt = self.config['user_prompt_template'].format(**request_data)
        system_prompt = self.config['system_prompt']
        
        # Call OpenAI
        api_result = self._call_openai(system_prompt, user_prompt)
        
        if not api_result['success']:
            return self._safe_fallback_correlation(
                api_result['error'], user_id, shift_id, api_result['latency_ms']
            )
        
        result = api_result['data']
        
        # Log metrics if user/shift provided
        if user_id or shift_id:
            self._log_metrics(
                user_id=user_id,
                shift_id=shift_id,
                request_data=request_data,
                response_data=result,
                latency_ms=api_result['latency_ms'],
                token_usage=api_result['token_usage'],
                success=True,
                error=None
            )
        
        return result
    
    def _safe_fallback_correlation(self, error_msg: str, user_id: int = None, 
                                  shift_id: int = None, latency_ms: int = 0) -> Dict[str, Any]:
        """Return safe fallback response on error"""
        fallback = {
            "correlation_score": 0.5,
            "risk_level": "moderate",
            "primary_risk_factors": ["Insufficient data for accurate correlation"],
            "patient_safety_concerns": [
                {
                    "type": "general_risk",
                    "likelihood": "moderate",
                    "reasoning": "Unable to perform detailed correlation analysis due to data limitations"
                }
            ],
            "high_risk_periods": [],
            "recommendations": [
                {
                    "priority": "recommended",
                    "action": "Collect comprehensive burnout and safety metrics for accurate analysis",
                    "expected_impact": "Enable data-driven safety interventions"
                }
            ],
            "confidence": 0.3,
            "_fallback": True,
            "_error": error_msg
        }
        
        # Log fallback as failed metric
        if user_id or shift_id:
            self._log_metrics(
                user_id=user_id,
                shift_id=shift_id,
                request_data={},
                response_data=fallback,
                latency_ms=latency_ms,
                token_usage=None,
                success=False,
                error=error_msg
            )
        
        return fallback


class EmotionClassifierAgent(BaseAgent):
    """AI agent for pre-processing shift notes to classify emotional states"""
    
    def __init__(self):
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'agents', 'emotion_classifier.yaml'
        )
        super().__init__(config_path)
    
    def classify(self, shift_note: str, user_id: int = None, shift_id: int = None,
                shift_type: str = "unknown", shift_hours: float = 8,
                stress_level: int = None, recent_pattern: str = "No prior data") -> Dict[str, Any]:
        """
        Classify emotions in shift note and flag for crisis detection if needed
        
        Args:
            shift_note: The shift note text to analyze (required)
            user_id: User ID for metrics logging
            shift_id: Shift ID for metrics logging
            shift_type: Type of shift (day/night/overnight, optional)
            shift_hours: Duration of shift in hours (optional)
            stress_level: Self-reported stress level 1-10 (optional)
            recent_pattern: Summary of recent emotional patterns (optional)
        
        Returns:
            {
                "primary_emotion": "burnout"|"frustration"|"anxiety"|"sadness"|"hopelessness"|"guilt"|"neutral"|"positive",
                "intensity": int (0-10),
                "secondary_emotions": [str],
                "sentiment_score": float (-1.0 to 1.0),
                "emotional_phrases": [str],
                "emotion_transitions": [
                    {
                        "from": str,
                        "to": str,
                        "trigger": str
                    }
                ],
                "crisis_flag": bool,
                "crisis_reasoning": str,
                "recommended_action": "immediate_analysis"|"standard_processing"|"positive_reinforcement"|"routine_monitoring",
                "confidence": float (0.0-1.0)
            }
        """
        # Input validation
        if not shift_note or not shift_note.strip():
            return self._safe_fallback_emotion("Empty shift note", user_id, shift_id)
        if len(shift_note) < 5:
            return self._safe_fallback_emotion("Shift note too short", user_id, shift_id)
        
        # Build request data
        request_data = {
            "shift_note": shift_note,
            "shift_type": shift_type,
            "shift_hours": shift_hours,
            "stress_level": stress_level if stress_level else "Not provided",
            "recent_pattern": recent_pattern
        }
        
        # Build user prompt from template
        user_prompt = self.config['user_prompt_template'].format(**request_data)
        system_prompt = self.config['system_prompt']
        
        # Call OpenAI
        api_result = self._call_openai(system_prompt, user_prompt)
        
        if not api_result['success']:
            return self._safe_fallback_emotion(
                api_result['error'], user_id, shift_id, api_result['latency_ms']
            )
        
        result = api_result['data']
        
        # Log metrics if user/shift provided
        if user_id or shift_id:
            self._log_metrics(
                user_id=user_id,
                shift_id=shift_id,
                request_data=request_data,
                response_data=result,
                latency_ms=api_result['latency_ms'],
                token_usage=api_result['token_usage'],
                success=True,
                error=None
            )
        
        return result
    
    def _safe_fallback_emotion(self, error_msg: str, user_id: int = None,
                              shift_id: int = None, latency_ms: int = 0) -> Dict[str, Any]:
        """Return safe fallback response on error"""
        fallback = {
            "primary_emotion": "neutral",
            "intensity": 5,
            "secondary_emotions": [],
            "sentiment_score": 0.0,
            "emotional_phrases": [],
            "emotion_transitions": [],
            "crisis_flag": False,
            "crisis_reasoning": "",
            "recommended_action": "standard_processing",
            "confidence": 0.2,
            "_fallback": True,
            "_error": error_msg
        }
        
        # Log fallback as failed metric
        if user_id or shift_id:
            self._log_metrics(
                user_id=user_id,
                shift_id=shift_id,
                request_data={},
                response_data=fallback,
                latency_ms=latency_ms,
                token_usage=None,
                success=False,
                error=error_msg
            )
        
        return fallback


class InsightComposerAgent(BaseAgent):
    """AI agent for synthesizing multiple agent outputs into actionable insights"""
    
    def __init__(self):
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'agents', 'insight_composer.yaml'
        )
        super().__init__(config_path)
    
    def compose(self, safeshift_index: float, current_zone: str,
               consecutive_shifts: int, days_since_break: int, audience: str,
               user_id: int = None, shift_id: int = None,
               crisis_detection_output: Dict = None,
               emotion_classification_output: Dict = None,
               patient_safety_output: Dict = None,
               micro_break_output: Dict = None,
               anomaly_output: str = "No anomalies detected",
               zone_history: str = "No historical data") -> Dict[str, Any]:
        """
        Synthesize multiple agent outputs into coherent, actionable insights
        
        Args:
            safeshift_index: Current SafeShiftIndex score (0-100, required)
            current_zone: Current burnout zone (green/yellow/orange/red, required)
            consecutive_shifts: Number of consecutive shifts worked (required)
            days_since_break: Days since last day off (required)
            audience: Target audience (nurse/supervisor/both, required)
            user_id: User ID for metrics logging
            shift_id: Shift ID for metrics logging
            crisis_detection_output: Output from CrisisDetectionAgent (optional)
            emotion_classification_output: Output from EmotionClassifierAgent (optional)
            patient_safety_output: Output from PatientSafetyCorrelationAgent (optional)
            micro_break_output: Output from MicroBreakCoachAgent (optional)
            anomaly_output: Anomaly detection results (optional)
            zone_history: Zone pattern over last 7 days (optional)
        
        Returns:
            {
                "summary": str,
                "urgency_level": "routine"|"attention_needed"|"urgent"|"critical",
                "primary_insights": [
                    {
                        "category": "crisis"|"burnout"|"patient_safety"|"wellness"|"trend",
                        "message": str,
                        "supporting_data": str,
                        "priority": int (1-5)
                    }
                ],
                "recommendations": [
                    {
                        "action": str,
                        "timing": "immediate"|"today"|"this_week"|"ongoing",
                        "expected_benefit": str,
                        "source_agents": [str]
                    }
                ],
                "nurse_message": str,
                "supervisor_message": str,
                "connections": [
                    {
                        "insight": str,
                        "agents_involved": [str],
                        "implication": str
                    }
                ],
                "confidence": float (0.0-1.0)
            }
        """
        # Input validation
        if not (0 <= safeshift_index <= 100):
            return self._safe_fallback_insight("Invalid SafeShiftIndex", user_id, shift_id)
        if current_zone not in ['green', 'yellow', 'orange', 'red']:
            return self._safe_fallback_insight("Invalid zone", user_id, shift_id)
        if audience not in ['nurse', 'supervisor', 'both']:
            return self._safe_fallback_insight("Invalid audience", user_id, shift_id)
        
        # At least one agent output should be provided
        if not any([crisis_detection_output, emotion_classification_output, 
                   patient_safety_output, micro_break_output]):
            return self._safe_fallback_insight("No agent outputs provided", user_id, shift_id)
        
        # Build request data
        request_data = {
            "crisis_detection_output": json.dumps(crisis_detection_output) if crisis_detection_output else "Not available",
            "emotion_classification_output": json.dumps(emotion_classification_output) if emotion_classification_output else "Not available",
            "patient_safety_output": json.dumps(patient_safety_output) if patient_safety_output else "Not available",
            "micro_break_output": json.dumps(micro_break_output) if micro_break_output else "Not available",
            "anomaly_output": anomaly_output,
            "safeshift_index": safeshift_index,
            "current_zone": current_zone,
            "zone_history": zone_history,
            "consecutive_shifts": consecutive_shifts,
            "days_since_break": days_since_break,
            "audience": audience
        }
        
        # Build user prompt from template
        user_prompt = self.config['user_prompt_template'].format(**request_data)
        system_prompt = self.config['system_prompt']
        
        # Call OpenAI
        api_result = self._call_openai(system_prompt, user_prompt)
        
        if not api_result['success']:
            return self._safe_fallback_insight(
                api_result['error'], user_id, shift_id, api_result['latency_ms']
            )
        
        result = api_result['data']
        
        # Log metrics if user/shift provided
        if user_id or shift_id:
            self._log_metrics(
                user_id=user_id,
                shift_id=shift_id,
                request_data=request_data,
                response_data=result,
                latency_ms=api_result['latency_ms'],
                token_usage=api_result['token_usage'],
                success=True,
                error=None
            )
        
        return result
    
    def _safe_fallback_insight(self, error_msg: str, user_id: int = None,
                              shift_id: int = None, latency_ms: int = 0) -> Dict[str, Any]:
        """Return safe fallback response on error"""
        fallback = {
            "summary": "Current shift data indicates standard monitoring recommended",
            "urgency_level": "routine",
            "primary_insights": [
                {
                    "category": "wellness",
                    "message": "Continue monitoring your stress levels and self-care practices",
                    "supporting_data": "Limited data available for comprehensive analysis",
                    "priority": 3
                }
            ],
            "recommendations": [
                {
                    "action": "Complete shift notes to enable better insights",
                    "timing": "ongoing",
                    "expected_benefit": "More personalized recommendations and early warning detection",
                    "source_agents": []
                }
            ],
            "nurse_message": "Keep taking care of yourself and documenting your experiences to help us support you better.",
            "supervisor_message": "Insufficient data for detailed insights. Encourage comprehensive shift note documentation.",
            "connections": [],
            "confidence": 0.3,
            "_fallback": True,
            "_error": error_msg
        }
        
        # Log fallback as failed metric
        if user_id or shift_id:
            self._log_metrics(
                user_id=user_id,
                shift_id=shift_id,
                request_data={},
                response_data=fallback,
                latency_ms=latency_ms,
                token_usage=None,
                success=False,
                error=error_msg
            )
        
        return fallback


class MicroBreakCoachAgent(BaseAgent):
    """AI agent for generating quick stress-relief interventions"""
    
    def __init__(self):
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'agents', 'micro_break_coach.yaml'
        )
        super().__init__(config_path)
    
    def generate_break(self, stress_level: int, minutes_available: int, 
                       location: str, user_id: int = None, shift_id: int = None,
                       shift_type: str = None) -> Dict[str, Any]:
        """
        Generate personalized micro-break intervention
        
        Args:
            stress_level: 1-10 stress rating (required)
            minutes_available: 2, 3, or 5 minutes (required)
            location: break_room, hallway, nurses_station, bathroom, outside (required)
            user_id: For metrics logging
            shift_id: For metrics logging
            shift_type: day/night (optional context)
        
        Returns:
            {
                "name": "Brief name for the break",
                "duration_minutes": int,
                "location_fit": "Confirmed location or suggested alternative",
                "steps": [str, str, ...],
                "why": "Physiological/psychological explanation",
                "expected_stress_reduction": int (1-3)
            }
        """
        # Validate and sanitize inputs
        if not isinstance(stress_level, int) or stress_level < 1 or stress_level > 10:
            stress_level = max(1, min(10, int(stress_level))) if stress_level else 5
        
        if minutes_available not in [2, 3, 5]:
            # Default to closest valid option
            minutes_available = min([2, 3, 5], key=lambda x: abs(x - minutes_available))
        
        valid_locations = ['break_room', 'hallway', 'nurses_station', 'bathroom', 'outside']
        if location not in valid_locations:
            location = 'break_room'  # Safe default
        
        # Build request
        request_data = {
            "stress_level": stress_level,
            "minutes_available": minutes_available,
            "location": location,
            "shift_type": shift_type
        }
        
        user_message = f"""stress_level: {stress_level}
minutes_available: {minutes_available}
location: {location}"""
        
        if shift_type:
            user_message += f"\nshift_type: {shift_type}"
        
        # Call OpenAI
        api_result = self._call_openai(self.config['system'], user_message)
        
        if not api_result['success']:
            return self._safe_fallback(
                api_result['error'], stress_level, minutes_available, 
                location, user_id, shift_id, request_data, api_result['latency_ms']
            )
        
        result = api_result['data']
        
        # Validate required keys
        required_keys = self.config.get('required_keys', [])
        missing_keys = [k for k in required_keys if k not in result]
        if missing_keys:
            return self._safe_fallback(
                f"Missing keys: {missing_keys}", stress_level, minutes_available,
                location, user_id, shift_id, request_data, api_result['latency_ms']
            )
        
        # Log metrics (only if user_id or shift_id provided)
        if user_id or shift_id:
            self._log_metrics(
                user_id=user_id,
                shift_id=shift_id,
                request_data=request_data,
                response_data=result,
                latency_ms=api_result['latency_ms'],
                token_usage=api_result['token_usage'],
                success=True,
                error=None
            )
        
        return result
    
    def _safe_fallback(self, error_msg: str, stress_level: int, 
                       minutes_available: int, location: str,
                       user_id: Optional[int] = None, shift_id: Optional[int] = None,
                       request_data: Optional[Dict] = None,
                       latency_ms: int = 0) -> Dict[str, Any]:
        """Return safe default break if agent fails"""
        
        # Provide different fallbacks based on stress level
        if stress_level >= 8:
            # High stress - grounding technique
            fallback = {
                "name": "Emergency Grounding Technique",
                "duration_minutes": minutes_available,
                "location_fit": location,
                "steps": [
                    "Find a quiet corner and stand or sit comfortably",
                    "Name 5 things you can see around you",
                    "Take 3 slow, deep breaths (in for 4, hold 4, out for 6)",
                    "Gently roll your shoulders back 3 times"
                ][:4 if minutes_available >= 3 else 3],
                "why": "Grounding techniques redirect focus from stress to present moment, activating calming response.",
                "expected_stress_reduction": 2,
                "_fallback": True,
                "_error": error_msg
            }
        else:
            # Moderate/low stress - breathing reset
            fallback = {
                "name": "Quick Breathing Reset",
                "duration_minutes": minutes_available,
                "location_fit": location,
                "steps": [
                    "Find a comfortable spot to stand or sit",
                    "Close your eyes if comfortable, or find a focal point",
                    "Breathe in slowly for 4 counts",
                    "Hold for 4 counts",
                    "Exhale slowly for 6 counts",
                    "Repeat 3-5 times"
                ][:5 if minutes_available >= 5 else 4],
                "why": "Deep breathing activates parasympathetic nervous system, reducing cortisol and heart rate.",
                "expected_stress_reduction": 2,
                "_fallback": True,
                "_error": error_msg
            }
        
        # Log fallback as failed metric
        if user_id or shift_id:
            self._log_metrics(
                user_id=user_id,
                shift_id=shift_id,
                request_data=request_data or {},
                response_data=fallback,
                latency_ms=latency_ms,
                token_usage=None,
                success=False,
                error=error_msg
            )
        
        return fallback
