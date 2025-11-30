from flask import Blueprint, jsonify, request
from app.models import db, User, Hospital, HospitalAdmin, Shift, TimeOffRequest, BurnoutAlert, Session
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

# Import services
from app.services import (
    SafeShiftService,
    AnomalyService,
    LLMService
)
from app.services.voice_service import VoiceService

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)

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
            'sessions': '/api/sessions'
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
        
        # Generate AI insights for high-risk shifts (optional)
        ai_explanation = None
        ai_tips = None
        if zone == 'red':
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
        
        # Run anomaly detection after shift is saved
        try:
            anomalies = AnomalyService.detect_anomalies(user_id=data['UserId'])
            
            # Create alerts for detected anomalies
            for anomaly in anomalies:
                # Check if alert already exists
                existing_alert = BurnoutAlert.query.filter_by(
                    UserId=data['UserId'],
                    AlertType=anomaly['type'],
                    IsResolved=False
                ).first()
                
                if not existing_alert:
                    alert = BurnoutAlert(
                        UserId=data['UserId'],
                        AlertType=anomaly['type'],
                        Severity=anomaly['severity'],
                        AlertMessage=anomaly['message'],
                        IsResolved=False
                    )
                    db.session.add(alert)
            
            db.session.commit()
        except Exception as anomaly_error:
            # Anomaly detection is supplementary - don't fail the whole request
            print(f"Anomaly detection error: {anomaly_error}")
        
        return jsonify({
            'success': True,
            'message': 'Shift created successfully',
            'data': shift.to_dict()
        }), 201
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
    """Get all burnout alerts"""
    try:
        user_id = request.args.get('user_id')
        unresolved_only = request.args.get('unresolved') == 'true'
        
        query = BurnoutAlert.query
        if user_id:
            query = query.filter_by(UserId=user_id)
        if unresolved_only:
            query = query.filter_by(IsResolved=False)
        
        alerts = query.all()
        return jsonify({
            'success': True,
            'data': [a.to_dict() for a in alerts],
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
    try:
        item = Item.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Session deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
