from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ---------------------------------------------
# Hospitals
# ---------------------------------------------
class Hospital(db.Model):
    __tablename__ = 'Hospitals'

    HospitalId = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(255), unique=True, nullable=False)
    City = db.Column(db.String(100), nullable=False)
    Country = db.Column(db.String(100), nullable=False)
    ContactEmail = db.Column(db.String(255))
    PhoneNumber = db.Column(db.String(20))
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = db.relationship('User', back_populates='hospital', cascade='all,delete-orphan', passive_deletes=True)
    admins = db.relationship('HospitalAdmin', back_populates='hospital', cascade='all,delete-orphan', passive_deletes=True)

    def to_dict(self):
        return {
            'HospitalId': self.HospitalId,
            'Name': self.Name,
            'City': self.City,
            'Country': self.Country,
            'ContactEmail': self.ContactEmail,
            'PhoneNumber': self.PhoneNumber,
            'CreatedAt': self.CreatedAt.isoformat() if self.CreatedAt else None,
            'UpdatedAt': self.UpdatedAt.isoformat() if self.UpdatedAt else None,
        }


# ---------------------------------------------
# Users (Healthcare Workers)
# ---------------------------------------------
class User(db.Model):
    __tablename__ = 'Users'

    UserId = db.Column(db.Integer, primary_key=True)
    Email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    FirstName = db.Column(db.String(100), nullable=False)
    LastName = db.Column(db.String(100), nullable=False)
    Role = db.Column(db.Enum('nurse', 'doctor', 'student', name='role_enum'), nullable=False)
    Department = db.Column(db.String(100), nullable=False)
    Hospital = db.Column(db.String(100), nullable=False)
    HospitalId = db.Column(db.Integer, db.ForeignKey('Hospitals.HospitalId', ondelete='SET NULL'), index=True)
    ProfilePictureUrl = db.Column(db.String(500))
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    IsActive = db.Column(db.Boolean, default=True)

    hospital = db.relationship('Hospital', back_populates='users')
    shifts = db.relationship('Shift', back_populates='user', cascade='all,delete-orphan', passive_deletes=True)
    sessions = db.relationship('Session', back_populates='user', cascade='all,delete-orphan', passive_deletes=True)
    time_off_requests = db.relationship('TimeOffRequest', back_populates='user', cascade='all,delete-orphan', passive_deletes=True)
    burnout_alerts = db.relationship('BurnoutAlert', back_populates='user', cascade='all,delete-orphan', passive_deletes=True)
    admin_links = db.relationship('HospitalAdmin', back_populates='user', cascade='all,delete-orphan', passive_deletes=True)

    def to_dict(self):
        return {
            'UserId': self.UserId,
            'Email': self.Email,
            'FirstName': self.FirstName,
            'LastName': self.LastName,
            'Role': self.Role,
            'Department': self.Department,
            'Hospital': self.Hospital,
            'HospitalId': self.HospitalId,
            'ProfilePictureUrl': self.ProfilePictureUrl,
            'CreatedAt': self.CreatedAt.isoformat() if self.CreatedAt else None,
            'UpdatedAt': self.UpdatedAt.isoformat() if self.UpdatedAt else None,
            'IsActive': self.IsActive,
        }


