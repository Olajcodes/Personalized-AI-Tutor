// import React, { useState, useEffect } from 'react';
// import { useNavigate, useParams } from "react-router-dom";
// import { useAuth } from '../context/AuthContext';
// import { useUser } from '../context/UserContext';
// import { Target, Brain, BarChart2 } from 'lucide-react';

// // Import your results components (Ensure these paths are correct for your project)
// import Breadcrumbs from "../components/BreadCrumbs";
// import ScoreSummary from "../components/ScoreSummary";
// import ConceptCard from "../components/ConceptCard";
// import AITutorInsights from "../components/AITutorInsights";
// import PathProgress from "../components/PathProgress";
// import FooterActions from "../components/FooterActions";

// export default function Quizes() {
//   const navigate = useNavigate();
//   const { topicId } = useParams(); // Using topicId to generate the quiz
//   const { token } = useAuth();
//   const { studentData, userData } = useUser();
//   const activeId = studentData?.user_id || userData?.id;

//   const currentSubject = localStorage.getItem('active_subject') || studentData?.subjects?.[0] || 'math';
//   const currentLevel = studentData?.sss_level || 'SSS3';
//   const currentTerm = studentData?.current_term || 1;

//   const apiUrl = import.meta.env.VITE_API_URL || 'https://mastery-backend-7xe8.onrender.com/api/v1';

//   // --- API LIFECYCLE STATES ---
//   const [phase, setPhase] = useState('setup'); // 'setup' | 'generating' | 'active' | 'submitting' | 'results'
//   const [error, setError] = useState("");

//   // Config
//   const [difficulty, setDifficulty] = useState('medium');
//   const [purpose, setPurpose] = useState('practice');

//   // Active Quiz
//   const [quizData, setQuizData] = useState(null);
//   const [currentQuestion, setCurrentQuestion] = useState(0);
//   const [selectedAnswers, setSelectedAnswers] = useState({}); // { question_id: "answer_value" }
//   const [startTime, setStartTime] = useState(null);

//   // Results
//   const [formattedResults, setFormattedResults] = useState(null);

//   // ======================================================================
//   // 1. GENERATE QUIZ
//   // ======================================================================
//   const handleGenerateQuiz = async () => {
//     setPhase('generating');
//     setError("");

//     try {
//       const response = await fetch(`${apiUrl}/learning/quizzes/generate`, {
//         method: 'POST',
//         headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
//         body: JSON.stringify({
//           student_id: activeId,
//           subject: currentSubject,
//           sss_level: currentLevel,
//           term: currentTerm,
//           topic_id: topicId,
//           purpose: purpose,
//           difficulty: difficulty,
//           num_questions: 5 // Defaulting to 5
//         })
//       });

//       if (!response.ok) throw new Error("Failed to generate quiz. Please try again.");

//       const data = await response.json();
//       setQuizData(data);
//       setStartTime(Date.now());
//       setPhase('active');
//     } catch (err) {
//       setError(err.message);
//       setPhase('setup');
//     }
//   };

//   // ======================================================================
//   // 2. SUBMIT QUIZ & FETCH RESULTS
//   // ======================================================================
//   const submitQuizAnswers = async (finalAnswers) => {
//     setPhase('submitting');
//     setError("");

//     const timeTakenSeconds = Math.floor((Date.now() - startTime) / 1000);
//     const formattedAnswers = Object.entries(finalAnswers).map(([qId, ans]) => ({
//       question_id: qId,
//       answer: ans
//     }));

//     try {
//       // A. Submit Answers to API
//       const submitRes = await fetch(`${apiUrl}/learning/quizzes/${quizData.quiz_id}/submit`, {
//         method: 'POST',
//         headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
//         body: JSON.stringify({ student_id: activeId, answers: formattedAnswers, time_taken_seconds: timeTakenSeconds })
//       });

//       if (!submitRes.ok) throw new Error("Failed to submit quiz.");
//       const submitData = await submitRes.json();
      
