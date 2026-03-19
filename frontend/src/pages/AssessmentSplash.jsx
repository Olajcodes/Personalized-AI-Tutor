import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  ClipboardList,
  Loader2,
  PlayCircle,
  Sparkles,
  Target,
} from 'lucide-react';

import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';
import {
  fetchDiagnosticStatus,
  startDiagnosticSession,
  submitDiagnosticSession,
} from '../services/api';

const SUBJECT_LABELS = {
  math: 'Mathematics',
  english: 'English Studies',
  civic: 'Civic Education',
};

const RUN_STATUS_STYLES = {
  pending: 'border-slate-200 bg-white text-slate-700',
  in_progress: 'border-amber-200 bg-amber-50 text-amber-800',
  completed: 'border-emerald-200 bg-emerald-50 text-emerald-800',
};

const RUN_STATUS_LABELS = {
  pending: 'Pending',
  in_progress: 'Resume',
  completed: 'Completed',
};

const storageKeyForDiagnostic = (diagnosticId) => `mastery_onboarding_diagnostic_${diagnosticId}`;

const readPersistedSession = (diagnosticId) => {
  if (!diagnosticId) return null;
  try {
    const raw = window.localStorage.getItem(storageKeyForDiagnostic(diagnosticId));
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return {
      answers: parsed?.answers && typeof parsed.answers === 'object' ? parsed.answers : {},
      currentIndex: Number.isFinite(Number(parsed?.currentIndex)) ? Number(parsed.currentIndex) : 0,
    };
  } catch (error) {
    console.warn('Failed to restore onboarding diagnostic progress:', error);
    return null;
  }
};

const persistSession = (diagnosticId, payload) => {
  if (!diagnosticId) return;
  window.localStorage.setItem(storageKeyForDiagnostic(diagnosticId), JSON.stringify(payload));
};

const clearPersistedSession = (diagnosticId) => {
  if (!diagnosticId) return;
  window.localStorage.removeItem(storageKeyForDiagnostic(diagnosticId));
};

const subjectLabel = (subject) => SUBJECT_LABELS[subject] || String(subject || '').toUpperCase();

const completionCount = (status, activeSession, answersById) => {
  const completedSubjects = Array.isArray(status?.completed_subjects) ? status.completed_subjects.length : 0;
  const activeAnswered = activeSession
    ? Math.min(
        Array.from(new Set(Object.keys(answersById || {}))).filter((questionId) =>
          activeSession.questions.some((question) => question.question_id === questionId),
        ).length,
        activeSession.questions.length,
      )
    : 0;
  return (completedSubjects * 10) + activeAnswered;
};

