# Feature Design: CO/PO Management (CO/PO CRUD + Mapping)

## Goal
Add fully versioned Course Outcomes (CO) and Program Outcomes (PO) models, CRUD APIs, and CO→PO mapping with weights. Provide migrations, seed data, and unit tests.

## API Contract (subset)
- GET /api/v1/programs
- POST /api/v1/programs
- GET /api/v1/programs/{program_id}/pos
- POST /api/v1/programs/{program_id}/pos
- GET /api/v1/programs/{program_id}/courses
- POST /api/v1/programs/{program_id}/courses
- GET /api/v1/courses/{course_id}/cos
- POST /api/v1/courses/{course_id}/cos
- GET /api/v1/co_po_maps
- POST /api/v1/co_po_maps

## DB Changes
Add tables: `pos`, `cos`, `co_po_maps`. Models added under `backend/app/models/models.py`.

## Migration Plan
- Create Alembic migration adding the tables (idempotent).
- Ensure enums are created by SQLAlchemy metadata during `create_tables()` on startup.

## Seeds
- Add a seed script to create one Program, 3 POs, 1 Course, 3 COs, and CO→PO weights summing appropriately.

## Security
- Require `write_po`, `write_co`, `write_co_po` permissions for create operations.

## Tests
- Unit tests for CRUD endpoints (happy path + 404s)
- Integration test for CO→PO mapping and weight normalization

## Acceptance Criteria
- Endpoints return correct models and HTTP codes.
- CO→PO map rejects weights that cause sum > 1 for a CO.
- Seed script inserts realistic data for frontend dev.
