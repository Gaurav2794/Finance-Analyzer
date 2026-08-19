import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  uploadDocument,
  fetchStatus,
  fetchDashboard,
  fetchEvidence,
  askAI,
} from "./src/api.js";
import EvidencePanel from "./src/components/EvidencePanel.jsx";
import AskAIPanel from "./src/components/AskAIPanel.jsx";
import AuditReport from "./src/components/AuditReport.jsx";
import WP514ReviewMatrix from "./src/components/WP514ReviewMatrix.jsx";
import LedgerView from "./src/components/LedgerView.jsx";
import IntegrityChecksView from "./src/components/IntegrityChecksView.jsx";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import {
  AlertTriangle,
  FileText,
  Search,
  Sparkles,
  ShieldCheck,
  CircleAlert,
  AlertOctagon,
  TrendingUp,
  Coins,
  Award,
  AlertCircle,
  LayoutDashboard,
  Layers,
  Bell,
  FileSpreadsheet,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Wallet,
  Upload,
  CheckCircle2,
  Loader2,
  X,
  FileCheck2,
  ArrowLeft,
  Scale,
  Calculator,
  Repeat,
  Percent,
  FileSearch,
  ChevronDown,
  ChevronRight,
  Filter,
} from "lucide-react";

/* ============================================================
   SEVERITY PALETTES
   ============================================================ */

const sev = {
  CRITICAL: { color: "var(--color-danger)", bg: "var(--color-danger-soft)", label: "Critical", Icon: AlertOctagon },
  HIGH:     { color: "var(--color-warning)", bg: "var(--color-warning-soft)", label: "High", Icon: AlertTriangle },
  REVIEW:   { color: "var(--color-purple)", bg: "var(--color-purple-soft)", label: "Review", Icon: CircleAlert },
  PASSED:   { color: "var(--color-success)", bg: "var(--color-success-soft)", label: "Passed", Icon: ShieldCheck },
};

const INTEGRITY_CONFIG = {
  mathematical_accuracy: { name: "Mathematical Accuracy", Icon: Calculator },
  cash_flow: { name: "Cash Flow Reconciliation", Icon: Coins },
  prior_year_tieout: { name: "Prior Year Tie-out", Icon: Repeat },
  internal_consistency: { name: "Internal Consistency", Icon: Layers },
  document_quality: { name: "Document Quality", Icon: FileCheck2 },
  analytical_comparison: { name: "Analytical Comparison", Icon: Activity },
  ratios: { name: "Key Financial Ratios", Icon: Percent },
  unusual_fluctuation: { name: "Unusual Fluctuation", Icon: TrendingUp },
  unusual_gain: { name: "Unusual Gain / Divergence", Icon: Scale },
  related_disclosure: { name: "Related Party Disclosure", Icon: FileSearch },
};

const fmt = (n) => (n === null || n === undefined ? "—" : n.toLocaleString("en-IN"));
const pct = (n) => (n === null || n === undefined ? "—" : `${n > 0 ? "+" : ""}${Number(n).toFixed(2)}%`);
const na = (v, fallback = "Not available") => (v === null || v === undefined ? fallback : v);

/* ============================================================
   STAT CARD
   ============================================================ */

function FinDashStatCard({ title, value, sub, subColor, subIcon: SubIcon, icon: Icon, iconColor, iconBg, isMissing, delay }) {
  return (
    <div className="fd-card animate-fade-up hover-scale" style={{ padding: "24px", animationDelay: delay || "0s" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: "14px", fontWeight: 500, color: "var(--text-secondary)", marginBottom: "8px" }}>{title}</div>
          <div style={{ fontSize: isMissing ? "18px" : "26px", fontWeight: isMissing ? 400 : 700, color: isMissing ? "var(--text-muted)" : "var(--text-primary)", fontStyle: isMissing ? "italic" : "normal", fontVariantNumeric: "tabular-nums" }}>
            {value}
          </div>
        </div>
        <div style={{ width: "52px", height: "52px", borderRadius: "50%", background: iconBg, display: "flex", alignItems: "center", justifyContent: "center", color: iconColor, flexShrink: 0 }}>
          <Icon size={24} strokeWidth={2.5} />
        </div>
      </div>
      <div style={{ marginTop: "14px", fontSize: "13px", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "6px" }}>
        {sub && (
          <span style={{ color: subColor, display: "flex", alignItems: "center", gap: "2px", fontWeight: 600 }}>
            {SubIcon && <SubIcon size={14} />}{sub}
          </span>
        )}
        {!sub && <span>&nbsp;</span>}
      </div>
    </div>
  );
}

/* ============================================================
   FINDING ITEM
   ============================================================ */

