from app.models import db, User, Hospital, HospitalAdmin, Shift, TimeOffRequest, BurnoutAlert, Session

class HospitalService:
    """Service layer for Hospital operations"""
    
    @staticmethod
    def get_all_hospitals():
        return Hospital.query.all()
    
    @staticmethod
    def get_hospital_by_id(hospital_id):
        return Hospital.query.get(hospital_id)
    
    @staticmethod
    def create_hospital(name, city, country, **kwargs):
        hospital = Hospital(Name=name, City=city, Country=country, **kwargs)
        db.session.add(hospital)
        db.session.commit()
        return hospital
    
    @staticmethod
    def update_hospital(hospital_id, **kwargs):
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return None
        for key, value in kwargs.items():
            if hasattr(hospital, key):
                setattr(hospital, key, value)
        db.session.commit()
        return hospital
    
    @staticmethod
    def delete_hospital(hospital_id):
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return False
        db.session.delete(hospital)
        db.session.commit()
        return True

class UserService:
    """Service layer for User operations"""
    
    @staticmethod
    def get_all_users():
        return User.query.all()
    
    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_email(email):
        return User.query.filter_by(Email=email).first()
    
    @staticmethod
    def create_user(email, password_hash, first_name, last_name, role, department, hospital, **kwargs):
        user = User(
            Email=email, 
            PasswordHash=password_hash,
            FirstName=first_name,
            LastName=last_name,
            Role=role,
            Department=department,
            Hospital=hospital,
            **kwargs
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def update_user(user_id, **kwargs):
        user = User.query.get(user_id)
        if not user:
            return None
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.session.commit()
        return user
    
    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return False
        db.session.delete(user)
        db.session.commit()
        return True

class ShiftService:
    """Service layer for Shift operations"""
    
    @staticmethod
    def get_all_shifts():
        return Shift.query.all()
    
    @staticmethod
    def get_shifts_by_user(user_id):
        return Shift.query.filter_by(UserId=user_id).all()
    
    @staticmethod
    def get_shift_by_id(shift_id):
        return Shift.query.get(shift_id)
    
    @staticmethod
    def create_shift(user_id, shift_date, hours_slept, shift_type, shift_length, patients, stress, **kwargs):
        shift = Shift(
            UserId=user_id,
            ShiftDate=shift_date,
            HoursSleptBefore=hours_slept,
            ShiftType=shift_type,
            ShiftLengthHours=shift_length,
            PatientsCount=patients,
            StressLevel=stress,
            **kwargs
        )
        db.session.add(shift)
        db.session.commit()
        return shift
    
    @staticmethod
    def update_shift(shift_id, **kwargs):
        shift = Shift.query.get(shift_id)
        if not shift:
            return None
        for key, value in kwargs.items():
            if hasattr(shift, key):
                setattr(shift, key, value)
        db.session.commit()
        return shift
    
    @staticmethod
    def delete_shift(shift_id):
        shift = Shift.query.get(shift_id)
        if not shift:
            return False
        db.session.delete(shift)
        db.session.commit()
        return True

class TimeOffService:
    """Service layer for TimeOff operations"""
    
    @staticmethod
    def get_all_timeoff():
        return TimeOffRequest.query.all()
    
    @staticmethod
    def get_timeoff_by_user(user_id):
        return TimeOffRequest.query.filter_by(UserId=user_id).all()
    
    @staticmethod
    def create_timeoff(user_id, start_date, end_date, reason, **kwargs):
        timeoff = TimeOffRequest(
            UserId=user_id,
            StartDate=start_date,
            EndDate=end_date,
            Reason=reason,
            **kwargs
        )
        db.session.add(timeoff)
        db.session.commit()
        return timeoff
    
    @staticmethod
    def update_timeoff(timeoff_id, **kwargs):
        timeoff = TimeOffRequest.query.get(timeoff_id)
        if not timeoff:
            return None
        for key, value in kwargs.items():
            if hasattr(timeoff, key):
                setattr(timeoff, key, value)
        db.session.commit()
        return timeoff

class BurnoutAlertService:
    """Service layer for BurnoutAlert operations"""
    
    @staticmethod
    def get_all_alerts():
        return BurnoutAlert.query.all()
    
    @staticmethod
    def get_alerts_by_user(user_id, unresolved_only=False):
        query = BurnoutAlert.query.filter_by(UserId=user_id)
        if unresolved_only:
            query = query.filter_by(IsResolved=False)
        return query.all()
    
    @staticmethod
    def create_alert(user_id, alert_type, severity, **kwargs):
        alert = BurnoutAlert(
            UserId=user_id,
            AlertType=alert_type,
            Severity=severity,
            **kwargs
        )
        db.session.add(alert)
        db.session.commit()
        return alert
    
    @staticmethod
    def resolve_alert(alert_id):
        alert = BurnoutAlert.query.get(alert_id)
        if not alert:
            return None
        alert.IsResolved = True
        from datetime import datetime
        alert.ResolvedAt = datetime.utcnow()
        db.session.commit()
        return alert
