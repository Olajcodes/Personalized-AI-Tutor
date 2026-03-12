import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Bot,
  BrainCircuit,
  CheckCircle2,
  GitBranch,
  LoaderCircle,
  Menu,
  MessageSquare,
  NotebookPen,
  Route,
  Send,
  ShieldAlert,
  Sparkles,
  Target,
  Zap,
} from 'lucide-react';

import CourseSidebar from '../components/CourseSidebar';
import InterventionTimeline from '../components/InterventionTimeline';
import LessonKnowledgeGraph from '../components/lesson/LessonKnowledgeGraph';
import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';
import { saveGraphIntervention } from '../services/graphIntervention';

const API_URL = import.meta.env.VITE_API_URL || 'https://mastery-backend-7xe8.onrender.com/api/v1';
const safeArray = (value) => (Array.isArray(value) ? value : []);
const BOOTSTRAP_CACHE_TTL_MS = 45_000;
const lessonBootstrapCache = new Map();

const iconByIntent = {
  teach: Sparkles,
  socratic: Route,
  diagnose: ShieldAlert,
  drill: Zap,
  recap: NotebookPen,
  assessment_start: Target,
  sparkles: Sparkles,
  lightbulb: Sparkles,
  'git-branch': GitBranch,
  route: Route,
  'shield-alert': ShieldAlert,
  target: Target,
  'graduation-cap': BrainCircuit,
  'notebook-pen': NotebookPen,
};

const bootstrapCacheKey = ({ studentId, subject, level, term, topicId }) => [studentId, subject, level, term, topicId].join(':');

const readBootstrapCache = (key) => {
  const entry = lessonBootstrapCache.get(key);
  if (!entry) return null;
  if ((Date.now() - entry.timestamp) > BOOTSTRAP_CACHE_TTL_MS) {
    lessonBootstrapCache.delete(key);
    return null;
  }
  return entry.payload;
};

const writeBootstrapCache = (key, payload) => {
  lessonBootstrapCache.set(key, { payload, timestamp: Date.now() });
};

const prewarmTopics = async ({ token, studentId, subject, sssLevel, term, topicIds }) => {
  const normalizedIds = Array.from(new Set((topicIds || []).filter(Boolean)));
  if (!normalizedIds.length) return;
  try {
    await fetch(`${API_URL}/learning/lesson/prewarm`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: studentId,
        subject,
        sss_level: sssLevel,
        term,
        topic_ids: normalizedIds,
      }),
    });
  } catch (error) {
    console.warn('Lesson remediation prewarm skipped:', error);
  }
};