function FinDashFindingItem({ f, documentId }) {
  const [open, setOpen] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false);
  const [showAskAI, setShowAskAI] = useState(false);
  const s = sev[f.severity] || sev.REVIEW;
  const Icon = s.Icon;

  return (
    <div className="finding-item-card animate-fade-in" style={{ borderColor: open ? "rgba(59, 130, 246, 0.4)" : "var(--border-light)" }}>
      <div onClick={() => setOpen(!open)} style={{ display: "flex", alignItems: "center", gap: "12px", cursor: "pointer" }}>
        <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: s.bg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Icon size={18} color={s.color} strokeWidth={2.2} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {f.title}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "2px" }}>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 500 }}>
              {(f.category || "").replace(/_/g, " ")}
            </span>
            {f.id && (
              <span style={{ fontSize: "10px", color: "var(--text-muted)", background: "var(--bg-main)", padding: "1px 5px", borderRadius: "4px", fontFamily: "monospace" }}>
                {f.id}
              </span>
            )}
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0 }}>
          <span style={{
            fontSize: "11px",
            fontWeight: 700,
            color: s.color,
            background: s.bg,
            padding: "3px 8px",
            borderRadius: "6px",
            border: `1px solid ${s.color}25`,
            display: "inline-flex",
            alignItems: "center",
            gap: "4px"
          }}>
            <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: s.color }} />
            {s.label}
          </span>
          <div style={{
            width: "22px",
            height: "22px",
            borderRadius: "50%",
            background: open ? "var(--color-primary-soft)" : "transparent",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "transform 0.2s ease",
            transform: open ? "rotate(90deg)" : "rotate(0deg)"
          }}>
            <ChevronRight size={14} color={open ? "var(--color-primary)" : "var(--text-muted)"} />
          </div>
        </div>
      </div>

      {open && (
        <div className="animate-slide-down" style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid var(--border-light)" }}>
          <p style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: 1.6, margin: "0 0 12px" }}>
            {f.description || f.explanation || "Verification check recorded in workpaper."}
          </p>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <button onClick={(e) => { e.stopPropagation(); setShowEvidence(true); }} className="fd-btn fd-btn-outline" style={{ fontSize: "11px", padding: "5px 10px", borderRadius: "6px" }}>
              <FileText size={13} color="var(--color-primary)" /> View Evidence
            </button>
            <button onClick={(e) => { e.stopPropagation(); setShowAskAI(true); }} className="fd-btn" style={{ fontSize: "11px", padding: "5px 10px", borderRadius: "6px", background: "var(--color-warning-soft)", color: "var(--color-warning)", border: "1px solid rgba(245, 158, 11, 0.2)" }}>
              <Sparkles size={13} /> Ask AI
            </button>
          </div>
        </div>
      )}

      {showEvidence && <EvidencePanel documentId={documentId} finding={f} onClose={() => setShowEvidence(false)} />}
      {showAskAI && <AskAIPanel finding={f} documentId={documentId} onClose={() => setShowAskAI(false)} />}
    </div>
  );
}

/* ============================================================
   UPLOAD SCREEN
   ============================================================ */

const PIPELINE_STEPS = [
  { status: "UPLOADED",   label: "Document Uploaded",          icon: Upload },
  { status: "EXTRACTING", label: "Financial Data Extraction",  icon: Loader2 },
  { status: "EXTRACTED",  label: "Extraction Complete",        icon: CheckCircle2 },
  { status: "REVIEWING",  label: "Financial Review (Team 2)",  icon: Loader2 },
  { status: "COMPLETED",  label: "Dashboard Ready",            icon: CheckCircle2 },
];

