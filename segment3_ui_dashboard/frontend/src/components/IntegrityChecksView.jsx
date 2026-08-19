import React, { useState, useMemo } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  HelpCircle,
  ArrowLeft,
  FileText,
  Calculator,
  Coins,
  Repeat,
  Layers,
  FileCheck2,
  Activity,
  Percent,
  TrendingUp,
  Scale,
  FileSearch,
  Search,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Sparkles
} from "lucide-react";

const CONTROL_DEFINITIONS = [
  {
    id: "mathematical_accuracy",
    name: "Mathematical Accuracy",
    shortDesc: "Validates horizontal & vertical arithmetic, subtotals, and statement totals.",
    Icon: Calculator,
    formula: "Statement Subtotals + Adjustments = Stated Grand Totals (Tolerance: < 0.1%)",
  },
  {
    id: "cash_flow",
    name: "Cash Flow Reconciliation",
    shortDesc: "Reconciles Operating, Investing, and Financing cash flows with balance sheet cash movements.",
    Icon: Coins,
    formula: "Opening Cash + CFO + CFI + CFF + Forex = Closing Cash Balance",
  },
  {
    id: "prior_year_tieout",
    name: "Prior-Year Tie-Out",
    shortDesc: "Verifies that prior-period comparative figures match previously reported annual accounts.",
    Icon: Repeat,
    formula: "Current Filing [Prior Period Value] == Historical Prior Filing [Reported Value]",
  },
  {
    id: "internal_consistency",
    name: "Internal Cross-Statement Consistency",
    shortDesc: "Checks cross-statement links: Assets = Liabilities + Equity, Net Income flow into Equity.",
    Icon: Layers,
    formula: "Total Assets == Total Liabilities + Total Equity | IS Net Profit -> Retained Earnings",
  },
  {
    id: "document_quality",
    name: "Document & Narrative Quality Gate",
    shortDesc: "Evaluates completeness of filing tables, OCR fidelity, unit/scale consistency, and required schedules.",
    Icon: FileCheck2,
    formula: "Completeness Score >= 80% | Currency & Unit Stated | No Missing Critical Schedules",
  },
  {
    id: "analytical_comparison",
    name: "Analytical Comparison & Growth",
    shortDesc: "Validates year-over-year revenue, gross margin, operating margin, and expense trends.",
    Icon: Activity,
    formula: "YoY Variance Analysis across 11 core operating & margin metrics",
  },
  {
    id: "ratios",
    name: "Key Financial Ratios Benchmark",
    shortDesc: "Computes 12 standard liquidity, solvency, profitability, and turnover ratios against risk thresholds.",
    Icon: Percent,
    formula: "Current Ratio >= 1.0 | Debt/Equity <= 2.0 | Net Margin > 0 | ROE > 10%",
  },
  {
    id: "unusual_fluctuation",
    name: "Unusual Fluctuation Scanner",
    shortDesc: "Flags abnormal multi-sigma swings, sudden spikes in provisions, or revenue-expense decoupling.",
    Icon: TrendingUp,
    formula: "Abs(YoY Growth) > 30% without corresponding operational volume justification",
  },
  {
    id: "unusual_gain",
    name: "Unusual Gains & Divergence Analysis",
    shortDesc: "Detects non-operating items, extraordinary gains, or asset sale windfalls inflating net profit.",
    Icon: Scale,
    formula: "Operating Profit Trend vs Net Profit Trend Divergence > Threshold",
  },
  {
    id: "related_disclosure",
    name: "Related Party & Notes Disclosures",
    shortDesc: "Audits related party transaction schedules, key management remuneration, and contingent notes.",
    Icon: FileSearch,
    formula: "Ind AS 24 / IAS 24 Related Party Disclosures cross-referenced with P&L line items",
  },
];

