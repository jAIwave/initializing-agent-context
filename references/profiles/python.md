# Profile: Python

## Detect

- `pyproject.toml`, `requirements*.txt`, `setup.py`, `setup.cfg`, `Pipfile`
- `poetry.lock`, `uv.lock`, `Pipfile.lock`
- `.python-version`, `.tool-versions`, `runtime.txt`
- Entry: `__main__.py`, `app.py`, `manage.py`, `wsgi.py`, `asgi.py`,
  `[project.scripts]`, `[tool.poetry.scripts]`
- Tests: `pytest.ini`, `tox.ini`, `conftest.py`, `[tool.pytest.ini_options]`,
  `tests/`, `test_*.py`, `*_test.py`
- Lint/type: `ruff.toml`, `.ruff.toml`, `[tool.ruff]`, `mypy.ini`, `.mypy.ini`,
  `[tool.mypy]`, `pyrightconfig.json`

## Package manager

- `uv.lock` -> `uv sync`, `uv run ...`
- `poetry.lock` -> `poetry install`, `poetry run ...`
- `Pipfile.lock` -> `pipenv install`, `pipenv run ...`
- `requirements.txt` -> `pip install -r requirements.txt`
- No lockfile: note it as a finding.

## Commands to verify

```bash
python -m pytest --collect-only -q
python -m pytest tests/test_one.py -q
python -m pytest -q
ruff check .
ruff format --check .
mypy .
python -m build
```

Django: `python manage.py check`, `python manage.py test`.
FastAPI: `uvicorn <module>:app --reload` (server; do not run in discovery).

## Common invariants

- Parse/validate at the boundary; internal code receives typed values.
- Money is integer minor units; no floats.
- One DB connection per request/transaction; no module-global connections.
- Migrations are additive; applied files are immutable.
- Tests run with the documented test mode, not production config.
- Secrets come from the environment; never log payloads with PII.
- Async code does not call blocking I/O on the event loop.

## Hazards

- Multiple virtualenvs; document which one owns which unit.
- `.env` and test databases; never read or commit them.
- Long-running workers (Celery/RQ) have different start commands.
- Generated clients and migrations are not hand-edited.
- `print()` in production paths; prefer the project logger.

## Docs to generate

- `docs/testing.md`: pytest markers, fixtures, test DB setup.
- `docs/architecture.md`: services, DB ownership, async boundaries.
- `docs/operations.md`: process manager, workers, migrations.
