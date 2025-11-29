"""
Services Module - Import all services from separate files
This makes it easy to import services in routes and other modules
"""

# CRUD Services
from app.services.crud_service import (
    HospitalService,
    UserService,
    ShiftService,
    TimeOffService,
    BurnoutAlertService
)

# SafeShift Core Services
from app.services.safeshift_service import SafeShiftService
from app.services.anomaly_service import AnomalyService
from app.services.prediction_service import PredictionService

# AI/LLM Service
from app.services.llm_service import LLMService

__all__ = [
    # CRUD
    'HospitalService',
    'UserService',
    'ShiftService',
    'TimeOffService',
    'BurnoutAlertService',
    # SafeShift
    'SafeShiftService',
    'AnomalyService',
    'PredictionService',
    # AI
    'LLMService',
]
