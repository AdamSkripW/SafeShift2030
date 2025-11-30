"""
Agent Orchestrator - Coordinates multi-agent workflows
Manages data flow between agents and implements intelligent agent chaining
"""

import json
from typing import Dict, List, Any, Optional
from app.services import (
    CrisisDetectionAgent,
    MicroBreakCoachAgent,
    PatientSafetyCorrelationAgent,
    EmotionClassifierAgent,
    InsightComposerAgent
)


class AgentOrchestrator:
    """
    Orchestrates multi-agent workflows for comprehensive healthcare worker analysis
    
    Supported workflows:
    1. Emotion → Crisis (preprocessing pipeline)
    2. Safety + Break → Insight (analysis synthesis)
    3. Full pipeline (all agents → comprehensive insight)
    """
    
    def __init__(self):
        """Initialize all agents"""
        self.emotion_agent = EmotionClassifierAgent()
        self.crisis_agent = CrisisDetectionAgent()
        self.safety_agent = PatientSafetyCorrelationAgent()
        self.break_agent = MicroBreakCoachAgent()
        self.insight_agent = InsightComposerAgent()
    
    def analyze_shift_note(self, shift_note: str, shift_data: Dict, 
                          user_id: int = None, shift_id: int = None) -> Dict[str, Any]:
        """
        Workflow 1: Emotion Classification → Crisis Detection (if needed)
        
        Args:
            shift_note: Text from shift note
            shift_data: Dict with shift_type, shift_hours, stress_level
            user_id: Optional user ID for metrics
            shift_id: Optional shift ID for metrics
        
        Returns:
            {
                "emotion_result": {...},
                "crisis_result": {...} or None,
                "workflow": "emotion_only" | "emotion_to_crisis"
            }
        """
        # Step 1: Classify emotions
        emotion_result = self.emotion_agent.classify(
            shift_note=shift_note,
            shift_type=shift_data.get('shift_type', 'unknown'),
            shift_hours=shift_data.get('shift_hours', 8),
            stress_level=shift_data.get('stress_level'),
            user_id=user_id,
            shift_id=shift_id
        )
        
        # Step 2: If crisis flagged, run crisis detection
        crisis_result = None
        workflow = "emotion_only"
        
        if emotion_result.get('crisis_flag'):
            workflow = "emotion_to_crisis"
            crisis_result = self.crisis_agent.detect(
                shift_note=shift_note,
                user_id=user_id,
                shift_id=shift_id,
                stress_history=shift_data.get('stress_history'),
                recent_shifts=shift_data.get('recent_shifts'),
                previous_alerts=shift_data.get('previous_alerts', 0)
            )
        
        return {
            "emotion_result": emotion_result,
            "crisis_result": crisis_result,
            "workflow": workflow,
            "orchestrator_version": "1.0.0"
        }
    
    def generate_comprehensive_insight(self, shift_context: Dict,
                                      user_id: int = None, shift_id: int = None,
                                      audience: str = "both") -> Dict[str, Any]:
        """
        Workflow 2: Multi-Agent → Comprehensive Insight
        
        Runs multiple agents and synthesizes results:
        1. Patient Safety Correlation
        2. Micro-Break Suggestion (if stress >= 6)
        3. Emotion Classification (if shift_note exists)
        4. Crisis Detection (if emotion flags crisis)
        5. Insight Composer (synthesizes all)
        
        Args:
            shift_context: Dict containing:
                - safeshift_index (required)
                - current_zone (required)
                - consecutive_shifts (required)
                - days_since_break (required)
                - stress_level (required)
                - red_zone_count (required)
                - sleep_deficit_hours (required)
                - avg_shift_hours (required)
                - shift_note (optional)
                - shift_type (optional)
                - shift_hours (optional)
                - team_red_zone_count (optional)
                - understaffing_percentage (optional)
                - recent_incidents (optional)
                - zone_history (optional)
                - anomaly_output (optional)
            user_id: Optional user ID for metrics
            shift_id: Optional shift ID for metrics
            audience: "nurse" | "supervisor" | "both"
        
        Returns:
            {
                "patient_safety": {...},
                "micro_break": {...} or None,
                "emotion": {...} or None,
                "crisis": {...} or None,
                "comprehensive_insight": {...},
                "agents_run": [str],
                "workflow": "comprehensive_analysis"
            }
        """
        agents_run = []
        
        # Step 1: Patient Safety Correlation (always run)
        safety_result = self.safety_agent.analyze_correlation(
            stress_level=shift_context['stress_level'],
            consecutive_shifts=shift_context['consecutive_shifts'],
            red_zone_count=shift_context['red_zone_count'],
            sleep_deficit_hours=shift_context['sleep_deficit_hours'],
            avg_shift_hours=shift_context['avg_shift_hours'],
            days_since_break=shift_context['days_since_break'],
            team_red_zone_count=shift_context.get('team_red_zone_count', 0),
            understaffing_percentage=shift_context.get('understaffing_percentage', 0),
            recent_incidents=shift_context.get('recent_incidents', 0),
            user_id=user_id,
            shift_id=shift_id
        )
        agents_run.append("PatientSafetyCorrelation")
        
        # Step 2: Micro-Break (if stress >= 6)
        break_result = None
        if shift_context['stress_level'] >= 6:
            break_result = self.break_agent.generate_break(
                stress_level=shift_context['stress_level'],
                minutes_available=shift_context.get('minutes_available', 5),
                location=shift_context.get('location', 'hallway'),
                shift_type=shift_context.get('shift_type', 'day'),
                user_id=user_id,
                shift_id=shift_id
            )
            agents_run.append("MicroBreakCoach")
        
        # Step 3: Emotion Classification (if shift_note exists)
        emotion_result = None
        crisis_result = None
        
        if shift_context.get('shift_note'):
            emotion_result = self.emotion_agent.classify(
                shift_note=shift_context['shift_note'],
                shift_type=shift_context.get('shift_type', 'unknown'),
                shift_hours=shift_context.get('shift_hours', 8),
                stress_level=shift_context['stress_level'],
                user_id=user_id,
                shift_id=shift_id
            )
            agents_run.append("EmotionClassifier")
            
            # Step 4: Crisis Detection (if emotion flags crisis)
            if emotion_result.get('crisis_flag'):
                crisis_result = self.crisis_agent.detect(
                    shift_note=shift_context['shift_note'],
                    user_id=user_id,
                    shift_id=shift_id,
                    stress_history=shift_context.get('stress_history'),
                    recent_shifts=shift_context.get('recent_shifts'),
                    previous_alerts=shift_context.get('previous_alerts', 0)
                )
                agents_run.append("CrisisDetection")
        
        # Step 5: Insight Composer (synthesize all results)
        insight_result = self.insight_agent.compose(
            safeshift_index=shift_context['safeshift_index'],
            current_zone=shift_context['current_zone'],
            consecutive_shifts=shift_context['consecutive_shifts'],
            days_since_break=shift_context['days_since_break'],
            audience=audience,
            crisis_detection_output=crisis_result,
            emotion_classification_output=emotion_result,
            patient_safety_output=safety_result,
            micro_break_output=break_result,
            anomaly_output=shift_context.get('anomaly_output', 'No anomalies detected'),
            zone_history=shift_context.get('zone_history', 'No historical data'),
            user_id=user_id,
            shift_id=shift_id
        )
        agents_run.append("InsightComposer")
        
        return {
            "patient_safety": safety_result,
            "micro_break": break_result,
            "emotion": emotion_result,
            "crisis": crisis_result,
            "comprehensive_insight": insight_result,
            "agents_run": agents_run,
            "workflow": "comprehensive_analysis",
            "orchestrator_version": "1.0.0"
        }
    
    def quick_wellness_check(self, stress_level: int, minutes_available: int = 5,
                            location: str = "hallway", shift_type: str = "day",
                            user_id: int = None, shift_id: int = None) -> Dict[str, Any]:
        """
        Workflow 3: Quick Wellness (just micro-break)
        
        Simple workflow for immediate intervention suggestion
        
        Args:
            stress_level: Current stress level 1-10
            minutes_available: Available minutes for break (2-5)
            location: Current location
            shift_type: day/night/overnight
            user_id: Optional user ID for metrics
            shift_id: Optional shift ID for metrics
        
        Returns:
            {
                "micro_break": {...},
                "workflow": "quick_wellness"
            }
        """
        break_result = self.break_agent.generate_break(
            stress_level=stress_level,
            minutes_available=minutes_available,
            location=location,
            shift_type=shift_type,
            user_id=user_id,
            shift_id=shift_id
        )
        
        return {
            "micro_break": break_result,
            "workflow": "quick_wellness",
            "orchestrator_version": "1.0.0"
        }
    
    def detect_crisis_with_context(self, shift_note: str, user_context: Dict,
                                   user_id: int = None, shift_id: int = None) -> Dict[str, Any]:
        """
        Workflow 4: Enhanced Crisis Detection (emotion preprocessing + crisis + safety correlation)
        
        Provides richer crisis detection with emotional context and safety implications
        
        Args:
            shift_note: Text to analyze
            user_context: Dict with user_name, recent_shifts, stress_history, previous_alerts, etc.
            user_id: Optional user ID for metrics
            shift_id: Optional shift ID for metrics
        
        Returns:
            {
                "emotion": {...},
                "crisis": {...},
                "patient_safety": {...} or None,
                "workflow": "enhanced_crisis_detection"
            }
        """
        # Step 1: Emotion classification
        emotion_result = self.emotion_agent.classify(
            shift_note=shift_note,
            shift_type=user_context.get('shift_type', 'unknown'),
            shift_hours=user_context.get('shift_hours', 8),
            stress_level=user_context.get('stress_level'),
            user_id=user_id,
            shift_id=shift_id
        )
        
        # Step 2: Crisis detection
        crisis_result = self.crisis_agent.detect(
            shift_note=shift_note,
            user_id=user_id,
            shift_id=shift_id,
            user_name=user_context.get('user_name'),
            recent_shifts=user_context.get('recent_shifts'),
            stress_history=user_context.get('stress_history'),
            previous_alerts=user_context.get('previous_alerts', 0)
        )
        
        # Step 3: Patient safety correlation (if high/critical crisis)
        safety_result = None
        if crisis_result.get('severity') in ['high', 'critical']:
            # Run safety correlation to assess patient risk
            if all(k in user_context for k in ['stress_level', 'consecutive_shifts', 'red_zone_count',
                                                'sleep_deficit_hours', 'avg_shift_hours', 'days_since_break']):
                safety_result = self.safety_agent.analyze_correlation(
                    stress_level=user_context['stress_level'],
                    consecutive_shifts=user_context['consecutive_shifts'],
                    red_zone_count=user_context['red_zone_count'],
                    sleep_deficit_hours=user_context['sleep_deficit_hours'],
                    avg_shift_hours=user_context['avg_shift_hours'],
                    days_since_break=user_context['days_since_break'],
                    user_id=user_id,
                    shift_id=shift_id
                )
        
        return {
            "emotion": emotion_result,
            "crisis": crisis_result,
            "patient_safety": safety_result,
            "workflow": "enhanced_crisis_detection",
            "orchestrator_version": "1.0.0"
        }
