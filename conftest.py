import os
import sqlite3
import pytest

@pytest.fixture(scope="session", autouse=True)
def reset_database():
    if os.path.exists("database.db"):
        os.remove("database.db")

    from models import init_db
    init_db()

    # Ensure priority column exists, since models.init_db() doesn't know about it
    conn = sqlite3.connect("database.db")
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # already exists
    conn.close()

    yield
