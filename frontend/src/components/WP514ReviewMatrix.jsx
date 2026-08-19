import React, { useState } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  ChevronRight,
  ExternalLink,
  Filter,
  Layers,
  FileCheck2,
  Scale,
  Calendar,
  Building,
  FileSpreadsheet,
  Calculator,
  TrendingUp,
  Coins,
  Repeat,
  FileSearch,
  CheckCircle2,
  Activity,
  Percent,
  Sliders,
  SpellCheck
} from "lucide-react";

/* ────────────────────────────────────────────────────────────
   STATUS HELPERS
   ──────────────────────────────────────────────────────────── */
const STATUS_CONFIG = {
  PASSED: {
    label: "PASSED",
    bg: "rgba(16, 185, 129, 0.12)",
    color: "#059669",
    border: "rgba(16, 185, 129, 0.3)",
    Icon: ShieldCheck,
  },
  REVIEW: {
    label: "REVIEW",
    bg: "rgba(245, 158, 11, 0.12)",
    color: "#d97706",
    border: "rgba(245, 158, 11, 0.3)",
    Icon: AlertTriangle,
  },
  WARNING: {
    label: "REVIEW",
    bg: "rgba(245, 158, 11, 0.12)",
    color: "#d97706",
    border: "rgba(245, 158, 11, 0.3)",
    Icon: AlertTriangle,
  },
  FAILED: {
    label: "FAILED",
    bg: "rgba(239, 68, 68, 0.12)",
    color: "#dc2626",
    border: "rgba(239, 68, 68, 0.3)",
    Icon: AlertOctagon,
  },
  NOT_AVAILABLE: {
    label: "NOT AVAILABLE",
    bg: "rgba(100, 116, 139, 0.08)",
    color: "#64748b",
    border: "rgba(100, 116, 139, 0.2)",
    Icon: HelpCircle,
  },
};

function getCategoryDisplayStatus(cat) {
  if (!cat) return "PASSED";
  if (cat.failed_checks > 0) return "FAILED";
  if (cat.review_checks > 0) return "REVIEW";
  if (cat.passed_checks > 0 && cat.failed_checks === 0 && cat.review_checks === 0) return "PASSED";
  if (cat.score !== null && cat.score !== undefined && cat.score >= 80) return "PASSED";
  if (cat.status && cat.status !== "NOT_AVAILABLE" && cat.status !== "COMPUTED") return cat.status;
  return "PASSED";
}

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.NOT_AVAILABLE;
  const Icon = cfg.Icon;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: "3px 8px",
        borderRadius: "6px",
        fontSize: "11px",
        fontWeight: 600,
        letterSpacing: "0.03em",
        background: cfg.bg,
        color: cfg.color,
        border: `1px solid ${cfg.border}`,
        whiteSpace: "nowrap",
      }}
    >
      <Icon size={12} />
      {cfg.label}
    </span>
  );
}

function getCategoryIcon(catId, catName) {
  const c = `${catId || ""} ${catName || ""}`.toLowerCase();
  if (c.includes("math") || c.includes("accuracy")) return Calculator;
  if (c.includes("cash") || c.includes("flow")) return Coins;
  if (c.includes("prior") || c.includes("tie")) return Repeat;
  if (c.includes("consistency") || c.includes("internal")) return Layers;
  if (c.includes("comparison") || c.includes("analytical")) return Activity;
  if (c.includes("ratio") || c.includes("key")) return Percent;
  if (c.includes("fluctuation") || c.includes("unusual")) return TrendingUp;
  if (c.includes("gain") || c.includes("loss")) return Scale;
  if (c.includes("related") || c.includes("party")) return FileSearch;
  if (c.includes("language") || c.includes("spelling") || c.includes("grammar")) return SpellCheck;
  return FileCheck2;
}

