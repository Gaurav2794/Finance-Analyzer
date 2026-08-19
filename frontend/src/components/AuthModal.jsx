import React, { useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import { ShieldCheck, Lock, Mail, User, X, Loader2, AlertCircle, Sparkles } from "lucide-react";

export default function AuthModal({ isOpen, onClose }) {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isRegister) {
        await register(email, password, fullName);
      } else {
        await login(email, password);
      }
      onClose();
    } catch (err) {
      setError(err.message || "Authentication failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError("");
    setLoading(true);
    try {
      await login("demo@financeanalyzer.local", "DemoPassword123!");
      onClose();
    } catch (err) {
      // If demo user does not exist yet on fresh DB, register it
      try {
        await register("demo@financeanalyzer.local", "DemoPassword123!", "Demo Auditor");
        onClose();
      } catch (regErr) {
        setError(regErr.message || "Demo login failed");
      }
    } finally {
      setLoading(false);
    }
  };

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
          maxWidth: "420px",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
          border: "1px solid var(--border-light, #E2E8F0)",
          overflow: "hidden",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: "20px 24px",
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
              <ShieldCheck size={20} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "#FFFFFF" }}>
                {isRegister ? "Create Auditor Account" : "Auditor Sign In"}
              </h3>
              <p style={{ margin: 0, fontSize: "11px", color: "#94A3B8" }}>
                Finance Analyzer Multi-Tenant Access
              </p>
            </div>
          </div>
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

        {/* Form Body */}
        <div style={{ padding: "24px" }}>
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
              <AlertCircle size={16} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {isRegister && (
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "11.5px",
                    fontWeight: 600,
                    color: "var(--text-secondary, #475569)",
                    marginBottom: "6px",
                  }}
                >
                  Full Name
                </label>
                <div style={{ position: "relative" }}>
                  <User
                    size={16}
                    style={{
                      position: "absolute",
                      left: "12px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      color: "#94A3B8",
                    }}
                  />
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Aditya Dolas"
                    style={{
                      width: "100%",
                      padding: "9px 12px 9px 36px",
                      borderRadius: "8px",
                      border: "1px solid var(--border-light, #CBD5E1)",
                      fontSize: "13px",
                      outline: "none",
                      boxSizing: "border-box",
                    }}
                  />
                </div>
              </div>
            )}

            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "11.5px",
                  fontWeight: 600,
                  color: "var(--text-secondary, #475569)",
                  marginBottom: "6px",
                }}
              >
                Work Email
              </label>
              <div style={{ position: "relative" }}>
                <Mail
                  size={16}
                  style={{
                    position: "absolute",
                    left: "12px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "#94A3B8",
                  }}
                />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="auditor@firm.com"
                  style={{
                    width: "100%",
                    padding: "9px 12px 9px 36px",
                    borderRadius: "8px",
                    border: "1px solid var(--border-light, #CBD5E1)",
                    fontSize: "13px",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />
              </div>
            </div>

            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "11.5px",
                  fontWeight: 600,
                  color: "var(--text-secondary, #475569)",
                  marginBottom: "6px",
                }}
              >
                Password
              </label>
              <div style={{ position: "relative" }}>
                <Lock
                  size={16}
                  style={{
                    position: "absolute",
                    left: "12px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "#94A3B8",
                  }}
                />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  minLength={6}
                  style={{
                    width: "100%",
                    padding: "9px 12px 9px 36px",
                    borderRadius: "8px",
                    border: "1px solid var(--border-light, #CBD5E1)",
                    fontSize: "13px",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: "6px",
                width: "100%",
                padding: "10px",
                borderRadius: "8px",
                border: "none",
                background: "#059669",
                color: "#FFFFFF",
                fontSize: "13px",
                fontWeight: 700,
                cursor: loading ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                boxShadow: "0 2px 4px rgba(5, 150, 105, 0.2)",
              }}
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : isRegister ? "Create Account" : "Sign In"}
            </button>
          </form>

          {/* Quick Demo Login Option */}
          <div style={{ marginTop: "16px", textAlign: "center" }}>
            <button
              type="button"
              onClick={handleDemoLogin}
              disabled={loading}
              style={{
                width: "100%",
                padding: "8px",
                borderRadius: "8px",
                border: "1px dashed #10B981",
                background: "rgba(16, 185, 129, 0.05)",
                color: "#059669",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "6px",
              }}
            >
              <Sparkles size={14} /> Quick Demo Login (demo@financeanalyzer.local)
            </button>
          </div>

          {/* Toggle Register / Login */}
          <div
            style={{
              marginTop: "18px",
              textAlign: "center",
              fontSize: "12px",
              color: "var(--text-secondary, #64748B)",
            }}
          >
            {isRegister ? "Already have an auditor account? " : "Need an auditor account? "}
            <button
              type="button"
              onClick={() => {
                setIsRegister(!isRegister);
                setError("");
              }}
              style={{
                background: "transparent",
                border: "none",
                color: "#059669",
                fontWeight: 700,
                cursor: "pointer",
                padding: 0,
              }}
            >
              {isRegister ? "Sign In" : "Create one"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
