"""
Admin Dashboard Service
Manage staff wellness, make interventions, analyze department
"""

from datetime import timedelta, date
from sqlalchemy import and_
import statistics

class AdminService:
    
    @staticmethod
    def get_staff_overview(db, User, Shift, department=None):
        """
        Get overview of all staff (or department)
        
        Returns list of staff with their current status
        """
        
        # Get staff
        if department:
            staff = db.session.query(User).filter_by(Department=department).all()
        else:
            staff = db.session.query(User).filter_by(IsActive=True).all()
        
        if not staff:
            return []
        
        start_date = date.today() - timedelta(days=14)
        
        staff_data = []
        for person in staff:
            shifts = db.session.query(Shift).filter(
                and_(
                    Shift.UserId == person.UserId,
                    Shift.ShiftDate >= start_date
                )
            ).order_by(Shift.ShiftDate.desc()).all()
            
            if not shifts:
                continue
            
            recent_index = shifts[0].SafeShiftIndex if shifts else 0
            recent_zone = shifts[0].Zone if shifts else 'green'
            avg_index = statistics.mean([s.SafeShiftIndex for s in shifts])
            
            # Determine alert level
            if recent_index >= 80:
                alert_level = 'CRITICAL'
                alert_color = 'red'
            elif recent_index >= 65:
                alert_level = 'WARNING'
                alert_color = 'orange'
            elif recent_index >= 50:
                alert_level = 'CAUTION'
                alert_color = 'yellow'
            else:
                alert_level = 'OK'
                alert_color = 'green'
            
            staff_data.append({
                'userId': person.UserId,
                'name': f"{person.FirstName} {person.LastName}",
                'email': person.Email,
                'role': person.Role,
                'department': person.Department,
                'recentIndex': recent_index,
                'recentZone': recent_zone,
                'averageIndex': round(avg_index, 1),
                'shiftsLogged': len(shifts),
                'alertLevel': alert_level,
                'alertColor': alert_color,
                'lastShift': shifts[0].ShiftDate.isoformat() if shifts else None
            })
        
        # Sort by alert level (CRITICAL first)
        priority_map = {'CRITICAL': 0, 'WARNING': 1, 'CAUTION': 2, 'OK': 3}
        staff_data.sort(key=lambda x: priority_map.get(x['alertLevel'], 4))
        
        return staff_data
    
    @staticmethod
    def get_staff_detail(db, User, Shift, user_id, llm_service):
        """
        Get detailed profile of one staff member with AI recommendations
        """
        
        user = db.session.query(User).filter_by(UserId=user_id).first()
        if not user:
            return {'error': 'User not found'}
        
        start_date = date.today() - timedelta(days=30)
        shifts = db.session.query(Shift).filter(
            and_(
                Shift.UserId == user_id,
                Shift.ShiftDate >= start_date
            )
        ).order_by(Shift.ShiftDate.desc()).all()
        
        if not shifts:
            return {
                'userId': user_id,
                'name': f"{user.FirstName} {user.LastName}",
                'noData': True
            }
        
        indices = [s.SafeShiftIndex for s in shifts]
        stress = [s.StressLevel for s in shifts]
        sleep = [s.HoursSleptBefore for s in shifts]
        
        # ⭐ AI RECOMMENDATION
        prompt = f"""You are an HR manager. Analyze this staff member and provide recommendations.

Staff Member: {user.FirstName} {user.LastName}
Role: {user.Role}
Department: {user.Department}

Recent Shifts (last 30 days): {len(shifts)}
SafeShift Index:
- Latest: {indices[0]}
- Average: {statistics.mean(indices):.0f}
- Trend: {"↑ Rising" if indices[0] > statistics.mean(indices) else "↓ Falling"}

Stress Levels: {statistics.mean(stress):.1f}/10 average
Sleep Hours: {statistics.mean(sleep):.1f}h average

Specific Patterns:
- Consecutive night shifts: {AdminService._count_consecutive_nights(shifts)}
- Red zone shifts: {sum(1 for s in shifts if s.Zone == 'red')} of {len(shifts)}
- Average workload: {statistics.mean([s.PatientsCount for s in shifts]):.0f} patients

TASK:
1. Assess their burnout risk (CRITICAL/HIGH/MEDIUM/LOW)
2. Recommend specific action (e.g., "Grant 2 days off", "Reduce night shifts", "Monitor closely")
3. Urgency (IMMEDIATE/THIS_WEEK/THIS_MONTH)
4. Estimated recovery time in days (if intervention taken)

Return SHORT and ACTIONABLE recommendations.
Focus on PROTECTING both staff AND patient safety.
"""
        
        try:
            response = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=[
                    {"role": "system", "content": "You are an empathetic HR manager focused on staff wellness and patient safety."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            ai_recommendation = response.choices[0].message.content
        except Exception as e:
            ai_recommendation = f"Unable to generate recommendation: {str(e)}"
        
        return {
            'userId': user_id,
            'name': f"{user.FirstName} {user.LastName}",
            'email': user.Email,
            'role': user.Role,
            'department': user.Department,
            'stats': {
                'shiftsLogged': len(shifts),
                'averageIndex': round(statistics.mean(indices), 1),
                'averageStress': round(statistics.mean(stress), 1),
                'averageSleep': round(statistics.mean(sleep), 1),
                'recentIndex': indices[0],
                'trend': 'Rising ↑' if indices[0] > statistics.mean(indices) else 'Falling ↓'
            },
            'shifts': [{
                'date': s.ShiftDate.isoformat(),
                'type': s.ShiftType,
                'hours': s.ShiftLengthHours,
                'patients': s.PatientsCount,
                'stress': s.StressLevel,
                'index': s.SafeShiftIndex,
                'zone': s.Zone
            } for s in shifts[:10]],
            'aiRecommendation': ai_recommendation
        }
    
    @staticmethod
    def _count_consecutive_nights(shifts):
        """Count consecutive night shifts"""
        max_consecutive = 0
        current_consecutive = 0
        
        for shift in reversed(shifts):
            if shift.ShiftType == 'night':
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    @staticmethod
    def get_critical_alerts(db, User, Shift, department=None):
        """
        Get all critical alerts that need immediate attention
        """
        
        staff = AdminService.get_staff_overview(db, User, Shift, department)
        
        alerts = []
        
        for person in staff:
            if person['alertLevel'] == 'CRITICAL':
                alerts.append({
                    'severity': 'CRITICAL',
                    'staffId': person['userId'],
                    'staffName': person['name'],
                    'message': f"{person['name']} has SafeShift Index {person['recentIndex']} (CRITICAL)",
                    'action': 'Immediate intervention needed',
                    'timestamp': date.today().isoformat()
                })
            elif person['alertLevel'] == 'WARNING':
                alerts.append({
                    'severity': 'WARNING',
                    'staffId': person['userId'],
                    'staffName': person['name'],
                    'message': f"{person['name']} has SafeShift Index {person['recentIndex']} (WARNING)",
                    'action': 'Monitor and consider intervention',
                    'timestamp': date.today().isoformat()
                })
        
        return sorted(alerts, key=lambda x: {'CRITICAL': 0, 'WARNING': 1}.get(x['severity'], 2))
    
    @staticmethod
    def generate_intervention_suggestion(db, User, Shift, user_id, llm_service):
        """
        Generate specific intervention suggestion for a staff member
        """
        
        detail = AdminService.get_staff_detail(db, User, Shift, user_id, llm_service)
        
        if 'noData' in detail:
            return {'suggestion': 'Not enough data to generate recommendation'}
        
        user = db.session.query(User).filter_by(UserId=user_id).first()
        
        prompt = f"""Based on this staff member's profile, suggest a SPECIFIC intervention.

{detail['aiRecommendation']}

POSSIBLE INTERVENTIONS:
1. Grant time off (how many days?)
2. Reduce night shifts (for how long?)
3. Reassign to less demanding ward
4. Schedule wellness appointment
5. Pair with mentor/support person
6. Temporary schedule modification

Choose the MOST EFFECTIVE intervention and explain WHY and WHEN to implement it.
Keep response SHORT and CLEAR for manager to understand and execute.
"""
        
        try:
            response = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=[
                    {"role": "system", "content": "You are an HR expert recommending workplace interventions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
            suggestion = response.choices[0].message.content
        except:
            suggestion = "Unable to generate suggestion at this time"
        
        return {
            'staffId': user_id,
            'staffName': f"{user.FirstName} {user.LastName}",
            'suggestion': suggestion
        }
