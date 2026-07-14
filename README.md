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

## Testing
### (under progress)
```bash
pytest
```
