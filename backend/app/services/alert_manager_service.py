"""
Alert Manager Service - Centralized alert management
Consolidates anomaly detection, agent insights, and trend analysis
Rule-based system with deduplication and cooldown periods
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.models import db, BurnoutAlert, Shift, User
from sqlalchemy import and_, func


class AlertManagerService:
    """
    Centralized alert management system
    Handles alert creation, deduplication, and prioritization
    """
    
    # Alert configuration with rules
    ALERT_RULES = {
        'crisis_detected': {
            'cooldown_hours': 24,
            'auto_escalate': True,
            'priority': 1
        },
        'comprehensive_analysis': {
            'cooldown_hours': 24,
            'auto_escalate': False,
            'priority': 2
        },
        'consecutive_nights': {
            'cooldown_hours': 48,
            'auto_escalate': False,
            'priority': 3
        },
        'chronic_low_sleep': {
            'cooldown_hours': 72,
            'auto_escalate': True,
            'priority': 2
        },
        'high_stress_pattern': {
            'cooldown_hours': 48,
            'auto_escalate': False,
            'priority': 3
        },
        'patient_safety_risk': {
            'cooldown_hours': 24,
            'auto_escalate': True,
            'priority': 1
        },
        'recovery_needed': {
            'cooldown_hours': 96,
            'auto_escalate': False,
            'priority': 4
        },
        'declining_health': {
            'cooldown_hours': 72,
            'auto_escalate': False,
            'priority': 3
        }
    }
    
    @staticmethod
    def evaluate_and_create_alerts(user_id: int, shift_id: int, context: Dict[str, Any]) -> List[BurnoutAlert]:
        """
        Main entry point - evaluates all alert rules and creates alerts
        
        Args:
            user_id: User ID to check
            shift_id: Current shift ID
            context: Dict with agent_insights, anomalies, safety_analysis, shift_data
        
        Returns:
            List of created BurnoutAlert objects
        """
        created_alerts = []
        
        print(f"[ALERT_MANAGER] Evaluating alerts for user {user_id}, shift {shift_id}")
        
        # 1. Check agent insights urgency
        if context.get('agent_insights'):
            alert = AlertManagerService._check_agent_urgency(
                user_id, shift_id, context['agent_insights']
            )
            if alert:
                created_alerts.append(alert)
                print(f"[ALERT_MANAGER] Created agent urgency alert: {alert.AlertType}")
        
        # 2. Check anomalies
        if context.get('anomalies'):
            alerts = AlertManagerService._check_anomalies(
                user_id, context['anomalies']
            )
            created_alerts.extend(alerts)
            print(f"[ALERT_MANAGER] Created {len(alerts)} anomaly alerts")
        
        # 3. Check patient safety correlation
        if context.get('safety_analysis'):
            alert = AlertManagerService._check_patient_safety(
                user_id, shift_id, context['safety_analysis']
            )
            if alert:
                created_alerts.append(alert)
                print(f"[ALERT_MANAGER] Created patient safety alert")
        
        # 4. Check trend-based patterns (every 3 shifts)
        shift_count = Shift.query.filter_by(UserId=user_id).count()
        if shift_count > 0 and shift_count % 3 == 0:
            alerts = AlertManagerService._check_trends(user_id)
            created_alerts.extend(alerts)
            print(f"[ALERT_MANAGER] Created {len(alerts)} trend alerts")
        
        # Save all alerts to database
        for alert in created_alerts:
            db.session.add(alert)
        
        if created_alerts:
            db.session.commit()
            print(f"[ALERT_MANAGER] ✓ Total alerts created: {len(created_alerts)}")
        
        return created_alerts
    
    @staticmethod
    def _should_create_alert(user_id: int, alert_type: str) -> bool:
        """
        Check if alert should be created (not duplicate within cooldown period)
        
        Args:
            user_id: User ID
            alert_type: Type of alert to check
        
        Returns:
            True if alert should be created, False if within cooldown
        """
        rule = AlertManagerService.ALERT_RULES.get(alert_type)
        if not rule:
            return True  # Unknown type, allow creation
        
        cooldown_hours = rule.get('cooldown_hours', 24)
        cutoff = datetime.utcnow() - timedelta(hours=cooldown_hours)
        
        # Check for existing unresolved alert within cooldown period
        existing = BurnoutAlert.query.filter(
            BurnoutAlert.UserId == user_id,
            BurnoutAlert.AlertType == alert_type,
            BurnoutAlert.CreatedAt >= cutoff,
            BurnoutAlert.IsResolved == False
        ).first()
        
        return existing is None
    
    @staticmethod
    def _check_agent_urgency(user_id: int, shift_id: int, agent_insights: Dict) -> Optional[BurnoutAlert]:
        """Check urgency level from comprehensive agent insights"""
        urgency = agent_insights.get('urgency_level')
        
        # Only create alerts for urgent or critical
        if urgency not in ['urgent', 'critical']:
            return None
        
        alert_type = 'comprehensive_analysis'
        
        if not AlertManagerService._should_create_alert(user_id, alert_type):
            return None
        
        severity = 'critical' if urgency == 'critical' else 'high'
        message = agent_insights.get('summary', 'Comprehensive analysis flagged elevated concern')
        
        return BurnoutAlert(
            UserId=user_id,
            AlertType=alert_type,
            Severity=severity,
            AlertMessage=message,
            Description=f"Agent urgency: {urgency}. {message}",
            IsResolved=False
        )
    
    @staticmethod
    def _check_anomalies(user_id: int, anomalies: List[Dict]) -> List[BurnoutAlert]:
        """Check anomalies detected by AnomalyService"""
        alerts = []
        
        for anomaly in anomalies:
            anomaly_type = anomaly.get('type')
            
            # Use anomaly type directly as alert type (now that AlertType is VARCHAR)
            alert_type = anomaly_type
            
            if not alert_type:
                print(f"[ALERT_MANAGER] Skipping anomaly with no type")
                continue
            
            if not AlertManagerService._should_create_alert(user_id, alert_type):
                continue
            
            # Map anomaly severity to alert severity
            severity_map = {
                'low': 'low',
                'medium': 'medium',
                'high': 'high',
                'critical': 'critical'
            }
            severity = severity_map.get(anomaly.get('severity', 'medium'), 'medium')
            
            message = anomaly.get('message', anomaly.get('description', 'Anomaly detected in shift pattern'))
            
            alert = BurnoutAlert(
                UserId=user_id,
                AlertType=alert_type,
                Severity=severity,
                AlertMessage=message,
                Description=anomaly.get('description', message),
                IsResolved=False
            )
            alerts.append(alert)
        
        return alerts
    
    @staticmethod
    def _check_patient_safety(user_id: int, shift_id: int, safety_analysis: Dict) -> Optional[BurnoutAlert]:
        """Check patient safety correlation results"""
        risk_level = safety_analysis.get('risk_level')
        
        # Only alert on high or critical risk
        if risk_level not in ['high', 'critical']:
            return None
        
        alert_type = 'patient_safety_risk'
        
        if not AlertManagerService._should_create_alert(user_id, alert_type):
            return None
        
        severity = 'critical' if risk_level == 'critical' else 'high'
        
        # Build message from primary concerns
        concerns = safety_analysis.get('patient_safety_concerns', [])
        concern_types = [c.get('type', '') for c in concerns if c.get('likelihood') in ['moderate', 'high']]
        
        if concern_types:
            concern_text = ', '.join(concern_types[:2])
            message = f"Elevated patient safety risk: {concern_text}"
        else:
            message = f"Patient safety risk level: {risk_level}"
        
        return BurnoutAlert(
            UserId=user_id,
            AlertType=alert_type,
            Severity=severity,
            AlertMessage=message,
            Description=f"Patient safety correlation detected {risk_level} risk level",
            IsResolved=False
        )
    
    @staticmethod
    def _check_trends(user_id: int) -> List[BurnoutAlert]:
        """Check 7-day trend patterns"""
        alerts = []
        
        # Get last 7 days of shifts
        cutoff_date = datetime.utcnow().date() - timedelta(days=7)
        
        shifts = Shift.query.filter(
            Shift.UserId == user_id,
            Shift.ShiftDate >= cutoff_date
        ).order_by(Shift.ShiftDate.desc()).all()
        
        if len(shifts) < 3:
            return alerts
        
        # Check 1: Consecutive high stress (3+ days with stress >= 7)
        high_stress_count = sum(1 for s in shifts if s.StressLevel >= 7)
        if high_stress_count >= 3:
            alert_type = 'high_stress_pattern'
            
            if AlertManagerService._should_create_alert(user_id, alert_type):
                message = f"High stress detected in {high_stress_count} of last {len(shifts)} shifts"
                alert = BurnoutAlert(
                    UserId=user_id,
                    AlertType=alert_type,
                    Severity='high',
                    AlertMessage=message,
                    Description=f"Persistent high stress pattern over {len(shifts)} shifts",
                    IsResolved=False
                )
                alerts.append(alert)
        
        # Check 2: Declining health (SafeShift Index getting worse)
        if len(shifts) >= 5:
            recent_indices = [s.SafeShiftIndex for s in shifts[:3] if s.SafeShiftIndex]
            older_indices = [s.SafeShiftIndex for s in shifts[3:6] if s.SafeShiftIndex]
            
            if recent_indices and older_indices:
                recent_avg = sum(recent_indices) / len(recent_indices)
                older_avg = sum(older_indices) / len(older_indices)
                
                # If SafeShift Index dropped by 15+ points
                if older_avg - recent_avg >= 15:
                    alert_type = 'declining_health'
                    
                    if AlertManagerService._should_create_alert(user_id, alert_type):
                        message = f"SafeShift Index declining: {older_avg:.0f} → {recent_avg:.0f}"
                        alert = BurnoutAlert(
                            UserId=user_id,
                            AlertType=alert_type,
                            Severity='high',
                            AlertMessage=message,
                            Description=f"Declining wellness trend detected over past week",
                            IsResolved=False
                        )
                        alerts.append(alert)
        
        # Check 3: Recovery needed (10+ consecutive days without break)
        if len(shifts) >= 7:
            # Check if shifts span 10+ consecutive days
            shift_dates = sorted([s.ShiftDate for s in shifts])
            if shift_dates:
                date_range = (shift_dates[-1] - shift_dates[0]).days
                
                if date_range >= 10 and len(shifts) >= 8:
                    alert_type = 'recovery_needed'
                    
                    if AlertManagerService._should_create_alert(user_id, alert_type):
                        message = f"You've worked {len(shifts)} shifts in {date_range} days without sufficient rest"
                        alert = BurnoutAlert(
                            UserId=user_id,
                            AlertType=alert_type,
                            Severity='medium',
                            AlertMessage=message,
                            Description="Extended work period without adequate recovery time",
                            IsResolved=False
                        )
                        alerts.append(alert)
        
        return alerts
    
    @staticmethod
    def get_active_alerts(user_id: int, limit: int = 10) -> List[BurnoutAlert]:
        """
        Get active (unresolved) alerts for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of alerts to return
        
        Returns:
            List of active BurnoutAlert objects, sorted by severity and date
        """
        alerts = BurnoutAlert.query.filter(
            BurnoutAlert.UserId == user_id,
            BurnoutAlert.IsResolved == False
        ).order_by(
            # Order by severity (critical first) then by creation date
            db.case(
                (BurnoutAlert.Severity == 'critical', 1),
                (BurnoutAlert.Severity == 'high', 2),
                (BurnoutAlert.Severity == 'medium', 3),
                (BurnoutAlert.Severity == 'low', 4),
                else_=5
            ),
            BurnoutAlert.CreatedAt.desc()
        ).limit(limit).all()
        
        return alerts
    
    @staticmethod
    def resolve_alert(alert_id: int, resolved_by: Optional[int] = None, 
                     resolution_note: Optional[str] = None,
                     resolution_action: Optional[str] = None) -> bool:
        """
        Mark an alert as resolved with optional action
        
        Args:
            alert_id: Alert ID to resolve
            resolved_by: Optional user ID who resolved it
            resolution_note: Optional note explaining resolution
            resolution_action: Optional action taken ('acknowledged', 'time_off_requested', etc.)
        
        Returns:
            True if successful, False if alert not found
        """
        alert = BurnoutAlert.query.get(alert_id)
        
        if not alert:
            return False
        
        alert.IsResolved = True
        alert.ResolvedAt = datetime.utcnow()
        if hasattr(alert, 'ResolvedBy'):
            alert.ResolvedBy = resolved_by
        if hasattr(alert, 'ResolutionNote'):
            alert.ResolutionNote = resolution_note
        if hasattr(alert, 'ResolutionAction'):
            alert.ResolutionAction = resolution_action or 'acknowledged'
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_alert_summary(user_id: int) -> Dict[str, Any]:
        """
        Get summary of alerts for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with alert counts by severity and type
        """
        # Count active alerts by severity
        severity_counts = db.session.query(
            BurnoutAlert.Severity,
            func.count(BurnoutAlert.AlertId)
        ).filter(
            BurnoutAlert.UserId == user_id,
            BurnoutAlert.IsResolved == False
        ).group_by(BurnoutAlert.Severity).all()
        
        # Count active alerts by type
        type_counts = db.session.query(
            BurnoutAlert.AlertType,
            func.count(BurnoutAlert.AlertId)
        ).filter(
            BurnoutAlert.UserId == user_id,
            BurnoutAlert.IsResolved == False
        ).group_by(BurnoutAlert.AlertType).all()
        
        return {
            'total_active': sum(count for _, count in severity_counts),
            'by_severity': {severity: count for severity, count in severity_counts},
            'by_type': {alert_type: count for alert_type, count in type_counts},
            'has_critical': any(severity == 'critical' for severity, _ in severity_counts),
            'has_high': any(severity == 'high' for severity, _ in severity_counts)
        }
