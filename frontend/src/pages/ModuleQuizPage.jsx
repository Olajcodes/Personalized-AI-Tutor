import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';
import CourseSidebar from '../components/CourseSidebar';

const ModuleQuizPage = () => {
  const navigate = useNavigate();
  const { topicId } = useParams(); // E.g., /module-quiz/energy-transformation
  const { token } = useAuth();
  const { studentData, userData } = useUser();
  const activeId = studentData?.user_id || userData?.id;

  const currentSubject = localStorage.getItem('active_subject') || studentData?.subjects?.[0] || 'science';
  const currentLevel = studentData?.sss_level || 'JSS2';
  const currentTerm = studentData?.current_term || 1;
  const apiUrl = import.meta.env.VITE_API_URL || 'https://mastery-backend-7xe8.onrender.com/api/v1';

  // --- States ---
  const [phase, setPhase] = useState('generating'); // 'generating' | 'active' | 'submitting' | 'error'
  const [errorMsg, setErrorMsg] = useState('');
  
  const [quizData, setQuizData] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState(null); // Stores 'A', 'B', 'C', 'D'
  const [answers, setAnswers] = useState({});
  const [startTime, setStartTime] = useState(null);

  // ======================================================================
  // 1. AUTO-GENERATE QUIZ ON MOUNT
  // ======================================================================
  useEffect(() => {
    const fetchQuiz = async () => {
      if (!topicId || !activeId) return;
      
      try {
        const response = await fetch(`${apiUrl}/learning/quizzes/generate`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            student_id: activeId,
            subject: currentSubject,
            sss_level: currentLevel,
            term: currentTerm,
            topic_id: topicId, 
            purpose: 'practice', // Defaulting to practice for module flow
            difficulty: 'medium', // Defaulting to medium 
            num_questions: 5 
          })
        });

        if (!response.ok) throw new Error("Failed to generate quiz module.");

        const data = await response.json();
        setQuizData(data);
        setStartTime(Date.now());
        setPhase('active');
      } catch (err) {
        console.error(err);
        setErrorMsg(err.message);
        setPhase('error');
      }
    };

    if (phase === 'generating') {
      fetchQuiz();
    }
  }, [topicId, activeId, token, currentSubject, currentLevel, currentTerm, phase, apiUrl]);


  // ======================================================================
  // 2. HANDLE SUBMISSION & NAVIGATION
  // ======================================================================
