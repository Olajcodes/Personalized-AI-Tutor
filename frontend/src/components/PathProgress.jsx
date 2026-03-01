import { Map } from 'lucide-react';

export default function PathProgress({ nextTopic }) {
  return (
    <div className="bg-[#1c2438] rounded-2xl p-6 border border-slate-700 mt-6">
      <div className="flex items-center gap-2 text-white font-bold mb-6">
        <Map className="w-5 h-5 text-slate-400" />
        Path Progress
      </div>
      
      <div className="bg-[#2a3447] rounded-xl p-6 flex justify-between items-center relative mb-4">
        {/* Connecting Line */}
        <div className="absolute top-1/2 left-8 right-8 h-0.5 bg-slate-600 -translate-y-1/2 z-0"></div>
        
        {/* Progress Nodes */}
        <div className="w-4 h-4 rounded-full bg-emerald-500 z-10 shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
        <div className="w-5 h-5 rounded-full bg-blue-500 border-4 border-[#2a3447] z-10 shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>
        <div className="w-4 h-4 rounded-full bg-slate-500 z-10"></div>
        <div className="w-4 h-4 rounded-full bg-slate-500 z-10"></div>
      </div>
      
      <div className="text-center">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Next Topic:</div>
        <div className="text-sm font-bold text-white uppercase">{nextTopic}</div>
      </div>
    </div>
  );
}