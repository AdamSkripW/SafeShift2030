from flask import Blueprint, jsonify, request
from app.models import db, User, Hospital, HospitalAdmin, Shift, TimeOffRequest, BurnoutAlert, Session, ChatLog
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

# Import services
from app.services import (
    SafeShiftService,
    AnomalyService,
    LLMService,
    CrisisDetectionAgent,
    MicroBreakCoachAgent,
    PatientSafetyCorrelationAgent,
    EmotionClassifierAgent,
    InsightComposerAgent,
    AgentMetricsService,
    AgentOrchestrator,
    ChatService
    AlertManagerService
)
from app.services.voice_service import VoiceService

# Initialize AI agents lazily to ensure environment variables are loaded
_crisis_agent = None
_micro_break_agent = None
_patient_safety_agent = None
_emotion_agent = None
_insight_agent = None
_orchestrator = None

def get_crisis_agent():
    global _crisis_agent
    if _crisis_agent is None:
        _crisis_agent = CrisisDetectionAgent()
    return _crisis_agent

def get_micro_break_agent():
    global _micro_break_agent
    if _micro_break_agent is None:
        _micro_break_agent = MicroBreakCoachAgent()
    return _micro_break_agent

def get_patient_safety_agent():
    global _patient_safety_agent
    if _patient_safety_agent is None:
        _patient_safety_agent = PatientSafetyCorrelationAgent()
    return _patient_safety_agent

def get_emotion_agent():
    global _emotion_agent
    if _emotion_agent is None:
        _emotion_agent = EmotionClassifierAgent()
    return _emotion_agent

def get_insight_agent():
    global _insight_agent
    if _insight_agent is None:
        _insight_agent = InsightComposerAgent()
    return _insight_agent

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)

# ============================================
# HELPER FUNCTIONS FOR CRISIS DETECTION
# ============================================
def _get_recent_shift_zones(user_id, limit=3):
    """Get recent shift zones for pattern detection"""
    recent_shifts = Shift.query.filter_by(UserId=user_id)\
        .order_by(Shift.ShiftDate.desc())\
        .limit(limit)\
        .all()
    return [s.Zone for s in recent_shifts if s.Zone]

def _get_stress_history(user_id, limit=5):
    """Get recent stress levels"""
    recent_shifts = Shift.query.filter_by(UserId=user_id)\
        .order_by(Shift.ShiftDate.desc())\
        .limit(limit)\
        .all()
    return [s.StressLevel for s in recent_shifts]

def _count_unresolved_alerts(user_id):
    """Count unresolved burnout alerts"""
    return BurnoutAlert.query.filter_by(UserId=user_id, IsResolved=False).count()

def _count_consecutive_shifts(user_id, days=7):
    """Count consecutive shifts in last N days"""
    cutoff_date = datetime.utcnow().date() - timedelta(days=days)
    shifts = Shift.query.filter(
        Shift.UserId == user_id,
        Shift.ShiftDate >= cutoff_date
    ).order_by(Shift.ShiftDate.desc()).all()
    
    if not shifts:
        return 0
    
    consecutive_count = 1
    for i in range(len(shifts) - 1):
        delta = (shifts[i].ShiftDate - shifts[i+1].ShiftDate).days
        if delta == 1:
            consecutive_count += 1
        else:
            break
    return consecutive_count

def _count_red_zone_shifts(user_id, limit=10):
    """Count red zone shifts in recent history"""
    red_shifts = Shift.query.filter_by(UserId=user_id, Zone='red')\
        .order_by(Shift.ShiftDate.desc())\
        .limit(limit)\
        .all()
    return len(red_shifts)

def _calculate_sleep_deficit(user_id, target_hours=7, limit=5):
    """Calculate cumulative sleep deficit from recent shifts"""
    recent_shifts = Shift.query.filter_by(UserId=user_id)\
        .order_by(Shift.ShiftDate.desc())\
        .limit(limit)\
        .all()
    
    if not recent_shifts:
        return 0
    
    total_deficit = sum(max(0, target_hours - s.HoursSleptBefore) for s in recent_shifts)
    return total_deficit

def _calculate_avg_shift_hours(user_id, limit=10):
    """Calculate average shift length hours"""
    recent_shifts = Shift.query.filter_by(UserId=user_id)\
        .order_by(Shift.ShiftDate.desc())\
        .limit(limit)\
        .all()
    
    if not recent_shifts:
        return 8  # Default
    
    total_hours = sum(s.ShiftLengthHours for s in recent_shifts)
    return total_hours / len(recent_shifts)

def _calculate_days_since_break(user_id):
    """Calculate days since last day off (no shift)"""
    # Get last 14 days of shifts
    cutoff_date = datetime.utcnow().date() - timedelta(days=14)
    shifts = Shift.query.filter(
        Shift.UserId == user_id,
        Shift.ShiftDate >= cutoff_date
    ).order_by(Shift.ShiftDate.desc()).all()
    
    if not shifts:
        return 0
    
    # Find first gap in consecutive days
    for i in range(len(shifts) - 1):
        delta = (shifts[i].ShiftDate - shifts[i+1].ShiftDate).days
        if delta > 1:
            # Found a gap (day off)
            return (datetime.utcnow().date() - shifts[i].ShiftDate).days
    
    # No gap found - been working consecutively
    return (datetime.utcnow().date() - shifts[-1].ShiftDate).days if shifts else 0

