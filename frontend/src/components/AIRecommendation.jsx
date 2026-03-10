import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Brain, Loader2, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';

export default function AIRecommendation({ availableTopics = [] }) {
  const navigate = useNavigate();
  const { token } = useAuth();
  const { studentData, userData } = useUser();
  const activeId = studentData?.user_id || userData?.id;

  // Derive scope from student profile
  const currentSubject = localStorage.getItem('active_subject') || studentData?.subjects?.[0] || 'math';
  const currentLevel = studentData?.sss_level || 'SSS1';
  const currentTerm = studentData?.current_term || 1;

  const apiUrl = import.meta.env.VITE_API_URL || 'https://mastery-backend-7xe8.onrender.com/api/v1';

  // State
  const [recommendation, setRecommendation] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!activeId || !token) return;

    const fetchNextStep = async () => {
      setIsLoading(true);
      setError("");

      try {
        const response = await fetch(`${apiUrl}/learning/path/next`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            student_id: activeId,
            subject: currentSubject,
            sss_level: currentLevel,
            term: currentTerm
          })
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => null);
          throw new Error(errData?.detail || "Failed to calculate optimal learning path.");
        }

        const data = await response.json();
        setRecommendation(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchNextStep();
  }, [activeId, currentSubject, currentLevel, currentTerm, token, apiUrl]);

  // Handle Loading State
  if (isLoading) {
    return (
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 w-full lg:w-80 h-64 flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mb-4" />
        <p className="text-sm font-semibold text-gray-500 animate-pulse">AI is calculating your path...</p>
      </div>
    );
  }

  // Handle Error State
  if (error) {
    return (
      <div className="bg-rose-50 rounded-3xl p-6 border border-rose-100 w-full lg:w-80 h-64 flex flex-col items-center justify-center text-center">
        <AlertCircle className="w-8 h-8 text-rose-500 mb-2" />
        <p className="text-xs font-bold text-rose-700">{error}</p>
      </div>
    );
  }

  if (!recommendation) return null;

  // --- Map the Data to the UI ---
  
  // 1. Determine if this is a prerequisite gap or a normal progression
  const hasPrereqGap = recommendation.prereq_gaps && recommendation.prereq_gaps.length > 0;
  const isRevision = recommendation.reason.includes("revision");
  
  // 2. Map the returned ID to an actual topic name (Assuming you pass the syllabus/topics as a prop)
  const targetTopicObj = availableTopics.find(t => t.id === recommendation.recommended_topic_id);
  const topicTitle = targetTopicObj ? targetTopicObj.title : "Your Next Module";

  return (
    <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 w-full lg:w-80 flex flex-col justify-between relative overflow-hidden">
      <div>
        <div className="flex items-center justify-between mb-4">
          <span className="bg-indigo-50 text-indigo-600 text-[10px] font-bold px-2 py-1 rounded uppercase tracking-wider">
            AI Recommended
          </span>
          <span className="text-xs text-gray-400">Just updated</span>
        </div>
        
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
          {isRevision ? "Needs Review" : "Why you should study this next"}
        </p>
        
        <h3 className="text-lg font-bold text-gray-900 mb-2">{topicTitle}</h3>
        
        {/* Dynamic Badge based on backend logic */}
        {hasPrereqGap && (
          <div className="inline-flex items-center gap-1.5 bg-yellow-50 text-yellow-700 text-xs px-2.5 py-1 rounded-md mb-3 font-medium">
            <div className="w-1.5 h-1.5 rounded-full bg-yellow-500"></div>
            Prerequisite gap identified
          </div>
        )}
        
        <p className="text-sm text-gray-500 leading-relaxed mb-6">
          {recommendation.reason}
        </p>
      </div>

      <div>
        {/* Since the API doesn't return a confidence score, we re-purpose this to show the Mastery Target */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-gray-900">Mastery Threshold Target</span>
          <span className="text-xl font-bold text-indigo-600">70%</span>
        </div>
        <div className="h-2 w-full bg-gray-100 rounded-full mb-4 overflow-hidden">
          {/* Static 70% width to represent the engine's hardcoded threshold */}
          <div className="h-full bg-indigo-600 rounded-full" style={{ width: '70%' }}></div>
        </div>
        
        <button 
          onClick={() => navigate(`/lesson/${recommendation.recommended_topic_id}`)}
          className="w-full bg-indigo-50 text-indigo-600 py-2.5 rounded-xl font-semibold text-sm hover:bg-indigo-100 transition-colors flex items-center justify-center gap-2 cursor-pointer"
        >
          Start Topic <ChevronRight className="w-4 h-4" />
        </button>
      </div>
      <Brain className="absolute -right-4 top-4 w-24 h-24 text-gray-50 opacity-[0.03] pointer-events-none" />
    </div>
  );
}