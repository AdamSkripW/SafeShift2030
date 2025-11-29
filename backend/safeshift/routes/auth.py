"""
Authentication Routes - /api/auth/*
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from safeshift.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new healthcare worker"""
    
    data = request.get_json()
    
    required_fields = ['email', 'password', 'firstName', 'lastName', 'role', 'department', 'hospital']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # ⭐ Import from models (not create_app)
        from models import db, User
        
        result, status_code = AuthService.register_user(
            db,
            User,
            email=data['email'],
            password=data['password'],
            first_name=data['firstName'],
            last_name=data['lastName'],
            role=data['role'],
            department=data['department'],
            hospital=data['hospital']
        )
        
        return jsonify(result), status_code
    
    except Exception as e:
        print(f"[ROUTE] Register error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400
    
    try:
        # ⭐ Import from models (not create_app)
        from models import db, User
        
        result, status_code = AuthService.login_user(
            db,
            User,
            email=data['email'],
            password=data['password']
        )
        
        return jsonify(result), status_code
    
    except Exception as e:
        print(f"[ROUTE] Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user"""
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    """Refresh JWT token"""
    from flask_jwt_extended import create_access_token
    from datetime import timedelta
    
    user_id = get_jwt_identity()
    new_token = create_access_token(
        identity=user_id,
        expires_delta=timedelta(days=1)
    )
    return jsonify({
        'token': new_token,
        'expiresIn': 86400
    }), 200
