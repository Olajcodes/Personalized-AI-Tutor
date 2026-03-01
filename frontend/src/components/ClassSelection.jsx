import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, LEVELS, TERMS } from "../api/client";

const DEFAULT_GRADE_META = {
  SSS1: { label: "Grade 10", icon: "📖" },
  SSS2: { label: "Grade 11", icon: "📘" },
  SSS3: { label: "Grade 12", icon: "🎓" },
};

const ClassSelection = () => {
  const [selectedGrade, setSelectedGrade] = useState("");
  const [selectedTerm, setSelectedTerm] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingMetadata, setIsFetchingMetadata] = useState(true);
  const [availableGrades, setAvailableGrades] = useState([]);
  const [availableTerms, setAvailableTerms] = useState([]);

  const navigate = useNavigate();

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const payload = await api.getMetadataLevels();
        const levels = Array.isArray(payload?.levels) && payload.levels.length ? payload.levels : LEVELS;
        const terms = Array.isArray(payload?.terms) && payload.terms.length ? payload.terms : TERMS;

        if (!active) return;
        setAvailableGrades(
          levels.map((id) => ({
            id,
            label: DEFAULT_GRADE_META[id]?.label || id,
            icon: DEFAULT_GRADE_META[id]?.icon || "📚",
          })),
        );
        setAvailableTerms(terms);
      } catch {
        if (!active) return;
        setAvailableGrades(
          LEVELS.map((id) => ({
            id,
            label: DEFAULT_GRADE_META[id]?.label || id,
            icon: DEFAULT_GRADE_META[id]?.icon || "📚",
          })),
        );
        setAvailableTerms(TERMS);
      } finally {
        if (active) setIsFetchingMetadata(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const handleContinue = () => {
    if (!selectedGrade || !selectedTerm) {
      alert("Please select both your grade and current term.");
      return;
    }
    setIsLoading(true);
    const scope = { sss_level: selectedGrade, term: Number(selectedTerm) };
    localStorage.setItem("mastery_onboarding_scope", JSON.stringify(scope));
    navigate("/SubjectSelection", { state: scope });
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen font-sans p-8" style={{ backgroundColor: "#F7FAFC" }}>
      <div className="flex items-center gap-2 mb-16">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold shadow-md" style={{ backgroundColor: "#635BFF" }}>
          M
        </div>
        <span className="text-xl font-bold tracking-tight" style={{ color: "#1A1F36" }}>
          MasteryAI
        </span>
      </div>

      <div className="max-w-4xl mx-auto text-center">
        <h1 className="text-4xl font-extrabold mb-4" style={{ color: "#1A1F36" }}>
          Tell us about your class
        </h1>
        <p className="mb-12 max-w-md mx-auto leading-relaxed" style={{ color: "#4F5668" }}>
          Select your current grade and term to personalize your curriculum path.
        </p>

        {isFetchingMetadata ? (
          <div className="mb-12 text-[#635BFF] font-bold animate-pulse">Loading curriculum levels...</div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
              {availableGrades.map((grade) => {
                const isSelected = selectedGrade === grade.id;
                return (
                  <div
                    key={grade.id}
                    onClick={() => setSelectedGrade(grade.id)}
                    className={`relative p-8 rounded-[2.5rem] border-2 transition-all duration-300 cursor-pointer bg-white flex flex-col items-center ${isSelected ? "shadow-2xl scale-[1.02]" : "border-transparent shadow-sm hover:shadow-md"}`}
                    style={{ borderColor: isSelected ? "#635BFF" : "transparent" }}
                  >
                    {isSelected && (
                      <div className="absolute top-4 right-6 text-white rounded-full w-6 h-6 flex items-center justify-center text-[10px] shadow-lg border-2 border-white" style={{ backgroundColor: "#635BFF" }}>
                        ✓
                      </div>
                    )}
                    <div className="w-20 h-20 rounded-full flex items-center justify-center text-3xl mb-6 transition-colors" style={{ backgroundColor: isSelected ? "#635BFF" : "#F7FAFC", color: isSelected ? "#FFFFFF" : "#635BFF" }}>
                      {grade.icon}
                    </div>
                    <h3 className="text-2xl font-bold" style={{ color: "#1A1F36" }}>
                      {grade.id}
                    </h3>
                    <p className="font-medium mb-2" style={{ color: "#A3ACBF" }}>
                      {grade.label}
                    </p>
                    {isSelected && (
                      <span className="mt-2 px-4 py-1.5 text-white text-[10px] font-bold rounded-full uppercase tracking-wider shadow-sm" style={{ backgroundColor: "#635BFF" }}>
                        Current Choice
                      </span>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="bg-white p-10 rounded-[2.5rem] shadow-sm border max-w-xl mx-auto mb-10" style={{ borderColor: "#E3E8EE" }}>
              <div className="flex items-center gap-3 font-semibold mb-5 justify-center" style={{ color: "#4F566B" }}>
                <span className="text-xl">📅</span> Which term are you currently in?
              </div>
              <div className="relative">
                <select
                  value={selectedTerm}
                  onChange={(e) => setSelectedTerm(e.target.value)}
                  className="w-full p-4 rounded-2xl border outline-none transition-all appearance-none cursor-pointer"
                  style={{ backgroundColor: "#F7FAFC", borderColor: "#E3E8EE", color: "#4F566B" }}
                >
                  <option value="">Select Current Term</option>
                  {availableTerms.map((term) => (
                    <option key={term} value={term}>
                      Term {term}
                    </option>
                  ))}
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: "#A3ACBF" }}>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                  </svg>
                </div>
              </div>
            </div>
          </>
        )}

        <button
          onClick={handleContinue}
          disabled={isLoading || !selectedGrade || !selectedTerm}
          className={`w-full max-w-xl py-5 text-white text-lg font-bold rounded-2xl shadow-xl transition-all transform ${!isLoading && "active:scale-[0.97]"}`}
          style={{
            backgroundColor: isLoading || !selectedGrade || !selectedTerm ? "#A3ACBF" : "#635BFF",
            boxShadow: isLoading || !selectedGrade || !selectedTerm ? "none" : "0 10px 15px -3px rgba(99, 91, 255, 0.3)",
            cursor: isLoading ? "wait" : "pointer",
          }}
        >
          {isLoading ? "Saving..." : "Continue"}
        </button>
      </div>
    </div>
  );
};

export default ClassSelection;
