"""
Authentication Routes - /api/auth/*
"""

from flask import Blueprint, request, jsonify
from safeshift.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# ============================================
# POST /api/auth/register
# ============================================
@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new healthcare worker"""
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'firstName', 'lastName', 'role', 'department', 'hospital']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    result, status_code = AuthService.register_user(
        email=data['email'],
        password=data['password'],
        first_name=data['firstName'],
        last_name=data['lastName'],
        role=data['role'],
        department=data['department'],
        hospital=data['hospital']
    )
    
    return jsonify(result), status_code

# ============================================
# POST /api/auth/login
# ============================================
@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400
    
    result, status_code = AuthService.login_user(
        email=data['email'],
        password=data['password']
    )
    
    return jsonify(result), status_code

# ============================================
# POST /api/auth/logout
# ============================================
@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (invalidate session)"""
    
    # For now, just return success
    # In production, you'd blacklist the token
    
    return jsonify({
        'message': 'Logged out successfully'
    }), 200

# ============================================
# POST /api/auth/refresh
# ============================================
@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh JWT token"""
    
    from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
    from datetime import timedelta
    
    @jwt_required()
    def _refresh():
        user_id = get_jwt_identity()
        new_token = create_access_token(
            identity=user_id,
            expires_delta=timedelta(days=1)
        )
        return jsonify({
            'token': new_token,
            'expiresIn': 86400
        }), 200
    
    return _refresh()
