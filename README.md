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
uvicorn apex_dashboard_analytics.main:app --reload --
```

Then open:

- Swagger UI: http://localhost:8000/docs (Only available for Development environment)
- Health: http://localhost:8000/health

## Configuration

Configuration is loaded from environment variables a
`.env` file. See `.env.example`.

<<<<<<< Updated upstream
=======
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

## Deployment (systemd)

A unit file is provided at `deploy/apex-dashboard-analytics.service`. It runs
the app with uvicorn (`--port 8005`, single process) as a dedicated user, and
intentionally has **no** DB/PostgreSQL dependency — run migrations separately.

1. Replace `{user}` throughout the unit file with your deploy user, and adjust
   the paths (defaults assume `/home/{user}/apex-dashboard-analytics` with a
   `.venv` created via `python -m venv .venv && .venv/bin/pip install -e .`).
2. Ensure `.env` exists (plain `KEY=value` lines — systemd does no shell
   expansion) and the `logs/` directory is writable.
3. Run any pending migrations (the service does not do this for you):

   ```bash
   .venv/bin/apex-dashboard-analytics db upgrade head
   ```

4. Install and start the service:

   ```bash
   sudo cp deploy/apex-dashboard-analytics.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now apex-dashboard-analytics
   sudo systemctl status apex-dashboard-analytics
   journalctl -u apex-dashboard-analytics -f      # follow logs (JSON in journal)
   ```

The unit sets `Environment=ENVIRONMENT=production`, so the app never runs DDL at
startup; the schema is owned by Alembic migrations.

>>>>>>> Stashed changes
## Testing
### (under progress)
```bash
pytest
```
