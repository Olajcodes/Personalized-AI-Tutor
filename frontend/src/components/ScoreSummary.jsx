import { CheckCircle } from 'lucide-react';

export default function ScoreSummary({ data }) {
  return (
    <div className="bg-linear-to-r from-blue-700 to-indigo-500 rounded-2xl p-8 text-white shadow-lg mb-8">
      <div className="flex items-center gap-2 text-emerald-300 text-xs font-bold uppercase tracking-wider mb-4">
        <CheckCircle className="w-4 h-4" />
        Mastery Achieved
      </div>
      
      <div className="flex items-start gap-6 mb-8">
        <div className="relative w-24 h-24 flex items-center justify-center shrink-0">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
            <path className="text-white/20" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
            <path className="text-emerald-400" strokeDasharray={`${(data.score / data.total) * 100}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
          </svg>
          <div className="absolute text-center">
            <span className="text-2xl font-bold">{data.score}/{data.total}</span>
            <span className="block text-[10px] font-medium text-white/80 uppercase tracking-wider">Score</span>
          </div>
        </div>
        
        <div>
          <h1 className="text-3xl font-bold mb-2">Excellent Work, {data.studentName}!</h1>
          <p className="text-blue-100 text-sm max-w-lg leading-relaxed">
            {data.message}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 border-t border-white/20 pt-6">
        <div>
          <div className="text-xs text-blue-200 font-bold uppercase tracking-wider mb-1">Time Taken</div>
          <div className="text-xl font-bold">{data.timeTaken}</div>
        </div>
        <div>
          <div className="text-xs text-blue-200 font-bold uppercase tracking-wider mb-1">Accuracy</div>
          <div className="text-xl font-bold text-emerald-300">{data.accuracy}%</div>
        </div>
        <div>
          <div className="text-xs text-blue-200 font-bold uppercase tracking-wider mb-1">XP Earned</div>
          <div className="text-xl font-bold text-amber-300">+{data.xpEarned} XP</div>
        </div>
      </div>
    </div>
  );
}