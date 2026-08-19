import React, { useMemo } from "react";
import ScoreSeal from "./ScoreSeal.jsx";
import RatioTile from "./RatioTile.jsx";
import WP514ReviewMatrix from "./WP514ReviewMatrix.jsx";
import AuditReportPrint from "./AuditReportPrint.jsx";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import {
  ArrowLeft,
  Printer,
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  CircleAlert,
  CheckCircle2,
  TrendingUp,
  Coins,
  Calculator,
  Repeat,
  Layers,
  Activity,
  Percent,
  Scale,
  FileSearch,
  FileText,
  FileCheck2,
  Award,
  Wallet,
  ArrowDownRight,
  ArrowUpRight,
  ExternalLink,
  Sparkles,
  Clock,
  FileBadge,
  Check,
  ChevronDown,
} from "lucide-react";

const sev = {
  CRITICAL: { color: "var(--color-danger, #EF4444)", bg: "var(--color-danger-soft, #FEE2E2)", label: "Critical", Icon: AlertOctagon },
  HIGH:     { color: "var(--color-warning, #F59E0B)", bg: "var(--color-warning-soft, #FEF3C7)", label: "High", Icon: AlertTriangle },
  REVIEW:   { color: "var(--color-purple, #8B5CF6)", bg: "var(--color-purple-soft, #EDE9FE)", label: "Review", Icon: CircleAlert },
  PASSED:   { color: "var(--color-success, #10B981)", bg: "var(--color-success-soft, #D1FAE5)", label: "Passed", Icon: ShieldCheck },
};

const INTEGRITY_CONFIG = {
  mathematical_accuracy: { name: "Mathematical Accuracy", Icon: Calculator, short: "Math Accuracy" },
  cash_flow: { name: "Cash Flow Reconciliation", Icon: Coins, short: "Cash Flow" },
  prior_year_tieout: { name: "Prior-Year Tie-Out", Icon: Repeat, short: "Prior Tieout" },
  internal_consistency: { name: "Internal Consistency", Icon: Layers, short: "Consistency" },
  document_quality: { name: "Document & Narrative Quality", Icon: FileCheck2, short: "Doc Quality" },
  analytical_comparison: { name: "Analytical Comparison", Icon: Activity, short: "Analytical" },
  ratios: { name: "Key Financial Ratios", Icon: Percent, short: "Ratios" },
  unusual_fluctuation: { name: "Unusual Fluctuations", Icon: TrendingUp, short: "Fluctuations" },
  unusual_gain: { name: "Unusual Gains & Divergence", Icon: Scale, short: "Unusual Gain" },
  related_disclosure: { name: "Related Party Disclosures", Icon: FileSearch, short: "Related Party" },
};

const fmt = (n) => (n === null || n === undefined ? "—" : n.toLocaleString("en-IN"));
const pct = (n) => (n === null || n === undefined ? "—" : `${n > 0 ? "+" : ""}${Number(n).toFixed(2)}%`);

// Sanitizer helper for string leaks (None%, None Cr, None pp, None)
const cleanText = (str) => {
  if (!str) return "";
  return str
    .replace(/None\s*%/gi, "N/A")
    .replace(/None\s*Cr/gi, "N/A")
    .replace(/None\s*pp/gi, "N/A")
    .replace(/=\s*None/gi, "= N/A")
    .replace(/:\s*None/gi, ": N/A")
    .replace(/\bNone\b/g, "N/A");
};

// Safe growth formatter
const fmtGrowth = (data) => {
  if (data?.growth_pct === null || data?.growth_pct === undefined) return "—";
  const num = Number(data.growth_pct);
  if (isNaN(num)) return "—";
  if (data.previous !== null && data.previous !== undefined && Math.abs(data.previous) < 1 && Math.abs(data.current || 0) > 1000) {
    return "> +999% (Base Near Zero)";
  }
  if (num > 9999) return "> +999%";
  if (num < -9999) return "< -999%";
  return `${num > 0 ? "+" : ""}${num.toFixed(2)}%`;
};

// Formatted generation time
const formatDateTime = (date = new Date()) => {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const d = date.getDate();
  const m = months[date.getMonth()];
  const y = date.getFullYear();
  let hours = date.getHours();
  const minutes = date.getMinutes().toString().padStart(2, "0");
  const ampm = hours >= 12 ? "PM" : "AM";
  hours = hours % 12 || 12;
  return `${d} ${m} ${y}, ${hours.toString().padStart(2, "0")}:${minutes} ${ampm}`;
};

