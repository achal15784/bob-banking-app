"""
test_transactions.py — Unit + integration tests for deposit and withdrawal.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "BACKEND"))


# ---------------------------------------------------------------------------
# Fixtures (identical pattern to test_auth.py)
# ---------------------------------------------------------------------------

@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test_banking.db")
    import db as db_module
    monkeypatch.setattr(db_module, "_DB_PATH", db_file)
    db_module.init_db()
    db_module.seed_db()

    import app as app_module
    app_module.app.config["TESTING"] = True
    return app_module.app


@pytest.fixture()
def client(app):
    return app.test_client()


def _login(client, username="alice", password="password123"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def _get_balance(db_module, username="alice"):
    row = db_module.get_customer_by_username(username)
    return row["balance"]


# ---------------------------------------------------------------------------
# Deposit tests
# ---------------------------------------------------------------------------

class TestDeposit:
    def test_valid_deposit_redirects_to_dashboard(self, client):
        _login(client)
        resp = client.post("/deposit", data={"amount": "100"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_valid_deposit_increases_balance(self, app, client):
        import db as db_module
        _login(client)
        before = _get_balance(db_module)
        client.post("/deposit", data={"amount": "200.00"})
        after = _get_balance(db_module)
        assert round(after - before, 2) == 200.00

    def test_deposit_zero_shows_error(self, client):
        _login(client)
        resp = client.post("/deposit", data={"amount": "0"})
        assert resp.status_code == 200
        assert b"greater than zero" in resp.data

    def test_deposit_negative_shows_error(self, client):
        _login(client)
        resp = client.post("/deposit", data={"amount": "-50"})
        assert resp.status_code == 200
        assert b"greater than zero" in resp.data

    def test_deposit_blank_shows_error(self, client):
        _login(client)
        resp = client.post("/deposit", data={"amount": ""})
        assert resp.status_code == 200
        assert b"required" in resp.data

    def test_deposit_non_numeric_shows_error(self, client):
        _login(client)
        resp = client.post("/deposit", data={"amount": "abc"})
        assert resp.status_code == 200
        assert b"number" in resp.data

    def test_unauthenticated_deposit_redirects_to_login(self, client):
        resp = client.post("/deposit", data={"amount": "50"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# Withdrawal tests
# ---------------------------------------------------------------------------

class TestWithdraw:
    def test_valid_withdrawal_redirects_to_dashboard(self, client):
        _login(client)
        resp = client.post("/withdraw", data={"amount": "100"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_valid_withdrawal_decreases_balance(self, app, client):
        import db as db_module
        _login(client)
        before = _get_balance(db_module)
        client.post("/withdraw", data={"amount": "150.00"})
        after = _get_balance(db_module)
        assert round(before - after, 2) == 150.00

    def test_insufficient_funds_shows_error_and_balance_unchanged(self, app, client):
        import db as db_module
        _login(client)
        before = _get_balance(db_module)
        resp = client.post("/withdraw", data={"amount": "9999.00"})
        after = _get_balance(db_module)
        assert resp.status_code == 200
        assert b"Insufficient funds" in resp.data
        assert before == after

    def test_withdraw_zero_shows_error(self, client):
        _login(client)
        resp = client.post("/withdraw", data={"amount": "0"})
        assert b"greater than zero" in resp.data

    def test_withdraw_negative_shows_error(self, client):
        _login(client)
        resp = client.post("/withdraw", data={"amount": "-10"})
        assert b"greater than zero" in resp.data

    def test_unauthenticated_withdraw_redirects_to_login(self, client):
        resp = client.post("/withdraw", data={"amount": "50"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# Integration: full deposit and withdrawal flow
# ---------------------------------------------------------------------------

class TestTransactionFlow:
    def test_deposit_then_withdraw_balance_correct(self, app, client):
        import db as db_module
        _login(client)
        initial = _get_balance(db_module)

        client.post("/deposit", data={"amount": "500.00"})
        client.post("/withdraw", data={"amount": "200.00"})

        final = _get_balance(db_module)
        assert round(final - initial, 2) == 300.00

    def test_dashboard_shows_updated_balance_after_deposit(self, client):
        _login(client)
        client.post("/deposit", data={"amount": "99.99"})
        resp = client.get("/dashboard")
        assert b"99.99" in resp.data
