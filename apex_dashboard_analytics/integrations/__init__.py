from .base import BaseIntegration
from .skill_profiler import SkillProfilerIntegration
from .learning_assistant import LearningAssistantIntegration
from apex_dashboard_analytics.integrations.skill_profiler import (
    SkillProfilerIntegration,
)

__all__ = [
    "BaseIntegration",
    "SkillProfilerIntegration",
    "LearningAssistantIntegration",
    "AssessmentIntegration"
]
