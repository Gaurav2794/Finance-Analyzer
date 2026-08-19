/**
 * api.js — Finance Analyzer Team 3 Data Layer
 *
 * MODE SWITCH
 * -----------
 * USE_MOCK=true  → reads fixture files from /fixtures/ (offline demo)
 * USE_MOCK=false → calls the real FastAPI backend (real pipeline results)
 *
 * The response shape returned by each function is IDENTICAL in both modes.
 * The UI components are never aware of which mode is active.
 *
 * Non-negotiable constraints:
 *  - Never compute growth_pct, ratios, or overall_score here.
 *  - Do not rename Team 1/2 fields.
 *  - If a value is missing, pass null through — the UI renders "Not available".
 */

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true" || false;
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

// ── Fixture paths (mock mode only) ───────────────────────────────────────────
const FIXTURE_DASHBOARD = "/fixtures/dashboard.sample.json";
const FIXTURE_EVIDENCE  = "/fixtures/evidence.sample.json";

// ── Generic fetch helper ──────────────────────────────────────────────────────

async function apiFetch(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (networkErr) {
    throw new Error(`Network error reaching ${url}: ${networkErr.message}`);
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch (_) {}
    throw new Error(`API ${response.status}: ${detail}`);
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    const preview = await response.text();
    throw new Error(
      `Expected JSON from ${url} but received "${contentType}" — ` +
      `starts with: ${preview.slice(0, 80).replace(/\s+/g, " ")}`
    );
  }

  return response.json();
}

// ── Upload ────────────────────────────────────────────────────────────────────

/**
 * Upload a financial document. Returns { document_id, status, filename }.
 * @param {File} file
 */
export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  return apiFetch(`${API_BASE}/documents/upload`, { method: "POST", body: form });
}

// ── Pipeline status ───────────────────────────────────────────────────────────

/**
 * Poll pipeline status for a document.
 * Returns { document_id, status, step, error }
 * status values: UPLOADED | EXTRACTING | EXTRACTED | REVIEWING | COMPLETED | FAILED
 * @param {string} documentId
 */
export async function fetchStatus(documentId) {
  return apiFetch(`${API_BASE}/documents/${encodeURIComponent(documentId)}/status`);
}

// ── Dashboard data ────────────────────────────────────────────────────────────

/**
 * Fetch the combined dashboard data (Team 1 + Team 2 via presentation adapter).
 * Returns { extraction_result, analysis_result }.
 * @param {string} documentId
 */
export async function fetchDashboard(documentId) {
  if (USE_MOCK) return apiFetch(FIXTURE_DASHBOARD);
  return apiFetch(`${API_BASE}/documents/${encodeURIComponent(documentId)}/dashboard`);
}

// ── Legacy compatibility shims (keep EvidencePanel/AskAIPanel working) ────────

/**
 * @deprecated Use fetchDashboard() instead.
 * Kept for backward-compat with EvidencePanel / AskAIPanel.
 */
export async function fetchExtractionResult(documentId) {
  const dash = await fetchDashboard(documentId);
  return dash.extraction_result;
}

/**
 * @deprecated Use fetchDashboard() instead.
 * Kept for backward-compat with EvidencePanel / AskAIPanel.
 */
export async function fetchAnalysisResult(documentId) {
  const dash = await fetchDashboard(documentId);
  return dash.analysis_result;
}

// ── Evidence ──────────────────────────────────────────────────────────────────

/**
 * Fetch source evidence for a finding.
 * Real mode: GET /api/documents/{id}/evidence/{finding_id}
 * Returns { status, finding, source, passage, message }
 * @param {string} documentId
 * @param {string} findingId
 */
export async function fetchEvidence(documentId, findingId) {
  if (USE_MOCK) return apiFetch(FIXTURE_EVIDENCE);
  return apiFetch(
    `${API_BASE}/documents/${encodeURIComponent(documentId)}/evidence/${encodeURIComponent(findingId)}`
  );
}

// ── AI ────────────────────────────────────────────────────────────────────────

/**
 * Ask AI about a finding or general report review.
 * Returns { answer, sections, grounded, sources, ai_provider }
 * @param {string} documentId
 * @param {string|null} findingId
 * @param {string} question
 * @param {string|null} category
 */
export async function askAI(documentId, findingId = null, question = "Why was this flagged?", category = null) {
  return apiFetch(`${API_BASE}/documents/${encodeURIComponent(documentId)}/ai`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      finding_id: findingId || undefined,
      question,
      category: category || undefined,
    }),
  });
}

// ── Report ────────────────────────────────────────────────────────────────────

/**
 * Fetch the full report payload (same data as dashboard + full check blocks).
 * @param {string} documentId
 */
export async function fetchReport(documentId) {
  if (USE_MOCK) return apiFetch(FIXTURE_DASHBOARD);
  return apiFetch(`${API_BASE}/documents/${encodeURIComponent(documentId)}/report`);
}