export default function WP514ReviewMatrix({ wp514Data, searchQuery = "", onOpenEvidence, appendixMode = false }) {
  if (!wp514Data) {
    return (
      <div className="fd-card" style={{ padding: "32px", textAlign: "center", color: "var(--text-secondary)" }}>
        No WP-514 Review data available.
      </div>
    );
  }

  const {
    title = "WP-514 Financial Statement Review",
    subtitle = "Standardized Financial Statement Review Matrix",
    document_information: docInfo = {},
    categories = [],
    checks = [],
    overall = {},
  } = wp514Data;

  const [selectedCatId, setSelectedCatId] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  // Default all expanded when in appendixMode so no audit checks are hidden
  const [expandedCategories, setExpandedCategories] = useState(() => {
    if (appendixMode) {
      const all = {};
      categories.forEach((c) => {
        all[c.id] = true;
      });
      return all;
    }
    return {};
  });

  const toggleCategory = (catId) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [catId]: !prev[catId],
    }));
  };

  const expandAllCategories = () => {
    const all = {};
    categories.forEach((c) => {
      all[c.id] = true;
    });
    setExpandedCategories(all);
  };

  const collapseAllCategories = () => {
    setExpandedCategories({});
  };

  const q = (searchQuery || "").trim().toLowerCase();

  // Filter checks by category, status, and search query
  const filteredChecks = checks.filter((c) => {
    const matchCat = selectedCatId === "ALL" || c.category === selectedCatId;
    const matchStatus =
      statusFilter === "ALL" ||
      (statusFilter === "REVIEW" && (c.status === "REVIEW" || c.status === "WARNING")) ||
      c.status === statusFilter;
    if (!matchCat || !matchStatus) return false;
    if (!q) return true;

    return (
      (c.check || "").toLowerCase().includes(q) ||
      (c.id || "").toLowerCase().includes(q) ||
      (c.category || "").toLowerCase().includes(q) ||
      (c.status || "").toLowerCase().includes(q) ||
      (c.evidence || "").toLowerCase().includes(q) ||
      (c.actual_value || "").toLowerCase().includes(q) ||
      (c.expected_value || "").toLowerCase().includes(q) ||
      (c.threshold || "").toLowerCase().includes(q) ||
      (c.difference || "").toLowerCase().includes(q)
    );
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* ────────────────────────────────────────────────────────────
          1. HEADER & DOCUMENT INFORMATION - HIGHLIGHTED HERO
          (suppressed in appendixMode — already shown in executive summary)
          ──────────────────────────────────────────────────────────── */}
      {!appendixMode && (
      <div
        className="fd-card animate-fade-up"
        style={{
          padding: "26px 28px",
          background: "linear-gradient(135deg, rgba(236, 253, 245, 0.85) 0%, #FFFFFF 50%, rgba(240, 253, 244, 0.7) 100%)",
          borderLeft: "6px solid var(--color-primary)",
          borderTop: "1px solid rgba(16, 185, 129, 0.25)",
          borderRight: "1px solid rgba(16, 185, 129, 0.2)",
          borderBottom: "1px solid rgba(16, 185, 129, 0.2)",
          boxShadow: "0 8px 24px -4px rgba(16, 185, 129, 0.12), 0 2px 6px rgba(0, 0, 0, 0.02)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
              <span
                style={{
                  background: "linear-gradient(135deg, #059669 0%, #10B981 100%)",
                  color: "#FFFFFF",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontWeight: 800,
                  letterSpacing: "0.06em",
                  boxShadow: "0 2px 6px rgba(16, 185, 129, 0.3)",
                }}
              >
                WP-514 WORKPAPER
              </span>
              <span style={{ fontSize: "12px", color: "var(--text-muted)", fontWeight: 600 }}>
                Engine v{docInfo.engine_version || "2.0.0"}
              </span>
            </div>
            <h2 style={{ fontSize: "22px", fontWeight: 800, color: "var(--text-primary)", margin: "0 0 4px 0" }}>
              {title}
            </h2>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: 0, fontWeight: 500 }}>
              {subtitle} • Grounded against verified document extractions and financial checks.
            </p>
          </div>

          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <div className="wp514-score-box">
              <div style={{ fontSize: "10px", color: "var(--text-secondary)", fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase" }}>
                Overall Compliance Score
              </div>
              <div style={{ fontSize: "26px", fontWeight: 800, color: "var(--color-primary)", lineHeight: 1.1, marginTop: "2px" }}>
                {overall.score?.toFixed(1) ?? "0.0"}
                <span style={{ fontSize: "14px", fontWeight: 500, color: "var(--text-muted)" }}> / 100</span>
              </div>
            </div>
          </div>
        </div>

        {/* Metadata Badges */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "12px",
            marginTop: "20px",
            paddingTop: "18px",
            borderTop: "1px solid rgba(16, 185, 129, 0.15)",
          }}
        >
          <div className="wp514-meta-card">
            <div style={{ width: "30px", height: "30px", borderRadius: "6px", background: "var(--color-primary-soft)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <Building size={16} color="var(--color-primary)" />
            </div>
            <div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Entity</div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                {docInfo.company_name || "Not available"}
              </div>
            </div>
          </div>

          <div className="wp514-meta-card">
            <div style={{ width: "30px", height: "30px", borderRadius: "6px", background: "var(--color-primary-soft)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <Calendar size={16} color="var(--color-primary)" />
            </div>
            <div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Period / FY</div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                {docInfo.reporting_period || docInfo.financial_year || "Not available"}
              </div>
            </div>
          </div>

          <div className="wp514-meta-card">
            <div style={{ width: "30px", height: "30px", borderRadius: "6px", background: "var(--color-primary-soft)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <Scale size={16} color="var(--color-primary)" />
            </div>
            <div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Unit & Scale</div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                {docInfo.currency && docInfo.scale ? `${docInfo.currency} in ${docInfo.scale}` : (docInfo.currency || docInfo.scale || "Not available")}
                {docInfo.statement_type ? ` (${docInfo.statement_type})` : ""}
              </div>
            </div>
          </div>

          <div className="wp514-meta-card">
            <div style={{ width: "30px", height: "30px", borderRadius: "6px", background: "var(--color-primary-soft)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <FileSpreadsheet size={16} color="var(--color-primary)" />
            </div>
            <div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Framework</div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                {docInfo.reporting_framework || "Not available"}
              </div>
            </div>
          </div>
        </div>
      </div>
      )}

      {/* ────────────────────────────────────────────────────────────
          2. EXECUTIVE SUMMARY METRICS WITH VISUAL ICONS
          (suppressed in appendixMode — already shown on page 1)
          ──────────────────────────────────────────────────────────── */}
      {!appendixMode && (
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          gap: "14px",
        }}
      >
        <div className="fd-card interactive-card hover-scale" style={{ padding: "16px 18px", display: "flex", alignItems: "center", gap: "14px", background: "#FFFFFF", borderTop: "3px solid #64748b" }}>
          <div style={{ width: "42px", height: "42px", borderRadius: "10px", background: "var(--bg-secondary)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <Layers size={20} color="var(--text-primary)" />
          </div>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", letterSpacing: "0.04em" }}>TOTAL CHECKS</div>
            <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--text-primary)", marginTop: "2px" }}>
              {overall.total_checks ?? checks.length}
            </div>
          </div>
        </div>

        <div className="fd-card interactive-card hover-scale" style={{ padding: "16px 18px", display: "flex", alignItems: "center", gap: "14px", background: "#FFFFFF", borderTop: "3px solid #10b981", boxShadow: "0 2px 8px rgba(16, 185, 129, 0.08)" }}>
          <div style={{ width: "42px", height: "42px", borderRadius: "10px", background: "rgba(16, 185, 129, 0.12)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <CheckCircle2 size={20} color="#059669" />
          </div>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "#059669", letterSpacing: "0.04em" }}>PASSED</div>
            <div style={{ fontSize: "22px", fontWeight: 800, color: "#059669", marginTop: "2px" }}>
              {overall.passed ?? 0}
            </div>
          </div>
        </div>

        <div className="fd-card interactive-card hover-scale" style={{ padding: "16px 18px", display: "flex", alignItems: "center", gap: "14px", background: "#FFFFFF", borderTop: "3px solid #f59e0b", boxShadow: "0 2px 8px rgba(245, 158, 11, 0.08)" }}>
          <div style={{ width: "42px", height: "42px", borderRadius: "10px", background: "rgba(245, 158, 11, 0.12)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <AlertTriangle size={20} color="#d97706" />
          </div>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "#d97706", letterSpacing: "0.04em" }}>REVIEW REQUIRED</div>
            <div style={{ fontSize: "22px", fontWeight: 800, color: "#d97706", marginTop: "2px" }}>
              {overall.review ?? 0}
            </div>
          </div>
        </div>

        <div className="fd-card interactive-card hover-scale" style={{ padding: "16px 18px", display: "flex", alignItems: "center", gap: "14px", background: "#FFFFFF", borderTop: "3px solid #ef4444", boxShadow: "0 2px 8px rgba(239, 68, 68, 0.08)" }}>
          <div style={{ width: "42px", height: "42px", borderRadius: "10px", background: "rgba(239, 68, 68, 0.12)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <AlertOctagon size={20} color="#dc2626" />
          </div>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "#dc2626", letterSpacing: "0.04em" }}>FAILED</div>
            <div style={{ fontSize: "22px", fontWeight: 800, color: "#dc2626", marginTop: "2px" }}>
              {overall.failed ?? 0}
            </div>
          </div>
        </div>

        <div className="fd-card interactive-card hover-scale" style={{ padding: "16px 18px", display: "flex", alignItems: "center", gap: "14px", background: "#FFFFFF", borderTop: "3px solid #64748b" }}>
          <div style={{ width: "42px", height: "42px", borderRadius: "10px", background: "rgba(100, 116, 139, 0.08)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <HelpCircle size={20} color="#64748b" />
          </div>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", letterSpacing: "0.04em" }}>NOT IN FILING</div>
            <div style={{ fontSize: "22px", fontWeight: 800, color: "#64748b", marginTop: "2px" }}>
              {overall.not_available ?? 0}
            </div>
          </div>
        </div>
      </div>
      )}

      {/* ────────────────────────────────────────────────────────────
          3. CATEGORIES OVERVIEW GRID WITH SHOW MORE / LESS OPTION
          (suppressed in appendixMode — category scores shown in Integrity Scorecard on page 2)
          ──────────────────────────────────────────────────────────── */}
      {!appendixMode && (
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <h3 style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
              WP-514 Audit Review Categories
            </h3>
            <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: "2px 0 0" }}>
              Click any category card to filter and highlight check details below.
            </p>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))",
            gap: "14px",
          }}
        >
          {categories.map((cat) => {
            const isSelected = selectedCatId === cat.id;
            const CatIcon = getCategoryIcon(cat.id, cat.name);
            const catScore = cat.score ?? 100;
            const scoreColor = catScore >= 80 ? "#059669" : catScore >= 60 ? "#D97706" : "#DC2626";

            return (
              <div
                key={cat.id}
                onClick={() => setSelectedCatId((prev) => (prev === cat.id ? "ALL" : cat.id))}
                className="fd-card interactive-card animate-fade-in"
                style={{
                  padding: "16px",
                  cursor: "pointer",
                  border: isSelected ? "2px solid var(--color-primary)" : "1px solid var(--border-subtle)",
                  background: isSelected ? "rgba(16, 185, 129, 0.05)" : "var(--bg-card)",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "12px",
                  boxShadow: isSelected ? "0 4px 14px rgba(16, 185, 129, 0.15)" : "0 1px 3px rgba(0,0,0,0.03)",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div
                        style={{
                          width: "34px",
                          height: "34px",
                          borderRadius: "8px",
                          background: isSelected ? "var(--color-primary-soft)" : "rgba(16, 185, 129, 0.08)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          flexShrink: 0,
                        }}
                      >
                        <CatIcon size={18} color={isSelected ? "var(--color-primary)" : "#059669"} />
                      </div>
                      <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.3 }}>
                        {cat.name}
                      </div>
                    </div>
                    <StatusBadge status={getCategoryDisplayStatus(cat)} />
                  </div>

                  {/* Visual Category Score Bar */}
                  {cat.score !== null && cat.score !== undefined && (
                    <div style={{ marginTop: "12px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                        <span style={{ color: "var(--text-secondary)", fontWeight: 500 }}>Category Score</span>
                        <strong style={{ color: scoreColor }}>{cat.score.toFixed(0)} / 100</strong>
                      </div>
                      <div style={{ height: "4px", width: "100%", background: "#F1F5F9", borderRadius: "2px", overflow: "hidden" }}>
                        <div
                          style={{
                            height: "100%",
                            width: `${Math.min(100, Math.max(0, cat.score))}%`,
                            background: scoreColor,
                            transition: "width 0.3s ease",
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "11px",
                    color: "var(--text-muted)",
                    paddingTop: "8px",
                    borderTop: "1px dashed var(--border-subtle)",
                  }}
                >
                  <span style={{ fontWeight: 600, color: "var(--text-secondary)" }}>{cat.total_checks} verification checks</span>
                  <span style={{ fontWeight: 600, color: cat.findings_count > 0 ? "#D97706" : "var(--text-muted)" }}>
                    {cat.findings_count} {cat.findings_count === 1 ? "finding" : "findings"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      )}

      {/* ────────────────────────────────────────────────────────────
          4. SUMMARIZED & COMPACT AUDIT REVIEW CHECKS WITH VIEW MORE
          (always shown, including in appendixMode — granular per-check detail)
          ──────────────────────────────────────────────────────────── */}
      <div className="fd-card animate-fade-up" style={{ padding: "18px 20px" }}>
        {/* Header & Controls */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "12px",
            marginBottom: "14px",
            paddingBottom: "12px",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <h3 style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
                Audit Review Checks Summary
              </h3>
              <span
                style={{
                  fontSize: "10px",
                  fontWeight: 700,
                  padding: "2px 7px",
                  borderRadius: "10px",
                  background: "var(--color-primary-soft)",
                  color: "var(--color-primary)",
                  letterSpacing: "0.03em",
                }}
              >
                Executive Summary
              </span>
            </div>
            <p style={{ fontSize: "11px", color: "var(--text-secondary)", margin: "2px 0 0" }}>
              Categorized compliance checks across WP-514 audit procedures. Click any category to drill down.
            </p>
          </div>

          {/* Quick Actions: Expand/Collapse + Filter Badges */}
          <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" }}>
            <button
              onClick={expandAllCategories}
              style={{
                padding: "4px 8px",
                borderRadius: "6px",
                fontSize: "11px",
                fontWeight: 600,
                background: "var(--bg-secondary)",
                color: "var(--text-primary)",
                border: "1px solid var(--border-subtle)",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              Expand All
            </button>
            <button
              onClick={collapseAllCategories}
              style={{
                padding: "4px 8px",
                borderRadius: "6px",
                fontSize: "11px",
                fontWeight: 600,
                background: "var(--bg-secondary)",
                color: "var(--text-primary)",
                border: "1px solid var(--border-subtle)",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              Collapse All
            </button>

            <div style={{ height: "16px", width: "1px", background: "var(--border-subtle)", margin: "0 2px" }} />

            {["ALL", "REVIEW", "FAILED", "PASSED", "NOT_AVAILABLE"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                style={{
                  padding: "4px 8px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontWeight: statusFilter === st ? 700 : 500,
                  background: statusFilter === st ? "var(--color-primary)" : "var(--bg-secondary)",
                  color: statusFilter === st ? "white" : "var(--text-secondary)",
                  border: "none",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {st === "ALL" ? "All Checks" : st === "REVIEW" ? "Review Required" : st === "NOT_AVAILABLE" ? "Not in Filing" : st}
              </button>
            ))}
          </div>
        </div>

        {/* Compact Executive Summary Meter / Segmented Progress Bar */}
        {(() => {
          const totalAll = checks.length || 1;
          const passTotal = checks.filter((c) => c.status === "PASSED").length;
          const revTotal = checks.filter((c) => c.status === "REVIEW" || c.status === "WARNING").length;
          const failTotal = checks.filter((c) => c.status === "FAILED").length;
          const naTotal = checks.filter((c) => c.status === "NOT_AVAILABLE").length;

          const passPct = (passTotal / totalAll) * 100;
          const revPct = (revTotal / totalAll) * 100;
          const failPct = (failTotal / totalAll) * 100;
          const naPct = (naTotal / totalAll) * 100;

          return (
            <div
              style={{
                background: "linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%)",
                borderRadius: "8px",
                padding: "10px 14px",
                marginBottom: "14px",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px", flexWrap: "wrap", gap: "6px" }}>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-primary)" }}>
                  Overall Checks Distribution
                </span>
                <span style={{ fontSize: "11px", fontWeight: 600, color: passTotal === totalAll ? "#059669" : "#D97706" }}>
                  {passTotal} Passed ({passPct.toFixed(0)}%) • {revTotal + failTotal} Attention Items
                </span>
              </div>

              {/* Segmented Progress Bar */}
              <div
                style={{
                  display: "flex",
                  height: "6px",
                  borderRadius: "9999px",
                  overflow: "hidden",
                  background: "#E2E8F0",
                  boxShadow: "inset 0 1px 2px rgba(0,0,0,0.06)",
                }}
              >
                {passPct > 0 && (
                  <div
                    style={{
                      width: `${passPct}%`,
                      background: "linear-gradient(90deg, #10B981, #059669)",
                      transition: "width 0.4s ease",
                    }}
                    title={`Passed: ${passTotal}`}
                  />
                )}
                {revPct > 0 && (
                  <div
                    style={{
                      width: `${revPct}%`,
                      background: "linear-gradient(90deg, #F59E0B, #D97706)",
                      transition: "width 0.4s ease",
                    }}
                    title={`Review Required: ${revTotal}`}
                  />
                )}
                {failPct > 0 && (
                  <div
                    style={{
                      width: `${failPct}%`,
                      background: "linear-gradient(90deg, #EF4444, #DC2626)",
                      transition: "width 0.4s ease",
                    }}
                    title={`Failed: ${failTotal}`}
                  />
                )}
                {naPct > 0 && (
                  <div
                    style={{
                      width: `${naPct}%`,
                      background: "#94A3B8",
                      transition: "width 0.4s ease",
                    }}
                    title={`Not in Filing: ${naTotal}`}
                  />
                )}
              </div>

              {/* Legend Badges */}
              <div style={{ display: "flex", gap: "12px", marginTop: "8px", flexWrap: "wrap", fontSize: "10px" }}>
                <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "#059669", fontWeight: 600 }}>
                  <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#10B981" }} />
                  {passTotal} Passed ({passPct.toFixed(0)}%)
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "#D97706", fontWeight: 600 }}>
                  <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#F59E0B" }} />
                  {revTotal} Review Required ({revPct.toFixed(0)}%)
                </span>
                {failTotal > 0 && (
                  <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "#DC2626", fontWeight: 600 }}>
                    <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#EF4444" }} />
                    {failTotal} Failed ({failPct.toFixed(0)}%)
                  </span>
                )}
                {naTotal > 0 && (
                  <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "#64748B", fontWeight: 500 }}>
                    <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#94A3B8" }} />
                    {naTotal} Not in Filing ({naPct.toFixed(0)}%)
                  </span>
                )}
              </div>
            </div>
          );
        })()}

        {filteredChecks.length === 0 ? (
          <div style={{ padding: "24px", textAlign: "center", color: "var(--text-muted)", fontSize: "12px" }}>
            No checks match the active filter criteria.
          </div>
        ) : (
          (() => {
            const availableCategories = categories.filter((cat) => {
              const catChecks = filteredChecks.filter((c) => c.category === cat.id);
              return (selectedCatId === "ALL" || cat.id === selectedCatId) && catChecks.length > 0;
            });

            const displayedCategories = availableCategories;

            return (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {displayedCategories.map((cat) => {
                  const catChecks = filteredChecks.filter((c) => c.category === cat.id);
                  if (catChecks.length === 0) return null;

                  const passedCount = catChecks.filter((c) => c.status === "PASSED").length;
                  const reviewCount = catChecks.filter((c) => c.status === "REVIEW" || c.status === "WARNING").length;
                  const failedCount = catChecks.filter((c) => c.status === "FAILED").length;
                  const notAvailCount = catChecks.filter((c) => c.status === "NOT_AVAILABLE").length;
                  const isExpanded = appendixMode || q ? true : Boolean(expandedCategories[cat.id]);
                  const passRate = catChecks.length > 0 ? (passedCount / catChecks.length) * 100 : 0;

                  return (
                    <div
                      key={cat.id}
                      className="interactive-card animate-fade-in"
                      style={{
                        border: isExpanded ? "1px solid rgba(16, 185, 129, 0.4)" : "1px solid var(--border-subtle)",
                        borderRadius: "8px",
                        overflow: "hidden",
                        background: "var(--bg-card)",
                        boxShadow: isExpanded ? "0 4px 10px rgba(0, 0, 0, 0.03)" : "0 1px 2px rgba(0,0,0,0.02)",
                      }}
                    >
                      {/* Category Summary Card Header (Click to Expand / Collapse) */}
                      <div
                        onClick={() => toggleCategory(cat.id)}
                        style={{
                          padding: "10px 14px",
                          background: isExpanded
                            ? "linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, #FFFFFF 100%)"
                            : "var(--bg-card)",
                          cursor: "pointer",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          flexWrap: "wrap",
                          gap: "8px",
                          borderBottom: isExpanded ? "1px solid var(--border-subtle)" : "none",
                          transition: "background 0.2s ease",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1, minWidth: "220px" }}>
                          <div
                            style={{
                              width: "24px",
                              height: "24px",
                              borderRadius: "6px",
                              background: isExpanded ? "var(--color-primary-soft)" : "var(--bg-secondary)",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              transition: "transform 0.25s ease, background 0.2s ease",
                              transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
                            }}
                          >
                            <ChevronRight size={14} color={isExpanded ? "var(--color-primary)" : "var(--text-secondary)"} />
                          </div>
                          <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                              <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                                {cat.name}
                              </span>
                              {cat.score !== null && cat.score !== undefined && (
                                <span style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-primary)", background: "var(--color-primary-soft)", padding: "1px 5px", borderRadius: "4px" }}>
                                  {cat.score.toFixed(0)}/100
                                </span>
                              )}
                            </div>
                            <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "1px" }}>
                              {catChecks.length} checks • {cat.description || "Automated audit procedure"}
                            </div>
                          </div>
                        </div>

                        {/* Micro Progress Bar & Status Badges */}
                        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                          {/* Miniature Category Health Gauge */}
                          <div style={{ display: "flex", flexDirection: "column", gap: "2px", width: "80px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "9px", color: "var(--text-muted)", fontWeight: 600 }}>
                              <span>Pass</span>
                              <span>{passRate.toFixed(0)}%</span>
                            </div>
                            <div style={{ height: "3px", width: "100%", background: "#E2E8F0", borderRadius: "2px", overflow: "hidden" }}>
                              <div
                                style={{
                                  height: "100%",
                                  width: `${passRate}%`,
                                  background: passRate === 100 ? "#10B981" : passRate >= 60 ? "#F59E0B" : "#EF4444",
                                  transition: "width 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
                                }}
                              />
                            </div>
                          </div>

                          {/* Breakdown pills */}
                          <div style={{ display: "flex", gap: "4px", alignItems: "center" }}>
                            {passedCount > 0 && (
                              <span style={{ fontSize: "10px", color: "#059669", background: "rgba(16, 185, 129, 0.1)", padding: "1px 5px", borderRadius: "4px", fontWeight: 600 }}>
                                {passedCount} passed
                              </span>
                            )}
                            {reviewCount > 0 && (
                              <span style={{ fontSize: "10px", color: "#d97706", background: "rgba(245, 158, 11, 0.12)", padding: "1px 5px", borderRadius: "4px", fontWeight: 700 }}>
                                {reviewCount} review
                              </span>
                            )}
                            {failedCount > 0 && (
                              <span style={{ fontSize: "10px", color: "#dc2626", background: "rgba(239, 68, 68, 0.12)", padding: "1px 5px", borderRadius: "4px", fontWeight: 700 }}>
                                {failedCount} failed
                              </span>
                            )}
                            {notAvailCount > 0 && (
                              <span style={{ fontSize: "10px", color: "#64748b", background: "rgba(100, 116, 139, 0.08)", padding: "1px 5px", borderRadius: "4px" }}>
                                {notAvailCount} n/a
                              </span>
                            )}
                            <StatusBadge status={getCategoryDisplayStatus(cat)} />
                          </div>
                        </div>
                      </div>

                      {/* Detailed Checks Sub-table when expanded */}
                      {isExpanded && (
                        <div
                          className="animate-slide-down"
                          style={{
                            overflowX: "auto",
                          }}
                        >
                          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
                            <thead>
                              <tr style={{ background: "rgba(0, 0, 0, 0.02)", textAlign: "left" }}>
                                <th style={{ padding: "6px 10px", fontWeight: 600, color: "var(--text-secondary)", width: "55px" }}>ID</th>
                                <th style={{ padding: "6px 10px", fontWeight: 600, color: "var(--text-secondary)" }}>Check Name</th>
                                <th style={{ padding: "6px 10px", fontWeight: 600, color: "var(--text-secondary)", width: "90px" }}>Status</th>
                                <th style={{ padding: "6px 10px", fontWeight: 600, color: "var(--text-secondary)" }}>Expected / Prior</th>
                                <th style={{ padding: "6px 10px", fontWeight: 600, color: "var(--text-secondary)" }}>Actual / Current</th>
                                <th style={{ padding: "6px 10px", fontWeight: 600, color: "var(--text-secondary)" }}>Variance / Diff</th>
                                <th style={{ padding: "6px 10px", fontWeight: 600, color: "var(--text-secondary)" }}>Threshold</th>
                                <th style={{ padding: "6px 10px", fontWeight: 600, color: "var(--text-secondary)", textAlign: "right" }}>Evidence / Finding</th>
                              </tr>
                            </thead>
                            <tbody>
                              {catChecks.map((chk, i) => {
                                const isEven = i % 2 === 0;
                                return (
                                  <tr
                                    key={chk.id}
                                    style={{
                                      background: isEven ? "transparent" : "rgba(0, 0, 0, 0.015)",
                                      borderBottom: "1px solid var(--border-subtle)",
                                    }}
                                  >
                                    <td style={{ padding: "6px 10px", fontFamily: "monospace", fontSize: "10px", color: "var(--text-muted)" }}>
                                      {chk.id}
                                    </td>
                                    <td style={{ padding: "6px 10px", fontWeight: 600, color: "var(--text-primary)" }}>
                                      <div>{chk.check}</div>
                                      {chk.evidence && (
                                        <div style={{ fontSize: "10px", fontWeight: 400, color: "var(--text-muted)", marginTop: "2px" }}>
                                          {chk.evidence}
                                        </div>
                                      )}
                                    </td>
                                    <td style={{ padding: "6px 10px" }}>
                                      <StatusBadge status={chk.status} />
                                    </td>
                                    <td style={{ padding: "6px 10px", color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
                                      {chk.expected_value || <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>Not available</span>}
                                    </td>
                                    <td style={{ padding: "6px 10px", fontWeight: 600, color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
                                      {chk.actual_value || <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>Not available</span>}
                                    </td>
                                    <td style={{ padding: "6px 10px", color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
                                      {chk.difference || chk.difference_percent || <span style={{ color: "var(--text-muted)" }}>—</span>}
                                    </td>
                                    <td style={{ padding: "6px 10px", fontSize: "10px", color: "var(--text-muted)" }}>
                                      {chk.threshold || "—"}
                                    </td>
                                    <td style={{ padding: "6px 10px", textAlign: "right" }}>
                                      {chk.finding_id ? (
                                        <button
                                          onClick={() => onOpenEvidence && onOpenEvidence(chk.finding_id)}
                                          style={{
                                            display: "inline-flex",
                                            alignItems: "center",
                                            gap: "3px",
                                            padding: "2px 6px",
                                            borderRadius: "4px",
                                            fontSize: "10px",
                                            fontWeight: 600,
                                            background: "rgba(16, 185, 129, 0.1)",
                                            color: "var(--color-primary)",
                                            border: "1px solid rgba(16, 185, 129, 0.3)",
                                            cursor: "pointer",
                                          }}
                                        >
                                          <ExternalLink size={11} />
                                          {chk.finding_id}
                                        </button>
                                      ) : chk.source ? (
                                        <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                                          {chk.source.page != null ? `p.${chk.source.page}` : (chk.source.sheet ? `Sheet: ${chk.source.sheet}` : (chk.source.file || "—"))}
                                        </span>
                                      ) : (
                                        <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>—</span>
                                      )}
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })()
        )}
      </div>
    </div>
  );
}
