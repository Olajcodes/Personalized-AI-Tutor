import React, { useState, useEffect } from 'react';
import { Calendar, Loader2, Inbox } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';

const TaskItem = ({ dateMonth, dateDay, title, subtext, buttonText, buttonVariant }) => {
  const isUrgent = subtext?.toLowerCase().includes('tomorrow') || subtext?.toLowerCase().includes('today');
  
  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-2xl mb-3 hover:bg-gray-100 transition-colors group">
      <div className="flex items-center gap-4">
        <div className="bg-white border border-gray-100 w-12 h-12 rounded-xl flex flex-col items-center justify-center shadow-sm group-hover:border-indigo-100 transition-colors">
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
      <button className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all
        ${buttonVariant === 'outline' 
          ? 'border border-gray-200 text-gray-700 hover:bg-indigo-600 hover:text-white hover:border-indigo-600 bg-white shadow-sm' 
          : 'bg-white shadow-sm text-gray-900 border border-gray-100 hover:bg-gray-50'}`}
      >
        {buttonText}
      </button>
    </div>
  );
};

export default function LearningTasks() {
  const { token } = useAuth();
  const { userData, studentData } = useUser();
  const activeId = studentData?.user_id || userData?.id;
  const apiUrl = import.meta.env.VITE_API_URL;

  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchTasks = async () => {
      if (!activeId || !token) return;

      try {
        const response = await fetch(`${apiUrl}/learning/tasks?student_id=${activeId}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) throw new Error("Failed to fetch tasks");
        const data = await response.json();
        
        // Ensure we handle different possible API response structures
        setTasks(data.tasks || data);
      } catch (err) {
        console.error("Task fetch error:", err);
        // Optional: Keep static data as fallback if the API fails
        setTasks([
          { id: 1, month: "Oct", day: "24", title: "Basic Algebra Quiz", subtext: "Due Tomorrow • 10:00 AM", btn: "Review" },
          { id: 2, month: "Oct", day: "27", title: "Oral English Exercise", subtext: "In 3 days • Speaking Practice", btn: "Open" }
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTasks();
  }, [activeId, token, apiUrl]);

  return (
    <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100 flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-indigo-600" />
          Learning Tasks
        </h3>
        <button className="text-sm font-bold text-indigo-600 hover:text-indigo-700 transition-colors">View All</button>
      </div>

      <div className="flex-1 overflow-y-auto pr-1">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-12 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin mb-2" />
            <p className="text-sm font-medium">Loading your schedule...</p>
          </div>
        ) : tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-slate-400 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            <Inbox className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-sm font-medium">All caught up! No tasks found.</p>
          </div>
        ) : (
          tasks.map((task) => (
            <TaskItem 
              key={task.id}
              dateMonth={task.month} 
              dateDay={task.day}
              title={task.title}
              subtext={task.subtext}
              buttonText={task.btn || "Open"} 
              buttonVariant="outline"
            />
          ))
        )}
      </div>
    </div>
  );
}