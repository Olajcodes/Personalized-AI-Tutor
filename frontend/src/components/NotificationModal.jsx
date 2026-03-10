import React from 'react';

const NotificationModal = ({ onClose }) => {
  return (
    <div className="absolute right-0 mt-4 w-80 bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
      {/* Header */}
      <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
        <h3 className="font-bold text-slate-800">Notifications</h3>
        <span className="text-[10px] font-bold text-indigo-700 bg-indigo-100 px-2 py-1 rounded-full uppercase tracking-wider">2 New</span>
      </div>
      
      {/* Notifications List */}
      <div className="max-h-[320px] overflow-y-auto">
        
        {/* Notification Item 1 */}
        <div 
          onClick={onClose} 
          className="p-4 border-b border-slate-50 hover:bg-slate-50 transition-colors cursor-pointer flex gap-3"
        >
          <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 flex-shrink-0 text-lg">🏆</div>
          <div>
            <p className="text-sm text-slate-800 font-bold">You leveled up!</p>
            <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">Amazing work! You've officially entered the Gold League.</p>
            <p className="text-[10px] text-slate-400 mt-2 font-bold uppercase tracking-widest">2 hours ago</p>
          </div>
        </div>

        {/* Notification Item 2 */}
        <div 
          onClick={onClose}
          className="p-4 border-b border-slate-50 hover:bg-slate-50 transition-colors cursor-pointer flex gap-3"
        >
          <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-600 flex-shrink-0 text-lg">⚠️</div>
          <div>
            <p className="text-sm text-slate-800 font-bold">Study Streak at Risk</p>
            <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">Complete one quick lesson today to keep your streak alive.</p>
            <p className="text-[10px] text-slate-400 mt-2 font-bold uppercase tracking-widest">5 hours ago</p>
          </div>
        </div>

        {/* Notification Item 3 (Read state) */}
        <div 
          onClick={onClose}
          className="p-4 hover:bg-slate-50 transition-colors cursor-pointer flex gap-3 opacity-60"
        >
          <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 flex-shrink-0 text-lg">🤖</div>
          <div>
            <p className="text-sm text-slate-800 font-bold">AI Tutor Insight</p>
            <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">Your personalized learning path for Fractions is ready.</p>
            <p className="text-[10px] text-slate-400 mt-2 font-bold uppercase tracking-widest">Yesterday</p>
          </div>
        </div>

      </div>

      {/* Footer */}
      <div className="p-3 text-center border-t border-slate-100 bg-slate-50/50">
        <button 
          onClick={onClose}
          className="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors"
        >
          Mark all as read
        </button>
      </div>
    </div>
  );
};

export default NotificationModal;