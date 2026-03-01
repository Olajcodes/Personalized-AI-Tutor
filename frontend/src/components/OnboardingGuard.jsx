import React, { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const BACKEND_BASE = (import.meta.env.VITE_BACKEND_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

const OnboardingGuard = () => {
  const { token, user, logout } = useAuth();
  const [state, setState] = useState({
    loading: true,
    hasProfile: false,
    error: "",
    unauthorized: false,
  });

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);

    (async () => {
      if (!token) {
        if (active) setState({ loading: false, hasProfile: false, error: "", unauthorized: true });
        return;
      }

      // Non-student roles do not require student profile onboarding.
      if (user?.role && user.role !== "student") {
        if (active) setState({ loading: false, hasProfile: true, error: "", unauthorized: false });
        return;
      }

      try {
        const response = await fetch(`${BACKEND_BASE}/api/v1/students/profile`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        if (!active) return;

        if (response.ok) {
          setState({ loading: false, hasProfile: true, error: "", unauthorized: false });
          return;
        }
        if (response.status === 404) {
          setState({ loading: false, hasProfile: false, error: "", unauthorized: false });
          return;
        }
        if (response.status === 401 || response.status === 403) {
          logout();
          setState({ loading: false, hasProfile: false, error: "", unauthorized: true });
          return;
        }

        const payload = await response.json().catch(() => null);
        setState({
          loading: false,
          hasProfile: false,
          error: payload?.detail || `Profile check failed (${response.status})`,
          unauthorized: false,
        });
      } catch (err) {
        if (!active) return;
        if (err?.name === "AbortError") {
          setState({
            loading: false,
            hasProfile: false,
            error: "Profile check timed out. Please retry.",
            unauthorized: false,
          });
          return;
        }
        setState({
          loading: false,
          hasProfile: false,
          error: err.message || "Profile check failed.",
          unauthorized: false,
        });
      } finally {
        clearTimeout(timer);
      }
    })();

    return () => {
      active = false;
      clearTimeout(timer);
      controller.abort();
    };
  }, [token, user?.role, logout]);

  if (state.loading) {
    return <div className="p-8 text-slate-700">Checking onboarding status...</div>;
  }

  if (state.unauthorized) {
    return <Navigate to="/login" replace />;
  }

  if (state.error) {
    return (
      <div className="p-8">
        <div className="max-w-2xl p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700">
          {state.error}
        </div>
      </div>
    );
  }

  if (!state.hasProfile) {
    return <Navigate to="/classselection" replace />;
  }

  return <Outlet />;
};

export default OnboardingGuard;
