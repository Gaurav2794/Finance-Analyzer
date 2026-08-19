import React from "react";
import { TrendingUp, Activity, Percent, Scale, DollarSign, ShieldCheck, AlertTriangle } from "lucide-react";

export default function RatioTile({ label, value }) {
  const isMissing = value === "Not available" || value === null || value === undefined || value === "";

  // Parse and cleanly format numeric value
  let formattedValue = value;
  let numericVal = null;
  let isPercentage = false;

  if (!isMissing) {
    if (typeof value === "number") {
      numericVal = value;
      formattedValue = Math.abs(numericVal) > 100000
        ? `${(numericVal / 1000000).toFixed(2)}M`
        : numericVal.toLocaleString("en-IN", { maximumFractionDigits: 2 });
    } else if (typeof value === "string") {
      if (value.includes("%")) {
        isPercentage = true;
        const parsed = parseFloat(value.replace("%", ""));
        if (!isNaN(parsed)) {
          numericVal = parsed;
          formattedValue = `${parsed.toFixed(2)}%`;
        }
      } else {
        const parsed = parseFloat(value);
        if (!isNaN(parsed)) {
          numericVal = parsed;
          formattedValue = Math.abs(parsed) > 100000
            ? `${(parsed / 1000000).toFixed(2)}M`
            : parsed.toFixed(2);
        }
      }
    }
  }

  // Derive visual category icon & benchmark status
  const l = (label || "").toLowerCase();

  const getIcon = () => {
    if (l.includes("margin") || l.includes("return") || l.includes("roe") || l.includes("roa")) return Percent;
    if (l.includes("ratio") || l.includes("current") || l.includes("quick") || l.includes("debt")) return Scale;
    if (l.includes("turnover") || l.includes("growth")) return TrendingUp;
    return Activity;
  };

  const Icon = getIcon();

  // Benchmark rules
  let statusText = "Standard";
  let statusColor = "var(--color-primary, #059669)";
  let statusBg = "var(--color-primary-soft, #ECFDF5)";
  let progressPct = 65;

  if (isMissing) {
    statusText = "Not in Filing";
    statusColor = "#94A3B8";
    statusBg = "#F1F5F9";
    progressPct = 0;
  } else if (numericVal !== null) {
    if (l.includes("current")) {
      if (numericVal >= 1.5) { statusText = "Healthy"; statusColor = "#059669"; statusBg = "rgba(16, 185, 129, 0.12)"; progressPct = 85; }
      else if (numericVal >= 1.0) { statusText = "Needs Review"; statusColor = "#D97706"; statusBg = "rgba(245, 158, 11, 0.12)"; progressPct = 55; }
      else { statusText = "Low Liquidity"; statusColor = "#DC2626"; statusBg = "rgba(239, 68, 68, 0.12)"; progressPct = 25; }
    } else if (l.includes("quick")) {
      if (numericVal >= 1.0) { statusText = "Healthy"; statusColor = "#059669"; statusBg = "rgba(16, 185, 129, 0.12)"; progressPct = 80; }
      else { statusText = "Needs Review"; statusColor = "#D97706"; statusBg = "rgba(245, 158, 11, 0.12)"; progressPct = 45; }
    } else if (l.includes("debt to equity") || l.includes("debt ratio")) {
      if (numericVal <= 1.0) { statusText = "Low Risk"; statusColor = "#059669"; statusBg = "rgba(16, 185, 129, 0.12)"; progressPct = 85; }
      else if (numericVal <= 2.0) { statusText = "Moderate"; statusColor = "#D97706"; statusBg = "rgba(245, 158, 11, 0.12)"; progressPct = 60; }
      else { statusText = "High Leverage"; statusColor = "#DC2626"; statusBg = "rgba(239, 68, 68, 0.12)"; progressPct = 30; }
    } else if (l.includes("margin") || l.includes("roe") || l.includes("roa")) {
      if (numericVal >= 20) { statusText = "Strong"; statusColor = "#059669"; statusBg = "rgba(16, 185, 129, 0.12)"; progressPct = 90; }
      else if (numericVal >= 0) { statusText = "Positive"; statusColor = "#059669"; statusBg = "rgba(16, 185, 129, 0.12)"; progressPct = 65; }
      else { statusText = "Negative"; statusColor = "#DC2626"; statusBg = "rgba(239, 68, 68, 0.12)"; progressPct = 20; }
    } else if (l.includes("turnover")) {
      statusText = "Efficiency";
      statusColor = "#059669";
      statusBg = "rgba(16, 185, 129, 0.12)";
      progressPct = 75;
    }
  }

  return (
    <div
      className="interactive-card"
      style={{
        background: "var(--bg-card, #FFFFFF)",
        border: "1px solid var(--border-subtle, #E2E8F0)",
        borderRadius: "10px",
        padding: "12px 14px",
        boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.03)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        gap: "6px",
        pageBreakInside: "avoid",
        breakInside: "avoid",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span
          style={{
            fontSize: "10.5px",
            color: "var(--text-secondary)",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            fontWeight: 700,
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontSize: "9.5px",
            fontWeight: 700,
            padding: "1px 6px",
            borderRadius: "4px",
            background: statusBg,
            color: statusColor,
            letterSpacing: "0.02em",
          }}
        >
          {statusText}
        </span>
      </div>

      <div
        style={{
          fontSize: isMissing ? "12px" : "17px",
          fontWeight: isMissing ? 500 : 800,
          color: isMissing ? "var(--text-muted)" : "var(--text-primary)",
          fontStyle: isMissing ? "italic" : "normal",
          fontVariantNumeric: "tabular-nums",
          display: "flex",
          alignItems: "baseline",
          gap: "4px",
          margin: "2px 0",
        }}
      >
        {isMissing ? "Not in Filing" : formattedValue}
      </div>

      {/* Visual Indicator Bar */}
      <div
        style={{
          height: "4px",
          width: "100%",
          background: "#F1F5F9",
          borderRadius: "2px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: isMissing ? "0%" : `${progressPct}%`,
            background: statusColor,
            borderRadius: "2px",
            transition: "width 0.4s ease",
          }}
        />
      </div>
    </div>
  );
}
