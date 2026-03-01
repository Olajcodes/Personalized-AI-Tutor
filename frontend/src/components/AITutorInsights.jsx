import { Lightbulb, Bot } from 'lucide-react';

export default function AITutorInsights({ insights }) {
  return (
    <div className="bg-[#1c2438] rounded-2xl overflow-hidden border border-slate-700 flex flex-col h-full">
      <div className="bg-blue-500 p-4 flex items-center gap-2 text-white font-bold">
        <Lightbulb className="w-5 h-5" />
        AI Tutor Insights
      </div>
      <div className="p-6 flex-1 space-y-6">
        
        {/* Chat bubble */}
        <div className="flex gap-3">
          <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0">
            <Bot className="w-4 h-4 text-blue-400" />
          </div>
          <div className="bg-[#2a3447] p-4 rounded-xl rounded-tl-none text-sm text-slate-300 leading-relaxed">
            {insights.greeting} However, I noticed you struggled with <strong>{insights.strugglePoints.join(" and ")}</strong>.
          </div>
        </div>

        {/* Key Insight Card */}
        <div className="bg-[#2a3447] rounded-xl p-4 border-l-4 border-orange-500">
          <div className="text-orange-500 text-xs font-bold uppercase tracking-wider mb-2">Key Insight</div>
          <p className="text-sm text-slate-300 leading-relaxed">
            {insights.keyInsight}
          </p>
        </div>

        {/* Prerequisite Check Card */}
        <div className="bg-[#2a3447] rounded-xl p-4 border-l-4 border-blue-500">
          <div className="text-blue-500 text-xs font-bold uppercase tracking-wider mb-2">Prerequisite Check</div>
          <p className="text-sm text-slate-300 leading-relaxed">
            {insights.prerequisite}
          </p>
        </div>

      </div>
    </div>
  );
}