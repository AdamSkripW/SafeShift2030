# SafeShift Services Architecture

## 📁 Directory Structure

```
app/
├── services/
│   ├── __init__.py              # Main entry point - imports all services
│   ├── crud_service.py          # CRUD operations for all models
│   ├── safeshift_service.py     # SafeShift Index calculation
│   ├── anomaly_service.py       # Anomaly detection in shift patterns
│   ├── prediction_service.py    # Burnout risk prediction
│   └── llm_service.py           # OpenAI integration (AI insights)
├── models.py
├── routes.py
├── auth.py
└── config.py
```

## 🎯 Service Overview

### 1. **crud_service.py** - Database CRUD Operations
**Purpose:** Basic database operations for all models

**Services:**
- `HospitalService` - Hospital CRUD
- `UserService` - User CRUD
- `ShiftService` - Shift CRUD
- `TimeOffService` - Time off request CRUD
- `BurnoutAlertService` - Alert CRUD

**Usage:**
```python
from app.services import UserService, ShiftService

user = UserService.get_user_by_id(1)
shifts = ShiftService.get_shifts_by_user(user_id=1)
```

---

### 2. **safeshift_service.py** - SafeShift Index Algorithm
**Purpose:** Calculate burnout risk index (0-100) and zone (green/yellow/red)

**Main Method:**
- `SafeShiftService.calculate_index(hours_slept, shift_type, shift_length, patients_count, stress_level)`

**Returns:** `(index, zone)` tuple

**Algorithm:**
- Sleep: 0-30 points (worse with <6h)
- Shift type: 0-25 points (night = higher risk)
- Shift length: 0-20 points (longer = higher risk)
- Patients: 0-15 points (more = higher workload)
- Stress: 0-20 points (based on 1-10 scale)

**Zones:**
- **Green**: 0-39 (Low risk)
- **Yellow**: 40-69 (Moderate risk)
- **Red**: 70-100 (High risk)

**Usage:**
```python
from app.services import SafeShiftService

index, zone = SafeShiftService.calculate_index(
    hours_slept=5,
    shift_type='night',
    shift_length=12,
    patients_count=10,
    stress_level=7
)
# Returns: (65, 'yellow')
```

---

### 3. **anomaly_service.py** - Pattern Detection
**Purpose:** Detect concerning patterns in shift history (last 14 days)

**Detects:**
1. **Consecutive Night Shifts** (3+ nights in a row)
2. **Chronic Low Sleep** (avg <6h over 2 weeks)
3. **Rising Stress Trend** (stress increasing significantly)
4. **Frequent High-Risk Shifts** (70%+ yellow/red zone)
5. **Extreme Single Shift** (index ≥85)

**Main Method:**
- `AnomalyService.detect_anomalies(user_id)`

**Returns:** List of anomalies with type, severity, description

**Usage:**
```python
from app.services import AnomalyService

anomalies = AnomalyService.detect_anomalies(user_id=1)
for anomaly in anomalies:
    print(f"{anomaly['type']}: {anomaly['description']}")
```

---

### 4. **prediction_service.py** - Burnout Risk Forecasting
**Purpose:** Predict future burnout risk using trend analysis (last 30 days)

**Method:** Simple linear regression on SafeShift Index trend

**Main Method:**
- `PredictionService.predict_burnout_risk(user_id, days_ahead=14)`

**Returns:**
```python
{
    'prediction': 'low_risk' | 'medium_risk' | 'high_risk',
    'predicted_index': int,
    'confidence': float (0-1),
    'days_until_critical': int or None,
    'reasoning': str,
    'slope': float,
    'current_index': int,
    'last_30_days_avg': float
}
```

**Usage:**
```python
from app.services import PredictionService

prediction = PredictionService.predict_burnout_risk(user_id=1, days_ahead=14)
print(f"Risk: {prediction['prediction']}, Index: {prediction['predicted_index']}")
```

---

### 5. **llm_service.py** - AI-Powered Insights (OpenAI)
**Purpose:** Generate AI-powered explanations, tips, and emotion analysis

**Requires:** `OPENAI_API_KEY` in .env file

**Features:**
- Gracefully disables if API key not present
- Uses GPT-4o-mini by default (configurable)
- Supportive, non-medical tone

**Main Methods:**