//       // B. Fetch Results/Insights
//       const resultsRes = await fetch(`${apiUrl}/learning/quizzes/${quizData.quiz_id}/results?student_id=${activeId}&attempt_id=${submitData.attempt_id}`, {
//         headers: { 'Authorization': `Bearer ${token}` }
//       });

//       if (!resultsRes.ok) throw new Error("Failed to load detailed results.");
//       const resultsJson = await resultsRes.json();

//       // C. Format for your Custom Results Components
//       const finalScorePercentage = Math.round((resultsJson.score || 0) * 100);
//       const wrongConcepts = (resultsJson.concept_breakdown || []).filter(c => !c.is_correct).map(c => `**${c.concept_id}**`);

//       setFormattedResults({
//         paths: { classLevel: currentLevel, topic: currentSubject },
//         summary: {
//             studentName: userData?.first_name || "Student",
//             score: Math.round((resultsJson.score || 0) * quizData.questions.length),
//             total: quizData.questions.length,
//             message: finalScorePercentage >= 70 ? "You've successfully mastered this module!" : "Good effort. Let's review some concepts.",
//             timeTaken: `${Math.floor(timeTakenSeconds / 60)}m ${timeTakenSeconds % 60}s`,
//             accuracy: finalScorePercentage,
//             xpEarned: submitData.xp_awarded || 0
//         },
//         concepts: (resultsJson.concept_breakdown || []).map((c, i) => ({
//             id: i,
//             title: c.concept_id || `Concept ${i+1}`,
//             mastery: c.weight_change > 0 ? 100 : 40, 
//             description: c.is_correct ? "Perfect score!" : "Needs review."
//         })),
//         aiInsights: {
//             greeting: `Hi ${userData?.first_name || 'there'}!`,
//             strugglePoints: wrongConcepts.length > 0 ? wrongConcepts : ["None"],
//             keyInsight: resultsJson.insights?.[0] || "Keep up the great work!",
//             prerequisite: resultsJson.insights?.[1] || "Continue practicing to maintain mastery."
//         },
//         nextTopic: resultsJson.recommended_revision_topic_id || "Next Module"
//       });

//       setPhase('results');
      
//       // NOTE: If you prefer to navigate to a totally different page instead of rendering the phase here, uncomment below:
//       // navigate(`/quiz/${quizData.quiz_id}/completed`, { state: { results: formattedResults } });

//     } catch (err) {
//       setError(err.message);
//       setPhase('active');
//     }
//   };

//   // ======================================================================
//   // ACTIVE UI HANDLERS
//   // ======================================================================
//   const handleSelectOption = (optionValue) => {
//     setSelectedAnswers(prev => ({ ...prev, [quizData.questions[currentQuestion].id]: optionValue }));
//   };

//   const handleNext = () => {
//     if (currentQuestion < quizData.questions.length - 1) setCurrentQuestion(currentQuestion + 1);
//   };

//   const handleSkip = () => {
//     const qId = quizData.questions[currentQuestion].id;
//     const updatedAnswers = { ...selectedAnswers, [qId]: "SKIPPED" };
//     setSelectedAnswers(updatedAnswers);

//     if (currentQuestion === quizData.questions.length - 1) {
//       submitQuizAnswers(updatedAnswers);
//     } else {
//       setCurrentQuestion(currentQuestion + 1);
//     }
//   };

//   const handleSubmit = () => {
//     submitQuizAnswers(selectedAnswers);
//   };

//   // ======================================================================
//   // RENDER: SETUP PHASE
//   // ======================================================================
//   if (phase === 'setup' || phase === 'generating') {
//     return (
//       <main className="min-h-screen bg-[#F3F0FF] flex items-center justify-center p-6">
//         <div className="max-w-md w-full bg-white rounded-3xl p-10 shadow-lg border-2" style={{ borderColor: '#7F13EC' }}>
//           <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6 mx-auto" style={{ backgroundColor: '#F3F0FF', color: '#7F13EC' }}>
//             <Target size={32} />
//           </div>
//           <h1 className="text-3xl font-bold text-center text-gray-900 mb-8">Configure Quiz</h1>
          
