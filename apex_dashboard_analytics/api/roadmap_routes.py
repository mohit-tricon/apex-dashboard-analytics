"""Mirrors Team 2 contract: GET /api/v1/{skill_id}/roadmap.

This is registered at the top level (no prefix) because that's the
literal path in the Overview table of Team 2's doc. It's an unusual
shape for a REST path — a bare {skill_id} segment at the API root
invites collisions as more endpoints get added. Worth pushing Team 2
to move this under something like /skills/{skill_id}/roadmap or
/roadmaps/{skill_id} instead; implemented as-is for now so the
frontend can build against the documented contract.
"""

from __future__ import annotations

from fastapi import HTTPException
from fastapi.routing import APIRouter

from apex_dashboard_analytics.data import mock_data
from apex_dashboard_analytics.schemas.learning import Roadmap

roadmap_router = APIRouter(tags=["roadmap"])


@roadmap_router.get("/{skill_id}/roadmap", response_model=Roadmap)
def get_roadmap(skill_id: str) -> Roadmap:
    roadmap = mock_data.get_roadmap_by_skill_id(skill_id)
    if roadmap is None:
        raise HTTPException(status_code=404, detail=f"No roadmap found for skill_id '{skill_id}'")
    return roadmap