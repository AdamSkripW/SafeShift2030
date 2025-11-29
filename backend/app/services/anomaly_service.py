"""
Anomaly Detection Service - Identify unusual patterns in shift data
Detects: consecutive nights, chronic low sleep, rising stress, frequent high-risk shifts
"""

from datetime import timedelta, date
from sqlalchemy import and_
from app.models import Shift


class AnomalyService:
    """Detect anomalies in user's shift patterns"""
    
    @staticmethod
    def detect_anomalies(user_id):
        """
        Detect anomalies in user's recent shifts
        
        Args:
            user_id: User ID to analyze
        
        Returns:
            List of anomalies with type, severity, and description
        """
        
        anomalies = []
        
        # Get last 14 days of shifts
        start_date = date.today() - timedelta(days=14)
        
        shifts = Shift.query.filter(
            and_(
                Shift.UserId == user_id,
                Shift.ShiftDate >= start_date
            )
        ).order_by(Shift.ShiftDate.asc()).all()
        
        if len(shifts) < 2:
            return anomalies
        
        # ============================================
        # Anomaly 1: Consecutive Night Shifts
        # ============================================
        
        consecutive_nights = 0
        for shift in shifts:
            if shift.ShiftType == 'night':
                consecutive_nights += 1
            else:
                if consecutive_nights >= 3:
                    anomalies.append({
                        'type': 'consecutive_nights',
                        'severity': 'high' if consecutive_nights >= 5 else 'medium',
                        'count': consecutive_nights,
                        'description': f'You had {consecutive_nights} consecutive night shifts. This significantly increases fatigue risk.'
                    })
                consecutive_nights = 0
        
        # Check last sequence
        if consecutive_nights >= 3:
            anomalies.append({
                'type': 'consecutive_nights',
                'severity': 'high' if consecutive_nights >= 5 else 'medium',
                'count': consecutive_nights,
                'description': f'You have {consecutive_nights} consecutive night shifts (ongoing). Consider requesting a day shift soon.'
            })
        
        # ============================================
        # Anomaly 2: Chronic Low Sleep
        # ============================================
        
        avg_sleep = sum(s.HoursSleptBefore for s in shifts) / len(shifts)
        
        if avg_sleep < 5:
            anomalies.append({
                'type': 'chronic_low_sleep',
                'severity': 'high',
                'average': round(avg_sleep, 1),
                'description': f'Your average sleep is only {avg_sleep:.1f}h over the last 2 weeks. This is significantly below recommended 7-8h and greatly increases error risk.'
            })
        elif avg_sleep < 6:
            anomalies.append({
                'type': 'chronic_low_sleep',
                'severity': 'medium',
                'average': round(avg_sleep, 1),
                'description': f'Your average sleep is {avg_sleep:.1f}h. Try to increase it to at least 7 hours.'
            })
        
        # ============================================
        # Anomaly 3: Rising Stress Trend
        # ============================================
        
        if len(shifts) >= 5:
            first_half = [s.StressLevel for s in shifts[:len(shifts)//2]]
            second_half = [s.StressLevel for s in shifts[len(shifts)//2:]]
            
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            
            if avg_second > avg_first + 2:
                anomalies.append({
                    'type': 'rising_stress',
                    'severity': 'high',
                    'first_half_avg': round(avg_first, 1),
                    'second_half_avg': round(avg_second, 1),
                    'description': f'Your stress is rising: {avg_first:.1f} → {avg_second:.1f}. This is concerning. Take proactive steps now.'
                })
        
        # ============================================
        # Anomaly 4: High Index Frequency
        # ============================================
        
        red_zone_count = sum(1 for s in shifts if s.Zone == 'red')
        yellow_zone_count = sum(1 for s in shifts if s.Zone == 'yellow')
        
        if red_zone_count >= 4:
            anomalies.append({
                'type': 'frequent_red_zone',
                'severity': 'high',
                'red_count': red_zone_count,
                'total_shifts': len(shifts),
                'description': f'{red_zone_count} out of {len(shifts)} shifts were in RED zone. Your burnout risk is critically high.'
            })
        elif yellow_zone_count + red_zone_count >= len(shifts) * 0.7:
            anomalies.append({
                'type': 'frequent_high_risk',
                'severity': 'medium',
                'high_risk_count': yellow_zone_count + red_zone_count,
                'total_shifts': len(shifts),
                'description': f'{yellow_zone_count + red_zone_count} out of {len(shifts)} shifts were in YELLOW or RED zone. Your fatigue is chronic.'
            })
        
        # ============================================
        # Anomaly 5: Single Very Bad Shift
        # ============================================
        
        if shifts and shifts[-1].SafeShiftIndex >= 85:
            anomalies.append({
                'type': 'extreme_single_shift',
                'severity': 'high',
                'index': shifts[-1].SafeShiftIndex,
                'description': f'Your most recent shift had an extreme SafeShift Index of {shifts[-1].SafeShiftIndex}. Immediate recovery is critical.'
            })
        
        return anomalies
