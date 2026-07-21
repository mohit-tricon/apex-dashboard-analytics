# apex-dashboard-analytics

A FastAPI analytics service using **structlog**, **pydantic**
(+ pydantic-settings), **uvicorn**, and **pytest**.

## Requirements

- Python >= 3.11

## Setup

Create and activate a virtual environment:

```bash
# create the virtual environment
python -m venv .venv

# activate it
# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
# runtime dependencies
pip install -r requirements.txt

# or install the project (editable) with dev/test extras
pip install -e ".[dev]"
```

```bash
# Development dependencies
pre-commit install  # Uses pre-commit hook for code management
```

## Run the server

```bash
uvicorn apex_dashboard_analytics.main:app --reload
```

Then open:

- Swagger UI: http://localhost:8000/docs (Only available for Development environment)
- Health: http://localhost:8000/health

## Configuration

Configuration is loaded from environment variables a
`.env` file. See `.env.example`.

## Employee Dashboard endpoint

`GET /api/v1/employees/{employee_id}/dashboard`

Returns one aggregated payload for the Employee View. It has two modes,
selected by a query flag:

| `use_actual_data` | Source | Behaviour |
| ----------------- | ------ | --------- |
| `false` (default) | `data/employees.json` (via `data/mock_json.py`) | Returns the mock payload for `employee_id`; `404` if unknown. |
| `true` | Live team integrations | Concurrently fans out to the 4 team services and assembles the same shape. |

### Live request flow (`use_actual_data=true`)

```
Request ─▶ RequestLoggingMiddleware (binds request_id, timing)
        ─▶ employee_routes.get_employee_dashboard()
        ─▶ EmployeeDashboardService.build()
             └─ gather_sections()  ── asyncio.gather + anyio.to_thread ──┐
                 ├ SkillProfiler.get_skill_profile / get_user_profile    │  (sync httpx
                 ├ Assessment.get_employee_assessments / ..._attempts    │   calls run
                 ├ AITutor.get_user_summary / get_user_skills            │   in worker
                 └ LearningAssistant.get_employee_roadmaps               │   threads,
                                                                         │   concurrently)
             ◀── SectionResult{status, data, duration_ms} per call ◀─────┘
             └─ dashboard_parsers: parse_* (normalize) → assemble_employee_dashboard()
        ─▶ CustomJSONResponse (wraps in {data, meta})
```

### How it works

- **Concurrency (latency):** the ~7 independent upstream calls are sync
  (`httpx.Client`), so they're fanned out across the AnyIO worker-thread pool
  with `asyncio.gather`. Total latency ≈ the slowest call, not the sum. Each
  integration instance reuses one pooled HTTP client across its calls.
- **Timeouts:** every call has a per-call timeout (`integration_timeout_seconds`)
  and the whole fan-out has an overall budget (`dashboard_total_timeout_seconds`).
- **Partial results / resilience:** a failing or slow upstream never breaks the
  dashboard. `gather_sections` isolates each call as `ok` / `error` / `timeout`;
  the assembler tolerates missing sections and defaults them.
- **Parsing (no fabrication):** `dashboard_parsers.parse_*` map each raw upstream
  response into normalized sections; `assemble_employee_dashboard()` builds the
  final `employees.json` shape purely from response data. Fields with no
  upstream attribute are `null` (scalars) or `[]` (lists).
- **Per-call auditing:** every outbound HTTP call goes through
  `BaseIntegration.make_request`, which times it, emits a structured log, and
  persists a row to `integration_logs` (logging failures never break the call).
- **Correlation:** the request middleware binds a `request_id` that appears on
  every app log line and on each `integration_logs` row for that request.

### Response shape

Matches one employee entry in `data/employees.json`:
`employee`, `summary`, `charts` (`skillTrend`, `skillDistribution`),
`course_recommendations`, `analytics`, `roadmap` — wrapped by
`CustomJSONResponse` as `{ "data": { ... }, "meta": { ... } }`.

