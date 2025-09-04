# DSBA LMS Backend

AI-Powered Learning Management System Backend built with FastAPI, PostgreSQL, and comprehensive real-time features.

## Features Implemented

### ✅ Core Authentication & Authorization
- JWT-based authentication with refresh tokens
- Role-based access control (Admin, Teacher, Student, Coordinator)
- Password reset functionality
- First-time login flow
- Comprehensive permission system

### ✅ User Management
- Complete CRUD operations for users
- Bulk user import/export (CSV/Excel)
- Account suspension/reactivation
- Profile management
- Audit logging for all user operations

### ✅ Academic Structure Management
- Programs, Courses, Course Outcomes (COs), Program Outcomes (POs)
- CO-PO mapping with weight validation
- Class sections and student enrollments
- Academic calendar management

### ✅ Exam Management System
- Complete exam lifecycle (Draft → Published → Started → Ended → Results Published)
- Real-time exam monitoring via WebSocket
- Auto-submission at exam end time
- Join window enforcement
- Proctoring event logging
- Multiple question types (MCQ, MSQ, TF, Numeric, Descriptive, Coding, File Upload)

### ✅ Grading System
- Auto-grading for objective questions
- AI-assisted grading for descriptive answers
- Teacher override capabilities
- Bulk grade upload (CSV/Excel)
- Comprehensive grading status tracking

### ✅ Internal Marks Management
- Component-wise internal assessment
- Weighted score calculations
- Bulk marks upload
- Internal marks reporting

### ✅ SGPA/CGPA Calculation
- Automatic grade point calculation
- Semester-wise SGPA computation
- Overall CGPA tracking
- Grade band configuration
- Academic transcripts

### ✅ Analytics & Reporting
- CO/PO attainment analysis
- Student performance analytics
- Class performance comparisons
- Exportable reports (PDF/CSV/JSON)
- Accreditation-ready reports

### ✅ AI Integration
- Question generation from course content
- Auto-grading with confidence scores
- Content analysis and topic extraction
- CO mapping suggestions
- Performance prediction

### ✅ Real-time Features
- WebSocket-based exam monitoring
- Live student activity tracking
- Real-time notifications
- Auto-submit service
- Proctor event streaming

### ✅ Lock Window System
- 7-day lock-in policy for grades
- Configurable lock windows
- Override capabilities for admins
- Audit trail for all overrides

### ✅ Notification System
- Real-time notifications
- Bulk notification sending
- System-generated alerts
- Notification statistics

### ✅ Audit & Compliance
- Comprehensive audit logging
- Hash-chained audit entries for integrity
- Immutable audit trail
- Compliance reporting

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with AsyncPG
- **ORM**: SQLAlchemy 2.0 (Async)
- **Authentication**: JWT with python-jose
- **Password Hashing**: Argon2
- **Real-time**: WebSocket
- **Data Processing**: Pandas, OpenPyXL
- **HTTP Client**: HTTPX (for AI service)
- **Monitoring**: Sentry (optional)

## Project Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── audit.py          # Audit logging system
│   │   ├── config.py         # Configuration management
│   │   ├── database.py       # Database connection
│   │   ├── dependencies.py   # FastAPI dependencies
│   │   ├── init_db.py        # Database initialization
│   │   ├── security.py       # Authentication & RBAC
│   │   └── startup.py        # Application lifecycle
│   ├── models/
│   │   └── models.py         # SQLAlchemy models
│   ├── routes/
│   │   ├── admin.py          # Admin operations
│   │   ├── ai_service.py     # AI integration
│   │   ├── auth.py           # Authentication
│   │   ├── exams.py          # Exam management
│   │   ├── grading.py        # Grading system
│   │   ├── internal_marks.py # Internal assessments
│   │   ├── lock_windows.py   # Lock window management
│   │   ├── notifications.py  # Notification system
│   │   ├── programs.py       # Academic structure
│   │   ├── questions.py      # Question bank
│   │   ├── reports.py        # Analytics & reporting
│   │   ├── users.py          # User management
│   │   └── websocket_routes.py # Real-time features
│   ├── schemas/
│   │   ├── common.py         # Common schemas
│   │   ├── exam.py           # Exam-related schemas
│   │   ├── grading.py        # Grading schemas
│   │   ├── internal_marks.py # Internal marks schemas
│   │   ├── lock_window.py    # Lock window schemas
│   │   ├── notification.py   # Notification schemas
│   │   ├── program.py        # Program schemas
│   │   ├── question.py       # Question schemas
│   │   └── user.py           # User schemas
│   ├── services/
│   │   ├── analytics.py      # Analytics service
│   │   ├── grade_calculation.py # SGPA/CGPA service
│   │   └── websocket.py      # WebSocket service
│   └── main.py               # FastAPI application
├── alembic/                  # Database migrations
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Setup Instructions

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb DSBA

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://DSBA:DSBA@localhost/DSBA"
export JWT_SECRET="your-super-secret-jwt-key-change-this-in-production"
export AI_SERVICE_URL="http://localhost:8001"
export AI_SERVICE_TOKEN="internal_token_change_me"
```

### 3. Database Initialization

```bash
# Initialize database with tables and seed data
python -m app.core.init_db
```

### 4. Start AI Service (Mock)

```bash
cd ../ai-service
pip install -r requirements.txt
python app/main.py
```

### 5. Start Backend Server

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Default Credentials

After running the database initialization:

- **Admin**: `admin` / `admin123`
- **Teacher**: `teacher1` / `teacher123`
- **Student**: `student1` / `student123`

## API Documentation

Once the server is running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Key API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/forgot-password` - Password reset request
- `GET /auth/me` - Get current user info

