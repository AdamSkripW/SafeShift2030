"""
SafeShift 2030 - Backend Flask Application
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
from datetime import timedelta

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# ============================================
# CONFIGURATION
# ============================================

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Connection Pooling Configuration
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 3,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'pool_timeout': 30,
    'max_overflow': 1,
}

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, origins=['http://localhost:4200', 'http://localhost:3000'])

# ============================================
# MODELS
# ============================================

class User(db.Model):
    __tablename__ = 'Users'
    
    UserId = db.Column(db.Integer, primary_key=True)
    Email = db.Column(db.String(255), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    FirstName = db.Column(db.String(100), nullable=False)
    LastName = db.Column(db.String(100), nullable=False)
    Role = db.Column(db.String(50), nullable=False)
    Department = db.Column(db.String(100), nullable=False)
    Hospital = db.Column(db.String(100), nullable=False)
    HospitalId = db.Column(db.Integer, db.ForeignKey('Hospitals.HospitalId'))
    ProfilePictureUrl = db.Column(db.String(500))
    IsActive = db.Column(db.Boolean, default=True)
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())
    UpdatedAt = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Hospital(db.Model):
    __tablename__ = 'Hospitals'
    
    HospitalId = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(255), unique=True, nullable=False)
    City = db.Column(db.String(100), nullable=False)
    Country = db.Column(db.String(100), nullable=False)
    ContactEmail = db.Column(db.String(255))
    PhoneNumber = db.Column(db.String(20))
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())
    UpdatedAt = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Shift(db.Model):
    __tablename__ = 'Shifts'
    
    ShiftId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    ShiftDate = db.Column(db.Date, nullable=False)
    HoursSleptBefore = db.Column(db.Integer, nullable=False)
    ShiftType = db.Column(db.String(10), nullable=False)
    ShiftLengthHours = db.Column(db.Integer, nullable=False)
    PatientsCount = db.Column(db.Integer, nullable=False)
    StressLevel = db.Column(db.Integer, nullable=False)
    ShiftNote = db.Column(db.Text)
    
    SafeShiftIndex = db.Column(db.Integer, default=0)
    Zone = db.Column(db.String(10), default='green')
    AiExplanation = db.Column(db.Text)
    AiTips = db.Column(db.Text)
    
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())
    UpdatedAt = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# ============================================
# ROUTES - HEALTH CHECK
# ============================================

@app.route('/health', methods=['GET'])
def health_check():
    """Check if backend is running"""
    return jsonify({
        'status': 'ok',
        'message': 'SafeShift 2030 Backend is running ✓'
    }), 200

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================
# IMPORT & REGISTER BLUEPRINTS
# ============================================


from safeshift.routes.auth import auth_bp
from safeshift.routes.shifts import shifts_bp

app.register_blueprint(auth_bp)
app.register_blueprint(shifts_bp)

# ============================================
# RUN APP
# ============================================

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database tables created/verified")
        except Exception as e:
            print(f"⚠ Error creating tables: {str(e)}")
    
    print("🚀 Starting SafeShift 2030 Backend...")
    app.run(debug=True, host='0.0.0.0', port=5000)