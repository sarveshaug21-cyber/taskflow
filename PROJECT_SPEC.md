# Project: TaskFlow — Personal Task Manager

## Stack
- Backend: Python Flask + SQLite
- Frontend: HTML/CSS/vanilla JS (no framework)
- Auth: simple session-based login

## Structure
- app.py — Flask app and routes
- models.py — SQLite schema and queries
- templates/ — HTML pages
- static/style.css, static/script.js
- tests/ — pytest tests

## Conventions
- Keep functions small and commented
- Validate all user input server-side
- Return proper HTTP status codes from the API
- Do not break previously working routes when adding new ones
