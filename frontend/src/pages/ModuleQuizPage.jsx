import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import CourseSidebar from "../components/CourseSidebar";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

const mapMasteryPayload = (payload) => {
  const result = {};
  for (const item of payload?.mastery || []) {
    const key = item?.topic_id || item?.concept_id;
    if (!key) continue;
    const score = Number(item?.score);
    result[key] = Number.isFinite(score) ? Math.max(0, Math.min(1, score)) : 0;
  }
  return result;
};

const ModuleQuizPage = () => {
  const navigate = useNavigate();
  const { token, userId } = useAuth();

  const [quiz, setQuiz] = useState(null);
  const [profile, setProfile] = useState(null);
  const [sidebarTopics, setSidebarTopics] = useState([]);
  const [masteryByTopic, setMasteryByTopic] = useState({});
  const [selectedTopicId, setSelectedTopicId] = useState(null);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const currentQuestion = quiz?.questions?.[currentQuestionIndex] || null;
  const isLastQuestion = currentQuestionIndex === (quiz?.questions?.length || 1) - 1;
  const canContinue = Boolean(currentQuestion && selectedAnswers[currentQuestion.id]);

  useEffect(() => {
    let active = true;
    (async () => {
      if (!token || !userId) return;
      setLoading(true);
      setError("");
      try {
        const profilePayload = await api.getProfile(token);
        const subject = profilePayload?.subjects?.[0] || "math";
        const term = Number(profilePayload?.current_term || 1);
        setProfile(profilePayload);

        const [topicsPayload, masteryPayload] = await Promise.all([
          api.listTopics({ student_id: userId, subject, term }, token),
          api.getMastery(token, {
            student_id: userId,
            subject,
            term,
            view: "topic",
          }),
        ]);
        if (!active) return;
        setSidebarTopics(topicsPayload || []);
        setMasteryByTopic(mapMasteryPayload(masteryPayload));

        const topicId = localStorage.getItem("mastery_current_topic_id");
        if (!topicId) throw new Error("No active topic found. Open Learning Path first.");
        setSelectedTopicId(topicId);

        const generated = await api.quizGenerate(token, {
          student_id: userId,
          subject,
          sss_level: profilePayload?.sss_level || "SSS1",
          term,
          topic_id: topicId,
          purpose: "practice",
          difficulty: "medium",
          num_questions: 10,
        });
        if (!active) return;
        setQuiz(generated);
      } catch (err) {
        if (!active) return;
        setError(err.message || "Failed to generate quiz.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [token, userId]);

  const progressPercent = useMemo(() => {
    if (!quiz?.questions?.length) return 0;
    return Math.round(((currentQuestionIndex + 1) / quiz.questions.length) * 100);
  }, [quiz, currentQuestionIndex]);

  const onSelectOption = (option) => {
    if (!currentQuestion) return;
    setSelectedAnswers((prev) => ({ ...prev, [currentQuestion.id]: option }));
  };

  const onNext = () => {
    if (!quiz) return;
    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    }
  };

  const onSubmit = async () => {
    if (!token || !userId || !quiz) return;
    setSubmitting(true);
    setError("");
    try {
      const answers = quiz.questions
        .map((q) => ({ question_id: q.id, answer: selectedAnswers[q.id] }))
        .filter((q) => q.answer);

      const submit = await api.quizSubmit(token, quiz.quiz_id, {
        student_id: userId,
        answers,
        time_taken_seconds: Math.max(60, quiz.questions.length * 20),
      });
      localStorage.setItem(
        "mastery_quiz_last_attempt",
        JSON.stringify({
          quiz_id: quiz.quiz_id,
          attempt_id: submit.attempt_id,
          score: submit.score,
          xp_awarded: submit.xp_awarded,
        }),
      );
      navigate("/quiz-result");
    } catch (err) {
      setError(err.message || "Failed to submit quiz.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-slate-700">Generating quiz...</div>;
  }

  if (!quiz || !currentQuestion) {
    return (
      <div className="p-8 text-slate-700">
        {error || "Quiz is unavailable right now."}
      </div>
    );
  }

  return (
    <div className="flex bg-slate-50 h-[calc(100vh-64px)] overflow-hidden">
      <CourseSidebar
        activeStep="quiz"
        topics={sidebarTopics}
        selectedTopicId={selectedTopicId}
        masteryByTopic={masteryByTopic}
        onSelectTopic={(topicId) => {
          if (!topicId) return;
          localStorage.setItem("mastery_current_topic_id", topicId);
          navigate("/learning-path");
        }}
        moduleTitle={`${profile?.subjects?.[0]?.toUpperCase() || "LEARNING"} - ${profile?.sss_level || "SSS"}`}
      />

      <div className="flex-1 overflow-y-auto px-12 py-10 relative">
        <div className="max-w-3xl mx-auto">
          <div className="mb-10">
            <p className="text-[10px] font-bold text-indigo-600 uppercase tracking-widest mb-1">Mastery Challenge</p>
            <div className="flex justify-between items-end mb-4">
              <h1 className="text-3xl font-black text-slate-900 tracking-tight">Module Quiz</h1>
              <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                Question {currentQuestionIndex + 1} of {quiz.questions.length}
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-slate-200 overflow-hidden">
              <div className="h-full bg-indigo-600" style={{ width: `${progressPercent}%` }} />
            </div>
          </div>

          <div className="bg-white p-10 rounded-[2.5rem] shadow-xl border border-slate-100 mb-8">
            <div className="inline-block px-3 py-1 bg-indigo-50 text-indigo-600 text-[10px] font-bold uppercase tracking-widest rounded-full mb-6">
              {currentQuestion.difficulty}
            </div>
            <h2 className="text-2xl font-bold text-slate-900 mb-8 leading-snug">{currentQuestion.text}</h2>

            <div className="space-y-4 mb-10">
              {(currentQuestion.options || []).map((option) => (
                <button
                  key={option}
                  onClick={() => onSelectOption(option)}
                  className={`w-full text-left p-5 rounded-2xl border-2 transition-all flex items-center gap-4 ${
                    selectedAnswers[currentQuestion.id] === option ? "border-indigo-600 bg-indigo-50/30 shadow-md" : "border-slate-100 hover:border-slate-300 bg-white"
                  }`}
                >
                  <span className="font-semibold text-slate-700">{option}</span>
                </button>
              ))}
            </div>

            {error && <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">{error}</div>}

            <div className="flex justify-end items-center">
              <button
                onClick={isLastQuestion ? onSubmit : onNext}
                disabled={!canContinue || submitting}
                className={`px-8 py-3.5 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg ${
                  canContinue && !submitting ? "bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-200 transform hover:-translate-y-0.5" : "bg-slate-200 text-slate-400 cursor-not-allowed shadow-none"
                }`}
              >
                {submitting ? "Submitting..." : isLastQuestion ? "Submit Quiz" : "Next"}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="w-80 bg-white border-l border-slate-200 flex flex-col p-8 h-[calc(100vh-64px)] justify-between">
        <div className="flex flex-col items-center text-center mt-8">
          <div className="w-20 h-20 bg-indigo-50 rounded-3xl flex items-center justify-center text-4xl shadow-inner border border-indigo-100 mb-6">🤖</div>
          <h3 className="text-lg font-black text-slate-900 mb-3">Need a Hint?</h3>
          <p className="text-sm text-slate-500 leading-relaxed mb-8">Use the tutor hint endpoint from quiz actions if needed.</p>
        </div>
      </div>
    </div>
  );
};

export default ModuleQuizPage;