//           {error && <p className="text-red-500 text-sm text-center mb-6 font-bold">{error}</p>}

//           <button 
//             onClick={handleGenerateQuiz} 
//             disabled={phase === 'generating'} 
//             className="w-full py-4 rounded-xl font-bold text-white transition-all shadow-lg flex justify-center items-center disabled:opacity-70"
//             style={{ backgroundColor: '#7F13EC' }}
//           >
//             {phase === 'generating' ? 'Compiling AI Questions...' : 'Start Quiz'}
//           </button>
//         </div>
//       </main>
//     );
//   }

//   // ======================================================================
//   // RENDER: ACTIVE PHASE (YOUR EXACT UI)
//   // ======================================================================
//   if (phase === 'active' || phase === 'submitting') {
//     const question = quizData.questions[currentQuestion];
//     const progress = ((currentQuestion) / quizData.questions.length) * 100;
//     const isLastQuestion = currentQuestion === quizData.questions.length - 1;
//     const currentSelectedValue = selectedAnswers[question.id];
//     const isAnswered = currentSelectedValue !== undefined;

//     return (
//       <main className="min-h-screen bg-[#F3F0FF]">
//         {/* Header */}
//         <header className="bg-white border-b-2 shadow-sm" style={{ borderColor: '#7F13EC' }}>
//           <div className="container mx-auto px-6 py-4 flex items-center justify-between">
//             <div className="flex items-center gap-2">
//               <div className="w-8 h-8 rounded flex items-center justify-center" style={{ backgroundColor: '#7F13EC' }}>
//                 <span className="text-white font-bold text-sm">M</span>
//               </div>
//               <span className="font-bold text-gray-900 hidden sm:block">MasteryAI</span>
//             </div>
            
//             <div className="flex items-center gap-6">
//               <div className="text-sm text-gray-600 hidden sm:block">
//                 Question <span className="font-semibold">{currentQuestion + 1} of {quizData.questions.length}</span>
//               </div>
//               <div className="flex items-center gap-2">
//                 <div className="w-24 sm:w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
//                   <div className="h-full transition-all duration-300" style={{ backgroundColor: '#7F13EC', width: `${progress}%` }} />
//                 </div>
//                 <div className="text-sm font-semibold text-gray-900 w-12 text-right">{Math.round(progress)}%</div>
//               </div>
//             </div>
//           </div>
//         </header>

//         {/* Question Area */}
//         <div className="container mx-auto px-4 sm:px-6 py-12">
//           <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-lg p-6 sm:p-10 md:p-16" style={{ border: '2px solid #7F13EC' }}>
            
//             <div className="text-center mb-8">
//               <span className="text-xs font-bold tracking-widest uppercase px-4 py-1.5 rounded-full" style={{ color: '#7F13EC', backgroundColor: '#F3F0FF' }}>
//                 {currentSubject} • {question.concept_id || 'ASSESSMENT'}
//               </span>
//             </div>
            
//             {/* The Prompt */}
//             <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold text-gray-900 text-center mb-10 leading-snug">
//               {question.text}
//             </h2>
            
//             {/* Note: If backend provides an equation, render it. Otherwise, rely on the text above. */}
//             {question.equation && (
//               <div className="bg-gray-50 border-2 border-gray-200 rounded-2xl p-8 md:p-12 text-center mb-12">
//                 <div className="text-3xl md:text-5xl font-bold text-gray-900">{question.equation}</div>
//               </div>
//             )}

//             {/* Options */}
//             <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
//               {question.options.map((opt, index) => {
//                 // Handle backend returning string vs object
//                 const optValue = typeof opt === 'string' ? opt : opt.text || opt.value;
//                 const isSelected = currentSelectedValue === optValue;
//                 const letter = String.fromCharCode(65 + index); // A, B, C...

