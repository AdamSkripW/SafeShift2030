"""
Authentication Service - Handle registration, login, token management
"""

from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta
from flask import current_app

class AuthService:
    
    @staticmethod
    def register_user(db, User, email, password, first_name, last_name, role, department, hospital, hospital_id=None):
        """Register a new healthcare worker"""
        
        try:
            # Check if user exists
            existing_user = db.session.query(User).filter_by(Email=email).first()
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
                HospitalId=hospital_id
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
    def login_user(db, User, email, password):
        """Login a user and return JWT token"""
        
        try:
            print(f"[LOGIN] Attempting login for: {email}")
            
            # Find user
            user = db.session.query(User).filter_by(Email=email).first()
            
            if not user:
                print(f"[LOGIN] User not found: {email}")
                return {'error': 'Invalid email or password'}, 401
            
            print(f"[LOGIN] User found, checking password...")
            
            if not check_password_hash(user.PasswordHash, password):
                print(f"[LOGIN] Password mismatch")
                return {'error': 'Invalid email or password'}, 401
            
            print(f"[LOGIN] Password correct, generating token...")
            
            # Create JWT token
            access_token = create_access_token(
                identity=user.UserId,
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
                'isAdmin': False,
                'token': access_token,
                'expiresIn': 86400,
                'message': 'Login successful'
            }, 200
        
        except Exception as e:
            print(f"[LOGIN] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': f'Login failed: {str(e)}'}, 500
