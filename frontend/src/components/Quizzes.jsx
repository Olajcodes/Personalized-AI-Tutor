import React, { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

function loadDiagnostic() {
  try {
    const raw = localStorage.getItem("mastery_diagnostic");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export default function Quizzes() {
  const navigate = useNavigate();
  const { quizId } = useParams();
  const { token, userId } = useAuth();

  const diagnostic = useMemo(() => loadDiagnostic(), []);
  const questions = diagnostic?.questions || [];

  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (!quizId || !diagnostic || String(diagnostic?.diagnostic_id) !== String(quizId)) {
    return (
      <main className="min-h-screen bg-[#F3F0FF] flex items-center justify-center p-6">
        <div className="max-w-xl bg-white border border-slate-200 rounded-2xl p-8 text-center">
          <h2 className="text-2xl font-bold text-slate-900 mb-3">Diagnostic Session Missing</h2>
          <p className="text-slate-600 mb-6">Start from onboarding to generate a valid diagnostic session.</p>
          <button onClick={() => navigate("/AssessmentSplash")} className="px-6 py-3 rounded-xl bg-[#7F13EC] text-white font-bold">
            Go To Assessment
          </button>
        </div>
      </main>
    );
  }

  if (!questions.length) {
    return (
      <main className="min-h-screen bg-[#F3F0FF] flex items-center justify-center">
        <div className="text-slate-700 font-semibold">No diagnostic questions were returned.</div>
      </main>
    );
  }

  const question = questions[currentQuestion];
  const progress = ((currentQuestion + 1) / questions.length) * 100;
  const isLastQuestion = currentQuestion === questions.length - 1;
  const isAnswered = selectedAnswers[currentQuestion] !== undefined;

  const handleSelectOption = (optionValue) => {
    setSelectedAnswers((prev) => ({ ...prev, [currentQuestion]: optionValue }));
    setError("");
  };

  const handleNext = () => {
    if (!isLastQuestion) setCurrentQuestion((prev) => prev + 1);
  };

  const handleSubmit = async () => {
    if (!token || !userId) {
      setError("Authentication missing. Please login again.");
      return;
    }
    setIsSubmitting(true);
    setError("");
    try {
      const answers = questions
        .map((q, idx) => ({
          question_id: q.question_id,
          answer: selectedAnswers[idx],
        }))
        .filter((a) => a.answer);

      const result = await api.diagnosticSubmit(token, {
        diagnostic_id: diagnostic.diagnostic_id,
        student_id: userId,
        answers,
      });

      localStorage.setItem(
        "mastery_diagnostic_result",
        JSON.stringify({
          ...result,
          total_questions: questions.length,
          answered: answers.length,
        }),
      );
      navigate(`/quiz/${quizId}/completed`);
    } catch (err) {
      setError(err.message || "Failed to submit diagnostic.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#F3F0FF]">
      <header className="bg-white border-b-2 shadow-sm" style={{ borderColor: "#7F13EC" }}>
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded flex items-center justify-center" style={{ backgroundColor: "#7F13EC" }}>
              <span className="text-white font-bold text-sm">M</span>
            </div>
            <span className="font-bold text-gray-900">MasteryAI</span>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-sm text-gray-600">
              Question <span className="font-semibold">{currentQuestion + 1} of {questions.length}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full transition-all duration-300" style={{ backgroundColor: "#7F13EC", width: `${progress}%` }} />
              </div>
              <div className="text-sm font-semibold text-gray-900 w-12 text-right">{Math.round(progress)}%</div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-12">
        <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-lg p-10 md:p-16" style={{ border: "2px solid #7F13EC" }}>
          <div className="text-center mb-8">
            <span className="text-xs font-bold tracking-widest uppercase" style={{ color: "#7F13EC" }}>
              {diagnostic.subject?.toUpperCase()} DIAGNOSTIC
            </span>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 text-center mb-10">{question.prompt}</h2>

          <div className="grid grid-cols-1 gap-4 mb-10">
            {question.options.map((option, idx) => (
              <button
                key={`${question.question_id}-${idx}`}
                onClick={() => handleSelectOption(option)}
                className="p-6 rounded-2xl border-2 text-left transition-all duration-200"
                style={{
                  borderColor: selectedAnswers[currentQuestion] === option ? "#7F13EC" : "#E5E7EB",
                  backgroundColor: selectedAnswers[currentQuestion] === option ? "#F3F0FF" : "#FFFFFF",
                }}
              >
                <div className="flex items-start gap-4">
                  <div
                    className="w-6 h-6 rounded-full border-2 mt-1 flex items-center justify-center flex-shrink-0"
                    style={{
                      borderColor: selectedAnswers[currentQuestion] === option ? "#7F13EC" : "#D1D5DB",
                      backgroundColor: selectedAnswers[currentQuestion] === option ? "#7F13EC" : "#FFFFFF",
                    }}
                  >
                    {selectedAnswers[currentQuestion] === option && <div className="w-2 h-2 bg-white rounded-full" />}
                  </div>
                  <div className="text-lg font-semibold text-gray-900">{option}</div>
                </div>
              </button>
            ))}
          </div>

          {error && <div className="mb-6 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">{error}</div>}

          <div className="flex items-center justify-end pt-6 border-t border-gray-200">
            <button
              onClick={isLastQuestion ? handleSubmit : handleNext}
              disabled={!isAnswered || isSubmitting}
              className="px-8 py-3 rounded-full font-semibold transition-all"
              style={{
                backgroundColor: !isAnswered || isSubmitting ? "#D1D5DB" : "#7F13EC",
                color: !isAnswered || isSubmitting ? "#9CA3AF" : "#FFFFFF",
                cursor: !isAnswered || isSubmitting ? "not-allowed" : "pointer",
              }}
            >
              {isSubmitting ? "Submitting..." : isLastQuestion ? "Submit Answers →" : "Next →"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
