import React from 'react';

const AIExplanationArea = ({ explanationData }) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
      {/* Header */}
      <div className="bg-indigo-600 px-6 py-4 flex justify-between items-center">
        <h2 className="text-white font-bold text-xl flex items-center gap-2">
          <span>✨</span> Explain My Mistake
        </h2>
        <span className="bg-indigo-500/50 text-indigo-100 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
          AI Generated
        </span>
      </div>

      <div className="p-6 space-y-8">
        {/* Misconception */}
        <section>
          <h3 className="flex items-center gap-2 text-indigo-700 font-bold mb-3">
            <span>🧠</span> The Misconception
          </h3>
          <p className="text-slate-700 leading-relaxed">
            {explanationData.misconception}
          </p>
        </section>

        {/* Analogy Box */}
        <section className="bg-slate-50 rounded-xl p-5 border border-slate-100">
          <h4 className="flex items-center gap-2 text-indigo-700 font-bold mb-4">
            <span>💡</span> {explanationData.analogy.title}
          </h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="bg-slate-200 h-32 rounded-lg mb-2 flex items-center justify-center text-slate-400">
                [Pool Image]
              </div>
              <p className="text-xs text-slate-600">{explanationData.analogy.item1.label}</p>
            </div>
            <div className="text-center">
              <div className="bg-slate-200 h-32 rounded-lg mb-2 flex items-center justify-center text-slate-400">
                [Tea Image]
              </div>
              <p className="text-xs text-slate-600">{explanationData.analogy.item2.label}</p>
            </div>
          </div>
        </section>

        {/* Breakdown */}
        <section>
          <h3 className="flex items-center gap-2 text-slate-800 font-bold mb-4">
            <span>📑</span> Let's Break it Down
          </h3>
          <ul className="space-y-3">
            {explanationData.breakdown.map((item, idx) => (
              <li key={idx} className="flex gap-3 text-sm text-slate-700 leading-relaxed">
                <span className="text-indigo-400 mt-1">•</span>
                <span>
                  <strong className="text-indigo-600">{item.term}</strong> {item.definition}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
};

export default AIExplanationArea;