import React from 'react';
import { PlayCircle, BookOpen, ArrowRight } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { useNavigate } from 'react-router-dom'; // <-- 1. Import useNavigate

const HeroSection = ({ enrolledSubjects, activeSubject, onSelectSubject, hasStartedLearning }) => {
  const { userData } = useUser();
  const firstName = userData?.first_name || 'Student';
  const navigate = useNavigate(); // <-- 2. Initialize it

  const handleStartLearning = () => {
    if (activeSubject) {
      // Changed to /course/ so it matches our new App.jsx route!
      navigate(`/course/${activeSubject}`); 
    }
  };

  return (
    <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200 flex-1 relative overflow-hidden">
      {/* Background Decoration */}
      <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-indigo-50 rounded-full blur-3xl opacity-50 pointer-events-none"></div>

      <div className="relative z-10">
        <h1 className="text-3xl font-black text-slate-900 mb-2 tracking-tight">
          Welcome back, {firstName}! 👋
        </h1>
        
        {!activeSubject ? (
          <>
            <p className="text-slate-500 mb-6">
              You are enrolled in {enrolledSubjects?.length || 0} subjects. Which one would you like to focus on today?
            </p>
            <div className="flex flex-wrap gap-4">
              {enrolledSubjects && enrolledSubjects.length > 0 ? (
                enrolledSubjects.map(sub => (
                  <button 
                    key={sub}
                    onClick={() => onSelectSubject(sub)}
                    className="flex items-center gap-3 bg-white border-2 border-slate-100 hover:border-indigo-600 text-slate-700 hover:text-indigo-700 px-6 py-4 rounded-2xl font-bold transition-all transform hover:-translate-y-1 hover:shadow-lg group cursor-pointer"
                  >
                    <div className="bg-indigo-50 p-2 rounded-lg group-hover:bg-indigo-100 transition-colors">
                      <BookOpen className="w-5 h-5 text-indigo-600" />
                    </div>
                    <span className="capitalize">{sub}</span>
                    <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity ml-2 text-indigo-500" />
                  </button>
                ))
              ) : (
                 <p className="text-sm text-rose-500 font-bold">No subjects found. Please update your class settings.</p>
              )}
            </div>
          </>
        ) : (
          <>
            <p className="text-slate-500 mb-6">
              Ready to dive into <strong className="text-indigo-600 capitalize">{activeSubject}</strong>?
            </p>
            <div className="flex items-center gap-4">
                {/* 4. Wire up the Start Learning button */}
                <button 
                  onClick={handleStartLearning}
                  className="bg-indigo-600 text-white px-8 py-3.5 rounded-xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200 flex items-center gap-2 transform hover:scale-105 active:scale-95 cursor-pointer"
                >
                  <PlayCircle className="w-5 h-5" />
                  {hasStartedLearning ? 'Resume Learning' : 'Start First Lesson'}
                </button>
                <button 
                  onClick={() => onSelectSubject(null)}
                  className="text-sm font-semibold text-slate-400 hover:text-indigo-600 transition-colors border border-transparent hover:border-indigo-100 bg-transparent hover:bg-indigo-50 px-4 py-2 rounded-lg cursor-pointer"
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