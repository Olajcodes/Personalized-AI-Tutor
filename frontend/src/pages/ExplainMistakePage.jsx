import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';
import { Loader2, AlertCircle } from 'lucide-react';

import ContextSidebar from '../components/ContextSidebar';
import AIExplanationArea from '../components/AIExplanationArea';
import PracticeSidebar from '../components/PracticeSidebar';

// Keeping mockData as a fallback for the Sidebars while the AI handles the center
import { mockData } from '../mocks/mockData';

const ExplainMistakePage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { token } = useAuth();
  const { studentData, userData } = useUser();
  const activeId = studentData?.user_id || userData?.id;

  const currentSubject = localStorage.getItem('active_subject') || studentData?.subjects?.[0] || 'math';
  const currentLevel = studentData?.sss_level || 'SSS3';
  const currentTerm = studentData?.current_term || 1;

  const apiUrl = import.meta.env.VITE_API_URL || 'https://mastery-backend-7xe8.onrender.com/api/v1';

  // We expect the previous page to pass these via route state
  const { 
    question = "What is the speed of light?", 
    studentAnswer = "100 km/s", 
    correctAnswer = "299,792 km/s", 
    topicId 
  } = location.state || {};

  // --- API STATES ---
  const [explanationData, setExplanationData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    // Safety check
    if (!question || !studentAnswer || !correctAnswer) {
      setError("Missing question details. Please go back and try again.");
      setIsLoading(false);
      return;
    }

    const fetchExplanation = async () => {
      setIsLoading(true);
      setError("");

      try {
        const response = await fetch(`${apiUrl}/tutor/explain-mistake`, {
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
            topic_id: topicId || "unknown-topic", // Provide a fallback if needed
            question: question,
            student_answer: studentAnswer,
            correct_answer: correctAnswer
          })
        });

        if (!response.ok) throw new Error("Failed to fetch AI explanation.");

        const data = await response.json();
        
        // Map the backend response to the shape AIExplanationArea expects
        setExplanationData({
          explanationText: data.explanation,
          improvementTip: data.improvement_tip,
          // Storing original inputs so the component can display them if needed
          questionText: question,
          studentAnswer: studentAnswer,
          correctAnswer: correctAnswer
        });

      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchExplanation();
  }, [question, studentAnswer, correctAnswer, topicId, activeId, currentSubject, currentLevel, currentTerm, token, apiUrl]);


  return (
    <div className="min-h-screen bg-slate-50">
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* 3-Column Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left Column: 3/12 width */}
          <div className="lg:col-span-3 space-y-6">
            <ContextSidebar 
              // Passing the actual question string down instead of mock data
              questionData={{ ...mockData.originalQuestion, text: question }} 
              insightData={mockData.topicInsight} 
            />
          </div>

          {/* Middle Column: 6/12 width */}
          <div className="lg:col-span-6">
            {isLoading ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 flex flex-col items-center justify-center min-h-[400px]">
                 <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mb-4" />
                 <p className="text-slate-500 font-medium">AI Tutor is analyzing your mistake...</p>
              </div>
            ) : error ? (
              <div className="bg-rose-50 rounded-2xl border border-rose-100 p-8 flex flex-col items-center justify-center min-h-[400px] text-center">
                 <AlertCircle className="w-10 h-10 text-rose-500 mb-4" />
                 <p className="text-rose-700 font-bold mb-4">{error}</p>
                 <button onClick={() => navigate(-1)} className="text-rose-600 font-semibold hover:underline">← Go Back</button>
              </div>
            ) : (
              <AIExplanationArea explanationData={explanationData} />
            )}
          </div>

          {/* Right Column: 3/12 width */}
          <div className="lg:col-span-3 space-y-6">
            <PracticeSidebar practiceData={mockData.practice} />
          </div>

        </div>
      </main>
    </div>
  );
};

export default ExplainMistakePage;