"""
Authentication Routes and Service - /api/auth/*
Consolidated auth functionality in the app directory
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from app.models import db, User

auth_bp = Blueprint('auth', __name__)

# ============================================
# AUTHENTICATION SERVICE
# ============================================
class AuthService:
    
    @staticmethod
    def register_user(email, password, first_name, last_name, role, department, hospital, hospital_id=None):
        """Register a new healthcare worker"""
        
        try:
            # Check if user exists
            existing_user = User.query.filter_by(Email=email).first()
            if existing_user:
                return {'error': 'Email already exists'}, 400
            
            # Create new user
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(
                Email=email,
                PasswordHash=hashed_password,
                FirstName=first_name,
                LastName=last_name,
                Role=role,
                Department=department,
                Hospital=hospital,
                HospitalId=hospital_id,
                IsActive=True
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            print(f"[REGISTER] User registered: {email}")
            
            return {
                'userId': new_user.UserId,
                'email': new_user.Email,
                'firstName': new_user.FirstName,
                'lastName': new_user.LastName,
                'role': new_user.Role,
                'department': new_user.Department,
                'message': 'Registration successful. Please log in.'
            }, 201
        
        except Exception as e:
            db.session.rollback()
            print(f"[REGISTER] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': f'Registration failed: {str(e)}'}, 500
    
    @staticmethod
    def login_user(email, password):
        """Login a user and return JWT token"""
        
        try:
            print(f"[LOGIN] Attempting login for: {email}")
            
            # Find user
            user = User.query.filter_by(Email=email).first()
            
            if not user:
                print(f"[LOGIN] User not found: {email}")
                return {'error': 'Invalid email or password'}, 401
            
            print(f"[LOGIN] User found, checking password...")
            
            if not check_password_hash(user.PasswordHash, password):
                print(f"[LOGIN] Password mismatch")
                return {'error': 'Invalid email or password'}, 401
            
            print(f"[LOGIN] Password correct, generating token...")
            
            # Create JWT token - convert to string
            access_token = create_access_token(
                identity=str(user.UserId),
                expires_delta=timedelta(days=1)
            )
            
            print(f"[LOGIN] Login successful for: {email}")
            
            return {
                'userId': user.UserId,
                'email': user.Email,
                'firstName': user.FirstName,
                'lastName': user.LastName,
                'role': user.Role,
                'department': user.Department,
                'hospital': user.Hospital,
                'isActive': user.IsActive,
                'token': access_token,
                'expiresIn': 86400,
                'message': 'Login successful'
            }, 200
        
        except Exception as e:
            print(f"[LOGIN] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': f'Login failed: {str(e)}'}, 500


# ============================================
# AUTHENTICATION ROUTES
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
        hospital=data['hospital'],
        hospital_id=data.get('hospitalId')
    )
    
    return jsonify(result), status_code


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


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (invalidate session)"""
    
    # For now, just return success
    # In production, you'd blacklist the token
    
    return jsonify({
        'message': 'Logged out successfully'
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    """Refresh JWT token"""
    
    user_id = get_jwt_identity()
    new_token = create_access_token(
        identity=user_id,
        expires_delta=timedelta(days=1)
    )
    return jsonify({
        'token': new_token,
        'expiresIn': 86400
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info from JWT token"""
    
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'userId': user.UserId,
        'email': user.Email,
        'firstName': user.FirstName,
        'lastName': user.LastName,
        'role': user.Role,
        'department': user.Department,
        'hospital': user.Hospital,
        'isActive': user.IsActive
    }), 200
