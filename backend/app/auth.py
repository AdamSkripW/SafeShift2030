"""
Authentication Routes and Service - /api/auth/*
Consolidated auth functionality in the app directory
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta, datetime
from app.models import db, User

auth_bp = Blueprint('auth', __name__)

# ============================================
# SESSION MANAGEMENT UTILITIES
# ============================================
class SessionManager:
    """Utilities for managing user sessions"""
    
    @staticmethod
    def cleanup_expired_sessions():
        """Delete all expired sessions from the database"""
        from .models import Session
        try:
            expired_sessions = Session.query.filter(Session.ExpiresAt < datetime.utcnow()).all()
            count = len(expired_sessions)
            if count > 0:
                for session in expired_sessions:
                    db.session.delete(session)
                db.session.commit()
                print(f"[SESSION_CLEANUP] Deleted {count} expired session(s)")
            return count
        except Exception as e:
            db.session.rollback()
            print(f"[SESSION_CLEANUP] Error: {str(e)}")
            return 0
    
    @staticmethod
    def delete_user_sessions(user_id):
        """Delete all sessions for a specific user"""
        from .models import Session
        try:
            sessions = Session.query.filter_by(UserId=user_id).all()
            count = len(sessions)
            for session in sessions:
                db.session.delete(session)
            db.session.commit()
            print(f"[SESSION_CLEANUP] Deleted {count} session(s) for user {user_id}")
            return count
        except Exception as e:
            db.session.rollback()
            print(f"[SESSION_CLEANUP] Error: {str(e)}")
            return 0
    
    @staticmethod
    def get_active_session_count(user_id=None):
        """Get count of active (non-expired) sessions"""
        from .models import Session
        query = Session.query.filter(Session.ExpiresAt > datetime.utcnow())
        if user_id:
            query = query.filter_by(UserId=user_id)
        return query.count()

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
            
            # Delete any existing sessions for this user (enforce single session per user)
            from .models import Session
            existing_sessions = Session.query.filter_by(UserId=user.UserId).all()
            if existing_sessions:
                session_count = len(existing_sessions)
                for old_session in existing_sessions:
                    db.session.delete(old_session)
                print(f"[LOGIN] Deleted {session_count} existing session(s) for user {user.UserId}")
            
            # Create JWT token - convert to string
            access_token = create_access_token(
                identity=str(user.UserId),
                expires_delta=timedelta(days=1)
            )
            
            # Create session record in database
            expires_at = datetime.utcnow() + timedelta(days=1)
            
            session = Session(
                UserId=user.UserId,
                Token=access_token,
                ExpiresAt=expires_at,
                IpAddress=request.remote_addr if request else None,
                UserAgent=request.headers.get('User-Agent') if request else None
            )
            
            db.session.add(session)
            db.session.commit()
            
            print(f"[LOGIN] Session created in database (SessionId: {session.SessionId})")
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
                'sessionId': session.SessionId,
                'expiresIn': 86400,
                'message': 'Login successful'
            }, 200
        
        except Exception as e:
            db.session.rollback()
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
@jwt_required()
def logout():
    """Logout user (invalidate session)"""
    
    try:
        # Get the token from the request
        auth_header = request.headers.get('Authorization', '')
        print(f"[LOGOUT] Auth header: {auth_header[:50]}..." if auth_header else "[LOGOUT] No auth header")
        
        token = auth_header.replace('Bearer ', '').strip()
        
        if token:
            # Delete the session from database
            from .models import Session
            
            # Try to find the session
            session = Session.query.filter_by(Token=token).first()
            
            if session:
                session_id = session.SessionId
                user_id = session.UserId
                db.session.delete(session)
                db.session.commit()
                print(f"[LOGOUT] ✅ Session {session_id} deleted for user {user_id}")
            else:
                # Debug: check if any session exists with partial match
                all_sessions = Session.query.all()
                print(f"[LOGOUT] ❌ No session found for this token")
                print(f"[LOGOUT] Total sessions in DB: {len(all_sessions)}")
                print(f"[LOGOUT] Token prefix: {token[:30]}...")
        else:
            print(f"[LOGOUT] ❌ No token provided in request")
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        print(f"[LOGOUT] ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'  # Still return success even if session deletion fails
        }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    """Refresh JWT token"""
    
    try:
        user_id = get_jwt_identity()
        
        # Get old token
        old_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        # Delete ALL existing sessions for this user (enforce single session)
        from .models import Session
        SessionManager.delete_user_sessions(int(user_id))
        
        # Create new JWT token
        new_token = create_access_token(
            identity=user_id,
            expires_delta=timedelta(days=1)
        )
        
        # Create new session
        expires_at = datetime.utcnow() + timedelta(days=1)
        new_session = Session(
            UserId=int(user_id),
            Token=new_token,
            ExpiresAt=expires_at,
            IpAddress=request.remote_addr,
            UserAgent=request.headers.get('User-Agent')
        )
        
        db.session.add(new_session)
        db.session.commit()
        
        print(f"[REFRESH] Token refreshed for user {user_id}, new SessionId: {new_session.SessionId}")
        
        return jsonify({
            'token': new_token,
            'sessionId': new_session.SessionId,
            'expiresIn': 86400
        }), 200
    
    except Exception as e:
        db.session.rollback()
        print(f"[REFRESH] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Token refresh failed: {str(e)}'}), 500


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


# ============================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================

@auth_bp.route('/sessions/cleanup', methods=['POST'])
@jwt_required()
def cleanup_sessions():
    """Cleanup expired sessions (admin/maintenance endpoint)"""
    try:
        count = SessionManager.cleanup_expired_sessions()
        return jsonify({
            'success': True,
            'message': f'Deleted {count} expired session(s)',
            'deletedCount': count
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/sessions/status', methods=['GET'])
@jwt_required()
def session_status():
    """Get current user's session status"""
    try:
        user_id = int(get_jwt_identity())
        active_count = SessionManager.get_active_session_count(user_id)
        
        from .models import Session
        sessions = Session.query.filter_by(UserId=user_id).all()
        
        return jsonify({
            'success': True,
            'userId': user_id,
            'activeSessionCount': active_count,
            'totalSessions': len(sessions),
            'sessions': [
                {
                    'sessionId': s.SessionId,
                    'createdAt': s.CreatedAt.isoformat() if s.CreatedAt else None,
                    'expiresAt': s.ExpiresAt.isoformat() if s.ExpiresAt else None,
                    'ipAddress': s.IpAddress,
                    'isExpired': s.ExpiresAt < datetime.utcnow() if s.ExpiresAt else False
                }
                for s in sessions
            ]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/sessions/validate', methods=['GET'])
@jwt_required()
def validate_session():
    """Validate if current session still exists in database"""
    try:
        # Get token from request
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '').strip()
        
        if not token:
            return jsonify({
                'valid': False,
                'error': 'No token provided'
            }), 401
        
        # Check if session exists in database
        from .models import Session
        session = Session.query.filter_by(Token=token).first()
        
        if not session:
            return jsonify({
                'valid': False,
                'error': 'Session not found - may have been invalidated by another login'
            }), 401
        
        # Check if session is expired
        if session.ExpiresAt < datetime.utcnow():
            # Delete expired session
            db.session.delete(session)
            db.session.commit()
            return jsonify({
                'valid': False,
                'error': 'Session expired'
            }), 401
        
        # Session is valid
        return jsonify({
            'valid': True,
            'sessionId': session.SessionId,
            'userId': session.UserId,
            'expiresAt': session.ExpiresAt.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 500
