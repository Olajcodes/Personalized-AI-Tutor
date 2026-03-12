import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';
import CourseSidebar from '../components/CourseSidebar';
import { PlayCircle, Clock, BookOpen, GitBranch, Lock, Sparkles } from 'lucide-react';
import {
  buildGraphInterventionScope,
  readGraphIntervention,
  subscribeGraphIntervention,
} from '../services/graphIntervention';

const safeArray = (value) => (Array.isArray(value) ? value : []);

const statusStyles = {
  current: 'border-indigo-300 bg-indigo-50 text-indigo-700',
  ready: 'border-sky-300 bg-sky-50 text-sky-700',
  mastered: 'border-emerald-300 bg-emerald-50 text-emerald-700',
  locked: 'border-slate-200 bg-slate-50 text-slate-500',
  unmapped: 'border-amber-300 bg-amber-50 text-amber-800',
  pending: 'border-slate-200 bg-slate-50 text-slate-500',
};

const statusLabels = {
  current: 'Current focus',
  ready: 'Ready',
  mastered: 'Mastered',
  locked: 'Locked',
  unmapped: 'Mapping pending',
  pending: 'Pending',
};

const prewarmTopics = async ({ apiUrl, token, studentId, subject, sssLevel, term, topicIds }) => {
  const normalizedIds = Array.from(new Set((topicIds || []).filter(Boolean)));
  if (!normalizedIds.length) return;
  try {
    await fetch(`${apiUrl}/learning/lesson/prewarm`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        student_id: studentId,
        subject,
        sss_level: sssLevel,
        term,
        topic_ids: normalizedIds,
      }),
    });
  } catch (error) {
    console.warn('Course recommendation prewarm skipped:', error);
  }
};

