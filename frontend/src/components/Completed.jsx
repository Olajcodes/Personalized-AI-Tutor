import React, { useMemo } from "react";
import { useNavigate } from "react-router-dom";

function getResult() {
  try {
    return JSON.parse(localStorage.getItem("mastery_diagnostic_result") || "{}");
  } catch {
    return {};
  }
}

export default function CompletedPage() {
  const navigate = useNavigate();
  const result = useMemo(() => getResult(), []);
  const updates = Array.isArray(result.baseline_mastery_updates) ? result.baseline_mastery_updates : [];

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <header className="bg-white shadow-sm" style={{ borderTop: "4px solid #0EA5E9" }}>
        <div className="container mx-auto px-6 py-4 flex items-center gap-2">
          <div className="w-8 h-8 rounded flex items-center justify-center" style={{ backgroundColor: "#7F13EC" }}>
            <span className="text-white font-bold text-sm">M</span>
          </div>
          <span className="font-bold text-gray-900">MasteryAI</span>
        </div>
      </header>

      <div className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <p className="text-xs font-bold tracking-widest mb-2" style={{ color: "#7F13EC" }}>
              ASSESSMENT COMPLETE
            </p>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Your Baseline Mastery Is Ready</h1>
            <p className="text-gray-600 text-lg">
              Answered <strong>{result.answered || 0}</strong> of <strong>{result.total_questions || 0}</strong> diagnostic questions.
            </p>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl p-6 mb-8">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Mastery Updates</h3>
            {updates.length === 0 && <p className="text-slate-500 text-sm">No mastery updates were returned.</p>}
            <div className="space-y-3">
              {updates.map((item) => (
                <div key={item.concept_id} className="flex justify-between items-center p-3 rounded-xl bg-slate-50">
                  <div>
                    <div className="font-semibold text-slate-800">{item.concept_id}</div>
                    <div className="text-xs text-slate-500">
                      {Math.round(item.previous_score * 100)}% → {Math.round(item.new_score * 100)}%
                    </div>
                  </div>
                  <div className={`font-bold ${item.delta >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                    {item.delta >= 0 ? "+" : ""}
                    {Math.round(item.delta * 100)}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          {result.recommended_start_topic_id && (
            <div className="rounded-2xl p-6 mb-8 bg-indigo-50 border border-indigo-200">
              <p className="text-xs font-bold uppercase tracking-wider text-indigo-700 mb-2">Recommended Start Topic</p>
              <p className="font-semibold text-indigo-900 break-all">{result.recommended_start_topic_id}</p>
            </div>
          )}

          <div className="text-center">
            <button
              onClick={() => navigate("/dashboard")}
              type="button"
              className="text-white font-bold py-4 px-8 rounded-full text-lg transition-all hover:opacity-90 cursor-pointer"
              style={{ backgroundColor: "#7F13EC" }}
            >
              Continue to Dashboard →
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
