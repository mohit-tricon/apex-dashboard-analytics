"""In-memory sample data used until the upstream team services (skill
profiler, learning recommendation, AI tutor, assessment) are live.

Nothing here talks to a database -- it exists purely so the frontend
dashboard can be built against realistic, stable payloads. Swap the
functions in `mock_data.py` for real HTTP calls to
`settings.skill_profiler_base_url` etc. once those services exist.
"""