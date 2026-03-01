import React from 'react';
import { Calendar } from 'lucide-react';

const TaskItem = ({ dateMonth, dateDay, title, subtext, buttonText, buttonVariant }) => {
  const isUrgent = subtext.toLowerCase().includes('tomorrow');
  
  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-2xl mb-3">
      <div className="flex items-center gap-4">
        <div className="bg-white border border-gray-100 w-12 h-12 rounded-xl flex flex-col items-center justify-center shadow-sm">
          <span className="text-[10px] font-bold text-indigo-600 uppercase">{dateMonth}</span>
          <span className="text-lg font-bold text-gray-900 leading-none">{dateDay}</span>
        </div>
        <div>
          <h4 className="font-bold text-gray-900">{title}</h4>
          <p className={`text-xs font-medium ${isUrgent ? 'text-red-500' : 'text-gray-500'}`}>
            {subtext}
          </p>
        </div>
      </div>
      <button className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-colors
        ${buttonVariant === 'outline' 
          ? 'border border-gray-200 text-gray-700 hover:bg-gray-100 bg-white shadow-sm' 
          : 'bg-white shadow-sm text-gray-900 border border-gray-100 hover:bg-gray-50'}`}
      >
        {buttonText}
      </button>
    </div>
  );
};

export default function LearningTasks() {
  return (
    <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-indigo-600" />
          Learning Tasks
        </h3>
        <a href="#" className="text-sm font-bold text-indigo-600 hover:text-indigo-700">View All</a>
      </div>
      <TaskItem 
        dateMonth="Oct" dateDay="24"
        title="Basic Algebra Quiz"
        subtext="Due Tomorrow • 10:00 AM"
        buttonText="Review" buttonVariant="outline"
      />
      <TaskItem 
        dateMonth="Oct" dateDay="27"
        title="Oral English Exercise"
        subtext="In 3 days • Speaking Practice"
        buttonText="Open" buttonVariant="outline"
      />
    </div>
  );
}