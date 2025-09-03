# Saturn APOLLO LMS - PRD & SRS

## Project Overview

**Apollo LMS (Academic Program Outcomes Learning and Operations Layer)** is an enterprise-grade Learning Management System designed specifically for educational institutions with accounting and engineering accreditation requirements.

## Executive Summary

A production-ready LMS platform featuring:
- **AI-powered Assessment Grading** with rubric-based evaluation for descriptive and coding questions
- **Comprehensive CO/PO Management** with version control and weighted attainment mapping
- **Advanced Analytics** including CO/PO attainment heatmaps and accreditation reports
- **Complete RBAC System** with Admin(HOD) → Teacher → Student hierarchy
- **Automated Proctoring-lite** with risk scoring and event monitoring
- **SGPA/CGPA Calculations** with configurable grading bands and transcript generation
- **Full Audit Trail** with hash-chained immutable logs
- **Production Security** with TLS, PII encryption, and zero-trust principles

## Functional Requirements

### 1. User Management & Authentication

#### 1.1 User Roles and Permissions
- **Admin (HOD)**: Full system administration, user management, overrides with audit trails
- **Teacher**: Course management, question banks, exam scheduling, grading, analytics access
- **Student**: Exam participation, results viewing, profile access
- **Coordinator**: Delegated administrative functions for specific programs

#### 1.2 Authentication Features
- JWT-based authentication with short-lived access tokens (15 min) and refresh tokens (7 days)
- Argon2id password hashing with time/memory cost configuration
- Mandatory first-login password change for imported users
- Optional MFA for staff accounts using TOTP
- Secure password reset workflows with audit logging

#### 1.3 Account Management
- No self-registration; admin-only account creation
- Bulk CSV/XLSX user import with validation
- Role-based access controls with middleware enforcement
- Account locking/unlocking with audit trails
- Bulk password reset capabilities

### 2. Program Management

#### 2.1 Program Structure
- Hierarchical organization: Program → Courses → Learning Outcomes (COs/POs)
- Program years and versioning
- Configurable grade bands (O/A+/A/B+/B/C+/...) with configurable credit systems
- Accreditation compliance tracking

#### 2.2 CO/PO Management
- **Program Outcomes (POs)**: Institutional-level learning goals
- **Course Outcomes (COs)**: Course-specific learning objectives
- **CO-PO Mapping**: Weighted relationships between course and program outcomes
- Version control for outcome definitions (immutable after use)
- Bloom's taxonomy classification for COs

### 3. Question Bank & Assessment Engine

#### 3.1 Question Types
- Multiple Choice Questions (MCQ)
- Multiple Selection Questions (MSQ)
- True/False questions
- Numeric answer questions
- Descriptive/essay questions
- Coding assessment questions
- File upload questions

#### 3.2 Question Management
- Centralized question bank with search and filtering
- CO tagging for question-outcome mapping
- AI-powered question generation (flagged "generated", editable)
- Rubric-based grading system for subjective questions
- Question versioning and reuse tracking

#### 3.3 Exam Engine
- Multi-stage lifecycle: Draft → Published → Started → Ended → Results Published
- Configurable join window (300s default)
- Server-authoritative timing with anti-cheating measures
- Real-time monitoring and analytics
- Auto-submit functionality at exam end
- Autosave with ≤5 second intervals

### 4. AI Grading & Generation Services

#### 4.1 AI Grading
- **Descriptive Questions**: Rubric-based AI scoring with criterion-wise evaluation
- **Coding Questions**: Static analysis and execution-based grading
- Teacher override capabilities with audit trails
- Confidence scores and AI suggestion annotations
- Bulk grading workflow with AI pre-assessment

#### 4.2 AI Generation
- **Question Generation**: Create questions from syllabus and learning outcomes
- **Lesson Planning**: Automatic learning material suggestions
- **Content Tagging**: Automated CO/PO classification
- **Pluggable Architecture**: Support for multiple LLM providers

### 5. Proctoring & Security

#### 5.1 Proctoring-lite Features
- Tab switch detection and logging
- Focus loss monitoring
- Network connectivity monitoring
- Clipboard paste prevention
- Fullscreen mode enforcement
- Risk scoring algorithms with configurable weights

#### 5.2 Security Features
- Comprehensive audit logging for all mutations
- Hash-chained audit trail (blockchain-inspired)
- PII field-level encryption
- Role-based data access controls
- Session management and invalidation

### 6. Analytics & Reporting

#### 6.1 CO/PO Attainment Analytics
- Student-level CO/PO achievement tracking
- Class-level aggregate analytics
- Program-level attainment heatmaps
- Accreditation reporting formats
- Direct attainment calculation formulas

#### 6.2 Grade Analytics
- SGPA/CGPA calculations with weighted averages
- Transcript generation with PDF/CSV export
- Grade distribution analytics
- Performance trend analysis
- Risk flagging for struggling students

