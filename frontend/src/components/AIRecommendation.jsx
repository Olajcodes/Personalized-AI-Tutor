import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Brain, Loader2, AlertCircle, GitBranch, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';
import { API_URL } from '../config/runtime';
import { resolveStudentId } from '../utils/sessionIdentity';

const safeArray = (value) => (Array.isArray(value) ? value : []);

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
    console.warn('Dashboard recommendation prewarm skipped:', error);
  }
};

export default function AIRecommendation({
  recommendation: recommendationOverride = null,
  activeSubject: activeSubjectProp = null,
  recentEvidence: recentEvidenceOverride = null,
  recommendationStory: recommendationStoryOverride = null,
}) {
  const navigate = useNavigate();
  const { token } = useAuth();
  const { studentData, userData } = useUser();
  const activeId = resolveStudentId(studentData, userData);

  // Derive scope from student profile
  const currentSubject = activeSubjectProp || localStorage.getItem('active_subject') || studentData?.subjects?.[0] || 'math';
  const currentLevel = studentData?.sss_level || 'SSS1';
  const currentTerm = studentData?.current_term || 1;

  const apiUrl = API_URL;

  // State
  const [recommendation, setRecommendation] = useState(null);
  const [recentEvidence, setRecentEvidence] = useState(null);
  const [recommendationStory, setRecommendationStory] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (recommendationOverride) {
      setRecommendation(recommendationOverride);
      setRecentEvidence(recentEvidenceOverride || null);
      setRecommendationStory(recommendationStoryOverride || null);
      setError("");
      setIsLoading(false);
      return;
    }

    if (!activeId || !token) return;

    const fetchNextStep = async () => {
      setIsLoading(true);
      setError("");

      try {
        const queryParams = new URLSearchParams({
          student_id: activeId,
          subject: currentSubject,
          term: currentTerm,
        });

        const response = await fetch(`${apiUrl}/learning/course/bootstrap?${queryParams.toString()}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => null);
          throw new Error(errData?.detail || "Failed to calculate graph recommendation.");
        }

        const data = await response.json();
        if (!data?.next_step) {
          throw new Error(data?.map_error || "Graph recommendation unavailable.");
        }
        setRecommendation(data.next_step);
        setRecentEvidence(data.recent_evidence || null);
        setRecommendationStory(data.recommendation_story || null);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchNextStep();
  }, [activeId, currentSubject, currentLevel, currentTerm, token, apiUrl, recommendationOverride, recentEvidenceOverride, recommendationStoryOverride]);

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

  const hasPrereqGap = safeArray(recommendation.prereq_gaps).length > 0;
  const blockingLabels = safeArray(recommendation.prereq_gap_labels);
  const scopeWarning = recommendation.scope_warning || null;
  const unmappedTopics = safeArray(recommendation.unmapped_topic_titles);
  const recommendedTopicId = recommendation.recommended_topic_id || null;

  const title = recommendation.recommended_topic_title
    || recommendation.recommended_concept_label
    || recommendation.reason
    || 'Graph recommendation unavailable';
  const subtitle = hasPrereqGap && blockingLabels.length
    ? `Rebuild ${blockingLabels[0]} before moving deeper.`
    : recommendation.recommended_concept_label
      ? `Current concept focus: ${recommendation.recommended_concept_label}`
      : 'Graph sequencing is using your mastery evidence to choose the best next step.';
  const story = recommendationStory || null;
  const primaryActionLabel = story?.action_label || (hasPrereqGap ? 'Repair prerequisite' : 'Open next unlock');

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
          {hasPrereqGap ? "Prerequisite bridge" : "Why you should study this next"}
        </p>
        
        <h3 className="text-lg font-bold text-gray-900 mb-2">{story?.headline || title}</h3>
        <p className="text-sm font-medium text-gray-600 mb-3">{subtitle}</p>
        
        {hasPrereqGap && (
          <div className="inline-flex items-center gap-1.5 bg-yellow-50 text-yellow-700 text-xs px-2.5 py-1 rounded-md mb-3 font-medium">
            <div className="w-1.5 h-1.5 rounded-full bg-yellow-500"></div>
            Prerequisite gap identified
          </div>
        )}

        {!hasPrereqGap && recommendation.recommended_concept_label && (
          <div className="inline-flex items-center gap-1.5 bg-indigo-50 text-indigo-700 text-xs px-2.5 py-1 rounded-md mb-3 font-medium">
            <GitBranch className="w-3.5 h-3.5" />
            Focus concept: {recommendation.recommended_concept_label}
          </div>
        )}
        
        <p className="text-sm text-gray-500 leading-relaxed mb-4">
          {story?.supporting_reason || recommendation.reason}
        </p>

        {blockingLabels.length > 0 && (
          <div className="mb-4 rounded-2xl border border-amber-100 bg-amber-50 px-4 py-3">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-amber-700">Blocking concepts</div>
            <p className="mt-2 text-xs font-semibold leading-6 text-amber-900">{blockingLabels.join(', ')}</p>
          </div>
        )}

        {story?.next_concept_label && !hasPrereqGap && (
          <div className="mb-4 rounded-2xl border border-cyan-100 bg-cyan-50 px-4 py-3">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-cyan-700">Best next concept</div>
            <p className="mt-2 text-xs font-semibold leading-6 text-cyan-900">{story.next_concept_label}</p>
          </div>
        )}

        {recentEvidence && (
          <div className="mb-4 rounded-2xl border border-indigo-100 bg-indigo-50 px-4 py-3">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-indigo-600">Latest evidence</div>
            <p className="mt-2 text-xs leading-6 text-indigo-900">{recentEvidence.summary}</p>
            {(recentEvidence.strongest_gain_concept_label || recentEvidence.strongest_drop_concept_label) && (
              <p className="mt-2 text-[11px] font-semibold leading-5 text-indigo-700">
                {recentEvidence.strongest_gain_concept_label ? `Gain: ${recentEvidence.strongest_gain_concept_label}` : 'No recent gain'}
                {recentEvidence.strongest_drop_concept_label ? ` · Gap: ${recentEvidence.strongest_drop_concept_label}` : ''}
              </p>
            )}
          </div>
        )}

        {story?.evidence_summary && !recentEvidence && (
          <div className="mb-4 rounded-2xl border border-indigo-100 bg-indigo-50 px-4 py-3">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-indigo-600">Latest evidence</div>
            <p className="mt-2 text-xs leading-6 text-indigo-900">{story.evidence_summary}</p>
          </div>
        )}

        {scopeWarning && (
          <div className="mb-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-500">Scope warning</div>
            <p className="mt-2 text-xs leading-6 text-slate-700">{scopeWarning}</p>
            {unmappedTopics.length > 0 && (
              <p className="mt-2 text-[11px] font-semibold leading-5 text-slate-600">
                Pending mapping: {unmappedTopics.join(', ')}
              </p>
            )}
          </div>
        )}
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-gray-900">Mastery Threshold Target</span>
          <span className="text-xl font-bold text-indigo-600">70%</span>
        </div>
        <div className="h-2 w-full bg-gray-100 rounded-full mb-4 overflow-hidden">
          <div className="h-full bg-indigo-600 rounded-full" style={{ width: '70%' }}></div>
        </div>
        
        <button 
          onClick={async () => {
            if (recommendedTopicId) {
              await prewarmTopics({
                apiUrl,
                token,
                studentId: activeId,
                subject: currentSubject,
                sssLevel: currentLevel,
                term: currentTerm,
                topicIds: [recommendedTopicId],
              });
              navigate(`/lesson/${recommendedTopicId}`);
            }
          }}
          disabled={!recommendedTopicId}
          className={`w-full py-2.5 rounded-xl font-semibold text-sm transition-colors flex items-center justify-center gap-2 ${
            recommendedTopicId
              ? 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100 cursor-pointer'
              : 'bg-slate-100 text-slate-400 cursor-not-allowed'
          }`}
        >
          {recommendedTopicId ? (
            <>
              {primaryActionLabel} <ChevronRight className="w-4 h-4" />
            </>
          ) : (
            <>
              Graph recommendation unavailable <Lock className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
      <Brain className="absolute -right-4 top-4 w-24 h-24 text-gray-50 opacity-[0.03] pointer-events-none" />
    </div>
  );
}

