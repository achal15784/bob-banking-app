"""
test_auth.py — Unit + integration tests for authentication.

Uses Flask's test client and an in-memory SQLite database so tests never
touch the real banking.db file.
"""

import sys
import os

import pytest

# Make BACKEND importable from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "BACKEND"))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app(tmp_path, monkeypatch):
    """Create a fresh app instance backed by a temporary SQLite file."""
    # Override the DB path before importing db so it points to a temp file
    db_file = str(tmp_path / "test_banking.db")
    import db as db_module
    monkeypatch.setattr(db_module, "_DB_PATH", db_file)

    # Re-run initialisation against the temp DB
    db_module.init_db()
    db_module.seed_db()

    import app as app_module
    app_module.app.config["TESTING"] = True
    app_module.app.config["WTF_CSRF_ENABLED"] = False
    return app_module.app


@pytest.fixture()
def client(app):
    return app.test_client()


def _login(client, username="alice", password="password123"):
    """Helper: POST login credentials and return the response."""
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------

class TestLogin:
    def test_valid_login_redirects_to_dashboard(self, client):
        resp = _login(client)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_valid_login_sets_session(self, app, client):
        with app.test_request_context():
            with client.session_transaction() as pre_sess:
                assert "customer_id" not in pre_sess

        _login(client)

        with client.session_transaction() as sess:
            assert "customer_id" in sess

    def test_wrong_password_shows_login_page_with_error(self, client):
        resp = _login(client, password="wrongpassword")
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data

    def test_unknown_username_shows_same_generic_error(self, client):
        resp = _login(client, username="ghost", password="whatever")
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data

    def test_blank_username_shows_specific_error(self, client):
        resp = client.post("/login", data={"username": "", "password": "pw"})
        assert b"Username is required" in resp.data

    def test_blank_password_shows_specific_error(self, client):
        resp = client.post("/login", data={"username": "alice", "password": ""})
        assert b"Password is required" in resp.data


# ---------------------------------------------------------------------------
# Logout tests
# ---------------------------------------------------------------------------

class TestLogout:
    def test_logout_clears_session_and_redirects(self, client):
        _login(client)

        with client.session_transaction() as sess:
            assert "customer_id" in sess

        resp = client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

        with client.session_transaction() as sess:
            assert "customer_id" not in sess

    def test_dashboard_inaccessible_after_logout(self, client):
        _login(client)
        client.get("/logout")
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# Integration: full login → dashboard flow
# ---------------------------------------------------------------------------

class TestLoginDashboardFlow:
    def test_login_then_dashboard_shows_customer_name(self, client):
        _login(client)
        resp = client.get("/dashboard", follow_redirects=True)
        assert resp.status_code == 200
        assert b"Alice" in resp.data
