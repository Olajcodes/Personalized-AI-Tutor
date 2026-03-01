import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

const BACKEND_BASE = (import.meta.env.VITE_BACKEND_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

async function callTeacherApi(path, token) {
  const response = await fetch(`${BACKEND_BASE}/api/v1${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) throw new Error(payload?.detail || `Failed: ${path}`);
  return payload;
}

const ConceptAnalyticsPage = () => {
  const { token } = useAuth();
  const [classes, setClasses] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [alerts, setAlerts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      if (!token) return;
      setLoading(true);
      setError("");
      try {
        const classList = await callTeacherApi("/teachers/classes", token);
        if (!active) return;
        const rows = classList.classes || [];
        setClasses(rows);
        if (rows.length) setSelectedClassId(rows[0].id);
      } catch (err) {
        if (!active) return;
        setError(err.message || "Unable to load teacher classes.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [token]);

  useEffect(() => {
    let active = true;
    (async () => {
      if (!token || !selectedClassId) return;
      try {
        const [d, h, a] = await Promise.all([
          callTeacherApi(`/teachers/classes/${selectedClassId}/dashboard`, token),
          callTeacherApi(`/teachers/classes/${selectedClassId}/heatmap`, token),
          callTeacherApi(`/teachers/classes/${selectedClassId}/alerts`, token),
        ]);
        if (!active) return;
        setDashboard(d);
        setHeatmap(h);
        setAlerts(a);
      } catch (err) {
        if (!active) return;
        setError(err.message || "Unable to load class analytics.");
      }
    })();
    return () => {
      active = false;
    };
  }, [token, selectedClassId]);

  if (loading) return <main className="p-8">Loading teacher analytics...</main>;

  return (
    <main className="p-8 space-y-6">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Teacher Analytics</h1>
          <p className="text-slate-500 text-sm mt-1">Live class dashboard, heatmap, and alerts.</p>
        </div>
        <select value={selectedClassId || ""} onChange={(e) => setSelectedClassId(e.target.value)} className="border border-slate-300 rounded-lg px-3 py-2 bg-white">
          {classes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </header>

      {error && <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">{error}</div>}

      {dashboard && (
        <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4">Class KPI</h2>
          <pre className="text-xs bg-slate-50 p-4 rounded-lg overflow-auto">{JSON.stringify(dashboard, null, 2)}</pre>
        </section>
      )}

      {heatmap && (
        <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4">Heatmap</h2>
          <pre className="text-xs bg-slate-50 p-4 rounded-lg overflow-auto">{JSON.stringify(heatmap, null, 2)}</pre>
        </section>
      )}

      {alerts && (
        <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4">Alerts</h2>
          <pre className="text-xs bg-slate-50 p-4 rounded-lg overflow-auto">{JSON.stringify(alerts, null, 2)}</pre>
        </section>
      )}
    </main>
  );
};

export default ConceptAnalyticsPage;
