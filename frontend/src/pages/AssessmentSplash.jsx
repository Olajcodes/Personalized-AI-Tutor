import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const AssessmentSplash = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const overviewItems = [
    {
      icon: '🔢',
      title: '8-12 Quick Questions',
      desc: 'Takes about 5-10 minutes',
    },
    {
      icon: '📋',
      title: 'No Grades, Just Insights',
      desc: 'Focus on what you need to improve',
    },
    {
      icon: '🗺️',
      title: 'Builds Your Map',
      desc: 'Your custom learning journey awaits',
    },
  ];

  const handleStartAssessment = () => {
    setIsLoading(true);
    
    // Simulate a brief loading state for UX
    setTimeout(() => {
      setIsLoading(false);
      
      // OPTION A: If your backend has a specific "Global Diagnostic" UUID, put it here:
      // const diagnosticTopicId = "YOUR-UUID-HERE";
      // navigate(`/quiz/${diagnosticTopicId}`, { state: { defaultPurpose: 'diagnostic' } });

      // OPTION B: (Recommended for now) Route them to the Dashboard to pick their subject
      // Since a quiz requires a specific topic ID, the best flow is to drop them in the Dashboard 
      // so they can select their first subject and click "Take Diagnostic" there.
      navigate('/dashboard'); 
      
    }, 600);
  };

  return (
    <div className="min-h-screen font-sans p-8 flex flex-col" style={{ backgroundColor: '#F9FAFB' }}>
      {/* Logo */}
      <div className="flex items-center gap-2 mb-12">
        <div 
          className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold shadow-md" 
          style={{ backgroundColor: '#5850EC' }}
        >
          <span className="text-xs">🧠</span>
        </div>
        <span className="text-xl font-bold tracking-tight" style={{ color: '#5850EC' }}>MasteryAI</span>
      </div>

      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-16 mt-10">
        
        {/* Left Side: Headline & Bot Quote */}
        <div className="flex-1 space-y-8">
          <div className="space-y-4">
            <h1 className="text-6xl font-black leading-tight" style={{ color: '#111827' }}>
              Let’s See <br /> 
              What You <br /> 
              <span style={{ color: '#5850EC' }}>Already Know</span>
            </h1>
            <p className="text-lg max-w-md" style={{ color: '#4F566B' }}>
              This short assessment helps MasteryAI create your personalized learning path by identifying your strengths and gaps.
            </p>
          </div>

          {/* Bot Quote Box */}
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 flex items-center gap-4 max-w-sm">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-2xl border border-slate-200">
              🤖
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: '#5850EC' }}>Mastery Bot</p>
              <p className="text-sm font-medium" style={{ color: '#111827' }}>"You've got this! Let's build your custom study plan together."</p>
            </div>
          </div>
        </div>

        {/* Right Side: Assessment Overview Card */}
        <div className="w-full max-w-md bg-white p-10 rounded-[2.5rem] shadow-xl border border-slate-50">
          <h2 className="text-xl font-extrabold mb-8" style={{ color: '#111827' }}>Assessment Overview</h2>
          
          <div className="space-y-8 mb-10">
            {overviewItems.map((item, index) => (
              <div key={index} className="flex items-start gap-4">
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: '#EEF2FF' }}
                >
                  {item.icon}
                </div>
                <div>
                  <h3 className="font-bold text-sm" style={{ color: '#111827' }}>{item.title}</h3>
                  <p className="text-xs" style={{ color: '#6B7280' }}>{item.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <button 
            onClick={handleStartAssessment}
            disabled={isLoading}
            className="w-full py-4 text-white font-bold rounded-2xl shadow-lg transition-all transform active:scale-95 flex items-center justify-center gap-2 mb-4"
            style={{ 
              backgroundColor: isLoading ? '#A3ACBF' : '#5850EC',
              boxShadow: isLoading ? 'none' : '0 10px 15px -3px rgba(88, 80, 236, 0.3)',
              cursor: isLoading ? 'wait' : 'pointer'
            }}
          >
            {isLoading ? 'Preparing...' : 'Start Assessment'} <span>→</span>
          </button>
          
          <button 
            onClick={() => navigate('/dashboard')}
            disabled={isLoading}
            className="w-full py-2 text-sm font-bold transition-colors hover:opacity-70 disabled:opacity-50"
            style={{ color: '#9CA3AF' }}
          >
            Skip for now
          </button>
        </div>

      </div>
    </div>
  );
};

export default AssessmentSplash;
