"""
Prediction Service - Burnout risk prediction using trend analysis
Predicts future burnout risk based on last 30 days of shift data
"""

from datetime import timedelta, date
from sqlalchemy import and_
import statistics
from app.models import Shift


class PredictionService:
    """Predict future burnout risk based on trends"""
    
    @staticmethod
    def predict_burnout_risk(user_id, days_ahead=14):
        """
        Predict burnout risk for next N days using linear regression
        
        Args:
            user_id: User ID to analyze
            days_ahead: Number of days to predict ahead (default: 14)
        
        Returns:
            dict: Prediction data including risk level, confidence, reasoning
        """
        
        # Get last 30 days of shifts
        start_date = date.today() - timedelta(days=30)
        
        shifts = Shift.query.filter(
            and_(
                Shift.UserId == user_id,
                Shift.ShiftDate >= start_date
            )
        ).order_by(Shift.ShiftDate.asc()).all()
        
        if len(shifts) < 3:
            return {
                'prediction': 'insufficient_data',
                'predicted_index': None,
                'confidence': 0,
                'days_until_critical': None,
                'reasoning': 'Not enough data to predict. Please log more shifts.'
            }
        
        # Calculate trend using linear regression
        indices = [s.SafeShiftIndex for s in shifts]
        
        # Simple linear regression
        n = len(indices)
        x = list(range(n))
        y = indices
        
        # Calculate slope (trend)
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Predict next value
        last_index = indices[-1]
        predicted_index = last_index + (slope * (days_ahead / len(shifts)))
        predicted_index = max(0, min(100, predicted_index))
        
        # ============================================
        # Determine Risk Level
        # ============================================
        
        if predicted_index >= 70:
            prediction = 'high_risk'
        elif predicted_index >= 50:
            prediction = 'medium_risk'
        else:
            prediction = 'low_risk'
        
        # ============================================
        # Calculate Days Until Critical (70+)
        # ============================================
        
        days_until_critical = None
        if slope > 0:
            if last_index < 70:
                days_needed = (70 - last_index) / (slope / len(shifts))
                days_until_critical = max(1, int(days_needed))
        
        # ============================================
        # Calculate Confidence
        # ============================================
        
        std_dev = statistics.stdev(indices) if len(indices) > 1 else 0
        confidence = 1.0 - (std_dev / 100)
        confidence = max(0.3, min(1.0, confidence))
        
        # ============================================
        # Generate Reasoning
        # ============================================
        
        if slope > 0.5:
            trend_desc = "rising (getting worse)"
        elif slope < -0.5:
            trend_desc = "falling (improving)"
        else:
            trend_desc = "stable"
        
        recent_avg = sum(indices[-7:]) / min(7, len(indices[-7:]))
        
        reasoning = f"Your SafeShift Index is {trend_desc}. Recent average: {recent_avg:.0f}. Predicted in {days_ahead} days: {predicted_index:.0f}."
        
        return {
            'prediction': prediction,
            'predicted_index': int(predicted_index),
            'confidence': round(confidence, 2),
            'days_until_critical': days_until_critical,
            'reasoning': reasoning,
            'slope': round(slope, 3),
            'current_index': last_index,
            'last_30_days_avg': round(sum(indices) / len(indices), 1)
        }
