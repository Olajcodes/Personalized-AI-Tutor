import React from 'react';
import { useNavigate } from 'react-router-dom';

const statusLabels = {
  current: 'CURRENT',
  ready: 'READY',
  mastered: 'MASTERED',
  locked: 'LOCKED',
  unmapped: 'UNMAPPED',
  pending: 'PENDING',
};

const badgeStyles = {
  current: 'bg-indigo-50 text-indigo-700 border-indigo-100',
  ready: 'bg-sky-50 text-sky-700 border-sky-100',
  mastered: 'bg-emerald-50 text-emerald-700 border-emerald-100',
  locked: 'bg-slate-100 text-slate-500 border-slate-200',
  unmapped: 'bg-amber-50 text-amber-700 border-amber-100',
  pending: 'bg-slate-100 text-slate-500 border-slate-200',
};

const CourseSidebar = ({ activeStep, subject = 'Subject', topics = [], level = 'Level' }) => {
  const navigate = useNavigate();

  const completedCount = topics.filter((topic) => topic.status === 'mastered').length;
  const totalCount = topics.length > 0 ? topics.length : 1;
  const progressPercent = Math.round((completedCount / totalCount) * 100);

  return (
    <div className="w-72 bg-white border-r border-slate-200 flex flex-col h-[calc(100vh-64px)] overflow-y-auto">
      <div className="p-6">
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-2 text-indigo-600 font-bold text-sm mb-8 hover:text-indigo-800 transition-colors"
        >
          <span>&larr;</span> Back to Dashboard
        </button>

        <div className="mb-8">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Current Syllabus</p>
          <h2 className="text-lg font-black text-slate-900 mb-2 capitalize">{level} {subject}</h2>
          <div className="flex justify-between items-center text-xs font-bold text-indigo-600 mb-2">
            <span>{progressPercent}% Complete</span>
            <span className="text-slate-400">{completedCount}/{topics.length} Units</span>
          </div>
          <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-indigo-600 rounded-full transition-all duration-1000" style={{ width: `${progressPercent}%` }}></div>
          </div>
        </div>

        <div>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">Modules</p>
          <div className="space-y-1">
            {topics.length > 0 ? (
              topics.map((topic, index) => {
                const targetId = topic.topic_id || topic.id;
                const currentStatus = topic.status || 'pending';
                const isLocked = currentStatus === 'locked';
                const isMastered = currentStatus === 'mastered';
                const isActive = activeStep === targetId || currentStatus === 'current';
                const badgeStyle = badgeStyles[currentStatus] || badgeStyles.pending;

                return (
                  <div
                    key={targetId || index}
                    onClick={() => {
                      if (!isLocked && targetId) navigate(`/lesson/${targetId}`);
                    }}
                    className={`flex items-start gap-3 p-3 rounded-xl transition-colors ${
                      isLocked ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'
                    } ${
                      isActive ? 'bg-indigo-50 border border-indigo-100/50' : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                      isMastered ? 'bg-emerald-100 text-emerald-600' :
                      isActive ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200' :
                      isLocked ? 'bg-slate-200 text-slate-500' :
                      'bg-slate-100 text-slate-400'
                    }`}>
                      {isMastered ? 'OK' :
                        isActive ? <span className="text-xs">&gt;</span> :
                        isLocked ? <span className="text-xs">L</span> :
                        <span className="text-xs">{index + 1}</span>}
                    </div>

                    <div className="min-w-0 flex-1">
                      <h4 className={`text-sm font-bold leading-tight ${
                        isActive ? 'text-indigo-900' :
                        isMastered ? 'text-slate-900' : 'text-slate-600'
                      }`}>
                        {topic.title || 'Untitled Topic'}
                      </h4>
                      {topic.concept_label && (
                        <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400 truncate">
                          {topic.concept_label}
                        </p>
                      )}
                      <div className="mt-2 flex items-center gap-2">
                        <span className={`rounded-full border px-2 py-1 text-[10px] font-black tracking-[0.14em] ${badgeStyle}`}>
                          {statusLabels[currentStatus] || 'PENDING'}
                        </span>
                        <span className="text-[10px] font-semibold text-slate-400">
                          {Math.round((topic.mastery_score || 0) * 100)}%
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-xs text-slate-400">Loading modules...</p>
            )}
          </div>
        </div>
      </div>

      <div className="mt-auto p-6 border-t border-slate-100">
        <button className="w-full py-3 flex items-center justify-center gap-2 text-sm font-bold text-slate-600 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors">
          <span>DL</span> Download Syllabus
        </button>
      </div>
    </div>
  );
};

export default CourseSidebar;