const submitAndNavigate = async (finalAnswers) => {
    setPhase('submitting');
    const timeTakenSeconds = Math.floor((Date.now() - startTime) / 1000);
    
    // Format answers as { question_id: "uuid", answer: "A" }
    const formattedAnswers = Object.entries(finalAnswers).map(([qId, ans]) => ({
      question_id: qId,
      answer: ans 
    }));

    try {
      // Step A: Submit Answers
      const submitRes = await fetch(`${apiUrl}/learning/quizzes/${quizData.quiz_id}/submit`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: activeId, answers: formattedAnswers, time_taken_seconds: timeTakenSeconds })
      });

      if (!submitRes.ok) throw new Error("Failed to submit quiz.");
      const submitData = await submitRes.json();

      // Step B: Fetch Detailed Results to pass to the next page
      const resultsRes = await fetch(`${apiUrl}/learning/quizzes/${quizData.quiz_id}/results?student_id=${activeId}&attempt_id=${submitData.attempt_id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!resultsRes.ok) throw new Error("Failed to load detailed results.");
      const resultsJson = await resultsRes.json();

      // ==========================================================
      // 👇 THE FIX: Smart math for Score and Accuracy 👇
      // ==========================================================
      const totalQs = quizData.questions.length;
      const rawScore = resultsJson.score || 0;
      
      // If backend returns 60, keep 60. If it returns 0.6, make it 60.
      const finalScorePercentage = rawScore > 1 ? rawScore : Math.round(rawScore * 100); 
      
      // Calculate correct points (e.g., 60% of 5 questions = 3 correct answers)
      const correctAnswersCount = Math.round((finalScorePercentage / 100) * totalQs);

      const minutes = Math.floor(timeTakenSeconds / 60);
      const seconds = timeTakenSeconds % 60;
      // ==========================================================
      
      const wrongConcepts = (resultsJson.concept_breakdown || [])
        .filter(c => !c.is_correct)
        .map(c => `**${c.concept_id}**`);

      const mappedApiData = {
        paths: { classLevel: currentLevel, topic: currentSubject },
        summary: {
            studentName: userData?.first_name || "Student",
            score: correctAnswersCount, // Fixed: Will show "3" instead of "300"
            total: totalQs,
            message: finalScorePercentage >= 70 ? "Great job! You've shown strong mastery." : "Good effort! Let's review the insights.",
            timeTaken: `${minutes}m ${seconds}s`,
            accuracy: finalScorePercentage, // Fixed: Will show "60" instead of "6000"
            xpEarned: submitData.xp_awarded || Math.round(finalScorePercentage * 2.5)
        },
        concepts: (resultsJson.concept_breakdown || []).map((c, i) => ({
            id: i + 1,
            title: c.concept_id.includes('fallback') ? `Concept ${i+1}` : c.concept_id,
            mastery: c.weight_change > 0 ? 100 : Math.max(0, 50 + (c.weight_change * 10)),
            description: c.is_correct ? "Perfect! You understand this core concept." : "Needs review. Pay attention to the rules here."
        })),
        aiInsights: {
            greeting: `Hi ${userData?.first_name || 'there'}! Here is my analysis:`,
            strugglePoints: wrongConcepts.length > 0 ? wrongConcepts : ["None! Perfect execution."],
            keyInsight: resultsJson.insights?.[0] || "Keep up the consistent practice!",
            prerequisite: resultsJson.insights?.[1] || "Review the foundational rules before moving forward."
        },
        nextTopic: resultsJson.recommended_revision_topic_id || "Next Module"
      };

      // 🚀 BOOM! Navigate to the result page and hand it all the formatted data!
      navigate('/quiz-result', { state: { quizResults: mappedApiData } });

    } catch (err) {
      console.error(err);
      setErrorMsg(err.message);
      setPhase('error');
    }
  };

  // ======================================================================
  // 3. ACTIVE QUIZ HANDLERS
  // ======================================================================
  const handleNextOrSubmit = () => {
    const currentQuestion = quizData.questions[currentIndex];
    const updatedAnswers = { ...answers, [currentQuestion.id]: selectedOption };
    setAnswers(updatedAnswers);

    const isLastQuestion = currentIndex === quizData.questions.length - 1;

    if (isLastQuestion) {
      submitAndNavigate(updatedAnswers);
    } else {
      setCurrentIndex(currentIndex + 1);
      setSelectedOption(updatedAnswers[quizData.questions[currentIndex + 1].id] || null);
    }
  };

  const handleSkip = () => {
    const currentQuestion = quizData.questions[currentIndex];
    const updatedAnswers = { ...answers, [currentQuestion.id]: "SKIPPED" };
    setAnswers(updatedAnswers);

    const isLastQuestion = currentIndex === quizData.questions.length - 1;

    if (isLastQuestion) {
      submitAndNavigate(updatedAnswers);
    } else {
      setCurrentIndex(currentIndex + 1);
      setSelectedOption(updatedAnswers[quizData.questions[currentIndex + 1].id] || null);
    }
  };


  // ======================================================================
  // RENDER: LOADING / ERROR STATES
  // ======================================================================
  if (phase === 'generating' || phase === 'submitting') {
    return (
      <div className="flex bg-slate-50 h-[calc(100vh-64px)] overflow-hidden">
        <CourseSidebar activeStep="quiz" />
        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="w-16 h-16 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin mb-6"></div>
          <h2 className="text-2xl font-black text-slate-800 tracking-tight">
            {phase === 'generating' ? 'Generating Module Challenge...' : 'Analyzing Your Mastery...'}
          </h2>
          <p className="text-slate-500 mt-2 font-medium">Powered by MasteryAI</p>
        </div>
      </div>
    );
  }

  if (phase === 'error') {
    return (
      <div className="flex bg-slate-50 h-[calc(100vh-64px)] overflow-hidden">
        <CourseSidebar activeStep="quiz" />
        <div className="flex-1 flex flex-col items-center justify-center px-8">
          <div className="text-rose-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-black text-slate-800 tracking-tight mb-2">Something went wrong</h2>
          <p className="text-slate-500 mb-6">{errorMsg}</p>
          <button onClick={() => navigate(-1)} className="px-6 py-3 bg-indigo-600 text-white font-bold rounded-xl shadow-lg">Go Back</button>
        </div>
      </div>
    );
  }

  // ======================================================================
  // RENDER: ACTIVE QUIZ
  // ======================================================================
  const currentQuestion = quizData.questions[currentIndex];
  const isLastQuestion = currentIndex === quizData.questions.length - 1;
  const formattedTopicTitle = topicId ? topicId.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Module Quiz';

  return (
    <div className="flex bg-slate-50 h-[calc(100vh-64px)] overflow-hidden">
      
      {/* Left Navigation */}
      <CourseSidebar activeStep="quiz" />

      {/* Center Main Content */}
      <div className="flex-1 overflow-y-auto px-12 py-10 relative">
        <div className="max-w-3xl mx-auto">
          
          {/* Header & Progress */}
          <div className="mb-10">
            <p className="text-[10px] font-bold text-indigo-600 uppercase tracking-widest mb-1">Mastery Challenge</p>
            <div className="flex justify-between items-end mb-4">
              <h1 className="text-3xl font-black text-slate-900 tracking-tight">{formattedTopicTitle}</h1>
              <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                Question {currentIndex + 1} of {quizData.questions.length}
              </span>
            </div>
            
            {/* Dynamic Segmented Progress Bar */}
            <div className="flex gap-1.5 w-full">
              {quizData.questions.map((_, step) => (
                <div key={step} className={`h-2 flex-1 rounded-full transition-colors duration-300 ${
                  step < currentIndex ? 'bg-emerald-400' : 
                  step === currentIndex ? 'bg-indigo-600' : 
                  'bg-slate-200'
                }`}></div>
              ))}
            </div>
          </div>

          {/* Quiz Card */}
          <div className="bg-white p-10 rounded-[2.5rem] shadow-xl border border-slate-100 mb-8">
            <div className="inline-block px-3 py-1 bg-indigo-50 text-indigo-600 text-[10px] font-bold uppercase tracking-widest rounded-full mb-6">
              {currentQuestion.concept_id || 'Multiple Choice'}
            </div>
            
            <h2 className="text-2xl font-bold text-slate-900 mb-8 leading-snug">
              {currentQuestion.text}
            </h2>

            {/* Dynamic Options */}
            <div className="space-y-4 mb-10">
              {currentQuestion.options.map((option, i) => {
                const optionLetter = String.fromCharCode(65 + i); // 'A', 'B', 'C', 'D'
                const optText = typeof option === 'string' ? option : option.text || option.value;
                const isSelected = selectedOption === optionLetter;

                return (
                  <button
                    key={i}
                    onClick={() => setSelectedOption(optionLetter)}
                    className={`w-full text-left p-5 rounded-2xl border-2 transition-all flex items-center gap-4 ${
                      isSelected 
                        ? 'border-indigo-600 bg-indigo-50/30 shadow-md' 
                        : 'border-slate-100 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className={`w-8 h-8 flex-shrink-0 rounded-lg flex items-center justify-center font-bold text-sm transition-colors ${
                      isSelected ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'
                    }`}>
                      {optionLetter}
                    </div>
                    <span className={`font-bold text-lg ${isSelected ? 'text-indigo-900' : 'text-slate-700'}`}>
                      {optText}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="flex justify-between items-center">
              <button onClick={handleSkip} className="text-sm font-bold text-slate-400 hover:text-slate-600 transition-colors">
                Skip Question
              </button>
              <button 
                onClick={handleNextOrSubmit} 
                disabled={!selectedOption}
                className={`px-8 py-3.5 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg ${
                  selectedOption 
                    ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-200 transform hover:-translate-y-0.5' 
                    : 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
                }`}
              >
                {isLastQuestion ? 'Submit Quiz' : 'Confirm Answer'} {selectedOption && <span>✓</span>}
              </button>
            </div>
          </div>

          {/* Bottom Metadata */}
          <div className="flex items-center justify-center gap-8 text-xs font-bold text-slate-400 uppercase tracking-widest">
            <div className="flex items-center gap-2"><span>📍</span> Difficulty: {currentQuestion.difficulty || 'Medium'}</div>
            <div className="flex items-center gap-2"><span>🏆</span> Mastery Points: +50 XP</div>
          </div>

        </div>
      </div>

      {/* Right Hint Sidebar */}
      <div className="w-80 bg-white border-l border-slate-200 flex flex-col p-8 h-[calc(100vh-64px)] justify-between">
        
        <div className="flex flex-col items-center text-center mt-8">
          <div className="relative mb-6">
            <div className="w-20 h-20 bg-indigo-50 rounded-3xl flex items-center justify-center text-4xl shadow-inner border border-indigo-100">
              🤖
            </div>
            <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-emerald-400 border-2 border-white rounded-full"></div>
          </div>
          
          <h3 className="text-lg font-black text-slate-900 mb-3">Need a Hint?</h3>
          <p className="text-sm text-slate-500 leading-relaxed mb-8">
            I can help you think through this, but try to answer independently first to earn max mastery!
          </p>
          
          <button 
            onClick={() => alert("AI Hint System coming soon! 🚀")}
            className="w-full py-3 bg-white border-2 border-slate-200 text-slate-700 font-bold rounded-xl hover:border-indigo-600 hover:text-indigo-600 transition-colors flex items-center justify-center gap-2 shadow-sm"
          >
            <span>💡</span> Ask AI Tutor for a Hint
          </button>
        </div>

        <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex items-start gap-3 text-amber-800 text-xs font-bold leading-relaxed">
          <span className="text-amber-500 text-base">⚠️</span>
          Asking for a hint reduces the mastery points gained on this question.
        </div>

      </div>

    </div>
  );
};

export default ModuleQuizPage;