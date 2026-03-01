import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import CourseSidebar from "../components/CourseSidebar";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

const LessonPage = () => {
  const navigate = useNavigate();
  const { token, userId } = useAuth();

  const [topics, setTopics] = useState([]);
  const [selectedTopicId, setSelectedTopicId] = useState(null);
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);
  const [isChatting, setIsChatting] = useState(false);

  const textBlocks = useMemo(
    () => (lesson?.content_blocks || []).filter((b) => b.type === "text"),
    [lesson],
  );

  useEffect(() => {
    let active = true;
    (async () => {
      if (!userId) return;
      setLoading(true);
      try {
        const profile = token ? await api.getProfile(token) : null;
        const subject = profile?.subjects?.[0] || "math";
        const term = profile?.current_term || 1;
        const topicList = await api.listTopics({ student_id: userId, subject, term });
        if (!active) return;
        setTopics(topicList || []);
        if (topicList?.length) {
          setSelectedTopicId(topicList[0].topic_id);
        } else {
          setError("No topics available for your profile yet.");
        }
      } catch (err) {
        if (!active) return;
        setError(err.message || "Failed to load topics.");
      } finally {
        if (active) setLoading(false);
      }
    })();

    return () => {
      active = false;
    };
  }, [token, userId]);

  useEffect(() => {
    let active = true;
    (async () => {
      if (!selectedTopicId || !userId) return;
      try {
        const payload = await api.getTopicLesson(selectedTopicId, userId);
        if (!active) return;
        setLesson(payload);
        localStorage.setItem("mastery_current_topic_id", selectedTopicId);
      } catch (err) {
        if (!active) return;
        setError(err.message || "Failed to load lesson content.");
      }
    })();
    return () => {
      active = false;
    };
  }, [selectedTopicId, userId]);

  useEffect(() => {
    let active = true;
    (async () => {
      if (!token || !userId || sessionId) return;
      try {
        const profile = await api.getProfile(token);
        const subject = profile?.subjects?.[0] || "math";
        const term = profile?.current_term || 1;
        const session = await api.startSession(token, { student_id: userId, subject, term });
        if (!active) return;
        setSessionId(session.session_id);
      } catch {
        // session creation failure should not block lesson rendering
      }
    })();
    return () => {
      active = false;
    };
  }, [token, userId, sessionId]);

  const sendTutorMessage = async () => {
    if (!token || !userId || !sessionId || !message.trim()) return;
    const text = message.trim();
    setMessage("");
    setChat((prev) => [...prev, { role: "student", content: text }]);
    setIsChatting(true);
    try {
      const profile = await api.getProfile(token);
      const response = await api.tutorChat(token, {
        student_id: userId,
        session_id: sessionId,
        subject: profile?.subjects?.[0] || "math",
        sss_level: profile?.sss_level || "SSS1",
        term: Number(profile?.current_term || 1),
        topic_id: selectedTopicId,
        message: text,
      });
      setChat((prev) => [...prev, { role: "assistant", content: response.assistant_message }]);
    } catch (err) {
      setChat((prev) => [...prev, { role: "assistant", content: `Tutor unavailable: ${err.message}` }]);
    } finally {
      setIsChatting(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-slate-700">Loading lesson...</div>;
  }

  return (
    <div className="flex bg-slate-50 h-[calc(100vh-64px)] overflow-hidden">
      <CourseSidebar activeStep="energy" />

      <div className="flex-1 overflow-y-auto px-12 py-8">
        <div className="max-w-3xl mx-auto">
          <div className="text-xs font-bold text-slate-400 mb-6 flex gap-2">
            <span>Courses</span> <span>›</span> <span>Learning Path</span> <span>›</span>{" "}
            <span className="text-slate-800">{lesson?.title || "Lesson"}</span>
          </div>

          {error && <div className="mb-6 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">{error}</div>}

          <div className="mb-6">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Topic</label>
            <select
              value={selectedTopicId || ""}
              onChange={(e) => setSelectedTopicId(e.target.value)}
              className="mt-2 w-full p-3 border border-slate-200 rounded-xl bg-white"
            >
              {topics.map((topic) => (
                <option key={topic.topic_id} value={topic.topic_id}>
                  {topic.title}
                </option>
              ))}
            </select>
          </div>

          <h1 className="text-4xl font-black text-slate-900 mb-8 tracking-tight">{lesson?.title || "Lesson"}</h1>

          <div className="prose prose-slate max-w-none">
            {textBlocks.length === 0 && <p className="text-slate-500">No text lesson blocks found for this topic.</p>}
            {textBlocks.map((block, idx) => (
              <p key={idx} className="text-slate-600 leading-relaxed mb-6">
                {typeof block.value === "string" ? block.value : JSON.stringify(block.value)}
              </p>
            ))}
          </div>

          <div className="flex justify-between items-center pt-8 border-t border-slate-200 pb-12">
            <button className="text-slate-500 font-bold hover:text-slate-800 transition-colors flex items-center gap-2">
              <span>←</span> Previous
            </button>
            <button
              onClick={() => navigate("/module-quiz")}
              className="bg-indigo-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200 flex items-center gap-2"
            >
              Take Mastery Quiz <span>→</span>
            </button>
          </div>
        </div>
      </div>

      <div className="w-80 bg-white border-l border-slate-200 flex flex-col h-[calc(100vh-64px)]">
        <div className="p-4 border-b border-slate-100 flex items-center gap-3 bg-indigo-50/50">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white text-sm shadow-md">🤖</div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">AI Tutor</h3>
            <p className="text-[10px] text-emerald-500 font-bold">SESSION {sessionId ? "ACTIVE" : "PENDING"}</p>
          </div>
        </div>

        <div className="flex-1 p-4 overflow-y-auto space-y-4 text-sm">
          {chat.length === 0 && (
            <div className="bg-slate-50 border border-slate-100 p-4 rounded-2xl text-slate-600">
              Ask questions about this lesson and I will explain with examples.
            </div>
          )}
          {chat.map((item, idx) => (
            <div
              key={`${item.role}-${idx}`}
              className={
                item.role === "student"
                  ? "bg-indigo-600 p-4 rounded-2xl rounded-tr-sm text-white shadow-md ml-4"
                  : "bg-slate-50 border border-slate-100 p-4 rounded-2xl rounded-tl-sm text-slate-600"
              }
            >
              {item.content}
            </div>
          ))}
          {isChatting && <div className="text-xs text-slate-400">Tutor is typing...</div>}
        </div>

        <div className="p-4 border-t border-slate-100 bg-white">
          <div className="relative">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") sendTutorMessage();
              }}
              placeholder="Ask a question about this topic..."
              className="w-full pl-4 pr-12 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent"
            />
            <button onClick={sendTutorMessage} className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-indigo-600 text-white rounded-lg flex items-center justify-center hover:bg-indigo-700 transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LessonPage;
