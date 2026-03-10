import React, { useState, useEffect } from 'react';
import { Star, Loader2, Trophy } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';

const LeaderboardItem = ({ rank, name, points, isCurrentUser }) => {
  const getRankColor = () => {
    if (rank === 1) return 'text-yellow-500';
    if (rank === 2) return 'text-slate-400';
    if (rank === 3) return 'text-amber-600';
    return 'text-indigo-600';
  };

  const getAvatarColor = () => {
    if (rank === 1) return 'bg-emerald-500';
    if (rank === 2) return 'bg-orange-500';
    if (rank === 3) return 'bg-indigo-400';
    return 'bg-slate-300';
  };

  return (
    <div className={`flex items-center justify-between p-3 rounded-2xl mb-2 transition-colors
      ${isCurrentUser ? 'bg-indigo-50 border border-indigo-100 shadow-sm' : 'hover:bg-slate-50 border border-transparent'}`}
    >
      <div className="flex items-center gap-4">
        <span className={`w-6 text-center font-bold ${getRankColor()}`}>
          {rank}
        </span>
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-200 to-slate-300 border-2 border-white shadow-sm overflow-hidden flex-shrink-0">
          <div className={`w-full h-full opacity-80 ${getAvatarColor()}`}></div>
        </div>
        <div className="flex flex-col">
          <span className="font-semibold text-slate-900 text-sm truncate max-w-[120px] sm:max-w-[180px]">
            {name} 
          </span>
          {isCurrentUser && <span className="text-[10px] font-bold text-indigo-500 uppercase tracking-wider">You</span>}
        </div>
      </div>
      <span className={`font-bold text-sm ${isCurrentUser ? 'text-indigo-700' : 'text-slate-600'}`}>
        {points.toLocaleString()} pts
      </span>
    </div>
  );
};

export default function Leaderboard({ leagueName = "Gold League" }) {
  const { token } = useAuth();
  const { userData, studentData } = useUser();
  const activeId = studentData?.user_id || studentData?.student_id || userData?.id;
  const apiUrl = import.meta.env.VITE_API_URL;

  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  console.log("Leaderboard Check:", { activeId, token, apiUrl });
  useEffect(() => {
    const fetchLeaderboard = async () => {
      if (!activeId || !token) return;

      try {
        // Hitting your exact endpoint with a limit of 5 students
        const response = await fetch(`${apiUrl}/students/leaderboard?limit=5`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error("Failed to fetch leaderboard");
        const data = await response.json();

        // 🎯 MAP THE API DATA TO YOUR UI PROPS
        const formattedData = data.map((item) => {
          const isMe = item.student_id === activeId;
          
          // Construct the name (Since backend lacks 'name' right now)
          let displayName = `Student ${item.student_id.substring(0, 4).toUpperCase()}`;
          if (isMe) {
            displayName = `${userData?.first_name || ''} ${userData?.last_name || ''}`.trim() || 'You';
          }

          return {
            id: item.student_id,
            rank: item.rank,
            points: item.total_mastery_points,
            name: displayName,
            isCurrentUser: isMe
          };
        });

        setItems(formattedData);
      } catch (err) {
        console.error("Leaderboard fetch error:", err);
        // Fallback demo data so your UI doesn't break during dev!
        setItems([
          { id: '1', rank: 1, name: "Sarah Jenkins", points: 4250, isCurrentUser: false },
          { id: '2', rank: 2, name: "Marcus Thorne", points: 3900, isCurrentUser: false },
          { id: activeId, rank: 3, name: `${userData?.first_name || 'You'}`, points: 3450, isCurrentUser: true },
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLeaderboard();
  }, [activeId, token, apiUrl, userData]);

  return (
    <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Star className="w-5 h-5 text-amber-500 fill-amber-500" />
          Class Leaderboard
        </h3>
        <span className="text-[10px] font-black text-amber-700 bg-amber-50 border border-amber-100 px-2 py-1 rounded-md uppercase tracking-wider">
          {leagueName}
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto pr-1">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-10 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin mb-3 text-indigo-400" />
            <p className="text-sm font-medium">Calculating ranks...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-slate-400 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            <Trophy className="w-8 h-8 mb-2 opacity-50 text-slate-400" />
            <p className="text-sm font-medium">No ranking data available yet.</p>
          </div>
        ) : (
          items.map((user, index) => (
            <LeaderboardItem 
              key={user.id || index} 
              rank={user.rank} 
              name={user.name} 
              points={user.points} 
              isCurrentUser={user.isCurrentUser} 
            />
          ))
        )}
      </div>
    </div>
  );
}