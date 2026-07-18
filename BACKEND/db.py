"""
db.py — Database access layer.

All SQL lives here. No other module should contain raw SQL statements.
"""

import os
import sqlite3

from werkzeug.security import generate_password_hash

# Absolute path to banking.db so the app works regardless of launch directory
_DB_PATH = os.path.join(os.path.dirname(__file__), "banking.db")


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def get_connection():
    """Open and return a connection to banking.db.

    Rows are returned as sqlite3.Row objects so columns can be accessed by name.
    """
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

def init_db():
    """Create the customers and transactions tables if they do not exist."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    NOT NULL UNIQUE,
                password TEXT    NOT NULL,
                name     TEXT    NOT NULL,
                balance  REAL    NOT NULL DEFAULT 0.0 CHECK (balance >= 0)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                type        TEXT    NOT NULL CHECK (type IN ('deposit', 'withdrawal')),
                amount      REAL    NOT NULL,
                timestamp   TEXT    NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        """)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

def seed_db():
    """Insert test customer accounts if the customers table is empty."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM customers").fetchone()
        if row["cnt"] == 0:
            test_accounts = [
                ("alice", generate_password_hash("password123"), "Alice Johnson", 1000.00),
                ("bob",   generate_password_hash("password123"), "Bob Smith",     500.00),
            ]
            conn.executemany(
                "INSERT INTO customers (username, password, name, balance) VALUES (?, ?, ?, ?)",
                test_accounts,
            )
            conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_customer_by_username(username: str):
    """Return the customer row matching *username*, or None."""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM customers WHERE username = ?", (username,)
        ).fetchone()
    finally:
        conn.close()


def get_customer_by_id(customer_id: int):
    """Return the customer row matching *customer_id*, or None."""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
    finally:
        conn.close()


def update_balance(customer_id: int, new_balance: float):
    """Overwrite the balance for *customer_id* with *new_balance*."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE customers SET balance = ? WHERE id = ?",
            (new_balance, customer_id),
        )
        conn.commit()
    finally:
        conn.close()


def insert_transaction(customer_id: int, transaction_type: str, amount: float):
    """Record a deposit or withdrawal transaction row."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO transactions (customer_id, type, amount) VALUES (?, ?, ?)",
            (customer_id, transaction_type, amount),
        )
        conn.commit()
    finally:
        conn.close()


def get_transactions(customer_id: int):
    """Return all transactions for *customer_id*, newest first."""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM transactions WHERE customer_id = ? ORDER BY id DESC",
            (customer_id,),
        ).fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Auto-initialise when this module is imported
# ---------------------------------------------------------------------------

init_db()
seed_db()
