# 🚀 Apollo LMS - AI-Powered Learning Management System

> Production-grade, enterprise-ready LMS with AI-assisted grading, real-time proctoring, and comprehensive CO/PO mapping

## 🎯 Overview

Apollo LMS is a comprehensive educational platform designed for colleges and universities that combines:

- **🤖 AI-Powered Grading**: Intelligent assessment with ML-driven feedback
- **📊 CO/PO Mapping**: Automated curriculum outcome tracking and accreditation compliance
- **🎥 Real-Time Proctoring**: Advanced monitoring with lite anti-cheating measures
- **📱 Role-Based Access**: HOD, Teacher, Student roles with granular permissions
- **🔐 Enterprise Security**: JWT authentication, audit logs, data privacy compliance

## ✨ Key Features

### 🎓 Learning Outcomes & Assessment
- Complete CO (Course Outcome) and PO (Program Outcome) framework
- Weighted mapping with accreditation compliance tracking
- Automated attainment calculation and reporting
- Visual analytics dashboards for curriculum effectiveness

### 📚 Question Bank Management
- Support for 6 question types: MCQ, MSQ, True/False, Numeric, Descriptive, Coding, File-Upload
- AI-powered question generation based on syllabus and learning objectives
- Immutable question versioning for exam integrity
- Advanced search and filtering capabilities

### 📝 Intelligent Exam Engine
- Lifecycle management: Draft → Published → Started → Results Published
- Real-time WebSocket monitoring and student activity tracking
- Configurable proctoring rules and integrity monitoring
- Auto-submit at exam end with reconciliation for off-line clients
- Mobile-responsive design with accessibility compliance

### 🤖 AI Grading System
- Descriptive/Coding question AI scoring with configurable rubric strictness
- Manual override capabilities with audit trails
- Batch processing for large-scale assessments
- Quality metrics and teacher feedback integration
- Pluggable AI backend architecture

### 🔐 Security & Compliance
- Argon2 password hashing with configurable complexity
- JWT-based authentication with refresh tokens
- MFA support framework (TOTP, SMS, Email)
- Complete audit logging for all sensitive operations
- Role-based access control with fine-grained permissions
- WCAG AA accessibility compliance

### 📊 Analytics & Reporting
- SGPA/CGPA calculation with configurable grade bands
- Student performance analytics and weak topic identification
- Question difficulty analysis and discrimination indexing
- CO/PO attainment heatmaps and trend analysis
- Export capabilities: CSV, Excel, PDF reports
- Real-time exam monitoring dashboards

## 🏗️ Architecture

