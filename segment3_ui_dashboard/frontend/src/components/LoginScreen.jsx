import React, { useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import {
  ShieldCheck,
  Lock,
  Mail,
  User,
  Loader2,
  AlertCircle,
  Sparkles,
  Activity,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";

export default function LoginScreen() {
  const { login, register, authError, clearError } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState("");

  const displayError = localError || authError;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError("");
    clearError();

    if (isRegister) {
      if (password !== confirmPassword) {
        setLocalError("Passwords do not match.");
        return;
      }
      if (password.length < 6) {
        setLocalError("Password must be at least 6 characters long.");
        return;
      }
    }

    setLoading(true);
    try {
      if (isRegister) {
        await register(email, password, fullName);
      } else {
        await login(email, password);
      }
    } catch (err) {
      setLocalError(err.message || "Authentication failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setLocalError("");
    clearError();
    setLoading(true);
    try {
      await login("auditor@example.com", "DemoPassword123!");
    } catch (err) {
      try {
        await login("demo@financeanalyzer.local", "DemoPassword123!");
      } catch (fallbackErr) {
        setLocalError(err.message || "Demo login failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg-main, #F8FAFC)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
      }}
    >
      <div style={{ maxWidth: "440px", width: "100%" }}>
        {/* Brand Header */}
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "14px",
              background: "linear-gradient(135deg, #059669 0%, #10B981 100%)",
              color: "#FFFFFF",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
              boxShadow: "0 10px 15px -3px rgba(16, 185, 129, 0.3)",
            }}
          >
            <Activity size={30} strokeWidth={2.5} />
          </div>
          <h1 style={{ fontSize: "26px", fontWeight: 800, color: "var(--text-primary, #0F172A)", margin: "0 0 6px" }}>
            Finance Analyzer
          </h1>
          <p style={{ color: "var(--text-secondary, #64748B)", fontSize: "13.5px", margin: 0 }}>
            Automated Financial Statement & WP-514 Audit Platform
          </p>
        </div>

        {/* Card Container */}
        <div
          className="fd-card animate-fade-up"
          style={{
            background: "#FFFFFF",
            borderRadius: "16px",
            boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01)",
            border: "1px solid var(--border-light, #E2E8F0)",
            overflow: "hidden",
          }}
        >
          {/* Header Tab Toggle */}
          <div
            style={{
              display: "flex",
              borderBottom: "1px solid var(--border-light, #E2E8F0)",
              background: "#F8FAFC",
            }}
          >
            <button
              type="button"
              onClick={() => {
                setIsRegister(false);
                setLocalError("");
                clearError();
              }}
              style={{
                flex: 1,
                padding: "14px",
                border: "none",
                background: !isRegister ? "#FFFFFF" : "transparent",
                fontWeight: !isRegister ? 700 : 600,
                color: !isRegister ? "#059669" : "var(--text-secondary, #64748B)",
                fontSize: "13.5px",
                cursor: "pointer",
                borderBottom: !isRegister ? "2px solid #059669" : "none",
                transition: "all 0.15s ease",
              }}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setIsRegister(true);
                setLocalError("");
                clearError();
              }}
              style={{
                flex: 1,
                padding: "14px",
                border: "none",
                background: isRegister ? "#FFFFFF" : "transparent",
                fontWeight: isRegister ? 700 : 600,
                color: isRegister ? "#059669" : "var(--text-secondary, #64748B)",
                fontSize: "13.5px",
                cursor: "pointer",
                borderBottom: isRegister ? "2px solid #059669" : "none",
                transition: "all 0.15s ease",
              }}
            >
              Create Account
            </button>
          </div>

          {/* Form Content */}
          <div style={{ padding: "28px" }}>
            {displayError && (
              <div
                style={{
                  padding: "11px 14px",
                  borderRadius: "8px",
                  background: "#FEE2E2",
                  border: "1px solid #FCA5A5",
                  color: "#B91C1C",
                  fontSize: "12.5px",
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "10px",
                  marginBottom: "18px",
                }}
              >
                <AlertCircle size={16} style={{ flexShrink: 0, marginTop: "2px" }} />
                <span style={{ lineHeight: 1.4 }}>{displayError}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {isRegister && (
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "12px",
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
                      required={isRegister}
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Auditor Lead"
                      style={{
                        width: "100%",
                        padding: "10px 12px 10px 36px",
                        borderRadius: "8px",
                        border: "1px solid var(--border-light, #CBD5E1)",
                        fontSize: "13.5px",
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
                    fontSize: "12px",
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
                    placeholder="auditor@example.com"
                    style={{
                      width: "100%",
                      padding: "10px 12px 10px 36px",
                      borderRadius: "8px",
                      border: "1px solid var(--border-light, #CBD5E1)",
                      fontSize: "13.5px",
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
                    fontSize: "12px",
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
                      padding: "10px 12px 10px 36px",
                      borderRadius: "8px",
                      border: "1px solid var(--border-light, #CBD5E1)",
                      fontSize: "13.5px",
                      outline: "none",
                      boxSizing: "border-box",
                    }}
                  />
                </div>
              </div>

              {isRegister && (
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "12px",
                      fontWeight: 600,
                      color: "var(--text-secondary, #475569)",
                      marginBottom: "6px",
                    }}
                  >
                    Confirm Password
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
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      minLength={6}
                      style={{
                        width: "100%",
                        padding: "10px 12px 10px 36px",
                        borderRadius: "8px",
                        border: "1px solid var(--border-light, #CBD5E1)",
                        fontSize: "13.5px",
                        outline: "none",
                        boxSizing: "border-box",
                      }}
                    />
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                style={{
                  marginTop: "6px",
                  width: "100%",
                  padding: "11px",
                  borderRadius: "8px",
                  border: "none",
                  background: "#059669",
                  color: "#FFFFFF",
                  fontSize: "14px",
                  fontWeight: 700,
                  cursor: loading ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  boxShadow: "0 4px 6px -1px rgba(5, 150, 105, 0.2)",
                  transition: "background 0.15s ease",
                }}
              >
                {loading ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : isRegister ? (
                  <>Create Auditor Account <ArrowRight size={16} /></>
                ) : (
                  <>Sign In to Audit Workspace <ArrowRight size={16} /></>
                )}
              </button>
            </form>

            {/* Quick Demo Access */}
            <div style={{ marginTop: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <div style={{ flex: 1, height: "1px", background: "var(--border-light, #E2E8F0)" }} />
                <span style={{ fontSize: "11px", color: "#94A3B8", textTransform: "uppercase", fontWeight: 700, letterSpacing: "0.05em" }}>
                  Fast Demo Access
                </span>
                <div style={{ flex: 1, height: "1px", background: "var(--border-light, #E2E8F0)" }} />
              </div>

              <button
                type="button"
                onClick={handleDemoLogin}
                disabled={loading}
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  borderRadius: "8px",
                  border: "1px dashed #10B981",
                  background: "rgba(16, 185, 129, 0.05)",
                  color: "#059669",
                  fontSize: "12.5px",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  transition: "background 0.15s ease",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(16, 185, 129, 0.1)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(16, 185, 129, 0.05)")}
              >
                <Sparkles size={15} /> Sign in as Lead Auditor (auditor@example.com)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}