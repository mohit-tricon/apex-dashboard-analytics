Problem statement is

AI Learning Assistant for Employees 
Business Problem 
Most organizations struggle with: 

* Employees not knowing what to learn next  

* Learning paths not aligned with career goals  

* Low completion rates of training programs  

* Managers having limited visibility into skill gaps  

* Difficulty measuring ROI of learning initiatives  


This is divided among 5 teams

Team 1 – Employee Skill Profiler Agent 
Team 2 – Learning Recommendation Agent 
Team 3 – AI Tutor Agent 
Team 4 – Assessment & Quiz Agent 
Team 5 – Learning Analytics Dashboard

---------------------------------------------------- Response --------------------------------------------------------------------
┌─────────────────────────────────────────────────────────────────────┐
│                    AI Learning Assistant Platform                    │
├─────────────┬──────────────┬─────────────┬─────────────┬────────────┤
│   Team 1    │   Team 2     │   Team 3    │   Team 4    │  Team 5    │
│  Skill      │  Learning    │  AI Tutor   │ Assessment  │ Analytics  │
│  Profiler   │  Recommender │  Agent      │ & Quiz      │ Dashboard  │
│  Agent      │  Agent       │             │  Agent      │            │
└──────┬──────┴──────┬───────┴──────┬──────┴──────┬──────┴─────┬──────┘
       │             │              │             │            │
       └─────────────┴──────────────┴─────────────┴────────────┘
                                    │
                          Shared Data / Events
                     (Skill Scores, Quiz Results,
                      Course Progress, Profiles)



The PR Reviewer / claude.md angle
Still valid as a DX tool for your own team. But given you're now the integration hub, consider extending it to validate inter-team API contracts — does Team 2's recommendation payload match what your dashboard expects? A schema validation agent in your CI pipeline is genuinely useful here.

This is your RBAC-gated dashboard. Three views, one backend, proper auth. Don't underestimate this — role-based data scoping done properly is solid engineering.

Employee View          Manager View            Executive View
─────────────          ────────────            ──────────────
Current Skill Score    Team Skill Distribution  AI Readiness Score
Learning Progress      Skill Gaps              Dept-wise Skills
Recommended Courses    Training Completion     Training ROI
Quiz Scores            Certification Status



--------------------------------------------------- Prompt ---------------------------------------------------------------------
I have prepared API contracts, go through with them and give suggestions/modifications 


##########################################################################################
Team 1 – Employee Skill Profiler Agent 
GET: /api/v1/employees/{id}/current-skills
{
  "user_id": "usr_9823471",
  "last_updated_at": "2026-06-29T07:25:00Z",
  "current_role": "Python Dev",
  "expected_role": "Fast API Dev",
  "skills": [
    {
      "skill_id": "sk_python",
      "name": "Python",
      "type": "hard_technical",
      "confidence_score": 0.95,
      "recency_year": 2026,
      "sources": [
        { "type": "resume", "weight": 0.7 },
        { "type": "linkedin_profile", "weight": 0.8 },
        { "type": "self_assessment", "weight": 0.5 }
      ]
    },
    {
      "skill_id": "sk_aws_solutions_architect",
      "name": "AWS Cloud Architecture",
      "type": "hard_domain",
      "confidence_score": 0.99,
      "recency_year": 2026,
      "sources": [
        { "type": "certifications", "id": "cert_001", "weight": 1.0 },
        { "type": "project_history", "weight": 0.9 }
      ]
    },
    {
      "skill_id": "sk_project_management",
      "name": "Project Management",
      "type": "soft_execution",
      "confidence_score": 0.65,
      "recency_year": 2025,
      "sources": [
        { "type": "project_history", "weight": 0.7 }
      ]
    }
  ],
  "metadata": {
    "total_skills_found": 3,
    "primary_domain": "Backend & Cloud Engineering"
  }
}





##########################################################################################
Team 2 – Learning Recommendation Agent 
GET: /api/v1/employees/{id}/recommendations
[
    { "courseId": "string", "title": "string", "priority": 1,
      "estimatedHours": 10, "tags": ["ML", "Python"] }
]
GET: /api/v1/plans/{id}
[
    { "month": 1, "courseId": "string", "milestone": "string" }
]
##########################################################################################
Team 3 – Tutor Agent
GET: /api/v1/employees/{id}/asks # questions asked by employees, or chat history to get jargons 
GET: /api/v1/tutoring/{id}
{		
  "employeeId": "string",
  "sessionId": "string",
  "topicsCovered": ["RAG", "Embeddings"],
  "durationMinutes": 25,
  "documentsAccessed": ["course_material_3.pdf"],
  "timestamp": "ISO8601"
} 
##########################################################################################
Team 4 – Assessment & quiz Agent
GET: /api/v1/quiz/{id}/attempts
{ score: 82, attemptCount: 2, topic: "MCP Protocol" }

#####################################################################################################################
Generate a FastAPI Named apex-dashboard-analytics using uv, structlog, pydantic, uvicorn and pytest as dependencies.

#####################################################################################################################

Follow best practices to use structlog
Handling Logging at Application and Request Level
Implement a logging middleware in middlewares/logging.py

#####################################################################################################################


For all the logs corresponding to request, they all should have request_id, start time and end time

Handling Integration with multiple teams
  Develop a db connection (postgresql) in config.py and a singleton object for DB
  Make a table integration_logs with following fields:
      url, request_headers, response_headers, payload, response, timestamp, status_code etc. This table would maitain logs for integration irrespective of which team is integrated to.
  Make an abstract integration class which has methods like make_request, save_to_integration_log (this method should not raise exception as it can break the integration part). All of the team-wise integration will inherit from this base class. DO NOT IMPLEMENT the child classes only the Base Class.
  There can be application_logger logs as well.

Implement a basic SkillProfilerIntegration, and how to deal in production if integration_logs not repeatedly created.

Add alembic flow with migrations handling and update into .env.example as well

#####################################################################################################################


write a systemd service file, for deployment we are using systemd with current app handling service uvicorn apex_dashboard_analytics.main:app --port 8005 (no worker as of now). Don't add dependency for DB/Postgresql Service into service file.

#####################################################################################################################
