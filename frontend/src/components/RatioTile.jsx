import React from "react";
import { TrendingUp, Activity, Percent, Scale, DollarSign } from "lucide-react";

export default function RatioTile({ label, value }) {
  const isMissing = value === "Not available" || value === null || value === undefined;

  // Derive visual category icon & health color based on label & value
  const numVal = typeof value === "number" ? value : parseFloat(value);
  const isPercentage = typeof value === "string" && value.includes("%");

  const getIcon = () => {
    const l = (label || "").toLowerCase();
    if (l.includes("margin") || l.includes("return") || l.includes("roe") || l.includes("roa")) return Percent;
    if (l.includes("ratio") || l.includes("current") || l.includes("quick")) return Scale;
    if (l.includes("turnover") || l.includes("growth")) return TrendingUp;
    return Activity;
  };

  const Icon = getIcon();

  return (
    <div
      className="interactive-card"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border-subtle, #E2E8F0)",
        borderRadius: "12px",
        padding: "14px 16px",
        boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.04)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        gap: "8px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span
          style={{
            fontSize: "11px",
            color: "var(--text-secondary)",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            fontWeight: 600,
          }}
        >
          {label}
        </span>
        <div
          style={{
            width: "24px",
            height: "24px",
            borderRadius: "6px",
            background: isMissing ? "var(--bg-secondary, #F1F5F9)" : "var(--color-primary-soft, #ECFDF5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Icon size={13} color={isMissing ? "#94A3B8" : "var(--color-primary, #059669)"} />
        </div>
      </div>

      <div
        style={{
          fontSize: isMissing ? "13px" : "18px",
          fontWeight: isMissing ? 500 : 800,
          color: isMissing ? "var(--text-muted)" : "var(--text-primary)",
          fontStyle: isMissing ? "italic" : "normal",
          fontVariantNumeric: "tabular-nums",
          display: "flex",
          alignItems: "baseline",
          gap: "4px",
        }}
      >
        {value}
      </div>

      {/* Visual Indicator Bar */}
      <div
        style={{
          height: "4px",
          width: "100%",
          background: "#F1F5F9",
          borderRadius: "2px",
          overflow: "hidden",
          marginTop: "2px",
        }}
      >
        <div
          style={{
            height: "100%",
            width: isMissing ? "0%" : "70%",
            background: isMissing
              ? "transparent"
              : "linear-gradient(90deg, #10B981, #059669)",
            borderRadius: "2px",
          }}
        />
      </div>
    </div>
  );
}
