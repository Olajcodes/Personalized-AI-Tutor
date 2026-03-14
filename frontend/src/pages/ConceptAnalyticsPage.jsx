import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  BookOpenCheck,
  BrainCircuit,
  Flame,
  GitBranch,
  Loader2,
  Route,
  ShieldAlert,
  Users,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import TeacherClassGraph from '../components/teacher/TeacherClassGraph';

const humanizeConceptId = (conceptId, fallback = 'Concept') => {
  const value = String(conceptId || '').trim();
  if (!value) return fallback;
  const token = value.split(':').pop()?.trim() || value;
  return token
    .replace(/-(\d+)$/, '')
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase()) || fallback;
};

const formatStudyTime = (seconds) => {
  const total = Number(seconds || 0);
  if (!total) return '0m';
  const minutes = Math.round(total / 60);
  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;
  return hours > 0 ? `${hours}h ${remaining}m` : `${remaining}m`;
};

const StatCard = ({ title, value, subtitle, icon: Icon, tone = 'indigo' }) => {
  const tones = {
    indigo: 'bg-indigo-50 text-indigo-600',
    amber: 'bg-amber-50 text-amber-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    slate: 'bg-slate-100 text-slate-700',
  };
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h3 className="mb-2 text-sm font-semibold text-slate-500">{title}</h3>
          <span className="text-3xl font-black text-slate-800">{value}</span>
          {subtitle ? <p className="mt-2 text-xs font-medium text-slate-500">{subtitle}</p> : null}
        </div>
        <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${tones[tone] || tones.indigo}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
};