export default function AssessmentSplash() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const {
    studentData,
    userData,
    diagnosticStatus,
    refreshDiagnosticStatus,
    replaceLocalStudent,
  } = useUser();

  const activeId =
    studentData?.student_id ||
    studentData?.user_id ||
    userData?.user_id ||
    userData?.id ||
    window.localStorage.getItem('mastery_student_id');
  const level = studentData?.sss_level || 'SSS1';
  const term = Number(studentData?.current_term || 1);
  const selectedSubjects = useMemo(
    () => (Array.isArray(studentData?.subjects) ? studentData.subjects : []).filter(Boolean),
    [studentData?.subjects],
  );

  const [status, setStatus] = useState(diagnosticStatus);
  const [statusError, setStatusError] = useState('');
  const [isLoadingStatus, setIsLoadingStatus] = useState(true);
  const [activeSession, setActiveSession] = useState(null);
  const [answersById, setAnswersById] = useState({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [isLaunching, setIsLaunching] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [launchError, setLaunchError] = useState('');
  const [latestSummary, setLatestSummary] = useState(null);

  const loadStatus = useCallback(async () => {
    if (!token || !activeId) {
      setStatus(null);
      setIsLoadingStatus(false);
      return null;
    }

    setIsLoadingStatus(true);
    setStatusError('');
    try {
      const nextStatus = await fetchDiagnosticStatus(token, activeId);
      setStatus(nextStatus);
      await refreshDiagnosticStatus(activeId);
      return nextStatus;
    } catch (error) {
      setStatusError(error.message || 'Unable to load onboarding diagnostic status.');
      return null;
    } finally {
      setIsLoadingStatus(false);
    }
  }, [activeId, refreshDiagnosticStatus, token]);

  useEffect(() => {
    setStatus(diagnosticStatus);
  }, [diagnosticStatus]);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  useEffect(() => {
    if (!activeSession) {
      setSelectedAnswer('');
      return;
    }
    const currentQuestion = activeSession.questions[currentIndex];
    setSelectedAnswer((currentQuestion && answersById[currentQuestion.question_id]) || '');
  }, [activeSession, answersById, currentIndex]);

  const hydrateSession = useCallback((session) => {
    const persisted = readPersistedSession(session?.diagnostic_id);
    const safeAnswers = persisted?.answers || {};
    const firstUnansweredIndex = session.questions.findIndex((question) => !safeAnswers[question.question_id]);
    const resolvedIndex =
      firstUnansweredIndex >= 0
        ? firstUnansweredIndex
        : Math.min(
            persisted?.currentIndex ?? session.questions.length - 1,
            Math.max(session.questions.length - 1, 0),
          );

    setActiveSession(session);
    setAnswersById(safeAnswers);
    setCurrentIndex(Math.max(resolvedIndex, 0));
  }, []);

  const launchSubjectDiagnostic = useCallback(
    async (subject) => {
      if (!token || !activeId || !subject) return;
      setIsLaunching(true);
      setLaunchError('');
      try {
        const session = await startDiagnosticSession(token, {
          student_id: activeId,
          subject,
          sss_level: level,
          term,
          num_questions: 10,
        });
        hydrateSession(session);
      } catch (error) {
        setLaunchError(error.message || 'Unable to start the onboarding diagnostic.');
      } finally {
        setIsLaunching(false);
      }
    },
    [activeId, hydrateSession, level, term, token],
  );

  const currentQuestion = activeSession?.questions?.[currentIndex] || null;
  const overallProgress = selectedSubjects.length
    ? Math.round((completionCount(status, activeSession, answersById) / (selectedSubjects.length * 10)) * 100)
    : 0;

  const handlePersistAndMove = (answerValue, direction = 'next') => {
    if (!activeSession || !currentQuestion) return;
    const nextAnswers = {
      ...answersById,
      [currentQuestion.question_id]: answerValue,
    };
    setAnswersById(nextAnswers);
    persistSession(activeSession.diagnostic_id, {
      answers: nextAnswers,
      currentIndex:
        direction === 'next'
          ? Math.min(currentIndex + 1, activeSession.questions.length - 1)
          : Math.max(currentIndex - 1, 0),
    });

    if (direction === 'next') {
      setCurrentIndex((prev) => Math.min(prev + 1, activeSession.questions.length - 1));
    } else {
      setCurrentIndex((prev) => Math.max(prev - 1, 0));
    }
  };

  const handleSubmitSubject = async (overrideAnswers = null) => {
    if (!token || !activeId || !activeSession) return;

    const finalAnswers = { ...answersById, ...(overrideAnswers || {}) };
    if (currentQuestion && selectedAnswer) {
      finalAnswers[currentQuestion.question_id] = selectedAnswer;
    }

    const payloadAnswers = activeSession.questions.map((question) => ({
      question_id: question.question_id,
      answer: finalAnswers[question.question_id] || 'SKIPPED',
    }));

    setIsSubmitting(true);
    setLaunchError('');

    try {
      const result = await submitDiagnosticSession(token, {
        diagnostic_id: activeSession.diagnostic_id,
        student_id: activeId,
        answers: payloadAnswers,
      });

      clearPersistedSession(activeSession.diagnostic_id);
      setLatestSummary({
        subject: activeSession.subject,
        result,
      });
      setActiveSession(null);
      setAnswersById({});
      setCurrentIndex(0);
      setSelectedAnswer('');

      const nextStatus = await loadStatus();
      if (nextStatus?.onboarding_complete) {
        replaceLocalStudent({
          ...(studentData || {}),
          has_profile: true,
        });
        return;
      }

      const nextRun = (nextStatus?.subject_runs || []).find((run) => run.status !== 'completed');
      if (nextRun?.subject) {
        await launchSubjectDiagnostic(nextRun.subject);
      }
    } catch (error) {
      setLaunchError(error.message || 'Unable to submit this diagnostic run.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const nextRun = useMemo(
    () => (status?.subject_runs || []).find((run) => run.status !== 'completed') || null,
    [status],
  );

  if (isLoadingStatus) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
        <div className="rounded-[2rem] border border-slate-200 bg-white px-8 py-10 text-center shadow-sm">
          <Loader2 className="mx-auto h-9 w-9 animate-spin text-indigo-600" />
          <p className="mt-4 text-sm font-semibold text-slate-600">Loading your onboarding diagnostic...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.12),_transparent_35%),linear-gradient(180deg,#f8fafc_0%,#eef2ff_100%)] px-6 py-8">
      <main className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-indigo-700">
              <BrainCircuit className="h-3.5 w-3.5" />
              Mandatory onboarding diagnostic
            </div>
            <h1 className="mt-4 text-4xl font-black tracking-tight text-slate-900">Let’s map your real starting point</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
              We’ll run 10 graph-grounded questions for each subject you selected. The results become your first mastery baseline, your blocking prerequisite repair plan, and your opening lesson route.
            </p>
          </div>
          <div className="rounded-[2rem] border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Overall progress</p>
            <p className="mt-2 text-3xl font-black text-slate-900">{overallProgress}%</p>
            <p className="mt-1 text-xs font-semibold text-slate-500">
              {status?.completed_subjects?.length || 0} of {selectedSubjects.length || 0} subjects completed
            </p>
          </div>
        </div>

        {(statusError || launchError) && (
          <div className="mb-6 rounded-3xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm font-semibold text-rose-700">
            {statusError || launchError}
          </div>
        )}

        {latestSummary && (
          <div className="mb-6 rounded-[2rem] border border-emerald-200 bg-emerald-50 px-6 py-5 shadow-sm">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-emerald-700" />
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.18em] text-emerald-700">
                  {subjectLabel(latestSummary.subject)} diagnostic submitted
                </p>
                <p className="mt-1 text-sm leading-6 text-emerald-900">
                  {latestSummary.result?.learning_gap_summary?.rationale || 'Your baseline mastery profile has been updated.'}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.3fr]">
          <section className="space-y-6">
            <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2">
                <ClipboardList className="h-4 w-4 text-indigo-600" />
                <p className="text-[10px] font-black uppercase tracking-[0.18em] text-indigo-600">Subject queue</p>
              </div>
              <div className="mt-4 space-y-3">
                {(status?.subject_runs || []).map((run) => (
                  <div
                    key={run.subject}
                    className={`rounded-3xl border px-4 py-4 ${RUN_STATUS_STYLES[run.status] || RUN_STATUS_STYLES.pending}`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-black text-slate-900">{subjectLabel(run.subject)}</p>
                        <p className="mt-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                          {RUN_STATUS_LABELS[run.status]} · {run.question_count || 10} questions
                        </p>
                      </div>
                      {run.status !== 'completed' && (
                        <button
                          type="button"
                          onClick={() => launchSubjectDiagnostic(run.subject)}
                          disabled={isLaunching || isSubmitting}
                          className="rounded-2xl bg-slate-900 px-3 py-2 text-xs font-black text-white hover:bg-slate-800 disabled:opacity-60"
                        >
                          {run.status === 'in_progress' ? 'Resume' : 'Start'}
                        </button>
                      )}
                    </div>
                    {run.recommended_start_topic_title && (
                      <p className="mt-3 text-xs leading-6 text-slate-600">
                        Recommended start: <span className="font-bold text-slate-800">{run.recommended_start_topic_title}</span>
                      </p>
                    )}
                    {run.blocking_prerequisite_label && (
                      <p className="mt-2 text-xs leading-6 text-amber-800">
                        Blocking prerequisite: <span className="font-bold">{run.blocking_prerequisite_label}</span>
                      </p>
                    )}
                    {Array.isArray(run.weakest_concepts) && run.weakest_concepts.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {run.weakest_concepts.slice(0, 3).map((concept) => (
                          <span
                            key={`${run.subject}-${concept.concept_id}`}
                            className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-slate-600"
                          >
                            {concept.concept_label}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-emerald-600" />
                <p className="text-[10px] font-black uppercase tracking-[0.18em] text-emerald-600">Why this matters</p>
              </div>
              <ul className="mt-4 space-y-3 text-sm leading-7 text-slate-600">
                <li>Every answer writes baseline mastery evidence into your graph profile.</li>
                <li>Weak prerequisite concepts become the first repair targets in your lesson path.</li>
                <li>The dashboard and course recommendation after onboarding are built from this result.</li>
              </ul>
            </div>
          </section>

          <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
            {!activeSession ? (
              status?.onboarding_complete ? (
                <div className="flex min-h-[28rem] flex-col items-center justify-center text-center">
                  <CheckCircle2 className="h-12 w-12 text-emerald-600" />
                  <h2 className="mt-4 text-3xl font-black text-slate-900">Diagnostic complete</h2>
                  <p className="mt-3 max-w-xl text-sm leading-7 text-slate-600">
                    Your baseline graph profile is ready. We’ve stored your weakest concepts, blocking prerequisites, and recommended lesson starts for each subject.
                  </p>
                  <button
                    type="button"
                    onClick={() => navigate('/dashboard')}
                    className="mt-6 inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-5 py-3 text-sm font-black text-white hover:bg-indigo-700"
                  >
                    Open dashboard
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <div className="flex min-h-[28rem] flex-col justify-center">
                  <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-indigo-700">
                    <Sparkles className="h-3.5 w-3.5" />
                    Ready to begin
                  </div>
                  <h2 className="mt-4 text-3xl font-black text-slate-900">
                    {nextRun?.status === 'in_progress'
                      ? `Resume ${subjectLabel(nextRun.subject)} diagnostic`
                      : 'Start your subject diagnostics'}
                  </h2>
                  <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
                    We’ll guide you through {selectedSubjects.length * 10 || 10} total questions across your selected subjects. You can refresh and resume exactly where you left off.
                  </p>
                  <div className="mt-8 flex flex-wrap gap-3">
                    <button
                      type="button"
                      onClick={() => launchSubjectDiagnostic(nextRun?.subject || selectedSubjects[0])}
                      disabled={!nextRun?.subject || isLaunching}
                      className="inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-5 py-3 text-sm font-black text-white hover:bg-indigo-700 disabled:opacity-60"
                    >
                      {isLaunching ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
                      {nextRun?.status === 'in_progress' ? 'Resume diagnostic' : 'Start diagnostic'}
                    </button>
                    <button
                      type="button"
                      onClick={() => navigate('/learning-preferences')}
                      className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-700 hover:bg-slate-50"
                    >
                      <ArrowLeft className="h-4 w-4" />
                      Back to preferences
                    </button>
                  </div>
                </div>
              )
            ) : (
              <>
                <div className="flex flex-col gap-4 border-b border-slate-100 pb-5 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-indigo-700">
                      <BrainCircuit className="h-3.5 w-3.5" />
                      {subjectLabel(activeSession.subject)}
                    </div>
                    <h2 className="mt-3 text-2xl font-black text-slate-900">
                      Question {currentIndex + 1} of {activeSession.question_count}
                    </h2>
                    <p className="mt-2 text-sm leading-7 text-slate-600">
                      Each question is grounded in the approved curriculum mappings for {level} term {term}.
                    </p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                    <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Subject progress</p>
                    <p className="mt-1 text-lg font-black text-slate-900">
                      {Math.round(((currentIndex + 1) / activeSession.question_count) * 100)}%
                    </p>
                  </div>
                </div>

                <div className="mt-6">
                  <div className="rounded-3xl border border-slate-200 bg-slate-50 px-5 py-4">
                    <div className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
                      Concept focus
                    </div>
                    <p className="mt-2 text-sm font-bold text-slate-900">
                      {currentQuestion?.concept_label || 'Mapped concept'}
                    </p>
                    {currentQuestion?.topic_title && (
                      <p className="mt-1 text-xs text-slate-500">Topic: {currentQuestion.topic_title}</p>
                    )}
                  </div>

                  <h3 className="mt-6 text-2xl font-black leading-tight text-slate-900">{currentQuestion?.prompt}</h3>

                  <div className="mt-6 grid gap-4 md:grid-cols-2">
                    {(currentQuestion?.options || []).map((option, index) => {
                      const optionLetter = String.fromCharCode(65 + index);
                      const isSelected = selectedAnswer === optionLetter;
                      return (
                        <button
                          key={`${currentQuestion?.question_id}-${optionLetter}`}
                          type="button"
                          onClick={() => setSelectedAnswer(optionLetter)}
                          className={`rounded-3xl border px-5 py-5 text-left transition ${
                            isSelected
                              ? 'border-indigo-300 bg-indigo-50 text-indigo-900 shadow-sm'
                              : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                          }`}
                        >
                          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
                            Option {optionLetter}
                          </p>
                          <p className="mt-3 text-sm font-semibold leading-7">{option}</p>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="mt-8 flex flex-col gap-3 border-t border-slate-100 pt-5 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex flex-wrap gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        if (!activeSession) return;
                        const previousIndex = Math.max(currentIndex - 1, 0);
                        setCurrentIndex(previousIndex);
                        persistSession(activeSession.diagnostic_id, {
                          answers: answersById,
                          currentIndex: previousIndex,
                        });
                      }}
                      disabled={currentIndex === 0 || isSubmitting}
                      className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-black text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                    >
                      <ArrowLeft className="h-4 w-4" />
                      Back
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        const skipValue = 'SKIPPED';
                        if (currentIndex === activeSession.question_count - 1) {
                          setSelectedAnswer(skipValue);
                          setAnswersById((prev) => ({ ...prev, [currentQuestion.question_id]: skipValue }));
                          persistSession(activeSession.diagnostic_id, {
                            answers: { ...answersById, [currentQuestion.question_id]: skipValue },
                            currentIndex,
                          });
                          void handleSubmitSubject({ [currentQuestion.question_id]: skipValue });
                          return;
                        }
                        handlePersistAndMove(skipValue, 'next');
                      }}
                      disabled={isSubmitting}
                      className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-black text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                    >
                      Skip
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      if (!selectedAnswer) return;
                      if (currentIndex === activeSession.question_count - 1) {
                        void handleSubmitSubject();
                        return;
                      }
                      handlePersistAndMove(selectedAnswer, 'next');
                    }}
                    disabled={!selectedAnswer || isSubmitting}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl bg-indigo-600 px-5 py-3 text-sm font-black text-white hover:bg-indigo-700 disabled:opacity-60"
                  >
                    {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                    {currentIndex === activeSession.question_count - 1 ? 'Submit subject diagnostic' : 'Next question'}
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
