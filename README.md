# NOMAYA — Premium D2C Saree & Drape Commerce

A local-first full-stack starter implementing the supplied NOMAYA visual direction: warm ivory backgrounds, deep plum typography, editorial serif headings, premium cards, animated Drape Finder, Draping Studio, customer auth, catalog, cart, wishlist, orders, and a Django admin.

## Stack
- Frontend: React + Vite + TypeScript + CSS + Framer Motion + React Router
- Backend: Django + Django REST Framework + SimpleJWT
- Database: PostgreSQL
- Local DB helper: Docker Compose (optional)

> SQL Developer is primarily an Oracle tool. For PostgreSQL use PostgreSQL + pgAdmin/psql, or start the included Docker PostgreSQL service.

## 1. Start PostgreSQL
### Option A — Docker (recommended)
```bash
docker compose up -d db
```
### Option B — Existing PostgreSQL
Create a database named `nomaya` and update `backend/.env`.

## 2. Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows CMD
# .venv\\Scripts\\activate.bat
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_nomaya
python manage.py createsuperuser
python manage.py runserver
```
Backend: http://127.0.0.1:8000
Admin: http://127.0.0.1:8000/admin/
API: http://127.0.0.1:8000/api/

## 3. Frontend
Open a second terminal:
```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```
Frontend: http://localhost:5173

## Demo account
After running the seed command:
- Email: demo@nomaya.local
- Password: Nomaya@12345

## Main routes
- `/` Home
- `/collections` Catalog + filters
- `/product/:slug` Product detail
- `/draping-studio` Interactive drape configurator
- `/drape-finder` Personalised recommendation flow
- `/login`, `/signup`
- `/cart`
- `/profile`
- `/admin` Django admin is separate from the React dashboard

## Production notes
Payment gateways, OAuth provider credentials, shipping APIs, transactional email, object storage and production secrets are intentionally environment-driven. The local order flow is functional and records orders in PostgreSQL; connect Razorpay/Stripe/other provider only after adding verified credentials.

## Visual direction
The implementation is original and inspired by the supplied NOMAYA references and the general premium editorial feel of Suta.in. Do not reuse Suta trademarks, copy, or proprietary assets.


## Oracle Database setup (no Docker)

This version is configured for Oracle Database instead of PostgreSQL.

1. Make sure Oracle Database is running and SQL Developer can connect.
2. Create an application user, for example:
   ```sql
   CREATE USER nomaya IDENTIFIED BY "YOUR_PASSWORD";
   GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE, CREATE VIEW, CREATE TRIGGER, CREATE PROCEDURE TO nomaya;
   ```
3. Copy `backend/.env.example` to `backend/.env`.
4. Set `ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_HOST`, `ORACLE_PORT`, and `ORACLE_SERVICE_NAME`.
5. In `backend`:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py seed_nomaya
   python manage.py createsuperuser
   python manage.py runserver
   ```
6. In `frontend`:
   ```cmd
   npm install
   npm run dev
   ```

Do not run the PostgreSQL `database/create_database.sql` for the Oracle configuration. Django migrations create the application tables.