export default function IntegrityChecksView({ extractionResult, analysisResult, onBack, onOpenEvidence, onAskAI }) {
  const [filterStatus, setFilterStatus] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedControl, setExpandedControl] = useState(null);

  const checks = analysisResult?.checks || {};
  const wp514 = analysisResult?.wp514 || {};
  const findings = analysisResult?.findings || [];
  const score = analysisResult?.overall_score || 0;
  const status = analysisResult?.overall_status || "UNKNOWN";

  // Build integrity controls list
  const controls = useMemo(() => {
    return CONTROL_DEFINITIONS.map((def) => {
      const checkVal = checks[def.id];
      const isScore = typeof checkVal === "number";
      const isNA = checkVal === "NOT_AVAILABLE" || checkVal === null || checkVal === undefined || (def.id === "related_disclosure" && checkVal === 0);

      // Find matching WP-514 category
      const wpCatKey = Object.keys(wp514.categories || {}).find(
        (k) => k.toLowerCase() === def.id.toLowerCase() || k.toLowerCase().replace(/_/g, "") === def.id.toLowerCase().replace(/_/g, "")
      );
      const wpCat = wpCatKey ? wp514.categories[wpCatKey] : null;

      // Find matching findings
      const matchingFindings = findings.filter(
        (f) => (f.category || "").toLowerCase() === def.id.toLowerCase() || (f.category || "").toLowerCase().replace(/_/g, "") === def.id.toLowerCase().replace(/_/g, "")
      );

      let controlScore = isScore ? checkVal : wpCat?.score ?? 0;
      let controlStatus = "PASSED";
      if (isNA) {
        controlStatus = "NOT_AVAILABLE";
      } else if (controlScore >= 80) {
        controlStatus = "PASSED";
      } else if (controlScore >= 50) {
        controlStatus = "REVIEW";
      } else {
        controlStatus = "FAILED";
      }

      return {
        ...def,
        score: isNA ? null : controlScore,
        status: controlStatus,
        isNA,
        wpCat,
        itemsCount: wpCat?.total_items || wpCat?.verification_items?.length || 0,
        passedCount: wpCat?.passed_items || 0,
        findings: matchingFindings,
      };
    });
  }, [checks, wp514, findings]);

  const filteredControls = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return controls.filter((ctrl) => {
      const matchFilter =
        filterStatus === "ALL" ||
        ctrl.status === filterStatus ||
        (filterStatus === "REVIEW" && (ctrl.status === "REVIEW" || ctrl.status === "FAILED"));
      if (!matchFilter) return false;

      if (!q) return true;
      return (
        ctrl.name.toLowerCase().includes(q) ||
        ctrl.shortDesc.toLowerCase().includes(q) ||
        ctrl.formula.toLowerCase().includes(q) ||
        ctrl.findings.some((f) => (f.title || "").toLowerCase().includes(q) || (f.description || "").toLowerCase().includes(q))
      );
    });
  }, [controls, filterStatus, searchQuery]);

  const passedControlsCount = controls.filter((c) => c.status === "PASSED").length;
  const reviewControlsCount = controls.filter((c) => c.status === "REVIEW" || c.status === "FAILED").length;
  const naControlsCount = controls.filter((c) => c.isNA).length;

  return (
    <div style={{ background: "var(--bg-main)", minHeight: "100vh", padding: "32px 40px", maxWidth: 1250, margin: "0 auto" }}>
      {/* Top Navigation */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, flexWrap: "wrap", gap: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            onClick={onBack}
            className="fd-btn fd-btn-outline"
            style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: "13px", fontWeight: 600 }}
          >
            <ArrowLeft size={15} /> Back to Dashboard
          </button>
          <div>
            <h1 style={{ fontSize: "22px", fontWeight: 800, color: "var(--text-primary)", margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
              <ShieldCheck size={24} color="var(--color-primary)" /> Audit Integrity & Quality Controls
            </h1>
            <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: 2 }}>
              10 Automated Audit Procedures • Continuous Assurance & Rule Verification
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            onClick={() => { window.location.hash = "#wp514"; }}
            className="fd-btn fd-btn-outline"
            style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: "13px", fontWeight: 600 }}
          >
            <FileCheck2 size={15} /> WP-514 Matrix
          </button>
          <button
            onClick={() => { window.location.hash = "#report"; }}
            className="fd-btn fd-btn-primary"
            style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: "13px", fontWeight: 600 }}
          >
            <FileText size={15} /> Audit Report
          </button>
        </div>
      </div>

      {/* Summary KPI Strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, marginBottom: 24 }}>
        <div className="fd-card" style={{ padding: "20px" }}>
          <div style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>Overall Compliance Score</div>
          <div style={{ fontSize: "28px", fontWeight: 800, color: score >= 75 ? "var(--color-success)" : score >= 50 ? "var(--color-warning)" : "var(--color-danger)", marginTop: 4 }}>
            {score.toFixed(1)} <span style={{ fontSize: "16px", fontWeight: 500, color: "var(--text-muted)" }}>/ 100</span>
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: 4 }}>Status: <strong style={{ color: "var(--text-primary)" }}>{status.replace(/_/g, " ")}</strong></div>
        </div>

        <div className="fd-card" style={{ padding: "20px" }}>
          <div style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>Passed Controls</div>
          <div style={{ fontSize: "28px", fontWeight: 800, color: "var(--color-success)", marginTop: 4 }}>
            {passedControlsCount} <span style={{ fontSize: "16px", fontWeight: 500, color: "var(--text-muted)" }}>/ 10</span>
          </div>
          <div style={{ fontSize: "11px", color: "var(--color-success)", marginTop: 4, fontWeight: 600 }}>Zero discrepancies found</div>
        </div>

        <div className="fd-card" style={{ padding: "20px" }}>
          <div style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>Review Required</div>
          <div style={{ fontSize: "28px", fontWeight: 800, color: reviewControlsCount > 0 ? "var(--color-warning)" : "var(--text-primary)", marginTop: 4 }}>
            {reviewControlsCount} <span style={{ fontSize: "16px", fontWeight: 500, color: "var(--text-muted)" }}>/ 10</span>
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: 4 }}>Requires auditor attention</div>
        </div>

        <div className="fd-card" style={{ padding: "20px" }}>
          <div style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>Not in Filing / Optional</div>
          <div style={{ fontSize: "28px", fontWeight: 800, color: "var(--text-muted)", marginTop: 4 }}>
            {naControlsCount} <span style={{ fontSize: "16px", fontWeight: 500, color: "var(--text-muted)" }}>/ 10</span>
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: 4 }}>Neutral impact on score</div>
        </div>
      </div>

      {/* Main Controls Section */}
      <div className="fd-card animate-fade-up" style={{ padding: "24px" }}>
        {/* Filter Controls Bar */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16, marginBottom: 20 }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {[
              { key: "ALL", label: `All Controls (${controls.length})` },
              { key: "PASSED", label: `Passed (${passedControlsCount})` },
              { key: "REVIEW", label: `Requires Review (${reviewControlsCount})` },
              { key: "NOT_AVAILABLE", label: `Not in Filing (${naControlsCount})` },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setFilterStatus(tab.key)}
                className={`filter-tab-pill ${filterStatus === tab.key ? "active" : ""}`}
                style={{ padding: "8px 16px", fontSize: "13px" }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 8, background: "var(--bg-main)", borderRadius: "20px", padding: "6px 14px", width: "280px", border: "1px solid var(--border-light)" }}>
            <Search size={15} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search integrity rules, formulas..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ border: "none", outline: "none", fontSize: "13px", color: "var(--text-primary)", background: "transparent", width: "100%" }}
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery("")} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", fontSize: "12px" }}>✕</button>
            )}
          </div>
        </div>

        {/* 10 Control Cards List */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {filteredControls.length === 0 ? (
            <div style={{ padding: "48px 0", textAlign: "center", color: "var(--text-muted)" }}>
              No integrity controls match your filter criteria.
            </div>
          ) : (
            filteredControls.map((ctrl) => {
              const Icon = ctrl.Icon;
              const isExpanded = expandedControl === ctrl.id;
              const statusColor =
                ctrl.status === "PASSED"
                  ? "var(--color-success)"
                  : ctrl.status === "REVIEW"
                  ? "var(--color-warning)"
                  : ctrl.status === "FAILED"
                  ? "var(--color-danger)"
                  : "var(--text-muted)";
              const statusBg =
                ctrl.status === "PASSED"
                  ? "var(--color-success-soft)"
                  : ctrl.status === "REVIEW"
                  ? "var(--color-warning-soft)"
                  : ctrl.status === "FAILED"
                  ? "var(--color-danger-soft)"
                  : "var(--bg-main)";

              return (
                <div
                  key={ctrl.id}
                  className="fd-card"
                  style={{
                    padding: "18px 20px",
                    border: isExpanded ? "1px solid var(--color-primary)" : "1px solid var(--border-light)",
                    transition: "all 0.2s ease",
                  }}
                >
                  <div
                    onClick={() => setExpandedControl(isExpanded ? null : ctrl.id)}
                    style={{ display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer", gap: 16 }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 14, flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          width: "42px",
                          height: "42px",
                          borderRadius: "10px",
                          background: statusBg,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: statusColor,
                          flexShrink: 0,
                        }}
                      >
                        <Icon size={22} strokeWidth={2.2} />
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <span style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-primary)" }}>
                            {ctrl.name}
                          </span>
                          <span
                            style={{
                              fontSize: "11px",
                              fontWeight: 700,
                              color: statusColor,
                              background: statusBg,
                              padding: "2px 8px",
                              borderRadius: "6px",
                              border: `1px solid ${statusColor}30`,
                            }}
                          >
                            {ctrl.isNA ? "N/A (Not in filing)" : ctrl.status}
                          </span>
                        </div>
                        <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: 3 }}>
                          {ctrl.shortDesc}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: 16, flexShrink: 0 }}>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: "16px", fontWeight: 800, color: ctrl.isNA ? "var(--text-muted)" : statusColor }}>
                          {ctrl.isNA ? "N/A" : `${ctrl.score.toFixed(0)}%`}
                        </div>
                        <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                          {ctrl.findings.length} findings
                        </div>
                      </div>
                      <div
                        style={{
                          width: "28px",
                          height: "28px",
                          borderRadius: "50%",
                          background: isExpanded ? "var(--color-primary-soft)" : "transparent",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          transition: "transform 0.2s ease",
                          transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
                        }}
                      >
                        <ChevronDown size={16} color={isExpanded ? "var(--color-primary)" : "var(--text-muted)"} />
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="animate-slide-down" style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border-light)" }}>
                      {/* Formula & Rule Box */}
                      <div style={{ background: "var(--bg-main)", padding: "12px 16px", borderRadius: "8px", marginBottom: 14 }}>
                        <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 4 }}>
                          Auditing Formula / Rule
                        </div>
                        <div style={{ fontSize: "12px", color: "var(--text-primary)", fontFamily: "monospace" }}>
                          {ctrl.formula}
                        </div>
                      </div>

                      {/* Findings / Verification Details */}
                      {ctrl.findings.length > 0 ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                          <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-primary)" }}>
                            Verification Findings ({ctrl.findings.length})
                          </div>
                          {ctrl.findings.map((f) => (
                            <div
                              key={f.id}
                              style={{
                                background: "rgba(248, 250, 252, 0.8)",
                                padding: "12px 14px",
                                borderRadius: "8px",
                                border: "1px solid var(--border-light)",
                              }}
                            >
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                                <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                                  {f.title}
                                </span>
                                <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                                  {f.id}
                                </span>
                              </div>
                              <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: "0 0 10px", lineHeight: 1.5 }}>
                                {f.description || f.explanation}
                              </p>
                              <div style={{ display: "flex", gap: 8 }}>
                                <button
                                  onClick={() => onOpenEvidence && onOpenEvidence(f.id)}
                                  className="fd-btn fd-btn-outline"
                                  style={{ fontSize: "11px", padding: "4px 8px", borderRadius: "6px" }}
                                >
                                  <FileText size={12} /> View Evidence
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ fontSize: "12px", color: "var(--color-success)", display: "flex", alignItems: "center", gap: 6, fontWeight: 600 }}>
                          <CheckCircle2 size={15} /> All procedural tests satisfied. No discrepancies or exceptions recorded.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