//                 return (
//                   <button
//                     key={index}
//                     onClick={() => handleSelectOption(optValue)}
//                     className="p-5 sm:p-6 rounded-2xl border-2 text-left transition-all duration-200"
//                     style={{
//                       borderColor: isSelected ? '#7F13EC' : '#E5E7EB',
//                       backgroundColor: isSelected ? '#F3F0FF' : '#FFFFFF'
//                     }}
//                   >
//                     <div className="flex items-start gap-4">
//                       <div className="w-6 h-6 rounded-full border-2 mt-1 flex items-center justify-center flex-shrink-0 transition-colors" style={{
//                         borderColor: isSelected ? '#7F13EC' : '#D1D5DB',
//                         backgroundColor: isSelected ? '#7F13EC' : '#FFFFFF'
//                       }}>
//                         {isSelected && <div className="w-2 h-2 bg-white rounded-full" />}
//                       </div>
//                       <div>
//                         <div className="text-[10px] font-bold text-gray-400 mb-1 uppercase tracking-widest">Option {letter}</div>
//                         <div className={`text-lg font-semibold ${isSelected ? 'text-[#7F13EC]' : 'text-gray-900'}`}>{optValue}</div>
//                       </div>
//                     </div>
//                   </button>
//                 );
//               })}
//             </div>

//             {/* Footer Actions */}
//             <div className="flex flex-col-reverse sm:flex-row items-center justify-between pt-6 border-t border-gray-200 gap-6">
//               <button onClick={handleSkip} disabled={phase === 'submitting'} className="text-gray-500 hover:text-gray-700 text-sm font-medium flex items-center gap-1 transition-colors">
//                 <span className="text-base">»</span> <span>I haven't learned this yet (Skip)</span>
//               </button>

//               <button
//                 onClick={isLastQuestion ? handleSubmit : handleNext}
//                 disabled={!isAnswered || phase === 'submitting'}
//                 className="w-full sm:w-auto px-8 py-3.5 rounded-full font-semibold transition-all shadow-md"
//                 style={{
//                   backgroundColor: isAnswered ? '#7F13EC' : '#D1D5DB',
//                   color: isAnswered ? '#FFFFFF' : '#9CA3AF',
//                   cursor: (isAnswered && phase !== 'submitting') ? 'pointer' : 'not-allowed'
//                 }}
//               >
//                 {phase === 'submitting' ? 'Scoring...' : (isLastQuestion ? 'Submit Answer →' : 'Next Question →')}
//               </button>
//             </div>
//           </div>
//         </div>
//       </main>
//     );
//   }

//   // ======================================================================
//   // RENDER: RESULTS PHASE (Using your external components)
//   // ======================================================================
//   if (phase === 'results' && formattedResults) {
//     return (
//       <div className="min-h-screen bg-slate-50">
//         <div className="max-w-7xl mx-auto px-6 py-8">
//             <Breadcrumbs classLevel={formattedResults.paths.classLevel} topic={formattedResults.paths.topic} />

//             <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
//                 {/* Left Column - Main Results */}
//                 <div className="lg:col-span-2 flex flex-col">
//                     <ScoreSummary data={formattedResults.summary} />

//                     <div className="mb-4 flex items-center gap-2 mt-8">
//                         <BarChart2 className="w-6 h-6 text-emerald-500" />
//                         <h2 className="text-xl font-bold text-gray-900">Concept Mastery Breakdown</h2>
//                     </div>

//                     <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
//                         {formattedResults.concepts.map(concept => (
//                             <ConceptCard 
//                               key={concept.id}
//                               title={concept.title}
//                               mastery={concept.mastery}
//                               description={concept.description}
//                             />
//                         ))}
//                     </div>
//                 </div>

//                 {/* Right Column - Sidebar */}
//                 <div className="lg:col-span-1 flex flex-col mt-8 lg:mt-0">
//                     <AITutorInsights insights={formattedResults.aiInsights} />
//                     <div className="mt-6">
//                        <PathProgress nextTopic={formattedResults.nextTopic} />
//                     </div>
//                 </div>
//             </div>

//             <div className="mt-12">
//               <FooterActions />
//             </div>
//         </div>
//       </div>
//     );
//   }

//   return null;
// }