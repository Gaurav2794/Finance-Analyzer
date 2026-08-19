import React, { createContext, useContext, useState, useEffect } from "react";
import {
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  fetchCurrentUser,
  loginUser,
  registerUser,
  logoutUser,
} from "../api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showAuditHistoryModal, setShowAuditHistoryModal] = useState(false);

  useEffect(() => {
    const initAuth = async () => {
      const token = getAuthToken();
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const u = await fetchCurrentUser();
        setUser(u);
      } catch (err) {
        clearAuthToken();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    initAuth();
  }, []);

  const login = async (email, password) => {
    const res = await loginUser(email, password);
    setUser(res.user);
    setShowAuthModal(false);
    return res;
  };

  const register = async (email, password, fullName) => {
    const res = await registerUser(email, password, fullName);
    setUser(res.user);
    setShowAuthModal(false);
    return res;
  };

  const logout = async () => {
    await logoutUser();
    setUser(null);
  };

  const value = {
    user,
    isAuthenticated: !!user,
    loading,
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
  return ctx;
}
