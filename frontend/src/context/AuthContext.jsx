import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import {
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  fetchCurrentUser,
  loginUser,
  registerUser,
  logoutUser,
  subscribeAuthChange,
} from "../api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState("");
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showAuditHistoryModal, setShowAuditHistoryModal] = useState(false);

  // Initialize Auth State on Mount
  useEffect(() => {
    let mounted = true;

    const initAuth = async () => {
      const token = getAuthToken();
      if (!token) {
        if (mounted) {
          setUser(null);
          setLoading(false);
        }
        return;
      }
      try {
        const u = await fetchCurrentUser();
        if (mounted) {
          setUser(u);
          setAuthError("");
        }
      } catch (err) {
        if (mounted) {
          clearAuthToken();
          setUser(null);
          setAuthError(err.message || "Session expired. Please sign in.");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    initAuth();

    // Subscribe to global 401 events from apiFetch
    const unsubscribe = subscribeAuthChange((newUser, errorMsg) => {
      if (mounted) {
        setUser(newUser);
        if (errorMsg) setAuthError(errorMsg);
      }
    });

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, []);

  const login = useCallback(async (email, password) => {
    setAuthError("");
    const res = await loginUser(email, password);
    setUser(res.user);
    setShowAuthModal(false);
    return res;
  }, []);

  const register = useCallback(async (email, password, fullName) => {
    setAuthError("");
    const res = await registerUser(email, password, fullName);
    setUser(res.user);
    setShowAuthModal(false);
    return res;
  }, []);

  const logout = useCallback(async () => {
    await logoutUser();
    setUser(null);
    setAuthError("");
  }, []);

  const clearError = useCallback(() => {
    setAuthError("");
  }, []);

  const value = {
    user,
    isAuthenticated: !!user,
    loading,
    authError,
    setAuthError,
    clearError,
    login,
    register,
    logout,
    showAuthModal,
    setShowAuthModal,
    showAuditHistoryModal,
    setShowAuditHistoryModal,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
}