# Main routes
@main_bp.route('/')
def index():
    return jsonify({
        'message': 'Welcome to SafeShift 2030 API',
        'version': '1.0',
        'endpoints': {
            'health': '/api/health',
            'auth': {
                'register': '/api/auth/register',
                'login': '/api/auth/login',
                'logout': '/api/auth/logout',
                'refresh': '/api/auth/refresh',
                'me': '/api/auth/me'
            },
            'hospitals': '/api/hospitals',
            'users': '/api/users',
            'admins': '/api/admins',
            'shifts': '/api/shifts',
            'timeoff': '/api/timeoff',
            'alerts': '/api/alerts',
            'sessions': '/api/sessions',
            'agents': {
                'metrics': '/api/agents/metrics',
                'crisis_rate': '/api/agents/metrics/crisis-rate',
                'user_history': '/api/agents/metrics/user/<user_id>',
                'performance_issues': '/api/agents/metrics/performance-issues',
                'high_risk_users': '/api/agents/metrics/high-risk-users',
                'micro_break': '/api/agents/micro-break'
            }
        }
    })

# API routes
@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok', 
        'message': 'Backend is running',
        'database': 'connected'
    })

# ============================================
# HOSPITAL ENDPOINTS
# ============================================
@api_bp.route('/hospitals', methods=['GET'])
def get_hospitals():
    """Get all hospitals"""
    try:
        hospitals = Hospital.query.all()
        print(hospitals)
        return jsonify({
            'success': True,
            'data': [h.to_dict() for h in hospitals],
            'count': len(hospitals)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/hospitals/<int:hospital_id>', methods=['GET'])
def get_hospital(hospital_id):
    """Get a specific hospital"""
    try:
        hospital = Hospital.query.get_or_404(hospital_id)
        return jsonify({'success': True, 'data': hospital.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@api_bp.route('/hospitals', methods=['POST'])
def create_hospital():
    """Create a new hospital"""
    try:
        data = request.get_json()
        
        if not data or not data.get('Name') or not data.get('City') or not data.get('Country'):
            return jsonify({'success': False, 'error': 'Name, City, and Country are required'}), 400
        
        if Hospital.query.filter_by(Name=data['Name']).first():
            return jsonify({'success': False, 'error': 'Hospital with this name already exists'}), 400
        
        hospital = Hospital(
            Name=data['Name'],
            City=data['City'],
            Country=data['Country'],
            ContactEmail=data.get('ContactEmail'),
            PhoneNumber=data.get('PhoneNumber')
        )
        
        db.session.add(hospital)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Hospital created successfully',
            'data': hospital.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/hospitals/<int:hospital_id>', methods=['PUT'])
def update_hospital(hospital_id):
    """Update a hospital"""
    try:
        hospital = Hospital.query.get_or_404(hospital_id)
        data = request.get_json()
        
        if data.get('Name'):
            hospital.Name = data['Name']
        if data.get('City'):
            hospital.City = data['City']
        if data.get('Country'):
            hospital.Country = data['Country']
        if 'ContactEmail' in data:
            hospital.ContactEmail = data['ContactEmail']
        if 'PhoneNumber' in data:
            hospital.PhoneNumber = data['PhoneNumber']
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Hospital updated successfully',
            'data': hospital.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/hospitals/<int:hospital_id>', methods=['DELETE'])
def delete_hospital(hospital_id):
    """Delete a hospital"""
    try:
        hospital = Hospital.query.get_or_404(hospital_id)
        db.session.delete(hospital)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Hospital deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# USER ENDPOINTS
# ============================================
@api_bp.route('/users', methods=['GET'])
def get_users():
    """Get all users"""
    try:
        users = User.query.all()
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users],
            'count': len(users)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user"""
    try:
        user = User.query.get_or_404(user_id)
        return jsonify({'success': True, 'data': user.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@api_bp.route('/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        required = ['Email', 'Password', 'FirstName', 'LastName', 'Role', 'Department', 'Hospital']
        if not data or not all(data.get(field) for field in required):
            return jsonify({'success': False, 'error': f'Required fields: {", ".join(required)}'}), 400
        
        if User.query.filter_by(Email=data['Email']).first():
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        # Hash the password before storing
        hashed_password = generate_password_hash(data['Password'], method='pbkdf2:sha256')
        
        user = User(
            Email=data['Email'],
            PasswordHash=hashed_password,
            FirstName=data['FirstName'],
            LastName=data['LastName'],
            Role=data['Role'],
            Department=data['Department'],
            Hospital=data['Hospital'],
            HospitalId=data.get('HospitalId'),
            ProfilePictureUrl=data.get('ProfilePictureUrl'),
            IsActive=data.get('IsActive', True)
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'data': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update a user"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Handle password update separately to hash it
        if 'Password' in data:
            user.PasswordHash = generate_password_hash(data['Password'], method='pbkdf2:sha256')
        
        updatable = ['Email', 'FirstName', 'LastName', 'Role', 'Department', 'Hospital', 
                     'HospitalId', 'ProfilePictureUrl', 'IsActive']
        for field in updatable:
            if field in data:
                setattr(user, field, data[field])
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'data': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# HOSPITAL ADMIN ENDPOINTS
# ============================================
@api_bp.route('/admins', methods=['GET'])
def get_admins():
    """Get all hospital admins"""
    try:
        admins = HospitalAdmin.query.all()
        return jsonify({
            'success': True,
            'data': [a.to_dict() for a in admins],
            'count': len(admins)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/admins/<int:admin_id>', methods=['GET'])
def get_admin(admin_id):
    """Get a specific admin"""
    try:
        admin = HospitalAdmin.query.get_or_404(admin_id)
        return jsonify({'success': True, 'data': admin.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@api_bp.route('/admins', methods=['POST'])
def create_admin():
    """Create a new hospital admin"""
    try:
        data = request.get_json()
        
        if not data or not data.get('UserId') or not data.get('HospitalId') or not data.get('Role'):
            return jsonify({'success': False, 'error': 'UserId, HospitalId, and Role are required'}), 400
        
        admin = HospitalAdmin(
            UserId=data['UserId'],
            HospitalId=data['HospitalId'],
            Role=data['Role'],
            PermissionsViewAll=data.get('PermissionsViewAll', True),
            PermissionsEditShifts=data.get('PermissionsEditShifts', False),
            PermissionsAssignTimeOff=data.get('PermissionsAssignTimeOff', True)
        )
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Admin created successfully',
            'data': admin.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/admins/<int:admin_id>', methods=['PUT'])
def update_admin(admin_id):
    """Update a hospital admin"""
    try:
        admin = HospitalAdmin.query.get_or_404(admin_id)
        data = request.get_json()
        
        updatable = ['Role', 'PermissionsViewAll', 'PermissionsEditShifts', 'PermissionsAssignTimeOff']
        for field in updatable:
            if field in data:
                setattr(admin, field, data[field])
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Admin updated successfully',
            'data': admin.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/admins/<int:admin_id>', methods=['DELETE'])
def delete_admin(admin_id):
    """Delete a hospital admin"""
    try:
        admin = HospitalAdmin.query.get_or_404(admin_id)
        db.session.delete(admin)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Admin deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# SHIFT ENDPOINTS
# ============================================
@api_bp.route('/shifts', methods=['GET'])
def get_shifts():
    """Get all shifts"""
    # try:
    user_id = request.args.get('user_id')
    if user_id:
        shifts = Shift.query.filter_by(UserId=user_id).all()
    else:
        shifts = Shift.query.all()
    return jsonify({
        'success': True,
        'data': [s.to_dict() for s in shifts],
        'count': len(shifts)
    }), 200
    # except Exception as e:
        # return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/shifts/<int:shift_id>', methods=['GET'])
def get_shift(shift_id):
    """Get a specific shift"""
    try:
        shift = Shift.query.get_or_404(shift_id)
        return jsonify({'success': True, 'data': shift.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@api_bp.route('/shifts', methods=['POST'])
def create_shift():
    """Create a new shift"""
    try:
        data = request.get_json()
        
        required = ['UserId', 'ShiftDate', 'HoursSleptBefore', 'ShiftType', 
                    'ShiftLengthHours', 'PatientsCount', 'StressLevel']
        if not data or not all(field in data for field in required):
            return jsonify({'success': False, 'error': f'Required fields: {", ".join(required)}'}), 400
        
        # Parse date
        shift_date = datetime.strptime(data['ShiftDate'], '%Y-%m-%d').date()
        
        # Calculate SafeShift Index
        safe_shift_index, zone = SafeShiftService.calculate_index(
            hours_slept=data['HoursSleptBefore'],
            shift_type=data['ShiftType'],
            shift_length=data['ShiftLengthHours'],
            patients_count=data['PatientsCount'],
            stress_level=data['StressLevel']
        )
        
        # Generate AI insights for all shifts (optional)
        ai_explanation = None
        ai_tips = None
        try:
            insights = LLMService.generate_insights(
                shift_data={
                    'hours_slept': data['HoursSleptBefore'],
                    'shift_type': data['ShiftType'],
                    'shift_length': data['ShiftLengthHours'],
                    'patients_count': data['PatientsCount'],
                    'stress_level': data['StressLevel'],
                    'shift_note': data.get('ShiftNote', '')
                },
                index=safe_shift_index,
                zone=zone
            )
            ai_explanation = insights.get('explanation')
            ai_tips = insights.get('tips')
        except Exception as llm_error:
            # LLM is optional - continue without it
            print(f"LLM generation skipped: {llm_error}")
        
        shift = Shift(
            UserId=data['UserId'],
            ShiftDate=shift_date,
            HoursSleptBefore=data['HoursSleptBefore'],
            ShiftType=data['ShiftType'],
            ShiftLengthHours=data['ShiftLengthHours'],
            PatientsCount=data['PatientsCount'],
            StressLevel=data['StressLevel'],
            ShiftNote=data.get('ShiftNote'),
            SafeShiftIndex=safe_shift_index,
            Zone=zone,
            AiExplanation=ai_explanation,
            AiTips=ai_tips
        )
        
        db.session.add(shift)
        db.session.commit()
        
        # Run comprehensive orchestrated agent analysis
        agent_insights = None
        try:
            # Get user context
            user = User.query.get(data['UserId'])
            user_name = f"{user.FirstName} {user.LastName}" if user else None
            recent_zones = _get_recent_shift_zones(data['UserId'])
            stress_history = _get_stress_history(data['UserId'])
            previous_alerts = _count_unresolved_alerts(data['UserId'])
            
            # Calculate additional context
            consecutive_shifts = _count_consecutive_shifts(data['UserId'])
            red_zone_count = _count_red_zone_shifts(data['UserId'])
            sleep_deficit = _calculate_sleep_deficit(data['UserId'])
            avg_shift_hours = _calculate_avg_shift_hours(data['UserId'])
            days_since_break = _calculate_days_since_break(data['UserId'])
            
            # Build comprehensive shift context
            shift_context = {
                'user_id': data['UserId'],
                'shift_id': shift.ShiftId,
                'user_name': user_name,
                'safeshift_index': safe_shift_index,  # Fixed: orchestrator expects 'safeshift_index'
                'current_zone': zone,  # Fixed: orchestrator expects 'current_zone'
                'hours_slept': data['HoursSleptBefore'],
                'shift_type': data['ShiftType'],
                'shift_length': data['ShiftLengthHours'],
                'patients_count': data['PatientsCount'],
                'stress_level': data['StressLevel'],
                'shift_note': data.get('ShiftNote'),
                'consecutive_shifts': consecutive_shifts,
                'red_zone_count': red_zone_count,
                'sleep_deficit_hours': sleep_deficit,  # Fixed: was sleep_deficit
                'avg_shift_hours': avg_shift_hours,
                'days_since_break': days_since_break,
                'team_red_zone_count': 0,  # TODO: Calculate team metrics if needed
                'understaffing_percentage': 0,  # TODO: Calculate if staffing data available
                'recent_incidents': 0,  # TODO: Track incidents if implemented
                'recent_shifts': recent_zones,
                'stress_history': stress_history,
                'previous_alerts': previous_alerts
            }
            
            # Run orchestrated comprehensive analysis
            print(f"[ORCHESTRATION] Starting comprehensive analysis for shift {shift.ShiftId}...")
            print(f"[ORCHESTRATION] Context keys: {list(shift_context.keys())}")
            print(f"[ORCHESTRATION] Stress level: {shift_context['stress_level']}, Zone: {shift_context['current_zone']}")
            
            orchestration_result = get_orchestrator().generate_comprehensive_insight(
                shift_context=shift_context,
                user_id=data['UserId'],
                shift_id=shift.ShiftId,
                audience='both'
            )
            
            print(f"[ORCHESTRATION] Result keys: {list(orchestration_result.keys())}")
            print(f"[ORCHESTRATION] Has comprehensive_insight: {'comprehensive_insight' in orchestration_result}")
            print(f"[ORCHESTRATION] Agents run: {orchestration_result.get('agents_run', [])}")
            
            if orchestration_result.get('comprehensive_insight'):
                agent_insights = orchestration_result['comprehensive_insight']
                print(f"[ORCHESTRATION] ✓ Got insights with urgency: {agent_insights.get('urgency_level')}")
                
                # Save insights to shift record
                shift.AgentInsights = agent_insights
                db.session.commit()
                print(f"[ORCHESTRATION] ✓ Saved insights to database")
            else:
                print(f"[ORCHESTRATION] ✗ No insights generated - result: {orchestration_result}")
                    
        except Exception as agent_error:
            # Agent analysis is supplementary - don't fail the request
            print(f"[ORCHESTRATION] ✗ ERROR: {agent_error}")
            import traceback
            traceback.print_exc()
            agent_insights = None
            orchestration_result = {}
        
        # Run anomaly detection
        anomalies = []
        try:
            anomalies = AnomalyService.detect_anomalies(user_id=data['UserId'])
            print(f"[ANOMALY] Detected {len(anomalies)} anomalies")
        except Exception as anomaly_error:
            print(f"[ANOMALY] ✗ ERROR: {anomaly_error}")
        
        # Centralized Alert Management - Let AlertManagerService handle all alerts
        try:
            alert_context = {
                'agent_insights': orchestration_result.get('comprehensive_insight'),
                'anomalies': anomalies,
                'safety_analysis': orchestration_result.get('patient_safety'),
                'shift_data': shift.to_dict()
            }
            
            created_alerts = AlertManagerService.evaluate_and_create_alerts(
                user_id=data['UserId'],
                shift_id=shift.ShiftId,
                context=alert_context
            )
            
            print(f"[ALERT_MANAGER] Created {len(created_alerts)} alerts")
            
        except Exception as alert_error:
            print(f"[ALERT_MANAGER] ✗ ERROR: {alert_error}")
            import traceback
            traceback.print_exc()
        
        response_data = {
            'success': True,
            'message': 'Shift created successfully',
            'data': shift.to_dict()
        }
        
        # Include comprehensive agent insights if available
        if agent_insights:
            response_data['agent_insights'] = agent_insights
        
        return jsonify(response_data), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/shifts/<int:shift_id>', methods=['PUT'])
def update_shift(shift_id):
    """Update a shift"""
    try:
        shift = Shift.query.get_or_404(shift_id)
        data = request.get_json()
        
        updatable = ['HoursSleptBefore', 'ShiftType', 'ShiftLengthHours', 'PatientsCount',
                     'StressLevel', 'ShiftNote']
        
        # Track if we need to recalculate index
        recalculate = False
        for field in updatable:
            if field in data:
                setattr(shift, field, data[field])
                if field != 'ShiftNote':  # All except notes affect the index
                    recalculate = True
        
        if 'ShiftDate' in data:
            shift.ShiftDate = datetime.strptime(data['ShiftDate'], '%Y-%m-%d').date()
        
        # Recalculate SafeShift Index if relevant fields changed
        if recalculate:
            safe_shift_index, zone = SafeShiftService.calculate_index(
                hours_slept=shift.HoursSleptBefore,
                shift_type=shift.ShiftType,
                shift_length=shift.ShiftLengthHours,
                patients_count=shift.PatientsCount,
                stress_level=shift.StressLevel
            )
            shift.SafeShiftIndex = safe_shift_index
            shift.Zone = zone
            
            # Update AI insights for high-risk shifts
            if zone == 'red':
                try:
                    insights = LLMService.generate_insights(
                        shift_data={
                            'hours_slept': shift.HoursSleptBefore,
                            'shift_type': shift.ShiftType,
                            'shift_length': shift.ShiftLengthHours,
                            'patients_count': shift.PatientsCount,
                            'stress_level': shift.StressLevel,
                            'shift_note': shift.ShiftNote or ''
                        },
                        index=safe_shift_index,
                        zone=zone
                    )
                    shift.AiExplanation = insights.get('explanation')
                    shift.AiTips = insights.get('tips')
                except Exception as llm_error:
                    print(f"LLM generation skipped: {llm_error}")
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Shift updated successfully',
            'data': shift.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/shifts/<int:shift_id>', methods=['DELETE'])
def delete_shift(shift_id):
    """Delete a shift"""
    try:
        shift = Shift.query.get_or_404(shift_id)
        db.session.delete(shift)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Shift deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# VOICE DICTATION ENDPOINT
# ============================================
@api_bp.route('/shifts/parse-voice', methods=['POST'])
def parse_voice_to_shift():
    """
    Parse voice audio and extract shift data
    Accepts audio file and returns structured shift data
    """
    
    print("\n" + "="*60)
    print("[VOICE ENDPOINT] Received voice dictation request")
    print("="*60)
    
    try:
        # Debug: Log request details
        print(f"[VOICE ENDPOINT] Content-Type: {request.content_type}")
        print(f"[VOICE ENDPOINT] Files in request: {list(request.files.keys())}")
        
        # Check if audio file is present
        if 'audio' not in request.files:
            print("[VOICE ENDPOINT] ❌ No 'audio' field in request.files")
            return jsonify({
                'success': False,
                'error': 'No audio file provided. Expected field name: "audio"'
            }), 400
        
        audio_file = request.files['audio']
        print(f"[VOICE ENDPOINT] Audio file: {audio_file.filename}")
        print(f"[VOICE ENDPOINT] Content-Type: {audio_file.content_type}")
        
        if audio_file.filename == '':
            print("[VOICE ENDPOINT] ❌ Empty filename")
            return jsonify({
                'success': False,
                'error': 'Empty audio file'
            }), 400
        
        # Process audio with Whisper + GPT
        print("[VOICE ENDPOINT] Processing audio with VoiceService...")
        voice_service = VoiceService()
        
        if not voice_service.enabled:
            print("[VOICE ENDPOINT] ❌ VoiceService not enabled (check OPENAI_API_KEY)")
            return jsonify({
                'success': False,
                'error': 'Voice service not configured. Check OPENAI_API_KEY in .env'
            }), 500
        
        result = voice_service.process_audio_to_shift_data(audio_file)
        
        if not result.get('success'):
            print(f"[VOICE ENDPOINT] ❌ VoiceService failed: {result.get('error')}")
            return jsonify(result), 400
        
        print(f"[VOICE ENDPOINT] ✅ Success! Transcript: {result.get('transcript', '')[:100]}...")
        print("="*60)
        
        return jsonify({
            'success': True,
            'transcript': result['transcript'],
            'data': result['data'],
            'message': 'Voice parsed successfully'
        }), 200
    
    except Exception as e:
        print(f"[VOICE ENDPOINT] ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60)
        return jsonify({
            'success': False,
            'error': str(e),
            'type': type(e).__name__
        }), 500


# ============================================
# TIME OFF REQUEST ENDPOINTS
# ============================================
@api_bp.route('/timeoff', methods=['GET'])
def get_timeoff_requests():
    """Get all time off requests"""
    try:
        user_id = request.args.get('user_id')
        if user_id:
            requests_list = TimeOffRequest.query.filter_by(UserId=user_id).all()
        else:
            requests_list = TimeOffRequest.query.all()
        return jsonify({
            'success': True,
            'data': [r.to_dict() for r in requests_list],
            'count': len(requests_list)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/timeoff/<int:timeoff_id>', methods=['GET'])
def get_timeoff_request(timeoff_id):
    """Get a specific time off request"""
    try:
        timeoff = TimeOffRequest.query.get_or_404(timeoff_id)
        return jsonify({'success': True, 'data': timeoff.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@api_bp.route('/timeoff', methods=['POST'])
def create_timeoff_request():
    """Create a new time off request"""
    try:
        data = request.get_json()
        
        required = ['UserId', 'StartDate', 'EndDate', 'Reason']
        if not data or not all(field in data for field in required):
            return jsonify({'success': False, 'error': f'Required fields: {", ".join(required)}'}), 400
        
        start_date = datetime.strptime(data['StartDate'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['EndDate'], '%Y-%m-%d').date()
        
        timeoff = TimeOffRequest(
            UserId=data['UserId'],
            StartDate=start_date,
            EndDate=end_date,
            Reason=data['Reason'],
            AssignedBy=data.get('AssignedBy'),
            Status=data.get('Status', 'pending'),
            Notes=data.get('Notes')
        )
        
        db.session.add(timeoff)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Time off request created successfully',
            'data': timeoff.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/timeoff/<int:timeoff_id>', methods=['PUT'])
def update_timeoff_request(timeoff_id):
    """Update a time off request"""
    try:
        timeoff = TimeOffRequest.query.get_or_404(timeoff_id)
        data = request.get_json()
        
        if 'StartDate' in data:
            timeoff.StartDate = datetime.strptime(data['StartDate'], '%Y-%m-%d').date()
        if 'EndDate' in data:
            timeoff.EndDate = datetime.strptime(data['EndDate'], '%Y-%m-%d').date()
        
        updatable = ['Reason', 'AssignedBy', 'Status', 'Notes']
        for field in updatable:
            if field in data:
                setattr(timeoff, field, data[field])
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Time off request updated successfully',
            'data': timeoff.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/timeoff/<int:timeoff_id>', methods=['DELETE'])
def delete_timeoff_request(timeoff_id):
    """Delete a time off request"""
    try:
        timeoff = TimeOffRequest.query.get_or_404(timeoff_id)
        db.session.delete(timeoff)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Time off request deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# BURNOUT ALERT ENDPOINTS
# ============================================
@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all burnout alerts with summary"""
    try:
        user_id = request.args.get('user_id')
        unresolved_only = request.args.get('unresolved') == 'true'
        
        query = BurnoutAlert.query
        if user_id:
            query = query.filter_by(UserId=user_id)
        if unresolved_only:
            query = query.filter_by(IsResolved=False)
        
        alerts = query.all()
        
        # Get summary for active alerts
        summary = None
        if user_id:
            summary = AlertManagerService.get_alert_summary(int(user_id))
        
        return jsonify({
            'success': True,
            'alerts': [a.to_dict() for a in alerts],
            'summary': summary,
            'count': len(alerts)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get a specific burnout alert"""
    try:
        alert = BurnoutAlert.query.get_or_404(alert_id)
        return jsonify({'success': True, 'data': alert.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@api_bp.route('/alerts', methods=['POST'])
def create_alert():
    """Create a new burnout alert"""
    try:
        data = request.get_json()
        
        required = ['UserId', 'AlertType', 'Severity']
        if not data or not all(field in data for field in required):
            return jsonify({'success': False, 'error': f'Required fields: {", ".join(required)}'}), 400
        
        alert = BurnoutAlert(
            UserId=data['UserId'],
            AlertType=data['AlertType'],
            Severity=data['Severity'],
            Description=data.get('Description'),
            IsResolved=data.get('IsResolved', False)
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Burnout alert created successfully',
            'data': alert.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/alerts/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """Update a burnout alert"""
    try:
        alert = BurnoutAlert.query.get_or_404(alert_id)
        data = request.get_json()
        
        updatable = ['AlertType', 'Severity', 'Description', 'IsResolved']
        for field in updatable:
            if field in data:
                setattr(alert, field, data[field])
        
        if data.get('IsResolved') and not alert.ResolvedAt:
            alert.ResolvedAt = datetime.utcnow()
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Burnout alert updated successfully',
            'data': alert.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete a burnout alert"""
    try:
        alert = BurnoutAlert.query.get_or_404(alert_id)
        db.session.delete(alert)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Burnout alert deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Mark an alert as resolved with optional action"""
    try:
        from app.models import TimeOffRequest
        data = request.get_json() or {}
        
        # Get current user from token
        resolved_by = None
        token = request.headers.get('Authorization', '').replace('Bearer ', '')\
        
        if token:
            from app.auth import decode_token
            decoded = decode_token(token)
            if decoded:
                resolved_by = decoded.get('user_id')
        
        resolution_note = data.get('note')
        resolution_action = data.get('action', 'acknowledged')  # 'acknowledged', 'time_off_requested', 'will_monitor'
        
        # If action is time_off_requested, create a time off request
        if resolution_action == 'time_off_requested':
            alert = BurnoutAlert.query.get(alert_id)
            if alert:
                from datetime import date, timedelta
                
                # Create time off request for recovery
                time_off = TimeOffRequest(
                    UserId=alert.UserId,
                    StartDate=date.today() + timedelta(days=1),
                    EndDate=date.today() + timedelta(days=3),  # Default 3 days
                    Reason='burnout_risk',
                    Status='pending',
                    Notes=f"Auto-created from alert: {alert.AlertType}. {resolution_note or ''}"
                )
                db.session.add(time_off)
        
        success = AlertManagerService.resolve_alert(
            alert_id, 
            resolved_by=resolved_by,
            resolution_note=resolution_note,
            resolution_action=resolution_action
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'Alert not found'}), 404
        
        db.session.commit()  # Commit time off request if created
        
        return jsonify({
            'success': True, 
            'message': 'Alert resolved successfully',
            'action': resolution_action
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# SESSION ENDPOINTS (Authentication)
# ============================================
@api_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """Get all sessions"""
    try:
        user_id = request.args.get('user_id')
        if user_id:
            sessions = Session.query.filter_by(UserId=user_id).all()
        else:
            sessions = Session.query.all()
        return jsonify({
            'success': True,
            'data': [s.to_dict() for s in sessions],
            'count': len(sessions)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """Get a specific session"""
    try:
        session = Session.query.get_or_404(session_id)
        return jsonify({'success': True, 'data': session.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@api_bp.route('/sessions', methods=['POST'])
def create_session():
    """Create a new session (login)"""
    try:
        data = request.get_json()
        
        if not data or not data.get('UserId'):
            return jsonify({'success': False, 'error': 'UserId is required'}), 400
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = Session(
            UserId=data['UserId'],
            Token=token,
            ExpiresAt=expires_at,
            IpAddress=data.get('IpAddress', request.remote_addr),
            UserAgent=data.get('UserAgent', request.headers.get('User-Agent'))
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Session created successfully',
            'data': session.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session (logout)"""
    try:
        session = Session.query.get_or_404(session_id)
        db.session.delete(session)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Session deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# AGENT METRICS ENDPOINTS
# ============================================
@api_bp.route('/agents/metrics', methods=['GET'])
def get_agent_metrics():
    """Get agent performance metrics"""
    try:
        agent_name = request.args.get('agent', 'crisis_detection')
        days = int(request.args.get('days', 7))
        
        stats = AgentMetricsService.get_agent_stats(agent_name, days)
        
        return jsonify({
            'success': True,
            'agent': agent_name,
            'period_days': days,
            'data': stats
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/agents/metrics/crisis-rate', methods=['GET'])
def get_crisis_rate():
    """Get daily crisis detection rate"""
    try:
        days = int(request.args.get('days', 7))
        
        daily_stats = AgentMetricsService.get_daily_crisis_rate(days)
        
        return jsonify({
            'success': True,
            'period_days': days,
            'data': daily_stats
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/agents/metrics/user/<int:user_id>', methods=['GET'])
def get_user_crisis_history(user_id):
    """Get crisis detection history for specific user"""
    try:
        days = int(request.args.get('days', 30))
        
        history = AgentMetricsService.get_user_crisis_history(user_id, days)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'period_days': days,
            'data': history
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/agents/metrics/performance-issues', methods=['GET'])
def get_performance_issues():
    """Get slow or failed agent calls"""
    try:
        threshold_ms = int(request.args.get('threshold_ms', 5000))
        
        issues = AgentMetricsService.get_performance_issues(threshold_ms)
        
        return jsonify({
            'success': True,
            'threshold_ms': threshold_ms,
            'data': issues
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/agents/metrics/high-risk-users', methods=['GET'])
def get_high_risk_users():
    """Get users with repeated crisis detections"""
    try:
        days = int(request.args.get('days', 7))
        min_alerts = int(request.args.get('min_alerts', 2))
        
        high_risk = AgentMetricsService.get_high_risk_users(days, min_alerts)
        
        return jsonify({
            'success': True,
            'period_days': days,
            'min_alerts': min_alerts,
            'data': high_risk
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/agents/micro-break', methods=['POST'])
def generate_micro_break():
    """Generate personalized micro-break intervention"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Request body required'}), 400
        
        # Validate required fields
        if 'stress_level' not in data or 'minutes_available' not in data or 'location' not in data:
            return jsonify({
                'success': False, 
                'error': 'Required fields: stress_level, minutes_available, location'
            }), 400
        
        result = get_micro_break_agent().generate_break(
            stress_level=data.get('stress_level'),
            minutes_available=data.get('minutes_available'),
            location=data.get('location'),
            user_id=data.get('user_id'),
            shift_id=data.get('shift_id'),
            shift_type=data.get('shift_type')
        )
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# NEW AGENT ENDPOINTS
# ============================================

@api_bp.route('/agents/emotion-classify', methods=['POST'])
def classify_emotion():
    """Classify emotions in shift note"""
    try:
        data = request.get_json()
        
        if not data or 'shift_note' not in data:
            return jsonify({'success': False, 'error': 'shift_note required'}), 400
        
        result = get_emotion_agent().classify(
            shift_note=data['shift_note'],
            shift_type=data.get('shift_type'),
            shift_hours=data.get('shift_hours'),
            stress_level=data.get('stress_level'),
            recent_pattern=data.get('recent_pattern'),
            user_id=data.get('user_id'),
            shift_id=data.get('shift_id')
        )
        
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/agents/patient-safety-correlation', methods=['POST'])
def analyze_patient_safety():
    """Analyze correlation between burnout and patient safety"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['stress_level', 'consecutive_shifts', 'red_zone_count', 
                   'sleep_deficit_hours', 'avg_shift_hours', 'days_since_break']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'success': False, 
                'error': f'Missing required fields: {", ".join(missing)}'
            }), 400
        
        result = get_patient_safety_agent().analyze_correlation(
            stress_level=data['stress_level'],
            consecutive_shifts=data['consecutive_shifts'],
            red_zone_count=data['red_zone_count'],
            sleep_deficit_hours=data['sleep_deficit_hours'],
            avg_shift_hours=data['avg_shift_hours'],
            days_since_break=data['days_since_break'],
            crisis_alert_count=data.get('crisis_alert_count', 0),
            team_red_zone_count=data.get('team_red_zone_count', 0),
            understaffing_percentage=data.get('understaffing_percentage', 0),
            recent_incidents=data.get('recent_incidents', 0),
            shift_pattern_summary=data.get('shift_pattern_summary'),
            recent_anomalies=data.get('recent_anomalies'),
            user_id=data.get('user_id'),
            shift_id=data.get('shift_id')
        )
        
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/agents/comprehensive-analysis', methods=['POST'])
def comprehensive_analysis():
    """
    Orchestrated multi-agent comprehensive analysis
    Runs patient safety, micro-break, emotion, crisis, and insight agents
    """
    try:
        data = request.get_json()
        
        # Validate required context fields
        required = ['safeshift_index', 'current_zone', 'consecutive_shifts', 
                   'days_since_break', 'stress_level', 'red_zone_count',
                   'sleep_deficit_hours', 'avg_shift_hours']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing)}'
            }), 400
        
        result = get_orchestrator().generate_comprehensive_insight(
            shift_context=data,
            user_id=data.get('user_id'),
            shift_id=data.get('shift_id'),
            audience=data.get('audience', 'both')
        )
        
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/agents/analyze-shift-note', methods=['POST'])
def analyze_shift_note():
    """
    Orchestrated emotion → crisis workflow
    Classifies emotions first, then runs crisis detection if flagged
    """
    try:
        data = request.get_json()
        
        if not data or 'shift_note' not in data:
            return jsonify({'success': False, 'error': 'shift_note required'}), 400
        
        shift_data = {
            'shift_type': data.get('shift_type'),
            'shift_hours': data.get('shift_hours'),
            'stress_level': data.get('stress_level'),
            'stress_history': data.get('stress_history'),
            'recent_shifts': data.get('recent_shifts'),
            'previous_alerts': data.get('previous_alerts')
        }
        
        result = get_orchestrator().analyze_shift_note(
            shift_note=data['shift_note'],
            shift_data=shift_data,
            user_id=data.get('user_id'),
            shift_id=data.get('shift_id')
        )
        
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/agents/quick-wellness', methods=['POST'])
def quick_wellness():
    """Quick wellness check - just generate micro-break"""
    try:
        data = request.get_json()
        
        if not data or 'stress_level' not in data:
            return jsonify({'success': False, 'error': 'stress_level required'}), 400
        
        result = get_orchestrator().quick_wellness_check(
            stress_level=data['stress_level'],
            minutes_available=data.get('minutes_available', 5),
            location=data.get('location', 'hallway'),
            shift_type=data.get('shift_type', 'day'),
            user_id=data.get('user_id'),
            shift_id=data.get('shift_id')
        )
        
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/agents/enhanced-crisis-detection', methods=['POST'])
def enhanced_crisis_detection():
    """
    Enhanced crisis detection with emotion preprocessing and safety correlation
    """
    try:
        data = request.get_json()
        
        if not data or 'shift_note' not in data:
            return jsonify({'success': False, 'error': 'shift_note required'}), 400
        
        user_context = {
            'user_name': data.get('user_name'),
            'shift_type': data.get('shift_type'),
            'shift_hours': data.get('shift_hours'),
            'stress_level': data.get('stress_level'),
            'recent_shifts': data.get('recent_shifts'),
            'stress_history': data.get('stress_history'),
            'previous_alerts': data.get('previous_alerts'),
            'consecutive_shifts': data.get('consecutive_shifts'),
            'red_zone_count': data.get('red_zone_count'),
            'sleep_deficit_hours': data.get('sleep_deficit_hours'),
            'avg_shift_hours': data.get('avg_shift_hours'),
            'days_since_break': data.get('days_since_break')
        }
        
        result = get_orchestrator().detect_crisis_with_context(
            shift_note=data['shift_note'],
            user_context=user_context,
            user_id=data.get('user_id'),
            shift_id=data.get('shift_id')
        )
        
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# END AGENT ENDPOINTS
# ============================================


# ============================================
# CHAT ENDPOINT (AI Assistant)
# ============================================
@api_bp.route('/chat', methods=['POST'])
def chat_with_assistant():
    """
    Chat with AI wellness assistant
    Context-aware chatbot with safety filters and crisis detection
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'message' not in data or 'userId' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: message, userId'
            }), 400
        
        user_message = data['message']
        user_id = data['userId']
        conversation_history = data.get('history', [])
        
        print(f"[CHAT] Processing message from user {user_id}: {user_message[:50]}...")
        
        # Load user context from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        print(f"[CHAT] User found: {user.FirstName} {user.LastName}")
        
        # Get latest shifts (last 5 shifts only)
        recent_shifts = Shift.query.filter_by(UserId=user_id)\
            .order_by(Shift.ShiftDate.desc())\
            .limit(5)\
            .all()
        
        print(f"[CHAT] Found {len(recent_shifts)} recent shifts")
        
        latest_shift = recent_shifts[0] if recent_shifts else None
        
        # Get unresolved alerts
        unresolved_alerts = BurnoutAlert.query.filter_by(
            UserId=user_id,
            IsResolved=False
        ).count()
        
        # Count consecutive shifts
        consecutive_shifts = _count_consecutive_shifts(user_id, days=7)
        
        # Build user context
        user_context = {
            'user_name': user.FirstName,
            'role': user.Role,
            'department': user.Department,
            'hospital': user.Hospital,
            'current_zone': latest_shift.Zone if latest_shift else 'unknown',
            'safeshift_index': latest_shift.SafeShiftIndex if latest_shift else 0,
            'unresolved_alerts': unresolved_alerts,
            'recent_zones': [s.Zone for s in recent_shifts],
            'consecutive_shifts': consecutive_shifts,
            'latest_shift': {
                'date': latest_shift.ShiftDate.isoformat() if latest_shift else None,
                'hours_slept': latest_shift.HoursSleptBefore if latest_shift else None,
                'shift_type': latest_shift.ShiftType if latest_shift else None,
                'shift_length': latest_shift.ShiftLengthHours if latest_shift else None,
                'stress_level': latest_shift.StressLevel if latest_shift else None
            } if latest_shift else None,
            'agent_insights': latest_shift.AgentInsights if latest_shift and latest_shift.AgentInsights else None
        }
        
        # Initialize ChatService
        chat_service = ChatService()
        
        print(f"[CHAT] Generating AI response...")
        
        # Generate response
        result = chat_service.generate_response(
            user_message=user_message,
            user_context=user_context,
            conversation_history=conversation_history
        )
        
        print(f"[CHAT] AI response generated successfully")
        
        # Log conversation to database
        try:
            chat_log = ChatLog(
                UserId=user_id,
                UserMessage=user_message,
                BotResponse=result.get('response', ''),
                CrisisDetected=result.get('crisis_detected', False),
                SafetyFiltered=result.get('content_filtered', False) or result.get('out_of_scope', False),
                RequiresEscalation=result.get('requires_escalation', False),
                Language=chat_service.detect_language(user_message),
                TokensUsed=result.get('tokens_used'),
                ContextUsed=result.get('context_used', False)
            )
            db.session.add(chat_log)
            db.session.commit()
        except Exception as log_error:
            # Logging error shouldn't break the response
            print(f"[CHAT] Error logging conversation: {log_error}")
            import traceback
            traceback.print_exc()
        
        # If crisis detected, create critical alert
        if result.get('requires_escalation'):
            try:
                alert = BurnoutAlert(
                    UserId=user_id,
                    AlertType='crisis_detection',
                    Severity='critical',
                    Description=f"Crisis detected in chat: {user_message[:100]}",
                    IsResolved=False
                )
                db.session.add(alert)
                db.session.commit()
                print(f"[CHAT] ⚠️ CRISIS ALERT created for user {user_id}")
            except Exception as alert_error:
                print(f"[CHAT] Error creating crisis alert: {alert_error}")
        
        return jsonify({
            'success': True,
            'response': result.get('response'),
            'suggestions': result.get('suggestions', []),
            'crisis_detected': result.get('crisis_detected', False),
            'requires_escalation': result.get('requires_escalation', False)
        }), 200
    
    except Exception as e:
        print(f"[CHAT] Error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/chat/history/<int:user_id>', methods=['GET'])
def get_chat_history(user_id):
    """Get chat history for a user"""
    try:
        # Get last N messages
        limit = request.args.get('limit', 50, type=int)
        
        chat_logs = ChatLog.query.filter_by(UserId=user_id)\
            .order_by(ChatLog.CreatedAt.desc())\
            .limit(limit)\
            .all()
        
        return jsonify({
            'success': True,
            'data': [log.to_dict() for log in chat_logs],
            'count': len(chat_logs)
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# END CHAT ENDPOINTS
# ============================================