# ---------------------------------------------
# Hospital Admins
# ---------------------------------------------
class HospitalAdmin(db.Model):
    __tablename__ = 'HospitalAdmins'

    AdminId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId', ondelete='CASCADE'), nullable=False)
    HospitalId = db.Column(db.Integer, db.ForeignKey('Hospitals.HospitalId', ondelete='CASCADE'), nullable=False, index=True)
    Role = db.Column(db.Enum('wellness_manager', 'hr_manager', 'hospital_admin', name='admin_role_enum'), nullable=False)
    PermissionsViewAll = db.Column(db.Boolean, default=True)
    PermissionsEditShifts = db.Column(db.Boolean, default=False)
    PermissionsAssignTimeOff = db.Column(db.Boolean, default=True)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='admin_links')
    hospital = db.relationship('Hospital', back_populates='admins')

    __table_args__ = (
        db.UniqueConstraint('UserId', 'HospitalId', name='uq_admin_user_hospital'),
    )

    def to_dict(self):
        return {
            'AdminId': self.AdminId,
            'UserId': self.UserId,
            'HospitalId': self.HospitalId,
            'Role': self.Role,
            'PermissionsViewAll': self.PermissionsViewAll,
            'PermissionsEditShifts': self.PermissionsEditShifts,
            'PermissionsAssignTimeOff': self.PermissionsAssignTimeOff,
            'CreatedAt': self.CreatedAt.isoformat() if self.CreatedAt else None,
            'UpdatedAt': self.UpdatedAt.isoformat() if self.UpdatedAt else None,
        }


# ---------------------------------------------
# Shifts
# ---------------------------------------------
class Shift(db.Model):
    __tablename__ = 'Shifts'

    ShiftId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId', ondelete='CASCADE'), nullable=False, index=True)
    ShiftDate = db.Column(db.Date, nullable=False)
    HoursSleptBefore = db.Column(db.Integer, nullable=False)
    ShiftType = db.Column(db.Enum('day', 'night', 'rest', name='shift_type_enum'), nullable=False)
    ShiftLengthHours = db.Column(db.Integer, nullable=False)
    PatientsCount = db.Column(db.Integer, nullable=False)
    StressLevel = db.Column(db.Integer, nullable=False)
    ShiftNote = db.Column(db.Text)
    IsRecommended = db.Column(db.Boolean, default=False, nullable=False, index=True)

    SafeShiftIndex = db.Column(db.Integer, nullable=False, default=0)
    Zone = db.Column(db.Enum('green', 'yellow', 'red', name='shift_zone_enum'), nullable=False, default='green')
    AiExplanation = db.Column(db.Text)
    AiTips = db.Column(db.Text)
    AgentInsights = db.Column(db.JSON, nullable=True)

    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='shifts')

    __table_args__ = (
        db.Index('ix_shifts_user_date', 'UserId', 'ShiftDate'),
        db.Index('ix_shifts_zone', 'Zone'),
    )

    def to_dict(self):
        return {
            'ShiftId': self.ShiftId,
            'UserId': self.UserId,
            'ShiftDate': self.ShiftDate.isoformat() if self.ShiftDate else None,
            'HoursSleptBefore': self.HoursSleptBefore,
            'ShiftType': self.ShiftType,
            'ShiftLengthHours': self.ShiftLengthHours,
            'PatientsCount': self.PatientsCount,
            'StressLevel': self.StressLevel,
            'ShiftNote': self.ShiftNote,
            'IsRecommended': self.IsRecommended if hasattr(self, 'IsRecommended') else False,
            'SafeShiftIndex': self.SafeShiftIndex,
            'Zone': self.Zone,
            'AiExplanation': self.AiExplanation,
            'AiTips': self.AiTips,
            'AgentInsights': self.AgentInsights,
            'CreatedAt': self.CreatedAt.isoformat() if self.CreatedAt else None,
            'UpdatedAt': self.UpdatedAt.isoformat() if self.UpdatedAt else None,
        }


