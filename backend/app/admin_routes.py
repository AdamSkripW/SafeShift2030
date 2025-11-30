"""
Admin Dashboard Routes - /api/admin/*
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, User, Shift, TimeOffRequest, BurnoutAlert
from app.services.admin_service import AdminService
from app.services.llm_service import LLMService
from datetime import date, timedelta

admin_bp = Blueprint('admin', __name__)

# Initialize LLM service
llm_service = LLMService()

# ============================================
# ADMIN ENDPOINTS
# ============================================

@admin_bp.route('/staff-overview', methods=['GET'])
@jwt_required()
def staff_overview():
    """Get overview of all staff in department"""
    
    department = request.args.get('department')
    
    try:
        staff = AdminService.get_staff_overview(db, User, Shift, department)
        
        return jsonify({
            'staff': staff,
            'count': len(staff),
            'department': department or 'All'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/staff/<int:user_id>', methods=['GET'])
@jwt_required()
def staff_detail(user_id):
    """Get detailed profile of specific staff member"""
    
    try:
        detail = AdminService.get_staff_detail(db, User, Shift, user_id, llm_service)
        
        if 'error' in detail:
            return jsonify(detail), 404
        
        return jsonify(detail), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    """Get all critical alerts"""
    
    department = request.args.get('department')
    
    try:
        alerts = AdminService.get_critical_alerts(db, User, Shift, department)
        
        return jsonify({
            'alerts': alerts,
            'count': len(alerts),
            'critical': sum(1 for a in alerts if a['severity'] == 'CRITICAL'),
            'warning': sum(1 for a in alerts if a['severity'] == 'WARNING')
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/intervention-suggestion/<int:user_id>', methods=['GET'])
@jwt_required()
def intervention_suggestion(user_id):
    """Generate AI intervention suggestion for staff member"""
    
    try:
        suggestion = AdminService.generate_intervention_suggestion(
            db, User, Shift, user_id, llm_service
        )
        
        return jsonify(suggestion), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/department-health', methods=['GET'])
@jwt_required()
def department_health():
    """Get overall health metrics for department"""
    
    department = request.args.get('department')
    
    if not department:
        return jsonify({'error': 'department parameter required'}), 400
    
    try:
        staff = AdminService.get_staff_overview(db, User, Shift, department)
        
        if not staff:
            return jsonify({
                'department': department,
                'staff_count': 0,
                'message': 'No staff found'
            }), 200
        
        # Calculate metrics
        critical_count = sum(1 for s in staff if s['alertLevel'] == 'CRITICAL')
        warning_count = sum(1 for s in staff if s['alertLevel'] == 'WARNING')
        ok_count = sum(1 for s in staff if s['alertLevel'] == 'OK')
        
        avg_index = sum(s['recentIndex'] for s in staff) / len(staff)
        
        # Overall health
        if critical_count > len(staff) * 0.2:
            health_status = 'CRITICAL'
            health_color = 'red'
        elif warning_count > len(staff) * 0.3:
            health_status = 'WARNING'
            health_color = 'orange'
        else:
            health_status = 'HEALTHY'
            health_color = 'green'
        
        return jsonify({
            'department': department,
            'staffCount': len(staff),
            'healthStatus': health_status,
            'healthColor': health_color,
            'averageIndex': round(avg_index, 1),
            'breakdown': {
                'critical': critical_count,
                'warning': warning_count,
                'caution': sum(1 for s in staff if s['alertLevel'] == 'CAUTION'),
                'ok': ok_count
            },
            'atRiskStaff': [
                {
                    'name': s['name'],
                    'index': s['recentIndex'],
                    'level': s['alertLevel']
                }
                for s in staff if s['alertLevel'] in ['CRITICAL', 'WARNING']
            ]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
