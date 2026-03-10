import React from 'react';
import { NavLink } from 'react-router-dom';

const TeacherSidebar = () => {
  const menuItems = [
    { id: 'overview', icon: '📊', label: 'Overview', path: '/teacher/overview' },
    { id: 'analytics', icon: '📈', label: 'Concept Analytics', path: '/teacher/analytics' },
    { id: 'classes', icon: '👥', label: 'My Classes', path: '/teacher/classes' },
    { id: 'settings', icon: '⚙️', label: 'AI Tutor Settings', path: '/teacher/settings' },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 h-screen flex flex-col sticky top-0">
      {/* Logo Area */}
      <div className="p-6 flex items-center gap-3 border-b border-slate-100">
        <div className="bg-indigo-600 p-1.5 rounded-lg text-white">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </div>
        <span className="text-xl font-bold text-indigo-900 tracking-tight">MasteryAI</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => (
          <NavLink
            key={item.id}
            to={item.path}
            className={({ isActive }) => 
              `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                isActive 
                  ? 'bg-indigo-50 text-indigo-700' 
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`
            }
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* User Profile */}
      <div className="p-4 border-t border-slate-100 flex items-center gap-3 hover:bg-slate-50 cursor-pointer transition-colors m-2 rounded-xl">
        <img src="https://i.pravatar.cc/150?img=47" alt="Teacher" className="w-10 h-10 rounded-full border border-slate-200" />
        <div>
          <p className="text-sm font-bold text-slate-800 leading-tight">Sarah Jenkins</p>
          <p className="text-xs text-slate-500">JSS3 Science Lead</p>
        </div>
      </div>
    </aside>
  );
};

export default TeacherSidebar;