### 7. Lock-in Policies

#### 7.1 Result Publication Lock-in
- Default 7-day lock period after exam results publication
- Weekly Saturday lock option (23:59 cutoff)
- HOD override workflow with mandatory justification
- Full audit trail for all overrides

#### 7.2 Data Integrity
- Prevention of post-publication modifications
- Hash-based transaction integrity
- Configurable lock period settings

## Non-Functional Requirements

### Performance
- P95 response time < 2 seconds for all operations
- System availability ≥ 99.5%
- Support for 1000+ concurrent users
- Database optimization for large result sets

### Security
- TLS 1.3 encryption for all communications
- Argon2id password hashing
- CSRF protection for web interfaces
- Rate limiting and DDoS protection
- Regular security audits and penetration testing

### Compliance
- WCAG AA accessibility standards
- GDPR compliance for data handling
- Accreditation data export capabilities
- Grade scale configurability for different institutions

### Scalability
- Stateless API design
- Horizontal scaling capabilities
- Database indexing and optimization
- Caching layer for performance

## Technical Architecture

- **Backend**: FastAPI (Python 3.11) with async database operations
- **Database**: PostgreSQL with ACID compliance
- **Cache**: Redis for session management and performance
- **Background Jobs**: Celery/RQ for AI processing and bulk operations
- **Frontend**: React 18 + TypeScript with role-based routing
- **AI Services**: Separate microservice with REST API
- **Monitoring**: Prometheus metrics, structured logging, Sentry integration
- **Deployment**: Docker containers with Kubernetes readiness

## Acceptance Criteria

### AT-01: Authentication & Authorization
- All role-based access controls enforced programmatically
- JWT tokens correctly validated and refreshed
- Password reset flows secure and auditable

### AT-02: Question Bank Management
- All question types supported with proper validation
- AI generation flags work correctly
- Search and tagging functionality operational

### AT-03: Exam Engine Functionality
- Timer synchronization works across different time zones
- Auto-submit functionality prevents cheating
- Live monitoring dashboard updates in real-time

### AT-04: CO/PO Attainment Calculation
- Mathematical formulas correctly implemented
- Report generation accurate and performant
- Accreditation compliance formats available

### AT-05: SGPA/CGPA Calculation
- Grade band configurations properly applied
- Transcript generation includes all required fields
- PDF/CSV export functionality works correctly

### AT-06: Lock-in Policy Enforcement
- Standard lock periods enforced
- HOD override workflow has proper approvals
- All overrides logged with justification and audit trail

### AT-07: AI Grading Integration
- AI service calls return within reasonable timeouts
- Grading results have confidence scores
- Teacher override workflow preserves AI suggestions

### AT-08: Audit & Compliance
- All mutations logged with before/after states
- Hash chain integrity maintained
- Audit reports exportable in compliance formats

### AT-09: Proctoring & Risk Assessment
- Event detection accurate for browser events
- Risk scoring algorithm configurable and mathematically sound
- Dashboard displays real-time risk indicators

### AT-10: Bulk Operations
- CSV/XLSX import with validation error reporting
- Bulk grading operations handle large datasets efficiently
- Progress tracking for long-running operations

## Implementation Phases

### Phase A: Core Platform (Backend + Database)
1. User authentication and RBAC system
2. Database schema and migrations
3. Basic CRUD operations for all entities
4. Audit logging framework

### Phase B: Advanced Features
1. AI grading service integration
2. CO/PO mapping and analytics
3. Exam engine with real-time features
4. Bulk import/export capabilities

### Phase C: Frontend & UX
1. React application with role-based routing
2. Exam interface with proctoring-lite
3. Analytics dashboards and reporting
4. Admin interface for system management

### Phase D: Production Readiness
1. Monitoring and observability
2. CI/CD pipeline
3. Performance optimization
4. Security hardening and compliance

## Success Metrics

- **Performance**: <2s p95 response time maintained
- **Reliability**: 99.5%+ uptime achieved
- **Security**: Zero security incidents in production
- **Compliance**: Full accreditation audit compliance achieved
- **User Satisfaction**: Positive feedback from teachers and students
- **Adoption**: Successful deployment in 80%+ target departments

## Risk Mitigation

### Technical Risks
- **AI Service Reliability**: Implement circuit breakers and fallback mechanisms
- **Database Performance**: Comprehensive indexing and query optimization
- **Real-time Requirements**: WebSocket connection management and failover

### Business Risks
- **User Adoption**: Comprehensive training and support programs
- **Regulatory Compliance**: Regular audits and compliance reviews
- **Scalability**: Cloud-based infrastructure with auto-scaling

### Operational Risks
- **Data Privacy**: Encryption and access control implementation
- **Backup and Recovery**: Complete disaster recovery procedures
- **Monitoring**: 24/7 monitoring and alerting systems