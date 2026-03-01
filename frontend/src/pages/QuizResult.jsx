import React, { useEffect, useMemo, useState } from "react";
import { BarChart2 } from "lucide-react";
import Breadcrumbs from "../components/BreadCrumbs";
import ScoreSummary from "../components/ScoreSummary";
import ConceptCard from "../components/ConceptCard";
import AITutorInsights from "../components/AITutorInsights";
import PathProgress from "../components/PathProgress";
import FooterActions from "../components/FooterActions";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

function loadAttempt() {
  try {
    return JSON.parse(localStorage.getItem("mastery_quiz_last_attempt") || "{}");
  } catch {
    return {};
  }
}

export default function QuizResult() {
  const { token, userId, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [quizData, setQuizData] = useState(null);
  const attempt = useMemo(() => loadAttempt(), []);

  useEffect(() => {
    let active = true;
    (async () => {
      if (!token || !userId || !attempt.quiz_id || !attempt.attempt_id) {
        setError("No recent quiz attempt found.");
        setLoading(false);
        return;
      }
      try {
        const result = await api.quizResults(token, attempt.quiz_id, userId, attempt.attempt_id);
        if (!active) return;
        const scorePct = Number(result.score || 0);
        const total = Math.max(1, result.concept_breakdown?.length || 1);
        const scoreRaw = Math.round((scorePct / 100) * total);
        setQuizData({
          paths: { classLevel: "SSS", topic: "Quiz Result" },
          summary: {
            studentName: user?.display_name || user?.first_name || "Student",
            score: scoreRaw,
            total,
            message: result.insights?.[0] || "Review your breakdown below.",
            timeTaken: "-",
            accuracy: Math.round(scorePct),
            xpEarned: attempt.xp_awarded || 0,
          },
          concepts: (result.concept_breakdown || []).map((item) => ({
            id: item.concept_id,
            title: item.concept_id,
            mastery: item.is_correct ? 100 : 0,
            description: item.is_correct ? "Answered correctly." : "Needs review.",
          })),
          aiInsights: {
            greeting: "Great effort!",
            strugglePoints: (result.concept_breakdown || []).filter((x) => !x.is_correct).slice(0, 2).map((x) => x.concept_id),
            keyInsight: result.insights?.[0] || "Keep practicing to improve mastery.",
            prerequisite: result.insights?.[1] || "Strengthen weak concepts before the next topic.",
          },
          nextTopic: result.recommended_revision_topic_id || "Next topic",
        });
      } catch (err) {
        if (!active) return;
        setError(err.message || "Failed to load quiz results.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [token, userId, attempt, user]);

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-slate-50">Loading results...</div>;
  if (error || !quizData) return <div className="min-h-screen flex items-center justify-center bg-slate-50 text-rose-700">{error || "Quiz results unavailable."}</div>;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <Breadcrumbs classLevel={quizData.paths.classLevel} topic={quizData.paths.topic} />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 flex flex-col">
          <ScoreSummary data={quizData.summary} />
          <div className="mb-4 flex items-center gap-2">
            <BarChart2 className="w-6 h-6 text-emerald-500" />
            <h2 className="text-xl font-bold text-gray-900">Concept Mastery Breakdown</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {quizData.concepts.map((concept) => (
              <ConceptCard key={concept.id} title={concept.title} mastery={concept.mastery} description={concept.description} />
            ))}
          </div>
        </div>
        <div className="lg:col-span-1 flex flex-col">
          <AITutorInsights insights={quizData.aiInsights} />
          <PathProgress nextTopic={quizData.nextTopic} />
        </div>
      </div>
      <FooterActions />
    </div>
  );
}
