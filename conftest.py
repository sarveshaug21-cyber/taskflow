import os
import sqlite3
import tempfile
import pytest

from models import init_db


@pytest.fixture(scope="session", autouse=True)
def temp_database():
    """Run the test session against a dedicated temporary SQLite database.

    The real `database.db` is never deleted, overwritten, or written to by the
    test suite. A temp file is created, initialised with the application
    schema, and removed when the session ends (even if tests fail).
    """
    fd, tmp_path = tempfile.mkstemp(prefix='taskform-test-', suffix='.db')
    os.close(fd)

    try:
        # Initialise the schema in the temporary database only.
        init_db(tmp_path)

        # Ensure the priority column exists (defensive, matches init_db default).
        conn = sqlite3.connect(tmp_path)
        try:
            conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # already exists
        conn.close()

        # Point the Flask app and get_db_connection() at the temp database.
        import app as app_module
        app_module.app.config['DATABASE'] = tmp_path
        app_module.app.config['TESTING'] = True

        yield tmp_path
    finally:
        # Always remove the temporary database, even on test failure.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@pytest.fixture(autouse=True)
def client(temp_database):
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
