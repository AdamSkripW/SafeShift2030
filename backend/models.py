"""
Database Models
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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