```
apollo-lms/
├── backend/                 # FastAPI microservice
│   ├── app/
│   │   ├── core/           # Auth, Security, Database, AI client
│   │   ├── models/         # SQLAlchemy models with relationships
│   │   ├── routes/         # API endpoints (REST + WebSocket)
│   │   ├── schemas/        # Pydantic models for validation
│   │   ├── services/       # Business logic layer
│   │   │   ├── grading.py          # AI grading orchestration
│   │   │   ├── reports.py          # Analytics & CO/PO calc
│   │   │   ├── bulk_operations.py  # User/file management
│   │   │   ├── ai_question_gen.py  # AI content generation
│   │   └── utils/
│   ├── alembic/            # Database migration scripts
│   ├── tests/              # Comprehensive test suite
│   │   ├── test_auth.py
│   │   ├── test_calculations.py
│   │   ├── test_exam_engine.py
│   ├── scripts/
│   ├── Makefile            # Development commands
│   └── requirements.txt
├── web/                    # React + TypeScript frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── contexts/       # React contexts (Auth, Theme)
│   │   ├── layouts/        # HOD/Teacher/Student dashboards
│   │   ├── pages/          # Route-based page components
│   │   ├── services/       # API client + WebSocket client
│   │   ├── types/          # TypeScript interfaces
│   │   ├── utils/          # Helper functions
│   │   └── hooks/          # Custom React hooks
│   ├── public/
│   │   ├── assets/         # Static files, images, docs
│   │   └── locales/        # i18n translations
│   ├── tests/              # E2E tests (Playwright)
│   └── docs/               # Component documentation
├── ai-worker/              # AI processing microservice
│   ├── app/                # Celery application
│   │   ├── tasks/          # Async AI processing tasks
│   │   │   ├── grading.py      # AI evaluation
│   │   │   ├── generation.py   # Content/question generation
│   │   │   ├── analysis.py     # Performance insights
│   │   └── core/           # ML models, embeddings
│   ├── models/             # Local AI models cache
│   ├── queue/              # Redis/message queues
│   └── logs/               # Processing metrics
├── infra/                  # Infrastructure as Code
│   ├── docker/             # Dockerfiles for each service
│   ├── k8s/                # Kubernetes manifests
│   ├── nginx.conf          # Reverse proxy configuration
│   ├── ssl/                # SSL certificates management
│   └── monitoring/         # EFK stack configuration
├── docs/                   # Documentation
│   ├── api/                # OpenAPI specifications
│   ├── ADR/                # Architecture Decision Records
│   ├── user-guides/        # User documentation
│   ├── security/           # Security handbook
│   └── deployment/         # Production deployment guides
└── pyrightconfig.json      # TypeScript configuration
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git & Git LFS (for large model files)
- Python 3.11+ (for local development)
- Node.js 18+ & npm (for frontend development)

### Production Setup (Docker)

```bash
# Clone and setup
git clone <repository-url> apollo-lms
cd apollo-lms

# Configure environment (copy and modify as needed)
cp .env.example .env
# Edit .env with your database credentials, JWT secrets, etc.

# Launch services
make dev

# Wait for services to start (check logs)
make logs

# Run database migrations
make migrate

# Seed with demo data
make seed
```

Access the application:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **AI Service**: http://localhost:8001/docs
- **Admin UI**: Auto-creates demo Hod account (hod@lms.edu / ChangeMe#1)

### Development Setup

```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend development (new terminal)
cd web
npm install
npm run dev  # Opens http://localhost:5173

# AI worker (new terminal)
cd ai-worker
pip install -r requirements.txt
celery -A app.tasks worker --loglevel=info
```

## 🎯 Demo & Testing

### Demo Accounts
- **HOD/Admin**: `hod@lms.edu` / `ChangeMe#1` - Full system access
- **Teacher**: `teacher@lms.edu` / `ChangeMe#1` - Course & exam management
- **Student**: `student@lms.edu` / `ChangeMe#1` - Exam participation

### Demo Workflow

1. **HOD Management**
   - Login as HOD, navigate to Users → Bulk Import
   - Upload CSV with student/teacher data
   - Create programs, courses, COs/POs
   - Assign course coordinators

2. **Teacher Workflow**
   - Login as Teacher, access assigned courses
   - Upload syllabus, generate questions with AI
   - Configure exam settings, schedule exam
   - Monitor real-time during exam
   - Review AI grades, provide overrides

3. **Student Experience**
   - Login, view available exams
   - Join exam within window, complete with proctoring
   - View results, CO/PO attainment analysis

### Performance Testing

```bash
# Run backend tests
make test

# End-to-end tests
npm run test:e2e

# AI model accuracy evaluation
cd ai-worker && python -m scripts.evaluate_models

# Load testing (requires artillery)
make load-test
```

## 🔧 Development Workflow

### Code Quality
```bash
# Backend
make lint           # Python code linting
make test           # Unit tests with coverage
make format         # Code formatting (black + isort)

# Frontend
npm run lint        # ESLint + Prettier
npm run type-check  # TypeScript validation
npm run test        # Component tests

# Full CI pipeline
make ci
```

### Database Management
```bash
# Development
make migrate         # Apply migrations
make seed           # Load demo data
make reset-db       # Reset database (⚠️ CAUTION)

# Production
alembic upgrade head  # Apply migrations
python -m scripts.backup_database  # Backup
```

