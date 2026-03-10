import { CheckCircle2, Brain, Lock } from 'lucide-react';

const MapNode = ({ status, title, details, isLast }) => {
  const isMastered = status === 'mastered';
  const isCurrent = status === 'current';
  
  return (
    // FIX 1: Replaced `flex-1` with `min-w-[160px] shrink-0 snap-center`
    // This forces the node to take up space, creating the horizontal scroll
    <div className="flex flex-col items-center relative min-w-[160px] shrink-0 snap-center">
      
      {/* Connecting Line - Stays perfect because of left-[50%] and w-full */}
      {!isLast && (
        <div className={`absolute top-6 left-[50%] w-full h-1 ${
          isMastered || isCurrent ? 'bg-green-500' : 'bg-gray-100'
        }`}></div>
      )}
      
      <div className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full border-4 bg-white
        ${isMastered ? 'border-green-500 bg-green-500 text-white' : 
          isCurrent ? 'border-indigo-600 bg-orange-50 text-orange-500 shadow-[0_0_0_4px_rgba(79,70,229,0.1)]' : 
          'border-gray-100 bg-gray-50 text-gray-300'}
      `}>
        {isMastered && <CheckCircle2 className="w-6 h-6" />}
        {isCurrent && <Brain className="w-6 h-6" />}
        {!isMastered && !isCurrent && <Lock className="w-5 h-5" />}
        
        {isCurrent && (
          <div className="absolute -top-8 bg-indigo-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide">
            Current
          </div>
        )}
      </div>

      <div className="text-center mt-4 px-2">
        <h4 className={`text-sm font-bold ${isCurrent ? 'text-gray-900' : 'text-gray-500'}`}>{title}</h4>
        <div className="mt-1">
          {isMastered && <span className="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded-sm">100% MASTERY</span>}
          {isCurrent && <span className="text-[10px] font-bold text-orange-600 bg-orange-50 px-2 py-0.5 rounded-sm">{details}</span>}
          {!isMastered && !isCurrent && <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wide">Locked</span>}
        </div>
      </div>
    </div>
  );
};

export default function LearningMap({ classLevel = "SSS 2", subject = "Mathematics", nodes = [] }) {
  return (
    <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 mb-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-12">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Your Learning Map</h2>
          <p className="text-sm text-gray-500">{classLevel} {subject} • Visual path through your curriculum</p>
        </div>
        <div className="bg-gray-50 p-1 rounded-full flex text-sm font-medium border border-gray-100 self-start md:self-auto">
          <button className="bg-white shadow-sm px-4 py-1.5 rounded-full text-gray-900">Concept View</button>
          <button className="px-4 py-1.5 text-gray-500 hover:text-gray-700">Curriculum List</button>
        </div>
      </div>

      {/* FIX 2: Added overflow-x-auto, flex-nowrap, and custom padding for the scrollbar */}
      {/* Added snap-x so scrolling feels smooth on mobile devices */}
      <div className="flex flex-nowrap overflow-x-auto pb-8 pt-4 px-2 mb-4 snap-x scroll-smooth custom-scrollbar">
        
        {nodes.map((node, index) => (
          <MapNode 
            key={node.id || index} 
            status={node.status} 
            title={node.title} 
            details={node.details} 
            isLast={index === nodes.length - 1} 
          />
        ))}
        
        {nodes.length === 0 && (
          <div className="text-center w-full text-gray-400 text-sm py-4">Loading map data...</div>
        )}
      </div>

      <div className="flex flex-wrap justify-center gap-4 md:gap-8 border-t border-gray-50 pt-6">
          <div className="flex items-center gap-2 text-xs font-medium text-gray-500">
              <div className="w-2 h-2 rounded-full bg-green-500"></div> Mastered
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-gray-500">
              <div className="w-2 h-2 rounded-full bg-orange-500"></div> Practice Needed
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-gray-500">
              <div className="w-2 h-2 rounded-full bg-indigo-600"></div> Current Focus
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-gray-500">
              <div className="w-2 h-2 rounded-full bg-gray-200"></div> Locked
          </div>
      </div>
    </div>
  );
}