### Examples

```bash
# default -> mock data
curl "http://localhost:8000/api/v1/employees/usr_9823471/dashboard"

# live aggregation from the team integrations
curl "http://localhost:8000/api/v1/employees/usr_9823471/dashboard?use_actual_data=true"
```

## Database migrations (Alembic)

The schema is managed by Alembic. Config lives in `alembic.ini` (scripts in
`migrations/`), and `migrations/env.py` resolves the DB URL from app settings
(`Settings.sqlalchemy_dsn`) and points autogenerate at `Base.metadata` — so
migrations and the app share the same `.env`.

### Prerequisites

- Alembic ships in the `dev` extra: `pip install -e ".[dev]"`.
- Run all commands from the project root (where `alembic.ini` lives).
- Any command that touches the DB (`upgrade`, `downgrade`, `current`,
  `--autogenerate`) needs a **reachable PostgreSQL**. Configure it in `.env`
  (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, or a full
  `DATABASE_URL`). To spin one up locally:

  ```bash
  docker run --rm -d --name apex-pg -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=apex_analytics -p 5432:5432 postgres:16
  ```

### Apply / inspect migrations

```bash
# apply all pending migrations (creates integration_logs on a fresh DB)
alembic upgrade head

# where is the DB now, and full history
alembic current
alembic history

# roll back the last migration (or to a specific revision)
alembic downgrade -1
alembic downgrade 0001

# preview SQL without touching a DB (useful for review / manual apply)
alembic upgrade head --sql
```

### Create a new migration

1. Edit/add an ORM model under `apex_dashboard_analytics/models/`. If it's a new
   model file, import it in `models/__init__.py` so `env.py` sees it.
2. Autogenerate (needs a live DB already at head):

   ```bash
   alembic revision --autogenerate -m "describe change"
   ```

3. **Review** the file in `migrations/versions/` — autogenerate can miss enum
   changes, server defaults, and index renames. Edit as needed.
4. Apply it: `alembic upgrade head`, then commit the migration file.

To hand-write a migration (no DB needed to author), use
`alembic revision -m "..."` without `--autogenerate` and fill in
`upgrade()`/`downgrade()` yourself.

### Dev vs production

- **Dev shortcut:** set `DB_AUTO_CREATE_TABLES=true` to auto-create tables at
  startup (see the `main.py` lifespan) — convenient, but it does not track
  versions.
- **Production:** keep `DB_AUTO_CREATE_TABLES=false`. The app never runs DDL when
  `ENVIRONMENT=production`; run `alembic upgrade head` as a separate deploy step
  (init-container / job), not inside the web process.

### Quick sanity check (no DB required)

```bash
alembic heads               # -> 0001 (head)
alembic upgrade head --sql  # prints CREATE TABLE / CREATE INDEX SQL
```

### Project CLI (wraps Alembic)

The console script exposes the same migration commands, so you don't need the
`alembic` binary on PATH (handy in Docker / deploy jobs):

```bash
apex-dashboard-analytics db upgrade            # upgrade to head
apex-dashboard-analytics db downgrade -1
apex-dashboard-analytics db revision -m "msg" --autogenerate
apex-dashboard-analytics db current
apex-dashboard-analytics db history
apex-dashboard-analytics db heads
apex-dashboard-analytics db upgrade head --sql # offline SQL
```

Running `apex-dashboard-analytics` with no arguments (or `serve`) starts the
uvicorn server.

## Testing
### (under progress)
```bash
pytest
```


## Configuring PythonPath (For testing on local)
Linux/Mac Environment
```bash
export PYTHONPATH="/path/to/project:$PYTHONPATH"
```

Windows Environment

Powershell
```powershell
$env:PYTHONPATH="C:\path\to\project;$env:PYTHONPATH"
```
CMD

```cmd
set PYTHONPATH=C:\path\to\project;%PYTHONPATH%
```
