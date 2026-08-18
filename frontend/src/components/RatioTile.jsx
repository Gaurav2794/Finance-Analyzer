import React from "react";

export default function RatioTile({ label, value }) {
  const isMissing = value === "Not available" || value === null || value === undefined;
  return (
    <div style={{
      background: "var(--bg-card)",
      border: "1px solid #E2E8F0",
      borderRadius: "0.75rem",
      padding: "1rem 1.25rem",
      boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.05)",
      transition: "transform 0.15s ease, box-shadow 0.15s ease",
    }}>
      <div style={{
        fontFamily: "'DM Sans', sans-serif",
        fontSize: "0.75rem",
        color: "var(--text-secondary)",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
        fontWeight: 600,
      }}>
        {label}
      </div>
      <div style={{
        fontFamily: isMissing ? "'DM Sans', sans-serif" : "'DM Sans', sans-serif",
        fontSize: isMissing ? "0.95rem" : "1.35rem",
        fontWeight: isMissing ? 500 : 700,
        color: isMissing ? "var(--text-muted)" : "var(--text-primary)",
        fontStyle: isMissing ? "italic" : "normal",
        marginTop: "0.25rem",
        fontVariantNumeric: "tabular-nums",
      }}>
        {value}
      </div>
    </div>
  );
}
