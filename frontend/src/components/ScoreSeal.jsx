import React from "react";

export default function ScoreSeal({ score }) {
  const getGradient = (s) => {
    if (s >= 80) return "var(--color-primary-hover)";
    if (s >= 60) return "var(--color-primary-soft)";
    return "var(--status-critical)";
  };

  const getTextColor = (s) => {
    if (s >= 80) return "#2E7D32";
    if (s >= 60) return "#E65100";
    return "#C62828";
  };

  return (
    <div style={{
      width: 100,
      height: 100,
      borderRadius: "1rem",
      background: "var(--bg-card)",
      border: "1px solid #E2E8F0",
      boxShadow: "0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      position: "relative",
      padding: "0.5rem",
    }}>
      <div style={{
        position: "absolute",
        top: -8,
        padding: "2px 8px",
        borderRadius: "9999px",
        background: getGradient(score),
        color: "var(--bg-card)",
        fontSize: "0.625rem",
        fontWeight: 700,
        letterSpacing: "0.05em",
        textTransform: "uppercase",
        boxShadow: "0 2px 5px rgba(0,0,0,0.15)",
      }}>
        Score
      </div>
      <span style={{
        fontFamily: "'DM Sans', sans-serif",
        fontSize: 32,
        fontWeight: 800,
        color: getTextColor(score),
        lineHeight: 1,
        marginTop: 6,
      }}>
        {score}
      </span>
      <span style={{
        fontFamily: "'Averia Serif Libre', serif",
        fontSize: 11,
        color: "var(--text-muted)",
        fontWeight: 600,
        letterSpacing: "0.05em",
        marginTop: 2,
      }}>
        / 100
      </span>
    </div>
  );
}
