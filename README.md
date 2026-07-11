# Full Stack Flask Record Management System

A modular Flask + SQLite record management application with JWT authentication, ADMIN/CLIENT authorization, Pydantic validation, bcrypt passwords, Loguru logging, audit history, login history, soft delete, workflow actions and a Bootstrap/Vanilla JavaScript frontend.

## Requirements

- Python 3.10+
- No external database. SQLite is created automatically at `backend/database.db`.

## Setup on Windows

1. Open Command Prompt in the project folder.
2. Create a virtual environment:
   `python -m venv venv`
3. Activate it:
   `venv\Scripts\activate`
4. Install packages:
   `pip install -r backend\requirements.txt`
5. Copy `backend\.env.example` to `backend\.env`.
6. Change both secrets in `.env` before production use.
7. Run:
   `python backend\app.py`
8. Open `http://127.0.0.1:5000/`.

## Seed users

Clients: `client1@gmail.com`, `client2@gmail.com`, `client3@gmail.com`

Admins: `admin1@gmail.com`, `admin2@gmail.com`

Password for all seed users: `Admin@123`

Seed creation is idempotent. Existing seed emails are never duplicated.

## Important architecture

- `models/`: SQLAlchemy entities.
- `schemas/`: Pydantic request validation.
- `routes/`: thin HTTP controllers.
- `services/`: reusable business/audit services.
- `middleware/`: authentication and role checks.
- `utils/`: errors, responses and logging.
- `auth/`: password security.
- `frontend/`: HTML/CSS/ES6 Axios UI.

## Login flow

The browser posts credentials to `/api/auth/login`. The backend verifies bcrypt, invalidates previous active tokens, creates a JWT, stores token/login-device metadata, and returns the role. `login.html` saves the JWT in local storage and redirects ADMIN to `admin.html` and CLIENT to `client.html`.

All protected Axios calls attach `Authorization: Bearer <token>`. `/api/auth/validate-token` verifies both the JWT and its active database token record.

## Database initialization

At application startup `db.create_all()` creates all missing tables. `seed_users()` creates only missing sample users. `logs`, `uploads`, `static`, and `templates` folders are created automatically.

## Error handling and logs

Application exceptions use reusable custom exception classes and one global error pipeline. Failed DB work is rolled back. API clients receive standardized safe JSON. Detailed traceback context is written to rotating Loguru files:

- `backend/logs/application.log`
- `backend/logs/error.log`
- `backend/logs/security.log`

Passwords and JWT secrets are never intentionally logged or returned.

## Swagger

Flasgger is initialized. Open `/apidocs/` after starting Flask. The included Postman collection is under `postman/`.

## Production notes

The project is directly runnable for local/internal deployment. For internet-facing production deployment, set strong environment secrets, disable Flask debug mode, terminate TLS at a reverse proxy, use a production WSGI server appropriate to the operating system, restrict CORS origins, add CSRF protections if moving JWTs to cookies, and establish backup/retention procedures for the SQLite database and logs.