function UploadScreen({ onDocumentReady }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [pipelineStep, setPipelineStep] = useState("");
  const [error, setError] = useState(null);
  const fileRef = useRef();
  const pollRef = useRef();

  const handleFile = useCallback(async (file) => {
    setError(null);
    setUploading(true);
    try {
      const res = await uploadDocument(file);
      setJobId(res.document_id);
      setPipelineStatus("UPLOADED");
      startPolling(res.document_id);
    } catch (err) {
      setError(err.message);
      setUploading(false);
    }
  }, []);

  const startPolling = useCallback((docId) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const st = await fetchStatus(docId);
        setPipelineStatus(st.status);
        setPipelineStep(st.step || "");
        if (st.status === "COMPLETED") {
          clearInterval(pollRef.current);
          setUploading(false);
          onDocumentReady(docId);
        } else if (st.status === "FAILED") {
          clearInterval(pollRef.current);
          setUploading(false);
          setError(st.error || "Pipeline failed. Please try again.");
        }
      } catch (err) {
        clearInterval(pollRef.current);
        setError(err.message);
        setUploading(false);
      }
    }, 2000);
  }, [onDocumentReady]);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer?.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const stepIndex = PIPELINE_STEPS.findIndex(s => s.status === pipelineStatus);

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-main)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "32px" }}>
      <div style={{ maxWidth: "520px", width: "100%" }}>
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div style={{ width: "56px", height: "56px", borderRadius: "50%", background: "var(--color-primary-soft)", color: "var(--color-primary)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
            <Activity size={28} />
          </div>
          <h1 style={{ fontSize: "26px", fontWeight: 700, color: "var(--text-primary)", margin: "0 0 8px" }}>Finance Analyzer</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px" }}>Upload a financial document to begin the analysis pipeline</p>
        </div>

        {!uploading ? (
          <div
            className="fd-card"
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
            style={{ padding: "48px 32px", textAlign: "center", cursor: "pointer", border: `2px dashed ${dragging ? "var(--color-primary)" : "var(--border-light)"}`, borderRadius: "16px", background: dragging ? "var(--color-primary-soft)" : "var(--bg-card)", transition: "all 0.15s ease" }}
          >
            <Upload size={36} color="var(--color-primary)" style={{ margin: "0 auto 16px" }} />
            <div style={{ fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", marginBottom: "8px" }}>
              Drop your financial document here
            </div>
            <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
              Supports PDF, XLSX, XLS, CSV, MD, TXT
            </div>
            <input ref={fileRef} type="file" accept=".pdf,.xlsx,.xls,.csv,.md,.txt" style={{ display: "none" }} onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
          </div>
        ) : (
          <div className="fd-card" style={{ padding: "32px" }}>
            <div style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: "24px", fontSize: "15px" }}>
              Processing Pipeline
            </div>
            {PIPELINE_STEPS.filter(s => s.status !== "COMPLETED").concat(PIPELINE_STEPS.filter(s => s.status === "COMPLETED")).map((step, i) => {
              const done = i < stepIndex;
              const active = i === stepIndex;
              const Icon = step.icon;
              return (
                <div key={step.status} style={{ display: "flex", alignItems: "center", gap: "14px", marginBottom: "18px" }}>
                  <div style={{ width: "32px", height: "32px", borderRadius: "50%", background: done ? "var(--color-success-soft)" : active ? "var(--color-primary-soft)" : "var(--bg-main)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                    {done ? <CheckCircle2 size={18} color="var(--color-success)" /> : active ? <Loader2 size={18} color="var(--color-primary)" style={{ animation: "spin 1s linear infinite" }} /> : <Icon size={18} color="var(--text-muted)" />}
                  </div>
                  <div style={{ fontSize: "13px", fontWeight: active ? 600 : 400, color: done ? "var(--color-success)" : active ? "var(--text-primary)" : "var(--text-muted)" }}>
                    {step.label}
                  </div>
                </div>
              );
            })}
            <div style={{ marginTop: "8px", fontSize: "12px", color: "var(--text-muted)" }}>{pipelineStep}</div>
          </div>
        )}

        {error && (
          <div style={{ marginTop: "16px", padding: "16px", background: "var(--color-danger-soft)", borderRadius: "12px", fontSize: "13px", color: "var(--color-danger)" }}>
            <strong>Error:</strong> {error}
            <button onClick={() => { setError(null); setUploading(false); setJobId(null); }} style={{ float: "right", background: "none", border: "none", cursor: "pointer", color: "var(--color-danger)" }}>
              <X size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ============================================================
   LOADING / ERROR SCREENS
   ============================================================ */

function LoadingScreen() {
  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-main)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16 }}>
      <div style={{ width: 48, height: 48, borderRadius: "50%", border: "3px solid #E2E8F0", borderTopColor: "var(--color-primary)", animation: "spin 0.8s linear infinite" }} />
      <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
      <div style={{ fontSize: "15px", color: "var(--text-secondary)", fontWeight: 600 }}>Loading Dashboard...</div>
    </div>
  );
}

function ErrorScreen({ message, onRetry }) {
  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-main)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div className="fd-card" style={{ maxWidth: 480, padding: 32, textAlign: "center" }}>
        <div style={{ width: 64, height: 64, borderRadius: "50%", background: "var(--color-danger-soft)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--color-danger)", margin: "0 auto 16px" }}>
          <AlertOctagon size={32} />
        </div>
        <h2 style={{ fontSize: "20px", fontWeight: 700, color: "var(--text-primary)", margin: "0 0 8px" }}>Unable to Load Data</h2>
        <p style={{ fontSize: "14px", color: "var(--text-secondary)", margin: "0 0 24px" }}>{message}</p>
        <button id="error-retry-btn" onClick={onRetry} className="fd-btn fd-btn-primary">
          <RefreshCw size={16} /> Retry
        </button>
      </div>
    </div>
  );
}

/* ============================================================
   MAIN DASHBOARD
   ============================================================ */

