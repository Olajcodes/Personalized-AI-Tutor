import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import CourseSidebar from "../components/CourseSidebar";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

const buildSessionStorageKey = (userId, subject, term) =>
  `mastery_tutor_session:${userId}:${subject}:term${term}`;

const mapMasteryPayload = (payload) => {
  const result = {};
  for (const item of payload?.mastery || []) {
    const id = item?.topic_id || item?.concept_id;
    if (!id) continue;
    const score = Number(item?.score);
    result[id] = Number.isFinite(score) ? Math.max(0, Math.min(1, score)) : 0;
  }
  return result;
};

const mapHistory = (messages) =>
  (messages || []).map((item) => ({
    role: item.role === "assistant" ? "assistant" : "student",
    content: item.content,
    createdAt: item.created_at || null,
    citations: [],
  }));

const LessonPage = () => {
  const navigate = useNavigate();
  const { token, userId } = useAuth();

  const [profile, setProfile] = useState(null);
  const [topics, setTopics] = useState([]);
  const [masteryByTopic, setMasteryByTopic] = useState({});
  const [selectedTopicId, setSelectedTopicId] = useState(null);
  const [lesson, setLesson] = useState(null);

  const [loading, setLoading] = useState(true);
  const [lessonLoading, setLessonLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [error, setError] = useState("");

  const [sessionId, setSessionId] = useState(null);
  const [chat, setChat] = useState([]);
  const [message, setMessage] = useState("");
  const [isChatting, setIsChatting] = useState(false);

  const scope = useMemo(() => {
    if (!profile) return null;
    return {
      subject: profile.subjects?.[0] || "math",
      term: Number(profile.current_term || 1),
      sssLevel: profile.sss_level || "SSS1",
    };
  }, [profile]);

  const topicIndex = useMemo(
    () => topics.findIndex((item) => item.topic_id === selectedTopicId),
    [topics, selectedTopicId],
  );

  const textBlocks = useMemo(
    () => (lesson?.content_blocks || []).filter((block) => block.type === "text"),
    [lesson],
  );
  const exampleBlocks = useMemo(
    () => (lesson?.content_blocks || []).filter((block) => block.type === "example"),
    [lesson],
  );
  const exerciseBlocks = useMemo(
    () => (lesson?.content_blocks || []).filter((block) => block.type === "exercise"),
    [lesson],
  );
  const mediaBlocks = useMemo(
    () => (lesson?.content_blocks || []).filter((block) => block.type === "video" || block.type === "image"),
    [lesson],
  );

  useEffect(() => {
    let active = true;
    (async () => {
      if (!token || !userId) return;
      setLoading(true);
      setError("");

      try {
        const profilePayload = await api.getProfile(token);
        if (!active) return;
        setProfile(profilePayload);

        const subject = profilePayload?.subjects?.[0] || "math";
        const term = Number(profilePayload?.current_term || 1);
        const [topicPayload, masteryPayload] = await Promise.all([
          api.listTopics(
            {
              student_id: userId,
              subject,
              term,
            },
            token,
          ),
          api.getMastery(token, {
            student_id: userId,
            subject,
            term,
            view: "topic",
          }),
        ]);
        if (!active) return;

        const topicList = topicPayload || [];
        setTopics(topicList);
        setMasteryByTopic(mapMasteryPayload(masteryPayload));

        if (!topicList.length) {
          setSelectedTopicId(null);
          setError("No approved topics found for your current class and term.");
          return;
        }

        const cachedTopicId = localStorage.getItem("mastery_current_topic_id");
        const hasCached = topicList.some((item) => item.topic_id === cachedTopicId);
        setSelectedTopicId(hasCached ? cachedTopicId : topicList[0].topic_id);
      } catch (err) {
        if (!active) return;
        setError(err.message || "Failed to load learning path.");
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
      setLessonLoading(true);
      try {
        const lessonPayload = await api.getTopicLesson(selectedTopicId, userId, token);
        if (!active) return;
        setLesson(lessonPayload);
        localStorage.setItem("mastery_current_topic_id", selectedTopicId);

        if (token && scope) {
          api
            .logActivity(token, {
              student_id: userId,
              subject: scope.subject,
              term: scope.term,
              event_type: "lesson_viewed",
              ref_id: selectedTopicId,
              duration_seconds: 0,
            })
            .catch(() => {});
        }
      } catch (err) {
        if (!active) return;
        setLesson(null);
        setError(err.message || "Failed to load lesson.");
      } finally {
        if (active) setLessonLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [selectedTopicId, userId, token, scope]);

  useEffect(() => {
    let active = true;
    (async () => {
      if (!token || !userId || !scope) return;

      setSessionLoading(true);
      const sessionStorageKey = buildSessionStorageKey(userId, scope.subject, scope.term);
      const cachedSessionId = localStorage.getItem(sessionStorageKey);

      try {
        if (cachedSessionId) {
          try {
            const history = await api.getSessionHistory(token, cachedSessionId, userId);
            if (!active) return;
            setSessionId(cachedSessionId);
            setChat(mapHistory(history?.messages));
            return;
          } catch {
            localStorage.removeItem(sessionStorageKey);
          }
        }

        const session = await api.startSession(token, {
          student_id: userId,
          subject: scope.subject,
          term: scope.term,
        });
        if (!active) return;
        const newSessionId = session?.session_id ? String(session.session_id) : null;
        setSessionId(newSessionId);
        setChat([]);
        if (newSessionId) localStorage.setItem(sessionStorageKey, newSessionId);
      } catch (err) {
        if (!active) return;
        setSessionId(null);
        setChat([]);
        setError((prev) => prev || err.message || "Tutor session could not be created.");
      } finally {
        if (active) setSessionLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [token, userId, scope]);

  const sendTutorMessage = async () => {
    if (!token || !userId || !scope || !sessionId) return;
    const text = message.trim();
    if (!text) return;

    setMessage("");
    setChat((prev) => [...prev, { role: "student", content: text, citations: [] }]);
    setIsChatting(true);

    try {
      const response = await api.tutorChat(token, {
        student_id: userId,
        session_id: sessionId,
        subject: scope.subject,
        sss_level: scope.sssLevel,
        term: scope.term,
        topic_id: selectedTopicId,
        message: text,
      });
      const assistantMessage = response?.assistant_message || "No response received from tutor.";
      setChat((prev) => [
        ...prev,
        {
          role: "assistant",
          content: assistantMessage,
          citations: response?.citations || [],
        },
      ]);

      api
        .logActivity(token, {
          student_id: userId,
          subject: scope.subject,
          term: scope.term,
          event_type: "tutor_chat",
          ref_id: sessionId,
          duration_seconds: 0,
        })
        .catch(() => {});
    } catch (err) {
      setChat((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Tutor unavailable: ${err.message}`,
          citations: [],
        },
      ]);
    } finally {
      setIsChatting(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-slate-700">Loading learning path...</div>;
  }

  const canGoPrev = topicIndex > 0;
  const canGoNext = topicIndex >= 0 && topicIndex < topics.length - 1;

  return (
    <div className="flex bg-slate-50 h-[calc(100vh-64px)] overflow-hidden">
      <CourseSidebar
        activeStep="lesson"
        topics={topics}
        selectedTopicId={selectedTopicId}
        masteryByTopic={masteryByTopic}
        onSelectTopic={setSelectedTopicId}
        moduleTitle={`${scope?.subject?.toUpperCase() || "LEARNING"} - ${scope?.sssLevel || "SSS"}`}
      />

      <div className="flex-1 overflow-y-auto px-12 py-8">
        <div className="max-w-3xl mx-auto">
          <div className="text-xs font-bold text-slate-400 mb-6 flex gap-2">
            <span>Courses</span>
            <span>{">"}</span>
            <span>Learning Path</span>
            <span>{">"}</span>
            <span className="text-slate-800">{lesson?.title || "Lesson"}</span>
          </div>

          {error && (
            <div className="mb-6 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">
              {error}
            </div>
          )}

          <div className="mb-6">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Topic</label>
            <select
              value={selectedTopicId || ""}
              onChange={(event) => setSelectedTopicId(event.target.value)}
              className="mt-2 w-full p-3 border border-slate-200 rounded-xl bg-white"
            >
              {topics.map((topic) => (
                <option key={topic.topic_id} value={topic.topic_id}>
                  {topic.title}
                </option>
              ))}
            </select>
          </div>

          <h1 className="text-4xl font-black text-slate-900 mb-4 tracking-tight">{lesson?.title || "Lesson"}</h1>
          {lesson?.summary && <p className="text-slate-600 mb-8">{lesson.summary}</p>}

          {lessonLoading ? (
            <div className="text-slate-600">Loading lesson content...</div>
          ) : (
            <div className="space-y-8">
              <div className="prose prose-slate max-w-none">
                {textBlocks.length === 0 && (
                  <p className="text-slate-500">No text lesson blocks found for this topic.</p>
                )}
                {textBlocks.map((block, idx) => (
                  <p key={`text-${idx}`} className="text-slate-600 leading-relaxed mb-6">
                    {typeof block.value === "string" ? block.value : JSON.stringify(block.value)}
                  </p>
                ))}
              </div>

              {exampleBlocks.map((block, idx) => (
                <div
                  key={`example-${idx}`}
                  className="bg-indigo-50 border border-indigo-100 rounded-2xl p-5"
                >
                  <h3 className="font-bold text-indigo-900 mb-2">Worked Example</h3>
                  <p className="text-indigo-900 text-sm">
                    {typeof block.value === "string" ? block.value : JSON.stringify(block.value)}
                  </p>
                </div>
              ))}

              {exerciseBlocks.map((block, idx) => (
                <div
                  key={`exercise-${idx}`}
                  className="bg-amber-50 border border-amber-100 rounded-2xl p-5"
                >
                  <h3 className="font-bold text-amber-900 mb-2">Try This</h3>
                  <p className="text-amber-900 text-sm">
                    {typeof block.value === "string" ? block.value : JSON.stringify(block.value)}
                  </p>
                </div>
              ))}

              {mediaBlocks.map((block, idx) => (
                <div
                  key={`media-${idx}`}
                  className="bg-slate-100 border border-slate-200 rounded-2xl p-4 text-sm"
                >
                  <span className="font-semibold uppercase text-xs text-slate-500 mr-2">{block.type}</span>
                  {block.url ? (
                    <a className="text-indigo-600 underline break-all" href={block.url} target="_blank" rel="noreferrer">
                      {block.url}
                    </a>
                  ) : (
                    <span className="text-slate-700">
                      {typeof block.value === "string" ? block.value : JSON.stringify(block.value)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-between items-center pt-8 border-t border-slate-200 pb-12 mt-10">
            <button
              onClick={() => {
                if (!canGoPrev) return;
                const previous = topics[topicIndex - 1];
                if (previous) setSelectedTopicId(previous.topic_id);
              }}
              disabled={!canGoPrev}
              className={`font-bold transition-colors flex items-center gap-2 ${
                canGoPrev ? "text-slate-600 hover:text-slate-900" : "text-slate-300 cursor-not-allowed"
              }`}
            >
              <span>{"<-"}</span> Previous Topic
            </button>

            <div className="flex items-center gap-3">
              {canGoNext ? (
                <button
                  onClick={() => {
                    const next = topics[topicIndex + 1];
                    if (next) setSelectedTopicId(next.topic_id);
                  }}
                  className="bg-white text-slate-700 border border-slate-200 px-6 py-3 rounded-xl font-bold hover:bg-slate-50 transition-colors"
                >
                  Next Topic
                </button>
              ) : null}
              <button
                onClick={() => navigate("/module-quiz")}
                className="bg-indigo-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200 flex items-center gap-2"
              >
                Take Mastery Quiz <span>{"->"}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="w-80 bg-white border-l border-slate-200 flex flex-col h-[calc(100vh-64px)]">
        <div className="p-4 border-b border-slate-100 flex items-center gap-3 bg-indigo-50/50">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white text-sm shadow-md">
            AI
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">AI Tutor</h3>
            <p className="text-[10px] text-emerald-500 font-bold">
              SESSION {sessionLoading ? "LOADING" : sessionId ? "ACTIVE" : "OFFLINE"}
            </p>
          </div>
        </div>

        <div className="flex-1 p-4 overflow-y-auto space-y-4 text-sm">
          {chat.length === 0 && (
            <div className="bg-slate-50 border border-slate-100 p-4 rounded-2xl text-slate-600">
              Ask a question about this lesson. The tutor will respond using your current scope.
            </div>
          )}
          {chat.map((item, idx) => (
            <div key={`${item.role}-${idx}`}>
              <div
                className={
                  item.role === "student"
                    ? "bg-indigo-600 p-4 rounded-2xl rounded-tr-sm text-white shadow-md ml-4"
                    : "bg-slate-50 border border-slate-100 p-4 rounded-2xl rounded-tl-sm text-slate-700"
                }
              >
                {item.content}
              </div>
              {item.role === "assistant" && item.citations?.length > 0 && (
                <div className="mt-2 px-1 text-[11px] text-slate-500">
                  Sources:{" "}
                  {item.citations
                    .map((citation) => `${citation.source_id || "source"}#${citation.chunk_id || "chunk"}`)
                    .join(", ")}
                </div>
              )}
            </div>
          ))}
          {isChatting && <div className="text-xs text-slate-400">Tutor is typing...</div>}
        </div>

        <div className="p-4 border-t border-slate-100 bg-white">
          <div className="relative">
            <input
              type="text"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") sendTutorMessage();
              }}
              disabled={!sessionId || !selectedTopicId || isChatting}
              placeholder={
                sessionId
                  ? "Ask a question about this topic..."
                  : "Tutor session unavailable. Refresh the page."
              }
              className="w-full pl-4 pr-12 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent disabled:opacity-50"
            />
            <button
              onClick={sendTutorMessage}
              disabled={!sessionId || !message.trim() || isChatting}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-indigo-600 text-white rounded-lg flex items-center justify-center hover:bg-indigo-700 transition-colors disabled:opacity-40"
            >
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