### AI Model Management
```bash
# Training & evaluation
cd ai-worker
python -m scripts.train_grading_model
python -m scripts.evaluate_performance
python -m scripts.update_model_cache

# Model versioning
git lfs track "models/*.pkl"
git add models/
```

## 🔒 Security & Compliance

### Authentication Features
- **JWT with refresh tokens** - Configurable expiry (default: 15min access, 7day refresh)
- **Password policies** - Complexity rules, 2FA ready with TOTP framework
- **Account lockout** - Configurable threshold after failed attempts
- **Session management** - Active session tracking and forced logout
- **Forgot password** - Secure token-based reset (email/console for development)

### Authorization & Audit
- **RBAC with roles**: HOD/Teacher/Student/Coordinator
- **Permission matrix**: Fine-grained access control per resource
- **Audit logging**: All grading changes, user management, system events
- **Immutability**: Critical records (grades, CO mappings) cannot be deleted, only superseded

### Data Protection
- **PII encryption**: Sensitive fields (emails, phone) encrypted at rest
- **Privacy controls**: GDPR-compliant data retention policies
- **Backup security**: Encrypted database dumps with role-based access

### Exam Integrity
- **Real-time proctoring**: Browser events, tab switching, fullscreen monitoring
- **Time reconciliation**: Server-authoritative timing with offline client sync
- **Answer integrity**: Cryptographic hashes of submitted answers
- **Network monitoring**: Connection drop detection with recovery

## 📊 Analytics & CO/PO Compliance

### Student Performance
```python
# SGPA/CGPA Calculation
sgpa = calculate_sgpa(student_id, semester=4, academic_year="2024")
cgpa = calculate_cgpa(student_id, semesters_included=[1,2,3,4])

# CO Attainment Analysis
co_achievements = measure_co_attainment(course_id, exam_ids=[1,2,3,4])
po_achievements = measure_po_attainment(program_id, exam_filter)
```

### Question Bank Analytics
- **Difficulty Index**: Statistical analysis of question performance
- **Discrimination Index**: Correlation between high/low performer scores
- **CO Mapping**: Automated verification of learning outcome coverage
- **AI Insights**: Pattern analysis for improving question quality

### Accreditation Reporting
```python
# Generate compliance report
report = ComplianceService.generate_accreditation_report(
    program_id=program_id,
    cycle="NBA_2023",  # NBA, NAAC, etc.
    output_format="pdf",
    include_trends=True
)
```

## 🔗 API Documentation

### REST API Endpoints

#### Authentication
```http
POST /auth/login              # JWT login
POST /auth/register          # First-time registration
POST /auth/refresh           # Renew access token
POST /auth/forgot-password   # Password reset request
```

#### User Management (HOD/Admin)
```http
GET  /users                  # List users (paginated)
POST /users                  # Create user
PUT  /users/{user_id}        # Update user
POST /users/bulk-import      # CSV bulk import
POST /users/bulk-reset-password # Batch password reset
```

#### Exam Management
```http
GET  /exams                 # List exams
POST /exams                 # Create exam
GET  /exams/{exam_id}       # Exam details
PUT  /exams/{exam_id}       # Update exam
POST /exams/{exam_id}/publish # Publish exam
POST /exams/{exam_id}/questions/bulk # Add questions to exam
```

#### Student Operations
```http
GET  /student/exams         # View available exams
POST /student/exams/{exam_id}/join # Join exam
POST /student/answers       # Submit answer
POST /student/exams/{exam_id}/submit # End exam
GET  /student/results/{attempt_id} # View results
```

#### AI Services
```http
POST /ai/grade/descriptive  # AI grade descriptive answer
POST /ai/questions/generate # Generate questions from syllabus
POST /ai/content/summarize  # Generate course summaries
POST /ai/study-plan/create  # Create personalized study plans
```

### WebSocket Real-Time
```javascript
// Exam monitoring (Teacher/HOD)
ws.subscribe('exam.monitor.{exam_id}', (data) => {
    console.log('Student activity:', data);
});

// Time warnings (Student)
ws.subscribe('user.{user_id}', (message) => {
    if (message.type === 'time_warning') {
        displayWarning(message.minutes_remaining);
    }
});
```