#### A. `generate_explanation()`
Explains WHY the SafeShift Index is in a specific zone

**Usage:**
```python
from app.services import LLMService

llm = LLMService()
explanation = llm.generate_explanation(
    first_name="Sarah",
    role="nurse",
    index=65,
    zone="yellow",
    hours_slept=5,
    shift_type="night",
    shift_length=12,
    patients_count=10,
    stress_level=7,
    shift_note="Busy night with 2 critical patients"
)
```

#### B. `generate_tips()`
Generates personalized recovery tips

**Returns:** Bullet-point list of actionable recovery tips

#### C. `analyze_emotion_from_note()`
Analyzes emotional tone from shift notes

**Returns:**
```python
{
    'dominant_emotion': 'exhaustion',
    'emotional_score': -6,
    'key_phrases': ['feeling drained', 'difficult night'],
    'ai_insight': 'Prioritize emotional recovery and rest'
}
```

#### D. `generate_anomaly_warning()`
Creates urgent warnings for detected anomalies

#### E. `generate_prediction_message()`
Creates forward-looking prediction messages

**Usage:**
```python
from app.services import LLMService

llm = LLMService()

# Check if enabled
if llm.enabled:
    tips = llm.generate_tips(...)
else:
    tips = "Default tips: Rest and recover"
```

---

## 🔧 How to Import Services

### Option 1: Import from main services module
```python
from app.services import (
    UserService,
    ShiftService,
    SafeShiftService,
    AnomalyService,
    PredictionService,
    LLMService
)
```

### Option 2: Import specific service file
```python
from app.services.crud_service import UserService
from app.services.llm_service import LLMService
```

---

## 🧪 Testing

Run service tests:
```bash
cd tests
python api-test-services.py
```

---

## 🌟 Usage Example in Routes

```python
from flask import Blueprint, request, jsonify
from app.services import (
    ShiftService,
    SafeShiftService,
    AnomalyService,
    LLMService
)

api_bp = Blueprint('api', __name__)

@api_bp.route('/shifts', methods=['POST'])
def create_shift():
    data = request.get_json()
    
    # 1. Calculate SafeShift Index
    index, zone = SafeShiftService.calculate_index(
        hours_slept=data['HoursSleptBefore'],
        shift_type=data['ShiftType'],
        shift_length=data['ShiftLengthHours'],
        patients_count=data['PatientsCount'],
        stress_level=data['StressLevel']
    )
    
    # 2. Generate AI insights (if enabled)
    llm = LLMService()
    if llm.enabled:
        explanation = llm.generate_explanation(...)
        tips = llm.generate_tips(...)
    else:
        explanation = f"Index: {index}, Zone: {zone}"
        tips = "Rest and recover"
    
    # 3. Create shift with calculated data
    shift = ShiftService.create_shift(
        user_id=data['UserId'],
        shift_date=data['ShiftDate'],
        hours_slept=data['HoursSleptBefore'],
        shift_type=data['ShiftType'],
        shift_length=data['ShiftLengthHours'],
        patients=data['PatientsCount'],
        stress=data['StressLevel'],
        SafeShiftIndex=index,
        Zone=zone,
        AiExplanation=explanation,
        AiTips=tips
    )
    
    # 4. Check for anomalies
    anomalies = AnomalyService.detect_anomalies(data['UserId'])
    if anomalies:
        # Create alerts...
        pass
    
    return jsonify({'success': True, 'data': shift.to_dict()}), 201
```

---

## 📝 Configuration

### Environment Variables (.env)

```bash
# Optional: OpenAI API (for LLM features)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Database
DB_USER=user
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=3306
DB_NAME=3bodyproblem_coalpushat

# Flask
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
```

---

## 🔒 Security Notes

- **LLM Service** gracefully degrades if `OPENAI_API_KEY` is not set
- All services use parameterized queries (SQLAlchemy ORM)
- No direct SQL injection risks
- User input validated in routes before passing to services

---

## 📊 Service Dependencies

```
crud_service.py          → models.py
safeshift_service.py     → (no dependencies)
anomaly_service.py       → models.py (Shift)
prediction_service.py    → models.py (Shift)
llm_service.py           → openai library
```

All services are **stateless** and can be used as static methods or instantiated (LLMService).
