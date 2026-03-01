import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api, SUBJECTS } from "../api/client";
import { useAuth } from "../context/AuthContext";

const SUBJECT_META = {
  math: {
    label: "MATHEMATICS",
    icon: "➕",
    description: "Algebra, Geometry, and Data Analysis tailored to your level.",
  },
  english: {
    label: "ENGLISH STUDIES",
    icon: "📖",
    description: "Grammar, Literature, and Writing mastery support.",
  },
  civic: {
    label: "CIVIC EDUCATION",
    icon: "🌍",
    description: "Civic rights, institutions, and social responsibility.",
  },
};

const SubjectSelection = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { token, userId } = useAuth();

  const [selectedSubjects, setSelectedSubjects] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [availableSubjects, setAvailableSubjects] = useState([]);
  const [isFetchingMetadata, setIsFetchingMetadata] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const payload = await api.getMetadataSubjects();
        const subjectIds = Array.isArray(payload?.subjects) && payload.subjects.length ? payload.subjects : SUBJECTS;
        if (!active) return;
        setAvailableSubjects(
          subjectIds.map((id) => ({
            id,
            label: SUBJECT_META[id]?.label || id.toUpperCase(),
            icon: SUBJECT_META[id]?.icon || "📚",
            description: SUBJECT_META[id]?.description || "Curriculum-aligned learning path.",
          })),
        );
      } catch {
        if (!active) return;
        setAvailableSubjects(
          SUBJECTS.map((id) => ({
            id,
            label: SUBJECT_META[id]?.label || id.toUpperCase(),
            icon: SUBJECT_META[id]?.icon || "📚",
            description: SUBJECT_META[id]?.description || "Curriculum-aligned learning path.",
          })),
        );
      } finally {
        if (active) setIsFetchingMetadata(false);
      }
    })();

    return () => {
      active = false;
    };
  }, []);

  const toggleSubject = (id) => {
    setError("");
    if (selectedSubjects.includes(id)) {
      setSelectedSubjects(selectedSubjects.filter((item) => item !== id));
    } else {
      setSelectedSubjects([...selectedSubjects, id]);
    }
  };

  const handleContinue = async () => {
    if (selectedSubjects.length === 0) {
      setError("Please select at least one subject.");
      return;
    }
    if (!token || !userId) {
      setError("Authentication missing. Please login again.");
      return;
    }

    const fallbackScope = (() => {
      try {
        return JSON.parse(localStorage.getItem("mastery_onboarding_scope") || "{}");
      } catch {
        return {};
      }
    })();

    const selectedScope = {
      sss_level: location.state?.grade || fallbackScope.sss_level || "SSS1",
      term: Number(location.state?.term || fallbackScope.term || 1),
    };

    setIsLoading(true);
    setError("");
    try {
      await api.setupProfile(token, {
        student_id: userId,
        sss_level: selectedScope.sss_level,
        subjects: selectedSubjects,
        term: selectedScope.term,
      });
      navigate("/learningpreferences");
    } catch (err) {
      setError(err.message || "Failed to setup profile.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen font-sans p-8" style={{ backgroundColor: "#F9FAFB" }}>
      <div className="flex items-center gap-2 mb-16">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold shadow-md" style={{ backgroundColor: "#635BFF" }}>
          M
        </div>
        <span className="text-xl font-bold tracking-tight" style={{ color: "#1A1F36" }}>
          MasteryAI
        </span>
      </div>

      <div className="max-w-6xl mx-auto text-center mb-12">
        <h1 className="text-4xl font-extrabold mb-4" style={{ color: "#111827" }}>
          Which subjects do you want help with?
        </h1>
        <p className="max-w-2xl mx-auto text-lg" style={{ color: "#6B7280" }}>
          Pick subjects to personalize your learning path.
        </p>
      </div>

      {error && (
        <div className="max-w-4xl mx-auto mb-6 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium">
          {error}
        </div>
      )}

      {isFetchingMetadata ? (
        <div className="text-center font-bold text-[#5850EC] animate-pulse mb-16">Fetching available subjects...</div>
      ) : (
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {availableSubjects.map((subject) => {
            const isSelected = selectedSubjects.includes(subject.id);
            return (
              <div
                key={subject.id}
                onClick={() => toggleSubject(subject.id)}
                className={`relative p-8 rounded-[2rem] border-2 transition-all duration-300 cursor-pointer bg-white flex flex-col items-start min-h-[280px] ${isSelected ? "shadow-2xl scale-[1.02]" : "border-transparent shadow-sm hover:shadow-md"}`}
                style={{ borderColor: isSelected ? "#5850EC" : "transparent" }}
              >
                {isSelected && (
                  <div className="absolute top-6 right-6 rounded-full w-6 h-6 flex items-center justify-center text-[10px] border-2 border-white shadow-sm text-white" style={{ backgroundColor: "#5850EC" }}>
                    ✓
                  </div>
                )}
                <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl mb-6 shadow-inner" style={{ backgroundColor: isSelected ? "#EEF2FF" : "#F3F4F6" }}>
                  {subject.icon}
                </div>
                <h3 className="text-xl font-bold mb-3" style={{ color: "#111827" }}>
                  {subject.label}
                </h3>
                <p className="text-sm leading-relaxed mb-6" style={{ color: "#6B7280" }}>
                  {subject.description}
                </p>
              </div>
            );
          })}
        </div>
      )}

      <div className="max-w-6xl mx-auto border-t pt-8 flex items-center justify-between" style={{ borderColor: "#E5E7EB" }}>
        <button onClick={() => navigate(-1)} disabled={isLoading} className="flex items-center gap-2 font-bold transition-colors hover:opacity-70 disabled:opacity-50" style={{ color: "#6B7280" }}>
          <span>←</span> Back
        </button>
        <button
          onClick={handleContinue}
          disabled={isLoading || selectedSubjects.length === 0}
          className="px-10 py-4 text-white font-bold rounded-2xl shadow-xl transition-all transform active:scale-95 flex items-center gap-2"
          style={{
            backgroundColor: isLoading || selectedSubjects.length === 0 ? "#A3ACBF" : "#5850EC",
            boxShadow: isLoading || selectedSubjects.length === 0 ? "none" : "0 10px 15px -3px rgba(88, 80, 236, 0.3)",
            cursor: isLoading ? "wait" : selectedSubjects.length === 0 ? "not-allowed" : "pointer",
          }}
        >
          {isLoading ? "Saving..." : "Continue"} <span>→</span>
        </button>
      </div>
    </div>
  );
};

export default SubjectSelection;
