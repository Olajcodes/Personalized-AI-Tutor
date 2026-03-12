import { AlertTriangle, ArrowRight, Brain, CheckCircle2, GitBranch, Lock, PlayCircle, Sparkles } from 'lucide-react';

const safeArray = (value) => (Array.isArray(value) ? value : []);

const statusStyles = {
  mastered: 'border-emerald-300 bg-emerald-50 text-emerald-700',
  current: 'border-indigo-300 bg-indigo-50 text-indigo-700',
  ready: 'border-sky-300 bg-sky-50 text-sky-700',
  locked: 'border-slate-200 bg-slate-50 text-slate-500',
  unmapped: 'border-amber-300 bg-amber-50 text-amber-800',
};

const statusIcon = {
  mastered: CheckCircle2,
  current: Brain,
  ready: Sparkles,
  locked: Lock,
  unmapped: AlertTriangle,
};

function MapNode({ node, isLast, isRecommended, onSelectTopic }) {
  const Icon = statusIcon[node.status] || Brain;
  const style = statusStyles[node.status] || statusStyles.locked;
  const isInteractive = typeof onSelectTopic === 'function' && !['locked', 'unmapped'].includes(node.status);

  return (
    <div className="relative flex min-w-[210px] shrink-0 snap-center flex-col items-center">
      {!isLast && <div className="absolute left-1/2 top-6 h-1 w-full bg-gradient-to-r from-indigo-200 via-slate-200 to-slate-200" />}
      <div className={`relative z-10 flex h-12 w-12 items-center justify-center rounded-full border-4 bg-white ${node.status === 'current' ? 'border-indigo-600 text-indigo-600 shadow-[0_0_0_6px_rgba(99,102,241,0.12)]' : node.status === 'mastered' ? 'border-emerald-500 text-emerald-600' : node.status === 'ready' ? 'border-sky-500 text-sky-600' : node.status === 'unmapped' ? 'border-amber-400 text-amber-600' : 'border-slate-200 text-slate-400'}`}>
        <Icon className="h-5 w-5" />
      </div>
      <button
        type="button"
        onClick={() => {
          if (isInteractive) {
            onSelectTopic(node.topic_id);
          }
        }}
        disabled={!isInteractive}
        className={`mt-4 w-full rounded-2xl border px-4 py-4 text-left shadow-sm ${style} ${
          isInteractive ? 'cursor-pointer transition-transform duration-200 hover:-translate-y-1 hover:shadow-md' : 'cursor-default'
        } ${isRecommended ? 'ring-2 ring-indigo-200 ring-offset-2' : ''}`}
      >
        <div className="flex items-center justify-between gap-3">
          <h4 className="text-sm font-black leading-5">{node.title}</h4>
          <span className="rounded-full bg-white/70 px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em]">
            {node.status}
          </span>
        </div>
        <p className="mt-2 text-xs leading-6 opacity-90">{node.details || 'Graph state unavailable.'}</p>
        <div className="mt-3 flex items-center justify-between text-[11px] font-bold uppercase tracking-[0.16em]">
          <span>{node.concept_label || (node.status === 'unmapped' ? 'Mapping pending' : 'Concept')}</span>
          <span>{Math.round((node.mastery_score || 0) * 100)}%</span>
        </div>
        <div className="mt-4 flex items-center justify-between text-[11px] font-black uppercase tracking-[0.16em]">
          <span>{isRecommended ? 'Recommended now' : isInteractive ? 'Open lesson' : 'Graph only'}</span>
          {isInteractive ? <PlayCircle className="h-4 w-4" /> : <Lock className="h-4 w-4" />}
        </div>
      </button>
    </div>
  );
}

export default function LearningMap({ classLevel = 'SSS 2', subject = 'Mathematics', mapData = {}, onSelectTopic = null }) {
  const nodes = safeArray(mapData?.nodes);
  const edges = safeArray(mapData?.edges);
  const nextStep = mapData?.next_step || null;
  const relationCount = edges.length;
  const scopeWarning = nextStep?.scope_warning || null;
  const unmappedTopics = safeArray(nextStep?.unmapped_topic_titles);

  return (
    <div className="mb-8 rounded-3xl border border-gray-100 bg-white p-8 shadow-sm">
      <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-indigo-700">
            <GitBranch className="h-3.5 w-3.5" />
            Graph-first path
          </div>
          <h2 className="text-lg font-bold text-gray-900">Your Learning Map</h2>
          <p className="text-sm text-gray-500">{classLevel} {subject} · {relationCount} prerequisite links are currently shaping your next steps</p>
        </div>
        {nextStep && (
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-emerald-600">Next best node</div>
            <div className="mt-1 font-bold">{nextStep.recommended_topic_title || nextStep.recommended_concept_label || 'Continue current focus'}</div>
          </div>
        )}
      </div>

      <div className="mb-6 flex snap-x flex-nowrap gap-6 overflow-x-auto px-2 pb-8 pt-4 scroll-smooth custom-scrollbar">
        {nodes.map((node, index) => (
          <MapNode
            key={node.topic_id || node.concept_id || index}
            node={node}
            isLast={index === nodes.length - 1}
            isRecommended={Boolean(nextStep?.recommended_topic_id && nextStep.recommended_topic_id === node.topic_id)}
            onSelectTopic={onSelectTopic}
          />
        ))}
        {nodes.length === 0 && (
          <div className="w-full py-8 text-center text-sm text-gray-400">Learning map unavailable for this scope.</div>
        )}
      </div>

      {nextStep && (
        <div className="grid gap-4 rounded-3xl border border-slate-100 bg-slate-50 p-5 lg:grid-cols-[1fr_auto_1fr] lg:items-center">
          <div>
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Recommendation reason</div>
            <p className="mt-2 text-sm leading-7 text-slate-700">{nextStep.reason}</p>
            {nextStep.recommended_topic_id && typeof onSelectTopic === 'function' && (
              <button
                type="button"
                onClick={() => onSelectTopic(nextStep.recommended_topic_id)}
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-black uppercase tracking-[0.16em] text-white hover:bg-indigo-700"
              >
                Open graph recommendation <PlayCircle className="h-4 w-4" />
              </button>
            )}
          </div>
          <div className="flex items-center justify-center text-slate-300">
            <ArrowRight className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Blocking prerequisites</div>
            <p className="mt-2 text-sm leading-7 text-slate-700">
              {safeArray(nextStep.prereq_gap_labels).length ? nextStep.prereq_gap_labels.join(', ') : 'No blocking prerequisite gap detected.'}
            </p>
          </div>
        </div>
      )}

      {(scopeWarning || unmappedTopics.length > 0) && (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-900">
          <div className="text-[10px] font-black uppercase tracking-[0.18em] text-amber-700">Mapping status</div>
          <p className="mt-2 leading-6">
            {scopeWarning || 'Some topics are visible but are still waiting for curriculum concept mapping.'}
          </p>
          {unmappedTopics.length > 0 && (
            <p className="mt-2 text-xs font-semibold text-amber-800">
              Pending topics: {unmappedTopics.join(', ')}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
