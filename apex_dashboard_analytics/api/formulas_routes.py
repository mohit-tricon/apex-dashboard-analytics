"""Formulas documentation endpoint.

Serves the formulas used across all dashboard parsers and assemblers
as both JSON (structured data) and HTML (readable documentation).
"""

from __future__ import annotations

from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter

from apex_dashboard_analytics.formulas import get_formulas_html

formulas_router = APIRouter(prefix="/formulas", tags=["formulas"])


# @formulas_router.get("")
# @formulas_router.get("/")
# async def get_formulas_root():
#     """Redirect to /formulas/json or /formulas/html."""
#     return {"json": "/formulas/json", "html": "/formulas/html"}


# @formulas_router.get("/json")
# async def get_formulas_json():
#     """Return all formulas as structured JSON."""
#     return FORMULAS


@formulas_router.get("/html", response_class=HTMLResponse)
async def get_formulas_html_endpoint():
    """Return all formulas as a readable HTML page."""
    html = get_formulas_html()
    return HTMLResponse(
        f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard Formulas</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 960px; margin: 2em auto; padding: 0 1em; color: #1e293b; background: #f8fafc; }}
    h1 {{ color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.3em; }}
    details {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1em; }}
    summary {{ cursor: pointer; font-weight: 600; color: #1e293b; }}
    table {{ margin: 0.5em 0; font-size: 0.9em; }}
    th {{ background: #f1f5f9; text-align: left; }}
    td, th {{ padding: 6px 10px; border: 1px solid #e2e8f0; }}
    code {{ background: #f1f5f9; padding: 0.15em 0.4em; border-radius: 3px; font-size: 0.9em; }}
    p {{ margin: 0.5em 0; }}
  </style>
</head>
<body>
{html}
</body>
</html>"""
    )