const ConceptAnalyticsPage = () => {
  const { token } = useAuth();
  const apiUrl = import.meta.env.VITE_API_URL;

  const [classes, setClasses] = useState([]);
  const [activeClassId, setActiveClassId] = useState('');
  const [dashboard, setDashboard] = useState(null);
  const [heatmap, setHeatmap] = useState([]);
  const [graphSummary, setGraphSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [isLoadingClasses, setIsLoadingClasses] = useState(true);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchClasses = async () => {
      if (!token) {
        setIsLoadingClasses(false);
        setError('Teacher analytics requires an authenticated teacher account.');
        return;
      }

      try {
        setError('');
        const response = await fetch(`${apiUrl}/teachers/classes`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) {
          const detail = await response.json().catch(() => null);
          throw new Error(detail?.detail || 'Failed to load teacher classes.');
        }
        const data = await response.json();
        const classList = Array.isArray(data?.classes) ? data.classes : [];
        setClasses(classList);
        if (classList.length > 0) {
          setActiveClassId((current) => current || classList[0].id);
        }
      } catch (err) {
        setClasses([]);
        setError(err.message || 'Teacher analytics is unavailable right now.');
      } finally {
        setIsLoadingClasses(false);
      }
    };

    fetchClasses();
  }, [apiUrl, token]);

  useEffect(() => {
    const fetchAnalytics = async () => {
      if (!token || !activeClassId) {
        setDashboard(null);
        setHeatmap([]);
        setGraphSummary(null);
        setAlerts([]);
        return;
      }

      try {
        setIsLoadingDetails(true);
        setError('');
        const [dashboardRes, heatmapRes, graphRes, alertsRes] = await Promise.all([
          fetch(`${apiUrl}/teachers/classes/${activeClassId}/dashboard`, { headers: { Authorization: `Bearer ${token}` } }),
          fetch(`${apiUrl}/teachers/classes/${activeClassId}/heatmap`, { headers: { Authorization: `Bearer ${token}` } }),
          fetch(`${apiUrl}/teachers/classes/${activeClassId}/graph-summary`, { headers: { Authorization: `Bearer ${token}` } }),
          fetch(`${apiUrl}/teachers/classes/${activeClassId}/alerts`, { headers: { Authorization: `Bearer ${token}` } }),
        ]);

        if (!dashboardRes.ok || !heatmapRes.ok || !graphRes.ok || !alertsRes.ok) {
          const firstFailure = [dashboardRes, heatmapRes, graphRes, alertsRes].find((response) => !response.ok);
          const detail = await firstFailure.json().catch(() => null);
          throw new Error(detail?.detail || 'Failed to load teacher analytics.');
        }

        const [dashboardData, heatmapData, graphData, alertsData] = await Promise.all([
          dashboardRes.json(),
          heatmapRes.json(),
          graphRes.json(),
          alertsRes.json(),
        ]);

        setDashboard(dashboardData);
        setHeatmap(Array.isArray(heatmapData?.points) ? heatmapData.points : []);
        setGraphSummary(graphData || null);
        setAlerts(Array.isArray(alertsData?.alerts) ? alertsData.alerts : []);
      } catch (err) {
        setDashboard(null);
        setHeatmap([]);
        setGraphSummary(null);
        setAlerts([]);
        setError(err.message || 'Teacher analytics is unavailable right now.');
      } finally {
        setIsLoadingDetails(false);
      }
    };

    fetchAnalytics();
  }, [activeClassId, apiUrl, token]);

  const activeClass = useMemo(
    () => classes.find((item) => item.id === activeClassId) || null,
    [activeClassId, classes],
  );
  const weakestConcepts = useMemo(
    () => [...heatmap].sort((a, b) => Number(a.avg_score || 0) - Number(b.avg_score || 0)).slice(0, 8),
    [heatmap],
  );

  const graphMetrics = graphSummary?.metrics || null;
  const graphSignal = graphSummary?.graph_signal || null;
  const graphBlockers = Array.isArray(graphSummary?.weakest_blockers) ? graphSummary.weakest_blockers : [];
  const readyToPush = Array.isArray(graphSummary?.ready_to_push) ? graphSummary.ready_to_push : [];

  return (
    <main className="space-y-8 p-8">
      <header className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Teacher Analytics Hub</h1>
          <p className="mt-1 text-sm text-slate-500">
            {activeClass
              ? `${activeClass.name} - ${activeClass.subject.toUpperCase()} ${activeClass.sss_level} term ${activeClass.term}`
              : 'Track real class mastery, blockers, and graph-driven next steps.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={activeClassId}
            onChange={(event) => setActiveClassId(event.target.value)}
            className="min-w-[260px] rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none focus:border-indigo-500"
            disabled={isLoadingClasses || classes.length === 0}
          >
            {classes.length === 0 ? (
              <option value="">No classes available</option>
            ) : (
              classes.map((teacherClass) => (
                <option key={teacherClass.id} value={teacherClass.id}>
                  {teacherClass.name} - {teacherClass.subject.toUpperCase()} {teacherClass.sss_level} T{teacherClass.term}
                </option>
              ))
            )}
          </select>
        </div>
      </header>

      {isLoadingClasses || isLoadingDetails ? (
        <div className="flex min-h-[320px] flex-col items-center justify-center rounded-3xl border border-slate-200 bg-white text-slate-400 shadow-sm">
          <Loader2 className="mb-3 h-10 w-10 animate-spin text-indigo-500" />
          <p className="text-sm font-semibold">Loading teacher analytics...</p>
        </div>
      ) : error ? (
        <div className="flex min-h-[320px] flex-col items-center justify-center rounded-3xl border border-rose-200 bg-white text-center shadow-sm">
          <AlertCircle className="mb-3 h-10 w-10 text-rose-500" />
          <p className="max-w-xl text-sm font-semibold text-rose-700">{error}</p>
        </div>
      ) : classes.length === 0 ? (
        <div className="flex min-h-[320px] flex-col items-center justify-center rounded-3xl border border-slate-200 bg-white text-center text-slate-400 shadow-sm">
          <Users className="mb-3 h-10 w-10" />
          <p className="text-sm font-semibold">No teacher classes are available yet.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
            <StatCard title="Students" value={dashboard?.total_students ?? 0} subtitle="Enrolled in this class" icon={Users} tone="indigo" />
            <StatCard title="Active in 7 days" value={dashboard?.active_students_7d ?? 0} subtitle="Recent learning activity" icon={Flame} tone="amber" />
            <StatCard title="Average mastery" value={`${Math.round(Number(dashboard?.avg_mastery_score || 0) * 100)}%`} subtitle="Across mapped concepts" icon={BookOpenCheck} tone="emerald" />
            <StatCard title="Study time" value={formatStudyTime(dashboard?.avg_study_time_seconds_7d)} subtitle="Average in the last 7 days" icon={BarChart3} tone="slate" />
          </div>

          {graphSignal && (
            <section className="rounded-3xl border border-indigo-200 bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.18),_transparent_42%),linear-gradient(135deg,#ffffff,_#eef2ff)] p-6 shadow-sm">
              <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
                <div className="max-w-3xl">
                  <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-indigo-700">
                    <GitBranch className="h-3.5 w-3.5" />
                    Class graph signal
                  </div>
                  <h2 className="mt-3 text-2xl font-black tracking-tight text-slate-900">{graphSignal.headline}</h2>
                  <p className="mt-2 text-sm leading-7 text-slate-600">{graphSignal.supporting_reason}</p>
                  <div className="mt-4 flex flex-wrap gap-3">
                    {graphSignal.focus_concept_label && (
                      <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs shadow-sm">
                        <p className="font-black uppercase tracking-[0.18em] text-slate-400">Focus concept</p>
                        <p className="mt-1 text-sm font-semibold text-slate-800">{graphSignal.focus_concept_label}</p>
                      </div>
                    )}
                    {graphSignal.blocking_prerequisite_label && (
                      <div className="rounded-2xl border border-amber-200 bg-white px-4 py-3 text-xs shadow-sm">
                        <p className="font-black uppercase tracking-[0.18em] text-amber-500">Blocking prerequisite</p>
                        <p className="mt-1 text-sm font-semibold text-slate-800">{graphSignal.blocking_prerequisite_label}</p>
                      </div>
                    )}
                    <div className="rounded-2xl border border-emerald-200 bg-white px-4 py-3 text-xs shadow-sm">
                      <p className="font-black uppercase tracking-[0.18em] text-emerald-500">Teacher action</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">{graphSignal.recommended_action}</p>
                    </div>
                  </div>
                </div>

                {graphMetrics && (
                  <div className="grid min-w-[280px] grid-cols-2 gap-3">
                    <StatCard title="Mapped concepts" value={graphMetrics.mapped_concepts} subtitle="In this scope" icon={BrainCircuit} tone="slate" />
                    <StatCard title="Blocked" value={graphMetrics.blocked_concepts} subtitle="Prereq barriers" icon={Route} tone="amber" />
                    <StatCard title="Needs attention" value={graphMetrics.weak_concepts} subtitle="Below mastery" icon={ShieldAlert} tone="indigo" />
                    <StatCard title="Mastered" value={graphMetrics.mastered_concepts} subtitle="Ready to push" icon={BookOpenCheck} tone="emerald" />
                  </div>
                )}
              </div>
            </section>
          )}

          <div className="grid grid-cols-1 gap-8 xl:grid-cols-3">
            <section className="xl:col-span-2 space-y-8">
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="mb-6 flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-slate-800">Class Concept Graph</h2>
                    <p className="text-xs text-slate-500">Interactive prerequisite map showing where the class is blocked, weak, or ready to advance.</p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-slate-500">
                    {graphSummary?.nodes?.length || 0} nodes
                  </span>
                </div>

                <TeacherClassGraph graphSummary={graphSummary} />
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="mb-6 flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-slate-800">Graph Blockers</h2>
                    <p className="text-xs text-slate-500">The concept and prerequisite combinations currently slowing the class down.</p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-slate-500">
                    {graphBlockers.length} blockers
                  </span>
                </div>

                {graphBlockers.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm font-semibold text-slate-400">
                    No active graph blockers detected for this class.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {graphBlockers.map((node) => {
                      const score = Math.round(Number(node.avg_score || 0) * 100);
                      return (
                        <div key={node.concept_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                            <div>
                              <div className="inline-flex items-center gap-2 rounded-full bg-white px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-amber-700">
                                <Route className="h-3.5 w-3.5" />
                                {node.status.replace('_', ' ')}
                              </div>
                              <h3 className="mt-3 text-base font-bold text-slate-900">{node.concept_label}</h3>
                              <p className="mt-1 text-xs font-semibold text-slate-500">{node.topic_title || 'Mapped concept node'}</p>
                              {node.blocking_prerequisite_labels?.length > 0 && (
                                <p className="mt-2 text-xs leading-6 text-amber-700">
                                  Blocked by: {node.blocking_prerequisite_labels.join(', ')}
                                </p>
                              )}
                            </div>
                            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-right text-xs shadow-sm">
                              <p className="font-black uppercase tracking-[0.18em] text-slate-400">Class mastery</p>
                              <p className="mt-1 text-lg font-black text-slate-800">{score}%</p>
                              <p className="mt-1 text-[11px] font-medium text-slate-500">{node.student_count} student{node.student_count === 1 ? '' : 's'}</p>
                            </div>
                          </div>
                          <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
                            <div className="h-full rounded-full bg-amber-500" style={{ width: `${Math.max(score, 4)}%` }} />
                          </div>
                          <div className="mt-3 flex items-start gap-2 text-xs leading-6 text-slate-600">
                            <ArrowRight className="mt-0.5 h-3.5 w-3.5 text-indigo-500" />
                            <span>{node.recommended_action}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="mb-6 flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-slate-800">Weakest Concepts</h2>
                    <p className="text-xs text-slate-500">Real mastery averages from the graph-backed class heatmap.</p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-slate-500">
                    {weakestConcepts.length} concepts
                  </span>
                </div>

                {weakestConcepts.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm font-semibold text-slate-400">
                    No concept heatmap data is available for this class yet.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {weakestConcepts.map((point) => {
                      const score = Math.round(Number(point.avg_score || 0) * 100);
                      const tone = score < 40 ? 'bg-rose-500' : score < 70 ? 'bg-amber-500' : 'bg-emerald-500';
                      return (
                        <div key={point.concept_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                          <div className="flex items-center justify-between gap-4">
                            <div>
                              <h3 className="text-sm font-bold text-slate-900">{humanizeConceptId(point.concept_id)}</h3>
                              <p className="mt-1 text-xs text-slate-500">{point.student_count} student{point.student_count === 1 ? '' : 's'} contributing</p>
                            </div>
                            <span className="text-sm font-black text-slate-700">{score}%</span>
                          </div>
                          <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
                            <div className={`h-full rounded-full ${tone}`} style={{ width: `${Math.max(score, 4)}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </section>

            <section className="space-y-6">
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="flex items-center gap-2 text-lg font-bold text-slate-800">
                  <BookOpenCheck className="h-5 w-5 text-emerald-500" />
                  Ready To Push
                </h2>
                <p className="mt-1 text-xs text-slate-500">Concept clusters the class is strong enough to build on next.</p>
                <div className="mt-6 space-y-3">
                  {readyToPush.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm font-semibold text-slate-400">
                      No mastered concept cluster is strong enough yet to push forward confidently.
                    </div>
                  ) : (
                    readyToPush.map((node) => (
                      <div key={node.concept_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <div className="flex items-center justify-between gap-4">
                          <div>
                            <p className="text-sm font-bold text-slate-900">{node.concept_label}</p>
                            <p className="mt-1 text-xs text-slate-500">{node.topic_title || 'Mapped concept node'}</p>
                          </div>
                          <span className="text-sm font-black text-emerald-600">{Math.round(Number(node.avg_score || 0) * 100)}%</span>
                        </div>
                        <p className="mt-3 text-xs leading-6 text-slate-600">{node.recommended_action}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="flex items-center gap-2 text-lg font-bold text-slate-800">
                  <ShieldAlert className="h-5 w-5 text-rose-500" />
                  At-Risk Alerts
                </h2>
                <p className="mt-1 text-xs text-slate-500">Real inactivity, decline, and prerequisite alerts from backend analytics.</p>

                <div className="mt-6 space-y-3">
                  {alerts.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm font-semibold text-slate-400">
                      No alerts are active for this class.
                    </div>
                  ) : (
                    alerts.map((alert, index) => (
                      <div key={`${alert.student_id}-${alert.alert_type}-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <div className="flex items-center justify-between gap-3">
                          <span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${
                            alert.severity === 'high'
                              ? 'bg-rose-100 text-rose-700'
                              : alert.severity === 'medium'
                                ? 'bg-amber-100 text-amber-700'
                                : 'bg-slate-200 text-slate-700'
                          }`}>
                            {alert.alert_type.replace('_', ' ')}
                          </span>
                          <span className="text-[11px] font-semibold text-slate-400">Student {String(alert.student_id).slice(0, 8)}</span>
                        </div>
                        <p className="mt-3 text-sm leading-6 text-slate-700">{alert.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </section>
          </div>
        </>
      )}
    </main>
  );
};

export default ConceptAnalyticsPage;
