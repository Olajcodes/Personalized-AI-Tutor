import React from 'react';
import { ArrowRight, BookOpen, GitBranch, PlayCircle, ShieldAlert, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { useUser } from '../context/UserContext';

const HeroSection = ({
  enrolledSubjects,
  activeSubject,
  onSelectSubject,
  hasStartedLearning,
  graphSignal = null,
  signalSubject = null,
  onResumeSignal = null,
}) => {
  const { userData } = useUser();
  const firstName = userData?.first_name || 'Student';
  const navigate = useNavigate();

  const handleStartLearning = () => {
    if (activeSubject) {
      navigate(`/course/${activeSubject}`);
    }
  };

  const signalPayload = graphSignal?.payload || graphSignal || null;
  const signalAnalytics = signalPayload?.analytics || null;
  const signalNextStep = signalPayload?.next_step || null;
  const signalRecommendation = signalPayload?.recommendation_story || null;

  return (
    <div className="relative flex-1 overflow-hidden rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <div className="pointer-events-none absolute right-0 top-0 -mr-8 -mt-8 h-64 w-64 rounded-full bg-indigo-50 opacity-50 blur-3xl" />

      <div className="relative z-10">
        <h1 className="mb-2 text-3xl font-black tracking-tight text-slate-900">
          Welcome back, {firstName}.
        </h1>

        {signalPayload && (
          <div className="mb-5 rounded-2xl border border-indigo-200 bg-indigo-50/70 p-4">
            <div className="flex flex-wrap items-center gap-2 text-[10px] font-black uppercase tracking-[0.18em] text-indigo-700">
              <GitBranch className="h-3.5 w-3.5" />
              Live graph signal
              {(signalAnalytics?.source_label || signalPayload?.intervention_timeline?.[0]?.source_label) && (
                <span className="rounded-full bg-white px-2 py-1 text-[10px] text-indigo-600">
                  {signalAnalytics?.source_label || signalPayload?.intervention_timeline?.[0]?.source_label}
                </span>
              )}
            </div>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <div className="rounded-2xl bg-white p-3">
                <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">Focus now</p>
                <p className="mt-1 text-sm font-bold text-slate-800">
                  {signalAnalytics?.focus_concept
                    || signalPayload?.intervention_timeline?.[0]?.focus_concept_label
                    || signalNextStep?.recommended_concept_label
                    || signalNextStep?.recommended_topic_title
                    || 'Current lesson focus'}
                </p>
              </div>
              <div className="rounded-2xl bg-white p-3">
                <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">Blocking prerequisite</p>
                <p className="mt-1 text-sm font-bold text-slate-800">
                  {signalAnalytics?.blocking_prerequisite
                    || signalRecommendation?.blocking_prerequisite_label
                    || signalNextStep?.prereq_gap_labels?.[0]
                    || 'No active block detected'}
                </p>
              </div>
              <div className="rounded-2xl bg-white p-3">
                <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">Next move</p>
                <p className="mt-1 text-sm font-bold text-slate-800">
                  {signalRecommendation?.action_label
                    || signalAnalytics?.outcome
                    || signalPayload?.intervention_timeline?.[0]?.action_label
                    || 'Resume graph recommendation'}
                </p>
              </div>
            </div>
            {typeof onResumeSignal === 'function' && signalNextStep?.recommended_topic_id && (
              <button
                type="button"
                onClick={onResumeSignal}
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-indigo-700"
              >
                <Sparkles className="h-4 w-4" />
                Open recommended lesson
              </button>
            )}
          </div>
        )}

        {!activeSubject ? (
          <>
            <p className="mb-6 text-slate-500">
              You are enrolled in {enrolledSubjects?.length || 0} subjects. Which one would you like to focus on today?
            </p>
            <div className="flex flex-wrap gap-4">
              {enrolledSubjects && enrolledSubjects.length > 0 ? (
                enrolledSubjects.map((sub) => (
                  <button
                    key={sub}
                    onClick={() => onSelectSubject(sub)}
                    className="group flex cursor-pointer items-center gap-3 rounded-2xl border-2 border-slate-100 bg-white px-6 py-4 font-bold text-slate-700 transition-all hover:-translate-y-1 hover:border-indigo-600 hover:text-indigo-700 hover:shadow-lg"
                  >
                    <div className="rounded-lg bg-indigo-50 p-2 transition-colors group-hover:bg-indigo-100">
                      <BookOpen className="h-5 w-5 text-indigo-600" />
                    </div>
                    <span className="capitalize">{sub}</span>
                    <ArrowRight className="ml-2 h-4 w-4 text-indigo-500 opacity-0 transition-opacity group-hover:opacity-100" />
                  </button>
                ))
              ) : (
                <p className="text-sm font-bold text-rose-500">No subjects found. Please update your class settings.</p>
              )}
            </div>
          </>
        ) : (
          <>
            <p className="mb-6 text-slate-500">
              Ready to dive into <strong className="capitalize text-indigo-600">{activeSubject}</strong>?
            </p>
            {signalPayload && (
              <div className="mb-5 flex flex-wrap gap-3">
                <div className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-2 text-xs font-bold text-slate-700 shadow-sm">
                  <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
                  {signalAnalytics?.source_label || signalPayload?.intervention_timeline?.[0]?.source_label || 'Latest evidence'}
                </div>
                {(signalAnalytics?.focus_concept || signalPayload?.intervention_timeline?.[0]?.focus_concept_label) && (
                  <div className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-2 text-xs font-bold text-slate-700 shadow-sm">
                    <BookOpen className="h-3.5 w-3.5 text-cyan-500" />
                    {signalAnalytics?.focus_concept || signalPayload?.intervention_timeline?.[0]?.focus_concept_label}
                  </div>
                )}
                {(signalAnalytics?.blocking_prerequisite || signalRecommendation?.blocking_prerequisite_label) && (
                  <div className="inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-2 text-xs font-bold text-amber-800 shadow-sm">
                    <ShieldAlert className="h-3.5 w-3.5 text-amber-500" />
                    {signalAnalytics?.blocking_prerequisite || signalRecommendation?.blocking_prerequisite_label}
                  </div>
                )}
              </div>
            )}
            <div className="flex items-center gap-4">
              <button
                onClick={handleStartLearning}
                className="flex cursor-pointer items-center gap-2 rounded-xl bg-indigo-600 px-8 py-3.5 font-bold text-white shadow-lg shadow-indigo-200 transition-all hover:scale-105 hover:bg-indigo-700 active:scale-95"
              >
                <PlayCircle className="h-5 w-5" />
                {signalNextStep?.recommended_topic_id ? `Continue ${signalSubject || activeSubject || 'learning'}` : hasStartedLearning ? 'Resume Learning' : 'Start First Lesson'}
              </button>
              <button
                onClick={() => onSelectSubject(null)}
                className="cursor-pointer rounded-lg border border-transparent bg-transparent px-4 py-2 text-sm font-semibold text-slate-400 transition-colors hover:border-indigo-100 hover:bg-indigo-50 hover:text-indigo-600"
              >
                Switch Subject
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default HeroSection;
