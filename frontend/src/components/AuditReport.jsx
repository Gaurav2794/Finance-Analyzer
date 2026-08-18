import React from "react";
import ScoreSeal from "./ScoreSeal.jsx";
import RatioTile from "./RatioTile.jsx";
import WP514ReviewMatrix from "./WP514ReviewMatrix.jsx";
import {
  ArrowLeft, Printer, ShieldCheck, AlertTriangle, AlertOctagon, CircleAlert, CheckCircle2,
} from "lucide-react";

const sev = {
  CRITICAL: { color: "var(--color-danger, #EF4444)", bg: "var(--color-danger-soft, #FEE2E2)", label: "Critical", Icon: AlertOctagon },
  HIGH: { color: "var(--color-warning, #F59E0B)", bg: "var(--color-warning-soft, #FEF3C7)", label: "High", Icon: AlertTriangle },
  REVIEW: { color: "var(--color-purple, #8B5CF6)", bg: "var(--color-purple-soft, #EDE9FE)", label: "Review", Icon: CircleAlert },
  PASSED: { color: "var(--color-success, #10B981)", bg: "var(--color-success-soft, #D1FAE5)", label: "Passed", Icon: ShieldCheck },
};

const fmt = (n) => (n === null || n === undefined ? "—" : n.toLocaleString("en-IN"));
const pct = (n) => (n === null || n === undefined ? "—" : `${n > 0 ? "+" : ""}${Number(n).toFixed(2)}%`);

