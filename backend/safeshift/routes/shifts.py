"""
Shift Routes - /api/shifts/*
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, date
from safeshift.services.safeshift_service import SafeShiftService
from safeshift.services.llm_service import LLMService
from safeshift.services.anomaly_service import AnomalyService
from safeshift.services.prediction_service import PredictionService

shifts_bp = Blueprint('shifts', __name__, url_prefix='/api/shifts')

llm_service = LLMService()

# Helper function to get models
def get_models():
    """Get models from models module"""
    # ⭐ Import from models (not create_app)
    from models import db, User, Shift
    return db, User, Shift
    
@shifts_bp.route('', methods=['POST'])
@jwt_required()
def create_shift():
    """Log a new shift with full AI analysis"""
    
    user_id = get_jwt_identity()
    data = request.get_json()
    
    db, User, Shift = get_models()
    
    required_fields = ['shiftDate', 'hoursSleptBefore', 'shiftType', 'shiftLengthHours', 'patientsCount', 'stressLevel']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        user = db.session.query(User).filter_by(UserId=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Calculate SafeShift Index
        index, zone = SafeShiftService.calculate_index(
            hours_slept=data['hoursSleptBefore'],
            shift_type=data['shiftType'],
            shift_length=data['shiftLengthHours'],
            patients_count=data['patientsCount'],
            stress_level=data['stressLevel']
        )
        
        # Generate AI Explanation
        ai_explanation = llm_service.generate_explanation(
            first_name=user.FirstName,
            role=user.Role,
            index=index,
            zone=zone,
            hours_slept=data['hoursSleptBefore'],
            shift_type=data['shiftType'],
            shift_length=data['shiftLengthHours'],
            patients_count=data['patientsCount'],
            stress_level=data['stressLevel'],
            shift_note=data.get('shiftNote', '')
        )
        
        # Generate AI Tips
        ai_tips = llm_service.generate_tips(
            first_name=user.FirstName,
            role=user.Role,
            zone=zone,
            hours_slept=data['hoursSleptBefore'],
            shift_type=data['shiftType'],
            shift_length=data['shiftLengthHours'],
            patients_count=data['patientsCount'],
            stress_level=data['stressLevel'],
            shift_note=data.get('shiftNote', '')
        )
        
        # Emotion Analysis
        emotion_data = llm_service.analyze_emotion_from_note(data.get('shiftNote', ''))
        
        # Create shift
        new_shift = Shift(
            UserId=user_id,
            ShiftDate=datetime.strptime(data['shiftDate'], '%Y-%m-%d').date(),
            HoursSleptBefore=data['hoursSleptBefore'],
            ShiftType=data['shiftType'],
            ShiftLengthHours=data['shiftLengthHours'],
            PatientsCount=data['patientsCount'],
            StressLevel=data['stressLevel'],
            ShiftNote=data.get('shiftNote', ''),
            SafeShiftIndex=index,
            Zone=zone,
            AiExplanation=ai_explanation,
            AiTips=ai_tips
        )
        
        db.session.add(new_shift)
        db.session.commit()
        
        # Detect Anomalies
        anomalies = AnomalyService.detect_anomalies(db, User, Shift, user_id)
        anomaly_warning = None
        if anomalies:
            anomaly_warning = AnomalyService.get_anomaly_ai_warning(llm_service, user.FirstName, anomalies)
        
        # Predict Burnout Risk
        prediction = PredictionService.predict_burnout_risk(db, Shift, user_id, days_ahead=14)
        prediction_warning = PredictionService.get_prediction_ai_message(llm_service, user.FirstName, prediction)
        
        # Return comprehensive response
        return jsonify({
            'shiftId': new_shift.ShiftId,
            'userId': new_shift.UserId,
            'safeShiftIndex': new_shift.SafeShiftIndex,
            'zone': new_shift.Zone,
            'aiExplanation': new_shift.AiExplanation,
            'aiTips': new_shift.AiTips,
            'emotion': emotion_data,
            'anomalies': anomalies,
            'anomalyWarning': anomaly_warning,
            'prediction': prediction,
            'predictionWarning': prediction_warning,
            'createdAt': new_shift.CreatedAt.isoformat()
        }), 201
    
    except Exception as e:
        print(f"Error creating shift: {str(e)}")
        return jsonify({'error': f'Failed to create shift: {str(e)}'}), 500

@shifts_bp.route('', methods=['GET'])
@jwt_required()
def get_shift_history():
    """Get all shifts for logged-in user"""
    
    user_id = get_jwt_identity()
    days = request.args.get('days', default=14, type=int)
    
    db, User, Shift = get_models()
    
    start_date = date.today() - timedelta(days=days)
    
    shifts = db.session.query(Shift).filter(
        Shift.UserId == user_id,
        Shift.ShiftDate >= start_date
    ).order_by(Shift.ShiftDate.desc()).all()
    
    return jsonify({
        'shifts': [{
            'shiftId': s.ShiftId,
            'shiftDate': s.ShiftDate.isoformat(),
            'safeShiftIndex': s.SafeShiftIndex,
            'zone': s.Zone,
            'shiftType': s.ShiftType,
            'patientsCount': s.PatientsCount,
            'stressLevel': s.StressLevel
        } for s in shifts]
    }), 200

@shifts_bp.route('/<int:shift_id>', methods=['GET'])
@jwt_required()
def get_shift(shift_id):
    """Get single shift"""
    
    user_id = get_jwt_identity()
    
    db, User, Shift = get_models()
    
    shift = db.session.query(Shift).filter_by(ShiftId=shift_id, UserId=user_id).first()
    
    if not shift:
        return jsonify({'error': 'Shift not found'}), 404
    
    return jsonify({
        'shiftId': shift.ShiftId,
        'shiftDate': shift.ShiftDate.isoformat(),
        'hoursSleptBefore': shift.HoursSleptBefore,
        'shiftType': shift.ShiftType,
        'shiftLengthHours': shift.ShiftLengthHours,
        'patientsCount': shift.PatientsCount,
        'stressLevel': shift.StressLevel,
        'shiftNote': shift.ShiftNote,
        'safeShiftIndex': shift.SafeShiftIndex,
        'zone': shift.Zone,
        'aiExplanation': shift.AiExplanation,
        'aiTips': shift.AiTips
    }), 200

@shifts_bp.route('/summary/weekly', methods=['GET'])
@jwt_required()
def get_weekly_summary():
    """Get weekly summary with AI analysis"""
    
    user_id = get_jwt_identity()
    
    db, User, Shift = get_models()
    
    user = db.session.query(User).filter_by(UserId=user_id).first()
    
    start_date = date.today() - timedelta(days=7)
    
    shifts = db.session.query(Shift).filter(
        Shift.UserId == user_id,
        Shift.ShiftDate >= start_date
    ).order_by(Shift.ShiftDate.asc()).all()
    
    if not shifts:
        return jsonify({
            'period': 'last_7_days',
            'shiftsCount': 0,
            'averageIndex': 0,
            'zoneBreakdown': {'green': 0, 'yellow': 0, 'red': 0},
            'summary': 'No shifts logged in the last 7 days.',
            'suggestions': []
        }), 200
    
    shifts_data = [{
        'date': s.ShiftDate.strftime('%Y-%m-%d'),
        'index': s.SafeShiftIndex,
        'zone': s.Zone,
        'shift_type': s.ShiftType,
        'hours_slept': s.HoursSleptBefore
    } for s in shifts]
    
    llm_result = llm_service.generate_weekly_summary(user.FirstName, shifts_data)
    
    red_count = sum(1 for s in shifts if s.Zone == 'red')
    yellow_count = sum(1 for s in shifts if s.Zone == 'yellow')
    green_count = sum(1 for s in shifts if s.Zone == 'green')
    avg_index = sum(s.SafeShiftIndex for s in shifts) / len(shifts)
    
    return jsonify({
        'period': 'last_7_days',
        'shiftsCount': len(shifts),
        'averageIndex': int(avg_index),
        'zoneBreakdown': {
            'green': green_count,
            'yellow': yellow_count,
            'red': red_count
        },
        'summary': llm_result.get('summary', ''),
        'suggestions': llm_result.get('suggestions', [])
    }), 200
