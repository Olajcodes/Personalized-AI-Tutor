import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';
import CourseSidebar from '../components/CourseSidebar';
import { PlayCircle, Clock, BookOpen } from 'lucide-react';

const CoursePage = () => {
  const { subject } = useParams(); 
  const navigate = useNavigate();
  
  const { token } = useAuth();
  const { studentData, userData } = useUser();
  const activeId = studentData?.user_id || userData?.id;
  const currentLevel = studentData?.sss_level || 'SSS1';
  const currentTerm = studentData?.current_term || 1;

  const [topics, setTopics] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const apiUrl = import.meta.env.VITE_API_URL || 'https://mastery-backend-7xe8.onrender.com/api/v1';

  useEffect(() => {
    if (!activeId || !token || !subject) return;

    const fetchTopicsList = async () => {
      setIsLoading(true);

      try {
        // Hitting the CORRECT endpoint for the course syllabus
        const queryParams = new URLSearchParams({
          student_id: activeId,
          subject: subject,
          term: currentTerm 
        });

        const response = await fetch(`${apiUrl}/learning/topics?${queryParams}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) throw new Error("Failed to fetch topics");

        // Inside the fetchTopicsList try block in CoursePage.jsx
const data = await response.json();
if (Array.isArray(data)) {
    setTopics(data);
    // Add this line:
    localStorage.setItem('active_subject', subject); 
}
        
        // if (Array.isArray(data)) {
        //     setTopics(data);
        // } else {
        //     setTopics([]);
        // }

      } catch (err) {
        console.error("CoursePage Error:", err);
        setTopics([]);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchTopicsList();
  }, [activeId, token, subject, currentTerm, apiUrl]);

  const safeTopics = Array.isArray(topics) ? topics : [];

  return (
    <div className="flex bg-slate-50 h-[calc(100vh-64px)] overflow-hidden">
      
      {/* Sidebar */}
      <CourseSidebar 
        activeStep={null} 
        subject={subject} 
        topics={safeTopics} 
        level={currentLevel}
      />
      
      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto px-8 py-10 lg:px-12">
        <div className="max-w-4xl mx-auto">
          
          <div className="mb-10">
            <h1 className="text-4xl font-black text-slate-900 mb-3 capitalize">{subject} Learning Path</h1>
            <p className="text-slate-500 text-lg">Follow this AI-curated syllabus to achieve mastery in {currentLevel} {subject}.</p>
          </div>

          {isLoading ? (
            <div className="space-y-4 animate-pulse">
               {[1,2,3,4].map(i => (
                 <div key={i} className="h-28 bg-white border border-slate-200 rounded-2xl w-full"></div>
               ))}
            </div>
          ) : safeTopics.length > 0 ? (
            <div className="space-y-4">
              {safeTopics.map((topic, index) => {
                
                // FIX IS HERE: We use topic.topic_id so it passes a valid UUID to the backend!
                const targetId = topic.topic_id || topic.id;

                return (
                  <div 
                    key={targetId || index} 
                    onClick={() => {
                        if (targetId) navigate(`/lesson/${targetId}`);
                    }}
                    className="p-6 rounded-2xl border-2 bg-white border-slate-200 cursor-pointer hover:border-indigo-300 hover:shadow-md transition-all group flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="flex items-start gap-5">
                      <div className="w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold bg-indigo-50 text-indigo-600 flex-shrink-0 mt-1 md:mt-0">
                          {index + 1}
                      </div>
                      <div>
                        {/* Now using the REAL title from the backend */}
                        <h3 className="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                            {topic.title || 'Untitled Topic'}
                        </h3>
                        {/* Using the REAL description */}
                        <p className="text-sm text-slate-500 mt-1 line-clamp-2 max-w-xl">
                            {topic.description || 'Dive into this module to expand your mastery.'}
                        </p>
                        
                        {/* Using the metadata from the backend */}
                        <div className="flex items-center gap-4 mt-3">
                           {topic.estimated_duration_minutes && (
                              <span className="flex items-center gap-1.5 text-xs font-bold text-slate-400">
                                 <Clock className="w-3.5 h-3.5" />
                                 ~{topic.estimated_duration_minutes} Mins
                              </span>
                           )}
                           {topic.lesson_title && (
                              <span className="flex items-center gap-1.5 text-xs font-bold text-slate-400 truncate max-w-[200px]">
                                 <BookOpen className="w-3.5 h-3.5" />
                                 {topic.lesson_title}
                              </span>
                           )}
                        </div>
                      </div>
                    </div>

                    <button className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-bold transition-colors bg-slate-100 text-slate-600 group-hover:bg-indigo-600 group-hover:text-white md:w-auto w-full">
                        Start Lesson <PlayCircle className="w-4 h-4" />
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
             <div className="text-center py-16 bg-white rounded-3xl border border-slate-200 shadow-sm">
                 <div className="w-20 h-20 bg-slate-50 text-slate-300 rounded-full flex items-center justify-center mx-auto mb-4">
                    <BookOpen className="w-10 h-10" />
                 </div>
                 <h3 className="text-xl font-bold text-slate-800 mb-2">No Topics Available</h3>
                 <p className="text-slate-500 max-w-md mx-auto">Your AI Tutor is still finalizing the syllabus for {currentLevel} {subject} Term {currentTerm}. Please check back soon!</p>
             </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CoursePage;