export default function AuditReport({ extractionResult, analysisResult, onBack }) {
  const fm = analysisResult?.financial_metrics || {};
  const fs = analysisResult?.findings_summary || {};
  const dq = extractionResult?.document_quality || {};
  const findings = analysisResult?.findings || [];

  const currentPeriod = extractionResult?.period?.current || extractionResult?.periods?.[0]?.period_key || "Current";
  const previousPeriod = extractionResult?.period?.previous || (extractionResult?.periods?.length > 1 ? extractionResult.periods[1].period_key : "Prior");

  const recommendedReview = findings.filter(
    (f) => f.severity === "CRITICAL" || f.severity === "HIGH"
  );

  return (
    <div className="audit-report-container" style={{
      background: "var(--bg-main, #F5F7FB)", minHeight: "100vh", color: "var(--text-primary)",
      padding: "32px 40px", maxWidth: 1120, margin: "0 auto",
    }}>
      <style>{`
        @media print {
          body {
            background: #FFFFFF !important;
            color: #1E293B !important;
          }
          .audit-report-container {
            background: #FFFFFF !important;
            padding: 0 !important;
            max-width: 100% !important;
          }
          .no-print {
            display: none !important;
          }
        }
      `}</style>

      {/* Action Bar (Screen Only) */}
      <div className="no-print" style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 28, paddingBottom: 16, borderBottom: "1px solid var(--border-light, #E2E8F0)",
      }}>
        <button
          onClick={onBack}
          className="fd-btn fd-btn-outline"
          style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            fontSize: "13px", fontWeight: 600,
          }}
        >
          <ArrowLeft size={15} /> Back to Dashboard
        </button>

        <button
          onClick={() => window.print()}
          className="fd-btn fd-btn-primary"
          style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            fontSize: "13px", fontWeight: 700,
          }}
        >
          <Printer size={15} /> Print / Export PDF
        </button>
      </div>

      {/* 1. Header */}
      <div className="fd-card" style={{
        padding: "24px 28px",
        display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 28,
      }}>
        <div>
          <div style={{
            fontSize: "12px",
            color: "var(--text-secondary)", letterSpacing: "0.08em", textTransform: "uppercase", fontWeight: 700,
          }}>
            FINANCIAL AUDIT REPORT · {extractionResult?.document_id || "DOC-ID"}
          </div>
          <h1 style={{
            fontSize: "24px", margin: "6px 0", fontWeight: 800, color: "var(--text-primary)",
          }}>
            {extractionResult?.company?.name || extractionResult?.file_name || "Audit Summary"}
          </h1>
          <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            Period: <strong style={{ color: "var(--text-primary)" }}>{currentPeriod}</strong>{previousPeriod ? ` vs ${previousPeriod}` : ""}{extractionResult?.currency ? <> · Currency: <strong style={{ color: "var(--text-primary)" }}>{extractionResult.currency} {extractionResult?.unit ? `(${extractionResult.unit})` : ""}</strong></> : ""}
          </div>
        </div>
        <ScoreSeal score={analysisResult?.overall_score} />
      </div>

      {/* 2. Executive Summary */}
      <div className="fd-card" style={{
        padding: "24px 28px", marginBottom: 28,
      }}>
        <h2 style={{
          fontSize: "17px", color: "var(--text-primary)", fontWeight: 700,
          marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: 8,
        }}>
          1. Executive Summary & Quality Status
        </h2>

        {dq.data_quality_status && dq.data_quality_status !== "EXCELLENT" && (
          <div style={{
            background: dq.data_quality_status === "INSUFFICIENT" ? "var(--color-danger-soft)" : "var(--color-warning-soft)",
            border: `1px solid ${dq.data_quality_status === "INSUFFICIENT" ? "var(--color-danger)" : "var(--color-warning)"}`,
            borderRadius: "8px", padding: "14px 18px", marginBottom: 16, display: "flex", alignItems: "center", gap: 12,
          }}>
            <AlertTriangle size={20} color={dq.data_quality_status === "INSUFFICIENT" ? "var(--color-danger)" : "var(--color-warning)"} />
            <div>
              <span style={{ fontWeight: 700, color: dq.data_quality_status === "INSUFFICIENT" ? "var(--color-danger)" : "var(--color-warning)" }}>
                {dq.data_quality_status} Extraction Warning:{" "}
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
          <div style={{
            background: "var(--color-warning-soft)", border: "1px solid var(--color-warning)",
            borderRadius: "8px", padding: "12px 18px", marginBottom: 16, display: "flex", alignItems: "center", gap: 12,
          }}>
            <AlertTriangle size={18} color="var(--color-warning)" />
            <div>
              <span style={{ fontWeight: 700, color: "var(--color-warning)" }}>Unit Mismatch Detected: </span>
              <span style={{ color: "var(--text-primary)" }}>{dq.unit_mismatch_detail || "Units between periods require normalization review."}</span>
            </div>
          </div>
        )}

        <div style={{
          display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14,
        }}>
          {[["CRITICAL", fs.critical || 0], ["HIGH", fs.high || 0], ["REVIEW", fs.review || 0], ["PASSED", fs.passed || 0]].map(([k, v]) => {
            const s = sev[k];
            return (
              <div key={k} style={{
                background: "var(--bg-main)", border: "1px solid var(--border-light)", borderRadius: "8px",
                padding: "16px", textAlign: "center",
              }}>
                <div style={{ fontSize: "24px", fontWeight: 800, color: s.color }}>{v}</div>
                <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", marginTop: 4 }}>
                  {s.label}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Overall Score Breakdown */}
      <div className="fd-card" style={{
        padding: "24px 28px", marginBottom: 28,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: 8 }}>
          <h2 style={{ fontSize: "17px", color: "var(--text-primary)", fontWeight: 700, margin: 0 }}>
            2. Audit Integrity Checks
          </h2>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 600 }}>
            engine version: {analysisResult?.score_formula_version || "2.0"}
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          {Object.entries(analysisResult?.checks || {}).filter(([, val]) => val !== null && val !== undefined).map(([key, val]) => {
            const num = Number(val);
            const isNA = val === "NOT_AVAILABLE" || (key === "related_disclosure" && num === 0);
            return (
              <div key={key} style={{
                background: "var(--bg-main)", border: "1px solid var(--border-light)", borderRadius: "8px",
                padding: "14px 18px", display: "flex", justifyContent: "space-between", alignItems: "center",
              }}>
                <span style={{ fontSize: "13px", textTransform: "capitalize", color: isNA ? "var(--text-secondary)" : "var(--text-primary)", fontWeight: 600 }}>
                  {key.replace(/_/g, " ")}
                </span>
                <span style={{
                  fontSize: "13px", fontWeight: 700,
                  color: isNA ? "var(--text-muted)" : num >= 80 ? "var(--color-success)" : num >= 50 ? "var(--color-warning)" : "var(--color-danger)",
                  fontStyle: isNA ? "italic" : "normal",
                }}>
                  {isNA ? "N/A (Not in filing)" : `${num.toFixed(0)} / 100`}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. Financial Metrics */}
      <div className="fd-card" style={{
        padding: "24px 28px", marginBottom: 28,
      }}>
        <h2 style={{
          fontSize: "17px", color: "var(--text-primary)", fontWeight: 700,
          marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: 8,
        }}>
          3. Financial Metrics Comparison
        </h2>
        <div style={{ border: "1px solid var(--border-light)", borderRadius: "8px", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
            <thead>
              <tr style={{ background: "var(--bg-main)", borderBottom: "1px solid var(--border-light)" }}>
                <th style={{ padding: "12px 16px", fontSize: "11px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 700 }}>Metric</th>
                <th style={{ padding: "12px 16px", fontSize: "11px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "right", fontWeight: 700 }}>Previous ({previousPeriod})</th>
                <th style={{ padding: "12px 16px", fontSize: "11px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "right", fontWeight: 700 }}>Current ({currentPeriod})</th>
                <th style={{ padding: "12px 16px", fontSize: "11px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "right", fontWeight: 700 }}>Growth %</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(fm).map(([key, data], idx) => {
                const isPrevMissing = data.previous === null || data.previous === undefined;
                const isCurrMissing = data.current === null || data.current === undefined;
                return (
                  <tr key={key} style={{ borderBottom: idx < Object.keys(fm).length - 1 ? "1px solid var(--border-light)" : "none" }}>
                    <td style={{ padding: "12px 16px", fontSize: "13px", textTransform: "capitalize", color: "var(--text-primary)", fontWeight: 600 }}>
                      {key.replace(/_/g, " ")}
                    </td>
                    <td style={{
                      padding: "12px 16px",
                      fontSize: "13px", textAlign: "right", color: "var(--text-secondary)", fontStyle: isPrevMissing ? "italic" : "normal",
                    }}>
                      {isPrevMissing ? "Not available" : fmt(data.previous)}
                    </td>
                    <td style={{
                      padding: "12px 16px", fontSize: "13px", textAlign: "right", color: isCurrMissing ? "var(--text-secondary)" : "var(--text-primary)",
                      fontWeight: isCurrMissing ? 400 : 700, fontStyle: isCurrMissing ? "italic" : "normal",
                    }}>
                      {isCurrMissing ? "Not available" : fmt(data.current)}
                    </td>
                    <td style={{
                      padding: "12px 16px", fontSize: "13px",
                      textAlign: "right", fontWeight: 600,
                      color: data.growth_pct === null ? "var(--text-muted)" : data.growth_pct < 0 ? "var(--color-danger)" : "var(--color-success)",
                    }}>
                      {data.growth_pct === null ? "—" : pct(data.growth_pct)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. Ratio Dashboard */}
      <div className="fd-card" style={{
        padding: "24px 28px", marginBottom: 28,
      }}>
        <h2 style={{
          fontSize: "17px", color: "var(--text-primary)", fontWeight: 700,
          marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: 8,
        }}>
          4. Financial Ratio Matrix
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
          {Object.entries(analysisResult?.ratios || {}).map(([key, val]) => (
            <RatioTile
              key={key}
              label={key.replace(/_pct$/, "").replace(/_/g, " ")}
              value={val === null || val === undefined ? "Not available" : key.endsWith("_pct") ? `${Number(val).toFixed(2)}%` : val}
            />
          ))}
        </div>
      </div>

      {/* 6. Findings Detail */}
      <div className="fd-card" style={{
        padding: "24px 28px", marginBottom: 28,
      }}>
        <h2 style={{
          fontSize: "17px", color: "var(--text-primary)", fontWeight: 700,
          marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: 8,
        }}>
          5. Detailed Findings & Audit Notes
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {findings.map((f, i) => {
            const s = sev[f.severity] || sev.REVIEW;
            const Icon = s.Icon;
            const fid = f.id || f.finding_id || `FINDING-${i}`;
            const desc = f.description || f.explanation || "No description provided.";
            const src = f.source || f.source_ref || {};
            return (
              <div key={fid} style={{
                background: "var(--bg-main)", border: "1px solid var(--border-light)", borderRadius: "8px", padding: "18px 20px",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ width: 24, height: 24, borderRadius: "6px", background: s.bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <Icon size={14} color={s.color} strokeWidth={2.2} />
                    </span>
                    <span style={{ fontSize: "11px", color: s.color, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      {s.label} · {(f.category || "").replace(/_/g, " ")}
                    </span>
                  </div>
                </div>

                <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
                  {f.title}
                </div>

                <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: 1.6, margin: "0 0 10px" }}>
                  {desc}
                </p>

                {(src.file || src.page || src.note_ref) && (
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    Source: {src.file ? `${src.file} ` : ""}{src.page ? `(Page ${src.page})` : ""}{src.note_ref ? ` [${src.note_ref}]` : ""}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 6. WP-514 Financial Statement Review Matrix */}
      {analysisResult?.wp514 && (
        <div style={{ marginBottom: 28 }}>
          <WP514ReviewMatrix wp514Data={analysisResult.wp514} />
        </div>
      )}

      {/* 7. Recommended Review Areas */}
      <div className="fd-card" style={{
        padding: "24px 28px",
      }}>
        <h2 style={{
          fontSize: "17px", color: "var(--text-primary)", fontWeight: 700,
          marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: 8,
        }}>
          7. Recommended Action & Review Areas
        </h2>
        {recommendedReview.length === 0 ? (
          <div style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
            No critical or high severity findings requiring immediate action.
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
                  {f.description || f.explanation || "Materiality review required."}
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
