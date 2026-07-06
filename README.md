# apex-dashboard-analytics

A FastAPI analytics service scaffolded with **uv**, using **structlog**,
**pydantic** (+ pydantic-settings), **uvicorn**, and **pytest**.

## Requirements

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

## Run the server

```bash
# via the console script
uv run apex-dashboard-analytics

# or directly with uvicorn (reload for development)
uv run uvicorn apex_dashboard_analytics.main:app --reload
```

Then open:

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

## API

| Method | Path                 | Description                    |
| ------ | -------------------- | ------------------------------ |
| GET    | `/health`            | Service health & metadata      |
| POST   | `/analytics/events`  | Record an analytics event      |
| GET    | `/analytics/events`  | List recorded events           |
| GET    | `/analytics/metrics` | Aggregated metrics summary     |

## Configuration

Configuration is loaded from environment variables (prefix `APEX_`) or a
`.env` file. See `.env.example`.

## Testing

```bash
uv run pytest
```

## Project layout

```
src/apex_dashboard_analytics/
├── __init__.py        # console entrypoint (runs uvicorn)
├── main.py            # FastAPI app factory + ASGI `app`
├── config.py          # pydantic-settings Settings
├── logging.py         # structlog configuration
├── api/               # routers (health, analytics)
└── schemas/           # pydantic request/response models
tests/                 # pytest suite
```
