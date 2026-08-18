import React, { useState, useEffect } from "react";
import {
  X,
  Sparkles,
  ShieldCheck,
  Copy,
  Check,
  RefreshCw,
  AlertCircle,
  HelpCircle,
  Search,
  ArrowRight,
  FileCheck2,
  Layers,
  Send,
} from "lucide-react";
import { askAI } from "../api.js";

export default function AskAIPanel({ finding, documentId, onClose }) {
  const [copied, setCopied] = useState(false);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeQuestion, setActiveQuestion] = useState("Why was this flagged?");
  const [customInput, setCustomInput] = useState("");
  const [mode, setMode] = useState(finding ? "finding" : "report");

  const findingId = finding?.id || finding?.finding_id;

  const fetchAI = async (questionText, targetFindingId = findingId) => {
    const q = questionText || activeQuestion;
    setActiveQuestion(q);
    setLoading(true);
    setError(null);

    try {
      if (documentId) {
        const res = await askAI(documentId, targetFindingId, q, finding?.category);
        setResponse(res);
      } else {
        // Fallback local response
        setResponse({
          answer: finding
            ? `${finding.title}: ${finding.description || "Review required."}`
            : "Grounded review assistance is ready for your document.",
          sections: [
            {
              title: "System Result",
              content: finding
                ? `Flagged as ${finding.severity} under ${(finding.category || "").replace(/_/g, " ")}.`
                : "General document review overview.",
            },
            {
              title: "Recommended Review",
              content: "Verify source lines and supporting disclosures in working papers.",
            },
          ],
          grounded: true,
          sources: [],
          ai_provider: "local",
        });
      }
    } catch (err) {
      setError(err.message || "Failed to generate AI explanation.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAI("Why was this flagged?", findingId);
  }, [findingId, documentId]);

  const handleCopy = () => {
    if (!response) return;
    const textToCopy = response.sections
      ? `${response.answer}\n\n` +
        response.sections.map((s) => `### ${s.title}\n${s.content}`).join("\n\n")
      : response.answer || "";
    navigator.clipboard?.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    if (!customInput.trim()) return;
    fetchAI(customInput.trim(), mode === "finding" ? findingId : null);
    setCustomInput("");
  };

  const findingQuestions = [
    "Why was this flagged?",
    "What changed?",
    "What is the evidence?",
    "What should I review?",
    "Explain this finding",
    "Explain the threshold",
  ];

  const reportQuestions = [
    "Summarize this financial statement.",
    "What are the highest-risk findings?",
    "What should the reviewer focus on?",
    "Explain the key ratios.",
    "Explain the unusual fluctuations.",
    "Give me an executive summary.",
  ];

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        justifyContent: "flex-end",
        background: "rgba(10, 46, 29, 0.45)",
        backdropFilter: "blur(4px)",
      }}
    >
      {/* Backdrop */}
      <div style={{ flex: 1 }} onClick={onClose} />

      {/* Drawer */}
      <div
        style={{
          width: "100%",
          maxWidth: 520,
          height: "100%",
          background: "var(--bg-card, #FFFFFF)",
          borderLeft: "1px solid var(--border-light, #E2E8F0)",
          display: "flex",
          flexDirection: "column",
          boxShadow: "-8px 0 28px rgba(0, 0, 0, 0.2)",
          animation: "slideIn 0.2s ease-out",
        }}
      >
        <style>{`
          @keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
          @keyframes spin { 100% { transform: rotate(360deg); } }
        `}</style>

        {/* Drawer Header */}
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid var(--border-light, #E2E8F0)",
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: 12,
            background: "linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(255, 255, 255, 1) 100%)",
          }}
        >
          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontSize: "11px",
                color: "var(--color-primary, #059669)",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                fontWeight: 800,
              }}
            >
              <Sparkles size={14} /> AI Financial Review Assistant
            </div>
            <h2
              style={{
                fontSize: "16px",
                color: "var(--text-primary, #0F172A)",
                margin: "4px 0 0",
                fontWeight: 700,
              }}
            >
              {finding ? finding.title : "Document Review Assistant"}
            </h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close AI panel"
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-secondary, #64748B)",
              cursor: "pointer",
              padding: 6,
              display: "flex",
              borderRadius: "8px",
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Scope Mode Switcher */}
        <div
          style={{
            padding: "10px 24px",
            background: "var(--bg-main, #F8FAFC)",
            borderBottom: "1px solid var(--border-light, #E2E8F0)",
            display: "flex",
            gap: 8,
          }}
        >
          {finding && (
            <button
              onClick={() => {
                setMode("finding");
                fetchAI("Why was this flagged?", findingId);
              }}
              style={{
                flex: 1,
                padding: "6px 12px",
                borderRadius: "6px",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
                border: "none",
                background: mode === "finding" ? "var(--color-primary, #059669)" : "transparent",
                color: mode === "finding" ? "#FFFFFF" : "var(--text-secondary, #64748B)",
              }}
            >
              Finding Context
            </button>
          )}
          <button
            onClick={() => {
              setMode("report");
              fetchAI("Give me an executive summary.", null);
            }}
            style={{
              flex: 1,
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: 600,
              cursor: "pointer",
              border: "none",
              background: mode === "report" ? "var(--color-primary, #059669)" : "transparent",
              color: mode === "report" ? "#FFFFFF" : "var(--text-secondary, #64748B)",
            }}
          >
            Full Report Context
          </button>
        </div>

        {/* Drawer Body */}
        <div style={{ flex: 1, padding: "20px 24px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Finding / Context Banner */}
          {mode === "finding" && finding && (
            <div
              style={{
                background: "var(--bg-main, #F8FAFC)",
                border: "1px solid var(--border-light, #E2E8F0)",
                borderRadius: "10px",
                padding: "12px 16px",
                display: "flex",
                flexDirection: "column",
                gap: 4,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    color: "var(--color-primary, #059669)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  SYSTEM RESULT · {(finding.category || "").replace(/_/g, " ")}
                </span>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background:
                      finding.severity === "CRITICAL"
                        ? "rgba(239, 68, 68, 0.12)"
                        : finding.severity === "HIGH"
                        ? "rgba(245, 158, 11, 0.12)"
                        : "rgba(16, 185, 129, 0.12)",
                    color:
                      finding.severity === "CRITICAL"
                        ? "#DC2626"
                        : finding.severity === "HIGH"
                        ? "#D97706"
                        : "#059669",
                  }}
                >
                  {finding.severity}
                </span>
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-secondary, #64748B)", marginTop: 2 }}>
                {finding.description}
              </div>
            </div>
          )}

          {/* Quick preset chips */}
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary, #64748B)", marginBottom: 8, textTransform: "uppercase" }}>
              Suggested Questions
            </div>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
              {(mode === "finding" ? findingQuestions : reportQuestions).map((q) => (
                <button
                  key={q}
                  onClick={() => fetchAI(q, mode === "finding" ? findingId : null)}
                  style={{
                    background: activeQuestion === q ? "var(--color-primary-soft, #ECFDF5)" : "var(--bg-main, #F8FAFC)",
                    color: activeQuestion === q ? "var(--color-primary, #059669)" : "var(--text-secondary, #64748B)",
                    border: `1px solid ${activeQuestion === q ? "var(--color-primary, #059669)" : "var(--border-light, #E2E8F0)"}`,
                    borderRadius: "14px",
                    padding: "4px 10px",
                    fontSize: "11px",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: 180,
                gap: 12,
                color: "var(--text-secondary, #64748B)",
              }}
            >
              <RefreshCw size={24} color="var(--color-primary, #059669)" style={{ animation: "spin 1s linear infinite" }} />
              <span style={{ fontSize: "13px", fontWeight: 500 }}>Generating grounded explanation...</span>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div style={{ background: "rgba(239, 68, 68, 0.08)", borderRadius: "10px", padding: "16px", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#DC2626", fontWeight: 700, fontSize: "13px" }}>
                <AlertCircle size={16} /> AI assistance temporarily unavailable
              </div>
              <p style={{ fontSize: "12px", color: "#DC2626", margin: "6px 0 10px" }}>{error}</p>
              <button
                onClick={() => fetchAI(activeQuestion, mode === "finding" ? findingId : null)}
                className="fd-btn fd-btn-primary"
                style={{ fontSize: "11px", padding: "4px 10px" }}
              >
                Retry
              </button>
            </div>
          )}

          {/* AI Response Display */}
          {!loading && !error && response && (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {/* Executive Answer Card */}
              <div
                style={{
                  background: "var(--bg-card, #FFFFFF)",
                  border: "1px solid var(--border-light, #E2E8F0)",
                  borderRadius: "10px",
                  padding: "16px 18px",
                  boxShadow: "0 1px 3px rgba(0, 0, 0, 0.04)",
                  borderLeft: "4px solid var(--color-primary, #059669)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--color-primary, #059669)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      AI Grounded Summary
                    </span>
                    <span style={{
                      fontSize: "10px",
                      fontWeight: 600,
                      padding: "2px 6px",
                      borderRadius: "4px",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      background: response.ai_provider === "gemini" ? "var(--color-primary-soft, #ECFDF5)" : "var(--bg-main, #F8FAFC)",
                      color: response.ai_provider === "gemini" ? "var(--color-primary, #059669)" : "var(--text-secondary, #64748B)",
                      border: "1px solid var(--border-light, #E2E8F0)",
                    }}>
                      <span style={{ width: 5, height: 5, borderRadius: "50%", background: response.ai_provider === "gemini" ? "#10B981" : "#94A3B8" }} />
                      {response.ai_provider === "gemini" ? "Gemini" : "Grounded Fallback"}
                    </span>
                  </div>
                  <button
                    onClick={handleCopy}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                      background: copied ? "var(--color-success-soft, #D1FAE5)" : "var(--bg-main, #F8FAFC)",
                      border: `1px solid ${copied ? "var(--color-success, #10B981)" : "var(--border-light, #E2E8F0)"}`,
                      color: copied ? "var(--color-success, #10B981)" : "var(--text-secondary, #64748B)",
                      borderRadius: "6px",
                      padding: "3px 8px",
                      fontSize: "11px",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    {copied ? <Check size={11} /> : <Copy size={11} />}
                    {copied ? "Copied" : "Copy"}
                  </button>
                </div>
                <div style={{ fontSize: "13px", color: "var(--text-primary, #0F172A)", lineHeight: 1.6, fontWeight: 500 }}>
                  {response.answer}
                </div>
              </div>

              {/* Structured Sections */}
              {response.sections &&
                response.sections.map((sec, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: "var(--bg-main, #F8FAFC)",
                      border: "1px solid var(--border-light, #E2E8F0)",
                      borderRadius: "8px",
                      padding: "14px 16px",
                    }}
                  >
                    <div
                      style={{
                        fontSize: "11px",
                        fontWeight: 700,
                        color: "var(--text-secondary, #64748B)",
                        textTransform: "uppercase",
                        letterSpacing: "0.04em",
                        marginBottom: 6,
                      }}
                    >
                      {sec.title}
                    </div>
                    <div
                      style={{
                        fontSize: "12px",
                        color: "var(--text-primary, #0F172A)",
                        lineHeight: 1.6,
                        whiteSpace: "pre-wrap",
                      }}
                    >
                      {sec.content}
                    </div>
                  </div>
                ))}

              {/* Sources */}
              {response.sources && response.sources.length > 0 && (
                <div
                  style={{
                    background: "var(--bg-card, #FFFFFF)",
                    borderRadius: "8px",
                    padding: "12px 14px",
                    border: "1px solid var(--border-light, #E2E8F0)",
                  }}
                >
                  <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary, #64748B)", textTransform: "uppercase", marginBottom: 6 }}>
                    Verified Sources
                  </div>
                  {response.sources.map((src, i) => (
                    <div key={i} style={{ fontSize: "11px", color: "var(--text-primary, #0F172A)", marginBottom: 3 }}>
                      • {src.description || src.file}
                      {src.page != null ? ` (Page ${src.page})` : src.sheet ? ` (Sheet: ${src.sheet})` : ""}
                    </div>
                  ))}
                </div>
              )}

              {/* Groundedness Badge */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "10px 14px",
                  borderRadius: "8px",
                  background: response.grounded ? "var(--color-primary-soft, #ECFDF5)" : "rgba(239, 68, 68, 0.08)",
                  border: `1px solid ${response.grounded ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.2)"}`,
                }}
              >
                <ShieldCheck size={16} color={response.grounded ? "var(--color-primary, #059669)" : "#DC2626"} />
                <span style={{ fontSize: "11px", color: response.grounded ? "var(--color-primary, #059669)" : "#DC2626", fontWeight: 600 }}>
                  {response.grounded
                    ? "Grounded in verified Team 1 + Team 2 review outputs"
                    : "Information not fully available in source filing"}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Drawer Footer / Custom Query Input */}
        <form
          onSubmit={handleCustomSubmit}
          style={{
            padding: "14px 20px",
            borderTop: "1px solid var(--border-light, #E2E8F0)",
            background: "var(--bg-card, #FFFFFF)",
            display: "flex",
            gap: 8,
          }}
        >
          <input
            type="text"
            placeholder={mode === "finding" ? "Ask a question about this finding..." : "Ask a question about the report..."}
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            style={{
              flex: 1,
              padding: "9px 14px",
              borderRadius: "8px",
              border: "1px solid var(--border-light, #E2E8F0)",
              fontSize: "12px",
              color: "var(--text-primary, #0F172A)",
              outline: "none",
              background: "var(--bg-main, #F8FAFC)",
            }}
          />
          <button
            type="submit"
            disabled={!customInput.trim() || loading}
            style={{
              padding: "0 14px",
              borderRadius: "8px",
              background: "var(--color-primary, #059669)",
              color: "#FFFFFF",
              border: "none",
              cursor: customInput.trim() && !loading ? "pointer" : "not-allowed",
              opacity: customInput.trim() && !loading ? 1 : 0.6,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Send size={15} />
          </button>
        </form>
      </div>
    </div>
  );
}