export default function AuditReport({ extractionResult, analysisResult, onBack }) {
  const fm = analysisResult?.financial_metrics || {};
  const fs = analysisResult?.findings_summary || {};
  const dq = extractionResult?.document_quality || {};
  const findings = analysisResult?.findings || [];
  const checks = analysisResult?.checks || {};
  const wp514 = analysisResult?.wp514 || {};
  const ratios = analysisResult?.ratios || {};

  const currentPeriod = extractionResult?.period?.current || extractionResult?.periods?.[0]?.period_key || "Current Period";
  const previousPeriod = extractionResult?.period?.previous || (extractionResult?.periods?.length > 1 ? extractionResult.periods[1].period_key : "Prior Period");

  // ── Single source of truth: all check counts come from wp514.overall ──
  // wp514.overall is the canonical computed struct from wp514_service.py.
  // Flat wp514.* fields do NOT exist — reading them gives undefined which
  // caused mismatches between the executive summary and the appendix.
  const wp514Overall = wp514.overall || {};
  const totalChecks         = wp514Overall.total_checks   ?? (analysisResult?.wp514?.checks?.length ?? 0);
  const passedChecks        = wp514Overall.passed         ?? 0;
  const reviewRequiredChecks = wp514Overall.review        ?? 0;
  const failedChecks        = wp514Overall.failed         ?? 0;
  const notInFilingChecks   = wp514Overall.not_available  ?? (totalChecks - passedChecks - reviewRequiredChecks - failedChecks);
  const overallScore        = wp514Overall.score          ?? analysisResult?.overall_score ?? 0;

  // Recommended review findings (Critical + High)
  const recommendedReview = findings.filter(
    (f) => f.severity === "CRITICAL" || f.severity === "HIGH"
  );

  // Visual Comparison Chart Data
  const chartMetricsData = [
    { name: "Revenue", Previous: (fm.revenue?.previous && Math.abs(fm.revenue.previous) > 1) ? fm.revenue.previous : 0, Current: fm.revenue?.current || 0 },
    { name: "Expenses", Previous: (fm.expenses?.previous && Math.abs(fm.expenses.previous) > 1) ? fm.expenses.previous : 0, Current: fm.expenses?.current || 0 },
    { name: "Gross Profit", Previous: (fm.gross_profit?.previous && Math.abs(fm.gross_profit.previous) > 1) ? fm.gross_profit.previous : 0, Current: fm.gross_profit?.current || 0 },
    { name: "Operating Profit", Previous: (fm.operating_profit?.previous && Math.abs(fm.operating_profit.previous) > 1) ? fm.operating_profit.previous : 0, Current: fm.operating_profit?.current || 0 },
    { name: "Net Profit", Previous: (fm.net_profit?.previous && Math.abs(fm.net_profit.previous) > 1) ? fm.net_profit.previous : 0, Current: fm.net_profit?.current || 0 },
    { name: "Equity", Previous: (fm.equity?.previous && Math.abs(fm.equity.previous) > 1) ? fm.equity.previous : 0, Current: fm.equity?.current || 0 },
  ].filter(item => item.Current !== 0 || item.Previous !== 0);

  // Audit Findings Donut Data
  const findingsDonutData = [
    { name: "Critical", value: fs.critical || 0, color: "#EF4444" },
    { name: "High", value: fs.high || 0, color: "#F59E0B" },
    { name: "Review", value: fs.review || 0, color: "#8B5CF6" },
    { name: "Passed", value: fs.passed || 0, color: "#10B981" },
  ].filter(d => d.value > 0);

  // Checks Distribution Data
  const checksDistData = [
    { name: "Passed", count: passedChecks, pct: Math.round((passedChecks / totalChecks) * 100), color: "#10B981" },
    { name: "Review Required", count: reviewRequiredChecks, pct: Math.round((reviewRequiredChecks / totalChecks) * 100), color: "#F59E0B" },
    { name: "Failed", count: failedChecks, pct: Math.round((failedChecks / totalChecks) * 100), color: "#EF4444" },
    { name: "Not in Filing", count: notInFilingChecks, pct: Math.round((notInFilingChecks / totalChecks) * 100), color: "#94A3B8" },
  ];

  // Integrity Controls Bar Data
  const integrityBarData = Object.entries(checks)
    .filter(([, val]) => val !== null && val !== undefined)
    .map(([key, val]) => {
      const num = Number(val);
      const isNA = val === "NOT_AVAILABLE" || (key === "related_disclosure" && num === 0);
      const config = INTEGRITY_CONFIG[key] || { name: key.replace(/_/g, " "), short: key.replace(/_/g, " ") };
      const score = isNA ? 0 : Math.min(100, Math.max(0, num));
      return {
        key,
        name: config.short,
        fullName: config.name,
        score,
        isNA,
        color: isNA ? "#94A3B8" : score >= 80 ? "#10B981" : score >= 50 ? "#F59E0B" : "#EF4444",
      };
    });

  // Financial Ratios Grouping
  const ratioGroups = useMemo(() => {
    const r = ratios || {};
    return {
      liquidity: [
        { label: "Current Ratio", key: "current_ratio", val: r.current_ratio },
        { label: "Quick Ratio", key: "quick_ratio", val: r.quick_ratio },
        { label: "Cash Ratio", key: "cash_ratio", val: r.cash_ratio },
      ],
      solvency: [
        { label: "Debt to Equity", key: "debt_to_equity", val: r.debt_to_equity },
        { label: "Debt Ratio", key: "debt_ratio", val: r.debt_ratio },
        { label: "Interest Coverage", key: "interest_coverage_ratio", val: r.interest_coverage_ratio },
      ],
      profitability: [
        { label: "Gross Margin", key: "gross_profit_margin_pct", val: r.gross_profit_margin_pct ? `${r.gross_profit_margin_pct}%` : null },
        { label: "Operating Margin", key: "operating_margin_pct", val: r.operating_margin_pct ? `${r.operating_margin_pct}%` : null },
        { label: "Net Margin", key: "net_margin_pct", val: r.net_margin_pct ? `${r.net_margin_pct}%` : null },
        { label: "Return on Assets", key: "return_on_assets_pct", val: r.return_on_assets_pct ? `${r.return_on_assets_pct}%` : null },
        { label: "ROE", key: "roe_pct", val: r.roe_pct ? `${r.roe_pct}%` : null },
      ],
      efficiency: [
        { label: "Asset Turnover", key: "asset_turnover_ratio", val: r.asset_turnover_ratio },
        { label: "Receivables Turnover", key: "receivables_turnover_ratio", val: r.receivables_turnover_ratio },
        { label: "Days Sales Outstanding", key: "days_sales_outstanding", val: r.days_sales_outstanding },
        { label: "Inventory Turnover", key: "inventory_turnover_ratio", val: r.inventory_turnover_ratio },
      ],
    };
  }, [ratios]);

  // Condensed Findings: Group boilerplate Prior-Year Tie-Out passes
  const condensedFindings = useMemo(() => {
    const list = [];
    const pyPassed = [];

    findings.forEach((f, i) => {
      const isPYPass = f.severity === "PASSED" && (f.category === "PRIOR_YEAR_TIEOUT" || (f.title || "").includes("Prior Year Tie-Out"));
      if (isPYPass) {
        pyPassed.push(f);
      } else {
        list.push({ ...f, originalIndex: i });
      }
    });

    if (pyPassed.length > 0) {
      list.unshift({
        id: "PY-SUMMARY",
        severity: "PASSED",
        category: "PRIOR_YEAR_TIEOUT",
        title: `Prior-Year Tie-Out Verification (${pyPassed.length}/${pyPassed.length} Passed)`,
        description: `Verified continuity of prior closing balances across all ${pyPassed.length} balance sheet and income statement line items. All opening balances tie out exactly with prior year closing.`,
        source: { note_ref: "Prior Year Comparison" },
        isSummaryGroup: true,
      });
    }

    return list;
  }, [findings]);

  return (
    <>
      <div
        className="audit-report-container"
        style={{
          background: "var(--bg-main, #F8FAFC)",
          minHeight: "100vh",
          color: "var(--text-primary, #0F172A)",
          padding: "24px 36px",
          maxWidth: 1140,
          margin: "0 auto",
        }}
      >
        {/* ── Action Bar (Screen Only) ── */}
      <div
        className="no-print"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
          paddingBottom: 12,
          borderBottom: "1px solid var(--border-light, #E2E8F0)",
        }}
      >
        <button
          onClick={onBack}
          className="fd-btn fd-btn-outline hover-scale"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            fontSize: "13px",
            fontWeight: 600,
          }}
        >
          <ArrowLeft size={15} /> Back to Dashboard
        </button>

        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <button
            onClick={() => {
              // Blank document.title so the browser print header
              // shows nothing (or just whitespace) instead of
              // "Financial Audit Dashboard". Restore after print closes.
              const prev = document.title;
              document.title = " ";
              window.print();
              document.title = prev;
            }}
            className="fd-btn fd-btn-primary hover-scale"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              fontSize: "13px",
              fontWeight: 700,
              boxShadow: "0 4px 14px rgba(16, 185, 129, 0.25)",
            }}
          >
            <Printer size={15} /> Print / Export PDF
          </button>
        </div>
      </div>

      {/* ── 1. REPORT HEADER WITH TIMESTAMP & REPORT ID ── */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "var(--bg-card, #FFFFFF)",
          border: "1px solid var(--border-light, #E2E8F0)",
          borderRadius: "8px",
          padding: "8px 16px",
          marginBottom: "16px",
          fontSize: "11.5px",
          color: "var(--text-secondary, #64748B)",
          boxShadow: "0 1px 3px rgba(0,0,0,0.02)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <Clock size={13} color="var(--color-primary, #059669)" />
          <span>
            Generated on: <strong style={{ color: "var(--text-primary)" }}>{formatDateTime()}</strong>
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <span>
            Audit Document Ref: <strong style={{ fontFamily: "monospace", color: "var(--color-primary, #059669)" }}>{extractionResult?.document_id || "DOC-20260819190030"}</strong>
          </span>
          <span>•</span>
          <span>Engine v{analysisResult?.score_formula_version || "2.0.0"} (Ind AS / IFRS)</span>
        </div>
      </div>

      {/* ── 2. EXECUTIVE SUMMARY (WP-514 REVIEW & TOP-LINE STATS) ── */}
      <div
        className="fd-card animate-fade-up report-section-break"
        style={{
          padding: "20px 24px",
          marginBottom: "18px",
          background: "linear-gradient(135deg, rgba(236, 253, 245, 0.9) 0%, #FFFFFF 50%, rgba(240, 253, 244, 0.8) 100%)",
          borderLeft: "6px solid var(--color-primary, #059669)",
          borderTop: "1px solid rgba(16, 185, 129, 0.25)",
          borderRight: "1px solid rgba(16, 185, 129, 0.2)",
          borderBottom: "1px solid rgba(16, 185, 129, 0.2)",
        }}
      >
        {/* Executive Info Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
          <div>
            <div
              style={{
                fontSize: "11px",
                color: "var(--color-primary, #059669)",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                fontWeight: 800,
                display: "flex",
                alignItems: "center",
                gap: "6px",
                marginBottom: "4px",
              }}
            >
              <ShieldCheck size={14} /> WP-514 FINANCIAL STATEMENT REVIEW · EXECUTIVE SUMMARY
            </div>
            <h1
              style={{
                fontSize: "24px",
                margin: "4px 0 6px",
                fontWeight: 800,
                color: "var(--text-primary, #0F172A)",
              }}
            >
              {extractionResult?.company?.name || extractionResult?.file_name || "Financial Statement"}
            </h1>
            <div style={{ fontSize: "12.5px", color: "var(--text-secondary, #64748B)", display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "center" }}>
              <span>
                Period: <strong style={{ color: "var(--text-primary)" }}>{currentPeriod}</strong>
                {previousPeriod ? ` vs ${previousPeriod}` : ""}
              </span>
              <span>•</span>
              <span>
                Scale: <strong style={{ color: "var(--text-primary)" }}>{extractionResult?.currency || "INR"} in {extractionResult?.unit || "Millions"} ({extractionResult?.is_consolidated ? "Consolidated" : "Standalone"})</strong>
              </span>
              <span>•</span>
              <span>
                Framework: <strong style={{ color: "var(--text-primary)" }}>{extractionResult?.reporting_framework || "Ind AS / IFRS"}</strong>
              </span>
            </div>
          </div>
          <ScoreSeal score={overallScore} />
        </div>

        {/* Top-Line Stat Cards Row */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10 }}>
          <div
            style={{
              background: "#FFFFFF",
              border: "1px solid var(--border-light)",
              borderRadius: "8px",
              padding: "10px 12px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
              Total Checks
            </div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "var(--text-primary)", marginTop: "2px" }}>
              {totalChecks}
            </div>
          </div>

          <div
            style={{
              background: "rgba(16, 185, 129, 0.08)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              borderRadius: "8px",
              padding: "10px 12px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-success)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
              Passed
            </div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "var(--color-success)", marginTop: "2px" }}>
              {passedChecks}
            </div>
          </div>

          <div
            style={{
              background: "rgba(245, 158, 11, 0.08)",
              border: "1px solid rgba(245, 158, 11, 0.3)",
              borderRadius: "8px",
              padding: "10px 12px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-warning)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
              Review Required
            </div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "var(--color-warning)", marginTop: "2px" }}>
              {reviewRequiredChecks}
            </div>
          </div>

          <div
            style={{
              background: "rgba(239, 68, 68, 0.08)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              borderRadius: "8px",
              padding: "10px 12px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-danger)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
              Failed
            </div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "var(--color-danger)", marginTop: "2px" }}>
              {failedChecks}
            </div>
          </div>

          <div
            style={{
              background: "rgba(100, 116, 139, 0.08)",
              border: "1px solid rgba(100, 116, 139, 0.2)",
              borderRadius: "8px",
              padding: "10px 12px",
              textAlign: "center",
            }}
            title="Items not present in current company filing format"
          >
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
              Not in Filing
            </div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "#64748B", marginTop: "2px" }}>
              {notInFilingChecks}
            </div>
          </div>
        </div>
      </div>

      {/* ── 3. RECOMMENDED ACTIONS / MATERIALITY SUMMARY (PROMINENT UP FRONT) ── */}
      <div
        className="fd-card animate-fade-up report-section-break"
        style={{
          padding: "16px 20px",
          marginBottom: "18px",
          borderLeft: recommendedReview.length > 0 ? "5px solid var(--color-warning)" : "5px solid var(--color-success)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <h2 style={{ fontSize: "15px", color: "var(--text-primary)", fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
            <Award size={16} color={recommendedReview.length > 0 ? "var(--color-warning)" : "var(--color-success)"} />
            Recommended Actions & Materiality Takeaways
          </h2>
          <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)" }}>
            {recommendedReview.length > 0 ? `${recommendedReview.length} Priority Action Items` : "Continuous Assurance Clear"}
          </span>
        </div>

        {recommendedReview.length === 0 ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              color: "var(--color-success)",
              fontSize: "12.5px",
              fontWeight: 600,
              background: "var(--color-success-soft)",
              padding: "10px 14px",
              borderRadius: "6px",
            }}
          >
            <CheckCircle2 size={16} /> All core audit verification criteria passed within acceptable tolerance thresholds. No critical anomalies identified.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {recommendedReview.map((f, i) => {
              const fid = f.id || f.finding_id || `REC-${i}`;
              const src = f.source || f.source_ref || {};
              const isCrit = f.severity === "CRITICAL";
              return (
                <div
                  key={fid}
                  style={{
                    background: isCrit ? "var(--color-danger-soft)" : "var(--color-warning-soft)",
                    border: `1px solid ${isCrit ? "rgba(239, 68, 68, 0.3)" : "rgba(245, 158, 11, 0.3)"}`,
                    borderRadius: "6px",
                    padding: "10px 14px",
                    fontSize: "12px",
                  }}
                >
                  <strong style={{ color: isCrit ? "var(--color-danger)" : "var(--color-warning)" }}>
                    [{f.severity}] {f.title}:
                  </strong>{" "}
                  <span style={{ color: "var(--text-primary)" }}>
                    {cleanText(f.description || f.explanation || "Materiality review required.")}
                  </span>
                  {src.page && (
                    <span style={{ color: "var(--text-secondary)", marginLeft: 6 }}>
                      (Reference: Page {src.page})
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── 4. FINANCIAL PERFORMANCE CHART & YOY TREND VISUALIZER ── */}
      <div className="fd-card animate-fade-up report-section-break" style={{ padding: "20px 24px", marginBottom: "18px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", borderBottom: "1px solid var(--border-light)", paddingBottom: 8 }}>
          <h2 style={{ fontSize: "16px", color: "var(--text-primary)", fontWeight: 700, margin: 0 }}>
            Financial Performance & YoY Variance Comparison
          </h2>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>
            {previousPeriod} vs {currentPeriod}
          </span>
        </div>

        {/* Recharts Bar Chart */}
        {chartMetricsData.length > 0 && (
          <div style={{ marginBottom: 18, padding: "12px 14px", background: "var(--bg-main)", borderRadius: "8px", border: "1px solid var(--border-light)" }}>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: 10, letterSpacing: "0.04em" }}>
              Key Statement Line Items (₹ in {extractionResult?.unit || "Millions"})
            </div>
            <div style={{ height: "210px", width: "100%" }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartMetricsData} margin={{ top: 10, right: 10, left: 10, bottom: 15 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#64748B" }} interval={0} />
                  <YAxis tick={{ fontSize: 11, fill: "#64748B" }} tickFormatter={(val) => (Math.abs(val) >= 1000 ? `${(val / 1000).toFixed(0)}k` : val)} />
                  <Tooltip
                    contentStyle={{ borderRadius: "8px", border: "none", boxShadow: "0 4px 14px rgba(0,0,0,0.1)", fontSize: "12px" }}
                    formatter={(v) => `₹${fmt(v)}`}
                  />
                  <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "4px" }} />
                  <Bar dataKey="Previous" name={`Previous (${previousPeriod})`} fill="#94A3B8" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Current" name={`Current (${currentPeriod})`} fill="#10B981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Condensed Financial Metrics Table */}
        <div style={{ border: "1px solid var(--border-light)", borderRadius: "6px", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
            <thead>
              <tr style={{ background: "var(--bg-main)", borderBottom: "1px solid var(--border-light)" }}>
                <th style={{ padding: "8px 12px", fontSize: "10.5px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 700 }}>Metric</th>
                <th style={{ padding: "8px 12px", fontSize: "10.5px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "right", fontWeight: 700 }}>Previous ({previousPeriod})</th>
                <th style={{ padding: "8px 12px", fontSize: "10.5px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "right", fontWeight: 700 }}>Current ({currentPeriod})</th>
                <th style={{ padding: "8px 12px", fontSize: "10.5px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "right", fontWeight: 700 }}>Growth %</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(fm).map(([key, data], idx) => {
                const isPrevMissing = data.previous === null || data.previous === undefined;
                const isCurrMissing = data.current === null || data.current === undefined;
                const isEven = idx % 2 === 0;
                return (
                  <tr
                    key={key}
                    style={{
                      background: isEven ? "#FFFFFF" : "rgba(248, 250, 252, 0.7)",
                      borderBottom: idx < Object.keys(fm).length - 1 ? "1px solid var(--border-light)" : "none",
                    }}
                  >
                    <td style={{ padding: "8px 12px", fontWeight: 600, color: "var(--text-primary)", textTransform: "capitalize" }}>
                      {key.replace(/_/g, " ")}
                    </td>
                    <td style={{ padding: "8px 12px", textAlign: "right", color: "var(--text-secondary)", fontStyle: isPrevMissing ? "italic" : "normal", fontVariantNumeric: "tabular-nums" }}>
                      {isPrevMissing ? "Not available" : fmt(data.previous)}
                    </td>
                    <td style={{ padding: "8px 12px", textAlign: "right", color: isCurrMissing ? "var(--text-secondary)" : "var(--text-primary)", fontWeight: isCurrMissing ? 400 : 700, fontStyle: isCurrMissing ? "italic" : "normal", fontVariantNumeric: "tabular-nums" }}>
                      {isCurrMissing ? "Not available" : fmt(data.current)}
                    </td>
                    <td style={{ padding: "8px 12px", textAlign: "right", fontWeight: 600, color: data.growth_pct === null ? "var(--text-muted)" : data.growth_pct < 0 ? "var(--color-danger)" : "var(--color-success)" }}>
                      {fmtGrowth(data)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── 5. AUDIT OBSERVATIONS & CHECKS DISTRIBUTION (SIDE-BY-SIDE CHARTS) ── */}
      <div className="report-section-break" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "18px" }}>
        {/* Card A: Findings Distribution */}
        <div className="fd-card animate-fade-up" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "12px", borderBottom: "1px solid var(--border-light)", paddingBottom: 6 }}>
            Audit Findings Distribution ({findings.length})
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ width: 120, height: 120 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={findingsDonutData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={32}
                    outerRadius={55}
                    paddingAngle={3}
                  >
                    {findingsDonutData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(val, name) => [`${val} findings`, name]} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6, fontSize: "11.5px" }}>
              {[
                ["CRITICAL", fs.critical || 0, "#EF4444"],
                ["HIGH", fs.high || 0, "#F59E0B"],
                ["REVIEW", fs.review || 0, "#8B5CF6"],
                ["PASSED", fs.passed || 0, "#10B981"],
              ].map(([label, val, color]) => (
                <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-secondary)" }}>
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: color }} />
                    {label}
                  </span>
                  <strong style={{ color: "var(--text-primary)" }}>{val}</strong>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Card B: Overall Verification Checks Breakdown */}
        <div className="fd-card animate-fade-up" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "12px", borderBottom: "1px solid var(--border-light)", paddingBottom: 6 }}>
            WP-514 Checks Status ({totalChecks} Total)
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {/* Horizontal Stacked Bar */}
            <div style={{ height: "14px", width: "100%", borderRadius: "7px", overflow: "hidden", display: "flex", background: "#E2E8F0" }}>
              {checksDistData.map((item) => (
                <div
                  key={item.name}
                  style={{
                    height: "100%",
                    width: `${item.pct}%`,
                    background: item.color,
                    transition: "width 0.4s ease",
                  }}
                  title={`${item.name}: ${item.count} (${item.pct}%)`}
                />
              ))}
            </div>

            {/* Legend & Breakdown */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "11px", marginTop: 4 }}>
              {checksDistData.map((item) => (
                <div key={item.name} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--bg-main)", padding: "4px 8px", borderRadius: "4px" }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-secondary)" }}>
                    <span style={{ width: 7, height: 7, borderRadius: "2px", background: item.color }} />
                    {item.name}
                  </span>
                  <strong style={{ color: "var(--text-primary)" }}>{item.count} ({item.pct}%)</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── 6. AUDIT INTEGRITY CONTROLS CHART & GAUGES ── */}
      <div className="fd-card animate-fade-up report-section-break" style={{ padding: "20px 24px", marginBottom: "18px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", borderBottom: "1px solid var(--border-light)", paddingBottom: 8 }}>
          <h2 style={{ fontSize: "16px", color: "var(--text-primary)", fontWeight: 700, margin: 0 }}>
            Audit Integrity Controls Scorecard
          </h2>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>
            10 Automated Audit Procedures
          </span>
        </div>

        {/* Small Multi-Bar Chart for Integrity Controls */}
        <div style={{ height: "180px", width: "100%", marginBottom: "16px" }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={integrityBarData} margin={{ top: 10, right: 10, left: 10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#64748B" }} angle={-20} textAnchor="end" interval={0} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#64748B" }} />
              <Tooltip
                formatter={(val, name, props) => [`${props.payload.score} / 100`, props.payload.fullName]}
              />
              <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                {integrityBarData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Compact Grid of Integrity Controls */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          {integrityBarData.map((item) => (
            <div
              key={item.key}
              style={{
                background: "var(--bg-main)",
                border: "1px solid var(--border-light)",
                borderRadius: "6px",
                padding: "8px 12px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>
                {item.fullName}
              </span>
              <span
                style={{
                  fontSize: "12px",
                  fontWeight: 800,
                  color: item.color,
                  fontStyle: item.isNA ? "italic" : "normal",
                }}
              >
                {item.isNA ? "N/A (Not in filing)" : `${item.score} / 100`}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ── 7. FINANCIAL RATIO MATRIX (GROUPED BY CATEGORY) ── */}
      <div className="fd-card animate-fade-up report-section-break" style={{ padding: "20px 24px", marginBottom: "18px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", borderBottom: "1px solid var(--border-light)", paddingBottom: 8 }}>
          <h2 style={{ fontSize: "16px", color: "var(--text-primary)", fontWeight: 700, margin: 0 }}>
            Financial Ratio Matrix (Categorized Benchmarks)
          </h2>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>
            Liquidity • Solvency • Profitability • Efficiency
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Liquidity */}
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>
              1. Liquidity & Cash Flow Ratios
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
              {ratioGroups.liquidity.map((r) => (
                <RatioTile key={r.key} label={r.label} value={r.val} />
              ))}
            </div>
          </div>

          {/* Solvency */}
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>
              2. Solvency & Leverage Ratios
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
              {ratioGroups.solvency.map((r) => (
                <RatioTile key={r.key} label={r.label} value={r.val} />
              ))}
            </div>
          </div>

          {/* Profitability */}
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>
              3. Profitability & Margin Health
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
              {ratioGroups.profitability.map((r) => (
                <RatioTile key={r.key} label={r.label} value={r.val} />
              ))}
            </div>
          </div>

          {/* Efficiency */}
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>
              4. Operating Efficiency & Turnover
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
              {ratioGroups.efficiency.map((r) => (
                <RatioTile key={r.key} label={r.label} value={r.val} />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── 8. CONDENSED AUDIT FINDINGS TABLE ── */}
      <div className="fd-card animate-fade-up report-section-break" style={{ padding: "20px 24px", marginBottom: "18px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", borderBottom: "1px solid var(--border-light)", paddingBottom: 8 }}>
          <h2 style={{ fontSize: "16px", color: "var(--text-primary)", fontWeight: 700, margin: 0 }}>
            Audit Findings & Observations Summary
          </h2>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>
            {findings.length} Grounded Notes (Condensed)
          </span>
        </div>

        <div style={{ border: "1px solid var(--border-light)", borderRadius: "6px", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "11.5px" }}>
            <thead>
              <tr style={{ background: "var(--bg-main)", borderBottom: "1px solid var(--border-light)" }}>
                <th style={{ padding: "8px 10px", width: "90px", fontSize: "10.5px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 700 }}>Severity</th>
                <th style={{ padding: "8px 10px", width: "160px", fontSize: "10.5px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 700 }}>Category</th>
                <th style={{ padding: "8px 10px", fontSize: "10.5px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 700 }}>Finding & Note</th>
                <th style={{ padding: "8px 10px", width: "140px", fontSize: "10.5px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "right", fontWeight: 700 }}>Reference</th>
              </tr>
            </thead>
            <tbody>
              {condensedFindings.map((f, idx) => {
                const s = sev[f.severity] || sev.REVIEW;
                const isEven = idx % 2 === 0;
                const desc = cleanText(f.description || f.explanation || "Verified.");
                const src = f.source || f.source_ref || {};
                return (
                  <tr
                    key={f.id || idx}
                    style={{
                      background: isEven ? "#FFFFFF" : "rgba(248, 250, 252, 0.7)",
                      borderBottom: idx < condensedFindings.length - 1 ? "1px solid var(--border-light)" : "none",
                    }}
                  >
                    <td style={{ padding: "8px 10px", verticalAlign: "top" }}>
                      <span
                        style={{
                          fontSize: "10px",
                          fontWeight: 700,
                          padding: "2px 6px",
                          borderRadius: "4px",
                          background: s.bg,
                          color: s.color,
                          display: "inline-block",
                        }}
                      >
                        {f.severity}
                      </span>
                    </td>
                    <td style={{ padding: "8px 10px", verticalAlign: "top", fontWeight: 600, color: "var(--text-primary)", textTransform: "capitalize" }}>
                      {(f.category || "").replace(/_/g, " ")}
                    </td>
                    <td style={{ padding: "8px 10px", verticalAlign: "top", color: "var(--text-primary)" }}>
                      <strong style={{ display: "block", marginBottom: 2 }}>{f.title}</strong>
                      <span style={{ color: "var(--text-secondary)", lineHeight: 1.4 }}>{desc}</span>
                    </td>
                    <td style={{ padding: "8px 10px", verticalAlign: "top", textAlign: "right", color: "var(--text-muted)", fontSize: "10.5px" }}>
                      {src.page ? `Page ${src.page}` : src.note_ref ? src.note_ref : f.id}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── 9. APPENDIX: FULL WP-514 VERIFICATION WORKPAPER ── */}
      {analysisResult?.wp514 && (
        <div className="report-section-break" style={{ marginTop: "24px", paddingTop: "16px", borderTop: "2px dashed var(--border-light)" }}>
          <div style={{ marginBottom: "14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                DOCUMENT APPENDIX
              </div>
              <h2 style={{ fontSize: "16px", color: "var(--text-primary)", fontWeight: 700, margin: "2px 0 0" }}>
                Appendix: Comprehensive WP-514 Verification Matrix
              </h2>
            </div>
          </div>

          {/* Compact reference line — full entity/period/framework details are on page 1 */}
          <div style={{
            fontSize: "11px",
            color: "var(--text-secondary)",
            background: "var(--bg-main)",
            border: "1px solid var(--border-light)",
            borderRadius: "6px",
            padding: "7px 14px",
            marginBottom: "16px",
            fontStyle: "italic",
          }}>
            Appendix for <strong style={{ color: "var(--text-primary)", fontStyle: "normal" }}>WP-514 Financial Statement Review</strong> — see Executive Summary (page 1) for entity, period, framework, and compliance score details.
          </div>

          <WP514ReviewMatrix wp514Data={analysisResult.wp514} appendixMode={true} />
        </div>
      )}
      </div>

      <AuditReportPrint extractionResult={extractionResult} analysisResult={analysisResult} />
    </>
  );
}
