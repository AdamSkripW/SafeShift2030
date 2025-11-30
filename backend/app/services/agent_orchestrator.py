"""
Agent Orchestrator - Coordinates multi-agent workflows
Manages data flow between agents and implements intelligent agent chaining
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, date
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
    4. Shift prediction (7-day optimal schedule)
    """
    
    def __init__(self):
        """Initialize all agents"""
        self.emotion_agent = EmotionClassifierAgent()
        self.crisis_agent = CrisisDetectionAgent()
        self.safety_agent = PatientSafetyCorrelationAgent()
        self.break_agent = MicroBreakCoachAgent()
        self.insight_agent = InsightComposerAgent()
        
        # Lazy load prediction agent (only when needed)
        self._prediction_agent = None
    
    @property
    def prediction_agent(self):
        """Lazy initialization of ShiftRecommendationAgent"""
        if self._prediction_agent is None:
            from app.services.agents import ShiftRecommendationAgent
            self._prediction_agent = ShiftRecommendationAgent()
        return self._prediction_agent
    
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
        
        print(f"[ORCHESTRATOR] Starting comprehensive insight generation")
        print(f"[ORCHESTRATOR] SafeShift Index: {shift_context['safeshift_index']}, Zone: {shift_context['current_zone']}")
        print(f"[ORCHESTRATOR] Stress: {shift_context['stress_level']}, Has note: {bool(shift_context.get('shift_note'))}")
        
        # Step 1: Patient Safety Correlation (always run)
        print(f"[ORCHESTRATOR] Step 1: Running PatientSafetyCorrelation...")
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
        print(f"[ORCHESTRATOR] ✓ PatientSafetyCorrelation complete, risk: {safety_result.get('risk_level')}")
        
        # Step 2: Micro-Break (if stress >= 6)
        break_result = None
        if shift_context['stress_level'] >= 6:
            print(f"[ORCHESTRATOR] Step 2: Running MicroBreakCoach (stress >= 6)...")
            break_result = self.break_agent.generate_break(
                stress_level=shift_context['stress_level'],
                minutes_available=shift_context.get('minutes_available', 5),
                location=shift_context.get('location', 'hallway'),
                shift_type=shift_context.get('shift_type', 'day'),
                user_id=user_id,
                shift_id=shift_id
            )
            agents_run.append("MicroBreakCoach")
            print(f"[ORCHESTRATOR] ✓ MicroBreakCoach complete")
        else:
            print(f"[ORCHESTRATOR] Step 2: Skipping MicroBreakCoach (stress < 6)")
        
        # Step 3: Emotion Classification (if shift_note exists)
        emotion_result = None
        crisis_result = None
        
        if shift_context.get('shift_note'):
            print(f"[ORCHESTRATOR] Step 3: Running EmotionClassifier...")
            emotion_result = self.emotion_agent.classify(
                shift_note=shift_context['shift_note'],
                shift_type=shift_context.get('shift_type', 'unknown'),
                shift_hours=shift_context.get('shift_hours', 8),
                stress_level=shift_context['stress_level'],
                user_id=user_id,
                shift_id=shift_id
            )
            agents_run.append("EmotionClassifier")
            print(f"[ORCHESTRATOR] ✓ EmotionClassifier complete, crisis_flag: {emotion_result.get('crisis_flag')}")
            
            # Step 4: Crisis Detection (if emotion flags crisis)
            if emotion_result.get('crisis_flag'):
                print(f"[ORCHESTRATOR] Step 4: Running CrisisDetection (emotion flagged crisis)...")
                crisis_result = self.crisis_agent.detect(
                    shift_note=shift_context['shift_note'],
                    user_id=user_id,
                    shift_id=shift_id,
                    stress_history=shift_context.get('stress_history'),
                    recent_shifts=shift_context.get('recent_shifts'),
                    previous_alerts=shift_context.get('previous_alerts', 0)
                )
                agents_run.append("CrisisDetection")
                print(f"[ORCHESTRATOR] ✓ CrisisDetection complete, severity: {crisis_result.get('severity')}")
        else:
            print(f"[ORCHESTRATOR] Step 3-4: Skipping Emotion/Crisis (no shift note)")
        
        # Step 5: Insight Composer (synthesize all results)
        print(f"[ORCHESTRATOR] Step 5: Running InsightComposer...")
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
        print(f"[ORCHESTRATOR] ✓ InsightComposer complete, urgency: {insight_result.get('urgency_level')}")
        print(f"[ORCHESTRATOR] ✓ All agents complete: {agents_run}")
        
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
    
    # ============================================
    # SHIFT PREDICTION WORKFLOW
    # ============================================
    
    def predict_optimal_shifts(self, user_id: int, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Predict optimal shift schedule for next N days
        
        Args:
            user_id: User ID to generate predictions for
            days_ahead: Number of days to predict (1-14, default 7)
        
        Returns:
            Dict with recommended_schedule, recovery_priority, key_recommendations, predicted_burnout_trend
        """
        from app.models import Shift, BurnoutAlert, User
        
        # Get user
        user = User.query.get(user_id)
        user_name = f"{user.FirstName} {user.LastName}" if user else None
        
        # Get historical shifts (last 30 days for analysis, return last 14 for LLM)
        recent_shifts = Shift.query.filter_by(UserId=user_id)\
            .order_by(Shift.ShiftDate.desc())\
            .limit(30).all()
        
        # Handle new users with no historical data
        if not recent_shifts:
            print(f"[ORCHESTRATOR] No historical shifts for user {user_id}, generating baseline recommendations")
            # Call prediction agent with minimal context for new users
            result = self.prediction_agent.predict_optimal_shifts(
                user_id=user_id,
                historical_shifts=[],
                consecutive_shifts=0,
                sleep_deficit_hours=0,
                avg_stress_7d=0,
                stress_trend="stable",
                active_alerts=0,
                days_ahead=days_ahead,
                user_name=user_name
            )
            result['success'] = True
            return result
        
        # Calculate metrics
        consecutive = self._count_consecutive_shifts(recent_shifts)
        sleep_deficit = self._calculate_sleep_deficit(recent_shifts)
        avg_stress = self._calculate_avg_stress(recent_shifts[:7])
        stress_trend = self._get_stress_trend(recent_shifts[:14])
        
        # Get active alerts
        active_alerts = BurnoutAlert.query.filter_by(
            UserId=user_id,
            IsResolved=False
        ).count()
        
        # Build shift summaries for LLM
        historical_summaries = [self._shift_summary(s) for s in recent_shifts[:14]]
        
        # Call prediction agent
        result = self.prediction_agent.predict_optimal_shifts(
            user_id=user_id,
            historical_shifts=historical_summaries,
            consecutive_shifts=consecutive,
            sleep_deficit_hours=sleep_deficit,
            avg_stress_7d=avg_stress,
            stress_trend=stress_trend,
            active_alerts=active_alerts,
            days_ahead=days_ahead,
            user_name=user_name
        )
        
        result['success'] = True
        return result
    
    def _count_consecutive_shifts(self, shifts: List) -> int:
        """Count consecutive working days from most recent"""
        if not shifts:
            return 0
        
        # Sort by date descending
        sorted_shifts = sorted(shifts, key=lambda s: s.ShiftDate, reverse=True)
        
        consecutive = 1
        for i in range(len(sorted_shifts) - 1):
            delta = (sorted_shifts[i].ShiftDate - sorted_shifts[i+1].ShiftDate).days
            if delta == 1:
                consecutive += 1
            else:
                break
        
        return consecutive
    
    def _calculate_sleep_deficit(self, shifts: List, target_hours: float = 7.0, days: int = 14) -> float:
        """Calculate total sleep deficit over last N days"""
        if not shifts:
            return 0.0
        
        recent = shifts[:days]
        total_deficit = sum(max(0, target_hours - s.HoursSleptBefore) for s in recent)
        return round(total_deficit, 1)
    
    def _calculate_avg_stress(self, shifts: List) -> float:
        """Calculate average stress level"""
        if not shifts:
            return 5.0
        
        total_stress = sum(s.StressLevel for s in shifts if s.StressLevel is not None)
        count = len([s for s in shifts if s.StressLevel is not None])
        
        if count == 0:
            return 5.0
        
        return round(total_stress / count, 1)
    
    def _get_stress_trend(self, shifts: List) -> str:
        """Determine if stress is increasing, stable, or decreasing"""
        if not shifts or len(shifts) < 4:
            return "stable"
        
        # Sort by date ascending
        sorted_shifts = sorted(shifts, key=lambda s: s.ShiftDate)
        
        # Compare first half vs second half average
        mid = len(sorted_shifts) // 2
        first_half_avg = sum(s.StressLevel for s in sorted_shifts[:mid] if s.StressLevel) / mid
        second_half_avg = sum(s.StressLevel for s in sorted_shifts[mid:] if s.StressLevel) / (len(sorted_shifts) - mid)
        
        diff = second_half_avg - first_half_avg
        
        if diff > 1.0:
            return "increasing"
        elif diff < -1.0:
            return "decreasing"
        else:
            return "stable"
    
    def _shift_summary(self, shift) -> Dict[str, Any]:
        """Create concise shift summary for LLM"""
        return {
            "date": shift.ShiftDate.isoformat(),
            "type": shift.ShiftType,
            "hours": shift.ShiftLengthHours,
            "sleep_before": shift.HoursSleptBefore,
            "stress": shift.StressLevel,
            "zone": shift.Zone,
            "patients": shift.PatientsCount
        }
