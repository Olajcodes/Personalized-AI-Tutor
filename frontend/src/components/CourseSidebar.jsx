import React from 'react';
import { useNavigate } from 'react-router-dom';

const CourseSidebar = ({ activeStep, subject = "Subject", topics = [], level = "Level" }) => {
  const navigate = useNavigate();

  // Safely calculate completion (fallback to 0 if status isn't provided by backend yet)
  const completedCount = topics.filter(t => t.status === 'mastered').length;
  const totalCount = topics.length > 0 ? topics.length : 1;
  const progressPercent = Math.round((completedCount / totalCount) * 100);

  return (
    <div className="w-72 bg-white border-r border-slate-200 flex flex-col h-[calc(100vh-64px)] overflow-y-auto">
      <div className="p-6">
        <button 
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-2 text-indigo-600 font-bold text-sm mb-8 hover:text-indigo-800 transition-colors"
        >
          <span>←</span> Back to Dashboard
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
                    // 1. SAFELY GRAB ID AND STATUS
                    const targetId = topic.topic_id || topic.id;
                    const currentStatus = topic.status || 'pending'; // Default to 'pending' if missing!
                    
                    const isLocked = currentStatus === 'locked';
                    const isMastered = currentStatus === 'mastered';
                    const isActive = activeStep === targetId || currentStatus === 'current';

                    return (
                        <div 
                            key={targetId || index}
                            onClick={() => {
                                if (!isLocked && targetId) navigate(`/lesson/${targetId}`);
                            }}
                            className={`flex items-start gap-3 p-3 rounded-xl transition-colors ${
                                isLocked ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
                            } ${
                                isActive ? 'bg-indigo-50 border border-indigo-100/50' : 'hover:bg-slate-50'
                            }`}
                        >
                            <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                                isMastered ? 'bg-emerald-100 text-emerald-600' :
                                isActive ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200' :
                                'bg-slate-100 text-slate-400'
                            }`}>
                                {isMastered ? '✓' : 
                                 isActive ? <span className="text-xs">▶</span> : 
                                 isLocked ? <span className="text-xs">🔒</span> :
                                 <span className="text-xs">{index + 1}</span>}
                            </div>
                            
                            <div>
                                <h4 className={`text-sm font-bold leading-tight ${
                                    isActive ? 'text-indigo-900' : 
                                    isMastered ? 'text-slate-900' : 'text-slate-500'
                                }`}>
                                    {topic.title || 'Untitled Topic'}
                                </h4>
                                <p className={`text-[10px] font-medium mt-1 ${
                                    isActive ? 'text-indigo-600' : 'text-slate-400'
                                }`}>
                                    {/* SAFELY CALL toUpperCase() ONLY ON A VALID STRING */}
                                    {currentStatus.toUpperCase()}
                                </p>
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
          <span>📥</span> Download Syllabus
        </button>
      </div>
    </div>
  );
};

export default CourseSidebar;