const CoursePage = () => {
  const { subject } = useParams(); 
  const navigate = useNavigate();
  
  const { token } = useAuth();
  const { studentData, userData } = useUser();
  const activeId = studentData?.user_id || userData?.id;
  const currentLevel = studentData?.sss_level || 'SSS1';
  const currentTerm = studentData?.current_term || 1;

  const [topics, setTopics] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [nextStep, setNextStep] = useState(null);
  const [recentEvidence, setRecentEvidence] = useState(null);
  const [recommendationStory, setRecommendationStory] = useState(null);
  const [mapError, setMapError] = useState('');
  const [graphIntervention, setGraphIntervention] = useState(null);

  const apiUrl = import.meta.env.VITE_API_URL || 'https://mastery-backend-7xe8.onrender.com/api/v1';
  const interventionScope = useMemo(
    () => buildGraphInterventionScope({
      studentId: activeId,
      subject,
      sssLevel: currentLevel,
      term: currentTerm,
    }),
    [activeId, currentLevel, currentTerm, subject],
  );
  const effectiveNextStep = graphIntervention?.next_step || nextStep || null;
  const effectiveRecentEvidence = graphIntervention?.recent_evidence || recentEvidence || null;
  const effectiveRecommendationStory = graphIntervention?.recommendation_story || recommendationStory || null;

  useEffect(() => {
    if (!interventionScope) {
      setGraphIntervention(null);
      return () => {};
    }
    setGraphIntervention(readGraphIntervention(interventionScope));
    return subscribeGraphIntervention(interventionScope, setGraphIntervention);
  }, [interventionScope]);

  useEffect(() => {
    if (!activeId || !token || !subject) return;

    const fetchTopicsList = async () => {
      setIsLoading(true);
      setMapError('');

      try {
        const bootstrapParams = new URLSearchParams({
          student_id: activeId,
          subject: subject,
          term: currentTerm,
        });
        const response = await fetch(`${apiUrl}/learning/course/bootstrap?${bootstrapParams.toString()}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) {
          throw new Error('Failed to fetch course bootstrap');
        }

        const data = await response.json();
        localStorage.setItem('active_subject', subject);
        setTopics(safeArray(data?.topics));
        setNextStep(data?.next_step || null);
        setRecentEvidence(data?.recent_evidence || null);
        setRecommendationStory(data?.recommendation_story || null);
        setMapError(data?.map_error || '');

      } catch (err) {
        console.error("CoursePage Error:", err);
        setTopics([]);
        setNextStep(null);
        setRecentEvidence(null);
        setRecommendationStory(null);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchTopicsList();
  }, [activeId, token, subject, currentLevel, currentTerm, apiUrl]);

  const displayTopics = useMemo(
    () => (Array.isArray(topics) ? topics : []).map((topic) => (
      effectiveNextStep?.recommended_topic_id && topic?.topic_id === effectiveNextStep.recommended_topic_id
        ? { ...topic, is_recommended: true }
        : topic
    )),
    [effectiveNextStep, topics],
  );

  return (
    <div className="flex bg-slate-50 h-[calc(100vh-64px)] overflow-hidden">
      
      {/* Sidebar */}
      <CourseSidebar 
        activeStep={null} 
        subject={subject} 
        topics={displayTopics} 
        level={currentLevel}
      />
      
      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto px-8 py-10 lg:px-12">
        <div className="max-w-4xl mx-auto">
          
          <div className="mb-10">
            <h1 className="text-4xl font-black text-slate-900 mb-3 capitalize">{subject} Learning Path</h1>
            <p className="text-slate-500 text-lg">Follow this AI-curated syllabus to achieve mastery in {currentLevel} {subject}.</p>
          </div>

          {effectiveNextStep && (
            <div className="mb-6 rounded-3xl border border-indigo-200 bg-gradient-to-r from-indigo-50 via-white to-sky-50 p-6 shadow-sm">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="max-w-2xl">
                  <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-indigo-700">
                    <GitBranch className="h-3.5 w-3.5" />
                    Next best move
                  </div>
                  <h2 className="mt-3 text-2xl font-black text-slate-900">
                    {effectiveRecommendationStory?.headline || effectiveNextStep.recommended_topic_title || effectiveNextStep.recommended_concept_label || 'Continue current focus'}
                  </h2>
                  <p className="mt-2 text-sm leading-7 text-slate-600">{effectiveRecommendationStory?.supporting_reason || effectiveNextStep.reason}</p>
                  {safeArray(effectiveNextStep.prereq_gap_labels).length > 0 && (
                    <p className="mt-3 text-sm font-semibold text-amber-700">
                      Blocking prerequisites: {effectiveNextStep.prereq_gap_labels.join(', ')}
                    </p>
                  )}
                  {effectiveRecommendationStory?.next_concept_label && (
                    <p className="mt-3 text-sm font-semibold text-cyan-700">
                      Best next concept: {effectiveRecommendationStory.next_concept_label}
                    </p>
                  )}
                  {effectiveRecommendationStory?.evidence_summary && (
                    <p className="mt-3 text-sm leading-7 text-slate-500">
                      {effectiveRecommendationStory.evidence_summary}
                    </p>
                  )}
                </div>
                <button
                  onClick={async () => {
                    if (effectiveNextStep.recommended_topic_id) {
                      await prewarmTopics({
                        apiUrl,
                        token,
                        studentId: activeId,
                        subject,
                        sssLevel: currentLevel,
                        term: currentTerm,
                        topicIds: [effectiveNextStep.recommended_topic_id],
                      });
                      navigate(`/lesson/${effectiveNextStep.recommended_topic_id}`);
                    }
                  }}
                  disabled={!effectiveNextStep.recommended_topic_id}
                  className={`inline-flex items-center justify-center gap-2 rounded-2xl px-5 py-3 text-sm font-black transition-colors ${
                    effectiveNextStep.recommended_topic_id
                      ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                      : 'bg-slate-200 text-slate-500 cursor-not-allowed'
                  }`}
                >
                  {effectiveRecommendationStory?.action_label || 'Open Recommended Lesson'} <Sparkles className="h-4 w-4" />
                </button>
              </div>
              {mapError && (
                <p className="mt-4 text-xs font-semibold text-slate-500">{mapError}</p>
              )}
            </div>
          )}

          {effectiveRecentEvidence && (
            <div className="mb-6 rounded-3xl border border-indigo-100 bg-white p-5 shadow-sm">
              <div className="text-[10px] font-black uppercase tracking-[0.18em] text-indigo-600">Latest evidence</div>
              <p className="mt-2 text-sm leading-7 text-slate-700">{effectiveRecentEvidence.summary}</p>
              {(effectiveRecentEvidence.strongest_gain_concept_label || effectiveRecentEvidence.strongest_drop_concept_label) && (
                <p className="mt-3 text-xs font-semibold text-slate-500">
                  {effectiveRecentEvidence.strongest_gain_concept_label ? `Gain: ${effectiveRecentEvidence.strongest_gain_concept_label}` : 'No recent gain'}
                  {effectiveRecentEvidence.strongest_drop_concept_label ? ` · Gap: ${effectiveRecentEvidence.strongest_drop_concept_label}` : ''}
                </p>
              )}
            </div>
          )}

          {mapError && !effectiveNextStep && (
            <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm font-semibold text-amber-800">
              {mapError}
            </div>
          )}

          {isLoading ? (
            <div className="space-y-4 animate-pulse">
               {[1,2,3,4].map(i => (
                 <div key={i} className="h-28 bg-white border border-slate-200 rounded-2xl w-full"></div>
               ))}
            </div>
          ) : displayTopics.length > 0 ? (
            <div className="space-y-4">
              {displayTopics.map((topic, index) => {
                const targetId = topic.topic_id || topic.id;
                const currentStatus = topic.status || 'pending';
                const isLocked = currentStatus === 'locked';
                const isRecommended = Boolean(topic.is_recommended);
                const cardStyle = statusStyles[currentStatus] || statusStyles.pending;
                const openTopic = async () => {
                  if (isLocked || !targetId) return;
                  await prewarmTopics({
                    apiUrl,
                    token,
                    studentId: activeId,
                    subject,
                    sssLevel: currentLevel,
                    term: currentTerm,
                    topicIds: [targetId],
                  });
                  navigate(`/lesson/${targetId}`);
                };

                return (
                  <div 
                    key={targetId || index} 
                    onClick={openTopic}
                    className={`p-6 rounded-2xl border-2 bg-white transition-all group flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                      isLocked ? 'opacity-75 cursor-not-allowed border-slate-200' : 'cursor-pointer hover:shadow-md'
                    } ${
                      isRecommended ? 'border-indigo-400 shadow-[0_18px_50px_rgba(99,102,241,0.12)]' : cardStyle.includes('border-') ? cardStyle.split(' ')[0] : 'border-slate-200'
                    }`}
                  >
                    <div className="flex items-start gap-5">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold flex-shrink-0 mt-1 md:mt-0 ${
                        currentStatus === 'mastered'
                          ? 'bg-emerald-50 text-emerald-600'
                          : currentStatus === 'current'
                            ? 'bg-indigo-50 text-indigo-600'
                            : currentStatus === 'ready'
                              ? 'bg-sky-50 text-sky-600'
                              : 'bg-slate-100 text-slate-500'
                      }`}>
                          {index + 1}
                      </div>
                      <div>
                        <div className="mb-2 flex flex-wrap items-center gap-2">
                          <span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${cardStyle}`}>
                            {statusLabels[currentStatus] || 'Pending'}
                          </span>
                          {isRecommended && (
                            <span className="rounded-full bg-indigo-600 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-white">
                              Recommended now
                            </span>
                          )}
                        </div>
                        <h3 className="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                            {topic.title || 'Untitled Topic'}
                        </h3>
                        <p className="text-sm text-slate-500 mt-1 line-clamp-2 max-w-xl">
                            {topic.graph_details || topic.description || topic.lesson_unavailable_reason || 'Topic context unavailable.'}
                        </p>
                        {topic.concept_label && (
                          <p className="mt-2 text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
                            Concept focus: {topic.concept_label}
                          </p>
                        )}
                        
                        <div className="flex items-center gap-4 mt-3">
                           {topic.estimated_duration_minutes && (
                              <span className="flex items-center gap-1.5 text-xs font-bold text-slate-400">
                                 <Clock className="w-3.5 h-3.5" />
                                 ~{topic.estimated_duration_minutes} Mins
                              </span>
                           )}
                           {topic.lesson_title && (
                              <span className="flex items-center gap-1.5 text-xs font-bold text-slate-400 truncate max-w-[200px]">
                                 <BookOpen className="w-3.5 h-3.5" />
                                 {topic.lesson_title}
                              </span>
                           )}
                           <span className="text-xs font-bold text-slate-400">
                             {Math.round((topic.mastery_score || 0) * 100)}% mastery
                           </span>
                        </div>
                      </div>
                    </div>

                    <button className={`flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-bold transition-colors md:w-auto w-full ${
                      isLocked
                        ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                        : 'bg-slate-100 text-slate-600 group-hover:bg-indigo-600 group-hover:text-white'
                    }`}>
                        {isLocked ? 'Locked in graph' : 'Start Lesson'} {isLocked ? <Lock className="w-4 h-4" /> : <PlayCircle className="w-4 h-4" />}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
             <div className="text-center py-16 bg-white rounded-3xl border border-slate-200 shadow-sm">
                 <div className="w-20 h-20 bg-slate-50 text-slate-300 rounded-full flex items-center justify-center mx-auto mb-4">
                    <BookOpen className="w-10 h-10" />
                 </div>
                 <h3 className="text-xl font-bold text-slate-800 mb-2">No Topics Available</h3>
                 <p className="text-slate-500 max-w-md mx-auto">Your AI Tutor is still finalizing the syllabus for {currentLevel} {subject} Term {currentTerm}. Please check back soon!</p>
             </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CoursePage;
