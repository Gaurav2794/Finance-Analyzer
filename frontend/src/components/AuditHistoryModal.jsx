import React, { useState, useEffect } from "react";
import { fetchMyDocuments, deleteDocument } from "../api.js";
import {
  FileSpreadsheet,
  Trash2,
  ExternalLink,
  X,
  Loader2,
  Calendar,
  Award,
  AlertCircle,
  Building,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";

export default function AuditHistoryModal({ isOpen, onClose, currentDocId, onSelectDocument }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  const loadDocuments = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchMyDocuments();
      setDocuments(data || []);
    } catch (err) {
      setError(err.message || "Failed to load audit history");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadDocuments();
    }
  }, [isOpen]);

  const handleDelete = async (docId, e) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this audit record and associated workpapers?")) {
      return;
    }
    setDeletingId(docId);
    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err) {
      alert(err.message || "Failed to delete document");
    } finally {
      setDeletingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(15, 23, 42, 0.6)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        padding: "16px",
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#FFFFFF",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "760px",
          maxHeight: "85vh",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
          border: "1px solid var(--border-light, #E2E8F0)",
          overflow: "hidden",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: "18px 24px",
            background: "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)",
            color: "#FFFFFF",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                background: "rgba(16, 185, 129, 0.2)",
                border: "1px solid rgba(16, 185, 129, 0.4)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#10B981",
              }}
            >
              <FileSpreadsheet size={20} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "#FFFFFF" }}>
                My Audits & Workpaper History
              </h3>
              <p style={{ margin: 0, fontSize: "11px", color: "#94A3B8" }}>
                {documents.length} Persisted Audit Record{documents.length === 1 ? "" : "s"}
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <button
              onClick={loadDocuments}
              title="Refresh list"
              style={{
                background: "rgba(255, 255, 255, 0.1)",
                border: "none",
                color: "#FFFFFF",
                cursor: "pointer",
                padding: "6px",
                borderRadius: "6px",
                display: "flex",
              }}
            >
              <RefreshCw size={15} />
            </button>
            <button
              onClick={onClose}
              style={{
                background: "transparent",
                border: "none",
                color: "#94A3B8",
                cursor: "pointer",
                padding: "4px",
                borderRadius: "6px",
                display: "flex",
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div style={{ padding: "20px 24px", overflowY: "auto", flex: 1 }}>
          {error && (
            <div
              style={{
                padding: "10px 12px",
                borderRadius: "8px",
                background: "#FEE2E2",
                border: "1px solid #FCA5A5",
                color: "#B91C1C",
                fontSize: "12px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "16px",
              }}
            >
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "48px 0", gap: "12px", color: "#64748B" }}>
              <Loader2 size={28} className="animate-spin" style={{ color: "#059669" }} />
              <span style={{ fontSize: "13px" }}>Loading your audit history…</span>
            </div>
          ) : documents.length === 0 ? (
            <div style={{ textAlign: "center", padding: "48px 16px", color: "#64748B" }}>
              <Building size={40} style={{ color: "#CBD5E1", margin: "0 auto 12px" }} />
              <h4 style={{ fontSize: "15px", fontWeight: 600, color: "#1E293B", margin: "0 0 4px" }}>
                No Audits Found
              </h4>
              <p style={{ fontSize: "12.5px", color: "#64748B", margin: 0 }}>
                Upload a financial statement (.xlsx, .pdf, .csv) to generate your first audit report.
              </p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {documents.map((doc) => {
                const isCurrent = doc.id === currentDocId;
                const score = doc.overall_score !== null ? `${Number(doc.overall_score).toFixed(1)}/100` : "--";
                const isExcellent = (doc.overall_score || 0) >= 90;

                return (
                  <div
                    key={doc.id}
                    onClick={() => {
                      onSelectDocument(doc.id);
                      onClose();
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "14px 16px",
                      borderRadius: "10px",
                      border: isCurrent ? "2px solid #059669" : "1px solid var(--border-light, #E2E8F0)",
                      background: isCurrent ? "rgba(16, 185, 129, 0.04)" : "#FFFFFF",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                    onMouseEnter={(e) => {
                      if (!isCurrent) e.currentTarget.style.borderColor = "#CBD5E1";
                      if (!isCurrent) e.currentTarget.style.boxShadow = "0 2px 4px rgba(0,0,0,0.04)";
                    }}
                    onMouseLeave={(e) => {
                      if (!isCurrent) e.currentTarget.style.borderColor = "#E2E8F0";
                      if (!isCurrent) e.currentTarget.style.boxShadow = "none";
                    }}
                  >
                    {/* Left details */}
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      <div
                        style={{
                          width: "38px",
                          height: "38px",
                          borderRadius: "8px",
                          background: isCurrent ? "#059669" : "#F1F5F9",
                          color: isCurrent ? "#FFFFFF" : "#475569",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontWeight: 700,
                          fontSize: "11px",
                        }}
                      >
                        {doc.id.replace("DOC-", "").slice(0, 4)}
                      </div>
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span style={{ fontSize: "13.5px", fontWeight: 700, color: "#0F172A" }}>
                            {doc.company_name}
                          </span>
                          {isCurrent && (
                            <span
                              style={{
                                fontSize: "10px",
                                fontWeight: 700,
                                background: "#D1FAE5",
                                color: "#059669",
                                padding: "1px 6px",
                                borderRadius: "4px",
                              }}
                            >
                              CURRENT
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: "11.5px", color: "#64748B", marginTop: "2px", display: "flex", gap: "10px" }}>
                          <span>{doc.filename}</span>
                          {doc.period && <span>• {doc.period}</span>}
                          <span>• {doc.created_at}</span>
                        </div>
                      </div>
                    </div>

                    {/* Right score and actions */}
                    <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                      <div style={{ textAlign: "right" }}>
                        <div
                          style={{
                            fontSize: "13px",
                            fontWeight: 800,
                            color: isExcellent ? "#059669" : "#D97706",
                          }}
                        >
                          {score}
                        </div>
                        <span
                          style={{
                            fontSize: "9.5px",
                            fontWeight: 700,
                            padding: "1px 6px",
                            borderRadius: "4px",
                            background: doc.status === "COMPLETED" ? "#D1FAE5" : "#FEF3C7",
                            color: doc.status === "COMPLETED" ? "#059669" : "#D97706",
                            textTransform: "uppercase",
                          }}
                        >
                          {doc.overall_status || doc.status}
                        </span>
                      </div>

                      <button
                        onClick={(e) => handleDelete(doc.id, e)}
                        disabled={deletingId === doc.id}
                        title="Delete audit record"
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "#94A3B8",
                          cursor: "pointer",
                          padding: "6px",
                          borderRadius: "6px",
                          display: "flex",
                          transition: "color 0.15s ease",
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.color = "#EF4444")}
                        onMouseLeave={(e) => (e.currentTarget.style.color = "#94A3B8")}
                      >
                        {deletingId === doc.id ? (
                          <Loader2 size={16} className="animate-spin" />
                        ) : (
                          <Trash2 size={16} />
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
