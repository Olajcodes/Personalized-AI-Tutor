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
import PresentationCueCard from '../components/PresentationCueCard';
import LessonKnowledgeGraph from '../components/lesson/LessonKnowledgeGraph';
import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';
import { saveGraphIntervention } from '../services/graphIntervention';

const API_URL = import.meta.env.VITE_API_URL || 'https://mastery-backend-7xe8.onrender.com/api/v1';
const safeArray = (value) => (Array.isArray(value) ? value : []);
const BOOTSTRAP_CACHE_TTL_MS = 45_000;
const lessonBootstrapCache = new Map();
const MODE_STORAGE_KEY = 'mastery_tutor_mode';

const iconByIntent = {
  teach: Sparkles,
  socratic: Route,
  diagnose: ShieldAlert,
  drill: Zap,
  recap: NotebookPen,
  'exam-practice': Target,
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

const TUTOR_MODES = [
  { id: 'teach', label: 'Teach', description: 'Direct explanation with clear steps.' },
  { id: 'socratic', label: 'Socratic', description: 'Guided questions to uncover the rule.' },
  { id: 'diagnose', label: 'Diagnose', description: 'Spot misconceptions and fix gaps.' },
  { id: 'drill', label: 'Drill', description: 'Short, focused practice prompts.' },
  { id: 'recap', label: 'Recap', description: 'Summarize key ideas quickly.' },
  { id: 'exam-practice', label: 'Exam', description: 'Exam-style prompts and timing.' },
];

const FOLLOW_UP_ACTIONS = [
  { id: 'simpler', label: 'Explain simpler', prompt: 'Explain this in simpler terms.', mode: 'teach' },
  { id: 'example', label: 'Show example', prompt: 'Give one concrete example for this topic.', mode: 'teach' },
  { id: 'check', label: 'Ask me one question', prompt: 'Ask me one short question to check understanding.', mode: 'socratic' },
  { id: 'waec', label: 'WAEC-style', prompt: 'Give me one WAEC-style question on this topic.', mode: 'exam-practice' },
];

const MODE_DEFAULT_PROMPTS = {
  teach: 'Teach this lesson step-by-step with one quick example.',
  socratic: 'Ask me 3 short questions that guide me to the rule.',
  diagnose: 'Diagnose where I might be confused and fix the gap.',
  drill: 'Give me one focused drill question on this lesson.',
  recap: 'Recap this lesson in three sharp points and a memory hook.',
  'exam-practice': 'Give me one WAEC-style question and show how to answer it.',
};

const bootstrapCacheKey = ({ studentId, subject, level, term, topicId }) => [studentId, subject, level, term, topicId].join(':');

const createMessageId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

  const STREAM_PHASE_LABELS = {
    retrieving_context: 'Gathering lesson context...',
    composing_response: 'Drafting the response...',
    finalizing_response: 'Finalizing actions...',
  };

  const MODE_LABELS = {
    teach: 'Teach',
    socratic: 'Socratic',
    diagnose: 'Diagnose',
    drill: 'Drill',
    recap: 'Recap',
    'exam-practice': 'Exam Practice',
  };

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

  const toUserActions = (actions = []) => {
    return safeArray(actions)
      .map((action) => String(action || '').trim())
      .filter((action) => action.length > 0)
      .filter((action) => !/^[A-Z0-9_:\-]+$/.test(action))
      .filter((action) => !action.startsWith('http'))
      .filter((action) => action.length <= 140);
  };

  function MessageCard({
    item,
    onOpenRecommendation,
    onStartCheckpoint,
    onOpenPrereqBridge,
    onStartDrill,
  followUps,
  onFollowUp,
  showFollowUps,
  }) {
    const isStudent = item.role === 'student';
    const isStreaming = !isStudent && Boolean(item.streaming);
    const showCheckpointAction = !isStudent && Boolean(item.recommended_assessment);
    const showPrereqAction = !isStudent && Boolean(item.prerequisite_warning);
    const showDrillAction = !isStudent && safeArray(item.concept_focus).length > 0;
    const userActions = toUserActions(item.actions);
    const showActionChips = !isStudent && userActions.length > 0;
    const showFollowUpActions = !isStudent && !item.streaming && showFollowUps && safeArray(followUps).length > 0;
    const modeLabel = item.mode ? (MODE_LABELS[item.mode] || item.mode) : null;
    return (
      <div className={`flex ${isStudent ? 'justify-end' : 'justify-start'}`}>
        <div className={`max-w-[92%] rounded-3xl p-4 text-sm ${isStudent ? 'bg-indigo-600 text-white' : 'border border-slate-200 bg-white text-slate-700'}`}>
          {isStudent ? (
            <p className="whitespace-pre-wrap">{item.content}</p>
          ) : (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
                <span>Tutor response</span>
                {modeLabel && <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2 py-0.5 text-indigo-700">{modeLabel}</span>}
              </div>
              <div>
                <p className="mb-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Answer</p>
                <div className="whitespace-pre-wrap text-sm leading-7">{item.content || ''}</div>
              </div>
              {isStreaming && (
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <LoaderCircle className="animate-spin text-indigo-500" size={14} />
                  <span>Streaming response...</span>
                </div>
              )}
            {item.error && (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
                {item.error}
              </div>
            )}
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
              {(item.prerequisite_warning || item.next_action || item.recommended_assessment || item.recommended_topic_title || showDrillAction) && (
                <div className="grid gap-2">
                  {item.prerequisite_warning && (
                    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
                      <p className="mb-1 text-[10px] font-black uppercase tracking-[0.2em] text-amber-500">Prerequisite alert</p>
                      <p>{item.prerequisite_warning}</p>
                    </div>
                  )}
                  {(item.next_action || item.recommended_topic_title) && (
                    <div className="rounded-2xl border border-indigo-200 bg-indigo-50 p-3 text-xs text-indigo-800">
                      <p className="mb-1 text-[10px] font-black uppercase tracking-[0.2em] text-indigo-500">Next step</p>
                      {item.next_action && <p>{item.next_action}</p>}
                      {item.recommended_topic_title && (
                        <p className="mt-1 text-[11px] font-semibold text-indigo-700">Next lesson: {item.recommended_topic_title}</p>
                      )}
                    </div>
                  )}
                  {item.recommended_assessment && (
                    <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800">
                      <p className="mb-1 text-[10px] font-black uppercase tracking-[0.2em] text-emerald-500">Recommended check</p>
                      <p>{item.recommended_assessment}</p>
                    </div>
                  )}
                  {showDrillAction && (
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
                      <p className="mb-1 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Optional drill</p>
                      <button
                        type="button"
                        onClick={onStartDrill}
                        className="mt-1 inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-[11px] font-black uppercase tracking-[0.16em] text-slate-700 hover:bg-slate-50"
                      >
                        <Zap size={14} />
                        1-minute drill
                      </button>
                    </div>
                  )}
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
              {showActionChips && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                  <p className="mb-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Suggested actions</p>
                  <div className="flex flex-wrap gap-2">
                    {userActions.map((action, index) => (
                      <button
                        key={`${action}-${index}`}
                        type="button"
                        onClick={() => onFollowUp?.({ prompt: action, label: action })}
                        disabled={item.streaming}
                      className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold text-slate-600 hover:border-indigo-200 hover:text-indigo-700 disabled:opacity-60"
                    >
                      {action}
                    </button>
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
              {(showCheckpointAction || showPrereqAction) && (
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
                </div>
              )}
            {showFollowUpActions && (
              <div className="flex flex-wrap gap-2">
                {followUps.map((action) => (
                  <button
                    key={action.id}
                    type="button"
                    onClick={() => onFollowUp?.(action)}
                    disabled={item.streaming}
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-[11px] font-black uppercase tracking-[0.16em] text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                  >
                    {action.label}
                  </button>
                ))}
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
  const [pendingAdaptiveAction, setPendingAdaptiveAction] = useState(null);
  const [lastAssessmentReview, setLastAssessmentReview] = useState(null);
  const [selectedGraphConcept, setSelectedGraphConcept] = useState(null);
  const [selectedMode, setSelectedMode] = useState(() => {
    if (typeof window === 'undefined') return 'teach';
    const stored = window.localStorage.getItem(MODE_STORAGE_KEY);
    return TUTOR_MODES.some((mode) => mode.id === stored) ? stored : 'teach';
  });
  const [isBusy, setIsBusy] = useState(false);
  const [streamPhase, setStreamPhase] = useState('');
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');
  const scrollRef = useRef(null);
  const streamingMessageRef = useRef(null);
  const adaptiveInterventionRef = useRef({});
  const activeCacheKey = useMemo(
    () => bootstrapCacheKey({ studentId: activeId, subject: currentSubject, level: currentLevel, term: currentTerm, topicId }),
    [activeId, currentLevel, currentSubject, currentTerm, topicId],
  );

  const lesson = bootstrap?.lesson || null;
  const graphContext = bootstrap?.graph_context || null;
  const whyTopicDetail = bootstrap?.why_topic_detail || null;
  const mapError = bootstrap?.map_error || null;
  const sessionId = bootstrap?.session_id || null;
  const quickActions = safeArray(bootstrap?.suggested_actions);
  const recentEvidence = bootstrap?.recent_evidence || null;
  const interventionTimeline = safeArray(bootstrap?.intervention_timeline);
  const graphStatus = graphContext?.status || (graphContext ? 'ready' : 'unavailable');
  const graphUnavailableReason = graphContext?.unavailable_reason || mapError || null;
  const graphAvailable = graphStatus === 'ready' && safeArray(graphContext?.current_concepts).length > 0;
  const lessonBlocks = safeArray(lesson?.content_blocks);
  const lessonAvailable = Boolean(lesson) && lessonBlocks.length > 0;

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isBusy, pendingAssessment]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(MODE_STORAGE_KEY, selectedMode);
  }, [selectedMode]);

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
          buildAssistantMessage({
            assistant_message: cachedBootstrap.greeting || 'Your lesson cockpit is ready.',
            key_points: [
              cachedBootstrap.why_this_topic || 'Use the graph rail to see why this lesson matters.',
              cachedBootstrap.recent_evidence?.summary || null,
            ].filter(Boolean),
          }),
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
          map_error: cockpitJson.map_error || null,
          why_topic_detail: cockpitJson.why_topic_detail || null,
        };
        setSidebarTopics(safeArray(cockpitJson.topics));
        setBootstrap(bootstrapJson);
        writeBootstrapCache(activeCacheKey, bootstrapJson);
        setPendingAssessment(bootstrapJson.pending_assessment || null);
        setMessages([
          buildAssistantMessage({
            assistant_message: bootstrapJson.greeting || 'Your lesson cockpit is ready.',
            key_points: [
              bootstrapJson.why_this_topic || 'Use the graph rail to see why this lesson matters.',
              cockpitJson.recent_evidence?.summary || null,
            ].filter(Boolean),
          }),
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

  useEffect(() => {
    if (!pendingAdaptiveAction || isBusy) return;
    const runAdaptive = async () => {
      const action = pendingAdaptiveAction;
      setPendingAdaptiveAction(null);
      if (action.type === 'bridge_prerequisite') {
        appendAssistant({
          assistant_message: action.reason || 'I noticed repeated misses. Let’s bridge the prerequisite before retrying.',
        });
        if (action.blockingLabel) {
          await handleBridgeLabel(action.blockingLabel);
          return;
        }
        await handlePrereqBridge();
        return;
      }
      if (action.type === 'harder_checkpoint') {
        appendAssistant({
          assistant_message: action.reason || 'Nice momentum. Let’s try a harder checkpoint.',
        });
        await startAssessment(action.difficulty || 'hard');
      }
    };
    runAdaptive();
  }, [pendingAdaptiveAction, isBusy]);

  const masteryPulse = useMemo(() => {
    const currentConcepts = safeArray(graphContext?.current_concepts);
    if (!currentConcepts.length) return null;
    const average = currentConcepts.reduce((sum, item) => sum + (item.mastery_score || 0), 0) / currentConcepts.length;
    return Math.round(average * 100);
  }, [graphContext]);
  const evidenceSummary = useMemo(() => {
    const currentConcepts = safeArray(graphContext?.current_concepts);
    if (!currentConcepts.length) return null;
    return currentConcepts.reduce((acc, concept) => {
      const state = concept.mastery_state || 'unassessed';
      if (state === 'demonstrated') acc.demonstrated += 1;
      else if (state === 'needs_review') acc.needs_review += 1;
      else acc.unassessed += 1;
      return acc;
    }, { demonstrated: 0, needs_review: 0, unassessed: 0 });
  }, [graphContext]);

  const evidenceTotal = useMemo(() => {
    if (!evidenceSummary) return 0;
    return evidenceSummary.demonstrated + evidenceSummary.needs_review + evidenceSummary.unassessed;
  }, [evidenceSummary]);

  const whyStory = useMemo(() => {
    if (whyTopicDetail?.explanation) return whyTopicDetail.explanation;
    if (bootstrap?.why_this_topic) return bootstrap.why_this_topic;
    return null;
  }, [bootstrap?.why_this_topic, whyTopicDetail]);

  const activeMode = useMemo(
    () => TUTOR_MODES.find((mode) => mode.id === selectedMode) || TUTOR_MODES[0],
    [selectedMode],
  );

  const assessmentStatus = useMemo(() => {
    if (pendingAssessment) {
      return {
        label: 'Checkpoint pending',
        detail: 'Resume the live checkpoint to log mastery.',
        tone: 'emerald',
      };
    }
    if (lastAssessmentReview && !lastAssessmentReview.isCorrect) {
      return {
        label: 'Needs review',
        detail: 'Recent checkpoint showed a gap. Retry or bridge the prerequisite.',
        tone: 'amber',
      };
    }
    if (lastAssessmentReview && lastAssessmentReview.isCorrect) {
      return {
        label: 'Mastery demonstrated',
        detail: 'Checkpoint cleared. Push ahead or try a harder one.',
        tone: 'indigo',
      };
    }
    if (lesson?.assessment_ready) {
      return {
        label: 'Ready for checkpoint',
        detail: 'Take a 1-minute check to record mastery.',
        tone: 'emerald',
      };
    }
    return {
      label: 'Unassessed',
      detail: 'No mastery evidence recorded yet for this lesson.',
      tone: 'slate',
    };
  }, [pendingAssessment, lastAssessmentReview, lesson?.assessment_ready]);

  const assessmentRecommendation = useMemo(() => {
    if (!lastAssessmentReview) return null;
    const remediation = lastAssessmentReview.graphRemediation || null;
    const recommendedTopicId = lastAssessmentReview.recommendedTopicId || remediation?.recommended_next_topic_id || null;
    const recommendedTopicTitle = lastAssessmentReview.recommendedTopicTitle || remediation?.recommended_next_topic_title || null;
    const blockingLabel = remediation?.blocking_prerequisite_label || null;
    const blockingTopicTitle = remediation?.blocking_prerequisite_topic_title || null;
    if (blockingLabel) {
      return {
        tone: 'amber',
        headline: `Bridge ${blockingLabel}`,
        detail: remediation?.recommendation_reason
          || (blockingTopicTitle
            ? `Revisit ${blockingTopicTitle} before retrying this checkpoint.`
            : 'Repair the blocking prerequisite before moving forward.'),
        actionLabel: blockingTopicTitle ? `Open ${blockingTopicTitle}` : 'Bridge prerequisite',
        actionType: blockingTopicTitle ? 'open_topic' : 'bridge_label',
        actionValue: blockingTopicTitle ? recommendedTopicId : blockingLabel,
      };
    }
    if (recommendedTopicId && recommendedTopicTitle && String(recommendedTopicId) !== String(topicId)) {
      return {
        tone: 'indigo',
        headline: `Next best lesson: ${recommendedTopicTitle}`,
        detail: remediation?.recommendation_reason || 'Your mastery evidence is ready to move forward.',
        actionLabel: `Open ${recommendedTopicTitle}`,
        actionType: 'open_topic',
        actionValue: recommendedTopicId,
      };
    }
    if (!lastAssessmentReview.isCorrect) {
      return {
        tone: 'rose',
        headline: 'Retry this checkpoint',
        detail: 'Review the explanation, then answer the checkpoint again to log mastery.',
        actionLabel: 'Retry checkpoint',
        actionType: 'retry',
        actionValue: null,
      };
    }
    return {
      tone: 'emerald',
      headline: 'You are ready to advance',
      detail: 'Push into a harder checkpoint or continue the lesson flow.',
      actionLabel: 'Try harder checkpoint',
      actionType: 'harder',
      actionValue: null,
    };
  }, [lastAssessmentReview, topicId]);

  const lastAssistantIndex = useMemo(() => {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      if (messages[index]?.role !== 'student') return index;
    }
    return -1;
  }, [messages]);

  const buildAssistantMessage = (payload = {}, overrides = {}) => ({
    id: overrides.id || payload.id || createMessageId(),
    role: 'assistant',
    content: payload.assistant_message || payload.message || payload.content || '',
    mode: payload.mode || null,
    key_points: payload.key_points || [],
    concept_focus: payload.concept_focus || [],
    citations: payload.citations || [],
    recommendations: payload.recommendations || [],
    actions: payload.actions || [],
    next_action: payload.next_action || null,
    prerequisite_warning: payload.prerequisite_warning || null,
    recommended_assessment: payload.recommended_assessment || null,
    recommended_topic_title: payload.recommended_topic_title || null,
    streaming: overrides.streaming || false,
    error: overrides.error || null,
  });

  const appendAssistant = (payload, overrides = {}) => {
    setMessages((prev) => [...prev, buildAssistantMessage(payload, overrides)]);
  };

  const startStreamingMessage = () => {
    const id = createMessageId();
    streamingMessageRef.current = id;
    setMessages((prev) => [
      ...prev,
      buildAssistantMessage({ assistant_message: '' }, { id, streaming: true }),
    ]);
    return id;
  };

  const updateStreamingMessage = (delta) => {
    const id = streamingMessageRef.current;
    if (!id || !delta) return;
    setMessages((prev) => prev.map((item) => (
      item.id === id
        ? { ...item, content: `${item.content || ''}${delta}` }
        : item
    )));
  };

  const finalizeStreamingMessage = (payload) => {
    const id = streamingMessageRef.current;
    if (!id) {
      appendAssistant(payload);
      return;
    }
    const finalMessage = buildAssistantMessage(payload, { id });
    setMessages((prev) => prev.map((item) => (
      item.id === id ? { ...finalMessage, streaming: false } : item
    )));
    streamingMessageRef.current = null;
  };

  const failStreamingMessage = (errorMessage) => {
    const id = streamingMessageRef.current;
    const message = errorMessage?.message || errorMessage || 'Tutor request failed.';
    if (!id) {
      appendAssistant({ assistant_message: message });
      return;
    }
    setMessages((prev) => prev.map((item) => (
      item.id === id ? { ...item, streaming: false, error: message } : item
    )));
    streamingMessageRef.current = null;
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

  const graphPulse = useMemo(() => {
    const currentLabel = graphContext?.current_concepts?.[0]?.label || null;
    const weakPrereqLabel = graphContext?.prerequisite_concepts?.[0]?.label || null;
    const nextUnlockLabel = bootstrap?.next_unlock?.topic_title || bootstrap?.next_unlock?.concept_label || null;
    const readiness = graphAvailable ? 'Graph ready' : 'Graph warming';
    return { currentLabel, weakPrereqLabel, nextUnlockLabel, readiness };
  }, [bootstrap?.next_unlock, graphAvailable, graphContext]);

  const fetchWhyThisTopic = async () => {
    const params = new URLSearchParams({
      student_id: activeId,
      subject: currentSubject,
      sss_level: currentLevel,
      term: String(currentTerm),
      topic_id: topicId,
    });
    const response = await fetch(`${API_URL}/learning/graph/why-this-topic?${params.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      const err = await response.json().catch(() => null);
      throw new Error(err?.detail || 'Why this topic is unavailable.');
    }
    return response.json();
  };

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

  const refreshCockpit = async ({ silent = true } = {}) => {
    if (!activeId || !token || !topicId) return;
    if (!silent) setStreamPhase('Refreshing graph context...');
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
        throw new Error(err?.detail || 'Failed to refresh lesson cockpit.');
      }
      const cockpitJson = await response.json();
      const bootstrapJson = {
        ...cockpitJson.tutor_bootstrap,
        recent_evidence: cockpitJson.recent_evidence || null,
        intervention_timeline: safeArray(cockpitJson.intervention_timeline),
        map_error: cockpitJson.map_error || null,
        why_topic_detail: cockpitJson.why_topic_detail || null,
      };
      setSidebarTopics(safeArray(cockpitJson.topics));
      setBootstrap(bootstrapJson);
      writeBootstrapCache(activeCacheKey, bootstrapJson);
      setPendingAssessment(bootstrapJson.pending_assessment || null);
    } catch (err) {
      console.warn('Lesson cockpit refresh skipped:', err);
    } finally {
      if (!silent) setStreamPhase('');
    }
  };

  const consumeStream = async (payload) => {
    try {
      const response = await fetch(`${API_URL}/tutor/chat/stream`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok || !response.body) {
        const err = await response.json().catch(() => null);
        throw new Error(err?.detail || 'Tutor stream failed.');
      }

      startStreamingMessage();
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
          if (event === 'status') setStreamPhase(STREAM_PHASE_LABELS[data.phase] || data.phase || '');
          if (event === 'delta') updateStreamingMessage(data.content || '');
          if (event === 'message') finalizeStreamingMessage(data);
          if (event === 'error') throw new Error(data.detail || 'Tutor stream failed.');
          if (event === 'done') setStreamPhase('');
        }
      }
    } catch (err) {
      failStreamingMessage(err);
      throw err;
    }
  };

  const sendChat = async (message, options = {}) => {
    const trimmed = (message ?? chatInput).trim();
    if (!trimmed || !sessionId || isBusy) return;
    setMessages((prev) => [...prev, { id: createMessageId(), role: 'student', content: trimmed }]);
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
        focus_concept_id: options.focusConceptId || null,
        focus_concept_label: options.focusConceptLabel || null,
        mode: options.mode ?? selectedMode ?? null,
        message: trimmed,
      });
    } catch (err) {
      console.warn('Tutor stream failed:', err);
    } finally {
      setIsBusy(false);
      setStreamPhase('');
    }
  };

  const startAssessment = async (difficulty = 'medium', options = {}) => {
    if (!sessionId || isBusy) return;
    const effectiveFocusConceptId = options.focusConceptId || selectedGraphConcept?.concept_id || null;
    const effectiveFocusConceptLabel = options.focusConceptLabel || selectedGraphConcept?.label || null;
    setIsBusy(true);
    try {
      const out = await postJson('/tutor/assessment/start', {
        student_id: activeId,
        session_id: sessionId,
        subject: currentSubject,
        sss_level: currentLevel,
        term: currentTerm,
        topic_id: topicId,
        focus_concept_id: effectiveFocusConceptId,
        focus_concept_label: effectiveFocusConceptLabel,
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
          effectiveFocusConceptLabel && effectiveFocusConceptLabel !== out.concept_label
            ? `Requested graph focus: ${effectiveFocusConceptLabel}`
            : null,
        ],
        next_action: difficulty === 'hard'
          ? 'Push for a sharper answer and justify it clearly.'
          : 'Answer the checkpoint below to update your mastery.',
      });
    } catch (err) {
      appendAssistant({ assistant_message: err.message || 'Checkpoint unavailable.' });
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
      appendAssistant({ assistant_message: err.message || 'Recap unavailable.' });
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
      appendAssistant({ assistant_message: err.message || 'Prerequisite bridge unavailable.' });
    } finally {
      setIsBusy(false);
    }
  };

  const handleGraphExplain = async (concept) => {
    if (!concept || isBusy) return;
    const conceptLabel = concept.label || 'this concept';
    const contextTitle = concept.topic_title || lesson?.title || 'this lesson';
    await sendChat(
      `Explain ${conceptLabel} inside ${contextTitle}. Show how it connects to the current lesson and what students usually miss.`,
      {
        focusConceptId: concept.concept_id || null,
        focusConceptLabel: conceptLabel,
      },
    );
  };

  const handleGraphBridge = async (concept) => {
    if (!concept || isBusy) return;
    const conceptLabel = concept.label || 'this concept';
    const blockingLabel = safeArray(concept.blocking_prerequisite_labels)[0];
    if (blockingLabel) {
      await sendChat(
        `Bridge ${blockingLabel} into ${conceptLabel} for me. Start from the prerequisite, then connect it to this lesson with one clear example.`,
        {
          focusConceptId: concept.concept_id || null,
          focusConceptLabel: conceptLabel,
        },
      );
      return;
    }
    await sendChat(
      `Connect the previous concept in this lesson graph to ${conceptLabel} and explain why that bridge matters.`,
      {
        focusConceptId: concept.concept_id || null,
        focusConceptLabel: conceptLabel,
      },
    );
  };

  const handleGraphDrill = async (concept) => {
    if (!concept || isBusy) return;
    const conceptLabel = concept.label || 'this concept';
    await startAssessment('medium', {
      focusConceptId: concept.concept_id || null,
      focusConceptLabel: conceptLabel,
    });
  };

  const handleWhyThisTopic = async () => {
    if (isBusy) return;
    setIsBusy(true);
    try {
      const detail = bootstrap?.why_topic_detail || await fetchWhyThisTopic();
      const prereqs = safeArray(detail?.prerequisite_labels);
      const unlocks = safeArray(detail?.unlock_labels);
      appendAssistant({
        assistant_message: detail?.explanation || 'This topic is placed to bridge prerequisites into the next unlock.',
        key_points: [
          prereqs.length ? `Prerequisites: ${prereqs.join(', ')}` : null,
          unlocks.length ? `Unlocks: ${unlocks.join(', ')}` : null,
        ].filter(Boolean),
        prerequisite_warning: detail?.weakest_prerequisite_label
          ? `Weakest prerequisite: ${detail.weakest_prerequisite_label}`
          : null,
        next_action: detail?.recommended_next?.topic_title
          ? `Next unlock: ${detail.recommended_next.topic_title}`
          : 'Stay with the current lesson until evidence is stronger.',
      });
    } catch (err) {
      appendAssistant({ assistant_message: err.message || 'Why this topic is unavailable.' });
    } finally {
      setIsBusy(false);
    }
  };

  const handleQuickAction = async (action) => {
    if (action.id === 'why-this-topic') {
      await handleWhyThisTopic();
      return;
    }
    if (action.intent === 'assessment_start') {
      await startAssessment('medium', {
        focusConceptId: action.focus_concept_id || null,
        focusConceptLabel: action.focus_concept_label || null,
      });
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
    sendChat(action.prompt, { mode: action.intent });
  };

  const runModeAction = async () => {
    if (isBusy) return;
    if (selectedMode === 'recap') {
      await handleRecap();
      return;
    }
    if (selectedMode === 'drill') {
      await handleDrill();
      return;
    }
    const prompt = MODE_DEFAULT_PROMPTS[selectedMode] || MODE_DEFAULT_PROMPTS.teach;
    await sendChat(prompt, { mode: selectedMode });
  };

  const handleFollowUp = (action) => {
    if (!action) return;
    const prompt = action.prompt || action.label;
    if (!prompt) return;
    sendChat(prompt, { mode: action.mode || selectedMode });
  };

  const handleBridgeLabel = async (label) => {
    if (!label || isBusy) return;
    await sendChat(
      `Bridge ${label} into the current lesson. Start from the prerequisite, then connect it with one example.`,
      { mode: 'socratic' },
    );
  };

  const handleAssessmentRecommendation = async () => {
    if (!assessmentRecommendation || isBusy) return;
    const { actionType, actionValue } = assessmentRecommendation;
    if (actionType === 'open_topic' && actionValue) {
      await openRecommendedLesson(actionValue);
      return;
    }
    if (actionType === 'bridge_label' && actionValue) {
      await handleBridgeLabel(actionValue);
      return;
    }
    if (actionType === 'retry') {
      await startAssessment('medium');
      return;
    }
    if (actionType === 'harder') {
      await startAssessment('hard');
    }
  };

  const shouldRunAdaptiveAction = (conceptId, actionType) => {
    if (!conceptId || !actionType) return false;
    const key = String(conceptId);
    const entry = adaptiveInterventionRef.current[key];
    if (!entry) return true;
    if (entry.action !== actionType) return true;
    const elapsed = Date.now() - entry.at;
    return elapsed > 10 * 60 * 1000;
  };

  const markAdaptiveAction = (conceptId, actionType) => {
    if (!conceptId || !actionType) return;
    adaptiveInterventionRef.current[String(conceptId)] = { action: actionType, at: Date.now() };
  };

  const requestMistakeExplanation = async ({
    question,
    studentAnswer,
    idealAnswer,
    conceptLabel,
    recommendedTopicTitle,
    graphRemediation,
  }, { useBusy = true } = {}) => {
    if (useBusy) setIsBusy(true);
    setStreamPhase('Explaining the miss...');
    try {
      const out = await postJson('/tutor/explain-mistake', {
        student_id: activeId,
        session_id: sessionId,
        subject: currentSubject,
        sss_level: currentLevel,
        term: currentTerm,
        topic_id: topicId,
        question,
        student_answer: studentAnswer,
        correct_answer: idealAnswer,
      });
      appendAssistant({
        assistant_message: out.explanation,
        key_points: [
          conceptLabel ? `Focus concept: ${conceptLabel}` : null,
          out.improvement_tip,
        ].filter(Boolean),
        prerequisite_warning: graphRemediation?.blocking_prerequisite_label
          ? `Fix ${graphRemediation.blocking_prerequisite_label} before retrying this concept.`
          : null,
        next_action: recommendedTopicTitle
          ? `Revise ${recommendedTopicTitle}, then retry this checkpoint.`
          : 'Retry the checkpoint after revising the core rule and one worked example.',
      });
    } catch (err) {
      appendAssistant({ assistant_message: err.message || 'Mistake explanation unavailable.' });
    } finally {
      setStreamPhase('');
      if (useBusy) setIsBusy(false);
    }
  };

  const explainLastMistake = async () => {
    if (!lastAssessmentReview || lastAssessmentReview.is_correct || isBusy) return;
    await requestMistakeExplanation({
      question: lastAssessmentReview.question,
      studentAnswer: lastAssessmentReview.studentAnswer,
      idealAnswer: lastAssessmentReview.idealAnswer,
      conceptLabel: lastAssessmentReview.conceptLabel,
      recommendedTopicTitle: lastAssessmentReview.recommendedTopicTitle,
      graphRemediation: lastAssessmentReview.graphRemediation,
    });
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
      appendAssistant({ assistant_message: err.message || 'Drill unavailable.' });
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
      appendAssistant({ assistant_message: err.message || 'Study plan unavailable.' });
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
      const adaptiveConceptId = out.concept_id || pendingAssessment.concept_id;
      if (out.adaptive_action && shouldRunAdaptiveAction(adaptiveConceptId, out.adaptive_action)) {
        markAdaptiveAction(adaptiveConceptId, out.adaptive_action);
        setPendingAdaptiveAction({
          type: out.adaptive_action,
          conceptId: adaptiveConceptId,
          conceptLabel: out.concept_label,
          blockingLabel: out.graph_remediation?.blocking_prerequisite_label || null,
          reason: out.adaptive_reason || null,
          difficulty: out.adaptive_difficulty || null,
        });
      }
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
      if (!out.is_correct) {
        await requestMistakeExplanation({
          question: submittedQuestion,
          studentAnswer: submittedAnswer,
          idealAnswer: out.ideal_answer,
          conceptLabel: out.concept_label,
          recommendedTopicTitle,
          graphRemediation: out.graph_remediation || null,
        }, { useBusy: false });
      }
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
      await refreshCockpit({ silent: true });
    } catch (err) {
      appendAssistant({ assistant_message: err.message || 'Failed to submit checkpoint.' });
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
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => navigate(`/graph-path?subject=${encodeURIComponent(currentSubject)}`)}
                className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-700 hover:bg-slate-100"
              >
                <GitBranch size={16} />
                Graph view
              </button>
              <button
                type="button"
                onClick={() => navigate(`/graph-briefing?subject=${encodeURIComponent(currentSubject)}`)}
                className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-700 hover:bg-slate-100"
              >
                Briefing
              </button>
              <button type="button" onClick={() => navigate(`/quiz/${topicId}`)} className="inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-4 py-2 text-sm font-bold text-white hover:bg-indigo-700">
                Take quiz
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>

          <div className="grid gap-8 p-4 md:p-8 xl:grid-cols-[minmax(0,1.35fr)_minmax(380px,1fr)]">
          <div className="xl:col-span-2">
            <PresentationCueCard
              stepId="lesson"
              nextClickLabel="Graph view"
              speakerNotes={[
                'This is the graph-first lesson cockpit, not a static lesson page with a chatbot attached.',
                `Use ${lesson?.title ? `"${lesson.title}"` : 'the lesson'} to show how the graph recommendation flows into content, tutor actions, and checkpointing.`,
                'Click "Graph view" next to reconnect this lesson to the wider concept map, then point out Check understanding or Take quiz.',
              ]}
            />
          </div>
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
                <span className="truncate text-slate-700">{lesson?.title || 'Lesson unavailable'}</span>
              </div>

              <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
                <div>
                  <h1 className="text-3xl font-black tracking-tight text-slate-950 md:text-4xl">{lesson?.title || 'Lesson unavailable'}</h1>
                  <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-600 md:text-base">
                    {lesson?.summary || (lessonAvailable ? '' : 'Lesson summary is unavailable for this topic right now.')}
                  </p>
                  <div className="mt-6 flex flex-wrap gap-3">
                    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs shadow-sm">
                      <p className="font-black uppercase tracking-[0.2em] text-slate-400">Lesson Focus</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">
                        {graphAvailable
                          ? (graphContext?.weakest_concepts?.[0]?.label || 'Graph context warming up')
                          : 'Graph context unavailable'}
                      </p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs shadow-sm">
                      <p className="font-black uppercase tracking-[0.2em] text-slate-400">Mastery Pulse</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">
                        {graphAvailable ? (masteryPulse !== null ? `${masteryPulse}% ready` : 'Unassessed') : 'Unavailable'}
                      </p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs shadow-sm">
                      <p className="font-black uppercase tracking-[0.2em] text-slate-400">Next Unlock</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">
                        {graphAvailable
                          ? (bootstrap?.next_unlock?.topic_title || 'No unlock yet')
                          : 'Graph context unavailable'}
                      </p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs shadow-sm">
                      <p className="font-black uppercase tracking-[0.2em] text-slate-400">Context warmed</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">
                        {graphAvailable
                          ? `${topicWarmSummary.currentCount} live / ${topicWarmSummary.prereqCount} prereq / ${topicWarmSummary.downstreamCount} unlock`
                          : 'Graph context unavailable'}
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
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Assessment status</p>
                      <p className={`mt-1 text-sm font-semibold ${
                        assessmentStatus.tone === 'emerald'
                          ? 'text-emerald-700'
                          : assessmentStatus.tone === 'amber'
                            ? 'text-amber-700'
                            : assessmentStatus.tone === 'indigo'
                              ? 'text-indigo-700'
                              : 'text-slate-700'
                      }`}>{assessmentStatus.label}</p>
                      <p className="mt-1 text-xs leading-5 text-slate-500">{assessmentStatus.detail}</p>
                    </div>
                    <div className="rounded-2xl bg-white p-4">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Weak prerequisite</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">
                        {graphAvailable
                          ? (graphContext?.prerequisite_concepts?.[0]?.label || 'No blocking prerequisite detected')
                          : 'Graph context unavailable'}
                      </p>
                    </div>
                    {evidenceSummary && (
                      <div className="rounded-2xl bg-white p-4">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Evidence breakdown</p>
                        <div className="mt-2 grid gap-2 text-xs font-semibold text-slate-600">
                          <div className="flex items-center justify-between">
                            <span>Demonstrated</span>
                            <span className="text-emerald-700">{evidenceSummary.demonstrated}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Needs review</span>
                            <span className="text-amber-700">{evidenceSummary.needs_review}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Unassessed</span>
                            <span className="text-slate-500">{evidenceSummary.unassessed}</span>
                          </div>
                        </div>
                      </div>
                    )}
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
                    {!graphAvailable && (
                      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-700">Graph context unavailable</p>
                        <p className="mt-2 text-xs leading-6 text-amber-800">
                          {graphUnavailableReason || 'No approved concept mappings found for this topic yet.'}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
              <div className="grid gap-8 p-6 md:p-8">
                {(whyStory || evidenceSummary || recentEvidence || lastAssessmentReview) && (
                  <div className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(260px,0.9fr)]">
                    <div className="rounded-[1.5rem] border border-indigo-200 bg-indigo-50 p-5">
                      <div className="flex items-center gap-2 text-indigo-700">
                        <Route size={16} />
                        <p className="text-[10px] font-black uppercase tracking-[0.2em]">Why this matters</p>
                      </div>
                      <p className="mt-3 text-sm leading-7 text-slate-700">
                        {whyStory || (graphUnavailableReason || 'Graph context is warming up for this topic.')}
                      </p>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {safeArray(whyTopicDetail?.prerequisite_labels).slice(0, 3).map((label) => (
                          <span key={label} className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-[11px] font-bold text-amber-800">
                            Builds from {label}
                          </span>
                        ))}
                        {safeArray(whyTopicDetail?.unlock_labels).slice(0, 2).map((label) => (
                          <span key={label} className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[11px] font-bold text-emerald-800">
                            Unlocks {label}
                          </span>
                        ))}
                        {whyTopicDetail?.recommended_next?.topic_title && (
                          <span className="rounded-full border border-indigo-200 bg-white px-3 py-1 text-[11px] font-bold text-indigo-700">
                            Then {whyTopicDetail.recommended_next.topic_title}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5">
                      <div className="flex items-center gap-2 text-slate-700">
                        <BrainCircuit size={16} />
                        <p className="text-[10px] font-black uppercase tracking-[0.2em]">Mastery evidence</p>
                      </div>
                      <p className="mt-2 text-xs leading-5 text-slate-500">
                        Mastery only updates from checkpoints and quizzes.
                      </p>
                      {evidenceSummary ? (
                        <div className="mt-3 grid gap-2 text-xs font-semibold text-slate-600">
                          <div className="flex items-center justify-between">
                            <span>Demonstrated</span>
                            <span className="text-emerald-700">{evidenceSummary.demonstrated}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Needs review</span>
                            <span className="text-amber-700">{evidenceSummary.needs_review}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Unassessed</span>
                            <span className="text-slate-500">{evidenceSummary.unassessed}</span>
                          </div>
                          <div className="flex items-center justify-between text-[11px] text-slate-500">
                            <span>Total concepts</span>
                            <span>{evidenceTotal}</span>
                          </div>
                        </div>
                      ) : (
                        <p className="mt-3 text-xs text-slate-500">No mastery evidence recorded yet.</p>
                      )}
                      {lastAssessmentReview && (
                        <div className="mt-3 rounded-2xl border border-slate-100 bg-slate-50 px-3 py-2 text-xs text-slate-600">
                          <p className="font-semibold text-slate-700">
                            Latest checkpoint: {lastAssessmentReview.conceptLabel}
                          </p>
                          <p className="mt-1">
                            {lastAssessmentReview.isCorrect ? 'Correct' : 'Needs review'} · {Math.round((lastAssessmentReview.score || 0) * 100)}%
                          </p>
                        </div>
                      )}
                      {recentEvidence && (
                        <div className="mt-3 rounded-2xl border border-indigo-100 bg-indigo-50 px-3 py-2 text-xs text-indigo-700">
                          <p className="font-semibold">Latest evidence</p>
                          <p className="mt-1">{recentEvidence.summary}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                {!lessonAvailable && (
                  <div className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-800">
                    Lesson content is unavailable for this topic right now. Please refresh after curriculum ingestion completes.
                  </div>
                )}
              {lessonAvailable && lessonBlocks.map((block, index) => (
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
              className="space-y-6 xl:sticky xl:top-6 self-start"
            >
              <section className="rounded-[2rem] border border-indigo-200 bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.18),_transparent_45%),linear-gradient(135deg,#ffffff,_#eef2ff)] p-5 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-500">Graph Rail Pulse</p>
                    <p className="mt-2 text-sm font-semibold text-slate-800">
                      {graphPulse.currentLabel || (graphAvailable ? 'Current concept focus' : 'Graph context unavailable')}
                    </p>
                  </div>
                  <div className="rounded-full border border-indigo-200 bg-white px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-indigo-700">
                    {graphPulse.readiness}
                  </div>
                </div>
                <div className="mt-4 grid gap-3">
                  <div className="rounded-2xl border border-white bg-white/80 px-4 py-3 text-xs text-slate-700">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Weak prerequisite</p>
                    <p className="mt-1 font-semibold">{graphPulse.weakPrereqLabel || 'No blocking prerequisite detected'}</p>
                  </div>
                  <div className="rounded-2xl border border-white bg-white/80 px-4 py-3 text-xs text-slate-700">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Next unlock</p>
                    <p className="mt-1 font-semibold">{graphPulse.nextUnlockLabel || 'Stay on this concept cluster'}</p>
                  </div>
                  <div className="rounded-2xl border border-white bg-white/80 px-4 py-3 text-xs text-slate-600">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Graph coverage</p>
                    <p className="mt-1 font-semibold">
                      {graphAvailable
                        ? `${topicWarmSummary.currentCount} current · ${topicWarmSummary.prereqCount} prereq · ${topicWarmSummary.downstreamCount} unlock`
                        : (graphUnavailableReason || 'Awaiting graph mapping')}
                    </p>
                  </div>
                </div>
              </section>

              <LessonKnowledgeGraph
                graphContext={graphContext}
                nextUnlock={bootstrap?.next_unlock}
                whyTopicDetail={whyTopicDetail}
                onOpenTopic={openRecommendedLesson}
                onExplainConcept={handleGraphExplain}
                onBridgeConcept={handleGraphBridge}
                onDrillConcept={handleGraphDrill}
                onSelectConcept={setSelectedGraphConcept}
              />

            <section className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <BrainCircuit className="text-indigo-600" size={18} />
                <h2 className="text-sm font-black uppercase tracking-[0.2em] text-slate-600">Mastery Overlay</h2>
              </div>
              <div className="grid gap-3">
                {safeArray(graphContext?.current_concepts).map((concept) => <ConceptChip key={concept.concept_id} concept={concept} />)}
                {!safeArray(graphContext?.current_concepts).length && (
                  <p className={`rounded-2xl px-3 py-3 text-xs ${graphAvailable ? 'bg-slate-50 text-slate-500' : 'border border-amber-200 bg-amber-50 text-amber-700'}`}>
                    {graphAvailable
                      ? 'Graph context is still warming for this topic.'
                      : (graphUnavailableReason || 'Graph context is unavailable for this topic yet.')}
                  </p>
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
                  <button type="button" onClick={() => sendChat('Teach me like I am completely new to this lesson.', { mode: 'teach' })} className="hidden rounded-2xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 md:inline-flex">
                    Teach from zero
                  </button>
                </div>
              </div>
              <div className="p-5">
                <div className="mb-4 rounded-[1.25rem] border border-slate-200 bg-slate-50 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Tutor mode</p>
                      <p className="mt-1 text-xs leading-6 text-slate-600">{activeMode.description}</p>
                    </div>
                    <span className="rounded-full border border-indigo-200 bg-white px-3 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-indigo-700">
                      {activeMode.label}
                    </span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {TUTOR_MODES.map((mode) => (
                      <button
                        key={mode.id}
                        type="button"
                        onClick={() => setSelectedMode(mode.id)}
                        className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold transition ${
                          selectedMode === mode.id
                            ? 'border-indigo-600 bg-indigo-600 text-white'
                            : 'border-slate-200 bg-white text-slate-600 hover:border-indigo-300 hover:text-indigo-700'
                        }`}
                      >
                        {mode.label}
                      </button>
                    ))}
                  </div>
                  <div className="mt-4 flex flex-wrap items-center gap-3">
                    <button
                      type="button"
                      onClick={runModeAction}
                      disabled={isBusy}
                      className="inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-white hover:bg-indigo-700 disabled:opacity-60"
                    >
                      Run {activeMode.label} flow
                      <ArrowRight size={14} />
                    </button>
                    <p className="text-xs leading-5 text-slate-500">
                      {MODE_DEFAULT_PROMPTS[activeMode.id]}
                    </p>
                  </div>
                </div>
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
                {assessmentRecommendation && (
                  <div className={`mb-4 rounded-[1.5rem] border p-4 ${
                    assessmentRecommendation.tone === 'amber'
                      ? 'border-amber-200 bg-amber-50'
                      : assessmentRecommendation.tone === 'rose'
                        ? 'border-rose-200 bg-rose-50'
                        : assessmentRecommendation.tone === 'emerald'
                          ? 'border-emerald-200 bg-emerald-50'
                          : 'border-indigo-200 bg-indigo-50'
                  }`}>
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Next best action</p>
                    <p className="mt-2 text-sm font-semibold text-slate-800">{assessmentRecommendation.headline}</p>
                    <p className="mt-2 text-xs leading-6 text-slate-600">{assessmentRecommendation.detail}</p>
                    <button
                      type="button"
                      onClick={handleAssessmentRecommendation}
                      disabled={isBusy}
                      className="mt-3 inline-flex items-center gap-2 rounded-2xl bg-slate-900 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-white disabled:opacity-60"
                    >
                      {assessmentRecommendation.actionLabel}
                      <ArrowRight size={14} />
                    </button>
                  </div>
                )}
                <div ref={scrollRef} className="max-h-[480px] space-y-4 overflow-y-auto rounded-[1.5rem] bg-slate-50 p-4">
                  {messages.map((item, index) => (
                    <MessageCard
                      key={item.id || `${item.role}-${index}`}
                      item={item}
                      onOpenRecommendation={openRecommendedLesson}
                      onStartCheckpoint={() => startAssessment()}
                      onOpenPrereqBridge={handlePrereqBridge}
                      onStartDrill={handleDrill}
                      followUps={FOLLOW_UP_ACTIONS}
                      onFollowUp={handleFollowUp}
                      showFollowUps={index === lastAssistantIndex}
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
                        <button type="button" onClick={() => sendChat('Explain this lesson with one real-life example.', { mode: 'teach' })} className="rounded-full bg-slate-100 px-3 py-1.5 font-semibold text-slate-600">Real-life example</button>
                        <button type="button" onClick={() => sendChat('Show me the common mistake students make here.', { mode: 'diagnose' })} className="rounded-full bg-slate-100 px-3 py-1.5 font-semibold text-slate-600">Common mistake</button>
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