function MessageCard({
  item,
  onOpenRecommendation,
  onStartCheckpoint,
  onOpenPrereqBridge,
  onStartDrill,
}) {
  const isStudent = item.role === 'student';
  const showCheckpointAction = !isStudent && Boolean(item.recommended_assessment);
  const showPrereqAction = !isStudent && Boolean(item.prerequisite_warning);
  const showDrillAction = !isStudent && safeArray(item.concept_focus).length > 0;
  return (
    <div className={`flex ${isStudent ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[92%] rounded-3xl p-4 text-sm ${isStudent ? 'bg-indigo-600 text-white' : 'border border-slate-200 bg-white text-slate-700'}`}>
        {isStudent ? (
          <p className="whitespace-pre-wrap">{item.content}</p>
        ) : (
          <div className="space-y-3">
            <div className="whitespace-pre-wrap text-sm leading-7">{item.content || ''}</div>
            {safeArray(item.key_points).length > 0 && (
              <div className="rounded-2xl bg-slate-50 p-3">
                <p className="mb-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Key Points</p>
                <ul className="space-y-1 text-xs text-slate-600">
                  {item.key_points.map((point, index) => (
                    <li key={`${point}-${index}`}>- {point}</li>
                  ))}
                </ul>
              </div>
            )}
            {(item.prerequisite_warning || item.next_action || item.recommended_assessment) && (
              <div className="grid gap-2">
                {item.prerequisite_warning && <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">{item.prerequisite_warning}</div>}
                {item.next_action && <div className="rounded-2xl border border-indigo-200 bg-indigo-50 p-3 text-xs text-indigo-800">{item.next_action}</div>}
                {item.recommended_assessment && <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800">{item.recommended_assessment}</div>}
              </div>
            )}
            {safeArray(item.concept_focus).length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                <p className="mb-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Concept Focus</p>
                <div className="flex flex-wrap gap-2">
                  {item.concept_focus.map((label, index) => (
                    <span key={`${label}-${index}`} className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-bold text-slate-600">
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {safeArray(item.citations).length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                <p className="mb-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Evidence</p>
                <div className="grid gap-2">
                  {item.citations.map((citation, index) => (
                    <div key={`${citation.chunk_id || citation.source_id}-${index}`} className="rounded-2xl border border-slate-200 bg-white p-3 text-xs leading-6 text-slate-600">
                      <p className="font-black uppercase tracking-[0.16em] text-slate-400">{citation.source_id || 'Curriculum source'}</p>
                      <p className="mt-1">{citation.snippet}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {safeArray(item.recommendations).length > 0 && (
              <div className="rounded-2xl border border-indigo-200 bg-indigo-50 p-3">
                <p className="mb-2 text-[10px] font-black uppercase tracking-[0.2em] text-indigo-500">Graph Recommendation</p>
                <div className="grid gap-2">
                  {item.recommendations.map((recommendation, index) => (
                    <div key={`${recommendation.topic_id || recommendation.type}-${index}`} className="rounded-2xl bg-white p-3">
                      <p className="text-xs font-bold text-slate-800">{recommendation.topic_title || recommendation.type}</p>
                      <p className="mt-1 text-xs leading-6 text-slate-600">{recommendation.reason}</p>
                      {recommendation.topic_id && (
                        <button
                          type="button"
                          onClick={() => onOpenRecommendation?.(recommendation.topic_id)}
                          className="mt-3 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-3 py-2 text-[11px] font-black uppercase tracking-[0.16em] text-white hover:bg-indigo-700"
                        >
                          Open lesson
                          <ArrowRight size={14} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {(showCheckpointAction || showPrereqAction || showDrillAction) && (
              <div className="flex flex-wrap gap-2">
                {showCheckpointAction && (
                  <button
                    type="button"
                    onClick={onStartCheckpoint}
                    className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-3 py-2 text-[11px] font-black uppercase tracking-[0.16em] text-white hover:bg-emerald-700"
                  >
                    <Target size={14} />
                    Check understanding
                  </button>
                )}
                {showPrereqAction && (
                  <button
                    type="button"
                    onClick={onOpenPrereqBridge}
                    className="inline-flex items-center gap-2 rounded-xl border border-amber-200 bg-white px-3 py-2 text-[11px] font-black uppercase tracking-[0.16em] text-amber-700 hover:bg-amber-50"
                  >
                    <Route size={14} />
                    Bridge prerequisite
                  </button>
                )}
                {showDrillAction && (
                  <button
                    type="button"
                    onClick={onStartDrill}
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-[11px] font-black uppercase tracking-[0.16em] text-slate-700 hover:bg-slate-50"
                  >
                    <Zap size={14} />
                    1-minute drill
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ConceptChip({ concept }) {
  const tone = concept.mastery_state === 'demonstrated'
    ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
    : concept.mastery_state === 'needs_review'
      ? 'border-amber-200 bg-amber-50 text-amber-700'
      : 'border-slate-200 bg-slate-100 text-slate-600';
  return (
    <div className={`rounded-2xl border px-3 py-2 text-xs ${tone}`}>
      <p className="font-bold">{concept.label}</p>
      <p className="mt-1 opacity-80">{typeof concept.mastery_score === 'number' ? `${Math.round(concept.mastery_score * 100)}% mastery` : 'Unassessed'}</p>
    </div>
  );
}

export default function LessonPage() {
  const navigate = useNavigate();
  const { topicId } = useParams();
  const { token } = useAuth();
  const { studentData, userData } = useUser();

  const activeId = studentData?.user_id || userData?.id;
  const currentSubject = localStorage.getItem('active_subject') || studentData?.subjects?.[0] || 'math';
  const currentLevel = studentData?.sss_level || 'SSS1';
  const currentTerm = studentData?.current_term || 1;

  const [isSidebarOpen, setIsSidebarOpen] = useState(typeof window !== 'undefined' ? window.innerWidth > 1180 : true);
  const [bootstrap, setBootstrap] = useState(null);
  const [sidebarTopics, setSidebarTopics] = useState([]);
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [assessmentAnswer, setAssessmentAnswer] = useState('');
  const [pendingAssessment, setPendingAssessment] = useState(null);
  const [lastAssessmentReview, setLastAssessmentReview] = useState(null);
  const [isBusy, setIsBusy] = useState(false);
  const [streamPhase, setStreamPhase] = useState('');
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');
  const scrollRef = useRef(null);
  const activeCacheKey = useMemo(
    () => bootstrapCacheKey({ studentId: activeId, subject: currentSubject, level: currentLevel, term: currentTerm, topicId }),
    [activeId, currentLevel, currentSubject, currentTerm, topicId],
  );

  const lesson = bootstrap?.lesson || null;
  const graphContext = bootstrap?.graph_context || null;
  const whyTopicDetail = bootstrap?.why_topic_detail || null;
  const sessionId = bootstrap?.session_id || null;
  const quickActions = safeArray(bootstrap?.suggested_actions);
  const recentEvidence = bootstrap?.recent_evidence || null;
  const interventionTimeline = safeArray(bootstrap?.intervention_timeline);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isBusy, pendingAssessment]);

  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth < 1180) setIsSidebarOpen(false);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    if (!activeId || !token || !topicId) return undefined;
    let cancelled = false;

    const init = async () => {
      setStatus('loading');
      setError('');
      const cachedBootstrap = readBootstrapCache(activeCacheKey);
      if (cachedBootstrap) {
        setBootstrap(cachedBootstrap);
        setPendingAssessment(cachedBootstrap.pending_assessment || null);
        setMessages([
          {
            role: 'assistant',
            content: cachedBootstrap.greeting || 'Your lesson cockpit is ready.',
            key_points: [
              cachedBootstrap.why_this_topic || 'Use the graph rail to see why this lesson matters.',
              cachedBootstrap.recent_evidence?.summary || null,
            ].filter(Boolean),
          },
        ]);
        setStatus('ready');
      }
      try {
        const response = await fetch(`${API_URL}/learning/lesson/cockpit`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: activeId,
            subject: currentSubject,
            sss_level: currentLevel,
            term: currentTerm,
            topic_id: topicId,
          }),
        });
        if (!response.ok) {
          const err = await response.json().catch(() => null);
          throw new Error(err?.detail || 'Failed to load lesson cockpit.');
        }
        const cockpitJson = await response.json();
        if (cancelled) return;
        const bootstrapJson = {
          ...cockpitJson.tutor_bootstrap,
          recent_evidence: cockpitJson.recent_evidence || null,
          intervention_timeline: safeArray(cockpitJson.intervention_timeline),
          why_topic_detail: cockpitJson.why_topic_detail || null,
        };
        setSidebarTopics(safeArray(cockpitJson.topics));
        setBootstrap(bootstrapJson);
        writeBootstrapCache(activeCacheKey, bootstrapJson);
        setPendingAssessment(bootstrapJson.pending_assessment || null);
        setMessages([
          {
            role: 'assistant',
            content: bootstrapJson.greeting || 'Your lesson cockpit is ready.',
            key_points: [
              bootstrapJson.why_this_topic || 'Use the graph rail to see why this lesson matters.',
              cockpitJson.recent_evidence?.summary || null,
            ].filter(Boolean),
          },
        ]);
        setStatus('ready');
      } catch (err) {
        if (cancelled) return;
        setError(err.message || 'Failed to load lesson cockpit.');
        setStatus('error');
      }
    };

    init();
    return () => { cancelled = true; };
  }, [activeCacheKey, activeId, currentLevel, currentSubject, currentTerm, token, topicId]);

  useEffect(() => {
    if (!bootstrap || !activeCacheKey) return;
    writeBootstrapCache(activeCacheKey, bootstrap);
  }, [activeCacheKey, bootstrap]);

  const masteryPulse = useMemo(() => {
    const currentConcepts = safeArray(graphContext?.current_concepts);
    if (!currentConcepts.length) return null;
    const average = currentConcepts.reduce((sum, item) => sum + (item.mastery_score || 0), 0) / currentConcepts.length;
    return Math.round(average * 100);
  }, [graphContext]);

  const appendAssistant = (payload) => {
    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: payload.assistant_message || payload.message || 'Tutor response unavailable.',
        key_points: payload.key_points || [],
        concept_focus: payload.concept_focus || [],
        citations: payload.citations || [],
        recommendations: payload.recommendations || [],
        actions: payload.actions || [],
        next_action: payload.next_action || null,
        prerequisite_warning: payload.prerequisite_warning || null,
        recommended_assessment: payload.recommended_assessment || null,
      },
    ]);
  };

  const openRecommendedLesson = async (recommendedTopicId) => {
    if (!recommendedTopicId || !activeId || !token) return;
    await prewarmTopics({
      token,
      studentId: activeId,
      subject: currentSubject,
      sssLevel: currentLevel,
      term: currentTerm,
      topicIds: [recommendedTopicId],
    });
    navigate(`/lesson/${recommendedTopicId}`);
  };

  const topicWarmSummary = useMemo(() => {
    const currentCount = safeArray(graphContext?.current_concepts).length;
    const prereqCount = safeArray(graphContext?.prerequisite_concepts).length;
    const downstreamCount = safeArray(graphContext?.downstream_concepts).length;
    return { currentCount, prereqCount, downstreamCount };
  }, [graphContext]);

  const postJson = async (path, body) => {
    const response = await fetch(`${API_URL}${path}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => null);
      throw new Error(err?.detail || 'Request failed.');
    }
    return response.json();
  };

  const consumeStream = async (payload) => {
    const response = await fetch(`${API_URL}/tutor/chat/stream`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok || !response.body) {
      const err = await response.json().catch(() => null);
      throw new Error(err?.detail || 'Tutor stream failed.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() || '';
      for (const block of events) {
        const lines = block.split('\n');
        const event = lines.find((line) => line.startsWith('event:'))?.replace('event:', '').trim();
        const dataLine = lines.find((line) => line.startsWith('data:'))?.replace('data:', '').trim() || '{}';
        const data = JSON.parse(dataLine);
        if (event === 'status') setStreamPhase(data.phase || '');
        if (event === 'message') appendAssistant(data);
        if (event === 'error') throw new Error(data.detail || 'Tutor stream failed.');
      }
    }
  };

  const sendChat = async (message) => {
    const trimmed = (message ?? chatInput).trim();
    if (!trimmed || !sessionId || isBusy) return;
    setMessages((prev) => [...prev, { role: 'student', content: trimmed }]);
    setChatInput('');
    setIsBusy(true);
    try {
      await consumeStream({
        student_id: activeId,
        session_id: sessionId,
        subject: currentSubject,
        sss_level: currentLevel,
        term: currentTerm,
        topic_id: topicId,
        message: trimmed,
      });
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: err.message || 'Tutor request failed.' }]);
    } finally {
      setIsBusy(false);
      setStreamPhase('');
    }
  };

  const startAssessment = async (difficulty = 'medium') => {
    if (!sessionId || isBusy) return;
    setIsBusy(true);
    try {
      const out = await postJson('/tutor/assessment/start', {
        student_id: activeId,
        session_id: sessionId,
        subject: currentSubject,
        sss_level: currentLevel,
        term: currentTerm,
        topic_id: topicId,
        difficulty,
      });
      setPendingAssessment(out);
      setAssessmentAnswer('');
      setLastAssessmentReview(null);
      saveGraphIntervention({
        studentId: activeId,
        subject: currentSubject,
        sssLevel: currentLevel,
        term: currentTerm,
        payload: {
          source: 'pending_assessment',
          analytics: {
            source_label: 'Tutor checkpoint',
            outcome: 'Resume checkpoint',
            focus_concept: out.concept_label || null,
            blocking_prerequisite: null,
          },
          next_step: {
            recommended_topic_id: topicId,
            recommended_topic_title: lesson?.title || bootstrap?.lesson?.title || 'Current lesson',
            recommended_concept_label: out.concept_label || null,
            prereq_gaps: [],
            prereq_gap_labels: [],
            reason: `Resume the live checkpoint on ${out.concept_label || 'this lesson'} before moving on.`,
          },
          recent_evidence: out.hint
            ? {
                summary: `Checkpoint ready: ${out.hint}`,
                strongest_gain_concept_label: null,
                strongest_drop_concept_label: out.concept_label || null,
              }
            : null,
          recommendation_story: {
            status: 'resume_checkpoint',
            headline: `Resume your checkpoint on ${out.concept_label || lesson?.title || 'this lesson'}`,
            supporting_reason: 'A live tutor checkpoint is waiting in your current lesson.',
            evidence_summary: out.hint ? `Hint ready: ${out.hint}` : 'Your next mastery checkpoint is already prepared.',
            next_concept_label: out.concept_label || null,
            action_label: 'Resume checkpoint',
          },
        },
      });
      appendAssistant({
        assistant_message: `Checkpoint: ${out.question}`,
        key_points: [
          `Focus concept: ${out.concept_label}`,
          `Difficulty: ${difficulty}`,
        ],
        next_action: difficulty === 'hard'
          ? 'Push for a sharper answer and justify it clearly.'
          : 'Answer the checkpoint below to update your mastery.',
      });
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: err.message || 'Checkpoint unavailable.' }]);
    } finally {
      setIsBusy(false);
    }
  };

  const handleRecap = async () => {
    setIsBusy(true);
    try {
      appendAssistant(await postJson('/tutor/recap', {
        student_id: activeId,
        session_id: sessionId,
        subject: currentSubject,
        sss_level: currentLevel,
        term: currentTerm,
        topic_id: topicId,
      }));
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: err.message || 'Recap unavailable.' }]);
    } finally {
      setIsBusy(false);
    }
  };

  const handlePrereqBridge = async () => {
    setIsBusy(true);
    try {
      appendAssistant(await postJson('/tutor/prereq-bridge', {
        student_id: activeId,
        session_id: sessionId,
        subject: currentSubject,
        sss_level: currentLevel,
        term: currentTerm,
        topic_id: topicId,
      }));
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: err.message || 'Prerequisite bridge unavailable.' }]);
    } finally {
      setIsBusy(false);
    }
  };

  const handleQuickAction = async (action) => {
    if (action.intent === 'assessment_start') {
      await startAssessment();
      return;
    }
    if (action.id === 'recap') {
      await handleRecap();
      return;
    }
    if (action.id === 'prereq-bridge') {
      await handlePrereqBridge();
      return;
    }
    sendChat(action.prompt);
  };

  const explainLastMistake = async () => {
    if (!lastAssessmentReview || lastAssessmentReview.is_correct || isBusy) return;
    setIsBusy(true);
    try {
      const out = await postJson('/tutor/explain-mistake', {
        student_id: activeId,
        session_id: sessionId,
        subject: currentSubject,
        sss_level: currentLevel,
        term: currentTerm,
        topic_id: topicId,
        question: lastAssessmentReview.question,
        student_answer: lastAssessmentReview.studentAnswer,
        correct_answer: lastAssessmentReview.idealAnswer,
      });
      appendAssistant({
        assistant_message: out.explanation,
        key_points: [
          `Focus concept: ${lastAssessmentReview.conceptLabel}`,
          out.improvement_tip,
        ].filter(Boolean),
        prerequisite_warning: lastAssessmentReview.graphRemediation?.blocking_prerequisite_label
          ? `Fix ${lastAssessmentReview.graphRemediation.blocking_prerequisite_label} before retrying this concept.`
          : null,
        next_action: lastAssessmentReview.recommendedTopicTitle
          ? `Revise ${lastAssessmentReview.recommendedTopicTitle}, then retry this checkpoint.`
          : 'Retry the checkpoint after revising the core rule and one worked example.',
      });
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: err.message || 'Mistake explanation unavailable.' }]);
    } finally {
      setIsBusy(false);
    }
  };

  const handleDrill = async () => {
    if (!sessionId || isBusy) return;
    setIsBusy(true);
    try {
      appendAssistant(await postJson('/tutor/drill', {
        student_id: activeId,
        session_id: sessionId,
        subject: currentSubject,
        sss_level: currentLevel,
        term: currentTerm,
        topic_id: topicId,
        difficulty: 'medium',
      }));
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: err.message || 'Drill unavailable.' }]);
    } finally {
      setIsBusy(false);
    }
  };

  const handleStudyPlan = async () => {
    if (!sessionId || isBusy) return;
    setIsBusy(true);
    try {
      appendAssistant(await postJson('/tutor/study-plan', {
        student_id: activeId,
        session_id: sessionId,
        subject: currentSubject,
        sss_level: currentLevel,
        term: currentTerm,
        topic_id: topicId,
        horizon_days: 7,
      }));
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: err.message || 'Study plan unavailable.' }]);
    } finally {
      setIsBusy(false);
    }
  };

  const submitAssessment = async () => {
    if (!pendingAssessment || !assessmentAnswer.trim() || isBusy) return;
    setIsBusy(true);
    try {
      const submittedAnswer = assessmentAnswer.trim();
      const submittedQuestion = pendingAssessment.question;
      const out = await postJson('/tutor/assessment/submit', {
        student_id: activeId,
        session_id: sessionId,
        assessment_id: pendingAssessment.assessment_id,
        subject: currentSubject,
        sss_level: currentLevel,
        term: currentTerm,
        topic_id: topicId,
        answer: submittedAnswer,
      });
      const recommendedTopicId = out.graph_remediation?.recommended_next_topic_id || out.recommended_topic_id || null;
      const recommendedTopicTitle = out.graph_remediation?.recommended_next_topic_title || out.recommended_topic_title || null;
      const assessmentSummary = out.is_correct
        ? `${out.concept_label} checkpoint cleared at ${Math.round((out.score || 0) * 100)}%.`
        : `${out.concept_label} checkpoint exposed a gap at ${Math.round((out.score || 0) * 100)}%.`;
      const nextStep = (recommendedTopicId || recommendedTopicTitle || out.graph_remediation?.recommended_next_concept_label || out.graph_remediation?.blocking_prerequisite_label || out.graph_remediation?.recommendation_reason)
        ? {
            recommended_topic_id: recommendedTopicId,
            recommended_topic_title: recommendedTopicTitle,
            recommended_concept_label: out.graph_remediation?.recommended_next_concept_label || null,
            prereq_gaps: out.graph_remediation?.blocking_prerequisite_label
              ? [{ label: out.graph_remediation.blocking_prerequisite_label }]
              : [],
            prereq_gap_labels: out.graph_remediation?.blocking_prerequisite_label
              ? [out.graph_remediation.blocking_prerequisite_label]
              : [],
            reason: out.graph_remediation?.recommendation_reason
              || (out.is_correct ? `Build on ${out.concept_label} while it is fresh.` : `Repair the blocking concept before retrying ${out.concept_label}.`),
          }
        : null;
      const recentEvidence = {
        summary: assessmentSummary,
        strongest_gain_concept_label: out.is_correct ? out.concept_label : null,
        strongest_drop_concept_label: out.is_correct ? null : out.concept_label,
      };
      const recommendationStory = {
        status: out.is_correct ? 'advance' : 'hold_current',
        headline: out.is_correct
          ? (recommendedTopicTitle ? `Push into ${recommendedTopicTitle}` : `Advance beyond ${out.concept_label}`)
          : (out.graph_remediation?.blocking_prerequisite_label
              ? `Rebuild ${out.graph_remediation.blocking_prerequisite_label}`
              : `Revisit ${out.concept_label}`),
        supporting_reason: out.graph_remediation?.recommendation_reason
          || (out.is_correct
            ? `Your latest checkpoint shows ${out.concept_label} is warming up.`
            : `Your latest checkpoint shows ${out.concept_label} still needs repair.`),
        evidence_summary: assessmentSummary,
        next_concept_label: out.graph_remediation?.recommended_next_concept_label || null,
        action_label: recommendedTopicId ? 'Open Recommended Lesson' : (out.is_correct ? 'Continue current focus' : 'Repair prerequisite'),
      };

      saveGraphIntervention({
        studentId: activeId,
        subject: currentSubject,
        sssLevel: currentLevel,
        term: currentTerm,
        payload: {
          source: 'tutor_assessment',
          analytics: {
            source_label: 'Tutor assessment',
            outcome: out.is_correct ? 'Advance from checkpoint' : 'Repair prerequisite',
            focus_concept: out.concept_label || out.graph_remediation?.recommended_next_concept_label || null,
            blocking_prerequisite: out.graph_remediation?.blocking_prerequisite_label || null,
          },
          next_step: nextStep,
          recent_evidence: recentEvidence,
          recommendation_story: recommendationStory,
        },
      });
      await prewarmTopics({
        token,
        studentId: activeId,
        subject: currentSubject,
        sssLevel: currentLevel,
        term: currentTerm,
        topicIds: recommendedTopicId ? [recommendedTopicId] : [],
      });
      setLastAssessmentReview({
        assessmentId: pendingAssessment.assessment_id,
        question: submittedQuestion,
        studentAnswer: submittedAnswer,
        idealAnswer: out.ideal_answer,
        isCorrect: out.is_correct,
        score: out.score,
        conceptLabel: out.concept_label,
        conceptId: out.concept_id,
        recommendedTopicId: recommendedTopicId,
        recommendedTopicTitle: recommendedTopicTitle,
        graphRemediation: out.graph_remediation || null,
      });
      setPendingAssessment(null);
      setAssessmentAnswer('');
      appendAssistant({
        assistant_message: out.feedback,
        key_points: [
          `${out.concept_label}: ${Math.round((out.score || 0) * 100)}%`,
          out.mastery_updated ? `Mastery updated to ${Math.round((out.new_mastery || 0) * 100)}%.` : 'No mastery update was applied.',
          out.graph_remediation?.blocking_prerequisite_label
            ? `Blocking prerequisite: ${out.graph_remediation.blocking_prerequisite_label}`
            : null,
          out.graph_remediation?.recommended_next_concept_label
            ? `Best next concept: ${out.graph_remediation.recommended_next_concept_label}`
            : null,
          out.graph_remediation?.recommended_next_topic_title
            ? `Recommended lesson: ${out.graph_remediation.recommended_next_topic_title}`
            : null,
          out.graph_remediation?.recommendation_reason || null,
        ].filter(Boolean),
        prerequisite_warning: out.graph_remediation?.blocking_prerequisite_label
          ? `You are still blocked by ${out.graph_remediation.blocking_prerequisite_label}.`
          : (out.prerequisite_warning || null),
        next_action: out.graph_remediation?.recommended_next_topic_title
          ? `Open ${out.graph_remediation.recommended_next_topic_title} next, or ask for a prerequisite bridge before moving on.`
          : out.recommended_topic_title
            ? `Next best focus: ${out.recommended_topic_title}.`
            : out.is_correct
              ? 'Push forward to the next unlock or try a harder drill.'
              : 'Ask for a prerequisite bridge and retry.',
        recommended_assessment: !out.is_correct && out.graph_remediation?.focus_concept_label
          ? `Recheck ${out.graph_remediation.focus_concept_label} with one more checkpoint after revising the prerequisite.`
          : null,
      });
      if (out.graph_remediation?.recommended_next_topic_id && out.graph_remediation?.recommended_next_topic_title) {
        setBootstrap((prev) => prev ? ({
          ...prev,
          next_unlock: {
            ...(prev.next_unlock || {}),
            topic_id: out.graph_remediation.recommended_next_topic_id,
            topic_title: out.graph_remediation.recommended_next_topic_title,
            concept_id: out.graph_remediation.recommended_next_concept_id || prev.next_unlock?.concept_id || null,
            concept_label: out.graph_remediation.recommended_next_concept_label || prev.next_unlock?.concept_label || null,
            reason: out.graph_remediation.recommendation_reason || prev.next_unlock?.reason || 'Recommended from latest assessment.',
          },
        }) : prev);
      }
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: err.message || 'Failed to submit checkpoint.' }]);
    } finally {
      setIsBusy(false);
    }
  };

  if (status === 'loading') {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center bg-slate-50">
        <div className="rounded-3xl border border-slate-200 bg-white px-8 py-10 text-center shadow-sm">
          <LoaderCircle className="mx-auto mb-4 animate-spin text-indigo-600" size={36} />
          <p className="text-sm font-semibold text-slate-700">Preparing your graph-first lesson cockpit...</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center bg-slate-50 px-6">
        <div className="max-w-xl rounded-3xl border border-rose-200 bg-white p-8 shadow-sm">
          <div className="mb-4 flex items-center gap-3 text-rose-600">
            <AlertCircle size={24} />
            <h1 className="text-xl font-black">Lesson cockpit unavailable</h1>
          </div>
          <p className="text-sm leading-7 text-slate-600">{error}</p>
          <div className="mt-6 flex gap-3">
            <button type="button" onClick={() => navigate('/dashboard')} className="rounded-2xl border border-slate-200 px-4 py-3 text-sm font-bold text-slate-700">
              Back to Dashboard
            </button>
            <button type="button" onClick={() => window.location.reload()} className="rounded-2xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white">
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-64px)] bg-slate-50">
      {isSidebarOpen && <button type="button" className="fixed inset-0 z-30 bg-slate-950/35 lg:hidden" onClick={() => setIsSidebarOpen(false)} />}

      <div className={`fixed inset-y-0 left-0 z-40 transition-transform duration-300 lg:relative ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <CourseSidebar activeStep={topicId} subject={currentSubject} level={currentLevel} topics={sidebarTopics} />
      </div>

      <div className="min-w-0 flex-1">
        <div className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 px-4 backdrop-blur md:px-8">
          <div className="flex h-16 items-center justify-between">
            <button type="button" onClick={() => setIsSidebarOpen((prev) => !prev)} className="inline-flex items-center gap-2 rounded-2xl px-3 py-2 text-sm font-bold text-slate-600 hover:bg-slate-100">
              <Menu size={18} />
              <span className="hidden md:inline">Syllabus</span>
            </button>
            <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-bold uppercase tracking-[0.2em] text-slate-500 md:flex">
              <GitBranch size={14} className="text-indigo-500" />
              Graph-first lesson mode
            </div>
            <button type="button" onClick={() => navigate(`/quiz/${topicId}`)} className="inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-4 py-2 text-sm font-bold text-white hover:bg-indigo-700">
              Take quiz
              <ArrowRight size={16} />
            </button>
          </div>
        </div>

        <div className="grid gap-6 p-4 md:p-8 xl:grid-cols-[minmax(0,1.45fr)_minmax(360px,0.9fr)]">
          <motion.section
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="space-y-6 overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm"
          >
            <div className="border-b border-slate-100 bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.18),_transparent_40%),linear-gradient(135deg,#ffffff,_#f8fafc)] p-6 md:p-8">
              <div className="mb-4 flex flex-wrap items-center gap-3 text-[11px] font-black uppercase tracking-[0.2em] text-slate-500">
                <button type="button" onClick={() => navigate('/dashboard')} className="inline-flex items-center gap-1 text-slate-400 hover:text-indigo-600">
                  <ArrowLeft size={14} />
                  Dashboard
                </button>
                <span>/</span>
                <span className="capitalize">{currentSubject}</span>
                <span>/</span>
                <span className="truncate text-slate-700">{lesson?.title}</span>
              </div>

              <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
                <div>
                  <h1 className="text-3xl font-black tracking-tight text-slate-950 md:text-4xl">{lesson?.title}</h1>
                  <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-600 md:text-base">{lesson?.summary}</p>
                  <div className="mt-6 flex flex-wrap gap-3">
                    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs shadow-sm">
                      <p className="font-black uppercase tracking-[0.2em] text-slate-400">Lesson Focus</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">{graphContext?.weakest_concepts?.[0]?.label || 'Current concept cluster'}</p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs shadow-sm">
                      <p className="font-black uppercase tracking-[0.2em] text-slate-400">Mastery Pulse</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">{masteryPulse !== null ? `${masteryPulse}% ready` : 'Unassessed'}</p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs shadow-sm">
                      <p className="font-black uppercase tracking-[0.2em] text-slate-400">Next Unlock</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">{bootstrap?.next_unlock?.topic_title || 'Stay on this lesson'}</p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs shadow-sm">
                      <p className="font-black uppercase tracking-[0.2em] text-slate-400">Context warmed</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">
                        {topicWarmSummary.currentCount} live / {topicWarmSummary.prereqCount} prereq / {topicWarmSummary.downstreamCount} unlock
                      </p>
                    </div>
                  </div>
                </div>
                <div className="rounded-[1.75rem] border border-indigo-200 bg-indigo-50 p-5 shadow-sm">
                  <div className="flex items-center gap-2 text-indigo-700">
                    <BrainCircuit size={18} />
                    <p className="text-xs font-black uppercase tracking-[0.2em]">Progress Pulse</p>
                  </div>
                  <p className="mt-4 text-sm leading-7 text-slate-700">{bootstrap?.why_this_topic}</p>
                  <div className="mt-5 grid gap-3">
                    <div className="rounded-2xl bg-white p-4">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Assessment readiness</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">{lesson?.assessment_ready ? 'Ready for a 1-minute checkpoint' : 'Lesson context still warming'}</p>
                    </div>
                    <div className="rounded-2xl bg-white p-4">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Weak prerequisite</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">{graphContext?.prerequisite_concepts?.[0]?.label || 'No blocking prerequisite detected'}</p>
                    </div>
                    {recentEvidence && (
                      <div className="rounded-2xl bg-white p-4">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Latest evidence</p>
                        <p className="mt-1 text-sm font-semibold leading-6 text-slate-800">{recentEvidence.summary}</p>
                        {(recentEvidence.strongest_gain_concept_label || recentEvidence.strongest_drop_concept_label) && (
                          <p className="mt-2 text-xs font-semibold leading-5 text-slate-500">
                            {recentEvidence.strongest_gain_concept_label ? `Gain: ${recentEvidence.strongest_gain_concept_label}` : 'No recent gain'}
                            {recentEvidence.strongest_drop_concept_label ? ` · Gap: ${recentEvidence.strongest_drop_concept_label}` : ''}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div className="grid gap-8 p-6 md:p-8">
              {safeArray(lesson?.content_blocks).map((block, index) => (
                <div key={`${block.type}-${index}`} className={`rounded-3xl ${block.type === 'example' ? 'border border-indigo-200 bg-indigo-50 p-5' : block.type === 'exercise' ? 'border border-emerald-200 bg-emerald-50 p-5' : ''}`}>
                  {block.type === 'example' && <p className="mb-2 text-[11px] font-black uppercase tracking-[0.25em] text-indigo-500">Worked Example</p>}
                  {block.type === 'exercise' && <p className="mb-2 text-[11px] font-black uppercase tracking-[0.25em] text-emerald-500">Checkpoint</p>}
                  <div className="whitespace-pre-wrap text-sm leading-8 text-slate-700">
                    {typeof block.value === 'string'
                      ? block.value
                      : typeof block.value === 'object' && block.value
                        ? block.value.note || block.value.solution || block.value.question || JSON.stringify(block.value)
                        : ''}
                  </div>
                </div>
              ))}
              <div className="flex flex-wrap gap-3 border-t border-slate-100 pt-6">
                <button type="button" onClick={() => navigate(`/quiz/${topicId}`)} className="inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white hover:bg-indigo-700">
                  Take mastery quiz
                  <ArrowRight size={16} />
                </button>
                <button type="button" onClick={handleDrill} className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-bold text-slate-700 hover:bg-slate-50">
                  <Zap size={16} />
                  1-minute drill
                </button>
                <button type="button" onClick={handleStudyPlan} className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-bold text-slate-700 hover:bg-slate-50">
                  <NotebookPen size={16} />
                  7-day plan
                </button>
              </div>
            </div>
          </motion.section>

          <motion.aside
            initial={{ opacity: 0, x: 18 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.35, delay: 0.05 }}
            className="space-y-6"
          >
            <LessonKnowledgeGraph
              graphContext={graphContext}
              nextUnlock={bootstrap?.next_unlock}
              whyTopicDetail={whyTopicDetail}
              onOpenTopic={openRecommendedLesson}
            />

            <section className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <BrainCircuit className="text-indigo-600" size={18} />
                <h2 className="text-sm font-black uppercase tracking-[0.2em] text-slate-600">Mastery Overlay</h2>
              </div>
              <div className="grid gap-3">
                {safeArray(graphContext?.current_concepts).map((concept) => <ConceptChip key={concept.concept_id} concept={concept} />)}
                {!safeArray(graphContext?.current_concepts).length && (
                  <p className="rounded-2xl bg-slate-50 px-3 py-3 text-xs text-slate-500">Graph context is still warming for this topic.</p>
                )}
              </div>
            </section>

            {interventionTimeline.length > 0 && (
              <InterventionTimeline
                title="Intervention Timeline"
                subtitle="Recent quiz and checkpoint evidence shaping this lesson path."
                timeline={interventionTimeline}
                compact
              />
            )}

            <section className="rounded-[2rem] border border-slate-200 bg-white shadow-sm">
              <div className="border-b border-slate-100 p-5">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-600 text-white">
                      <Bot size={18} />
                    </div>
                      <div>
                        <h2 className="text-sm font-black uppercase tracking-[0.2em] text-slate-600">Tutor Workbench</h2>
                      <p className="text-xs text-slate-500">{streamPhase || 'Lesson-aware, graph-grounded, and cache-warmed'}</p>
                    </div>
                  </div>
                  <button type="button" onClick={() => sendChat('Teach me like I am completely new to this lesson.')} className="hidden rounded-2xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 md:inline-flex">
                    Teach from zero
                  </button>
                </div>
              </div>
              <div className="p-5">
                <div className="mb-4 grid gap-2 sm:grid-cols-2">
                  {quickActions.map((action) => {
                    const Icon = iconByIntent[action.icon] || iconByIntent[action.intent] || MessageSquare;
                    return (
                      <button key={action.id} type="button" disabled={isBusy} onClick={() => handleQuickAction(action)} className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-left transition hover:border-indigo-300 hover:bg-indigo-50 disabled:opacity-60">
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5 rounded-xl bg-white p-2 text-indigo-600 shadow-sm">
                            <Icon size={16} />
                          </div>
                          <div>
                            <p className="text-sm font-bold text-slate-800">{action.label}</p>
                            <p className="mt-1 text-xs leading-5 text-slate-500">{action.prompt}</p>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
                {pendingAssessment && (
                  <div className="mb-4 rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-4">
                    <div className="mb-3 flex items-center gap-2 text-emerald-700">
                      <Target size={16} />
                      <p className="text-xs font-black uppercase tracking-[0.2em]">Live checkpoint</p>
                    </div>
                    <p className="text-sm font-semibold leading-7 text-slate-800">{pendingAssessment.question}</p>
                    {pendingAssessment.hint && <p className="mt-2 text-xs leading-6 text-emerald-800">Hint: {pendingAssessment.hint}</p>}
                    <textarea value={assessmentAnswer} onChange={(event) => setAssessmentAnswer(event.target.value)} rows={4} placeholder="Answer the checkpoint here..." className="mt-4 w-full rounded-2xl border border-emerald-200 bg-white px-4 py-3 text-sm outline-none focus:border-emerald-400" />
                    <div className="mt-3 flex flex-wrap gap-3">
                      <button type="button" onClick={submitAssessment} disabled={isBusy || !assessmentAnswer.trim()} className="inline-flex items-center gap-2 rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-60">
                        <CheckCircle2 size={16} />
                        Submit checkpoint
                      </button>
                      <button type="button" onClick={() => startAssessment('hard')} disabled={isBusy} className="inline-flex items-center gap-2 rounded-2xl border border-emerald-300 bg-white px-4 py-3 text-sm font-bold text-emerald-700 disabled:opacity-60">
                        <Zap size={16} />
                        Try harder checkpoint
                      </button>
                    </div>
                  </div>
                )}
                {lastAssessmentReview && (
                  <div className={`mb-4 rounded-[1.5rem] border p-4 ${lastAssessmentReview.isCorrect ? 'border-indigo-200 bg-indigo-50' : 'border-amber-200 bg-amber-50'}`}>
                    <div className={`mb-3 flex items-center gap-2 ${lastAssessmentReview.isCorrect ? 'text-indigo-700' : 'text-amber-700'}`}>
                      {lastAssessmentReview.isCorrect ? <CheckCircle2 size={16} /> : <ShieldAlert size={16} />}
                      <p className="text-xs font-black uppercase tracking-[0.2em]">
                        {lastAssessmentReview.isCorrect ? 'Checkpoint cleared' : 'Checkpoint follow-up'}
                      </p>
                    </div>
                    <p className="text-sm font-semibold text-slate-800">
                      {lastAssessmentReview.conceptLabel} - {Math.round((lastAssessmentReview.score || 0) * 100)}%
                    </p>
                    <p className="mt-2 text-xs leading-6 text-slate-600">
                      {lastAssessmentReview.isCorrect
                        ? 'Push into a harder checkpoint or open the recommended next lesson while the concept is warm.'
                        : 'Review the mistake explanation, then retry or bridge the blocking prerequisite.'}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-3">
                      {!lastAssessmentReview.isCorrect && (
                        <button type="button" onClick={explainLastMistake} disabled={isBusy} className="inline-flex items-center gap-2 rounded-2xl bg-amber-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-60">
                          <ShieldAlert size={16} />
                          Explain my mistake
                        </button>
                      )}
                      <button type="button" onClick={() => startAssessment(lastAssessmentReview.isCorrect ? 'hard' : 'medium')} disabled={isBusy} className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 disabled:opacity-60">
                        <Target size={16} />
                        {lastAssessmentReview.isCorrect ? 'Try harder checkpoint' : 'Retry checkpoint'}
                      </button>
                      {lastAssessmentReview.recommendedTopicId && (
                        <button type="button" onClick={() => openRecommendedLesson(lastAssessmentReview.recommendedTopicId)} className="inline-flex items-center gap-2 rounded-2xl border border-indigo-200 bg-white px-4 py-3 text-sm font-bold text-indigo-700">
                          Open recommended lesson
                          <ArrowRight size={16} />
                        </button>
                      )}
                    </div>
                  </div>
                )}
                <div ref={scrollRef} className="max-h-[480px] space-y-4 overflow-y-auto rounded-[1.5rem] bg-slate-50 p-4">
                  {messages.map((item, index) => (
                    <MessageCard
                      key={`${item.role}-${index}`}
                      item={item}
                      onOpenRecommendation={openRecommendedLesson}
                      onStartCheckpoint={() => startAssessment()}
                      onOpenPrereqBridge={handlePrereqBridge}
                      onStartDrill={handleDrill}
                    />
                  ))}
                  {isBusy && (
                    <div className="rounded-3xl border border-slate-200 bg-white p-4 text-sm text-slate-500">
                      <div className="flex items-center gap-3">
                        <LoaderCircle className="animate-spin text-indigo-600" size={18} />
                        <span>{streamPhase || 'Tutor is building a grounded response...'}</span>
                      </div>
                    </div>
                  )}
                </div>
                <form onSubmit={(event) => { event.preventDefault(); sendChat(); }} className="mt-4">
                  <div className="rounded-[1.5rem] border border-slate-200 bg-white p-3 shadow-sm">
                    <textarea value={chatInput} onChange={(event) => setChatInput(event.target.value)} rows={3} placeholder="Ask about this lesson, a prerequisite, or how this unlocks the next concept..." className="w-full resize-none border-none bg-transparent px-1 py-1 text-sm text-slate-700 outline-none" />
                    <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3">
                      <div className="flex flex-wrap gap-2 text-xs">
                        <button type="button" onClick={() => sendChat('Explain this lesson with one real-life example.')} className="rounded-full bg-slate-100 px-3 py-1.5 font-semibold text-slate-600">Real-life example</button>
                        <button type="button" onClick={() => sendChat('Show me the common mistake students make here.')} className="rounded-full bg-slate-100 px-3 py-1.5 font-semibold text-slate-600">Common mistake</button>
                      </div>
                      <button type="submit" disabled={isBusy || !chatInput.trim()} className="inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-4 py-2 text-sm font-bold text-white disabled:opacity-60">
                        Send
                        <Send size={15} />
                      </button>
                    </div>
                  </div>
                </form>
              </div>
            </section>
          </motion.aside>
        </div>
      </div>
    </div>
  );
}