# ---------------------------------------------
# Time Off Requests
# ---------------------------------------------
class TimeOffRequest(db.Model):
    __tablename__ = 'TimeOffRequests'

    TimeOffId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId', ondelete='CASCADE'), nullable=False, index=True)
    StartDate = db.Column(db.Date, nullable=False)
    EndDate = db.Column(db.Date, nullable=False)
    Reason = db.Column(db.Enum('rest_recovery', 'burnout_risk', 'personal', 'admin_assigned', name='timeoff_reason_enum'), nullable=False)
    AssignedBy = db.Column(db.Integer, db.ForeignKey('HospitalAdmins.AdminId', ondelete='SET NULL'))
    Status = db.Column(db.Enum('pending', 'approved', 'rejected', 'taken', name='timeoff_status_enum'), nullable=False, default='pending')
    Notes = db.Column(db.Text)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='time_off_requests')
    assigned_admin = db.relationship('HospitalAdmin')

    __table_args__ = (
        db.Index('ix_timeoff_user_status', 'UserId', 'Status'),
        db.Index('ix_timeoff_startdate', 'StartDate'),
    )

    def to_dict(self):
        return {
            'TimeOffId': self.TimeOffId,
            'UserId': self.UserId,
            'StartDate': self.StartDate.isoformat() if self.StartDate else None,
            'EndDate': self.EndDate.isoformat() if self.EndDate else None,
            'Reason': self.Reason,
            'AssignedBy': self.AssignedBy,
            'Status': self.Status,
            'Notes': self.Notes,
            'CreatedAt': self.CreatedAt.isoformat() if self.CreatedAt else None,
            'UpdatedAt': self.UpdatedAt.isoformat() if self.UpdatedAt else None,
        }


