import React, { useState, useMemo } from "react";
import {
  FileText,
  Search,
  ArrowLeft,
  ArrowUpRight,
  ArrowDownRight,
  Filter,
  Layers,
  FileSpreadsheet,
  Download,
  Calendar,
  Building,
  Coins,
  Calculator,
  CheckCircle2,
  AlertCircle,
  Tag
} from "lucide-react";

export default function LedgerView({ extractionResult, analysisResult, onBack }) {
  const [activeTab, setActiveTab] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");

  const metadata = extractionResult?.metadata || {};
  const currentPeriod = extractionResult?.period?.current || "Current";
  const previousPeriod = extractionResult?.period?.previous || "Prior";
  const currency = extractionResult?.currency === "INR" ? "₹" : (extractionResult?.currency === "USD" ? "$" : (extractionResult?.currency ? `${extractionResult?.currency} ` : ""));
  const unit = extractionResult?.unit || "";

  const fmt = (v) => {
    if (v === null || v === undefined) return "";
    if (typeof v === "number") {
      return `${currency}${v.toLocaleString("en-IN", { maximumFractionDigits: 2 })} ${unit}`.trim();
    }
    return String(v);
  };

  const fmtNum = (v) => {
    if (v === null || v === undefined || isNaN(v)) return null;
    return Number(v);
  };

  // Compile items from all statements
  const ledgerItems = useMemo(() => {
    const items = [];
    const isStmt = extractionResult?.income_statement || {};
    const bsStmt = extractionResult?.balance_sheet || {};
    const cfStmt = extractionResult?.cash_flow_statement || {};

    // 1. Income Statement
    Object.entries(isStmt).forEach(([key, val]) => {
      if (!val || typeof val !== "object") return;
      const currVal = fmtNum(val.values?.[currentPeriod]);
      const prevVal = fmtNum(val.values?.[previousPeriod]);
      const diff = currVal !== null && prevVal !== null ? currVal - prevVal : null;
      const diffPct = currVal !== null && prevVal !== null && prevVal !== 0 ? (diff / Math.abs(prevVal)) * 100 : null;

      items.push({
        id: `IS-${key}`,
        key,
        statement: "income_statement",
        statementLabel: "Income Statement",
        label: val.standard_label || key.replace(/_/g, " "),
        rawLabels: val.raw_labels || [],
        currentValue: currVal,
        previousValue: prevVal,
        variance: diff,
        variancePct: diffPct,
        source: val.source || {},
        noteRef: val.source?.note_ref || null,
        page: val.source?.page || null,
        tableIndex: val.source?.table_index || null,
      });
    });

    // 2. Balance Sheet
    Object.entries(bsStmt).forEach(([key, val]) => {
      if (!val || typeof val !== "object") return;
      const currVal = fmtNum(val.values?.[currentPeriod]);
      const prevVal = fmtNum(val.values?.[previousPeriod]);
      const diff = currVal !== null && prevVal !== null ? currVal - prevVal : null;
      const diffPct = currVal !== null && prevVal !== null && prevVal !== 0 ? (diff / Math.abs(prevVal)) * 100 : null;

      items.push({
        id: `BS-${key}`,
        key,
        statement: "balance_sheet",
        statementLabel: "Balance Sheet",
        label: val.standard_label || key.replace(/_/g, " "),
        rawLabels: val.raw_labels || [],
        currentValue: currVal,
        previousValue: prevVal,
        variance: diff,
        variancePct: diffPct,
        source: val.source || {},
        noteRef: val.source?.note_ref || null,
        page: val.source?.page || null,
        tableIndex: val.source?.table_index || null,
      });
    });

    // 3. Cash Flow
    Object.entries(cfStmt).forEach(([key, val]) => {
      if (!val || typeof val !== "object") return;
      const currVal = fmtNum(val.values?.[currentPeriod]);
      const prevVal = fmtNum(val.values?.[previousPeriod]);
      const diff = currVal !== null && prevVal !== null ? currVal - prevVal : null;
      const diffPct = currVal !== null && prevVal !== null && prevVal !== 0 ? (diff / Math.abs(prevVal)) * 100 : null;

      items.push({
        id: `CF-${key}`,
        key,
        statement: "cash_flow",
        statementLabel: "Cash Flow",
        label: val.standard_label || key.replace(/_/g, " "),
        rawLabels: val.raw_labels || [],
        currentValue: currVal,
        previousValue: prevVal,
        variance: diff,
        variancePct: diffPct,
        source: val.source || {},
        noteRef: val.source?.note_ref || null,
        page: val.source?.page || null,
        tableIndex: val.source?.table_index || null,
      });
    });

    return items;
  }, [extractionResult, currentPeriod, previousPeriod]);

  // Filtered items
  const filteredItems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return ledgerItems.filter((item) => {
      const matchTab =
        activeTab === "all" ||
        (activeTab === "income_statement" && item.statement === "income_statement") ||
        (activeTab === "balance_sheet" && item.statement === "balance_sheet") ||
        (activeTab === "cash_flow" && item.statement === "cash_flow");

      if (!matchTab) return false;

      if (!q) return true;
      return (
        item.label.toLowerCase().includes(q) ||
        item.key.toLowerCase().includes(q) ||
        item.statementLabel.toLowerCase().includes(q) ||
        (item.noteRef && item.noteRef.toLowerCase().includes(q)) ||
        item.rawLabels.some((rl) => rl.toLowerCase().includes(q))
      );
    });
  }, [ledgerItems, activeTab, searchQuery]);

  const fm = analysisResult?.financial_metrics || {};

  return (
    <div style={{ background: "var(--bg-main)", minHeight: "100vh", padding: "32px 40px", maxWidth: 1300, margin: "0 auto" }}>
      {/* Top Header */}
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
            <h1 style={{ fontSize: "22px", fontWeight: 800, color: "var(--text-primary)", margin: 0 }}>
              General Financial Ledger
            </h1>
            <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: 2 }}>
              {extractionResult?.company?.name || extractionResult?.file_name} • {currentPeriod} {previousPeriod ? `vs ${previousPeriod}` : ""} ({unit})
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            onClick={() => { window.location.hash = "#report"; }}
            className="fd-btn fd-btn-primary"
            style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: "13px", fontWeight: 600 }}
          >
            <FileText size={15} /> View Audit Report
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 24 }}>
        <div className="fd-card" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600, marginBottom: 6 }}>Total Extracted Items</div>
          <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--text-primary)" }}>{ledgerItems.length}</div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: 4 }}>Across all 3 financial statements</div>
        </div>
        <div className="fd-card" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600, marginBottom: 6 }}>Total Revenue ({currentPeriod})</div>
          <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--color-primary)" }}>
            {fm.revenue?.current != null ? fmt(fm.revenue.current) : "—"}
          </div>
          <div style={{ fontSize: "11px", color: "var(--color-success)", marginTop: 4, fontWeight: 600 }}>
            {fm.revenue?.growth_pct != null ? `+${fm.revenue.growth_pct}% YoY` : "Verified"}
          </div>
        </div>
        <div className="fd-card" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600, marginBottom: 6 }}>Operating Expenses</div>
          <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--text-primary)" }}>
            {fm.expenses?.current != null ? fmt(fm.expenses.current) : "—"}
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: 4 }}>P&L operating lines</div>
        </div>
        <div className="fd-card" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600, marginBottom: 6 }}>Net Profit</div>
          <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--color-success)" }}>
            {fm.net_profit?.current != null ? fmt(fm.net_profit.current) : "—"}
          </div>
          <div style={{ fontSize: "11px", color: "var(--color-success)", marginTop: 4, fontWeight: 600 }}>Audited PAT</div>
        </div>
      </div>

      {/* Main Ledger Table Card */}
      <div className="fd-card animate-fade-up" style={{ padding: "24px" }}>
        {/* Controls Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16, marginBottom: 20 }}>
          {/* Statement Tabs */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {[
              { key: "all", label: `All Statements (${ledgerItems.length})` },
              { key: "income_statement", label: "Income Statement (P&L)" },
              { key: "balance_sheet", label: "Balance Sheet" },
              { key: "cash_flow", label: "Cash Flow Statement" },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`filter-tab-pill ${activeTab === tab.key ? "active" : ""}`}
                style={{ padding: "8px 16px", fontSize: "13px" }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, background: "var(--bg-main)", borderRadius: "20px", padding: "6px 14px", width: "280px", border: "1px solid var(--border-light)" }}>
            <Search size={15} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search ledger accounts, notes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ border: "none", outline: "none", fontSize: "13px", color: "var(--text-primary)", background: "transparent", width: "100%" }}
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery("")} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", fontSize: "12px" }}>✕</button>
            )}
          </div>
        </div>

        {/* Ledger Table */}
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid var(--border-light)", color: "var(--text-secondary)", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                <th style={{ padding: "12px 16px", fontWeight: 700 }}>Line Item / Account Name</th>
                <th style={{ padding: "12px 16px", fontWeight: 700 }}>Statement</th>
                <th style={{ padding: "12px 16px", fontWeight: 700, textAlign: "right" }}>{previousPeriod || "Prior"}</th>
                <th style={{ padding: "12px 16px", fontWeight: 700, textAlign: "right" }}>{currentPeriod || "Current"}</th>
                <th style={{ padding: "12px 16px", fontWeight: 700, textAlign: "right" }}>YoY Variance</th>
                <th style={{ padding: "12px 16px", fontWeight: 700, textAlign: "center" }}>Source Ref</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: "40px 16px", textAlign: "center", color: "var(--text-muted)" }}>
                    No ledger entries match your filter criteria.
                  </td>
                </tr>
              ) : (
                filteredItems.map((item, idx) => {
                  const isPos = item.variance != null && item.variance > 0;
                  const isNeg = item.variance != null && item.variance < 0;
                  const isRatio = item.label.toLowerCase().includes("ratio") || item.label.toLowerCase().includes("margin");

                  return (
                    <tr
                      key={item.id || idx}
                      className="hover-scale"
                      style={{
                        borderBottom: "1px solid var(--border-light)",
                        background: idx % 2 === 0 ? "transparent" : "rgba(248, 250, 252, 0.5)",
                        transition: "background 0.15s ease",
                      }}
                    >
                      <td style={{ padding: "12px 16px" }}>
                        <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>{item.label}</div>
                        <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace", marginTop: 2 }}>{item.key}</div>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <span
                          style={{
                            fontSize: "11px",
                            fontWeight: 600,
                            padding: "2px 8px",
                            borderRadius: "6px",
                            background:
                              item.statement === "income_statement"
                                ? "var(--color-primary-soft)"
                                : item.statement === "balance_sheet"
                                ? "var(--color-purple-soft)"
                                : "var(--color-success-soft)",
                            color:
                              item.statement === "income_statement"
                                ? "var(--color-primary)"
                                : item.statement === "balance_sheet"
                                ? "var(--color-purple)"
                                : "var(--color-success)",
                          }}
                        >
                          {item.statementLabel}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums", color: "var(--text-secondary)" }}>
                        {item.previousValue !== null ? (isRatio ? item.previousValue.toFixed(2) : fmt(item.previousValue)) : ""}
                      </td>
                      <td style={{ padding: "12px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums", fontWeight: 700, color: "var(--text-primary)" }}>
                        {item.currentValue !== null ? (isRatio ? item.currentValue.toFixed(2) : fmt(item.currentValue)) : ""}
                      </td>
                      <td style={{ padding: "12px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                        {item.variancePct !== null ? (
                          <span
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: 2,
                              fontWeight: 600,
                              fontSize: "12px",
                              color: isPos ? "var(--color-success)" : isNeg ? "var(--color-danger)" : "var(--text-muted)",
                            }}
                          >
                            {isPos ? <ArrowUpRight size={14} /> : isNeg ? <ArrowDownRight size={14} /> : null}
                            {isPos ? "+" : ""}{item.variancePct.toFixed(2)}%
                          </span>
                        ) : null}
                      </td>
                      <td style={{ padding: "12px 16px", textAlign: "center" }}>
                        {item.noteRef ? (
                          <span style={{ fontSize: "11px", color: "var(--color-primary)", background: "var(--color-primary-soft)", padding: "2px 6px", borderRadius: "4px", fontWeight: 600 }}>
                            {item.noteRef}
                          </span>
                        ) : item.page ? (
                          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Page {item.page}</span>
                        ) : (
                          <span style={{ color: "var(--text-muted)", fontSize: "11px" }}>Filing Body</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
