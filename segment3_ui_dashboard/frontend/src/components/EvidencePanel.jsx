import React, { useState, useEffect } from "react";
import { fetchEvidence } from "../api.js";
import { X, FileText, AlertCircle, RefreshCw, CheckCircle2 } from "lucide-react";

export default function EvidencePanel({ documentId, finding, onClose }) {
  const [evidence, setEvidence] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const findingId = finding?.id || finding?.finding_id;

  const loadEvidence = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEvidence(documentId, findingId);
      if (!data) {
        setError("Evidence not available for this finding.");
      } else {
        setEvidence(data);
      }
    } catch (err) {
      setError(err.message || "Evidence not available for this finding.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadEvidence(); }, [documentId, findingId]);

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 9999, display: "flex", justifyContent: "flex-end", background: "rgba(15, 23, 42, 0.4)", backdropFilter: "blur(4px)" }}>
      <div style={{ flex: 1 }} onClick={onClose} />
      <div style={{ width: "100%", maxWidth: 480, height: "100%", background: "var(--bg-card)", borderLeft: "1px solid var(--border-light)", display: "flex", flexDirection: "column", boxShadow: "-8px 0 24px rgba(0,0,0,0.12)", animation: "slideIn 0.2s ease-out" }}>
        <style>{`@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } } @keyframes spin { 100% { transform: rotate(360deg); } }`}</style>

        {/* Header */}
        <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border-light)", display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "11px", color: "var(--color-primary)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 700 }}>
              <FileText size={13} /> Source Evidence
            </div>
            <h2 style={{ fontSize: "15px", color: "var(--text-primary)", margin: "6px 0 0", fontWeight: 700 }}>{finding.title}</h2>
          </div>
          <button id="close-evidence-btn" aria-label="Close evidence panel" onClick={onClose} style={{ background: "transparent", border: "none", color: "var(--text-secondary)", cursor: "pointer", padding: 6, borderRadius: "8px", display: "flex" }}>
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, padding: "24px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 18 }}>
          {loading && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: 240, gap: 12, color: "var(--text-secondary)" }}>
              <RefreshCw size={24} style={{ animation: "spin 1s linear infinite" }} />
              <span style={{ fontSize: "14px" }}>Resolving source evidence...</span>
            </div>
          )}

          {error && !loading && (
            <div style={{ background: "var(--color-danger-soft)", borderRadius: "12px", padding: "20px", textAlign: "center" }}>
              <AlertCircle size={24} color="var(--color-danger)" style={{ margin: "0 auto 10px" }} />
              <div style={{ fontWeight: 700, fontSize: "14px", color: "var(--color-danger)" }}>Evidence Unavailable</div>
              <p style={{ fontSize: "13px", color: "var(--color-danger)", margin: "8px 0 16px" }}>{error}</p>
              <button onClick={loadEvidence} style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "var(--color-primary)", color: "#fff", border: "none", borderRadius: "8px", padding: "8px 16px", fontSize: "12px", fontWeight: 700, cursor: "pointer" }}>
                <RefreshCw size={12} /> Retry
              </button>
            </div>
          )}

          {evidence && !loading && !error && (
            <>
              {/* Status badge */}
              <div style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: "12px", fontWeight: 600, color: evidence.status === "AVAILABLE" ? "var(--color-success)" : "var(--color-warning)", background: evidence.status === "AVAILABLE" ? "var(--color-success-soft)" : "var(--color-warning-soft)", padding: "4px 12px", borderRadius: "20px", alignSelf: "flex-start" }}>
                <CheckCircle2 size={13} />
                {evidence.status === "AVAILABLE" ? "Evidence Found" : "Source Metadata Only"}
              </div>

              {/* Source location */}
              {evidence.source && (
                <div style={{ background: "var(--bg-main)", borderRadius: "12px", padding: "16px", border: "1px solid var(--border-light)" }}>
                  <div style={{ fontSize: "11px", color: "var(--text-secondary)", textTransform: "uppercase", fontWeight: 700, letterSpacing: "0.05em", marginBottom: 8 }}>Source Location</div>
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-primary)" }}>{evidence.source.file || "Source document"}</div>
                  {evidence.source.page && <div style={{ fontSize: "13px", color: "var(--color-primary)", marginTop: 4 }}>Page {evidence.source.page}{evidence.source.note_ref ? ` — ${evidence.source.note_ref}` : ""}</div>}
                  {evidence.source.raw_label && <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: 4 }}>Field: {evidence.source.raw_label}</div>}
                </div>
              )}

              {/* Passage */}
              {evidence.passage && (
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-secondary)", textTransform: "uppercase", fontWeight: 700, letterSpacing: "0.05em", marginBottom: 8 }}>Source Passage</div>
                  <div style={{ background: "var(--bg-main)", borderLeft: "4px solid var(--color-primary)", borderRadius: "0 12px 12px 0", padding: "16px 18px", fontSize: "13px", color: "var(--text-primary)", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
                    {evidence.passage}
                  </div>
                </div>
              )}

              {/* Fallback message */}
              {evidence.message && (
                <div style={{ background: "var(--color-warning-soft)", borderRadius: "12px", padding: "14px", fontSize: "13px", color: "var(--color-warning)" }}>
                  <strong>Note:</strong> {evidence.message}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
