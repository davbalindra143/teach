# Teaching App

A Python-based learning management app for schools and coaching centers.

Features:
- Multiple classes and subjects
- Chapter-wise notes with direct links
- Practice sets by chapter
- Question papers upload + student download/view
- Online Python code runner
- FastAPI + PostgreSQL backend
- Streamlit frontend

Project structure:
- backend_app.py - FastAPI app with SQLAlchemy + PostgreSQL
- frontend_app.py - Streamlit student/admin UI
- docker-compose.yml - PostgreSQL service
- seed_data.py - demo data creator
- .env - environment values

## Tech stack
- Frontend: Python + Streamlit
- Backend: Python + FastAPI
- Database: PostgreSQL

## Quick start

1. Start PostgreSQL with Docker: `docker compose up -d`
2. Update `.env` with your local Postgres settings if needed
3. Install backend dependencies: `pip install -r backend_requirements.txt`
4. Run backend: `uvicorn backend_app:app --reload --host 0.0.0.0 --port 8000`
5. Install frontend dependencies: `pip install -r frontend_requirements.txt`
6. Run frontend: `streamlit run frontend_app.py`

## Backend setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend_requirements.txt
uvicorn backend_app:app --reload --host 0.0.0.0 --port 8000
```

## Frontend setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r frontend_requirements.txt
streamlit run frontend_app.py
```

## Free Render deployment

This project includes `render.yaml` for deploying the FastAPI backend and Streamlit frontend as two Render web services.

1. Push this folder to a GitHub repository.
2. In Render, choose **New > Blueprint** and select the repository.
3. Set `DATABASE_URL` on `teaching-app-api` to a hosted PostgreSQL connection string.
4. Set `ADMIN_PASSWORD` on `teaching-app-frontend`.
5. Deploy both services. Open the generated `teaching-app-frontend` URL.

The free web services may sleep when idle. SQLite and local uploads are not persistent on free hosting, so PostgreSQL and object storage should be configured before relying on uploaded books or files.

## VPS deployment with Docker

The production Compose file runs PostgreSQL, the FastAPI backend, and the Streamlit frontend together. The frontend binds to `127.0.0.1:8502`, leaving the host's public ports available for the existing app and reverse proxy.

1. Copy the project to the VPS and install Docker Compose.
2. Create a `.env` file containing `ADMIN_PASSWORD` and optionally `CONTACT_NUMBER`.
3. Start the stack:

```bash
docker compose up -d --build
```

Point a new domain or subdomain in the existing Nginx/Caddy proxy to `127.0.0.1:8502`. Do not expose PostgreSQL publicly. Keep `ADMIN_PASSWORD` only in the VPS `.env` file and do not commit it.

## Default admin data flow
- Create classes from the API or through database seed scripts.
- Add subjects under a class, then chapters under subject.
- Add notes, practice sets, and question papers for each chapter.

## Notes
This MVP is intentionally simple, ideal for a local classroom app. For production, add:
- authentication and roles
- file storage (AWS S3 / MinIO)
- sandboxed code execution for Python
- PDF rendering and download protection
