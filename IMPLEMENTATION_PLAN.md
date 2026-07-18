# Banking Web Application — Implementation Plan

> **Status:** Pending implementation  
> **Stack:** HTML + Bootstrap (Frontend) · Python Flask (Backend) · SQLite (Database)

---

## 1. Solution Overview

### Objective
Build a lightweight, browser-based banking application that allows customers to securely log in, view their account balance, and perform basic transactions (deposit and withdrawal) through a clean web interface.

### Scope
| In Scope | Out of Scope |
|---|---|
| Customer login / logout | Admin console |
| Dashboard (summary view) | Multi-currency support |
| View account balance | Loan or credit features |
| Deposit funds | External payment integrations |
| Withdraw funds | Email / SMS notifications |
| Session management | Mobile native app |

### Users
- **Customer** — the sole user role; accesses the application via a web browser to manage their personal bank account.

### Functional Requirements
1. A customer can log in with a username and password.
2. After login, the customer is presented with a dashboard showing their account summary.
3. The customer can view their current balance.
4. The customer can deposit a positive monetary amount into their account.
5. The customer can withdraw a positive monetary amount, provided sufficient funds exist.
6. The customer can log out, which terminates their session.

### Non-Functional Requirements
- **Security:** Passwords must be stored as hashed values; sessions must be invalidated on logout.
- **Usability:** All pages must be responsive and render correctly on modern desktop browsers using Bootstrap.
- **Reliability:** Invalid or insufficient-fund transactions must be rejected with a clear user message.
- **Maintainability:** Frontend and Backend must reside in clearly separated folders with no cross-folder hard dependencies.
- **Portability:** SQLite is used so no external database server is required.

### Assumptions
- A single account per customer is sufficient for this application.
- Seed / test customer accounts may be pre-populated in the database at setup time.
- The application runs on localhost during development; production deployment is out of scope.
- Python 3.11 and Flask are the approved backend versions (confirmed by CI pipeline in `docs/banking-app-ci.yml`).
- No third-party authentication provider (OAuth, SSO) is required.

---

## 2. High-Level Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                        BROWSER                          │
│                                                         │
│  ┌─────────────┐   ┌──────────┐   ┌─────────────────┐  │
│  │  Login Page │   │Dashboard │   │Transaction Pages│  │
│  │  (HTML+BS)  │   │(HTML+BS) │   │   (HTML+BS)     │  │
│  └──────┬──────┘   └────┬─────┘   └────────┬────────┘  │
│         │               │                  │            │
└─────────┼───────────────┼──────────────────┼────────────┘
          │   HTTP Request (form POST / GET)  │
          ▼               ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│                   BACKEND — Python Flask                │
│                                                         │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │  Auth Module │  │  Dashboard  │  │  Transaction  │  │
│  │  /login      │  │  Module     │  │  Module       │  │
│  │  /logout     │  │  /dashboard │  │  /deposit     │  │
│  └──────┬───────┘  └──────┬──────┘  │  /withdraw    │  │
│         │                 │         └───────┬───────┘  │
│         └─────────────────┴─────────────────┘          │
│                           │                             │
│                    ┌──────▼──────┐                      │
│                    │  DB Layer   │                      │
│                    │  (queries)  │                      │
│                    └──────┬──────┘                      │
└───────────────────────────┼─────────────────────────────┘
                            │  SQL via sqlite3
                            ▼
┌─────────────────────────────────────────────────────────┐
│               DATABASE — SQLite file                    │
│                   banking.db                            │
└─────────────────────────────────────────────────────────┘
```

### Frontend → Backend → Database Interaction
1. The browser renders HTML templates served by Flask (Jinja2).
2. User actions (form submissions) are sent as HTTP POST requests to Flask route handlers.
3. Flask processes the request, calls the database layer, and returns a redirect or a rendered template.
4. SQLite persists all customer and transaction data in a single file on the server.

### Request Lifecycle
```
Browser submits form
        │
        ▼
