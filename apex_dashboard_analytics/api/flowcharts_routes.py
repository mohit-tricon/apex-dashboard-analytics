"""Flowcharts endpoint.

Serves the Mermaid flowchart diagrams as markdown content
or renders them in-browser using the Mermaid.js library.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter

_FLOWCHART_DIR = Path(__file__).resolve().parents[2] / "flowcharts"

flowcharts_router = APIRouter(prefix="/flowcharts", tags=["flowcharts"])


def _list_flowcharts() -> list[dict[str, str]]:
    if not _FLOWCHART_DIR.is_dir():
        return []
    charts = []
    for f in sorted(_FLOWCHART_DIR.iterdir()):
        if f.suffix == ".md":
            name = f.stem
            charts.append({"name": name, "title": name.replace("-", " ").title()})
    return charts


# @flowcharts_router.get("")
# @flowcharts_router.get("/")
# async def list_flowcharts():
#     """List available flowcharts."""
#     charts = _list_flowcharts()
#     return {
#         "flowcharts": charts,
#         "endpoints": {
#             "html": "/api/v1/flowcharts/view",
#             "raw": "/api/v1/flowcharts/{name}/raw",
#         },
#     }


# @flowcharts_router.get("/{name}/raw", response_class=PlainTextResponse)
# async def get_flowchart_raw(name: str):
#     """Return the raw Mermaid markdown for a flowchart."""
#     charts = _list_flowcharts()
#     if not any(c["name"] == name for c in charts):
#         raise HTTPException(status_code=404, detail=f"Flowchart '{name}' not found")
#     content = (_FLOWCHART_DIR / f"{name}.md").read_text(encoding="utf-8")
#     return content


@flowcharts_router.get("/view", response_class=HTMLResponse)
async def view_all_flowcharts():
    """Render all flowcharts in-browser using Mermaid.js."""
    charts = _list_flowcharts()
    cards = []
    for c in charts:
        content = (_FLOWCHART_DIR / f"{c['name']}.md").read_text(encoding="utf-8")
        # Extract just the mermaid block (remove ```mermaid and ``` fences)
        mermaid_code = content.strip()
        if mermaid_code.startswith("```mermaid"):
            mermaid_code = mermaid_code[len("```mermaid") :]
        if mermaid_code.endswith("```"):
            mermaid_code = mermaid_code[:-3]
        mermaid_code = mermaid_code.strip()

        cards.append(f"""
        <div class="card">
          <h2>{c["title"]}</h2>
          <div class="mermaid">{mermaid_code}</div>
        </div>""")

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard Flowcharts</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{startOnLoad:true, theme:'base', themeVariables:{{background:'#fff'}}}})</script>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 2em auto; padding: 0 1em; background: #f8fafc; color: #1e293b; }}
    h1 {{ color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.3em; }}
    .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5em; margin: 1.5em 0; overflow-x: auto; }}
    h2 {{ margin-top: 0; color: #334155; font-size: 1.2em; }}
    .mermaid {{ display: flex; justify-content: center; }}
  </style>
</head>
<body>
  <h1>Dashboard Flowcharts</h1>
  {"".join(cards)}
</body>
</html>""")
