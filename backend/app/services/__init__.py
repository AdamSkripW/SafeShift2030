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
from app.services.chat_service import ChatService

# Agent Services
from app.services.agents import (
    CrisisDetectionAgent, 
    MicroBreakCoachAgent,
    PatientSafetyCorrelationAgent,
    EmotionClassifierAgent,
    InsightComposerAgent
)
from app.services.agent_metrics_service import AgentMetricsService
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.alert_manager_service import AlertManagerService

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
    'ChatService',
    # Agents
    'CrisisDetectionAgent',
    'MicroBreakCoachAgent',
    'PatientSafetyCorrelationAgent',
    'EmotionClassifierAgent',
    'InsightComposerAgent',
    'AgentMetricsService',
    'AgentOrchestrator',
    'AlertManagerService',
]
