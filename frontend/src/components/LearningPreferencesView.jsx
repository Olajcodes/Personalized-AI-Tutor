import React, { useEffect, useState } from "react";

const DEPTH_OPTIONS = ["simple", "standard", "detailed"];
const PACE_OPTIONS = ["slow", "normal", "fast"];

const LearningPreferencesView = ({ preferences, onSave, saving }) => {
  const [form, setForm] = useState({
    explanation_depth: "standard",
    examples_first: false,
    pace: "normal",
  });

  useEffect(() => {
    setForm({
      explanation_depth: preferences?.explanation_depth || "standard",
      examples_first: Boolean(preferences?.examples_first),
      pace: preferences?.pace || "normal",
    });
  }, [preferences]);

  const submit = (e) => {
    e.preventDefault();
    onSave?.(form);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <div className="mb-8">
          <h2 className="text-xl font-bold text-slate-800">AI Tutor Personalization</h2>
          <p className="text-sm text-slate-500 mt-1">Configure how your tutor explains and paces content.</p>
        </div>

        <form onSubmit={submit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700">Explanation Depth</label>
            <select
              value={form.explanation_depth}
              onChange={(e) => setForm((prev) => ({ ...prev, explanation_depth: e.target.value }))}
              className="w-full border border-slate-300 rounded-lg px-4 py-2.5"
            >
              {DEPTH_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700">Pace</label>
            <select
              value={form.pace}
              onChange={(e) => setForm((prev) => ({ ...prev, pace: e.target.value }))}
              className="w-full border border-slate-300 rounded-lg px-4 py-2.5"
            >
              {PACE_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-3 text-sm font-semibold text-slate-700">
            <input
              type="checkbox"
              checked={form.examples_first}
              onChange={(e) => setForm((prev) => ({ ...prev, examples_first: e.target.checked }))}
              className="w-4 h-4"
            />
            Prefer examples before explanations
          </label>

          <div className="flex justify-end pt-2">
            <button type="submit" disabled={saving} className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-semibold py-2.5 px-6 rounded-lg transition-colors shadow-sm">
              {saving ? "Saving..." : "Save Preferences"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LearningPreferencesView;
