import React from 'react';
import { analyticsData } from '../mocks/analyticsData';

const ConceptAnalyticsPage = () => {
  return (
    <main className="p-8">
      
      {/* Header Section */}
      <header className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Concept Analytics Hub</h1>
          <p className="text-slate-500 text-sm mt-1">Monitoring JSS3 Integrated Science - Term 2</p>
        </div>
        
        <div className="flex gap-4">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
            <input 
              type="text" 
              placeholder="Search students..." 
              className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 shadow-sm">
            <span>📥</span> Export Report
          </button>
        </div>
      </header>

      {/* Top Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard title="Class Mastery" stat={analyticsData.stats.classMastery} color="text-indigo-600" bg="bg-indigo-50" />
        <StatCard title="Concept Velocity" stat={analyticsData.stats.velocity} color="text-amber-600" bg="bg-amber-50" />
        <StatCard title="AI Interventions" stat={analyticsData.stats.interventions} color="text-purple-600" bg="bg-purple-50" />
      </div>

      {/* Main Split Content */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        
        {/* Left Column (Span 2) */}
        <div className="xl:col-span-2 space-y-8">
          
          {/* Heatmap Section */}
          <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-lg font-bold text-slate-800">Concept Dependency Heatmap</h2>
                <p className="text-xs text-slate-500">Visualizing mastery overlap across curriculum nodes</p>
              </div>
              <div className="flex bg-slate-100 p-1 rounded-lg">
                <button className="px-4 py-1.5 text-xs font-semibold bg-white shadow-sm rounded-md text-slate-800">By Student</button>
                <button className="px-4 py-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800">By Topic</button>
              </div>
            </div>
            <HeatmapTable data={analyticsData.heatmap} />
          </section>

          {/* Intervention Action Panel */}
          <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <span className="text-indigo-600 bg-indigo-50 p-2 rounded-lg">⚡</span>
              <h2 className="text-lg font-bold text-slate-800">Intervention Action Panel</h2>
            </div>
            <div className="space-y-4">
              {analyticsData.interventions.map(action => (
                <div key={action.id} className="flex items-center justify-between p-4 border border-slate-100 rounded-xl bg-slate-50/50">
                  <div className="flex items-center gap-4">
                    <span className={`text-xs font-bold px-3 py-1 rounded-full ${action.typeColor}`}>
                      {action.type}
                    </span>
                    <p className="text-sm font-medium text-slate-700">{action.target}</p>
                  </div>
                  <div className="flex gap-3">
                    <button className="px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-200 rounded-lg transition-colors">
                      {action.actionSecondary}
                    </button>
                    <button className="px-4 py-2 text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 rounded-lg shadow-sm transition-colors">
                      {action.actionPrimary}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Right Column (Span 1) */}
        <div className="space-y-6">
          
          {/* At-Risk Alerts */}
          <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <span className="text-rose-500">⚠️</span> At-Risk Alerts
              </h2>
              <span className="bg-rose-100 text-rose-700 text-xs font-bold px-2.5 py-0.5 rounded-full">3 URGENT</span>
            </div>
            
            <div className="space-y-4">
              {analyticsData.alerts.map(alert => (
                <div key={alert.id} className="border border-slate-100 rounded-xl p-4 shadow-sm">
                  <div className="flex items-center gap-3 mb-3">
                    <img src={alert.avatar} alt="" className="w-10 h-10 rounded-full" />
                    <div>
                      <h4 className="font-bold text-slate-800 text-sm">{alert.student}</h4>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${alert.tagColor}`}>
                        • {alert.tag}
                      </span>
                    </div>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 mb-4">
                    <p className="text-xs text-slate-500 font-bold mb-1 uppercase tracking-wider flex items-center gap-1">
                      <span>🤖</span> AI REASON
                    </p>
                    <p className="text-xs text-slate-700 leading-relaxed">{alert.reason}</p>
                  </div>
                  <button className="w-full py-2 bg-slate-900 text-white hover:bg-slate-800 rounded-lg text-sm font-semibold transition-colors">
                    {alert.actionText}
                  </button>
                </div>
              ))}
            </div>
          </section>

          {/* Curriculum Linkage */}
          <section className="bg-indigo-600 rounded-2xl shadow-md p-6 text-white relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-20 text-6xl">🔗</div>
            <h2 className="text-lg font-bold mb-4 relative z-10 flex items-center gap-2">
              <span>🔗</span> Curriculum Linkage
            </h2>
            <div className="bg-indigo-700/50 p-4 rounded-xl mb-4 relative z-10">
              <p className="text-sm text-indigo-50 leading-relaxed">
                Students failing <strong className="text-white">Photosynthesis</strong> are often missing <strong className="text-white">Solar Radiation</strong> mastery.
              </p>
            </div>
            <p className="text-xs font-bold text-indigo-200 uppercase tracking-wider mb-2 relative z-10">Suggested Action</p>
            <p className="text-sm font-medium mb-5 relative z-10">
              Conduct a 15-min bridge lab on light-waves before Chapter 4.
            </p>
            <button className="w-full py-2.5 bg-white text-indigo-700 hover:bg-indigo-50 rounded-lg text-sm font-bold shadow-sm transition-colors relative z-10">
              Add to Lesson Plan
            </button>
          </section>

        </div>
      </div>
    </main>
  );
};

/* --- Helper Sub-Components --- */

const StatCard = ({ title, stat, color, bg }) => (
  <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
    <h3 className="text-slate-500 text-sm font-semibold mb-2">{title}</h3>
    <div className="flex items-end justify-between">
      <div>
        <span className="text-3xl font-black text-slate-800">{stat.value}</span>
        <p className={`text-xs mt-2 font-medium ${stat.trend ? 'text-emerald-600' : 'text-slate-500'}`}>
          {stat.trend || stat.subtitle}
        </p>
      </div>
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${bg} ${color}`}>
        {stat.icon}
      </div>
    </div>
  </div>
);

const HeatmapTable = ({ data }) => {
  // Helper to color-code mastery scores
  const getScoreColor = (score) => {
    if (score === null) return 'bg-slate-100 text-slate-400 font-medium';
    if (score >= 85) return 'bg-emerald-500 text-white font-bold';
    if (score >= 70) return 'bg-amber-400 text-white font-bold';
    if (score >= 40) return 'bg-orange-400 text-white font-bold';
    return 'bg-rose-500 text-white font-bold';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-separate border-spacing-y-3">
        <thead>
          <tr>
            <th className="text-[10px] font-bold text-slate-400 uppercase tracking-wider w-1/4 pb-2">Concept / Prereq</th>
            {data.concepts.map((concept, idx) => (
              <th key={idx} className="text-[10px] font-bold text-slate-400 uppercase tracking-wider text-center w-32 pb-2 px-2 leading-tight">
                {concept}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.students.map((student) => (
            <tr key={student.id}>
              <td className="text-sm font-bold text-slate-700 py-2">{student.name}</td>
              {student.scores.map((score, idx) => (
                <td key={idx} className="px-1">
                  <div className={`h-10 w-full rounded flex items-center justify-center text-sm transition-transform hover:scale-105 cursor-pointer ${getScoreColor(score)}`}>
                    {score !== null ? `${score}%` : '--'}
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      
      {/* Legend */}
      <div className="flex justify-end items-center gap-4 mt-4 pt-4 border-t border-slate-100">
        <span className="text-xs text-slate-500 font-semibold">CRITICAL (&lt;40%)</span>
        <div className="flex gap-1">
          <div className="w-4 h-4 rounded bg-rose-500"></div>
          <div className="w-4 h-4 rounded bg-orange-400"></div>
          <div className="w-4 h-4 rounded bg-amber-400"></div>
          <div className="w-4 h-4 rounded bg-emerald-500"></div>
        </div>
        <span className="text-xs text-slate-500 font-semibold">MASTERED (&gt;85%)</span>
      </div>
    </div>
  );
};

export default ConceptAnalyticsPage;