Flask route handler receives request
        │
        ├── Validate session (Flask session cookie)
        │
        ├── Validate input data
        │
        ├── Execute database query
        │
        └── Render template  ──▶  Browser displays result
              OR redirect
```

---

## 3. Component Design

### Frontend Responsibilities (FRONTEND/)
- Render all visible pages as HTML files styled with Bootstrap.
- Collect user input through HTML forms (login credentials, deposit/withdrawal amounts).
- Display feedback messages (success, error) returned from the backend.
- Enforce no business logic — all validation lives in the backend.
- Maintain no client-side state beyond what the browser session cookie provides.

### Backend Responsibilities (BACKEND/)
- Serve HTML templates to the browser via Flask's Jinja2 templating engine.
- Handle all HTTP routes: login, logout, dashboard, deposit, withdraw.
- Authenticate users and manage session state using Flask's built-in session mechanism.
- Enforce all business rules (e.g., sufficient balance check before withdrawal).
- Interact with SQLite through a dedicated database-access layer (no raw SQL scattered in route handlers).
- Hash and verify passwords using a standard library (e.g., Werkzeug's `generate_password_hash` / `check_password_hash`).

### Database Responsibilities (BACKEND/banking.db)
- Persist customer account data (credentials, balance).
- Persist transaction history for audit purposes.
- Enforce data integrity at the storage level (e.g., non-negative balances via constraints where possible).
- Remain entirely passive — all reads and writes are initiated by the Flask backend.

---

## 4. Folder Structure

```
banking-workshop/
├── FRONTEND/
│   ├── templates/              # Jinja2 HTML templates served by Flask
│   │   ├── login.html          # Login page
│   │   ├── dashboard.html      # Account dashboard
│   │   ├── deposit.html        # Deposit form
│   │   └── withdraw.html       # Withdrawal form
│   └── static/
│       ├── css/                # Custom CSS overrides (Bootstrap loaded via CDN)
│       └── images/             # Any logo or image assets
│
├── BACKEND/
│   ├── app.py                  # Flask application entry point; route definitions
│   ├── auth.py                 # Authentication helpers (login, logout, session guard)
│   ├── transactions.py         # Deposit and withdrawal business logic
│   ├── db.py                   # Database connection and query helpers
│   ├── banking.db              # SQLite database file (auto-created on first run)
│   └── requirements.txt        # Python dependencies (Flask, Werkzeug)
│
├── tests/                      # Pytest test suite (per CI pipeline)
│   ├── test_auth.py
│   └── test_transactions.py
│
├── docs/                       # Existing project documentation and CI templates
│   ├── banking-app-ci.yml
│   └── ...
│
└── IMPLEMENTATION_PLAN.md      # This document
```

### Responsibility of Each Folder
| Folder / File | Responsibility |
|---|---|
| `FRONTEND/templates/` | All user-facing HTML pages (rendered server-side by Flask) |
| `FRONTEND/static/` | Static assets: custom CSS, images |
| `BACKEND/app.py` | Flask app factory, URL routing, request/response cycle |
| `BACKEND/auth.py` | Login validation, session creation, logout, login-required decorator |
| `BACKEND/transactions.py` | Deposit and withdrawal rules and execution |
| `BACKEND/db.py` | SQLite connection management, reusable query helpers |
| `BACKEND/banking.db` | Persistent SQLite data store |
| `BACKEND/requirements.txt` | Reproducible Python dependency list |
| `tests/` | Automated unit and integration tests run by CI |
| `docs/` | Supporting docs, CI/CD config, workshop setup guides |

---

## 5. Module Breakdown

### Authentication Module
- **Purpose:** Control access to the application.
- **Handles:** Login form processing, credential verification (hashed password comparison), session creation on success, session destruction on logout, route protection (redirect unauthenticated users to login).
- **Key Routes:** `GET/POST /login`, `GET /logout`
- **Pages:** `login.html`

### Dashboard Module
- **Purpose:** Provide the customer with an at-a-glance summary after login.
- **Handles:** Fetching account holder name and current balance from the database, rendering the summary view.
- **Key Routes:** `GET /dashboard`
- **Pages:** `dashboard.html`

### Account Management Module
- **Purpose:** Display detailed balance information.
- **Handles:** Querying and presenting the live balance; this may be a sub-section of the dashboard rather than a standalone route.
- **Key Routes:** Embedded in `/dashboard` or `GET /balance`
- **Pages:** Section within `dashboard.html`

### Transactions Module
- **Purpose:** Allow customers to move money in and out of their account.
- **Handles:**
  - **Deposit:** Accept a positive amount, validate input, add to balance, record transaction.
  - **Withdrawal:** Accept a positive amount, validate input, check sufficient balance, subtract from balance, record transaction.
  - Return success or error feedback to the user after each operation.
- **Key Routes:** `GET/POST /deposit`, `GET/POST /withdraw`
- **Pages:** `deposit.html`, `withdraw.html`

---

## 6. Implementation Roadmap

### Development Phases

#### Phase 1 — Project Scaffold
- Create `FRONTEND/` and `BACKEND/` directory structures.
- Initialise Flask app in `BACKEND/app.py` with a health-check route.
- Add `requirements.txt` with Flask and Werkzeug.
- Confirm the CI pipeline (`docs/banking-app-ci.yml`) can install dependencies and run (empty) tests.

**Dependencies:** None  
**Estimated Effort:** Small

---

#### Phase 2 — Database Layer
- Implement `BACKEND/db.py`: connection helper, database initialisation routine, and seed data function.
- Create the SQLite database with customer and transaction tables on first run.
- Pre-populate at least one test customer account.

**Dependencies:** Phase 1  
**Estimated Effort:** Small

---

#### Phase 3 — Authentication
- Implement login/logout routes in `BACKEND/auth.py` and wire into `app.py`.
- Build `FRONTEND/templates/login.html` with Bootstrap form layout.
- Add a login-required decorator to protect all non-login routes.
- Write `tests/test_auth.py` covering valid login, invalid password, and logout.

**Dependencies:** Phase 2  
**Estimated Effort:** Medium

---

#### Phase 4 — Dashboard & Balance View
- Implement the `/dashboard` route in `app.py`.
- Build `FRONTEND/templates/dashboard.html` showing account name and balance.
- Ensure the page is only accessible to authenticated sessions.

**Dependencies:** Phase 3  
**Estimated Effort:** Small

---

#### Phase 5 — Transactions (Deposit & Withdrawal)
- Implement deposit and withdrawal logic in `BACKEND/transactions.py`.
- Build `FRONTEND/templates/deposit.html` and `withdraw.html` with Bootstrap forms.
- Wire routes into `app.py`; display success/error flash messages.
- Write `tests/test_transactions.py` covering normal deposit, normal withdrawal, and insufficient-funds rejection.

**Dependencies:** Phase 4  
**Estimated Effort:** Medium

---

#### Phase 6 — Polish & Integration Testing
- Apply consistent Bootstrap styling across all pages (navbar, alerts, responsive layout).
- End-to-end walkthrough: login → dashboard → deposit → withdraw → logout.
- Confirm all CI pipeline steps pass (install, lint if added, pytest).

**Dependencies:** Phase 5  
**Estimated Effort:** Small

---

### Phase Dependency Map

```
Phase 1 (Scaffold)
      │
      ▼
Phase 2 (Database Layer)
      │
      ▼
Phase 3 (Authentication)
      │
      ▼
Phase 4 (Dashboard)
      │
      ▼
Phase 5 (Transactions)
      │
      ▼
Phase 6 (Polish & Integration)
```

---

*End of Implementation Plan*
