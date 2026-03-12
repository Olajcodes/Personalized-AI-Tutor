import { useMemo, useState, useRef, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import NotificationModal from './NotificationModal';
import { useUser } from '../context/UserContext';
import { readLatestGraphIntervention } from '../services/graphIntervention';

const Navbar = () => {
  const [showNotifications, setShowNotifications] = useState(false);
  const notifRef = useRef(null);
  const { userData, studentData } = useUser();
  const activeId = studentData?.user_id || studentData?.student_id || userData?.id;

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const displayName = userData
    ? `${userData.first_name || ''} ${userData.last_name || ''}`.trim()
    : 'Student';

  const displayLevel = studentData?.sss_level || 'Student';
  const displayLeague = studentData?.league_name || 'Current League';
  const avatarUrl = userData?.avatar_url || null;
  const latestIntervention = useMemo(
    () => (activeId ? readLatestGraphIntervention(activeId) : null),
    [activeId],
  );

  const getInitials = (name) => {
    if (!name || name === 'Student') return 'U';
    const nameParts = name.trim().split(' ');
    if (nameParts.length >= 2) {
      return `${nameParts[0][0]}${nameParts[nameParts.length - 1][0]}`.toUpperCase();
    }
    return nameParts[0][0].toUpperCase();
  };

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm w-full">
      <div className="max-w-9xl mx-auto px-6 py-3 flex items-center gap-6">
        <div className="flex-[3] flex items-center justify-between">
          <NavLink to="/dashboard" className="flex items-center gap-2 hover:opacity-80 transition-opacity flex-shrink-0">
            <div className="bg-indigo-600 p-1.5 rounded-lg text-white shadow-md">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <span className="text-xl font-black text-indigo-700 tracking-tight">MasteryAI</span>
          </NavLink>

          <div className="relative hidden lg:block w-72 flex-shrink-0">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            </span>
            <input
              type="text"
              placeholder="Search topics..."
              className="w-full bg-slate-50 border border-slate-200 rounded-full py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all shadow-inner"
            />
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center gap-6">
          <div className="relative" ref={notifRef}>
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className={`relative transition-colors ${showNotifications ? 'text-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
              {latestIntervention ? <span className="absolute top-0 right-1 w-2 h-2 bg-rose-500 rounded-full border border-white"></span> : null}
            </button>
            {showNotifications && <NotificationModal onClose={() => setShowNotifications(false)} />}
          </div>

          <div className="h-8 w-px bg-slate-200"></div>

          <NavLink to="/profile" className="flex items-center gap-3 group cursor-pointer flex-shrink-0">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-bold text-slate-800 group-hover:text-indigo-600 transition-colors">
                {displayName}
              </p>
              <p className="text-[10px] font-bold text-indigo-500 bg-indigo-50 px-2 py-0.5 rounded-full inline-block mt-0.5 uppercase tracking-wider">
                {displayLevel} • {displayLeague}
              </p>
            </div>

            <div className="w-10 h-10 rounded-full overflow-hidden border border-slate-200 bg-indigo-50 flex items-center justify-center flex-shrink-0 group-hover:border-indigo-300 transition-colors shadow-sm">
              {avatarUrl ? (
                <img src={avatarUrl} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                <span className="text-sm font-black text-indigo-600 tracking-widest">
                  {getInitials(displayName)}
                </span>
              )}
            </div>
          </NavLink>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
