# Finance Analyzer — Production Deployment Guide

This guide describes how to deploy the **Finance Analyzer (Team 1, Team 2, and Team 3)** platform to production environments (Render, AWS, Railway, Vercel, Docker).

---

## Architecture Overview

* **Backend**: FastAPI with Uvicorn (Python 3.10+)
* **Database**: PostgreSQL (Production) / SQLite (Development)
* **Frontend**: React 18 SPA built with Vite (Static deployment)
* **AI Engine**: Google Gemini API via server-side grounding (keys never exposed to frontend)
* **File Storage**: Persistent storage mount for `/uploads` and `/outputs`

---

## 1. Environment Variables

### Backend Environment Variables (`.env` or Cloud Dashboard)

| Variable | Required | Description | Example |
| :--- | :---: | :--- | :--- |
| `PORT` | Auto | Port provided by host environment | `8000` (Render/Heroku injects `$PORT`) |
| `DATABASE_URL` | **Yes** | SQLAlchemy connection URI | `postgresql://user:pass@host:5432/finance_db` |
| `JWT_SECRET_KEY` | **Yes** | 32+ byte cryptographic secret for JWT signing | `d8a9f3...` (generate with `secrets.token_hex(32)`) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token lifetime in minutes | `1440` (24 hours) |
| `GEMINI_API_KEY` | **Yes** | Google Gemini API Key | `AIzaSy...` (from Google AI Studio) |
| `GEMINI_MODEL` | No | Gemini Model identifier | `gemini-2.5-flash` |
| `FRONTEND_URL` | **Yes** | Allowed CORS origins (comma-separated) | `https://finance-analyzer.vercel.app` |
| `UPLOAD_DIR` | No | Path to store uploaded files | `/var/data/uploads` |
| `OUTPUT_DIR` | No | Path to store analyzed outputs | `/var/data/outputs` |

### Frontend Environment Variables (`.env.production` or Cloud Dashboard)

| Variable | Required | Description | Example |
| :--- | :---: | :--- | :--- |
| `VITE_API_BASE_URL` | **Yes** | Public backend API URL | `https://api.financeanalyzer.com` |

---

## 2. Render 1-Click Deployment (Recommended)

The repository includes a `render.yaml` Blueprint specification.

1. Connect your GitHub repository to [Render](https://render.com/).
2. Select **Blueprints** $	o$ **New Blueprint Instance**.
3. Render will provision:
   * **PostgreSQL Database** (`finance-analyzer-db`)
   * **FastAPI Web Service** (`finance-analyzer-api`) with 10GB persistent disk
   * **Static Site Frontend** (`finance-analyzer-ui`)
4. Add your `GEMINI_API_KEY` in the Render Environment Variables tab for the backend.
5. Click **Apply Blueprint**.

---

## 3. Manual Deployment Instructions

### A. Backend Deployment (Render / Railway / Fly.io / AWS EC2)

1. **Build Command**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Start Command**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
3. **Health Check Endpoint**:
   ```http
   GET /health
   ```
   Expected response: `{"status": "ok", "service": "Finance Analyzer Team 3 API"}`

4. **Persistent Disk Storage**:
   Attach a persistent disk mounted to `/var/data` and configure:
   * `UPLOAD_DIR=/var/data/uploads`
   * `OUTPUT_DIR=/var/data/outputs`

### B. PostgreSQL Database Setup

1. Create a PostgreSQL database instance on Render, Neon, Supabase, or AWS RDS.
2. Copy the connection string (e.g., `postgresql://user:password@host:5432/finance_db`).
3. Set `DATABASE_URL` in the backend environment.
4. The application automatically initializes all tables on startup via `init_db()`.
5. *(Optional)* Seed initial auditor accounts:
   ```bash
   python backend/db/seed.py
   ```
   Default accounts seeded:
   * `auditor@example.com` / `DemoPassword123!`
   * `demo@financeanalyzer.local` / `DemoPassword123!`

### C. Frontend Deployment (Vercel / Netlify / Cloudflare Pages / Render)

1. **Root Directory**: `frontend/`
2. **Build Command**:
   ```bash
   npm install && npm run build
   ```
3. **Publish Directory**:
   `dist` (or `frontend/dist` if building from root)
4. **Environment Variable**:
   ```env
   VITE_API_BASE_URL=https://your-backend-api-url.com
   ```

---

## 4. Post-Deployment Verification Checklist

Once deployed, verify:

1. **Health Check**:
   ```bash
   curl https://your-backend-url.com/health
   # Expected: {"status":"ok","service":"Finance Analyzer Team 3 API"}
   ```
2. **CORS Verification**:
   Ensure `FRONTEND_URL` matches the deployed frontend URL so authentication cookies and `Authorization: Bearer` headers pass through without CORS errors.
3. **Authentication & Upload Flow**:
   * Open the frontend URL $	o$ Verify `LoginScreen` renders.
   * Sign in using the seeded auditor account or register a new account.
   * Upload `tests/fixtures/automobile_datasets/Apex_Auto_Mobility_ALL_PASS_Finance_Analyzer_Test.xlsx`.
   * Verify WP-514 matrix renders 100/100 and General Financial Ledger loads correctly.
