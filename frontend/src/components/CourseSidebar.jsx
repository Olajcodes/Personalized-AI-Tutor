import React, { useMemo } from "react";
import { useNavigate } from "react-router-dom";

const MASTERY_DONE_THRESHOLD = 0.7;

const statusStyles = {
  completed: {
    container: "hover:bg-slate-50",
    icon: "bg-emerald-100 text-emerald-600",
    title: "text-slate-900",
    meta: "text-emerald-600",
    symbol: "OK",
  },
  active: {
    container: "bg-indigo-50 border border-indigo-100/60",
    icon: "bg-indigo-600 text-white shadow-md shadow-indigo-200",
    title: "text-indigo-900",
    meta: "text-indigo-600",
    symbol: ">",
  },
  available: {
    container: "hover:bg-slate-50",
    icon: "bg-slate-100 text-slate-500",
    title: "text-slate-800",
    meta: "text-slate-500",
    symbol: "...",
  },
};

const normalizeScore = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return Math.max(0, Math.min(1, num));
};

const toDurationText = (minutes) => {
  const value = Number(minutes);
  if (!Number.isFinite(value) || value <= 0) return "Approx. 15 min";
  return `Approx. ${Math.round(value)} min`;
};

const CourseSidebar = ({
  activeStep = "lesson",
  topics = [],
  selectedTopicId = null,
  masteryByTopic = {},
  onSelectTopic,
  moduleTitle = "Adaptive Learning Path",
}) => {
  const navigate = useNavigate();

  const lessonRows = useMemo(() => {
    return (topics || []).map((topic) => {
      const score = normalizeScore(masteryByTopic?.[topic.topic_id]);
      const isCompleted = score >= MASTERY_DONE_THRESHOLD;
      const isActive = !isCompleted && activeStep !== "quiz" && topic.topic_id === selectedTopicId;

      const status = isCompleted ? "completed" : isActive ? "active" : "available";
      const style = statusStyles[status];
      const scoreLabel = `${Math.round(score * 100)}% mastery`;
      const fallbackMeta = toDurationText(topic.estimated_duration_minutes);
      const meta = isActive ? "In progress" : score > 0 ? scoreLabel : fallbackMeta;

      return {
        id: topic.topic_id,
        title: topic.title,
        status,
        style,
        meta,
      };
    });
  }, [topics, masteryByTopic, selectedTopicId, activeStep]);

  const completedCount = lessonRows.filter((item) => item.status === "completed").length;
  const totalCount = lessonRows.length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div className="w-72 bg-white border-r border-slate-200 flex flex-col h-[calc(100vh-64px)] overflow-y-auto">
      <div className="p-6">
        <button
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-2 text-indigo-600 font-bold text-sm mb-8 hover:text-indigo-800 transition-colors"
        >
          <span>{"<-"}</span> Back to Dashboard
        </button>

        <div className="mb-8">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Current Module</p>
          <h2 className="text-lg font-black text-slate-900 mb-2">{moduleTitle}</h2>
          <div className="flex justify-between items-center text-xs font-bold text-indigo-600 mb-2">
            <span>{progressPercent}% Complete</span>
            <span className="text-slate-400">
              {completedCount}/{Math.max(totalCount, 1)} Units
            </span>
          </div>
          <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-indigo-600 rounded-full" style={{ width: `${progressPercent}%` }} />
          </div>
        </div>

        <div>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">Lessons</p>
          {lessonRows.length === 0 ? (
            <div className="text-xs text-slate-500 bg-slate-50 border border-slate-100 p-3 rounded-xl">
              No topics yet for this scope.
            </div>
          ) : (
            <div className="space-y-1">
              {lessonRows.map((lesson) => (
                <button
                  key={lesson.id}
                  onClick={() => {
                    if (typeof onSelectTopic === "function") onSelectTopic(lesson.id);
                    if (activeStep === "quiz") navigate("/learning-path");
                  }}
                  className={`w-full text-left flex items-start gap-3 p-3 rounded-xl transition-colors ${lesson.style.container}`}
                >
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 text-[10px] font-bold ${lesson.style.icon}`}
                  >
                    {lesson.style.symbol}
                  </div>
                  <div>
                    <h4 className={`text-sm font-bold ${lesson.style.title}`}>{lesson.title}</h4>
                    <p className={`text-[10px] font-medium mt-0.5 ${lesson.style.meta}`}>{lesson.meta}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mt-auto p-6 border-t border-slate-100">
        <button
          onClick={() => navigate("/module-quiz")}
          className={`w-full py-3 flex items-center justify-center gap-2 text-sm font-bold rounded-xl transition-colors ${
            activeStep === "quiz"
              ? "text-white bg-indigo-600 hover:bg-indigo-700"
              : "text-slate-600 bg-white border border-slate-200 hover:bg-slate-50"
          }`}
        >
          Open Mastery Quiz
        </button>
      </div>
    </div>
  );
};

export default CourseSidebar;
