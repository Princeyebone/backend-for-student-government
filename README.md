#  Student Government CMS — Backend API

A production-ready **Content Management System API** built for a Student Government website. It powers all public-facing content (news, leadership, gallery, hero slideshow, contact) and provides a secure administrative interface for managing that content, users, and legislative senate bills.

**Live Frontend:** [student-government-website.vercel.app](https://student-government-website.vercel.app)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Project Structure](#project-structure)
- [Database Models](#database-models)
- [API Reference](#api-reference)
- [Authentication & Authorization](#authentication--authorization)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running the Server](#running-the-server)
- [Security](#security)
- [Deployment](#deployment)

---

## Overview

This is the backend REST API for the Student Government CMS. It is built with **FastAPI** and **PostgreSQL** (via SQLModel), and integrates with **Cloudinary** for image hosting. All sensitive content mutations require JWT authentication. Public read endpoints are open and return graceful empty responses when the database is empty.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) `>=0.129` |
| **Database ORM** | [SQLModel](https://sqlmodel.tiangolo.com/) `>=0.0.33` (built on SQLAlchemy + Pydantic) |
| **Database** | PostgreSQL `>=14` |
| **DB Driver** | psycopg2-binary |
| **Authentication** | JWT (access + refresh tokens) via `python-jose` |
| **Password Hashing** | Argon2 via `argon2-cffi` |
| **Image Hosting** | [Cloudinary](https://cloudinary.com/) |
| **Settings** | `pydantic-settings` (loads from `.env`) |
| **Runtime** | Python `>=3.12` |
| **ASGI Server** | Uvicorn |
| **Package Manager** | [uv](https://github.com/astral-sh/uv) |

---

## Features

### 🔐 Authentication & User Management
- **JWT-based auth** with separate short-lived access tokens (24h) and long-lived refresh tokens (30 days)
- **Role-based access control** — two roles: `admin` and `editor`
- Admin self-registration bootstrap endpoint (should be disabled after first admin is created)
- Admin-only editor creation — new editors receive a temporary default password and are prompted to change it on first login
- Password change endpoint (authenticated)
- Token refresh endpoint
- Full **audit log** — every action (login, create, update, delete) is recorded with user info, IP address, and timestamp

### 📰 Content Management
All content sections support full CRUD with authentication. Public `GET` endpoints require no authentication and return empty arrays/null gracefully when no data exists.

| Section | Description |
|---|---|
| **News** | Create, read, update, delete news articles with optional Cloudinary images |
| **Leadership** | Manage student government leadership profiles with photos, roles, and academic year |
| **Gallery** | Image gallery with captions and Cloudinary integration |
| **Home** | Hero section — hero image, hero text, and president's desk message |
| **Hero Slideshow** | Multi-slide carousel with ordering, captions, and active/inactive toggling |
| **Contact** | Organization contact information (address, email, phone) |

### 🏛️ Senate Bills
A full legislative tracking system for the Student Senate:
- Track bills through a defined lifecycle: **Draft → Under Review → Voting → Approved / Rejected**
- Categorize bills: `Welfare`, `Academic`, `Finance`, `Infrastructure`, `Events`, `Constitutional`
- Record voting outcomes (votes for, against, abstain, total senators)
- Attach supporting documents (JSON array)
- Auto-generated timeline entries on every status change
- Filter by status, category, or search by title
- Public read, authenticated write, admin-only delete

### 📤 Cloudinary Upload Signatures
- Backend generates signed upload parameters for **direct browser-to-Cloudinary uploads**
- Uses NTP time sync (Google NTP) to prevent stale-request errors from server clock drift
- Authenticated endpoint — only logged-in users can request upload signatures

### 🛡️ Security
- All secrets are loaded from environment variables — never hardcoded
- CORS configured for known frontend origins
- Argon2 password hashing (memory-hard, resistant to GPU attacks)
- Passwords hashed; never stored or returned in plaintext
- Audit logging on all sensitive operations
- Admin users cannot be deleted; admins cannot delete themselves

---

## Project Structure

```
backend/
├── src/
│   ├── main.py              # FastAPI app entrypoint, CORS config, router registration
│   ├── config.py            # Settings loaded from .env via pydantic-settings
│   ├── database.py          # SQLModel engine, session factory, table creation
│   ├── model.py             # All SQLModel table definitions (ORM models)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── auth.py              # JWT token creation/decoding, Argon2 password utilities
│   ├── dependencies.py      # FastAPI dependency injection (auth guards)
│   ├── audit.py             # Audit log helper
│   ├── routes_auth.py       # Auth & user management routes (/api/auth/*)
│   ├── routes_content.py    # CMS content routes (/api/news, /api/leadership, etc.)
│   ├── routes_bills.py      # Senate bills routes (/api/bills/*)
│   └── uploads.py           # Cloudinary upload signature route (/api/upload/*)
├── migrations/              # SQL migration scripts
├── .env.example             # Environment variable template (safe to commit)
├── .gitignore               # Excludes .env and sensitive files
├── pyproject.toml           # Project metadata and dependencies
├── requirements.txt         # Full dependency lockfile
└── README.md                # This file
```

---

## Database Models

| Model | Table | Description |
|---|---|---|
| `User` | `user` | Admin and editor accounts with UUID primary keys |
| `Home` | `home` | Hero section content (image, text, president's message) |
| `HeroSlide` | `heroslide` | Individual slides for the hero carousel |
| `Leadership` | `leadership` | Student government leaders with photos and roles |
| `News` | `news` | News articles with optional images |
| `Gallary` | `gallary` | Photo gallery items with captions |
| `Contact` | `contact` | Organization contact information |
| `AuditLog` | `auditlog` | Immutable log of all user actions |
| `Bill` | `bill` | Senate legislative bills with full lifecycle tracking |

### Bill Lifecycle

```
Draft  →  Under Review  →  Voting  →  Approved
                                   ↘  Rejected
```

Every status transition automatically appends a dated entry to the bill's `timeline` JSON field.

---

## API Reference

Interactive Swagger documentation is available at `/docs` when the server is running.

### Authentication — `/api/auth`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register/admin` | ❌ Public | Bootstrap first admin account |
| `POST` | `/api/auth/register/editor` | 🔒 Admin | Create a new editor account |
| `POST` | `/api/auth/login` | ❌ Public | Login with email + password → JWT tokens |
| `POST` | `/api/auth/login/form` | ❌ Public | OAuth2 form login (Swagger UI) |
| `POST` | `/api/auth/refresh` | ❌ Public | Exchange refresh token for new access token |
| `POST` | `/api/auth/change-password` | 🔑 Auth | Change own password |
| `GET` | `/api/auth/users` | 🔒 Admin | List all users |
| `DELETE` | `/api/auth/users/{id}` | 🔒 Admin | Delete an editor account |
| `GET` | `/api/auth/audit-logs` | 🔒 Admin | View paginated audit logs |

### Content — `/api`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/news/` | ❌ Public | List all news articles |
| `POST` | `/api/news/` | 🔑 Auth | Create a news article (FormData) |
| `PUT` | `/api/news/{id}` | 🔑 Auth | Update a news article |
| `DELETE` | `/api/news/{id}` | 🔑 Auth | Delete a news article |
| `GET` | `/api/leadership/` | ❌ Public | List all leadership members |
| `POST` | `/api/leadership/` | 🔑 Auth | Add a leadership member |
| `PUT` | `/api/leadership/{id}` | 🔑 Auth | Update a leadership member |
| `DELETE` | `/api/leadership/{id}` | 🔑 Auth | Remove a leadership member |
| `GET` | `/api/gallery/` | ❌ Public | List all gallery items |
| `POST` | `/api/gallery/` | 🔑 Auth | Add a gallery image |
| `PUT` | `/api/gallery/{id}` | 🔑 Auth | Update a gallery image |
| `DELETE` | `/api/gallery/{id}` | 🔑 Auth | Delete a gallery image |
| `GET` | `/api/home/` | ❌ Public | Get home section content |
| `PUT` | `/api/home/` | 🔑 Auth | Update home section content |
| `GET` | `/api/hero-slides/` | ❌ Public | List all hero slides |
| `POST` | `/api/hero-slides/` | 🔑 Auth | Add a hero slide |
| `PUT` | `/api/hero-slides/{id}` | 🔑 Auth | Update a hero slide |
| `DELETE` | `/api/hero-slides/{id}` | 🔒 Admin | Delete a hero slide |
| `GET` | `/api/contact/` | ❌ Public | Get contact information |
| `PUT` | `/api/contact/` | 🔑 Auth | Update contact information |

### Senate Bills — `/api/bills`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/bills/` | ❌ Public | List bills (filter: `?status=`, `?category=`, `?search=`) |
| `GET` | `/api/bills/{id}` | ❌ Public | Get a single bill's full details |
| `POST` | `/api/bills/` | 🔑 Auth | Create a new bill |
| `PUT` | `/api/bills/{id}` | 🔑 Auth | Update a bill (partial update supported) |
| `DELETE` | `/api/bills/{id}` | 🔒 Admin | Permanently delete a bill |

### Upload Signatures — `/api/upload`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/upload/signature` | 🔑 Auth | Get Cloudinary signed upload parameters |

### Health Check

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/` | ❌ Public | API welcome message and version |
| `GET` | `/health` | ❌ Public | Health check with database connectivity status |

---

## Authentication & Authorization

The API uses **Bearer JWT tokens**. Include the token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### User Roles

| Role | Permissions |
|---|---|
| `admin` | Full access — all read/write operations, user management, audit logs, admin-only deletes |
| `editor` | Read + content write — can create/update content and bills, cannot manage users or delete bills |

### Token Lifecycle

1. `POST /api/auth/login` → returns `access_token` (24h) + `refresh_token` (30 days)
2. Use `access_token` for all authenticated requests
3. When `access_token` expires, call `POST /api/auth/refresh` with `refresh_token` to get a new one
4. The response also includes `must_change_password: true` if the user is still on the default editor password

---

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 14+
- [uv](https://github.com/astral-sh/uv) package manager (recommended) — or pip
- A [Cloudinary](https://cloudinary.com/) account (free tier works)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/student-backend.git
cd student-backend/backend
```

### 2. Set up your environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your actual values (see [Environment Variables](#environment-variables) below).

### 3. Create the PostgreSQL database and user

Connect to PostgreSQL as a superuser and run:

```sql
CREATE USER your_db_user WITH PASSWORD 'your_password';
CREATE DATABASE your_db_name OWNER your_db_user;
GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_user;
```

### 4. Install dependencies

**Using uv (recommended):**
```bash
uv sync
```

**Using pip:**
```bash
pip install -r requirements.txt
```

### 5. Run the development server

```bash
uv run uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Swagger UI is at `http://localhost:8000/docs`.

### 6. Create your first admin account

Use the bootstrap endpoint (only needs to be called once):

```bash
curl -X POST http://localhost:8000/api/auth/register/admin \
  -H "Content-Type: application/json" \
  -d '{"name": "Your Name", "email": "admin@example.com", "password": "StrongPassword123"}'
```

> ⚠️ **Important:** Disable or protect this endpoint in production after your first admin is created.

---

## Environment Variables

Copy `.env.example` to `.env` and configure the following:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string: `postgresql://user:password@host:port/dbname` |
| `SECRET_KEY` | ✅ | Random secret for signing JWT tokens. Generate with: `openssl rand -hex 32` |
| `CLOUDINARY_CLOUD_NAME` | ✅ | Your Cloudinary cloud name (from Cloudinary dashboard) |
| `CLOUDINARY_API_KEY` | ✅ | Your Cloudinary API key |
| `CLOUDINARY_SECRET` | ✅ | Your Cloudinary API secret |

> **Never commit your `.env` file.** It is excluded by `.gitignore`. Use `.env.example` as a template.

---

## Running the Server

### Development

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or using a process manager like **gunicorn**:

```bash
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Security

- **Secrets in environment variables** — no credentials are hardcoded in source code
- **Argon2 password hashing** — memory-hard algorithm, resistant to brute-force and GPU attacks
- **JWT with token types** — access and refresh tokens are distinct types; a refresh token cannot be used as an access token
- **Role guards** — admin-only endpoints enforce `Role.ADMIN` before any operation
- **Self-deletion prevention** — admins cannot delete their own account
- **Admin protection** — admin accounts cannot be deleted by any user via the API
- **Audit logging** — every login, create, update, and delete action is recorded with actor, IP, timestamp, and details
- **CORS** — restricted to known frontend origins

---

## Deployment

This API is designed to be deployed on any Python-compatible platform:

- **Railway / Render / Fly.io** — recommended for simple PostgreSQL + Python deployments
- **AWS / GCP / Azure** — using App Service, Cloud Run, or EC2 with a managed PostgreSQL instance
- **Docker** — containerise with a `Dockerfile` using a Python 3.12 base image

Set all environment variables as **platform secrets / environment variables** — never as part of the deployed code.

The app performs automatic database table creation on startup, so no separate migration step is required for initial deployment.

---

## License

This project is proprietary software developed for the Student Government organization.

---

*Built with FastAPI, SQLModel, and PostgreSQL.*