export default function FinancialAuditDashboard() {
  const [documentId, setDocumentId] = useState(null);
  const [extractionResult, setExtractionResult] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [route, setRoute] = useState(window.location.hash || "");
  const [searchQuery, setSearchQuery] = useState("");
  const [chartMetric, setChartMetric] = useState("revenue");
  const [findingFilter, setFindingFilter] = useState("ALL");
  const [showGlobalAI, setShowGlobalAI] = useState(false);
  const [selectedFindingForEvidence, setSelectedFindingForEvidence] = useState(null);

  useEffect(() => {
    const fn = () => setRoute(window.location.hash);
    window.addEventListener("hashchange", fn);
    return () => window.removeEventListener("hashchange", fn);
  }, []);

  const loadDashboard = useCallback(async (docId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDashboard(docId);
      setExtractionResult(data.extraction_result);
      setAnalysisResult(data.analysis_result);
    } catch (err) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDocumentReady = useCallback((docId) => {
    setDocumentId(docId);
    loadDashboard(docId);
  }, [loadDashboard]);

  // Show upload screen if no document loaded
  if (!documentId && !loading) {
    return <UploadScreen onDocumentReady={handleDocumentReady} />;
  }

  if (loading) return <LoadingScreen />;
  if (error) return <ErrorScreen message={error} onRetry={() => loadDashboard(documentId)} />;
  if (!extractionResult || !analysisResult) return <LoadingScreen />;

  if (route === "#report") {
    return (
      <AuditReport
        extractionResult={extractionResult}
        analysisResult={analysisResult}
        onBack={() => { window.location.hash = ""; }}
      />
    );
  }

  if (route === "#ledger") {
    return (
      <LedgerView
        extractionResult={extractionResult}
        analysisResult={analysisResult}
        onBack={() => { window.location.hash = ""; }}
      />
    );
  }

  if (route === "#integrity") {
    return (
      <>
        <IntegrityChecksView
          extractionResult={extractionResult}
          analysisResult={analysisResult}
          onBack={() => { window.location.hash = ""; }}
          onOpenEvidence={(findingId) => {
            const found = (analysisResult.findings || []).find(f => f.id === findingId);
            if (found) setSelectedFindingForEvidence(found);
          }}
          onAskAI={(findingId) => {
            setShowGlobalAI(true);
          }}
        />
        {selectedFindingForEvidence && (
          <EvidencePanel
            documentId={documentId}
            finding={selectedFindingForEvidence}
            onClose={() => setSelectedFindingForEvidence(null)}
          />
        )}
      </>
    );
  }

  if (route === "#wp514") {
    return (
      <div style={{ background: "var(--bg-main)", minHeight: "100vh", padding: "32px 40px", maxWidth: 1200, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <button
            onClick={() => { window.location.hash = ""; }}
            className="fd-btn fd-btn-outline"
            style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: "13px", fontWeight: 600 }}
          >
            <ArrowLeft size={15} /> Back to Dashboard
          </button>
          <button
            onClick={() => { window.location.hash = "#report"; }}
            className="fd-btn fd-btn-primary"
            style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: "13px", fontWeight: 600 }}
          >
            <FileText size={15} /> View Audit Report
          </button>
        </div>
        <WP514ReviewMatrix
          wp514Data={analysisResult.wp514}
          searchQuery={searchQuery}
          onOpenEvidence={(findingId) => {
            const found = (analysisResult.findings || []).find(f => f.id === findingId);
            if (found) setSelectedFindingForEvidence(found);
          }}
        />
        {selectedFindingForEvidence && (
          <EvidencePanel
            documentId={documentId}
            finding={selectedFindingForEvidence}
            onClose={() => setSelectedFindingForEvidence(null)}
          />
        )}
      </div>
    );
  }

  // ── Derived display values (READ from API — never calculated here) ──────────
  const fm = analysisResult.financial_metrics || {};
  const fs = analysisResult.findings_summary || {};
  const dq = extractionResult.document_quality || {};
  const currentPeriod = extractionResult.period?.current || "";
  const previousPeriod = extractionResult.period?.previous || "";

  const q = (searchQuery || "").trim().toLowerCase();
  const filteredFindings = (analysisResult.findings || []).filter(f => {
    const matchFilter =
      findingFilter === "ALL" ||
      (findingFilter === "CRITICAL" && (f.severity === "CRITICAL" || f.severity === "HIGH")) ||
      f.severity === findingFilter;
    if (!matchFilter) return false;

    if (!q) return true;
    return (
      (f.title || "").toLowerCase().includes(q) ||
      (f.category || "").toLowerCase().includes(q) ||
      (f.description || "").toLowerCase().includes(q) ||
      (f.explanation || "").toLowerCase().includes(q) ||
      (f.severity || "").toLowerCase().includes(q) ||
      (f.id || "").toLowerCase().includes(q) ||
      (f.finding_id || "").toLowerCase().includes(q) ||
      (f.recommendation || "").toLowerCase().includes(q) ||
      (f.impact || "").toLowerCase().includes(q) ||
      (f.source?.note_ref || "").toLowerCase().includes(q) ||
      (f.source?.raw_label || "").toLowerCase().includes(q)
    );
  });

  const activeMetricData = fm[chartMetric] || {};
  const isChartDataMissing = activeMetricData.current == null && activeMetricData.previous == null;

  const areaData = [
    { name: previousPeriod || "Prior", value: activeMetricData.previous },
    { name: currentPeriod || "Current", value: activeMetricData.current },
  ];

  const donutData = [
    { name: "Critical", value: fs.critical || 0, color: "var(--color-danger)" },
    { name: "High",     value: fs.high || 0,     color: "var(--color-warning)" },
    { name: "Review",   value: fs.review || 0,   color: "var(--color-purple)" },
    { name: "Passed",   value: fs.passed || 0,   color: "var(--color-success)" },
  ].filter(d => d.value > 0);
  const totalFindings = (fs.critical || 0) + (fs.high || 0) + (fs.review || 0) + (fs.passed || 0);

  const ratios = analysisResult.ratios || {};
  const currSymbol = extractionResult.currency === "INR" ? "₹" : (extractionResult.currency === "USD" ? "$" : (extractionResult.currency ? `${extractionResult.currency} ` : ""));

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg-main)", overflowX: "hidden" }}>
      {/* ── SIDEBAR ── */}
      <aside className="fd-sidebar" style={{ width: "260px", background: "var(--bg-sidebar)", display: "flex", flexDirection: "column", borderRight: "1px solid var(--border-light)", flexShrink: 0, position: "sticky", top: 0, height: "100vh" }}>
        <div style={{ padding: "28px 24px", display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: "var(--color-primary-soft)", color: "var(--color-primary)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Activity size={22} strokeWidth={2.5} />
          </div>
          <div style={{ fontSize: "18px", fontWeight: 800, color: "var(--text-primary)" }}>Finance Analyzer</div>
        </div>

        <nav style={{ padding: "0 16px", display: "flex", flexDirection: "column", gap: "6px", flex: 1 }}>
          {[
            { hash: "", label: "Overview", icon: LayoutDashboard },
            { hash: "#wp514", label: "WP-514 Review", icon: FileCheck2 },
            { hash: "#report", label: "Audit Report", icon: FileText },
            { hash: "#integrity", label: "Integrity Checks", icon: ShieldCheck },
            { hash: "#ledger", label: "Ledger", icon: Layers },
          ].map(({ hash, label, icon: Icon }) => (
            <button key={hash} onClick={() => { window.location.hash = hash; }}
              style={{ display: "flex", alignItems: "center", gap: "14px", padding: "11px 16px", background: route === hash ? "var(--color-primary-soft)" : "transparent", color: route === hash ? "var(--color-primary)" : "var(--text-secondary)", borderRadius: "12px", border: "none", cursor: "pointer", fontWeight: 600, fontSize: "14px", textAlign: "left" }}>
              <Icon size={18} /> {label}
            </button>
          ))}
        </nav>

        <div style={{ padding: "20px 24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
            <div style={{ width: "38px", height: "38px", borderRadius: "50%", background: "var(--color-purple-soft)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--color-purple)", fontWeight: 700 }}>A</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>Auditor</div>
              <div style={{ fontSize: "11px", color: "var(--text-secondary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{extractionResult.file_name}</div>
            </div>
          </div>
          <button onClick={() => { setDocumentId(null); setExtractionResult(null); setAnalysisResult(null); window.location.hash = ""; }}
            className="fd-btn fd-btn-outline" style={{ width: "100%", fontSize: "12px" }}>
            <Upload size={14} /> Upload New Document
          </button>
        </div>
      </aside>

      {/* ── MAIN CONTENT ── */}
      <main className="fd-main" style={{ flex: 1, padding: "32px 36px", minWidth: 0 }}>
        {/* Header */}
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "28px" }}>
          <div>
            <h1 style={{ fontSize: "26px", fontWeight: 700, color: "var(--text-primary)", margin: "0 0 4px" }}>
              {extractionResult.company?.name || extractionResult.file_name || "Financial Statement"}
            </h1>
            <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
              {currentPeriod}{previousPeriod ? ` vs ${previousPeriod}` : ""}{extractionResult.currency ? ` · ${extractionResult.currency}` : ""}{extractionResult.unit ? ` ${extractionResult.unit}` : ""}
            </div>
            <div style={{ display: "flex", gap: "8px", marginTop: "10px", flexWrap: "wrap" }}>
              {dq.data_quality_status && dq.data_quality_status !== "EXCELLENT" && (
                <div className="fd-chip" style={{ background: dq.data_quality_status === "INSUFFICIENT" ? "var(--color-danger-soft)" : "var(--color-warning-soft)", color: dq.data_quality_status === "INSUFFICIENT" ? "var(--color-danger)" : "var(--color-warning)" }}>
                  <AlertTriangle size={12} /> {dq.extraction_completeness_pct}% ({dq.data_quality_status})
                </div>
              )}
              {dq.unit_mismatch_detected && (
                <div className="fd-chip" style={{ background: "var(--color-warning-soft)", color: "var(--color-warning)" }} title={dq.unit_mismatch_detail}>⚠ Unit Mismatch</div>
              )}
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", background: "var(--bg-card)", borderRadius: "24px", padding: "8px 14px", width: "260px", boxShadow: "0 2px 4px rgba(0,0,0,0.02)", border: searchQuery ? "1px solid var(--color-primary)" : "1px solid var(--border-light)", transition: "border 0.2s ease" }}>
              <Search size={15} color={searchQuery ? "var(--color-primary)" : "var(--text-muted)"} />
              <input
                type="text"
                placeholder="Search findings, checks, accounts..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onKeyDown={e => { if (e.key === "Escape") setSearchQuery(""); }}
                style={{ border: "none", outline: "none", fontSize: "13px", color: "var(--text-primary)", width: "100%", background: "transparent" }}
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", padding: "2px", color: "var(--text-muted)" }}
                  title="Clear search"
                >
                  <X size={14} />
                </button>
              )}
            </div>
            <button
              onClick={() => setShowGlobalAI(true)}
              className="fd-btn"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                background: "var(--color-primary-soft)",
                color: "var(--color-primary)",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                padding: "8px 14px",
                borderRadius: "20px",
                fontSize: "12px",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              <Sparkles size={14} /> Ask AI Assistant
            </button>
            <div style={{ width: "42px", height: "42px", borderRadius: "50%", background: "var(--bg-card)", display: "flex", alignItems: "center", justifyContent: "center", position: "relative", cursor: "pointer" }}>
              <Bell size={18} color="var(--text-secondary)" />
              {(fs.critical || 0) > 0 && (
                <div className="animate-pulse-soft" style={{ position: "absolute", top: "10px", right: "11px", width: "8px", height: "8px", background: "var(--color-danger)", borderRadius: "50%", border: "2px solid var(--bg-card)" }} />
              )}
            </div>
          </div>
        </header>

        {/* STAT CARDS */}
        <section className="fd-stat-grid">
          <FinDashStatCard title="Total Revenue" delay="0.1s"
            value={fm.revenue?.current != null ? `${currSymbol}${fmt(fm.revenue.current)}` : "Not available"}
            sub={fm.revenue?.growth_pct != null ? pct(fm.revenue.growth_pct) + " vs prior" : null}
            subColor={fm.revenue?.growth_pct >= 0 ? "var(--color-success)" : "var(--color-danger)"}
            subIcon={fm.revenue?.growth_pct >= 0 ? ArrowUpRight : ArrowDownRight}
            icon={Wallet} iconColor="var(--color-primary)" iconBg="var(--color-primary-soft)"
            isMissing={fm.revenue?.current == null} />
          <FinDashStatCard title="Operating Expenses" delay="0.2s"
            value={fm.expenses?.current != null ? `${currSymbol}${fmt(fm.expenses.current)}` : "Not available"}
            sub={fm.expenses?.growth_pct != null ? pct(fm.expenses.growth_pct) + " vs prior" : null}
            subColor={fm.expenses?.growth_pct <= 0 ? "var(--color-success)" : "var(--color-danger)"}
            subIcon={fm.expenses?.growth_pct <= 0 ? ArrowDownRight : ArrowUpRight}
            icon={ArrowDownRight} iconColor="var(--color-success)" iconBg="var(--color-success-soft)"
            isMissing={fm.expenses?.current == null} />
          <FinDashStatCard title="Net Profit" delay="0.3s"
            value={fm.net_profit?.current != null ? `${currSymbol}${fmt(fm.net_profit.current)}` : "Not available"}
            sub={fm.net_profit?.growth_pct != null ? pct(fm.net_profit.growth_pct) + " vs prior" : null}
            subColor={fm.net_profit?.growth_pct >= 0 ? "var(--color-success)" : "var(--color-danger)"}
            subIcon={fm.net_profit?.growth_pct >= 0 ? ArrowUpRight : ArrowDownRight}
            icon={TrendingUp} iconColor="var(--color-danger)" iconBg="var(--color-danger-soft)"
            isMissing={fm.net_profit?.current == null} />
          <FinDashStatCard title="Overall Score" delay="0.4s"
            value={analysisResult.overall_score != null ? `${Number(analysisResult.overall_score).toFixed(1)} / 100` : "Not available"}
            sub={`${(fs.critical || 0) + (fs.high || 0)} issues need review`}
            subColor="var(--text-secondary)"
            icon={Award} iconColor="var(--color-purple)" iconBg="var(--color-purple-soft)" />
        </section>

        {/* MAIN AREA CHART + RATIOS */}
        <section className="fd-overview-grid">
          <div className="fd-card animate-fade-up" style={{ padding: "24px", animationDelay: "0.5s" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
              <div>
                <h2 style={{ fontSize: "17px", fontWeight: 700, color: "var(--text-primary)", margin: "0 0 12px" }}>Financial Overview</h2>
                <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "6px" }}>Current Period Value</div>
                <div style={{ fontSize: "26px", fontWeight: 800, color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
                  {activeMetricData.current != null ? `${currSymbol}${fmt(activeMetricData.current)}` : "Not available"}
                </div>
                {activeMetricData.growth_pct != null && (
                  <div style={{ display: "inline-flex", alignItems: "center", gap: "4px", marginTop: "8px", color: "var(--color-success)", background: "var(--color-success-soft)", padding: "4px 8px", borderRadius: "12px", fontSize: "12px", fontWeight: 600 }}>
                    <ArrowUpRight size={14} /> {pct(activeMetricData.growth_pct)}
                  </div>
                )}
              </div>
              <select value={chartMetric} onChange={e => setChartMetric(e.target.value)}
                style={{ appearance: "none", background: "var(--bg-main)", border: "1px solid var(--border-light)", borderRadius: "8px", padding: "8px 28px 8px 14px", fontSize: "13px", fontWeight: 600, color: "var(--text-primary)", cursor: "pointer", backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2364748B' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`, backgroundRepeat: "no-repeat", backgroundPosition: "right 8px center" }}>
                <option value="revenue">Revenue</option>
                <option value="expenses">Operating Expenses</option>
                <option value="net_profit">Net Profit</option>
                <option value="operating_profit">Operating Profit</option>
              </select>
            </div>
            <div style={{ height: "240px" }}>
              {isChartDataMissing ? (
                <div style={{ height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: "var(--text-muted)" }}>
                  <AlertCircle size={30} style={{ marginBottom: "10px" }} />
                  <div style={{ fontSize: "13px" }}>Data not available in filing</div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={areaData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "var(--text-secondary)" }} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "var(--text-secondary)" }} tickFormatter={v => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v} />
                    <Tooltip contentStyle={{ borderRadius: "8px", border: "none", boxShadow: "var(--shadow-card)", fontSize: "13px" }} formatter={v => `${currSymbol}${fmt(v)}`} />
                    <Area type="monotone" dataKey="value" stroke="var(--color-primary)" strokeWidth={3} fillOpacity={1} fill="url(#areaGrad)" connectNulls={true} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* RATIOS */}
          <div className="fd-card animate-fade-up" style={{ padding: "24px", animationDelay: "0.6s" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
              <h2 style={{ fontSize: "17px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>Financial Ratios</h2>
              <button onClick={() => { window.location.hash = "#report"; }} style={{ fontSize: "12px", color: "var(--color-primary)", background: "none", border: "none", fontWeight: 600, cursor: "pointer" }}>View All</button>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {[
                { name: "Current Ratio", val: ratios.current_ratio != null ? Number(ratios.current_ratio).toFixed(2) : null, icon: Scale, status: ratios.current_ratio >= 1.5 ? "Healthy" : "Needs Review", color: ratios.current_ratio >= 1.5 ? "#059669" : "#D97706", pct: Math.min(100, (ratios.current_ratio || 0) * 40) },
                { name: "Debt to Equity", val: ratios.debt_to_equity != null ? Number(ratios.debt_to_equity).toFixed(2) : null, icon: Layers, status: ratios.debt_to_equity <= 2 ? "Healthy" : "Elevated", color: ratios.debt_to_equity <= 2 ? "#059669" : "#DC2626", pct: Math.min(100, (ratios.debt_to_equity || 0) * 35) },
                { name: "Net Margin", val: ratios.net_margin_pct != null ? `${Number(ratios.net_margin_pct).toFixed(2)}%` : null, icon: TrendingUp, status: "Profitability", color: "#059669", pct: Math.min(100, Math.max(10, (ratios.net_margin_pct || 0) * 2)) },
                { name: "ROE", val: ratios.roe_pct != null ? `${Number(ratios.roe_pct).toFixed(2)}%` : null, icon: Award, status: "Efficiency", color: "#3B82F6", pct: Math.min(100, Math.max(10, (ratios.roe_pct || 0) * 2)) },
              ].map((r, i) => (
                <div key={i} className="interactive-card" style={{ padding: "10px 12px", background: "var(--bg-main)", borderRadius: "10px", display: "flex", flexDirection: "column", gap: "6px" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <div style={{ width: "26px", height: "26px", borderRadius: "6px", background: "var(--bg-card)", display: "flex", alignItems: "center", justifyContent: "center", color: r.color, flexShrink: 0 }}>
                        <r.icon size={14} />
                      </div>
                      <div>
                        <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>{r.name}</div>
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontSize: "10px", fontWeight: 700, color: r.color, background: "var(--bg-card)", padding: "2px 6px", borderRadius: "4px", border: "1px solid var(--border-light)" }}>
                        {r.status}
                      </span>
                      <span style={{ fontSize: "13px", fontWeight: 800, color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
                        {r.val != null ? r.val : "N/A"}
                      </span>
                    </div>
                  </div>
                  {/* Visual gauge bar */}
                  <div style={{ height: "4px", width: "100%", background: "#E2E8F0", borderRadius: "2px", overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${r.val != null ? r.pct : 0}%`, background: r.color, borderRadius: "2px", transition: "width 0.4s ease" }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* WP-514 REVIEW SECTION */}
        {analysisResult.wp514 && (
          <section className="animate-fade-up" style={{ marginBottom: "28px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <FileCheck2 size={20} color="var(--color-primary)" />
                <h2 style={{ fontSize: "17px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
                  WP-514 Financial Statement Review
                </h2>
              </div>
              <button
                onClick={() => { window.location.hash = "#wp514"; }}
                className="fd-btn fd-btn-outline"
                style={{ fontSize: "12px", padding: "6px 14px" }}
              >
                View Full WP-514 Matrix →
              </button>
            </div>
            <WP514ReviewMatrix
              wp514Data={analysisResult.wp514}
              searchQuery={searchQuery}
              onOpenEvidence={(findingId) => {
                const found = (analysisResult.findings || []).find(f => f.id === findingId);
                if (found) setSelectedFindingForEvidence(found);
              }}
            />
          </section>
        )}

        {/* BOTTOM ROW */}
        <section className="fd-bottom-grid">
          {/* DONUT / FINDINGS BREAKDOWN */}
          <div className="fd-card animate-fade-up hover-scale" style={{ padding: "24px", animationDelay: "0.7s", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <h2 style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>Findings Breakdown</h2>
                <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--color-primary)", background: "var(--color-primary-soft)", padding: "2px 8px", borderRadius: "10px" }}>
                  {totalFindings} Total
                </span>
              </div>
              <div style={{ position: "relative", height: "160px", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div style={{ background: "rgba(15, 23, 42, 0.9)", backdropFilter: "blur(8px)", color: "#FFFFFF", padding: "6px 12px", borderRadius: "8px", fontSize: "12px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)" }}>
                              <div style={{ fontWeight: 700, color: data.color }}>{data.name}</div>
                              <div>{data.value} findings ({totalFindings ? Math.round((data.value / totalFindings) * 100) : 0}%)</div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Pie
                      data={donutData}
                      innerRadius={50}
                      outerRadius={72}
                      paddingAngle={4}
                      cornerRadius={6}
                      dataKey="value"
                      stroke="none"
                      animationDuration={900}
                      animationEasing="ease-out"
                    >
                      {donutData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} style={{ outline: "none", cursor: "pointer" }} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ position: "absolute", textAlign: "center", pointerEvents: "none" }}>
                  <div style={{ fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", fontWeight: 600 }}>Total</div>
                  <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.1 }}>{totalFindings}</div>
                </div>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "14px" }}>
              {donutData.map(d => {
                const isSelected = findingFilter === d.name.toUpperCase();
                const itemPct = totalFindings ? Math.round((d.value / totalFindings) * 100) : 0;
                return (
                  <div
                    key={d.name}
                    onClick={() => setFindingFilter(isSelected ? "ALL" : d.name.toUpperCase())}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      fontSize: "12px",
                      padding: "6px 10px",
                      borderRadius: "8px",
                      background: isSelected ? `${d.color}15` : "var(--bg-main)",
                      border: `1px solid ${isSelected ? d.color : "transparent"}`,
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: d.color, marginRight: "8px", boxShadow: `0 0 6px ${d.color}60` }} />
                    <span style={{ color: "var(--text-primary)", fontWeight: 600, flex: 1 }}>{d.name}</span>
                    <span style={{ fontWeight: 700, color: "var(--text-primary)", marginRight: "8px" }}>{d.value}</span>
                    <span style={{ color: "var(--text-muted)", fontSize: "11px", minWidth: "32px", textAlign: "right" }}>{itemPct}%</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* AUDIT INTEGRITY */}
          <div className="fd-card animate-fade-up hover-scale" style={{ padding: "24px", animationDelay: "0.8s", display: "flex", flexDirection: "column" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <ShieldCheck size={18} color="var(--color-primary)" />
                <h2 style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>Audit Integrity</h2>
              </div>
              <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--color-success)", background: "var(--color-success-soft)", padding: "2px 8px", borderRadius: "10px", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "var(--color-success)" }} />
                10 Controls
              </span>
            </div>

            <div style={{ flex: 1, overflowY: "auto", maxHeight: "330px", paddingRight: "4px", display: "flex", flexDirection: "column", gap: "4px" }}>
              {Object.entries(analysisResult.checks || {}).filter(([, v]) => v != null).map(([key, val]) => {
                const score = Number(val);
                const isNA = val === "NOT_AVAILABLE" || (key === "related_disclosure" && score === 0);
                const cfg = INTEGRITY_CONFIG[key] || { name: key.replace(/_/g, " "), Icon: Activity };
                const Icon = cfg.Icon;
                
                const gradColor = isNA
                  ? "#94A3B8"
                  : score >= 80
                  ? "linear-gradient(90deg, #10B981, #059669)"
                  : score >= 60
                  ? "linear-gradient(90deg, #F59E0B, #D97706)"
                  : "linear-gradient(90deg, #EF4444, #DC2626)";
                
                const badgeColor = isNA
                  ? "var(--text-muted)"
                  : score >= 80
                  ? "var(--color-success)"
                  : score >= 60
                  ? "var(--color-warning)"
                  : "var(--color-danger)";

                return (
                  <div key={key} className="integrity-item-row">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <div style={{ width: "20px", height: "20px", borderRadius: "4px", background: "var(--bg-main)", display: "flex", alignItems: "center", justifyContent: "center", color: isNA ? "var(--text-muted)" : "var(--color-primary)", flexShrink: 0 }}>
                          <Icon size={12} />
                        </div>
                        <span style={{ color: isNA ? "var(--text-secondary)" : "var(--text-primary)", fontWeight: 600 }}>
                          {cfg.name}
                        </span>
                      </div>
                      <span style={{ color: badgeColor, fontWeight: 700, fontSize: "11px" }}>
                        {isNA ? "N/A" : `${score.toFixed(0)}%`}
                      </span>
                    </div>

                    <div style={{ height: "6px", background: "var(--bg-main)", borderRadius: "999px", overflow: "hidden" }}>
                      {!isNA && (
                        <div
                          className="animated-progress-fill"
                          style={{
                            width: `${Math.min(100, score)}%`,
                            background: gradColor,
                          }}
                        />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* FINDINGS LIST */}
          <div className="fd-card animate-fade-up" style={{ padding: "24px", display: "flex", flexDirection: "column", animationDelay: "0.9s" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>Recent Findings</h2>
                <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-muted)", background: "var(--bg-main)", padding: "1px 6px", borderRadius: "6px" }}>
                  {filteredFindings.length}
                </span>
              </div>
              <button onClick={() => { window.location.hash = "#report"; }} style={{ fontSize: "12px", color: "var(--color-primary)", background: "none", border: "none", fontWeight: 600, cursor: "pointer", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                View All <ArrowUpRight size={13} />
              </button>
            </div>

            {/* Quick Severity Filter Pills */}
            <div style={{ display: "flex", gap: "6px", marginBottom: "14px", flexWrap: "wrap" }}>
              {["ALL", "CRITICAL", "REVIEW", "PASSED"].map((flt) => {
                const count = flt === "ALL"
                  ? (analysisResult.findings || []).length
                  : flt === "CRITICAL"
                  ? (analysisResult.findings || []).filter(f => f.severity === "CRITICAL" || f.severity === "HIGH").length
                  : (analysisResult.findings || []).filter(f => f.severity === flt).length;
                return (
                  <button
                    key={flt}
                    onClick={() => setFindingFilter(flt)}
                    className={`filter-tab-pill ${findingFilter === flt ? "active" : ""}`}
                  >
                    {flt === "ALL" ? "All" : flt.charAt(0) + flt.slice(1).toLowerCase()}
                    <span style={{ opacity: 0.75, fontSize: "10px" }}>({count})</span>
                  </button>
                );
              })}
            </div>

            <div style={{ flex: 1, overflowY: "auto", maxHeight: "310px", paddingRight: "4px" }}>
              {filteredFindings.length === 0 ? (
                <div style={{ padding: "40px 0", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
                  <ShieldCheck size={32} style={{ margin: "0 auto 10px", opacity: 0.4 }} />
                  <div>{searchQuery ? "No findings match your search." : "No findings match active filter."}</div>
                  {findingFilter !== "ALL" && (
                    <button onClick={() => setFindingFilter("ALL")} style={{ marginTop: "8px", background: "none", border: "none", color: "var(--color-primary)", fontSize: "12px", fontWeight: 600, cursor: "pointer" }}>
                      Reset filter
                    </button>
                  )}
                </div>
              ) : (
                filteredFindings.map(f => (
                  <FinDashFindingItem key={f.id} f={f} documentId={documentId} />
                ))
              )}
            </div>
          </div>
        </section>
      </main>

      {showGlobalAI && (
        <AskAIPanel
          documentId={documentId}
          onClose={() => setShowGlobalAI(false)}
        />
      )}
    </div>
  );
}