# ---------------------------------------------
# Burnout Alerts
# ---------------------------------------------
class BurnoutAlert(db.Model):
    __tablename__ = 'BurnoutAlerts'

    AlertId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId', ondelete='CASCADE'), nullable=False, index=True)
    AlertType = db.Column(db.Enum(
        'chronic_low_sleep', 
        'consecutive_nights', 
        'high_stress_pattern', 
        'declining_health',
        'comprehensive_analysis',
        'crisis_detected',
        'patient_safety_risk',
        'recovery_needed',
        name='alert_type_enum'
    ), nullable=False)
    Severity = db.Column(db.Enum('low', 'medium', 'high', 'critical', name='alert_severity_enum'), nullable=False)
    AlertMessage = db.Column(db.Text)  # User-friendly short message
    Description = db.Column(db.Text)   # Detailed description
    IsResolved = db.Column(db.Boolean, default=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    ResolvedAt = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', back_populates='burnout_alerts')

    __table_args__ = (
        db.Index('ix_alerts_user_resolved', 'UserId', 'IsResolved'),
        db.Index('ix_alerts_severity', 'Severity'),
    )

    def to_dict(self):
        return {
            'AlertId': self.AlertId,
            'UserId': self.UserId,
            'AlertType': self.AlertType,
            'Severity': self.Severity,
            'AlertMessage': self.AlertMessage,
            'Description': self.Description,
            'IsResolved': self.IsResolved,
            'CreatedAt': self.CreatedAt.isoformat() if self.CreatedAt else None,
            'ResolvedAt': self.ResolvedAt.isoformat() if self.ResolvedAt else None,
        }


# ---------------------------------------------
# Sessions (Authentication)
# ---------------------------------------------
class Session(db.Model):
    __tablename__ = 'Sessions'

    SessionId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId', ondelete='CASCADE'), nullable=False, index=True)
    Token = db.Column(db.String(500), unique=True, index=True, nullable=False)
    ExpiresAt = db.Column(db.DateTime, nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    IpAddress = db.Column(db.String(50))
    UserAgent = db.Column(db.String(500))

    user = db.relationship('User', back_populates='sessions')

    __table_args__ = (
        db.Index('ix_sessions_user_expires', 'UserId', 'ExpiresAt'),
    )

    def to_dict(self):
        return {
            'SessionId': self.SessionId,
            'UserId': self.UserId,
            'Token': self.Token,
            'ExpiresAt': self.ExpiresAt.isoformat() if self.ExpiresAt else None,
            'CreatedAt': self.CreatedAt.isoformat() if self.CreatedAt else None,
            'IpAddress': self.IpAddress,
            'UserAgent': self.UserAgent,
        }


# ---------------------------------------------
# Agent Metrics (AI Agent Monitoring)
# ---------------------------------------------
class AgentMetric(db.Model):
    __tablename__ = 'AgentMetrics'

    MetricId = db.Column(db.Integer, primary_key=True)
    
    # Agent identification
    AgentName = db.Column(db.String(100), nullable=False, index=True)
    ModelVersion = db.Column(db.String(50), default='gpt-4o-mini')
    
    # User context
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId', ondelete='SET NULL'), nullable=True, index=True)
    ShiftId = db.Column(db.Integer, db.ForeignKey('Shifts.ShiftId', ondelete='SET NULL'), nullable=True)
    
    # Request/Response metrics
    InputTokens = db.Column(db.Integer, nullable=True)
    OutputTokens = db.Column(db.Integer, nullable=True)
    LatencyMs = db.Column(db.Integer, nullable=True)
    
    # Agent-specific output (for CrisisDetectionAgent)
    Severity = db.Column(db.String(20), nullable=True, index=True)
    ConfidenceScore = db.Column(db.Float, nullable=True)
    CrisisDetected = db.Column(db.Boolean, default=False, index=True)
    EscalationNeeded = db.Column(db.Boolean, default=False)
    
    # Execution status
    Success = db.Column(db.Boolean, default=True, index=True)
    ErrorMessage = db.Column(db.Text, nullable=True)
    FallbackUsed = db.Column(db.Boolean, default=False)
    
    # Metadata (JSON for flexibility)
    RequestPayload = db.Column(db.JSON, nullable=True)
    ResponsePayload = db.Column(db.JSON, nullable=True)
    
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', backref='agent_metrics')
    shift = db.relationship('Shift', backref='agent_metrics')
    
    def to_dict(self):
        return {
            'MetricId': self.MetricId,
            'AgentName': self.AgentName,
            'ModelVersion': self.ModelVersion,
            'UserId': self.UserId,
            'ShiftId': self.ShiftId,
            'InputTokens': self.InputTokens,
            'OutputTokens': self.OutputTokens,
            'TotalTokens': (self.InputTokens or 0) + (self.OutputTokens or 0),
            'LatencyMs': self.LatencyMs,
            'Severity': self.Severity,
            'ConfidenceScore': self.ConfidenceScore,
            'CrisisDetected': self.CrisisDetected,
            'EscalationNeeded': self.EscalationNeeded,
            'Success': self.Success,
            'ErrorMessage': self.ErrorMessage,
            'FallbackUsed': self.FallbackUsed,
            'CreatedAt': self.CreatedAt.isoformat() if self.CreatedAt else None
        }
    
    def to_dict_detailed(self):
        """Include full payloads for debugging"""
        base = self.to_dict()
        base['RequestPayload'] = self.RequestPayload
        base['ResponsePayload'] = self.ResponsePayload
        return base


# ---------------------------------------------
# Chat Logs (AI Assistant Conversation History)
# ---------------------------------------------
class ChatLog(db.Model):
    __tablename__ = 'ChatLogs'
    
    ChatId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId', ondelete='CASCADE'), nullable=False, index=True)
    UserMessage = db.Column(db.Text, nullable=False)
    BotResponse = db.Column(db.Text, nullable=False)
    
    # Safety flags
    CrisisDetected = db.Column(db.Boolean, default=False, index=True)
    SafetyFiltered = db.Column(db.Boolean, default=False)
    RequiresEscalation = db.Column(db.Boolean, default=False, index=True)
    
    # Metadata
    Language = db.Column(db.String(5), default='sk')  # 'sk' or 'en'
    TokensUsed = db.Column(db.Integer, nullable=True)
    ContextUsed = db.Column(db.Boolean, default=True)
    
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    user = db.relationship('User', backref='chat_logs')
    
    def to_dict(self):
        return {
            'ChatId': self.ChatId,
            'UserId': self.UserId,
            'UserMessage': self.UserMessage,
            'BotResponse': self.BotResponse,
            'CrisisDetected': self.CrisisDetected,
            'SafetyFiltered': self.SafetyFiltered,
            'RequiresEscalation': self.RequiresEscalation,
            'Language': self.Language,
            'TokensUsed': self.TokensUsed,
            'CreatedAt': self.CreatedAt.isoformat() if self.CreatedAt else None
        }
