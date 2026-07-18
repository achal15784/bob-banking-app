"""
app.py — Flask application entry point.

Creates the app object, wires up blueprints, and defines the dashboard route.
"""

import os
import sys

from flask import Flask, redirect, render_template, session, url_for

# Ensure BACKEND/ is on the import path so auth and db can import each other
sys.path.insert(0, os.path.dirname(__file__))

from auth import auth_bp, login_required
from db import get_customer_by_id, get_transactions
from transactions import transactions_bp

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "FRONTEND")

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, "templates"),
    static_folder=os.path.join(FRONTEND_DIR, "static"),
)

# Secret key — hard-coded for development only.
# In production, read from an environment variable.
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production-abc123")

# ---------------------------------------------------------------------------
# Register blueprints
# ---------------------------------------------------------------------------

app.register_blueprint(auth_bp)
app.register_blueprint(transactions_bp)


# ---------------------------------------------------------------------------
# Core routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Redirect root URL to login."""
    return redirect(url_for("auth.login"))


@app.route("/dashboard")
@login_required
def dashboard():
    """Show account summary for the authenticated customer."""
    customer = get_customer_by_id(session["customer_id"])
    if customer is None:
        # Edge case: session references a customer that no longer exists
        session.clear()
        return redirect(url_for("auth.login"))

    transactions = get_transactions(customer["id"])
    return render_template(
        "dashboard.html",
        name=customer["name"],
        balance=customer["balance"],
        transactions=transactions,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
