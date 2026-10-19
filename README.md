# TaskFlow

Personal task manager — Flask backend, SQLite database, vanilla HTML/CSS/JS frontend, with an optional pywebview desktop wrapper.

Repository: https://github.com/sarveshaug21-cyber/taskflow

> **Status:** Functional task manager with authentication, projects, tasks, subtasks, priority, recurrence, search/filter/sort, and overdue grouping.

## Stack

- Backend: Python 3, Flask 3, SQLite
- Frontend: HTML/CSS, vanilla JavaScript (no framework)
- Auth: session-based login, password hashing (werkzeug)
- Desktop (optional): pywebview (`desktop_app.py`, `TaskFlow.spec`)
- Tests: pytest

## Features

- User signup / login / logout (session-based)
- Create, read, update, delete tasks via REST API (`/api/tasks`)
- Projects: create, list, delete; assign tasks to a project or Inbox
- Subtasks per task (add, toggle, delete)
- Task fields: title, description, status, due date, priority (low/medium/high), recurrence (none/daily/weekly/monthly)
- Recurring tasks: completing a recurring task automatically creates the next occurrence
- Frontend: search, filter (all/active/completed), sort (due date/priority/newest), overdue / today / upcoming / no-date grouping, inline task editing, empty states
- Keyboard shortcuts: `c` = focus "Add a task" title; `t` = set due date to today (ignored while typing in a field)
- Optional desktop app via pywebview with due-date notifications

## Project structure

```
app.py              Flask app + REST API routes
models.py           SQLite schema (init_db)
templates/          Jinja2 HTML pages (login, signup, dashboard)
static/             CSS and vanilla JS served by Flask
desktop_app.py      pywebview desktop wrapper (untracked build output)
TaskFlow.spec       pyinstaller spec for the desktop bundle
tests/              pytest tests (test_auth.py, test_tasks.py)
conftest.py         pytest fixtures (temporary test database)
.github/workflows/ci.yml  CI: pytest + pyflakes + py_compile
```

## Setup

### Local development

1. Clone the repository and create a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install flask pytest pyflakes
   ```

3. Set a secret key for session signing (required in production; a dev-only
   fallback is used automatically in debug/testing mode):

   ```bash
   export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
   ```

   Add this to your shell profile or a `.env` file (`.env` is gitignored).

4. Run the app:

   ```bash
   python3 app.py
   ```

   The SQLite database (`database.db`) is created automatically on first run.

### Production requirements

- Set the `SECRET_KEY` environment variable to a strong, random value. The app
  refuses to start in non-debug mode without it.
- Do not run with `debug=True` in production.
- `database.db` contains user data and is gitignored — back it up separately.

## Tests

```bash
pytest -v
```

The test suite runs against a dedicated temporary SQLite database; the real
`database.db` is never touched by tests.

### Static checks

```bash
python3 -m py_compile app.py models.py desktop_app.py conftest.py test_*.py
python3 -m pyflakes app.py models.py desktop_app.py conftest.py test_*.py
```

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on push/PR to `master`:
Python setup, dependency install, `py_compile`, `pyflakes`, and `pytest`. No
secrets are used or exposed.

## Open decisions (confirmation needed before publishing)

1. **Licence ownership/copyright.** The `LICENSE` file uses `Copyright (c) 2026 sarveshaug21-cyber` under the MIT licence. Confirm you own the code and are comfortable with this copyright holder and year before publishing.

2. **Tracked sensitive files.** `database.db`, `agent_log.txt`, `diagnostic_report.txt`, `test_auth.py.bak` and `__pycache__/*.pyc` remain tracked in the original repository's history. They are gitignored going forward but must be removed from the index (and ideally purged from history) before publishing. See Stage B/C commands below.

## Known limitations

- No email verification, password reset, or OAuth.
- `database.db` is a single-user local SQLite file; no multi-user server mode.
- Desktop wrapper (`desktop_app.py`) is present but its build artifacts
  (`build/`, `dist/`) are untracked and gitignored.
