import React from "react";
import ScoreSeal from "./ScoreSeal.jsx";
import RatioTile from "./RatioTile.jsx";
import WP514ReviewMatrix from "./WP514ReviewMatrix.jsx";
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
} from "lucide-react";

const sev = {
  CRITICAL: { color: "var(--color-danger, #EF4444)", bg: "var(--color-danger-soft, #FEE2E2)", label: "Critical", Icon: AlertOctagon },
  HIGH:     { color: "var(--color-warning, #F59E0B)", bg: "var(--color-warning-soft, #FEF3C7)", label: "High", Icon: AlertTriangle },
  REVIEW:   { color: "var(--color-purple, #8B5CF6)", bg: "var(--color-purple-soft, #EDE9FE)", label: "Review", Icon: CircleAlert },
  PASSED:   { color: "var(--color-success, #10B981)", bg: "var(--color-success-soft, #D1FAE5)", label: "Passed", Icon: ShieldCheck },
};

const INTEGRITY_CONFIG = {
  mathematical_accuracy: { name: "Mathematical Accuracy", Icon: Calculator, desc: "Arithmetic consistency of financial statements" },
  cash_flow: { name: "Cash Flow Reconciliation", Icon: Coins, desc: "Opening/closing cash flow arithmetic check" },
  prior_year_tieout: { name: "Prior-Year Tie-Out", Icon: Repeat, desc: "Continuity of prior closing balances" },
  internal_consistency: { name: "Internal Consistency", Icon: Layers, desc: "Cross-statement line item reconciliation" },
  document_quality: { name: "Document & Narrative Quality", Icon: FileCheck2, desc: "Completeness & text extraction integrity" },
  analytical_comparison: { name: "Analytical Comparison", Icon: Activity, desc: "YoY variance analysis & trend validation" },
  ratios: { name: "Key Financial Ratios", Icon: Percent, desc: "Liquidity, solvency & efficiency metrics" },
  unusual_fluctuation: { name: "Unusual Fluctuations", Icon: TrendingUp, desc: "Outlier detection on line item movements" },
  unusual_gain: { name: "Unusual Gains & Divergence", Icon: Scale, desc: "Operating vs non-operating profit variance" },
  related_disclosure: { name: "Related Party Disclosures", Icon: FileSearch, desc: "Material related-party transaction checks" },
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

export default function AuditReport({ extractionResult, analysisResult, onBack }) {
  const fm = analysisResult?.financial_metrics || {};
  const fs = analysisResult?.findings_summary || {};
  const dq = extractionResult?.document_quality || {};
  const findings = analysisResult?.findings || [];
  const checks = analysisResult?.checks || {};

  const currentPeriod = extractionResult?.period?.current || extractionResult?.periods?.[0]?.period_key || "Current Period";
  const previousPeriod = extractionResult?.period?.previous || (extractionResult?.periods?.length > 1 ? extractionResult.periods[1].period_key : "Prior Period");

  const recommendedReview = findings.filter(
    (f) => f.severity === "CRITICAL" || f.severity === "HIGH"
  );

  // Total findings and checks breakdown
  const totalFindingsCount = (fs.critical || 0) + (fs.high || 0) + (fs.review || 0) + (fs.passed || 0);

  // Visual Comparison Chart Data
  const chartMetricsData = [
    { name: "Revenue", Previous: (fm.revenue?.previous && Math.abs(fm.revenue.previous) > 1) ? fm.revenue.previous : 0, Current: fm.revenue?.current || 0 },
    { name: "Expenses", Previous: (fm.expenses?.previous && Math.abs(fm.expenses.previous) > 1) ? fm.expenses.previous : 0, Current: fm.expenses?.current || 0 },
    { name: "Gross Profit", Previous: (fm.gross_profit?.previous && Math.abs(fm.gross_profit.previous) > 1) ? fm.gross_profit.previous : 0, Current: fm.gross_profit?.current || 0 },
    { name: "Operating Profit", Previous: (fm.operating_profit?.previous && Math.abs(fm.operating_profit.previous) > 1) ? fm.operating_profit.previous : 0, Current: fm.operating_profit?.current || 0 },
    { name: "Net Profit", Previous: (fm.net_profit?.previous && Math.abs(fm.net_profit.previous) > 1) ? fm.net_profit.previous : 0, Current: fm.net_profit?.current || 0 },
    { name: "Assets", Previous: (fm.assets?.previous && Math.abs(fm.assets.previous) > 1) ? fm.assets.previous : 0, Current: fm.assets?.current || 0 },
    { name: "Liabilities", Previous: (fm.liabilities?.previous && Math.abs(fm.liabilities.previous) > 1) ? fm.liabilities.previous : 0, Current: fm.liabilities?.current || 0 },
    { name: "Equity", Previous: (fm.equity?.previous && Math.abs(fm.equity.previous) > 1) ? fm.equity.previous : 0, Current: fm.equity?.current || 0 },
  ].filter(item => item.Current !== 0 || item.Previous !== 0);

  return (
    <div
      className="audit-report-container"
      style={{
        background: "var(--bg-main, #F8FAFC)",
        minHeight: "100vh",
        color: "var(--text-primary, #0F172A)",
        padding: "36px 48px",
        maxWidth: 1160,
        margin: "0 auto",
      }}
    >
      <style>{`
        @media print {
          body {
            background: #FFFFFF !important;
            color: #0F172A !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          .audit-report-container {
            background: #FFFFFF !important;
            padding: 0 !important;
            max-width: 100% !important;
            margin: 0 !important;
          }
          .no-print {
            display: none !important;
          }
          .fd-card {
            box-shadow: none !important;
            border: 1px solid #CBD5E1 !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            margin-bottom: 20px !important;
          }
          table, tr, td, th {
            page-break-inside: avoid !important;
            break-inside: avoid !important;
          }
          .report-page-break {
            page-break-before: always !important;
            break-before: page !important;
          }
        }
      `}</style>

      {/* ── Action Bar (Screen Only) ── */}
      <div
        className="no-print"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 28,
          paddingBottom: 16,
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
            onClick={() => window.print()}
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

      {/* ── 1. Executive Title & Compliance Seal Card ── */}
      <div
        className="fd-card animate-fade-up"
        style={{
          padding: "26px 32px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 28,
          background: "linear-gradient(135deg, rgba(236, 253, 245, 0.85) 0%, #FFFFFF 50%, rgba(240, 253, 244, 0.7) 100%)",
          borderLeft: "6px solid var(--color-primary, #059669)",
          borderTop: "1px solid rgba(16, 185, 129, 0.25)",
          borderRight: "1px solid rgba(16, 185, 129, 0.2)",
          borderBottom: "1px solid rgba(16, 185, 129, 0.2)",
          boxShadow: "0 8px 24px -4px rgba(16, 185, 129, 0.12), 0 2px 6px rgba(0, 0, 0, 0.02)",
        }}
      >
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
            <ShieldCheck size={14} /> FINANCIAL AUDIT ASSURANCE REPORT · {extractionResult?.document_id || "DOC-ID"}
          </div>
          <h1
            style={{
              fontSize: "26px",
              margin: "6px 0 8px",
              fontWeight: 800,
              color: "var(--text-primary, #0F172A)",
            }}
          >
            {extractionResult?.company?.name || extractionResult?.file_name || "Financial Statement Audit"}
          </h1>
          <div style={{ fontSize: "13px", color: "var(--text-secondary, #64748B)", display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "center" }}>
            <span>
              Period: <strong style={{ color: "var(--text-primary)" }}>{currentPeriod}</strong>
              {previousPeriod ? ` vs ${previousPeriod}` : ""}
            </span>
            <span>•</span>
            <span>
              Unit & Currency: <strong style={{ color: "var(--text-primary)" }}>{extractionResult?.currency || "INR"} in {extractionResult?.unit || "Millions"}</strong>
            </span>
            <span>•</span>
            <span>
              Framework: <strong style={{ color: "var(--text-primary)" }}>{extractionResult?.reporting_framework || "Ind AS / IFRS"}</strong>
            </span>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <ScoreSeal score={analysisResult?.overall_score} />
        </div>
      </div>

      {/* ── 2. Executive Summary & Findings Quality Status ── */}
      <div className="fd-card animate-fade-up" style={{ padding: "24px 28px", marginBottom: 28 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: 8 }}>
          <h2 style={{ fontSize: "17px", color: "var(--text-primary)", fontWeight: 700, margin: 0 }}>
            1. Executive Summary & Audit Distribution
          </h2>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>
            {totalFindingsCount} Total Observations
          </span>
        </div>

        {dq.data_quality_status && dq.data_quality_status !== "EXCELLENT" && (
          <div
            style={{
              background: dq.data_quality_status === "INSUFFICIENT" ? "var(--color-danger-soft)" : "var(--color-warning-soft)",
              border: `1px solid ${dq.data_quality_status === "INSUFFICIENT" ? "var(--color-danger)" : "var(--color-warning)"}`,
              borderRadius: "8px",
              padding: "14px 18px",
              marginBottom: 16,
              display: "flex",
              alignItems: "center",
              gap: 12,
            }}
          >
            <AlertTriangle size={20} color={dq.data_quality_status === "INSUFFICIENT" ? "var(--color-danger)" : "var(--color-warning)"} />
            <div>
              <span style={{ fontWeight: 700, color: dq.data_quality_status === "INSUFFICIENT" ? "var(--color-danger)" : "var(--color-warning)" }}>
                {dq.data_quality_status} Extraction Quality:{" "}
              </span>
              <span style={{ color: "var(--text-primary)" }}>Document completeness is at {dq.extraction_completeness_pct}%.</span>
              {dq.missing_sections && dq.missing_sections.length > 0 && (
                <span style={{ color: "var(--text-secondary)", marginLeft: 8 }}>
                  Missing sections: {dq.missing_sections.join(", ")}
                </span>
              )}
            </div>
          </div>
        )}

        {dq.unit_mismatch_detected && (
          <div
            style={{
              background: "var(--color-warning-soft)",
              border: "1px solid var(--color-warning)",
              borderRadius: "8px",
              padding: "12px 18px",
              marginBottom: 16,
              display: "flex",
              alignItems: "center",
              gap: 12,
            }}
          >
            <AlertTriangle size={18} color="var(--color-warning)" />
            <div>
              <span style={{ fontWeight: 700, color: "var(--color-warning)" }}>Unit Mismatch Detected: </span>
              <span style={{ color: "var(--text-primary)" }}>
                {dq.unit_mismatch_detail || "Units between periods require normalization review."}
              </span>
            </div>
          </div>
        )}

        {/* 4 Summary Stat Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
          {[
            ["CRITICAL", fs.critical || 0, "var(--color-danger)", "var(--color-danger-soft)", AlertOctagon],
            ["HIGH", fs.high || 0, "var(--color-warning)", "var(--color-warning-soft)", AlertTriangle],
            ["REVIEW", fs.review || 0, "var(--color-purple)", "var(--color-purple-soft)", CircleAlert],
            ["PASSED", fs.passed || 0, "var(--color-success)", "var(--color-success-soft)", ShieldCheck],
          ].map(([k, v, color, bg, Icon]) => (
            <div
              key={k}
              className="interactive-card hover-scale"
              style={{
                background: "var(--bg-main)",
                border: "1px solid var(--border-light)",
                borderRadius: "10px",
                padding: "16px",
                textAlign: "center",
                borderTop: `3px solid ${color}`,
              }}
            >
              <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 6, marginBottom: 6 }}>
                <Icon size={16} color={color} />
                <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  {k}
                </span>
              </div>
              <div style={{ fontSize: "24px", fontWeight: 800, color: color }}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── 3. Visual Financial Metrics Comparison (Chart + Table) ── */}
      <div className="fd-card animate-fade-up" style={{ padding: "24px 28px", marginBottom: 28 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: 8 }}>
          <h2 style={{ fontSize: "17px", color: "var(--text-primary)", fontWeight: 700, margin: 0 }}>
            2. Financial Performance & YoY Trend Visualizer
          </h2>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>
            {previousPeriod} vs {currentPeriod}
          </span>
        </div>

        {/* Graphical Bar Comparison Chart */}
        {chartMetricsData.length > 0 && (
          <div style={{ marginBottom: 24, padding: "16px", background: "var(--bg-main)", borderRadius: "10px", border: "1px solid var(--border-light)" }}>
            <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: 12, letterSpacing: "0.04em" }}>
              Key Financial Line Items Comparison (₹ in {extractionResult?.unit || "Millions"})
            </div>
            <div style={{ height: "240px", width: "100%" }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartMetricsData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#64748B" }} interval={0} angle={-15} textAnchor="end" />
                  <YAxis tick={{ fontSize: 11, fill: "#64748B" }} tickFormatter={(val) => (Math.abs(val) >= 1000 ? `${(val / 1000).toFixed(0)}k` : val)} />
                  <Tooltip
                    contentStyle={{ borderRadius: "8px", border: "none", boxShadow: "0 4px 14px rgba(0,0,0,0.1)", fontSize: "12px" }}
                    formatter={(v) => `₹${fmt(v)}`}
                  />
                  <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }} />
                  <Bar dataKey="Previous" name={`Previous (${previousPeriod})`} fill="#94A3B8" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Current" name={`Current (${currentPeriod})`} fill="#10B981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Financial Metrics Comparison Table */}
        <div style={{ border: "1px solid var(--border-light)", borderRadius: "8px", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
            <thead>
              <tr style={{ background: "var(--bg-main)", borderBottom: "1px solid var(--border-light)" }}>
                <th style={{ padding: "10px 14px", fontSize: "11px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 700 }}>Metric</th>
                <th style={{ padding: "10px 14px", fontSize: "11px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "right", fontWeight: 700 }}>Previous ({previousPeriod})</th>
                <th style={{ padding: "10px 14px", fontSize: "11px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "right", fontWeight: 700 }}>Current ({currentPeriod})</th>
                <th style={{ padding: "10px 14px", fontSize: "11px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "right", fontWeight: 700 }}>Growth %</th>
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
                    <td style={{ padding: "10px 14px", fontSize: "12px", textTransform: "capitalize", color: "var(--text-primary)", fontWeight: 600 }}>
                      {key.replace(/_/g, " ")}
                    </td>
                    <td style={{ padding: "10px 14px", fontSize: "12px", textAlign: "right", color: "var(--text-secondary)", fontStyle: isPrevMissing ? "italic" : "normal", fontVariantNumeric: "tabular-nums" }}>
                      {isPrevMissing ? "Not available" : fmt(data.previous)}
                    </td>
                    <td style={{ padding: "10px 14px", fontSize: "12px", textAlign: "right", color: isCurrMissing ? "var(--text-secondary)" : "var(--text-primary)", fontWeight: isCurrMissing ? 400 : 700, fontStyle: isCurrMissing ? "italic" : "normal", fontVariantNumeric: "tabular-nums" }}>
                      {isCurrMissing ? "Not available" : fmt(data.current)}
                    </td>
                    <td style={{ padding: "10px 14px", fontSize: "12px", textAlign: "right", fontWeight: 600, color: data.growth_pct === null ? "var(--text-muted)" : data.growth_pct < 0 ? "var(--color-danger)" : "var(--color-success)" }}>
                      {fmtGrowth(data)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── 4. Audit Integrity Controls Health Matrix ── */}
      <div className="fd-card animate-fade-up" style={{ padding: "24px 28px", marginBottom: 28 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: 8 }}>
          <h2 style={{ fontSize: "17px", color: "var(--text-primary)", fontWeight: 700, margin: 0 }}>
            3. Audit Integrity Controls & Compliance Health
          </h2>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>
            Engine v{analysisResult?.score_formula_version || "2.0.0"}
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          {Object.entries(checks).filter(([, val]) => val !== null && val !== undefined).map(([key, val]) => {
            const num = Number(val);
            const isNA = val === "NOT_AVAILABLE" || (key === "related_disclosure" && num === 0);
            const config = INTEGRITY_CONFIG[key] || { name: key.replace(/_/g, " "), Icon: Activity, desc: "Automated integrity verification" };
            const Icon = config.Icon;
            const healthColor = isNA ? "#94A3B8" : num >= 80 ? "#10B981" : num >= 50 ? "#F59E0B" : "#EF4444";
            const healthBg = isNA ? "rgba(100, 116, 139, 0.08)" : num >= 80 ? "rgba(16, 185, 129, 0.1)" : num >= 50 ? "rgba(245, 158, 11, 0.1)" : "rgba(239, 68, 68, 0.1)";

            return (
              <div
                key={key}
                className="interactive-card hover-scale"
                style={{
                  background: "var(--bg-main)",
                  border: "1px solid var(--border-light)",
                  borderRadius: "10px",
                  padding: "12px 16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                  pageBreakInside: "avoid",
                  breakInside: "avoid",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ width: 28, height: 28, borderRadius: "6px", background: healthBg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <Icon size={14} color={healthColor} />
                    </div>
                    <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                      {config.name}
                    </span>
                  </div>
                  <span
                    style={{
                      fontSize: "12px",
                      fontWeight: 800,
                      color: healthColor,
                      fontStyle: isNA ? "italic" : "normal",
                    }}
                  >
                    {isNA ? "N/A (Not in filing)" : `${num.toFixed(0)} / 100`}
                  </span>
                </div>

                {/* Progress bar */}
                <div style={{ height: "4px", width: "100%", background: "#E2E8F0", borderRadius: "2px", overflow: "hidden" }}>
                  <div
                    style={{
                      height: "100%",
                      width: isNA ? "0%" : `${Math.min(100, Math.max(0, num))}%`,
                      background: healthColor,
                      borderRadius: "2px",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── 5. Financial Ratio Matrix ── */}
      <div className="fd-card animate-fade-up" style={{ padding: "24px 28px", marginBottom: 28 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: 8 }}>
          <h2 style={{ fontSize: "17px", color: "var(--text-primary)", fontWeight: 700, margin: 0 }}>
            4. Financial Ratio Matrix & Health Benchmarks
          </h2>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>
            Liquidity, Solvency, Profitability & Efficiency
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
          {Object.entries(analysisResult?.ratios || {}).map(([key, val]) => (
            <RatioTile
              key={key}
              label={key.replace(/_pct$/, "").replace(/_/g, " ")}
              value={val === null || val === undefined ? "Not available" : key.endsWith("_pct") ? `${Number(val).toFixed(2)}%` : val}
            />
          ))}
        </div>
      </div>

      {/* ── 6. Detailed Findings & Audit Observations ── */}
      <div className="fd-card animate-fade-up" style={{ padding: "24px 28px", marginBottom: 28 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: 8 }}>
          <h2 style={{ fontSize: "17px", color: "var(--text-primary)", fontWeight: 700, margin: 0 }}>
            5. Detailed Audit Findings & Grounded Observations
          </h2>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>
            {findings.length} Verification Notes
          </span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {findings.map((f, i) => {
            const s = sev[f.severity] || sev.REVIEW;
            const Icon = s.Icon;
            const fid = f.id || f.finding_id || `FINDING-${i}`;
            const desc = cleanText(f.description || f.explanation || "No description provided.");
            const src = f.source || f.source_ref || {};
            return (
              <div
                key={fid}
                style={{
                  background: "var(--bg-main)",
                  border: "1px solid var(--border-light)",
                  borderRadius: "8px",
                  padding: "14px 18px",
                  pageBreakInside: "avoid",
                  breakInside: "avoid",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ width: 22, height: 22, borderRadius: "5px", background: s.bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <Icon size={13} color={s.color} strokeWidth={2.2} />
                    </span>
                    <span style={{ fontSize: "11px", color: s.color, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      {s.label} · {(f.category || "").replace(/_/g, " ")}
                    </span>
                  </div>
                  <span style={{ fontSize: "10px", fontFamily: "monospace", color: "var(--text-muted)" }}>
                    {fid}
                  </span>
                </div>

                <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>
                  {f.title}
                </div>

                <p style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: 1.5, margin: "0 0 8px" }}>
                  {desc}
                </p>

                {(src.file || src.page || src.note_ref) && (
                  <div style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>
                    Verified Reference: {src.file ? `${src.file} ` : ""}{src.page ? `(Page ${src.page})` : ""}{src.note_ref ? ` [${src.note_ref}]` : ""}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── 7. WP-514 Financial Statement Review Matrix ── */}
      {analysisResult?.wp514 && (
        <div style={{ marginBottom: 28, pageBreakInside: "avoid", breakInside: "avoid" }}>
          <WP514ReviewMatrix wp514Data={analysisResult.wp514} />
        </div>
      )}

      {/* ── 8. Recommended Action & Review Areas ── */}
      <div className="fd-card animate-fade-up" style={{ padding: "24px 28px", pageBreakInside: "avoid", breakInside: "avoid" }}>
        <h2 style={{ fontSize: "17px", color: "var(--text-primary)", fontWeight: 700, marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: 8 }}>
          7. Recommended Action & Materiality Review Areas
        </h2>
        {recommendedReview.length === 0 ? (
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--color-success)", fontSize: "13px", fontWeight: 600, background: "var(--color-success-soft)", padding: "12px 16px", borderRadius: "8px" }}>
            <CheckCircle2 size={16} /> All core audit verification criteria passed within acceptable tolerance thresholds.
          </div>
        ) : (
          <ul style={{ margin: 0, paddingLeft: 20, display: "flex", flexDirection: "column", gap: 10 }}>
            {recommendedReview.map((f, i) => {
              const fid = f.id || f.finding_id || `REC-${i}`;
              const src = f.source || f.source_ref || {};
              return (
                <li key={fid} style={{ fontSize: "13px", color: "var(--text-primary)", lineHeight: 1.5 }}>
                  <strong style={{ color: f.severity === "CRITICAL" ? "var(--color-danger)" : "var(--color-warning)" }}>
                    [{f.severity}] {f.title}:
                  </strong>{" "}
                  {cleanText(f.description || f.explanation || "Materiality review required.")}
                  {src.page && ` (Reference: Page ${src.page})`}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
