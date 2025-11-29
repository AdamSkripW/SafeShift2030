"""
Shift Routes - /api/shifts/*
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from safeshift.models import Shift, User, db
from safeshift.services.safeshift_service import SafeShiftService
from datetime import datetime

shifts_bp = Blueprint('shifts', __name__, url_prefix='/api/shifts')

# ============================================
# POST /api/shifts - Create New Shift
# ============================================
@shifts_bp.route('', methods=['POST'])
@jwt_required()
def create_shift():
    """Log a new shift"""
    
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['shiftDate', 'hoursSleptBefore', 'shiftType', 'shiftLengthHours', 'patientsCount', 'stressLevel']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Calculate SafeShift Index
    index, zone = SafeShiftService.calculate_index(
        hours_slept=data['hoursSleptBefore'],
        shift_type=data['shiftType'],
        shift_length=data['shiftLengthHours'],
        patients_count=data['patientsCount'],
        stress_level=data['stressLevel']
    )
    
    # TODO: Call LLM for AI explanation and tips
    ai_explanation = f"You are in the {zone} zone."
    ai_tips = "• Rest well\n• Take breaks"
    
    # Create shift record
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
    
    return jsonify({
        'shiftId': new_shift.ShiftId,
        'userId': new_shift.UserId,
        'safeShiftIndex': new_shift.SafeShiftIndex,
        'zone': new_shift.Zone,
        'aiExplanation': new_shift.AiExplanation,
        'aiTips': new_shift.AiTips,
        'createdAt': new_shift.CreatedAt.isoformat()
    }), 201

# ============================================
# GET /api/shifts - Get Shift History
# ============================================
@shifts_bp.route('', methods=['GET'])
@jwt_required()
def get_shift_history():
    """Get all shifts for logged-in user"""
    
    user_id = get_jwt_identity()
    days = request.args.get('days', default=14, type=int)
    
    # Get shifts from last X days
    from datetime import timedelta, date
    start_date = date.today() - timedelta(days=days)
    
    shifts = Shift.query.filter(
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

# ============================================
# GET /api/shifts/:id - Get Single Shift
# ============================================
@shifts_bp.route('/<int:shift_id>', methods=['GET'])
@jwt_required()
def get_shift(shift_id):
    """Get detailed info about one shift"""
    
    user_id = get_jwt_identity()
    shift = Shift.query.filter_by(ShiftId=shift_id, UserId=user_id).first()
    
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
