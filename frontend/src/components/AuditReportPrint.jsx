import React from "react";

const RATIO_NIF_REASONS = {
  cash_ratio: "Cash and Bank Balances not separately disclosed as a line item",
  interest_coverage_ratio: "Finance Costs (Interest Expense) not disclosed as a distinct line item",
  asset_turnover_ratio: "Total Assets not separately available for the comparison period",
  days_sales_outstanding: "Trade Receivables (Accounts Receivable) not disclosed in the filing",
  inventory_turnover_ratio: "Inventory / Stock-in-Trade not reported as a separate line item",
  receivables_turnover_ratio: "Trade Receivables not separately available for ratio computation",
  net_margin_pct: "Net Profit not available or insufficient data for margin calculation",
  debt_to_equity: "Total Borrowings or Equity details incomplete for leverage computation",
  debt_ratio: "Total Debt or Total Assets not explicitly segregated",
  current_ratio: "Current Assets or Current Liabilities not disclosed",
  quick_ratio: "Liquid assets or inventory breakdown not provided in filing",
  gross_profit_margin_pct: "Gross Profit or Revenue not disclosed",
  operating_margin_pct: "Operating Profit line item not separately reported",
  return_on_assets_pct: "Asset balance unavailable for average asset base calculation",
  roe_pct: "Shareholder equity reconciliation not fully available",
};

const fmt = (n) => (n === null || n === undefined ? "" : n.toLocaleString("en-IN"));
const pct = (n) => (n === null || n === undefined ? "" : `${n > 0 ? "+" : ""}${Number(n).toFixed(2)}%`);

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

const formatCheckValue = (val, checkName = "") => {
  if (val === null || val === undefined || val === "") return "";
  let str = String(val).trim();
  if (!str) return "";

  const isMargin = /margin/i.test(checkName);

  if (isMargin) {
    str = str.replace(/[₹$]/g, "").replace(/\s*(Millions|Cr|Crores|Billion|M)\b/gi, "").trim();
    const match = str.match(/[-+]?\d*\.?\d+/);
    if (match) {
      const num = parseFloat(match[0]);
      if (!isNaN(num)) {
        return `${num.toFixed(2)}%`;
      }
    }
  }

  const currencyMatch = str.match(/^([+-]?[₹$]?-?)\s*([-+]?\d+(?:\.\d+)?)\s*(.*)$/);
  if (currencyMatch) {
    const rawPrefix = currencyMatch[1] || "";
    const num = parseFloat(currencyMatch[2]);
    const suffix = currencyMatch[3] ? ` ${currencyMatch[3].trim()}` : "";
    if (!isNaN(num)) {
      const isNegative = num < 0 || rawPrefix.includes("-");
      const absVal = Math.abs(num);
      const isWhole = absVal === Math.floor(absVal);
      const formattedNum = isWhole 
        ? absVal.toLocaleString("en-IN") 
        : absVal.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      const sign = isNegative ? "-" : (rawPrefix.includes("+") ? "+" : "");
      const sym = rawPrefix.replace(/[-+]/g, "");
      return `${sign}${sym}${formattedNum}${suffix}`.trim();
    }
  }

  return str;
};

