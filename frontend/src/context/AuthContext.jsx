import React, { createContext, useCallback, useContext, useMemo, useState } from "react";
import { decodeJwt, normalizeUserId } from "../api/client";

const TOKEN_KEY = "mastery-ai_token";
const USER_KEY = "mastery-ai_user";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(() => {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  const login = useCallback((authPayload) => {
    const accessToken = authPayload?.access_token || authPayload;
    if (!accessToken) return;
    const decoded = decodeJwt(accessToken);
    const normalizedUser = {
      user_id: normalizeUserId(authPayload) || decoded.user_id || decoded.student_id || null,
      role: authPayload?.role || decoded.role || "student",
      first_name: authPayload?.first_name || null,
      last_name: authPayload?.last_name || null,
      display_name: authPayload?.display_name || null,
    };
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(USER_KEY, JSON.stringify(normalizedUser));
    if (normalizedUser.user_id) {
      localStorage.setItem("mastery_student_id", normalizedUser.user_id);
    }
    setToken(accessToken);
    setUser(normalizedUser);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem("mastery_student_id");
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback((profile) => {
    setUser((prev) => {
      const merged = {
        ...(prev || {}),
        ...(profile || {}),
        user_id: profile?.user_id || prev?.user_id || null,
      };
      const prevJson = JSON.stringify(prev || {});
      const mergedJson = JSON.stringify(merged);
      if (prevJson === mergedJson) return prev;
      localStorage.setItem(USER_KEY, mergedJson);
      return merged;
    });
  }, []);

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      userId: user?.user_id || null,
      login,
      logout,
      refreshUser,
    }),
    [token, user, login, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
