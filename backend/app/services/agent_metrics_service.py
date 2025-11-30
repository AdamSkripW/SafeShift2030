"""
Agent Metrics Service
Analytics and monitoring functions for AI agent performance
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy import func, and_

from app.models import db, AgentMetric, User


class AgentMetricsService:
    """Service layer for agent metrics analytics"""
    
    @staticmethod
    def get_agent_stats(agent_name: Optional[str] = None, days: int = 7) -> Dict:
        """
        Get usage statistics for AI agents
        
        Args:
            agent_name: Filter by specific agent (None = all agents)
            days: Number of days to look back
        
        Returns:
            {
                "total_calls": int,
                "success_rate": float,
                "avg_latency_ms": float,
                "total_tokens": int,
                "crisis_detections": int,
                "avg_confidence": float,
                "severity_breakdown": {...},
                "cost_estimate_usd": float
            }
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = AgentMetric.query.filter(AgentMetric.CreatedAt >= cutoff)
        if agent_name:
            query = query.filter(AgentMetric.AgentName == agent_name)
        
        metrics = query.all()
        
        if not metrics:
            return {
                "total_calls": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0,
                "total_tokens": 0,
                "crisis_detections": 0,
                "avg_confidence": 0.0,
                "severity_breakdown": {},
                "cost_estimate_usd": 0.0
            }
        
        total_calls = len(metrics)
        successful_calls = sum(1 for m in metrics if m.Success)
        total_input_tokens = sum(m.InputTokens or 0 for m in metrics)
        total_output_tokens = sum(m.OutputTokens or 0 for m in metrics)
        
        # gpt-4o-mini pricing: $0.15/1M input, $0.60/1M output tokens
        cost_usd = (total_input_tokens * 0.15 / 1_000_000) + \
                   (total_output_tokens * 0.60 / 1_000_000)
        
        return {
            "total_calls": total_calls,
            "success_rate": round(successful_calls / total_calls, 3) if total_calls > 0 else 0.0,
            "avg_latency_ms": round(sum(m.LatencyMs or 0 for m in metrics) / total_calls) if total_calls > 0 else 0,
            "total_tokens": total_input_tokens + total_output_tokens,
            "crisis_detections": sum(1 for m in metrics if m.CrisisDetected),
            "avg_confidence": round(sum(m.ConfidenceScore or 0 for m in metrics) / total_calls, 2) if total_calls > 0 else 0.0,
            "severity_breakdown": {
                "critical": sum(1 for m in metrics if m.Severity == 'critical'),
                "high": sum(1 for m in metrics if m.Severity == 'high'),
                "medium": sum(1 for m in metrics if m.Severity == 'medium'),
                "low": sum(1 for m in metrics if m.Severity == 'low'),
                "none": sum(1 for m in metrics if m.Severity == 'none')
            },
            "cost_estimate_usd": round(cost_usd, 4),
            "period_days": days
        }
    
    @staticmethod
    def get_daily_crisis_rate(days: int = 7) -> List[Dict]:
        """
        Get daily crisis detection statistics
        
        Returns:
            [
                {
                    "date": "2025-11-30",
                    "total_analyses": int,
                    "crises_detected": int,
                    "critical_cases": int,
                    "escalations": int,
                    "crisis_rate": float
                },
                ...
            ]
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        results = db.session.query(
            func.date(AgentMetric.CreatedAt).label('date'),
            func.count(AgentMetric.MetricId).label('total'),
            func.sum(AgentMetric.CrisisDetected.cast(db.Integer)).label('crises'),
            func.sum((AgentMetric.Severity == 'critical').cast(db.Integer)).label('critical'),
            func.sum(AgentMetric.EscalationNeeded.cast(db.Integer)).label('escalations')
        ).filter(
            and_(
                AgentMetric.AgentName == 'CrisisDetectionAgent',
                AgentMetric.CreatedAt >= cutoff
            )
        ).group_by(func.date(AgentMetric.CreatedAt)).all()
        
        return [
            {
                "date": row.date.isoformat() if row.date else None,
                "total_analyses": row.total or 0,
                "crises_detected": row.crises or 0,
                "critical_cases": row.critical or 0,
                "escalations": row.escalations or 0,
                "crisis_rate": round((row.crises or 0) / row.total, 3) if row.total > 0 else 0.0
            }
            for row in results
        ]
    
    @staticmethod
    def get_user_crisis_history(user_id: int, days: int = 30) -> Dict:
        """
        Get crisis detection history for specific user
        
        Returns:
            {
                "user_id": int,
                "total_analyses": int,
                "crises_detected": int,
                "highest_severity": str,
                "last_analysis": datetime,
                "recent_severities": [str]
            }
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        metrics = AgentMetric.query.filter(
            and_(
                AgentMetric.UserId == user_id,
                AgentMetric.AgentName == 'CrisisDetectionAgent',
                AgentMetric.CreatedAt >= cutoff
            )
        ).order_by(AgentMetric.CreatedAt.desc()).all()
        
        if not metrics:
            return {
                "user_id": user_id,
                "total_analyses": 0,
                "crises_detected": 0,
                "highest_severity": None,
                "last_analysis": None,
                "recent_severities": []
            }
        
        # Severity ranking for comparison
        severity_rank = {'none': 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        highest = max(metrics, key=lambda m: severity_rank.get(m.Severity or 'none', 0))
        
        return {
            "user_id": user_id,
            "total_analyses": len(metrics),
            "crises_detected": sum(1 for m in metrics if m.CrisisDetected),
            "highest_severity": highest.Severity,
            "last_analysis": metrics[0].CreatedAt.isoformat() if metrics[0].CreatedAt else None,
            "recent_severities": [m.Severity for m in metrics[:5] if m.Severity]
        }
    
    @staticmethod
    def get_performance_issues(threshold_ms: int = 5000) -> List[Dict]:
        """
        Find slow or failed agent calls for debugging
        
        Args:
            threshold_ms: Consider calls slower than this as issues
        
        Returns:
            [
                {
                    "metric_id": int,
                    "agent_name": str,
                    "latency_ms": int,
                    "success": bool,
                    "error": str,
                    "created_at": datetime
                },
                ...
            ]
        """
        issues = AgentMetric.query.filter(
            db.or_(
                AgentMetric.Success == False,
                AgentMetric.LatencyMs > threshold_ms
            )
        ).order_by(AgentMetric.CreatedAt.desc()).limit(50).all()
        
        return [
            {
                "metric_id": m.MetricId,
                "agent_name": m.AgentName,
                "latency_ms": m.LatencyMs,
                "success": m.Success,
                "error": m.ErrorMessage,
                "created_at": m.CreatedAt.isoformat() if m.CreatedAt else None
            }
            for m in issues
        ]
    
    @staticmethod
    def get_high_risk_users(days: int = 7, min_alerts: int = 2) -> List[Dict]:
        """
        Identify users with repeated crisis detections
        
        Returns:
            [
                {
                    "user_id": int,
                    "first_name": str,
                    "last_name": str,
                    "crisis_count": int,
                    "latest_severity": str,
                    "latest_analysis": datetime
                },
                ...
            ]
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        results = db.session.query(
            User.UserId,
            User.FirstName,
            User.LastName,
            func.count(AgentMetric.MetricId).label('crisis_count'),
            func.max(AgentMetric.Severity).label('max_severity'),
            func.max(AgentMetric.CreatedAt).label('latest')
        ).join(
            AgentMetric, AgentMetric.UserId == User.UserId
        ).filter(
            and_(
                AgentMetric.CrisisDetected == True,
                AgentMetric.CreatedAt >= cutoff
            )
        ).group_by(
            User.UserId, User.FirstName, User.LastName
        ).having(
            func.count(AgentMetric.MetricId) >= min_alerts
        ).order_by(
            func.count(AgentMetric.MetricId).desc()
        ).all()
        
        return [
            {
                "user_id": r.UserId,
                "first_name": r.FirstName,
                "last_name": r.LastName,
                "crisis_count": r.crisis_count,
                "latest_severity": r.max_severity,
                "latest_analysis": r.latest.isoformat() if r.latest else None
            }
            for r in results
        ]