export default function AuditReportPrint({ extractionResult, analysisResult }) {
  const fm = analysisResult?.financial_metrics || {};
  const findings = analysisResult?.findings || [];
  const wp514 = analysisResult?.wp514 || {};
  const ratios = analysisResult?.ratios || {};
  const wp514Overall = wp514.overall || {};
  const categories = wp514.categories || [];
  const allChecks = wp514.checks || [];

  const currentPeriod = extractionResult?.period?.current || extractionResult?.periods?.[0]?.period_key || "Current Period";
  const previousPeriod = extractionResult?.period?.previous || (extractionResult?.periods?.length > 1 ? extractionResult.periods[1].period_key : "Prior Period");

  const totalChecks = wp514Overall.total_checks ?? allChecks.length;
  const passedChecks = wp514Overall.passed ?? 0;
  const reviewRequiredChecks = wp514Overall.review ?? 0;
  const failedChecks = wp514Overall.failed ?? 0;
  const notInFilingChecks = wp514Overall.not_available ?? (totalChecks - passedChecks - reviewRequiredChecks - failedChecks);
  const overallScore = wp514Overall.score ?? analysisResult?.overall_score ?? 0;

  const entityName = extractionResult?.company?.name || extractionResult?.file_name || "Audited Entity";
  const docRef = extractionResult?.document_id || "DOC-20260820-001";
  const genTimestamp = formatDateTime();

  // Categorized Ratios List
  const ratioGroups = [
    {
      group: "Liquidity & Cash Flow Ratios",
      items: [
        { key: "current_ratio", label: "Current Ratio", value: ratios.current_ratio },
        { key: "quick_ratio", label: "Quick Ratio", value: ratios.quick_ratio },
        { key: "cash_ratio", label: "Cash Ratio", value: ratios.cash_ratio },
      ],
    },
    {
      group: "Solvency & Leverage Ratios",
      items: [
        { key: "debt_to_equity", label: "Debt to Equity", value: ratios.debt_to_equity },
        { key: "debt_ratio", label: "Debt Ratio", value: ratios.debt_ratio },
        { key: "interest_coverage_ratio", label: "Interest Coverage Ratio", value: ratios.interest_coverage_ratio },
      ],
    },
    {
      group: "Profitability & Margin Health",
      items: [
        { key: "gross_profit_margin_pct", label: "Gross Profit Margin", value: ratios.gross_profit_margin_pct ? `${ratios.gross_profit_margin_pct}%` : null },
        { key: "operating_margin_pct", label: "Operating Margin", value: ratios.operating_margin_pct ? `${ratios.operating_margin_pct}%` : null },
        { key: "net_margin_pct", label: "Net Margin", value: ratios.net_margin_pct ? `${ratios.net_margin_pct}%` : null },
        { key: "return_on_assets_pct", label: "Return on Assets (ROA)", value: ratios.return_on_assets_pct ? `${ratios.return_on_assets_pct}%` : null },
        { key: "roe_pct", label: "Return on Equity (ROE)", value: ratios.roe_pct ? `${ratios.roe_pct}%` : null },
      ],
    },
    {
      group: "Operating Efficiency & Turnover",
      items: [
        { key: "asset_turnover_ratio", label: "Asset Turnover Ratio", value: ratios.asset_turnover_ratio },
        { key: "receivables_turnover_ratio", label: "Receivables Turnover Ratio", value: ratios.receivables_turnover_ratio },
        { key: "days_sales_outstanding", label: "Days Sales Outstanding (DSO)", value: ratios.days_sales_outstanding },
        { key: "inventory_turnover_ratio", label: "Inventory Turnover Ratio", value: ratios.inventory_turnover_ratio },
      ],
    },
  ];

  return (
    <div className="print-document-root">
      <style>{`
        /* Screen: Hide completely */
        .print-document-root {
          display: none;
        }

        @media print {
          /* Suppress interactive screen container */
          .audit-report-container {
            display: none !important;
          }
          .no-print {
            display: none !important;
          }

          /* Display formal print document */
          .print-document-root {
            display: block !important;
            background: #FFFFFF !important;
            color: #1E293B !important;
            font-family: Georgia, "Times New Roman", Times, serif !important;
            font-size: 10pt !important;
            line-height: 1.5 !important;
            margin: 0 !important;
            padding: 0 !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }

          @page {
            size: A4 portrait;
            margin: 18mm 16mm 18mm 16mm;
          }

          .print-page-break {
            page-break-before: always !important;
            break-before: page !important;
          }

          .print-avoid-break {
            page-break-inside: avoid !important;
            break-inside: avoid !important;
          }

          .print-header {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 8pt;
            color: #64748B;
            border-bottom: 1px solid #CBD5E1;
            padding-bottom: 4px;
            margin-bottom: 14px;
            display: flex;
            justify-content: space-between;
          }

          .print-footer {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 8pt;
            color: #94A3B8;
            border-top: 1px solid #E2E8F0;
            padding-top: 4px;
            margin-top: 18px;
            display: flex;
            justify-content: space-between;
          }

          /* Formal Tables */
          table.print-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
            margin-bottom: 14px;
            font-size: 9pt;
          }
          table.print-table th {
            font-family: Arial, Helvetica, sans-serif;
            background-color: #F1F5F9;
            color: #0F172A;
            font-weight: 700;
            text-align: left;
            padding: 6px 8px;
            border: 1px solid #CBD5E1;
            font-size: 8.5pt;
            text-transform: uppercase;
            letter-spacing: 0.03em;
          }
          table.print-table td {
            padding: 5px 8px;
            border: 1px solid #E2E8F0;
            vertical-align: top;
          }
          table.print-table tr:nth-child(even) td {
            background-color: #F8FAFC;
          }

          h1.print-title {
            font-family: Georgia, serif;
            font-size: 20pt;
            color: #0F172A;
            margin: 0 0 6px 0;
            font-weight: 700;
          }
          h2.print-sec-heading {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 13pt;
            font-weight: 800;
            color: #0F172A;
            border-bottom: 1.5px solid #0F172A;
            padding-bottom: 4px;
            margin-top: 20px;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
          }
          h3.print-subsec-heading {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 10.5pt;
            font-weight: 700;
            color: #1E293B;
            margin-top: 14px;
            margin-bottom: 6px;
          }

          .status-tag {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 8pt;
            font-weight: 700;
            display: inline-block;
            padding: 1px 5px;
            border-radius: 3px;
            text-transform: uppercase;
          }
          .status-passed { color: #047857; background: #D1FAE5; }
          .status-review { color: #B45309; background: #FEF3C7; }
          .status-failed { color: #B91C1C; background: #FEE2E2; }
          .status-na { color: #475569; background: #F1F5F9; }
        }
      `}</style>

      {/* ────────────────────────────────────────────────────────────
          COVER PAGE
          ──────────────────────────────────────────────────────────── */}
      <div className="print-cover-page" style={{ minHeight: "92vh", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
        <div>
          <div style={{ borderBottom: "3px solid #047857", paddingBottom: 16, marginBottom: 24 }}>
            <div style={{ fontFamily: "Arial, sans-serif", fontSize: "10pt", fontWeight: 800, color: "#047857", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>
              WP-514 Standardized Financial Statement Review
            </div>
            <h1 className="print-title" style={{ fontSize: "24pt", lineHeight: 1.2 }}>
              Independent Financial Audit &amp; Compliance Assurance Report
            </h1>
            <div style={{ fontFamily: "Arial, sans-serif", fontSize: "12pt", color: "#475569", marginTop: 6, fontWeight: 600 }}>
              {entityName}
            </div>
          </div>

          <div style={{ marginTop: 24, marginBottom: 24 }}>
            <table className="print-table" style={{ fontSize: "10pt" }}>
              <tbody>
                <tr>
                  <td style={{ width: "30%", fontWeight: 700, background: "#F8FAFC", fontFamily: "Arial, sans-serif" }}>Audit Subject Entity</td>
                  <td style={{ fontWeight: 700 }}>{entityName}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 700, background: "#F8FAFC", fontFamily: "Arial, sans-serif" }}>Review Period / Financial Year</td>
                  <td>{currentPeriod} {previousPeriod ? `(Comparative: ${previousPeriod})` : ""}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 700, background: "#F8FAFC", fontFamily: "Arial, sans-serif" }}>Accounting Framework</td>
                  <td>{extractionResult?.reporting_framework || "Ind AS / IFRS Compliant"}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 700, background: "#F8FAFC", fontFamily: "Arial, sans-serif" }}>Reporting Scale &amp; Currency</td>
                  <td>{extractionResult?.currency || "INR"} in {extractionResult?.unit || "Millions"} ({extractionResult?.is_consolidated ? "Consolidated" : "Standalone"})</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 700, background: "#F8FAFC", fontFamily: "Arial, sans-serif" }}>Audit Document Reference</td>
                  <td style={{ fontFamily: "Courier, monospace" }}>{docRef}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 700, background: "#F8FAFC", fontFamily: "Arial, sans-serif" }}>Report Execution Timestamp</td>
                  <td>{genTimestamp}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 700, background: "#F8FAFC", fontFamily: "Arial, sans-serif" }}>Audit Engine Specification</td>
                  <td>v{analysisResult?.score_formula_version || "2.0.0"} (Deterministic WP-514 Verification Rules)</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div style={{ marginTop: 20, padding: "16px 20px", border: "1.5px solid #CBD5E1", borderRadius: 4, background: "#F8FAFC" }}>
            <div style={{ fontFamily: "Arial, sans-serif", fontSize: "11pt", fontWeight: 800, color: "#0F172A", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.04em" }}>
              Executive Compliance Rating Summary
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: "28pt", fontWeight: 800, color: overallScore >= 75 ? "#047857" : overallScore >= 50 ? "#B45309" : "#B91C1C", fontFamily: "Arial, sans-serif" }}>
                  {typeof overallScore === "number" ? overallScore.toFixed(1) : overallScore} <span style={{ fontSize: "14pt", color: "#64748B", fontWeight: 500 }}>/ 100</span>
                </div>
                <div style={{ fontSize: "9.5pt", color: "#475569", marginTop: 2 }}>
                  Standard WP-514 Composite Index
                </div>
              </div>
              <div style={{ textAlign: "right", fontFamily: "Arial, sans-serif", fontSize: "9pt", lineHeight: 1.6 }}>
                <div>Total Verification Procedures: <strong>{totalChecks}</strong></div>
                <div>Passed within Tolerance: <strong style={{ color: "#047857" }}>{passedChecks}</strong></div>
                <div>Review Required / Caveats: <strong style={{ color: "#B45309" }}>{reviewRequiredChecks}</strong></div>
                <div>Failed Validations: <strong style={{ color: "#B91C1C" }}>{failedChecks}</strong></div>
                <div>Not in Filing Disclosures: <strong style={{ color: "#64748B" }}>{notInFilingChecks}</strong></div>
              </div>
            </div>
          </div>
        </div>

        <div style={{ borderTop: "1px solid #CBD5E1", paddingTop: 12, fontSize: "8pt", color: "#64748B", fontFamily: "Arial, sans-serif" }}>
          <div><strong>Notice &amp; Confidentiality:</strong> This audit report has been automatically compiled by the WP-514 Continuous Assurance Engine from verified document extractions. Information presented herein is grounded exclusively in disclosures extracted from filed statements.</div>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          TABLE OF CONTENTS
          ──────────────────────────────────────────────────────────── */}
      <div className="print-page-break">
        <div className="print-header">
          <span>WP-514 Financial Statement Review — {entityName}</span>
          <span>Doc Ref: {docRef}</span>
        </div>

        <h2 className="print-sec-heading">Table of Contents</h2>
        
        <table className="print-table" style={{ marginTop: 16 }}>
          <thead>
            <tr>
              <th style={{ width: "12%" }}>Section</th>
              <th>Document Section Title</th>
              <th style={{ width: "25%", textAlign: "right" }}>Scope / Content</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ fontWeight: 700, fontFamily: "Arial, sans-serif" }}>1.0</td>
              <td><strong>Executive Summary &amp; Recommended Actions</strong></td>
              <td style={{ textAlign: "right", color: "#64748B" }}>Core Findings &amp; Statistics</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 700, fontFamily: "Arial, sans-serif" }}>2.0</td>
              <td><strong>Financial Performance &amp; Line-Item Variance</strong></td>
              <td style={{ textAlign: "right", color: "#64748B" }}>YoY Variance Statement</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 700, fontFamily: "Arial, sans-serif" }}>3.0</td>
              <td><strong>Audit Integrity Controls Scorecard &amp; Category Breakdown</strong></td>
              <td style={{ textAlign: "right", color: "#64748B" }}>10 Core Audit Domains</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 700, fontFamily: "Arial, sans-serif" }}>4.0</td>
              <td><strong>Financial Ratio Matrix &amp; Non-Disclosure Notes</strong></td>
              <td style={{ textAlign: "right", color: "#64748B" }}>Liquidity, Leverage, Margins</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 700, fontFamily: "Arial, sans-serif" }}>5.0</td>
              <td><strong>Complete Findings &amp; Observations Register</strong></td>
              <td style={{ textAlign: "right", color: "#64748B" }}>Exhaustive Findings Trail</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 700, fontFamily: "Arial, sans-serif" }}>6.0</td>
              <td><strong>Comprehensive WP-514 Verification Workpaper (Master Appendix)</strong></td>
              <td style={{ textAlign: "right", color: "#64748B" }}>All 62 Individual Checks</td>
            </tr>
          </tbody>
        </table>

        <div className="print-footer">
          <span>CONFIDENTIAL — FOR INTERNAL USE ONLY</span>
          <span>Generated: {genTimestamp}</span>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          SECTION 1: EXECUTIVE SUMMARY
          ──────────────────────────────────────────────────────────── */}
      <div className="print-page-break">
        <div className="print-header">
          <span>WP-514 Financial Statement Review — {entityName}</span>
          <span>Section 1: Executive Summary</span>
        </div>

        <h2 className="print-sec-heading">1.0 Executive Summary &amp; Key Recommendations</h2>

        <p style={{ margin: "6px 0 12px" }}>
          This standardized financial review was conducted under the WP-514 continuous assurance protocol against the disclosed financial statements of <strong>{entityName}</strong> for the period <strong>{currentPeriod}</strong>{previousPeriod ? ` with comparative analysis against ${previousPeriod}` : ""}. A total of <strong>{totalChecks}</strong> verification rules were executed across 10 deterministic audit categories.
        </p>

        <h3 className="print-subsec-heading">1.1 Compliance Score &amp; Verification Breakdown</h3>
        <table className="print-table">
          <thead>
            <tr>
              <th>Verification Category</th>
              <th style={{ textAlign: "right", width: "15%" }}>Count</th>
              <th style={{ textAlign: "right", width: "15%" }}>Share (%)</th>
              <th>Audit Assessment &amp; Action Required</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Checks Passed</strong></td>
              <td style={{ textAlign: "right", fontWeight: 700, color: "#047857" }}>{passedChecks}</td>
              <td style={{ textAlign: "right" }}>{totalChecks > 0 ? ((passedChecks / totalChecks) * 100).toFixed(1) : 0}%</td>
              <td>Satisfies verification criteria within defined precision tolerances.</td>
            </tr>
            <tr>
              <td><strong>Review Required</strong></td>
              <td style={{ textAlign: "right", fontWeight: 700, color: "#B45309" }}>{reviewRequiredChecks}</td>
              <td style={{ textAlign: "right" }}>{totalChecks > 0 ? ((reviewRequiredChecks / totalChecks) * 100).toFixed(1) : 0}%</td>
              <td>Variance exceeds standard deviation; requires manual auditor scrutiny.</td>
            </tr>
            <tr>
              <td><strong>Failed Validations</strong></td>
              <td style={{ textAlign: "right", fontWeight: 700, color: "#B91C1C" }}>{failedChecks}</td>
              <td style={{ textAlign: "right" }}>{totalChecks > 0 ? ((failedChecks / totalChecks) * 100).toFixed(1) : 0}%</td>
              <td>Mathematical or tie-out divergence detected in statements.</td>
            </tr>
            <tr>
              <td><strong>Not in Filing</strong></td>
              <td style={{ textAlign: "right", fontWeight: 700, color: "#64748B" }}>{notInFilingChecks}</td>
              <td style={{ textAlign: "right" }}>{totalChecks > 0 ? ((notInFilingChecks / totalChecks) * 100).toFixed(1) : 0}%</td>
              <td>Optional or extended note disclosure omitted in current filing format.</td>
            </tr>
            <tr style={{ fontWeight: 700, background: "#F1F5F9" }}>
              <td>Total Audit Procedures Executed</td>
              <td style={{ textAlign: "right" }}>{totalChecks}</td>
              <td style={{ textAlign: "right" }}>100.0%</td>
              <td>Overall WP-514 Compliance Index: {overallScore.toFixed(1)} / 100</td>
            </tr>
          </tbody>
        </table>

        <h3 className="print-subsec-heading">1.2 Materiality Takeaways &amp; Recommended Actions</h3>
        {findings.filter(f => f.severity === "CRITICAL" || f.severity === "HIGH").length === 0 ? (
          <div style={{ padding: "8px 12px", border: "1px solid #A7F3D0", background: "#ECFDF5", borderRadius: 4, color: "#065F46", fontSize: "9pt" }}>
            <strong>All Core Audit Verification Criteria Clear:</strong> No Critical or High severity exceptions were raised. Routine continuous assurance recommended.
          </div>
        ) : (
          <table className="print-table">
            <thead>
              <tr>
                <th style={{ width: "15%" }}>Severity</th>
                <th style={{ width: "25%" }}>Finding</th>
                <th>Description &amp; Recommended Auditor Action</th>
              </tr>
            </thead>
            <tbody>
              {findings
                .filter(f => f.severity === "CRITICAL" || f.severity === "HIGH")
                .map((f, i) => (
                  <tr key={i}>
                    <td>
                      <span className={`status-tag ${f.severity === "CRITICAL" ? "status-failed" : "status-review"}`}>
                        {f.severity}
                      </span>
                    </td>
                    <td><strong>{f.title}</strong></td>
                    <td>{cleanText(f.description || f.explanation)} {f.recommended_action ? `— Action: ${f.recommended_action}` : ""}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        )}

        <div className="print-footer">
          <span>CONFIDENTIAL — FOR INTERNAL USE ONLY</span>
          <span>Section 1 • Page 3</span>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          SECTION 2: FINANCIAL PERFORMANCE & LINE ITEMS
          ──────────────────────────────────────────────────────────── */}
      <div className="print-page-break">
        <div className="print-header">
          <span>WP-514 Financial Statement Review — {entityName}</span>
          <span>Section 2: Financial Performance</span>
        </div>

        <h2 className="print-sec-heading">2.0 Financial Performance &amp; Line-Item Variance</h2>
        <p style={{ margin: "4px 0 10px" }}>
          Summary of primary statement line items extracted from the financial statement, showing comparison between previous period (<strong>{previousPeriod}</strong>) and current period (<strong>{currentPeriod}</strong>). Amounts in <strong>{extractionResult?.currency || "INR"} ({extractionResult?.unit || "Millions"})</strong>.
        </p>

        <table className="print-table">
          <thead>
            <tr>
              <th>Financial Metric / Line Item</th>
              <th style={{ textAlign: "right" }}>Previous ({previousPeriod})</th>
              <th style={{ textAlign: "right" }}>Current ({currentPeriod})</th>
              <th style={{ textAlign: "right" }}>YoY Variance (%)</th>
              <th>Audit Observation</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(fm).map(([key, item]) => {
              const prev = item.previous;
              const curr = item.current;
              const growth = item.growth_pct;
              return (
                <tr key={key}>
                  <td style={{ fontWeight: 600, textTransform: "capitalize" }}>{key.replace(/_/g, " ")}</td>
                  <td style={{ textAlign: "right", fontFamily: "Courier, monospace" }}>
                    {prev === null || prev === undefined ? <span style={{ color: "#94A3B8", fontStyle: "italic" }}>Not available</span> : fmt(prev)}
                  </td>
                  <td style={{ textAlign: "right", fontWeight: 700, fontFamily: "Courier, monospace" }}>
                    {curr === null || curr === undefined ? <span style={{ color: "#94A3B8", fontStyle: "italic" }}>Not available</span> : fmt(curr)}
                  </td>
                  <td style={{ textAlign: "right", fontWeight: 600, color: growth > 0 ? "#047857" : growth < 0 ? "#B91C1C" : "#1E293B", fontFamily: "Courier, monospace" }}>
                    {growth !== null && growth !== undefined ? pct(growth) : "—"}
                  </td>
                  <td style={{ fontSize: "8.5pt", color: "#475569" }}>
                    {curr === null ? "Line item omitted in filing" : prev === null ? "New line item in period" : Math.abs(growth || 0) > 20 ? "Elevated variance (>20% YoY)" : "Within normal operational bounds"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <div className="print-footer">
          <span>CONFIDENTIAL — FOR INTERNAL USE ONLY</span>
          <span>Section 2 • Page 4</span>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          SECTION 3: INTEGRITY CONTROLS & CATEGORY BREAKDOWN
          ──────────────────────────────────────────────────────────── */}
      <div className="print-page-break">
        <div className="print-header">
          <span>WP-514 Financial Statement Review — {entityName}</span>
          <span>Section 3: Audit Integrity Controls</span>
        </div>

        <h2 className="print-sec-heading">3.0 Audit Integrity Controls &amp; Category Breakdown</h2>
        <p style={{ margin: "4px 0 10px" }}>
          Summary of scores across 10 deterministic audit procedures. All sub-procedures are fully expanded in the category breakdown below.
        </p>

        <table className="print-table">
          <thead>
            <tr>
              <th style={{ width: "8%" }}>#</th>
              <th>Integrity Control Domain</th>
              <th style={{ textAlign: "right", width: "14%" }}>Score (/100)</th>
              <th style={{ width: "18%" }}>Overall Status</th>
              <th>Audit Scope &amp; Procedure Summary</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((cat, idx) => {
              const s = cat.score;
              const isNA = s === null || s === undefined;
              return (
                <tr key={cat.id || idx}>
                  <td style={{ fontWeight: 700, fontFamily: "Arial, sans-serif" }}>3.{idx + 1}</td>
                  <td><strong>{cat.name}</strong></td>
                  <td style={{ textAlign: "right", fontWeight: 700, color: isNA ? "#64748B" : s >= 80 ? "#047857" : s >= 50 ? "#B45309" : "#B91C1C", fontFamily: "Courier, monospace" }}>
                    {isNA ? "N/A" : `${s.toFixed(0)} / 100`}
                  </td>
                  <td>
                    <span className={`status-tag ${cat.status === "PASSED" ? "status-passed" : cat.status === "FAILED" ? "status-failed" : cat.status === "NOT_AVAILABLE" ? "status-na" : "status-review"}`}>
                      {cat.status}
                    </span>
                  </td>
                  <td style={{ fontSize: "8.5pt", color: "#475569" }}>
                    {cat.total_checks} checks executed • {cat.findings_count} findings raised
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {/* Detailed Category Sub-sections */}
        {categories.map((cat, idx) => {
          const catChecks = allChecks.filter(c => c.category === cat.id);
          const hasExp = catChecks.some(chk => chk.expected_value != null && String(chk.expected_value).trim() !== "");
          return (
            <div key={cat.id || idx} className="print-avoid-break" style={{ marginTop: 16 }}>
              <h3 className="print-subsec-heading" style={{ borderBottom: "1px solid #CBD5E1", paddingBottom: 2 }}>
                3.{idx + 1} {cat.name} ({catChecks.length} Procedures)
              </h3>
              <table className="print-table" style={{ fontSize: "8.5pt" }}>
                <thead>
                  <tr>
                    <th style={{ width: "12%" }}>Check ID</th>
                    <th style={{ width: hasExp ? "38%" : "55%" }}>Audit Procedure</th>
                    <th style={{ width: "14%" }}>Status</th>
                    {hasExp && <th style={{ textAlign: "right", width: "18%" }}>Expected / Prior</th>}
                    <th style={{ textAlign: "right", width: hasExp ? "18%" : "20%" }}>Actual / Current</th>
                  </tr>
                </thead>
                <tbody>
                  {catChecks.map(chk => (
                    <tr key={chk.id}>
                      <td style={{ fontFamily: "Courier, monospace", fontSize: "8pt", color: "#64748B" }}>{chk.id}</td>
                      <td>
                        <strong>{chk.check}</strong>
                        {chk.evidence && <div style={{ fontSize: "7.5pt", color: "#64748B", marginTop: 2 }}>{chk.evidence}</div>}
                      </td>
                      <td>
                        <span className={`status-tag ${chk.status === "PASSED" ? "status-passed" : chk.status === "FAILED" ? "status-failed" : chk.status === "NOT_AVAILABLE" ? "status-na" : "status-review"}`}>
                          {chk.status}
                        </span>
                      </td>
                      {hasExp && <td style={{ textAlign: "right", fontFamily: "Courier, monospace" }}>{formatCheckValue(chk.expected_value, chk.check)}</td>}
                      <td style={{ textAlign: "right", fontFamily: "Courier, monospace", fontWeight: 600 }}>{formatCheckValue(chk.actual_value, chk.check)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        })}

        <div className="print-footer">
          <span>CONFIDENTIAL — FOR INTERNAL USE ONLY</span>
          <span>Section 3 • Page 5</span>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          SECTION 4: FINANCIAL RATIO MATRIX & DISCLOSURE NOTES
          ──────────────────────────────────────────────────────────── */}
      <div className="print-page-break">
        <div className="print-header">
          <span>WP-514 Financial Statement Review — {entityName}</span>
          <span>Section 4: Financial Ratio Matrix</span>
        </div>

        <h2 className="print-sec-heading">4.0 Financial Ratio Matrix &amp; Non-Disclosure Notes</h2>
        <p style={{ margin: "4px 0 10px" }}>
          Analytical ratios computed from balance sheet and income statement items. Line items not disclosed in the filing include specific audit reasons.
        </p>

        {ratioGroups.map((grp, gIdx) => (
          <div key={gIdx} className="print-avoid-break" style={{ marginTop: 14 }}>
            <h3 className="print-subsec-heading">4.{gIdx + 1} {grp.group}</h3>
            <table className="print-table">
              <thead>
                <tr>
                  <th style={{ width: "28%" }}>Ratio Indicator</th>
                  <th style={{ textAlign: "right", width: "20%" }}>Computed Value</th>
                  <th style={{ width: "16%" }}>Status</th>
                  <th>Disclosure &amp; Computation Note</th>
                </tr>
              </thead>
              <tbody>
                {grp.items.map((r) => {
                  const isPresent = r.value !== null && r.value !== undefined;
                  const reason = RATIO_NIF_REASONS[r.key] || "Component line item not reported in filing";
                  return (
                    <tr key={r.key}>
                      <td style={{ fontWeight: 600 }}>{r.label}</td>
                      <td style={{ textAlign: "right", fontFamily: "Courier, monospace", fontWeight: isPresent ? 700 : 400, color: isPresent ? "#0F172A" : "#94A3B8" }}>
                        {isPresent ? r.value : "Not in Filing"}
                      </td>
                      <td>
                        <span className={`status-tag ${isPresent ? "status-passed" : "status-na"}`}>
                          {isPresent ? "COMPUTED" : "NOT IN FILING"}
                        </span>
                      </td>
                      <td style={{ fontSize: "8.5pt", color: isPresent ? "#475569" : "#64748B" }}>
                        {isPresent ? "Successfully evaluated from disclosed statement line items." : reason}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ))}

        <div className="print-footer">
          <span>CONFIDENTIAL — FOR INTERNAL USE ONLY</span>
          <span>Section 4 • Page 6</span>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          SECTION 5: COMPLETE FINDINGS REGISTER
          ──────────────────────────────────────────────────────────── */}
      <div className="print-page-break">
        <div className="print-header">
          <span>WP-514 Financial Statement Review — {entityName}</span>
          <span>Section 5: Findings Register</span>
        </div>

        <h2 className="print-sec-heading">5.0 Complete Findings &amp; Observations Register</h2>
        <p style={{ margin: "4px 0 10px" }}>
          Comprehensive list of all <strong>{findings.length}</strong> findings and observations generated during the audit procedure execution.
        </p>

        <table className="print-table">
          <thead>
            <tr>
              <th style={{ width: "10%" }}>Finding ID</th>
              <th style={{ width: "12%" }}>Severity</th>
              <th style={{ width: "18%" }}>Category</th>
              <th style={{ width: "25%" }}>Finding Title</th>
              <th>Description &amp; Evidence Grounding</th>
            </tr>
          </thead>
          <tbody>
            {findings.map((f, i) => {
              const src = f.source || f.source_ref || {};
              const refStr = src.page ? `Page ${src.page}` : src.note_ref ? src.note_ref : "";
              return (
                <tr key={f.id || f.finding_id || i}>
                  <td style={{ fontFamily: "Courier, monospace", fontSize: "8pt" }}>{f.id || f.finding_id || `FND-${i + 1}`}</td>
                  <td>
                    <span className={`status-tag ${f.severity === "PASSED" ? "status-passed" : f.severity === "CRITICAL" ? "status-failed" : f.severity === "HIGH" ? "status-review" : "status-review"}`}>
                      {f.severity}
                    </span>
                  </td>
                  <td style={{ textTransform: "capitalize", fontWeight: 600 }}>{(f.category || "").replace(/_/g, " ")}</td>
                  <td><strong>{f.title}</strong></td>
                  <td style={{ fontSize: "8.5pt" }}>
                    {cleanText(f.description || f.explanation)}
                    {refStr && <span style={{ color: "#64748B", marginLeft: 6 }}>({refStr})</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <div className="print-footer">
          <span>CONFIDENTIAL — FOR INTERNAL USE ONLY</span>
          <span>Section 5 • Page 7</span>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          SECTION 6: COMPREHENSIVE WP-514 VERIFICATION MASTER APPENDIX
          ──────────────────────────────────────────────────────────── */}
      <div className="print-page-break">
        <div className="print-header">
          <span>WP-514 Financial Statement Review — {entityName}</span>
          <span>Section 6: Master Appendix</span>
        </div>

        <h2 className="print-sec-heading">6.0 Master Verification Workpaper Appendix</h2>
        <p style={{ margin: "4px 0 10px" }}>
          Exhaustive check-by-check audit trail of all <strong>{allChecks.length}</strong> standardized WP-514 procedures across all statement schedules.
        </p>

        <table className="print-table" style={{ fontSize: "8pt" }}>
          <thead>
            <tr>
              <th style={{ width: "8%" }}>ID</th>
              <th style={{ width: "16%" }}>Category</th>
              <th style={{ width: "32%" }}>Procedure / Check Name</th>
              <th style={{ width: "12%" }}>Status</th>
              <th style={{ textAlign: "right", width: "16%" }}>Prior / Expected</th>
              <th style={{ textAlign: "right", width: "16%" }}>Current / Actual</th>
            </tr>
          </thead>
          <tbody>
            {allChecks.map((chk, i) => (
              <tr key={chk.id || i}>
                <td style={{ fontFamily: "Courier, monospace", color: "#64748B" }}>{chk.id}</td>
                <td style={{ textTransform: "capitalize" }}>{(chk.category || "").replace(/_/g, " ")}</td>
                <td>
                  <strong>{chk.check}</strong>
                  {chk.evidence && <div style={{ fontSize: "7.5pt", color: "#64748B", marginTop: 1 }}>{chk.evidence}</div>}
                </td>
                <td>
                  <span className={`status-tag ${chk.status === "PASSED" ? "status-passed" : chk.status === "FAILED" ? "status-failed" : chk.status === "NOT_AVAILABLE" ? "status-na" : "status-review"}`}>
                    {chk.status}
                  </span>
                </td>
                <td style={{ textAlign: "right", fontFamily: "Courier, monospace" }}>{formatCheckValue(chk.expected_value, chk.check)}</td>
                <td style={{ textAlign: "right", fontFamily: "Courier, monospace", fontWeight: 600 }}>{formatCheckValue(chk.actual_value, chk.check)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div style={{ marginTop: 18, borderTop: "2px solid #0F172A", paddingTop: 10, fontSize: "8pt", color: "#64748B", fontFamily: "Arial, sans-serif" }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span><strong>End of WP-514 Audit Report</strong> • Verification Rule Count: {allChecks.length}</span>
            <span>Compliance Engine v{analysisResult?.score_formula_version || "2.0.0"}</span>
          </div>
        </div>

        <div className="print-footer">
          <span>CONFIDENTIAL — FOR INTERNAL USE ONLY</span>
          <span>Section 6 • Final Page</span>
        </div>
      </div>
    </div>
  );
}
