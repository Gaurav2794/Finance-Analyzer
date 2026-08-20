/**
 * api.js — Finance Analyzer Team 3 Data Layer
 *
 * Centralized Token Management, Global 401 Session Handling,
 * and Protected API Request Execution.
 */

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true" || false;
const rawBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || "http://localhost:8000/api";
const API_BASE = rawBase.endsWith("/api") ? rawBase : `${rawBase.replace(/\/+$/, "")}/api`;

export const AUTH_TOKEN_KEY = "finance_analyzer_token";

let authStateListeners = [];

export function subscribeAuthChange(listener) {
  authStateListeners.push(listener);
  return () => {
    authStateListeners = authStateListeners.filter((l) => l !== listener);
  };
}

function notifyAuthChange(user, errorMsg = null) {
  authStateListeners.forEach((fn) => fn(user, errorMsg));
}

export function getAuthToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY) || "";
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  }
}

export function clearAuthToken() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

// ── Fixture paths (mock mode only) ───────────────────────────────────────────
const FIXTURE_DASHBOARD = "/fixtures/dashboard.sample.json";
const FIXTURE_EVIDENCE  = "/fixtures/evidence.sample.json";

// ── Generic fetch helper ──────────────────────────────────────────────────────

async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  
  const token = getAuthToken();
  const isAuthEndpoint = url.includes("/auth/login") || url.includes("/auth/register");
  
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
    
    // Handle 401 Unauthorized globally
    if (response.status === 401 && !isAuthEndpoint) {
      clearAuthToken();
      notifyAuthChange(null, "Your session has expired. Please sign in again.");
      throw new Error("Your session has expired. Please sign in again.");
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
    notifyAuthChange(res.user, null);
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
    notifyAuthChange(res.user, null);
  }
  return res;
}

export async function fetchCurrentUser() {
  const token = getAuthToken();
  if (!token) return null;
  return apiFetch(`${API_BASE}/auth/me`);
}

export async function logoutUser() {
  try {
    await apiFetch(`${API_BASE}/auth/logout`, { method: "POST" });
  } catch (_) {}
  clearAuthToken();
  notifyAuthChange(null, null);
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

export async function fetchMyDocuments() {
  return apiFetch(`${API_BASE}/documents`);
}

export async function fetchDocumentMetadata(documentId) {
  return apiFetch(`${API_BASE}/documents/${encodeURIComponent(documentId)}`);
}

export async function deleteDocument(documentId) {
  return apiFetch(`${API_BASE}/documents/${encodeURIComponent(documentId)}`, {
    method: "DELETE",
  });
}

// ── Pipeline status ───────────────────────────────────────────────────────────

export async function fetchStatus(documentId) {
  return apiFetch(`${API_BASE}/documents/${encodeURIComponent(documentId)}/status`);
}

// ── Dashboard data ────────────────────────────────────────────────────────────

export async function fetchDashboard(documentId) {
  if (USE_MOCK) return apiFetch(FIXTURE_DASHBOARD);
  return apiFetch(`${API_BASE}/documents/${encodeURIComponent(documentId)}/dashboard`);
}

// ── WP-514 Matrix ─────────────────────────────────────────────────────────────

export async function fetchWP514Review(documentId) {
  return apiFetch(`${API_BASE}/documents/${encodeURIComponent(documentId)}/wp514`);
}

// ── Evidence ──────────────────────────────────────────────────────────────────

export async function fetchEvidence(documentId, findingId) {
  if (USE_MOCK) return apiFetch(FIXTURE_EVIDENCE);
  return apiFetch(
    `${API_BASE}/documents/${encodeURIComponent(documentId)}/evidence/${encodeURIComponent(findingId)}`
  );
}

// ── AI ────────────────────────────────────────────────────────────────────────

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

export async function fetchReport(documentId) {
  if (USE_MOCK) return apiFetch(FIXTURE_DASHBOARD);
}