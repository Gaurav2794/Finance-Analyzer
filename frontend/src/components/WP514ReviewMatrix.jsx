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

export default function WP514ReviewMatrix({ wp514Data, searchQuery = "", onOpenEvidence }) {
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
  // Default all collapsed for clean, summarized-first executive view
  const [expandedCategories, setExpandedCategories] = useState({});
  const [showAllCategories, setShowAllCategories] = useState(false);

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
          1. EXECUTIVE WORKPAPER BANNER WITH RADIAL COMPLIANCE SEAL
          ──────────────────────────────────────────────────────────── */}
      <div
        className="fd-card animate-fade-up hover-scale"
        style={{
          padding: "26px 30px",
          background: "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)",
          color: "#FFFFFF",
          borderRadius: "16px",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          boxShadow: "0 10px 30px -10px rgba(15, 23, 42, 0.4)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Ambient background glow */}
        <div
          style={{
            position: "absolute",
            top: "-40px",
            right: "-40px",
            width: "220px",
            height: "220px",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(16, 185, 129, 0.25) 0%, rgba(16, 185, 129, 0) 70%)",
            pointerEvents: "none",
          }}
        />

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "20px", position: "relative", zIndex: 1 }}>
          <div style={{ flex: 1, minWidth: "280px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
              <span
                style={{
                  background: "rgba(16, 185, 129, 0.2)",
                  color: "#34D399",
                  padding: "4px 10px",
                  borderRadius: "20px",
                  fontSize: "11px",
                  fontWeight: 800,
                  letterSpacing: "0.06em",
                  border: "1px solid rgba(52, 211, 153, 0.3)",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "5px",
                }}
              >
                <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#34D399", boxShadow: "0 0 8px #34D399" }} />
                WP-514 WORKPAPER
              </span>
              <span style={{ fontSize: "11px", color: "#94A3B8", background: "rgba(255, 255, 255, 0.08)", padding: "3px 8px", borderRadius: "6px" }}>
                Engine v{docInfo.engine_version || "2.0.0"}
              </span>
            </div>

            <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#FFFFFF", margin: "0 0 6px 0", letterSpacing: "-0.02em" }}>
              {title}
            </h2>
            <p style={{ fontSize: "13px", color: "#94A3B8", margin: 0, lineHeight: 1.5 }}>
              Standardized Financial Statement Review Matrix • Grounded against verified document extractions.
            </p>
          </div>

          {/* Radial Compliance Gauge */}
          {(() => {
            const scoreVal = overall.score ?? 0;
            const radius = 34;
            const circumference = 2 * Math.PI * radius;
            const strokeDash = circumference - (Math.min(100, Math.max(0, scoreVal)) / 100) * circumference;
            const ringColor = scoreVal >= 80 ? "#10B981" : scoreVal >= 60 ? "#F59E0B" : "#EF4444";
            const statusText = scoreVal >= 80 ? "CLEAN AUDIT" : scoreVal >= 60 ? "ATTENTION" : "HIGH RISK";

            return (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "16px",
                  background: "rgba(255, 255, 255, 0.05)",
                  padding: "10px 18px",
                  borderRadius: "14px",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  backdropFilter: "blur(8px)",
                }}
              >
                <div style={{ position: "relative", width: "80px", height: "80px", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <svg width="80" height="80" viewBox="0 0 80 80" style={{ transform: "rotate(-90deg)" }}>
                    <circle cx="40" cy="40" r={radius} stroke="rgba(255, 255, 255, 0.1)" strokeWidth="6" fill="none" />
                    <circle
                      cx="40"
                      cy="40"
                      r={radius}
                      stroke={ringColor}
                      strokeWidth="6"
                      strokeDasharray={circumference}
                      strokeDashoffset={strokeDash}
                      strokeLinecap="round"
                      fill="none"
                      style={{ transition: "stroke-dashoffset 0.8s ease" }}
                    />
                  </svg>
                  <div style={{ position: "absolute", textAlign: "center" }}>
                    <span style={{ fontSize: "17px", fontWeight: 800, color: "#FFFFFF", lineHeight: 1 }}>
                      {scoreVal.toFixed(1)}
                    </span>
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "10px", color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 700 }}>
                    Overall Compliance
                  </div>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: ringColor, background: `${ringColor}25`, padding: "2px 8px", borderRadius: "6px", marginTop: "4px", display: "inline-block" }}>
                    {statusText}
                  </div>
                </div>
              </div>
            );
          })()}
        </div>

        {/* Metadata Frosted Pills */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
            gap: "10px",
            marginTop: "20px",
            paddingTop: "16px",
            borderTop: "1px solid rgba(255, 255, 255, 0.1)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px", background: "rgba(255, 255, 255, 0.04)", padding: "8px 12px", borderRadius: "10px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
            <Building size={16} color="#34D399" />
            <div>
              <div style={{ fontSize: "10px", color: "#94A3B8", textTransform: "uppercase" }}>Entity</div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#FFFFFF", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {docInfo.company_name || "Not available"}
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px", background: "rgba(255, 255, 255, 0.04)", padding: "8px 12px", borderRadius: "10px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
            <Calendar size={16} color="#34D399" />
            <div>
              <div style={{ fontSize: "10px", color: "#94A3B8", textTransform: "uppercase" }}>Period / FY</div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#FFFFFF" }}>
                {docInfo.reporting_period || docInfo.financial_year || "Not available"}
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px", background: "rgba(255, 255, 255, 0.04)", padding: "8px 12px", borderRadius: "10px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
            <Scale size={16} color="#34D399" />
            <div>
              <div style={{ fontSize: "10px", color: "#94A3B8", textTransform: "uppercase" }}>Unit & Scale</div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#FFFFFF" }}>
                {docInfo.currency && docInfo.scale ? `${docInfo.currency} in ${docInfo.scale}` : (docInfo.currency || docInfo.scale || "Not available")}
                {docInfo.statement_type ? ` (${docInfo.statement_type})` : ""}
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px", background: "rgba(255, 255, 255, 0.04)", padding: "8px 12px", borderRadius: "10px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
            <FileSpreadsheet size={16} color="#34D399" />
            <div>
              <div style={{ fontSize: "10px", color: "#94A3B8", textTransform: "uppercase" }}>Framework</div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#FFFFFF" }}>
                {docInfo.reporting_framework || "Not available"}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          2. INTERACTIVE EXECUTIVE STATUS STRIP (KPI PILLS)
          ──────────────────────────────────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "12px",
        }}
      >
        <div
          onClick={() => setStatusFilter("ALL")}
          className="fd-card interactive-card hover-scale"
          style={{
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            cursor: "pointer",
            border: statusFilter === "ALL" ? "2px solid var(--color-primary)" : "1px solid var(--border-subtle)",
            background: statusFilter === "ALL" ? "var(--color-primary-soft)" : "var(--bg-card)",
          }}
        >
          <div style={{ width: "38px", height: "38px", borderRadius: "10px", background: "var(--bg-secondary)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <Layers size={18} color="var(--text-primary)" />
          </div>
          <div>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--text-secondary)", letterSpacing: "0.04em" }}>TOTAL CHECKS</div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "var(--text-primary)", marginTop: "1px" }}>
              {overall.total_checks ?? checks.length}
            </div>
          </div>
        </div>

        <div
          onClick={() => setStatusFilter("PASSED")}
          className="fd-card interactive-card hover-scale"
          style={{
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            cursor: "pointer",
            border: statusFilter === "PASSED" ? "2px solid #10B981" : "1px solid var(--border-subtle)",
            background: statusFilter === "PASSED" ? "rgba(16, 185, 129, 0.1)" : "var(--bg-card)",
          }}
        >
          <div style={{ width: "38px", height: "38px", borderRadius: "10px", background: "rgba(16, 185, 129, 0.12)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <CheckCircle2 size={18} color="#059669" />
          </div>
          <div>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "#059669", letterSpacing: "0.04em" }}>PASSED</div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "#059669", marginTop: "1px" }}>
              {overall.passed ?? 0}
            </div>
          </div>
        </div>

        <div
          onClick={() => setStatusFilter("REVIEW")}
          className="fd-card interactive-card hover-scale"
          style={{
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            cursor: "pointer",
            border: statusFilter === "REVIEW" ? "2px solid #F59E0B" : "1px solid var(--border-subtle)",
            background: statusFilter === "REVIEW" ? "rgba(245, 158, 11, 0.1)" : "var(--bg-card)",
          }}
        >
          <div style={{ width: "38px", height: "38px", borderRadius: "10px", background: "rgba(245, 158, 11, 0.12)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <AlertTriangle size={18} color="#D97706" />
          </div>
          <div>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "#D97706", letterSpacing: "0.04em" }}>REVIEW REQUIRED</div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "#D97706", marginTop: "1px" }}>
              {overall.review ?? 0}
            </div>
          </div>
        </div>

        <div
          onClick={() => setStatusFilter("FAILED")}
          className="fd-card interactive-card hover-scale"
          style={{
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            cursor: "pointer",
            border: statusFilter === "FAILED" ? "2px solid #EF4444" : "1px solid var(--border-subtle)",
            background: statusFilter === "FAILED" ? "rgba(239, 68, 68, 0.1)" : "var(--bg-card)",
          }}
        >
          <div style={{ width: "38px", height: "38px", borderRadius: "10px", background: "rgba(239, 68, 68, 0.12)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <AlertOctagon size={18} color="#DC2626" />
          </div>
          <div>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "#DC2626", letterSpacing: "0.04em" }}>FAILED</div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "#DC2626", marginTop: "1px" }}>
              {overall.failed ?? 0}
            </div>
          </div>
        </div>

        <div
          onClick={() => setStatusFilter("NOT_AVAILABLE")}
          className="fd-card interactive-card hover-scale"
          style={{
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            cursor: "pointer",
            border: statusFilter === "NOT_AVAILABLE" ? "2px solid #64748B" : "1px solid var(--border-subtle)",
            background: statusFilter === "NOT_AVAILABLE" ? "rgba(100, 116, 139, 0.1)" : "var(--bg-card)",
          }}
        >
          <div style={{ width: "38px", height: "38px", borderRadius: "10px", background: "rgba(100, 116, 139, 0.08)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <HelpCircle size={18} color="#64748B" />
          </div>
          <div>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "#64748B", letterSpacing: "0.04em" }}>NOT IN FILING</div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "#64748B", marginTop: "1px" }}>
              {overall.not_available ?? 0}
            </div>
          </div>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          3. CATEGORIES OVERVIEW GRID WITH SHOW MORE / LESS OPTION
          ──────────────────────────────────────────────────────────── */}
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
          <button
            onClick={() => setShowAllCategories((prev) => !prev)}
            className="fd-btn fd-btn-outline hover-scale"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 14px",
              fontSize: "12px",
              fontWeight: 600,
              borderRadius: "8px",
              color: "var(--color-primary)",
              borderColor: "var(--color-primary)",
              background: showAllCategories ? "var(--color-primary-soft)" : "transparent",
            }}
          >
            {showAllCategories ? (
              <>
                Show Less <ChevronUp size={15} />
              </>
            ) : (
              <>
                Show More Categories <ChevronDown size={15} />
              </>
            )}
          </button>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))",
            gap: "14px",
          }}
        >
          {(showAllCategories ? categories : categories.slice(0, 3)).map((cat) => {
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
                    <StatusBadge status={cat.status} />
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

          {/* Quick "Show More" expansion card when collapsed */}
          {!showAllCategories && categories.length > 3 && (
            <div
              onClick={() => setShowAllCategories(true)}
              className="fd-card interactive-card hover-scale animate-fade-in"
              style={{
                padding: "20px 16px",
                cursor: "pointer",
                border: "2px dashed var(--border-subtle)",
                background: "rgba(248, 250, 252, 0.7)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                textAlign: "center",
                gap: "8px",
                minHeight: "120px",
              }}
            >
              <div
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "50%",
                  background: "var(--color-primary-soft)",
                  color: "var(--color-primary)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <ChevronDown size={20} />
              </div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                + More Categories
              </div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                Click to view all review procedures
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          4. SUMMARIZED & ANIMATED AUDIT REVIEW CHECKS
          ──────────────────────────────────────────────────────────── */}
      <div className="fd-card animate-fade-up" style={{ padding: "24px" }}>
        {/* Header & Controls */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "16px",
            marginBottom: "18px",
            paddingBottom: "16px",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <h3 style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
                Audit Review Checks Summary ({filteredChecks.length})
              </h3>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  padding: "2px 8px",
                  borderRadius: "12px",
                  background: "var(--color-primary-soft)",
                  color: "var(--color-primary)",
                  letterSpacing: "0.03em",
                }}
              >
                Executive Summary
              </span>
            </div>
            <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: "4px 0 0" }}>
              Categorized compliance checks across 10 WP-514 audit procedures. Click any category to drill down.
            </p>
          </div>

          {/* Quick Actions: Expand/Collapse All + Filter Badges */}
          <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
            <button
              onClick={expandAllCategories}
              style={{
                padding: "5px 10px",
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
                padding: "5px 10px",
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

            <div style={{ height: "18px", width: "1px", background: "var(--border-subtle)", margin: "0 4px" }} />

            {["ALL", "REVIEW", "FAILED", "PASSED", "NOT_AVAILABLE"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                style={{
                  padding: "5px 10px",
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

        {/* Executive Summary Meter / Segmented Progress Bar */}
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
                borderRadius: "10px",
                padding: "14px 18px",
                marginBottom: "20px",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", flexWrap: "wrap", gap: "8px" }}>
                <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-primary)" }}>
                  Overall Checks Distribution ({checks.length} Total Verification Items)
                </span>
                <span style={{ fontSize: "12px", fontWeight: 600, color: passTotal === totalAll ? "#059669" : "#D97706" }}>
                  {passTotal} Passed ({passPct.toFixed(0)}%) • {revTotal + failTotal} Attention Items
                </span>
              </div>

              {/* Segmented Progress Bar */}
              <div
                style={{
                  display: "flex",
                  height: "10px",
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
              <div style={{ display: "flex", gap: "16px", marginTop: "10px", flexWrap: "wrap", fontSize: "11px" }}>
                <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "#059669", fontWeight: 600 }}>
                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10B981" }} />
                  {passTotal} Passed ({passPct.toFixed(0)}%)
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "#D97706", fontWeight: 600 }}>
                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#F59E0B" }} />
                  {revTotal} Review Required ({revPct.toFixed(0)}%)
                </span>
                {failTotal > 0 && (
                  <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "#DC2626", fontWeight: 600 }}>
                    <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#EF4444" }} />
                    {failTotal} Failed ({failPct.toFixed(0)}%)
                  </span>
                )}
                {naTotal > 0 && (
                  <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "#64748B", fontWeight: 500 }}>
                    <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#94A3B8" }} />
                    {naTotal} Not in Filing ({naPct.toFixed(0)}%)
                  </span>
                )}
              </div>
            </div>
          );
        })()}

        {filteredChecks.length === 0 ? (
          <div style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
            No checks match the active filter criteria.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {categories
              .filter((cat) => selectedCatId === "ALL" || cat.id === selectedCatId)
              .map((cat) => {
                const catChecks = filteredChecks.filter((c) => c.category === cat.id);
                if (catChecks.length === 0) return null;

                const passedCount = catChecks.filter((c) => c.status === "PASSED").length;
                const reviewCount = catChecks.filter((c) => c.status === "REVIEW" || c.status === "WARNING").length;
                const failedCount = catChecks.filter((c) => c.status === "FAILED").length;
                const notAvailCount = catChecks.filter((c) => c.status === "NOT_AVAILABLE").length;
                const isExpanded = q ? true : Boolean(expandedCategories[cat.id]);
                const passRate = catChecks.length > 0 ? (passedCount / catChecks.length) * 100 : 0;

                return (
                  <div
                    key={cat.id}
                    className="interactive-card animate-fade-in"
                    style={{
                      border: isExpanded ? "1px solid rgba(16, 185, 129, 0.4)" : "1px solid var(--border-subtle)",
                      borderRadius: "10px",
                      overflow: "hidden",
                      background: "var(--bg-card)",
                      boxShadow: isExpanded ? "0 4px 12px rgba(0, 0, 0, 0.04)" : "0 1px 3px rgba(0,0,0,0.02)",
                    }}
                  >
                    {/* Category Summary Card Header (Click to Expand / Collapse) */}
                    <div
                      onClick={() => toggleCategory(cat.id)}
                      style={{
                        padding: "14px 18px",
                        background: isExpanded
                          ? "linear-gradient(135deg, rgba(16, 185, 129, 0.06) 0%, #FFFFFF 100%)"
                          : "var(--bg-card)",
                        cursor: "pointer",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        flexWrap: "wrap",
                        gap: "12px",
                        borderBottom: isExpanded ? "1px solid var(--border-subtle)" : "none",
                        transition: "background 0.2s ease",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "12px", flex: 1, minWidth: "260px" }}>
                        <div
                          style={{
                            width: "28px",
                            height: "28px",
                            borderRadius: "6px",
                            background: isExpanded ? "var(--color-primary-soft)" : "var(--bg-secondary)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            transition: "transform 0.25s ease, background 0.2s ease",
                            transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
                          }}
                        >
                          <ChevronRight size={16} color={isExpanded ? "var(--color-primary)" : "var(--text-secondary)"} />
                        </div>
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <span style={{ fontSize: "14px", fontWeight: 700, color: "var(--text-primary)" }}>
                              {cat.name}
                            </span>
                            {cat.score !== null && cat.score !== undefined && (
                              <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--color-primary)", background: "var(--color-primary-soft)", padding: "1px 6px", borderRadius: "4px" }}>
                                {cat.score.toFixed(0)}/100
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                            {catChecks.length} checks • {cat.description || "Automated audit procedure"}
                          </div>
                        </div>
                      </div>

                      {/* Micro Progress Bar & Status Badges */}
                      <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
                        {/* Miniature Category Health Gauge */}
                        <div style={{ display: "flex", flexDirection: "column", gap: "3px", width: "100px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "var(--text-muted)", fontWeight: 600 }}>
                            <span>Pass Rate</span>
                            <span>{passRate.toFixed(0)}%</span>
                          </div>
                          <div style={{ height: "4px", width: "100%", background: "#E2E8F0", borderRadius: "2px", overflow: "hidden" }}>
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
                        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                          {passedCount > 0 && (
                            <span style={{ fontSize: "11px", color: "#059669", background: "rgba(16, 185, 129, 0.1)", padding: "2px 6px", borderRadius: "4px", fontWeight: 600 }}>
                              {passedCount} passed
                            </span>
                          )}
                          {reviewCount > 0 && (
                            <span style={{ fontSize: "11px", color: "#d97706", background: "rgba(245, 158, 11, 0.12)", padding: "2px 6px", borderRadius: "4px", fontWeight: 700 }}>
                              {reviewCount} review
                            </span>
                          )}
                          {failedCount > 0 && (
                            <span style={{ fontSize: "11px", color: "#dc2626", background: "rgba(239, 68, 68, 0.12)", padding: "2px 6px", borderRadius: "4px", fontWeight: 700 }}>
                              {failedCount} failed
                            </span>
                          )}
                          {notAvailCount > 0 && (
                            <span style={{ fontSize: "11px", color: "#64748b", background: "rgba(100, 116, 139, 0.08)", padding: "2px 6px", borderRadius: "4px" }}>
                              {notAvailCount} n/a
                            </span>
                          )}
                          <StatusBadge status={cat.status} />
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
                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                          <thead>
                            <tr style={{ background: "rgba(0, 0, 0, 0.02)", textAlign: "left" }}>
                              <th style={{ padding: "8px 12px", fontWeight: 600, color: "var(--text-secondary)", width: "60px" }}>ID</th>
                              <th style={{ padding: "8px 12px", fontWeight: 600, color: "var(--text-secondary)" }}>Check Name</th>
                              <th style={{ padding: "8px 12px", fontWeight: 600, color: "var(--text-secondary)", width: "100px" }}>Status</th>
                              <th style={{ padding: "8px 12px", fontWeight: 600, color: "var(--text-secondary)" }}>Expected / Prior</th>
                              <th style={{ padding: "8px 12px", fontWeight: 600, color: "var(--text-secondary)" }}>Actual / Current</th>
                              <th style={{ padding: "8px 12px", fontWeight: 600, color: "var(--text-secondary)" }}>Variance / Diff</th>
                              <th style={{ padding: "8px 12px", fontWeight: 600, color: "var(--text-secondary)" }}>Threshold</th>
                              <th style={{ padding: "8px 12px", fontWeight: 600, color: "var(--text-secondary)", textAlign: "right" }}>Evidence / Finding</th>
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
                                  <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: "11px", color: "var(--text-muted)" }}>
                                    {chk.id}
                                  </td>
                                  <td style={{ padding: "8px 12px", fontWeight: 600, color: "var(--text-primary)" }}>
                                    <div>{chk.check}</div>
                                    {chk.evidence && (
                                      <div style={{ fontSize: "11px", fontWeight: 400, color: "var(--text-muted)", marginTop: "2px" }}>
                                        {chk.evidence}
                                      </div>
                                    )}
                                  </td>
                                  <td style={{ padding: "8px 12px" }}>
                                    <StatusBadge status={chk.status} />
                                  </td>
                                  <td style={{ padding: "8px 12px", color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
                                    {chk.expected_value || <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>Not available</span>}
                                  </td>
                                  <td style={{ padding: "8px 12px", fontWeight: 600, color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
                                    {chk.actual_value || <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>Not available</span>}
                                  </td>
                                  <td style={{ padding: "8px 12px", color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
                                    {chk.difference || chk.difference_percent || <span style={{ color: "var(--text-muted)" }}>—</span>}
                                  </td>
                                  <td style={{ padding: "8px 12px", fontSize: "11px", color: "var(--text-muted)" }}>
                                    {chk.threshold || "—"}
                                  </td>
                                  <td style={{ padding: "8px 12px", textAlign: "right" }}>
                                    {chk.finding_id ? (
                                      <button
                                        onClick={() => onOpenEvidence && onOpenEvidence(chk.finding_id)}
                                        style={{
                                          display: "inline-flex",
                                          alignItems: "center",
                                          gap: "4px",
                                          padding: "3px 8px",
                                          borderRadius: "4px",
                                          fontSize: "11px",
                                          fontWeight: 600,
                                          background: "rgba(16, 185, 129, 0.1)",
                                          color: "var(--color-primary)",
                                          border: "1px solid rgba(16, 185, 129, 0.3)",
                                          cursor: "pointer",
                                        }}
                                      >
                                        <ExternalLink size={12} />
                                        {chk.finding_id}
                                      </button>
                                    ) : chk.source ? (
                                      <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                                        {chk.source.page != null ? `p.${chk.source.page}` : (chk.source.sheet ? `Sheet: ${chk.source.sheet}` : (chk.source.file || "—"))}
                                      </span>
                                    ) : (
                                      <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>—</span>
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
        )}
      </div>
    </div>
  );
}