### User Management
- `GET /users/` - List users
- `POST /users/` - Create user (Admin only)
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

### Exam Management
- `POST /exams/` - Create exam
- `POST /exams/{id}/publish` - Publish exam
- `POST /exams/{id}/start` - Start exam
- `POST /exams/{id}/end` - End exam
- `GET /exams/{id}/monitor` - Real-time monitoring

### Grading
- `POST /responses/{id}/grade` - Grade response
- `POST /responses/{id}/ai-grade` - AI-assisted grading
- `POST /exams/{id}/bulk-grade` - Bulk grade upload

### Analytics
- `GET /analytics/student/{id}/sgpa-cgpa` - Student SGPA/CGPA
- `GET /analytics/class/{id}/co-attainment` - CO attainment
- `GET /analytics/class/{id}/po-attainment` - PO attainment

### Real-time Features
- `WS /api/v1/ws/exam/{attempt_id}` - Student exam WebSocket
- `WS /api/v1/ws/monitor/{exam_id}` - Exam monitoring WebSocket

## Configuration

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://DSBA:DSBA@localhost/DSBA

# JWT
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRES_MIN=15
REFRESH_EXPIRES_DAYS=7

# AI Service
AI_SERVICE_URL=http://localhost:8001
AI_SERVICE_TOKEN=internal_token_change_me

# CORS
ALLOW_ORIGINS_0=http://localhost:3000
ALLOW_ORIGINS_1=http://localhost:3001

# Features
FEATURE_AI=true
FEATURE_ANALYTICS=true
FEATURE_TELEMETRY=true

# Monitoring (Optional)
SENTRY_DSN=your-sentry-dsn
```

## Database Schema

The system uses a comprehensive relational schema with:

- **Users & Roles**: Multi-role user management
- **Academic Structure**: Programs → Courses → COs → POs
- **Assessments**: Exams → Questions → Responses
- **Grading**: Internal marks, SGPA/CGPA calculations
- **Audit**: Complete audit trail with hash chaining
- **Real-time**: WebSocket connection management

## Security Features

- **Authentication**: JWT with refresh tokens
- **Authorization**: Role-based permissions
- **Password Security**: Argon2 hashing
- **Audit Trail**: Immutable audit logs
- **CORS**: Configurable origins
- **Rate Limiting**: Built-in FastAPI features
- **Input Validation**: Pydantic schemas

## Performance Features

- **Async/Await**: Full async implementation
- **Connection Pooling**: SQLAlchemy async engine
- **Efficient Queries**: Optimized database queries
- **Caching**: Ready for Redis integration
- **WebSocket**: Real-time communication
- **Background Tasks**: Auto-submit service

## Monitoring & Observability

- **Health Checks**: `/health` endpoint
- **Structured Logging**: Comprehensive logging
- **Metrics**: Ready for Prometheus integration
- **Error Tracking**: Sentry integration
- **Audit Logs**: Complete operation tracking

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t dsba-lms-backend .

# Run container
docker run -p 8000:8000 -e DATABASE_URL=... dsba-lms-backend
```

### Production Considerations

1. **Environment Variables**: Use proper secrets management
2. **Database**: Use managed PostgreSQL service
3. **Load Balancing**: Use multiple workers
4. **Monitoring**: Set up proper monitoring
5. **Backup**: Regular database backups
6. **SSL**: Use HTTPS in production

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests
3. Update documentation
4. Follow Python best practices
5. Use type hints throughout

## License

This project is part of the DSBA LMS system.