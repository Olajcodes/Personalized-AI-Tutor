import { Star } from 'lucide-react';

const LeaderboardItem = ({ rank, name, points, isCurrentUser }) => {
  const getRankColor = () => {
    if (rank === 1) return 'text-yellow-500';
    if (rank === 2) return 'text-gray-400';
    return 'text-indigo-600';
  };

  const getAvatarColor = () => {
    if (rank === 1) return 'bg-green-600';
    if (rank === 2) return 'bg-orange-600';
    return 'bg-gray-200';
  };

  return (
    <div className={`flex items-center justify-between p-3 rounded-2xl mb-2
      ${isCurrentUser ? 'bg-indigo-50 border border-indigo-100' : 'hover:bg-gray-50'}`}
    >
      <div className="flex items-center gap-4">
        <span className={`w-6 text-center font-bold ${getRankColor()}`}>
          {rank}
        </span>
        <div className="w-8 h-8 rounded-full bg-linear-to-br from-gray-200 to-gray-300 border-2 border-white shadow-sm overflow-hidden">
          <div className={`w-full h-full opacity-80 ${getAvatarColor()}`}></div>
        </div>
        <span className="font-semibold text-gray-900 text-sm">
          {name} {isCurrentUser && <span className="text-gray-500 font-normal">(You)</span>}
        </span>
      </div>
      <span className={`font-bold text-sm ${isCurrentUser ? 'text-indigo-600' : 'text-gray-600'}`}>
        {points} pts
      </span>
    </div>
  );
};

// Added `items` prop with an empty array as the default fallback
export default function Leaderboard({ items = [], leagueName = "Gold League" }) {
  return (
    <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <Star className="w-5 h-5 text-yellow-500" />
          Class Leaderboard
        </h3>
        <span className="text-xs font-bold text-yellow-700 bg-yellow-50 px-2 py-1 rounded-md">
          {leagueName}
        </span>
      </div>
      
      {/* Dynamic Mapping over the items prop */}
      <div className="flex flex-col">
        {items.map((user, index) => (
          <LeaderboardItem 
            key={user.id || index} 
            rank={user.rank || index + 1} 
            name={user.name} 
            points={user.points} 
            isCurrentUser={user.isCurrentUser} 
          />
        ))}

        {/* Fallback state if the API array is empty */}
        {items.length === 0 && (
          <div className="text-center w-full text-gray-400 text-sm py-4">
            Loading leaderboard...
          </div>
        )}
      </div>
    </div>
  );
}