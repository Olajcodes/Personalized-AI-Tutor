import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, GitBranch } from 'lucide-react';

import HeroSection from '../components/HeroSection';
import AIRecommendation from '../components/AIRecommendation';
import DashboardStats from '../components/DashboardStats';
import InterventionTimeline from '../components/InterventionTimeline';
import LearningMap from '../components/LearningMap';
import LearningTasks from '../components/LearningTasks';
import Leaderboard from '../components/Leaderboard';
import Footer from '../components/Footer';
import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';
import {
    applyGraphInterventionOverlay,
    buildGraphInterventionScope,
    readLatestGraphIntervention,
    readGraphIntervention,
    subscribeGraphIntervention,
} from '../services/graphIntervention';

const prewarmTopics = async ({ apiUrl, token, studentId, subject, sssLevel, term, topicIds }) => {
    const normalizedIds = Array.from(new Set((topicIds || []).filter(Boolean)));
    if (!normalizedIds.length) return;
    try {
        await fetch(`${apiUrl}/learning/lesson/prewarm`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_id: studentId,
                subject,
                sss_level: sssLevel,
                term,
                topic_ids: normalizedIds,
            }),
        });
    } catch (error) {
        console.warn('Dashboard lesson prewarm skipped:', error);
    }
};

const normalizeCourseBootstrap = (data) => ({
    nodes: Array.isArray(data?.nodes) ? data.nodes : [],
    edges: Array.isArray(data?.edges) ? data.edges : [],
    next_step: data?.next_step || null,
    recent_evidence: data?.recent_evidence || null,
    intervention_timeline: Array.isArray(data?.intervention_timeline) ? data.intervention_timeline : [],
    recommendation_story: data?.recommendation_story || null,
});

const EMPTY_MAP_DATA = {
    nodes: [],
    edges: [],
    next_step: null,
    recent_evidence: null,
    intervention_timeline: [],
    recommendation_story: null,
};

