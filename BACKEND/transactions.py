"""
transactions.py — Deposit and withdrawal blueprint.
"""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from auth import login_required
from db import get_customer_by_id, insert_transaction, update_balance

transactions_bp = Blueprint("transactions", __name__)


# ---------------------------------------------------------------------------
# Shared validation helper
# ---------------------------------------------------------------------------

def _parse_amount(raw: str):
    """Return (amount_float, error_string).

    error_string is None when the amount is valid.
    """
    if not raw or not raw.strip():
        return None, "Amount is required."
    try:
        amount = float(raw.strip())
    except ValueError:
        return None, "Amount must be a number."
    if amount <= 0:
        return None, "Amount must be greater than zero."
    # Enforce at most two decimal places
    if round(amount, 2) != amount:
        return None, "Amount cannot have more than 2 decimal places."
    return amount, None


# ---------------------------------------------------------------------------
# Deposit
# ---------------------------------------------------------------------------

@transactions_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method == "POST":
        amount, error = _parse_amount(request.form.get("amount", ""))
        if error:
            return render_template("deposit.html", error=error)

        customer = get_customer_by_id(session["customer_id"])
        new_balance = round(customer["balance"] + amount, 2)
        update_balance(customer["id"], new_balance)
        insert_transaction(customer["id"], "deposit", amount)

        flash(f"Successfully deposited £{amount:,.2f}.", "success")
        return redirect(url_for("dashboard"))

    return render_template("deposit.html")


# ---------------------------------------------------------------------------
# Withdrawal
# ---------------------------------------------------------------------------

@transactions_bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    customer = get_customer_by_id(session["customer_id"])

    if request.method == "POST":
        amount, error = _parse_amount(request.form.get("amount", ""))
        if error:
            return render_template("withdraw.html", error=error, balance=customer["balance"])

        if amount > customer["balance"]:
            return render_template(
                "withdraw.html",
                error="Insufficient funds.",
                balance=customer["balance"],
            )

        new_balance = round(customer["balance"] - amount, 2)
        update_balance(customer["id"], new_balance)
        insert_transaction(customer["id"], "withdrawal", amount)

        flash(f"Successfully withdrew £{amount:,.2f}.", "success")
        return redirect(url_for("dashboard"))

    return render_template("withdraw.html", balance=customer["balance"])
