"""
auth.py — Authentication blueprint.

Handles login, logout, and the login_required decorator.
"""

import functools

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from db import get_customer_by_username

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# Login-required decorator
# ---------------------------------------------------------------------------

def login_required(view):
    """Redirect unauthenticated users to the login page."""
    @functools.wraps(view)
    def wrapped(**kwargs):
        if not session.get("customer_id"):
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # --- input presence validation ---
        if not username:
            return render_template("login.html", error="Username is required.")
        if not password:
            return render_template("login.html", error="Password is required.")

        # --- credential validation ---
        customer = get_customer_by_username(username)
        if customer is None or not check_password_hash(customer["password"], password):
            return render_template("login.html", error="Invalid username or password.")

        # --- success: create session ---
        session.clear()
        session["customer_id"] = customer["id"]
        return redirect(url_for("dashboard"))

    # GET — show the login form
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
