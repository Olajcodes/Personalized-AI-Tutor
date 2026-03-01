import React from 'react';
import { useNavigate } from 'react-router-dom';

const CourseSidebar = ({ activeStep }) => {
  const navigate = useNavigate();

  const lessons = [
    { id: 'matter', title: 'Matter in Nature', duration: 'Approximate 12 min', status: 'completed' },
    { id: 'living', title: 'Living Things', duration: 'Approximate 20 min', status: 'completed' },
    { id: 'energy', title: 'Energy Transformation', duration: 'In Progress • 10 Min', status: activeStep === 'energy' ? 'active' : 'locked' },
    { id: 'forces', title: 'Forces & Power', duration: 'Locked until Oct 25', status: 'locked' },
    { id: 'quiz', title: 'Mastery Quiz', duration: 'QUESTION 3 OF 10', status: activeStep === 'quiz' ? 'active' : 'locked' },
  ];

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
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Current Module</p>
          <h2 className="text-lg font-black text-slate-900 mb-2">03: Basic Science (JSS2)</h2>
          <div className="flex justify-between items-center text-xs font-bold text-indigo-600 mb-2">
            <span>60% Complete</span>
            <span className="text-slate-400">3/5 Units</span>
          </div>
          <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-indigo-600 w-[60%] rounded-full"></div>
          </div>
        </div>

        <div>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">Lessons</p>
          <div className="space-y-1">
            {lessons.map((lesson) => (
              <div 
                key={lesson.id}
                onClick={() => {
                  // <-- FIXED: Updated to point to /learning-path instead of /lesson -->
                  if (lesson.id === 'energy') navigate('/learning-path'); 
                  if (lesson.id === 'quiz') navigate('/module-quiz');
                }}
                className={`flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-colors ${
                  lesson.status === 'active' ? 'bg-indigo-50 border border-indigo-100/50' : 'hover:bg-slate-50'
                }`}
              >
                {/* Status Icon */}
                <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  lesson.status === 'completed' ? 'bg-emerald-100 text-emerald-600' :
                  lesson.status === 'active' ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200' :
                  'bg-slate-100 text-slate-400'
                }`}>
                  {lesson.status === 'completed' ? '✓' : 
                   lesson.status === 'active' ? <span className="text-xs">▶</span> : 
                   <span className="text-xs">🔒</span>}
                </div>
                
                <div>
                  <h4 className={`text-sm font-bold ${
                    lesson.status === 'active' ? 'text-indigo-900' : 
                    lesson.status === 'completed' ? 'text-slate-900' : 'text-slate-500'
                  }`}>
                    {lesson.title}
                  </h4>
                  <p className={`text-[10px] font-medium mt-0.5 ${
                    lesson.status === 'active' ? 'text-indigo-600' : 'text-slate-400'
                  }`}>
                    {lesson.duration}
                  </p>
                </div>
              </div>
            ))}
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