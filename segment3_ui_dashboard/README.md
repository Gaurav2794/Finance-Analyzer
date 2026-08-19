# Segment 3: Interactive Financial Audit Dashboard & AI Presentation Layer

Segment 3 delivers the complete interactive UI, audit dashboard, WP-514 matrix viewer, and presentation backend for the Finance-Analyzer platform.

## Architecture

- **Frontend (`frontend/`)**: Modern React + Vite financial dashboard built with custom Deep Green & Mint styling, interactive Recharts data visualizations, real-time multi-field search, responsive design, and audit findings drill-downs.
  - `FinancialAuditDashboard.jsx`: Main executive dashboard view featuring Core Financial Metrics, Financial Overview interactive charts, Key Financial Ratios, and live Findings Breakdown.
  - `src/components/WP514ReviewMatrix.jsx`: Standardized WP-514 Financial Statement Review matrix covering 10 audit categories and 62 automated verification procedures with animated progress bars and collapsible procedure details.
  - `src/components/AuditReport.jsx`: Comprehensive executive audit report viewer.
  - `src/components/EvidencePanel.jsx`: Line-item verification evidence viewer.
  - `src/components/AskAIPanel.jsx`: Grounded Gemini AI interactive audit assistant.

- **Backend Presentation Layer (`backend/`)**: FastAPI server orchestrating the end-to-end audit pipeline, document storage, and presentation endpoints.
  - `backend/routes/documents.py`: Document upload and pipeline orchestration (`POST /api/documents/upload`, `GET /api/documents/{id}/status`).
  - `backend/routes/financial.py`: Presentation data endpoints (`GET /api/documents/{id}/dashboard`, `GET /api/documents/{id}/wp514`, `GET /api/documents/{id}/report`).
  - `backend/routes/evidence.py`: Verification check evidence extraction (`GET /api/documents/{id}/evidence/{finding_id}`).
  - `backend/routes/ai.py`: Grounded Gemini conversational endpoint (`POST /api/ai/ask`).
  - `backend/services/dashboard_service.py`: High-performance data mapping adapter between Team 1 extractions, Team 2 calculations, and frontend presentation models.
  - `backend/services/wp514_service.py`: Standardized WP-514 matrix generator and check normalizer.

## Getting Started

### Launching Segment 3

You can launch both the FastAPI backend and Vite React dashboard together:

```bash
python run_segment3.py
```

Or run them individually:

```bash
# Start backend server (port 8000)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Start frontend dev server (port 5173)
cd frontend && npm run dev
```
