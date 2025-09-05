# AGENTS Instructions for python-service

- Use FastAPI with async endpoints.
- Keep business logic in `app/services`, schemas in `app/schemas`, and ORM models in `app/models`.
- Validate configuration through `app/core/config.py`.
- Run `python -m py_compile $(git ls-files '*.py')` before committing changes.
