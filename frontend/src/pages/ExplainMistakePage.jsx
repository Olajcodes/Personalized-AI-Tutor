import React, { useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

const ExplainMistakePage = () => {
  const { token, userId } = useAuth();
  const [form, setForm] = useState({
    subject: "math",
    sss_level: "SSS1",
    term: 1,
    question: "",
    student_answer: "",
    correct_answer: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    if (!token || !userId) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await api.tutorExplainMistake(token, {
        student_id: userId,
        subject: form.subject,
        sss_level: form.sss_level,
        term: Number(form.term),
        topic_id: localStorage.getItem("mastery_current_topic_id"),
        question: form.question,
        student_answer: form.student_answer,
        correct_answer: form.correct_answer,
      });
      setResult(response);
    } catch (err) {
      setError(err.message || "Unable to explain mistake.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl border border-slate-200 p-8">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">Explain My Mistake</h1>
          <p className="text-slate-600 text-sm mb-6">Paste a question and your answer to get AI remediation.</p>

          <form className="space-y-4" onSubmit={submit}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <select value={form.subject} onChange={(e) => setForm((p) => ({ ...p, subject: e.target.value }))} className="border border-slate-300 rounded-lg px-3 py-2">
                <option value="math">math</option>
                <option value="english">english</option>
                <option value="civic">civic</option>
              </select>
              <select value={form.sss_level} onChange={(e) => setForm((p) => ({ ...p, sss_level: e.target.value }))} className="border border-slate-300 rounded-lg px-3 py-2">
                <option value="SSS1">SSS1</option>
                <option value="SSS2">SSS2</option>
                <option value="SSS3">SSS3</option>
              </select>
              <select value={form.term} onChange={(e) => setForm((p) => ({ ...p, term: Number(e.target.value) }))} className="border border-slate-300 rounded-lg px-3 py-2">
                <option value={1}>Term 1</option>
                <option value={2}>Term 2</option>
                <option value={3}>Term 3</option>
              </select>
            </div>
            <textarea placeholder="Question" value={form.question} onChange={(e) => setForm((p) => ({ ...p, question: e.target.value }))} className="w-full h-24 border border-slate-300 rounded-lg px-3 py-2" required />
            <input placeholder="Your Answer" value={form.student_answer} onChange={(e) => setForm((p) => ({ ...p, student_answer: e.target.value }))} className="w-full border border-slate-300 rounded-lg px-3 py-2" required />
            <input placeholder="Correct Answer" value={form.correct_answer} onChange={(e) => setForm((p) => ({ ...p, correct_answer: e.target.value }))} className="w-full border border-slate-300 rounded-lg px-3 py-2" required />
            <button disabled={loading} className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg font-semibold">
              {loading ? "Explaining..." : "Explain"}
            </button>
          </form>

          {error && <div className="mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">{error}</div>}

          {result && (
            <div className="mt-6 space-y-4">
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                <h3 className="font-bold text-slate-900 mb-2">Explanation</h3>
                <p className="text-slate-700">{result.explanation}</p>
              </div>
              <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
                <h3 className="font-bold text-indigo-900 mb-2">Improvement Tip</h3>
                <p className="text-indigo-800">{result.improvement_tip}</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ExplainMistakePage;
