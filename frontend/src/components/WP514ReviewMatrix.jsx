import React, { useState } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  HelpCircle,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Filter,
  Layers,
  FileCheck2,
  Scale,
  Calendar,
  Building,
  FileSpreadsheet
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

export default function WP514ReviewMatrix({ wp514Data, onOpenEvidence }) {
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
  const [expandedCategories, setExpandedCategories] = useState(() => {
    // Default open the first category
    const initial = {};
    if (categories.length > 0) initial[categories[0].id] = true;
    return initial;
  });

  const toggleCategory = (catId) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [catId]: !prev[catId],
    }));
  };

  // Filter checks
  const filteredChecks = checks.filter((c) => {
    const matchCat = selectedCatId === "ALL" || c.category === selectedCatId;
    const matchStatus =
      statusFilter === "ALL" ||
      (statusFilter === "REVIEW" && (c.status === "REVIEW" || c.status === "WARNING")) ||
      c.status === statusFilter;
    return matchCat && matchStatus;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* ────────────────────────────────────────────────────────────
          1. HEADER & DOCUMENT INFORMATION
          ──────────────────────────────────────────────────────────── */}
      <div
        className="fd-card animate-fade-up"
        style={{
          padding: "24px",
          background: "linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(255, 255, 255, 0.9) 100%)",
          borderLeft: "4px solid var(--color-primary)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <span
                style={{
                  background: "var(--color-primary-soft)",
                  color: "var(--color-primary)",
                  padding: "3px 8px",
                  borderRadius: "4px",
                  fontSize: "11px",
                  fontWeight: 700,
                  letterSpacing: "0.05em",
                }}
              >
                WP-514 WORKPAPER
              </span>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Engine v{docInfo.engine_version || "2.0.0"}
              </span>
            </div>
            <h2 style={{ fontSize: "20px", fontWeight: 700, color: "var(--text-primary)", margin: "0 0 4px 0" }}>
              {title}
            </h2>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: 0 }}>
              {subtitle} • Grounded against verified document extractions and financial checks.
            </p>
          </div>

          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <div
              style={{
                textAlign: "right",
                background: "white",
                padding: "8px 14px",
                borderRadius: "8px",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div style={{ fontSize: "11px", color: "var(--text-secondary)", fontWeight: 500 }}>
                OVERALL COMPLIANCE SCORE
              </div>
              <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--color-primary)" }}>
                {overall.score?.toFixed(1) ?? "0.0"}
                <span style={{ fontSize: "13px", fontWeight: 500, color: "var(--text-muted)" }}> / 100</span>
              </div>
            </div>
          </div>
        </div>

        {/* Metadata Badges */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "12px",
            marginTop: "18px",
            paddingTop: "16px",
            borderTop: "1px solid var(--border-subtle)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Building size={16} color="var(--color-primary)" />
            <div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Entity</div>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
                {docInfo.company_name || "Not available"}
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Calendar size={16} color="var(--color-primary)" />
            <div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Period / FY</div>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
                {docInfo.reporting_period || docInfo.financial_year || "Not available"}
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Scale size={16} color="var(--color-primary)" />
            <div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Unit & Scale</div>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
                {docInfo.currency && docInfo.scale ? `${docInfo.currency} in ${docInfo.scale}` : (docInfo.currency || docInfo.scale || "Not available")}
                {docInfo.statement_type ? ` (${docInfo.statement_type})` : ""}
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <FileSpreadsheet size={16} color="var(--color-primary)" />
            <div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Framework</div>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
                {docInfo.reporting_framework || "Not available"}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          2. EXECUTIVE SUMMARY METRICS
          ──────────────────────────────────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "12px",
        }}
      >
        <div className="fd-card" style={{ padding: "16px", textAlign: "center" }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)" }}>TOTAL CHECKS</div>
          <div style={{ fontSize: "24px", fontWeight: 700, color: "var(--text-primary)", marginTop: "4px" }}>
            {overall.total_checks ?? checks.length}
          </div>
        </div>

        <div className="fd-card" style={{ padding: "16px", textAlign: "center", borderTop: "3px solid #10b981" }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#059669" }}>PASSED</div>
          <div style={{ fontSize: "24px", fontWeight: 700, color: "#059669", marginTop: "4px" }}>
            {overall.passed ?? 0}
          </div>
        </div>

        <div className="fd-card" style={{ padding: "16px", textAlign: "center", borderTop: "3px solid #f59e0b" }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#d97706" }}>REVIEW REQUIRED</div>
          <div style={{ fontSize: "24px", fontWeight: 700, color: "#d97706", marginTop: "4px" }}>
            {overall.review ?? 0}
          </div>
        </div>

        <div className="fd-card" style={{ padding: "16px", textAlign: "center", borderTop: "3px solid #ef4444" }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#dc2626" }}>FAILED</div>
          <div style={{ fontSize: "24px", fontWeight: 700, color: "#dc2626", marginTop: "4px" }}>
            {overall.failed ?? 0}
          </div>
        </div>

        <div className="fd-card" style={{ padding: "16px", textAlign: "center", borderTop: "3px solid #64748b" }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#64748b" }}>NOT IN FILING</div>
          <div style={{ fontSize: "24px", fontWeight: 700, color: "#64748b", marginTop: "4px" }}>
            {overall.not_available ?? 0}
          </div>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          3. CATEGORIES OVERVIEW GRID
          ──────────────────────────────────────────────────────────── */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
          <h3 style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
            WP-514 Audit Review Categories ({categories.length})
          </h3>
          <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            Select a category to filter check detail
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
            gap: "12px",
          }}
        >
          {categories.map((cat) => {
            const isSelected = selectedCatId === cat.id;
            return (
              <div
                key={cat.id}
                onClick={() => setSelectedCatId((prev) => (prev === cat.id ? "ALL" : cat.id))}
                className="fd-card hover-scale"
                style={{
                  padding: "14px",
                  cursor: "pointer",
                  border: isSelected ? "2px solid var(--color-primary)" : "1px solid var(--border-subtle)",
                  background: isSelected ? "rgba(16, 185, 129, 0.04)" : "white",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "10px",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "8px" }}>
                    <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                      {cat.name}
                    </div>
                    <StatusBadge status={cat.status} />
                  </div>
                  {cat.score !== null && cat.score !== undefined && (
                    <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px" }}>
                      Score: <strong>{cat.score.toFixed(1)}</strong> / 100
                    </div>
                  )}
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "11px",
                    color: "var(--text-muted)",
                    paddingTop: "6px",
                    borderTop: "1px dashed var(--border-subtle)",
                  }}
                >
                  <span>{cat.total_checks} checks</span>
                  <span>{cat.findings_count} findings</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          4. SUMMARIZED REVIEW CHECKS SECTION
          ──────────────────────────────────────────────────────────── */}
      <div className="fd-card" style={{ padding: "20px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "12px",
            marginBottom: "16px",
            paddingBottom: "12px",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <h3 style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
                Audit Review Checks Summary ({filteredChecks.length})
              </h3>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: 600,
                  padding: "2px 8px",
                  borderRadius: "12px",
                  background: "var(--color-primary-soft)",
                  color: "var(--color-primary)",
                }}
              >
                Summarized
              </span>
            </div>
            {selectedCatId !== "ALL" && (
              <span style={{ fontSize: "12px", color: "var(--color-primary)", fontWeight: 600, display: "block", marginTop: "2px" }}>
                Filtering: {categories.find((c) => c.id === selectedCatId)?.name || selectedCatId}
              </span>
            )}
          </div>

          <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
            <span style={{ fontSize: "12px", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
              <Filter size={14} /> Filter:
            </span>
            {["ALL", "REVIEW", "FAILED", "PASSED", "NOT_AVAILABLE"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                style={{
                  padding: "4px 10px",
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
                {st === "ALL" ? "All Status" : st === "REVIEW" ? "Review Required" : st === "NOT_AVAILABLE" ? "Not in Filing" : st}
              </button>
            ))}
            {selectedCatId !== "ALL" && (
              <button
                onClick={() => setSelectedCatId("ALL")}
                style={{
                  padding: "4px 10px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontWeight: 600,
                  background: "transparent",
                  color: "var(--color-primary)",
                  border: "1px solid var(--color-primary)",
                  cursor: "pointer",
                }}
              >
                Reset Category
              </button>
            )}
          </div>
        </div>

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
                const isExpanded = expandedCategories[cat.id] ?? (reviewCount > 0 || failedCount > 0);

                return (
                  <div
                    key={cat.id}
                    style={{
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "8px",
                      overflow: "hidden",
                      background: "var(--bg-card)",
                    }}
                  >
                    {/* Category Summary Header (Click to Expand / Collapse) */}
                    <div
                      onClick={() => toggleCategory(cat.id)}
                      style={{
                        padding: "12px 16px",
                        background: isExpanded ? "rgba(16, 185, 129, 0.04)" : "var(--bg-secondary)",
                        cursor: "pointer",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        flexWrap: "wrap",
                        gap: "10px",
                        borderBottom: isExpanded ? "1px solid var(--border-subtle)" : "none",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        {isExpanded ? (
                          <ChevronDown size={18} color="var(--color-primary)" />
                        ) : (
                          <ChevronRight size={18} color="var(--text-muted)" />
                        )}
                        <div>
                          <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                            {cat.name}
                          </div>
                          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                            {catChecks.length} checks in this area • {cat.description || "Audit review verification"}
                          </div>
                        </div>
                      </div>

                      <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                        {/* Breakdown pills */}
                        {passedCount > 0 && (
                          <span style={{ fontSize: "11px", color: "#059669", background: "rgba(16, 185, 129, 0.1)", padding: "2px 6px", borderRadius: "4px", fontWeight: 600 }}>
                            {passedCount} passed
                          </span>
                        )}
                        {reviewCount > 0 && (
                          <span style={{ fontSize: "11px", color: "#d97706", background: "rgba(245, 158, 11, 0.1)", padding: "2px 6px", borderRadius: "4px", fontWeight: 700 }}>
                            {reviewCount} review required
                          </span>
                        )}
                        {failedCount > 0 && (
                          <span style={{ fontSize: "11px", color: "#dc2626", background: "rgba(239, 68, 68, 0.1)", padding: "2px 6px", borderRadius: "4px", fontWeight: 700 }}>
                            {failedCount} failed
                          </span>
                        )}
                        {notAvailCount > 0 && (
                          <span style={{ fontSize: "11px", color: "#64748b", background: "rgba(100, 116, 139, 0.08)", padding: "2px 6px", borderRadius: "4px" }}>
                            {notAvailCount} not in filing
                          </span>
                        )}
                        <StatusBadge status={cat.status} />
                      </div>
                    </div>

                    {/* Detailed Checks Sub-table when expanded */}
                    {isExpanded && (
                      <div style={{ overflowX: "auto" }}>
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