## 🧪 Testing Strategy

### Unit Through Integration Tests
```bash
# Backend tests
pytest tests/ -v --cov=app --cov-report=term-missing

# Key test areas:
# - Authentication flows (login, refresh, MFA)
# - Exam lifecycle (join → submit → auto-submit)
# - Grade calculations (SGPA/CGPA, CO/PO attainment)
# - Lock-in policy enforcement
# - Bulk operations (user import, grading)
# - AI grading accuracy and override flows
```

### Component Tests (Frontend)
```bash
# React Testing Library + Vitest
npm run test:unit         # Component unit tests
npm run test:integration  # Integration tests
npm run test:accessibility # Accessibility validation
```

### E2E Tests (Full System)
```bash
# Playwright end-to-end
npm run test:e2e -- --headed  # Visual testing
npm run test:e2e              # Headless CI

# Test scenarios:
# 1. Student registration → password change → profile completion
# 2. HOD bulk imports users → assigns coordinators
# 3. Teacher uploads syllabus → AI generates questions → schedules exam
# 4. Student joins exam → answers questions → exam auto-ends
# 5. Teacher reviews AI grades → provides overrides → publishes results
```

## 🚀 Deployment & Scaling

### Docker Production Setup
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    image: apollo/backend:latest
    environment:
      - ENVIRONMENT=production
      - WORKERS=4
    volumes:
      - ssl:/ssl:ro
      - backups:/backups

  ai-worker:
    image: apollo/ai-worker:latest
    deploy:
      replicas: 3
    environment:
      - HF_TOKEN=${HF_TOKEN}

  postgres:
    image: postgres:15-alpine
    volumes:
      - ./backups:/backups
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ssl:/ssl:ro
```

### Kubernetes Scaling
```yaml
# k8s/backend-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apollo-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: apollo-backend
  template:
    spec:
      containers:
      - name: backend
        image: apollo/backend:latest
        env:
        - name: DATABASE_URL
          value: "postgresql://"
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### Monitoring & Observability
- **Metrics**: Prometheus scraped from FastAPI `/metrics` endpoint
- **Logs**: Centralized logging with ELK stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: OpenTelemetry integration for distributed tracing
- **Health Checks**: Automatic SLO monitoring and alerting

## 🤝 Contributing

### Development Workflow
1. Fork and create feature branch
2. Follow conventional commit format
3. Add tests for new functionality
4. Update documentation
5. Create pull request with detailed description

### Code Guidelines
- **Backend**: Follow SOLID principles, type hints required
- **Frontend**: Functional components with TypeScript strict mode
- **API**: RESTful design with JSON API spec compliance
- **Security**: Input validation, output escaping, no hardcoded secrets

## 📚 Resources

### Architecture Decisions
- **ADR-001**: JWT vs Sessions for authentication
- **ADR-002**: SQLAlchemy vs raw SQL queries
- **ADR-003**: AI model hosting (local vs external)
- **ADR-004**: WebSocket implementation choice
- **ADR-005**: Proctoring strategy and privacy considerations

### Security Documentation
- Threat modeling documentation
- Penetration testing reports
- Compliance checklists (GDPR, WCAG AA)
- Data retention policy

### Performance Benchmarks
- Concurrent user capacity testing
- AI grading response times
- Database query optimization metrics
- CDN integration for file serving

## 📞 Support

- **Documentation**: [`https://docs.apollo-lms.edu`](https://docs.apollo-lms.edu)
- **API Reference**: [`https://api.apollo-lms.edu/docs`](https://api.apollo-lms.edu/docs)
- **Issues**: GitHub Issues for bug reports and feature requests
- **Security**: `security@apollo-lms.edu` for security concerns

## 📄 License

Licensed under the MIT License. See [LICENSE](LICENSE) for full text.

---

**🎓 Built with ❤️ for educational excellence. Empowering teachers, engaging students, ensuring quality education.**
