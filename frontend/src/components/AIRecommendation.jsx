import { ChevronRight, Brain } from 'lucide-react';

export default function AIRecommendation({ 
  topic = "Linear Equations", 
  confidenceScore = 82, 
  nextConcept = "Coordinate Geometry" 
}) {
  return (
    <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 w-full lg:w-80 flex flex-col justify-between relative overflow-hidden">
      <div>
        <div className="flex items-center justify-between mb-4">
          <span className="bg-indigo-50 text-indigo-600 text-[10px] font-bold px-2 py-1 rounded uppercase tracking-wider">
            AI Recommended
          </span>
          <span className="text-xs text-gray-400">Updated 10mins ago</span>
        </div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Why you should study this next</p>
        <h3 className="text-lg font-bold text-gray-900 mb-2">{topic}</h3>
        
        <div className="inline-flex items-center gap-1.5 bg-yellow-50 text-yellow-700 text-xs px-2.5 py-1 rounded-md mb-3 font-medium">
          <div className="w-1.5 h-1.5 rounded-full bg-yellow-500"></div>
          Prerequisite gap identified
        </div>
        
        <p className="text-sm text-gray-500 leading-relaxed mb-6">
          Mastering this concept now will boost your confidence in <span className="font-semibold text-gray-700">{nextConcept}</span>.
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-gray-900">AI Confidence Score</span>
          <span className="text-xl font-bold text-indigo-600">{confidenceScore}%</span>
        </div>
        <div className="h-2 w-full bg-gray-100 rounded-full mb-4 overflow-hidden">
          <div className="h-full bg-indigo-600 rounded-full" style={{ width: `${confidenceScore}%` }}></div>
        </div>
        <button className="w-full bg-indigo-50 text-indigo-600 py-2.5 rounded-xl font-semibold text-sm hover:bg-indigo-100 transition-colors flex items-center justify-center gap-2 cursor-pointer">
          Start Topic <ChevronRight className="w-4 h-4" />
        </button>
      </div>
      <Brain className="absolute -right-4 top-4 w-24 h-24 text-gray-50 opacity-[0.03]" />
    </div>
  );
}