export default function Dashboard() {
    const { token } = useAuth();
    const { userData, studentData } = useUser();
    const navigate = useNavigate();

    const activeId = studentData?.user_id || userData?.id;
    const currentLevel = studentData?.sss_level || 'SSS1';
    const currentTerm = studentData?.current_term || 1;
    const enrolledSubjects = studentData?.subjects || [];
    const latestIntervention = useMemo(
        () => readLatestGraphIntervention(activeId),
        [activeId],
    );

    const [activeSubject, setActiveSubject] = useState(() => localStorage.getItem('active_subject') || null);
    const [mapData, setMapData] = useState(EMPTY_MAP_DATA);
    const [isLoadingMap, setIsLoadingMap] = useState(false);
    const [mapError, setMapError] = useState('');
    const [graphIntervention, setGraphIntervention] = useState(null);

    const apiUrl = import.meta.env.VITE_API_URL;
    const interventionScope = useMemo(
        () => buildGraphInterventionScope({
            studentId: activeId,
            subject: activeSubject,
            sssLevel: currentLevel,
            term: currentTerm,
        }),
        [activeId, activeSubject, currentLevel, currentTerm],
    );
    const effectiveMapData = useMemo(
        () => applyGraphInterventionOverlay(mapData, graphIntervention),
        [graphIntervention, mapData],
    );
    const dashboardSignal = useMemo(() => {
        if (latestIntervention?.payload) {
            return latestIntervention;
        }
        if (!activeSubject) {
            return null;
        }
        if (!effectiveMapData?.next_step && !effectiveMapData?.recent_evidence && !effectiveMapData?.recommendation_story) {
            return null;
        }
        return {
            subject: activeSubject,
            sssLevel: currentLevel,
            term: currentTerm,
            payload: {
                next_step: effectiveMapData?.next_step || null,
                recent_evidence: effectiveMapData?.recent_evidence || null,
                recommendation_story: effectiveMapData?.recommendation_story || null,
                intervention_timeline: Array.isArray(effectiveMapData?.intervention_timeline) ? effectiveMapData.intervention_timeline : [],
            },
        };
    }, [activeSubject, currentLevel, currentTerm, effectiveMapData, latestIntervention]);

    useEffect(() => {
        if (studentData && (!studentData.subjects || studentData.subjects.length === 0)) {
            navigate('/class-selection');
        }
    }, [studentData, navigate]);

    useEffect(() => {
        if (!activeSubject && latestIntervention?.subject) {
            setActiveSubject(latestIntervention.subject);
        }
    }, [activeSubject, latestIntervention]);

    useEffect(() => {
        if (activeSubject) {
            localStorage.setItem('active_subject', activeSubject);
        }
    }, [activeSubject]);

    useEffect(() => {
        if (!interventionScope) {
            setGraphIntervention(null);
            return () => {};
        }
        setGraphIntervention(readGraphIntervention(interventionScope));
        return subscribeGraphIntervention(interventionScope, setGraphIntervention);
    }, [interventionScope]);

    useEffect(() => {
        if (!activeId || !token) {
            return;
        }

        const fetchDashboardBootstrap = async () => {
            setIsLoadingMap(true);
            setMapError('');

            try {
                const queryParams = new URLSearchParams({ student_id: activeId });
                if (activeSubject) {
                    queryParams.set('subject', activeSubject);
                }

                const response = await fetch(`${apiUrl}/learning/dashboard/bootstrap?${queryParams.toString()}`, {
                    method: 'GET',
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    throw new Error('Failed to fetch learning map');
                }

                const data = await response.json();
                if (data?.active_subject && data.active_subject !== activeSubject) {
                    setActiveSubject(data.active_subject);
                }
                setMapData(normalizeCourseBootstrap(data?.course_bootstrap || {}));
                setMapError(data?.course_bootstrap?.map_error || '');
            } catch (err) {
                console.error('Map fetch error:', err);
                setMapData(EMPTY_MAP_DATA);
                setMapError(err.message || 'Learning map unavailable.');
            } finally {
                setIsLoadingMap(false);
            }
        };

        fetchDashboardBootstrap();
    }, [activeId, activeSubject, token, apiUrl]);

    const openTopicFromGraph = useCallback(async (topicId) => {
        if (!topicId) return;
        await prewarmTopics({
            apiUrl,
            token,
            studentId: activeId,
            subject: activeSubject,
            sssLevel: currentLevel,
            term: currentTerm,
            topicIds: [topicId],
        });
        navigate(`/lesson/${topicId}`);
    }, [activeId, activeSubject, apiUrl, currentLevel, currentTerm, navigate, token]);

    const resumeLatestIntervention = useCallback(async () => {
        const topicId = dashboardSignal?.payload?.next_step?.recommended_topic_id;
        if (!topicId) return;
        await prewarmTopics({
            apiUrl,
            token,
            studentId: activeId,
            subject: dashboardSignal?.subject || activeSubject,
            sssLevel: dashboardSignal?.sssLevel || currentLevel,
            term: Number(dashboardSignal?.term || currentTerm),
            topicIds: [topicId],
        });
        navigate(`/lesson/${topicId}`);
    }, [activeId, activeSubject, apiUrl, currentLevel, currentTerm, dashboardSignal, navigate, token]);

    const dashboardTasks = useMemo(() => {
        const tasks = [];
        const nextStep = dashboardSignal?.payload?.next_step || effectiveMapData?.next_step || null;
        const recommendationStory = dashboardSignal?.payload?.recommendation_story || effectiveMapData?.recommendation_story || null;
        const timeline = Array.isArray(dashboardSignal?.payload?.intervention_timeline)
            ? dashboardSignal.payload.intervention_timeline
            : Array.isArray(effectiveMapData?.intervention_timeline)
                ? effectiveMapData.intervention_timeline
                : [];

        if (nextStep?.recommended_topic_id) {
            tasks.push({
                id: 'recommended-lesson',
                badge: recommendationStory?.status === 'bridge_prerequisite' ? 'Repair gap' : 'Next lesson',
                title: nextStep.recommended_topic_title || nextStep.recommended_concept_label || 'Continue your graph path',
                subtext: recommendationStory?.supporting_reason || nextStep.reason || 'Open the lesson the graph recommends next.',
                actionLabel: recommendationStory?.action_label || 'Open lesson',
                onClick: resumeLatestIntervention,
                tone: recommendationStory?.status === 'bridge_prerequisite' ? 'amber' : 'indigo',
            });
        }

        if (timeline.length > 0) {
            tasks.push({
                id: 'latest-evidence',
                badge: timeline[0].source_label || 'Latest evidence',
                title: timeline[0].focus_concept_label || 'Review your latest intervention',
                subtext: timeline[0].summary,
                actionLabel: 'Resume',
                onClick: resumeLatestIntervention,
                tone: 'slate',
            });
        }

        const alternateNode = Array.isArray(effectiveMapData?.nodes)
            ? effectiveMapData.nodes.find(
                (node) =>
                    node?.topic_id &&
                    node.status === 'ready' &&
                    node.topic_id !== nextStep?.recommended_topic_id,
            )
            : null;
        if (alternateNode?.topic_id) {
            tasks.push({
                id: 'alternate-ready-node',
                badge: 'Ready concept',
                title: alternateNode.concept_label || alternateNode.topic_title || 'Explore a ready concept',
                subtext: alternateNode.details || 'Open another graph-ready lesson in this scope.',
                actionLabel: 'Open node',
                onClick: () => openTopicFromGraph(alternateNode.topic_id),
                tone: 'indigo',
            });
        }

        return tasks.slice(0, 3);
    }, [dashboardSignal, effectiveMapData, openTopicFromGraph, resumeLatestIntervention]);

    return (
        <div className="min-h-screen bg-[#F8FAFC] font-sans">
            <main className="max-w-9xl mx-auto px-6 py-8">
                <div className="mb-8 flex flex-col gap-6 lg:flex-row">
                    <HeroSection
                        enrolledSubjects={enrolledSubjects}
                        activeSubject={activeSubject}
                        onSelectSubject={setActiveSubject}
                        hasStartedLearning={false}
                        graphSignal={dashboardSignal}
                        signalSubject={dashboardSignal?.subject || activeSubject}
                        onResumeSignal={dashboardSignal?.payload?.next_step?.recommended_topic_id ? resumeLatestIntervention : null}
                    />
                    <AIRecommendation
                        activeSubject={activeSubject}
                        recommendation={activeSubject ? effectiveMapData?.next_step : null}
                        recentEvidence={activeSubject ? effectiveMapData?.recent_evidence : null}
                        recommendationStory={activeSubject ? effectiveMapData?.recommendation_story : null}
                    />
                </div>

                {dashboardSignal?.payload && (
                    <div className="mb-8 rounded-3xl border border-indigo-200 bg-gradient-to-r from-indigo-50 via-white to-sky-50 p-6 shadow-sm">
                        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                            <div className="max-w-3xl">
                                <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-indigo-700">
                                    <GitBranch className="h-3.5 w-3.5" />
                                    Resume last intervention
                                </div>
                                <h2 className="mt-3 text-2xl font-black text-slate-900">
                                    {dashboardSignal.payload.recommendation_story?.headline
                                        || dashboardSignal.payload.next_step?.recommended_topic_title
                                        || dashboardSignal.payload.next_step?.recommended_concept_label
                                        || `Continue ${dashboardSignal.subject}`}
                                </h2>
                                <p className="mt-2 text-sm leading-7 text-slate-600">
                                    {dashboardSignal.payload.recommendation_story?.supporting_reason
                                        || dashboardSignal.payload.next_step?.reason
                                        || dashboardSignal.payload.recent_evidence?.summary
                                        || 'Resume the last graph-backed recommendation from your latest evidence.'}
                                </p>
                                {dashboardSignal.payload.recent_evidence?.summary && (
                                    <p className="mt-3 text-xs font-semibold text-slate-500">
                                        Latest evidence: {dashboardSignal.payload.recent_evidence.summary}
                                    </p>
                                )}
                            </div>
                            <div className="flex flex-wrap gap-3">
                                {dashboardSignal.subject && dashboardSignal.subject !== activeSubject && (
                                    <button
                                        type="button"
                                        onClick={() => setActiveSubject(dashboardSignal.subject)}
                                        className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 hover:bg-slate-50"
                                    >
                                        Open {dashboardSignal.subject}
                                    </button>
                                )}
                                {dashboardSignal.payload.next_step?.recommended_topic_id && (
                                    <button
                                        type="button"
                                        onClick={async () => {
                                            await prewarmTopics({
                                                apiUrl,
                                                token,
                                                studentId: activeId,
                                                subject: dashboardSignal.subject,
                                                sssLevel: dashboardSignal.sssLevel || currentLevel,
                                                term: Number(dashboardSignal.term || currentTerm),
                                                topicIds: [dashboardSignal.payload.next_step.recommended_topic_id],
                                            });
                                            navigate(`/lesson/${dashboardSignal.payload.next_step.recommended_topic_id}`);
                                        }}
                                        className="inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white hover:bg-indigo-700"
                                    >
                                        Resume now
                                        <ArrowRight className="h-4 w-4" />
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {activeSubject && Array.isArray(effectiveMapData?.intervention_timeline) && effectiveMapData.intervention_timeline.length > 0 && (
                    <div className="mb-8">
                        <InterventionTimeline
                            title={`${activeSubject} Evidence Timeline`}
                            subtitle="Recent quiz and checkpoint evidence from the backend graph state."
                            timeline={effectiveMapData.intervention_timeline}
                        />
                    </div>
                )}

                <DashboardStats />

                {!activeSubject ? (
                    <div className="mb-8 flex w-full flex-col items-center justify-center rounded-3xl border border-slate-200 bg-white p-16 text-center shadow-sm">
                        <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-indigo-50 text-indigo-400 shadow-inner">
                            <svg className="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"></path></svg>
                        </div>
                        <h3 className="mb-3 text-2xl font-bold text-slate-800">Your Learning Map is Waiting</h3>
                        <p className="mx-auto max-w-md text-lg text-slate-500">Select a subject from the top section to generate your personalized AI curriculum map.</p>
                    </div>
                ) : isLoadingMap ? (
                    <div className="mb-8 flex w-full flex-col items-center rounded-3xl border border-slate-200 bg-white p-16 text-center font-medium text-indigo-500 shadow-sm animate-pulse">
                        <div className="mb-4 h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
                        Generating your personalized {activeSubject} path...
                    </div>
                ) : mapError ? (
                    <div className="mb-8 flex w-full flex-col items-center justify-center rounded-3xl border border-rose-200 bg-white p-16 text-center shadow-sm">
                        <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-rose-50 text-rose-400 shadow-inner">
                            <svg className="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v4m0 4h.01M5.07 19h13.86c1.54 0 2.5-1.67 1.73-3L13.73 4c-.77-1.33-2.69-1.33-3.46 0L3.34 16c-.77 1.33.19 3 1.73 3z"></path></svg>
                        </div>
                        <h3 className="mb-3 text-2xl font-bold text-slate-800">Learning Map Unavailable</h3>
                        <p className="mx-auto max-w-md text-lg text-slate-500">{mapError}</p>
                    </div>
                ) : (
                    <LearningMap
                        classLevel={currentLevel}
                        subject={activeSubject}
                        mapData={effectiveMapData}
                        onSelectTopic={openTopicFromGraph}
                    />
                )}

                <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
                    <LearningTasks tasks={dashboardTasks} />
                    <Leaderboard leagueName="Gold League" />
                </div>

                <Footer />
            </main>
        </div>
    );
}
