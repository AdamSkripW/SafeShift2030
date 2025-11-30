# SafeShift 2030 Backend API

> **📋 For comprehensive project status and architecture, see [PROJECT_STATUS.md](PROJECT_STATUS.md)**

**Quick Links**:
- 🚀 [Quick Start Guide](QUICK_START.md) - Get started in 5 minutes
- 🐛 [Recent Critical Fix](CRITICAL_BUG_FIX.md) - Field name mismatch bug fix
- ✅ [Merge Review](ORCHESTRATION_MERGE_REVIEW.md) - Production readiness checklist

---

Flask REST API for SafeShift 2030 - connects to existing MySQL database.

## Prerequisites

- Python 3.8+
- MySQL database (already set up with SafeShift schema)
- Database credentials

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Database

Edit `.env` file with your database credentials:

```env
DB_USER=user
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=3306
DB_NAME=3bodyproblem_coalpushat
```

### 3. Run the API

```bash
python run.py
```

Server starts on: `http://localhost:5000`

## API Endpoints

### Health Check
- `GET /api/health` - Check backend status

### Hospitals
- `GET /api/hospitals` - List all hospitals
- `GET /api/hospitals/:id` - Get hospital by ID
- `POST /api/hospitals` - Create hospital
- `PUT /api/hospitals/:id` - Update hospital
- `DELETE /api/hospitals/:id` - Delete hospital

### Users
- `GET /api/users` - List all users
- `GET /api/users/:id` - Get user by ID
- `POST /api/users` - Create user
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user

### Hospital Admins
- `GET /api/admins` - List all admins
- `GET /api/admins/:id` - Get admin by ID
- `POST /api/admins` - Create admin
- `PUT /api/admins/:id` - Update admin
- `DELETE /api/admins/:id` - Delete admin

### Shifts
- `GET /api/shifts` - List all shifts
- `GET /api/shifts?user_id=:id` - Get shifts for user
- `GET /api/shifts/:id` - Get shift by ID
- `POST /api/shifts` - Create shift
- `PUT /api/shifts/:id` - Update shift
- `DELETE /api/shifts/:id` - Delete shift

### Time Off Requests
- `GET /api/timeoff` - List all time-off requests
- `GET /api/timeoff?user_id=:id` - Get requests for user
- `GET /api/timeoff/:id` - Get request by ID
- `POST /api/timeoff` - Create request
- `PUT /api/timeoff/:id` - Update request
- `DELETE /api/timeoff/:id` - Delete request

### Burnout Alerts
- `GET /api/alerts` - List all alerts
- `GET /api/alerts?user_id=:id` - Get alerts for user
- `GET /api/alerts?unresolved=true` - Get unresolved alerts
- `GET /api/alerts/:id` - Get alert by ID
- `POST /api/alerts` - Create alert
- `PUT /api/alerts/:id` - Update alert
- `DELETE /api/alerts/:id` - Delete alert

### Sessions (Authentication)
- `GET /api/sessions` - List all sessions
- `GET /api/sessions?user_id=:id` - Get sessions for user
- `POST /api/sessions` - Create session (login)
- `DELETE /api/sessions/:id` - Delete session (logout)

## Response Format

All endpoints return JSON:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message"
}
```

## Testing

```bash
# Health check
curl http://localhost:5000/api/health

# Get all users
curl http://localhost:5000/api/users

# Get shifts for user ID 2
curl http://localhost:5000/api/shifts?user_id=2

# Create a shift
curl -X POST http://localhost:5000/api/shifts \
  -H "Content-Type: application/json" \
  -d '{
    "UserId": 1,
    "ShiftDate": "2025-11-30",
    "HoursSleptBefore": 7,
    "ShiftType": "day",
    "ShiftLengthHours": 8,
    "PatientsCount": 5,
    "StressLevel": 4,
    "SafeShiftIndex": 80,
    "Zone": "green"
  }'
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py      # Flask app initialization
│   ├── config.py        # Configuration (DB credentials)
│   ├── models.py        # SQLAlchemy models
│   ├── routes.py        # API endpoints
│   └── services.py      # Business logic layer
├── .env                 # Database credentials (DO NOT COMMIT)
├── .env.example         # Environment template
├── requirements.txt     # Python dependencies
├── run.py              # Application entry point
└── README.md           # This file
```

## Notes

- Backend connects to **existing** MySQL database
- Database tables must already exist (created via SQL schema)
- No database migration/initialization - tables are managed externally
- CORS enabled for frontend on `http://localhost:4200`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_USER` | Database username | `user` |
| `DB_PASSWORD` | Database password | - |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `3306` |
| `DB_NAME` | Database name | `3bodyproblem_coalpushat` |
| `SECRET_KEY` | Flask secret key | (auto-generated) |
| `FLASK_ENV` | Environment | `development` |
| `PORT` | Server port | `5000` |

## Troubleshooting

**Connection Error:**
- Verify database credentials in `.env`
- Ensure MySQL server is running
- Check database exists and tables are created

**Import Error:**
```bash
pip install -r requirements.txt
```

**Port Already in Use:**
Change port in `.env`:
```env
PORT=5001
```
