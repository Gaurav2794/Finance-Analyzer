import React from "react";

export default function ScoreSeal({ score }) {
  const numScore = Number(score) || 0;
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(100, Math.max(0, numScore)) / 100) * circumference;

  const getColor = (s) => {
    if (s >= 80) return "#059669";
    if (s >= 60) return "#D97706";
    return "#DC2626";
  };

  const color = getColor(numScore);

  return (
    <div
      className="interactive-card"
      style={{
        width: 108,
        height: 108,
        borderRadius: "16px",
        background: "var(--bg-card)",
        border: "1px solid var(--border-subtle, #E2E8F0)",
        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
      }}
    >
      {/* Circular Progress Ring */}
      <svg width="86" height="86" viewBox="0 0 86 86" style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx="43"
          cy="43"
          r={radius}
          stroke="#F1F5F9"
          strokeWidth="6"
          fill="none"
        />
        <circle
          cx="43"
          cy="43"
          r={radius}
          stroke={color}
          strokeWidth="6"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          fill="none"
          style={{ transition: "stroke-dashoffset 0.8s cubic-bezier(0.16, 1, 0.3, 1)" }}
        />
      </svg>

      {/* Centered Score Display */}
      <div
        style={{
          position: "absolute",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span
          style={{
            fontSize: 22,
            fontWeight: 800,
            color: color,
            lineHeight: 1,
          }}
        >
          {numScore.toFixed(0)}
        </span>
        <span
          style={{
            fontSize: 9,
            color: "var(--text-muted)",
            fontWeight: 700,
            textTransform: "uppercase",
            marginTop: 2,
            letterSpacing: "0.04em",
          }}
        >
          / 100
        </span>
      </div>
    </div>
  );
}
