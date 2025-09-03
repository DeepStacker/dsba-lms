## GitHub Copilot — repository guide (DSBA LMS)

This file gives focused, actionable context an AI coding agent needs to be immediately productive in this repo.

Checklist for the agent
- Understand the service boundary: `backend` (FastAPI API) and `ai-service` (AI microservice). ✅
- Know where runtime configuration lives: `backend/app/core/config.py` and env vars (.env). ✅
- How to run & test locally: `make dev`, `make migrate`, `make seed`, `make test`. ✅
- Key integration patterns: internal AI HTTP API, JWT auth header semantics, and CORS handling. ✅

Big picture (short)
- Components: `backend/` (FastAPI, DB, business logic), `ai-service/` (LLM adapters + REST endpoints), `web/` (React + TS client). See `README.md` for architecture diagram.
- Communication:
  - Frontend -> Backend: standard REST + JWT in `Authorization: Bearer <token>` (see `web/src/utils/api.ts`).
  - Backend -> AI service: HTTP POST to AI endpoints (default `http://ai-service:8001`) with internal auth header `X-Internal-Auth` (see `backend/app/core/ai_client.py`).

Where to look (concrete files)
- Backend app entry: `backend/app/main.py` — registers routers, calls `create_tables()` on startup.
- DB config and env pattern: `backend/app/core/config.py` — uses Pydantic BaseSettings; note special pattern: `allow_origins_0`, `allow_origins_1`, ... and properties `allow_origins`, `async_database_url`.
- DB bootstrap: `backend/app/core/database.py` — async SQLAlchemy engine and `create_tables()` used at startup.
- AI client (backend): `backend/app/core/ai_client.py` — retry + exponential backoff, simple circuit-breaker, and a fallback grading implementation; useful for understanding error handling and expected AI response shape.
- AI service entry: `ai-service/app/main.py` and adapters under `ai-service/app/core/llm_adapter.py` (providers: `mock`, `openai`).
- Frontend API conventions: `web/src/utils/api.ts` — singleton `ApiClient`, token refresh flow, Vite envs `VITE_API_URL` and `VITE_AI_SERVICE_URL`.

Project-specific conventions & patterns
- Environment & config
  - Settings are loaded via Pydantic `BaseSettings` and an `.env` file; some config values are split into numbered env vars (CORS origins). Change values in `.env` or set env vars for docker.

- Async DB
  - Uses SQLAlchemy async engine + `sessionmaker(class_=AsyncSession)`; `create_tables()` is invoked in backend startup rather than running sync migrations automatically.

- AI integration
  - Backend calls AI via `AIClient._make_request(endpoint, payload)`; expected success returns JSON with domain fields (examples: grading returns `ai_score`, `per_criterion`, `feedback_bullets`). If AI is unavailable, backend relies on `_fallback_grading()` — preserve its response shape when changing AI outputs.
  - AI service enforces an internal header `X-Internal-Auth`. Default token shown in code: `internal_token_change_me` — update `.env` and both sides when wiring real secret.
  - To change LLM provider, edit `ai-service/app/core/llm_adapter.py` or instantiate `get_llm_adapter('openai', api_key=...)` and ensure the `ai-service` process has the API key.

- Error handling and observability
  - `AIClient` uses retries and a circuit breaker; when adding new AI calls, follow same pattern (exponential backoff, record_failure / record_success).
  - Sentry optional initialization in `backend/app/main.py` (controlled by `sentry_dsn` setting).

Developer workflows (commands you can use)
- Local dev (recommended):
  - Root: `make dev` — brings up the stack via docker-compose (see `README.md`).
  - Backend only: `cd backend` then `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (or use `pip install -r requirements.txt`).
  - AI service only: `cd ai-service` then `uvicorn app.main:app --reload --host 0.0.0.0 --port 8001`.

- Tests & quality
  - Backend unit tests: `cd backend && pytest -q` (see `backend/tests/`).
  - Lint/format per README: `make lint`, `make format`, `npm run lint` in `web`.

Quick examples (concrete)
- Call AI grading endpoint (internal auth required):
```
curl -X POST http://localhost:8001/grade/descriptive \
  -H 'Content-Type: application/json' \
  -H 'X-Internal-Auth: internal_token_change_me' \
  -d '{"answer":"...","model_answer":"...","rubric_json":{}}'
```

- Where to change CORS origins: edit `backend/app/core/config.py` or set `allow_origins_0` / `allow_origins_1` env vars.

Integration notes for edits
- Maintain API shapes used by frontend and the fallback logic in `AIClient._fallback_grading()` when changing AI outputs.
- When adding new backend routes, register them in `backend/app/main.py` using `app.include_router(...)` with the `prefix` conventions already in use (e.g. `/api/v1`).
- Tests rely on real DB migrations in `alembic/`; run `make migrate` before running integration tests.

What not to change lightly
- The `X-Internal-Auth` header and payload/response contract between backend and `ai-service` — breaking these will quickly cause silent failures and fallbacks.
- The `allow_origins_*` env pattern; replace it only if you update `Settings.allow_origins` behavior accordingly.

If something is unclear or missing
- Tell me which area you want expanded (local debugging, CI, data migrations, AI model wiring). I can iterate the file to add more examples or a short troubleshooting checklist.

Files referenced in this doc (quick map)
- backend/app/main.py
- backend/app/core/config.py
- backend/app/core/ai_client.py
- backend/app/core/database.py
- backend/alembic/
- ai-service/app/main.py
- ai-service/app/core/llm_adapter.py
- web/src/utils/api.ts
- README.md
