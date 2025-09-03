# Apollo LMS API Documentation

## Overview

Apollo LMS provides a comprehensive REST API for Learning Management System operations. The API is organized into logical modules with consistent authentication and error handling.

## Authentication

All endpoints (except login/refresh) require JWT authentication:

```
Authorization: Bearer <access_token>
```

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Role-Based Access Control

- **Admin**: Full system access, user management, audit logs
- **Teacher**: Course management, exam creation, grading, analytics
- **Student**: Exam participation, results viewing

## Endpoints Summary

### Authentication
| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| POST | `/auth/login` | User login | Public |
| POST | `/auth/refresh` | Refresh access token | Authenticated |
| POST | `/auth/logout` | User logout | Authenticated |

### User Management
| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| POST | `/users` | Create user | Admin |
| GET | `/users` | List users | Admin, Teachers |
| GET | `/users/me` | Get current user | Authenticated |
| PUT | `/users/me` | Update profile | Authenticated |
| DELETE | `/users/{id}` | Delete user | Admin |
| POST | `/users/import` | CSV import | Admin |
| POST | `/users/reset-password-bulk` | Reset multiple passwords | Admin |

### Programs & Outcomes
| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| GET | `/programs/programs` | List programs | Admin, Teachers |
| POST | `/programs/programs` | Create program | Admin |
| GET | `/programs/{id}/pos` | Get program POs | Admin, Teachers |
| POST | `/programs/{id}/pos` | Create PO | Admin |
| GET | `/programs/{id}/courses` | Get program courses | All |
| POST | `/programs/{id}/courses` | Create course | Admin |
| GET | `/courses/{id}/cos` | Get course COs | All |
| POST | `/courses/{id}/cos` | Create CO | Teachers |
| GET | `/co_po_maps` | Get CO-PO mappings | All |
| POST | `/co_po_maps` | Create CO-PO mapping | Teachers |

### Questions Bank
| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| GET | `/questions/questions` | List questions | Teachers |
| POST | `/questions/questions` | Create question | Teachers |
| PUT | `/questions/{id}` | Update question | Teachers |
| DELETE | `/questions/{id}` | Delete question | Teachers |
| GET | `/questions/{id}/options` | Get question options | Teachers |
| POST | `/questions/{id}/options` | Add option | Teachers |
| POST | `/questions/ai/generate` | AI generate questions | Teachers |
| GET | `/questions/search` | Search questions | Teachers |
| GET | `/questions/stats/course/{id}` | Question statistics | Teachers |

### Exams & Assessments
| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| GET | `/exams/exams` | List exams | All |
| POST | `/exams/exams` | Create exam | Teachers |
| GET | `/exams/{id}` | Get exam details | All |
| PUT | `/exams/{id}` | Update exam | Teachers |
| DELETE | `/exams/{id}` | Delete exam | Teachers |
| GET | `/exams/{id}/attempts` | Get exam attempts | Teachers |
| POST | `/attempts` | Start/join exam | Students |
| PUT | `/attempts/{id}` | Update attempt | Students |
| GET | `/attempts/{id}/responses` | Get responses | Students, Teachers |
| POST | `/responses` | Submit response | Students |
| PUT | `/responses/{id}` | Update response | Teachers |

### Grading & Assessment
| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| POST | `/grading/ai/descriptive/{response_id}` | AI grade response | Teachers |
| POST | `/grading/bulk/ai` | Bulk AI grading | Teachers |
| PUT | `/grading/override/{response_id}` | Teacher override grade | Teachers |
| POST | `/grading/bulk/override` | Bulk grade overrides | Teachers |
| GET | `/grading/exam/{exam_id}/progress` | Grading progress | Teachers |

### Analytics & Reports
| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| GET | `/reports/analytics/overview` | System analytics | Teachers, Admin |
| GET | `/reports/exam/{id}` | Exam report | Teachers, Admin |
| GET | `/reports/Program/{id}` | Program report | Teachers, Admin |
| GET | `/reports/student/{id}/sgpa` | Student SGPA | Students, Teachers, Admin |
| GET | `/reports/student/{id}/cgpa` | Student CGPA | Students, Teachers, Admin |
| POST | `/reports/export/pdf/{type}` | Export PDF | Teachers, Admin |
| POST | `/reports/export/excel/{type}` | Export Excel | Teachers, Admin |

### Admin Functions
| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| GET | `/admin/audit/logs` | Audit logs | Admin |
| GET | `/admin/audit/entity/{type}/{id}` | Entity audit history | Admin |
| GET | `/admin/stats/system` | System statistics | Admin |
| POST | `/admin/audit/export` | Export audit logs | Admin |
| PUT | `/admin/config/grade-bands` | Update grade bands | Admin |
| GET | `/admin/locks` | List lock windows | Admin |
| POST | `/admin/locks` | Create lock window | Admin |
| PUT | `/admin/locks/{id}` | Update lock window | Admin |
| POST | `/admin/locks/{id}/override` | Override lock window | Admin |

## Error Responses

Standard error format:
```json
{
  "detail": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2023-09-03T10:00:00Z"
}
```

Common error codes:
- `401`: Unauthorized
- `403`: Forbidden (insufficient permissions)
- `404`: Resource not found
- `409`: Conflict (e.g., duplicate email)
- `422`: Validation error
- `500`: Internal server error

## Data Formats

### Question Types
- `mcq`: Multiple Choice (single correct)
- `msq`: Multiple Selection (multiple correct)
- `tf`: True/False
- `numeric`: Numeric answer
- `descriptive`: Essay/description
- `coding`: Programming question
- `file_upload`: File submission

### Exam Statuses
- `draft`: Not published
- `published`: Available for students
- `started`: Students taking exam
- `ended`: Time expired
- `results_published`: Grades available

### Attempt Statuses
- `not_started`: Student not started
- `in_progress`: Student taking exam
- `submitted`: Completed and submitted
- `auto_submitted`: Automatically submitted

### Proctor Events
- `tab_switch`: Student switched tabs
- `focus_loss`: Browser lost focus
- `network_drop`: Network disconnection
- `paste`: Paste operation detected
- `fullscreen_exit`: Exited fullscreen mode

## Rate Limiting

API endpoints are rate-limited:
- General: 100 requests/minute
- Auth: 10 requests/minute
- AI grading: 20 requests/minute (per user)

## File Uploads

Maximum file sizes:
- Question files: 5MB
- Submissions: 10MB
- Bulk imports: 25MB

## Pagination

List endpoints support pagination:
```
GET /api/v1/resource?page=1&limit=50
```

Response format:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "limit": 50,
  "pages": 3
}
```

## WebSocket Integration

Real-time features available via WebSocket:
- `/ws/exam/{exam_id}`: Live exam monitoring
- `/ws/notifications`: User notifications

## API Versioning

Current API version: `v1`
- Maintains backward compatibility
- New major features in `v2`+

## Testing the API

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@college.edu","password":"admin123"}'

# Get current user
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <your_token>"
```

## Production Considerations

- Use HTTPS in production
- Implement request/response compression
- Configure proper CORS settings
- Enable API gateway for rate limiting
- Use database connection pooling
- Implement comprehensive logging and monitoring

---

For interactive API documentation, visit: `http://localhost:8000/docs`