/**
 * api.js — Finance Analyzer Team 3 Data Layer
 *
 * Includes Bearer Token authentication, document ownership,
 * audit history querying, and WP-514 matrix fetching.
 */

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true" || false;
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

const TOKEN_KEY = "fa_auth_token";

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function clearAuthToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// ── Fixture paths (mock mode only) ───────────────────────────────────────────
const FIXTURE_DASHBOARD = "/fixtures/dashboard.sample.json";
const FIXTURE_EVIDENCE  = "/fixtures/evidence.sample.json";

// ── Generic fetch helper ──────────────────────────────────────────────────────

async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  
  const token = getAuthToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const fetchOptions = {
    ...options,
    headers,
    credentials: options.credentials || "include",
  };

  let response;
  try {
    response = await fetch(url, fetchOptions);
  } catch (networkErr) {
    throw new Error(`Network error reaching ${url}: ${networkErr.message}`);
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch (_) {}
    
    // Auto-clear invalid/expired token on 401
    if (response.status === 401 && !url.includes("/auth/login")) {
      clearAuthToken();
    }
    
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

// ── Authentication Endpoints ─────────────────────────────────────────────────

export async function loginUser(email, password) {
  const res = await apiFetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (res.access_token) {
    setAuthToken(res.access_token);
  }
  return res;
}

export async function registerUser(email, password, fullName = "") {
  const res = await apiFetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  if (res.access_token) {
    setAuthToken(res.access_token);
  }
  return res;
}

export async function fetchCurrentUser() {
  return apiFetch(`${API_BASE}/auth/me`);
}

export async function logoutUser() {
  try {
    await apiFetch(`${API_BASE}/auth/logout`, { method: "POST" });
  } catch (_) {}
  clearAuthToken();
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

// ── Audit History & Document Management ──────────────────────────────────────

/**
 * Fetch all documents owned by current user.
 */
export async function fetchMyDocuments() {
  return apiFetch(`${API_BASE}/documents`);
}

/**
 * Fetch single document metadata.
 */
export async function fetchDocumentMetadata(documentId) {
  return apiFetch(`${API_BASE}/documents/${encodeURIComponent(documentId)}`);
}

/**
 * Delete a user-owned document.
 */
export async function deleteDocument(documentId) {
  return apiFetch(`${API_BASE}/documents/${encodeURIComponent(documentId)}`, {
    method: "DELETE",
  });
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

// ── WP-514 Matrix ─────────────────────────────────────────────────────────────

export async function fetchWP514Review(documentId) {
  return apiFetch(`${API_BASE}/documents/${encodeURIComponent(documentId)}/wp514`);
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
