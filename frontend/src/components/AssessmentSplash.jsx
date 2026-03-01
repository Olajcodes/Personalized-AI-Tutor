import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

const AssessmentSplash = () => {
  const navigate = useNavigate();
  const { token, userId } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const overviewItems = [
    { icon: "🔢", title: "8-12 Quick Questions", desc: "Takes about 5-10 minutes" },
    { icon: "📋", title: "No Grades, Just Insights", desc: "Focus on what to improve" },
    { icon: "🗺️", title: "Builds Your Map", desc: "Creates your personalized path" },
  ];

  const handleStartAssessment = async () => {
    if (!token || !userId) {
      setError("Authentication missing. Please login again.");
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      const profile = await api.getProfile(token);
      const subject = profile?.subjects?.[0] || "math";
      const sssLevel = profile?.sss_level || "SSS1";
      const term = Number(profile?.current_term || 1);

      const diagnostic = await api.diagnosticStart(token, {
        student_id: userId,
        subject,
        sss_level: sssLevel,
        term,
      });

      localStorage.setItem(
        "mastery_diagnostic",
        JSON.stringify({
          ...diagnostic,
          subject,
          sss_level: sssLevel,
          term,
          student_id: userId,
        }),
      );
      navigate(`/quiz/${diagnostic.diagnostic_id}`);
    } catch (err) {
      setError(err.message || "Failed to start diagnostic.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen font-sans p-8 flex flex-col" style={{ backgroundColor: "#F9FAFB" }}>
      <div className="flex items-center gap-2 mb-12">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold shadow-md" style={{ backgroundColor: "#5850EC" }}>
          <span className="text-xs">🧠</span>
        </div>
        <span className="text-xl font-bold tracking-tight" style={{ color: "#5850EC" }}>
          MasteryAI
        </span>
      </div>

      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-16 mt-10">
        <div className="flex-1 space-y-8">
          <div className="space-y-4">
            <h1 className="text-6xl font-black leading-tight" style={{ color: "#111827" }}>
              Let's See <br />
              What You <br />
              <span style={{ color: "#5850EC" }}>Already Know</span>
            </h1>
            <p className="text-lg max-w-md" style={{ color: "#4F566B" }}>
              This short assessment helps MasteryAI create your personalized learning path by identifying strengths and gaps.
            </p>
          </div>
        </div>

        <div className="w-full max-w-md bg-white p-10 rounded-[2.5rem] shadow-xl border border-slate-50">
          <h2 className="text-xl font-extrabold mb-8" style={{ color: "#111827" }}>
            Assessment Overview
          </h2>

          <div className="space-y-8 mb-10">
            {overviewItems.map((item, index) => (
              <div key={index} className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: "#EEF2FF" }}>
                  {item.icon}
                </div>
                <div>
                  <h3 className="font-bold text-sm" style={{ color: "#111827" }}>
                    {item.title}
                  </h3>
                  <p className="text-xs" style={{ color: "#6B7280" }}>
                    {item.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {error && <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">{error}</div>}

          <button
            onClick={handleStartAssessment}
            disabled={isLoading}
            className="w-full py-4 text-white font-bold rounded-2xl shadow-lg transition-all transform active:scale-95 flex items-center justify-center gap-2 mb-4"
            style={{
              backgroundColor: isLoading ? "#A3ACBF" : "#5850EC",
              boxShadow: isLoading ? "none" : "0 10px 15px -3px rgba(88, 80, 236, 0.3)",
              cursor: isLoading ? "wait" : "pointer",
            }}
          >
            {isLoading ? "Preparing..." : "Start Assessment"} <span>→</span>
          </button>

          <button onClick={() => navigate("/dashboard")} disabled={isLoading} className="w-full py-2 text-sm font-bold transition-colors hover:opacity-70 disabled:opacity-50" style={{ color: "#9CA3AF" }}>
            Skip for now
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssessmentSplash;
