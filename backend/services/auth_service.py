"""
Authentication Service - Handle registration, login, token management
"""

from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from safeshift.models import User, db
from datetime import timedelta

class AuthService:
    
    @staticmethod
    def register_user(email, password, first_name, last_name, role, department, hospital, hospital_id=None):
        """Register a new healthcare worker"""
        
        # Check if user exists
        if User.query.filter_by(Email=email).first():
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
        
        return {
            'userId': new_user.UserId,
            'email': new_user.Email,
            'firstName': new_user.FirstName,
            'lastName': new_user.LastName,
            'role': new_user.Role,
            'department': new_user.Department,
            'message': 'Registration successful. Please log in.'
        }, 201
    
    @staticmethod
    def login_user(email, password):
        """Login a user and return JWT token"""
        
        # Find user
        user = User.query.filter_by(Email=email).first()
        
        if not user or not check_password_hash(user.PasswordHash, password):
            return {'error': 'Invalid email or password'}, 401
        
        # Create JWT token
        access_token = create_access_token(
            identity=user.UserId,
            expires_delta=timedelta(days=1)
        )
        
        return {
            'userId': user.UserId,
            'email': user.Email,
            'firstName': user.FirstName,
            'lastName': user.LastName,
            'role': user.Role,
            'department': user.Department,
            'isAdmin': False,  # TODO: Check if user is admin
            'token': access_token,
            'expiresIn': 86400,
            'message': 'Login successful'
        }, 200
