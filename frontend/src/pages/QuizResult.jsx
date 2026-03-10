// // import Header from "./components/Header";
// import Breadcrumbs from "../components/BreadCrumbs";
// import ScoreSummary from "../components/ScoreSummary";
// import ConceptCard from "../components/ConceptCard";
// import AITutorInsights from "../components/AITutorInsights";
// import PathProgress from "../components/PathProgress";
// import FooterActions from "../components/FooterActions";
// import { useState, useEffect } from "react";
// import { BarChart2 } from 'lucide-react';

// export default function QuizResult() {

//         // State to hold the API data
//     const [quizData, setQuizData] = useState(null);
//     const [isLoading, setIsLoading] = useState(true);

//     // Simulating API fetch
//     useEffect(() => {
//         // In a real application, you'd make an Axios or fetch call here:
//         // fetch('/api/quiz/results/latest').then(res => res.json()).then(data => setQuizData(data))
        
//         const mockApiData = {
//         paths: {
//             classLevel: "SSS 2",
//             topic: "Calculus"
//         },
//         summary: {
//             studentName: "Samuel",
//             score: 8,
//             total: 10,
//             message: "You've successfully mastered the foundations of Energy. You're ready to explore more complex thermal dynamics.",
//             timeTaken: "12m 45s",
//             accuracy: 80,
//             xpEarned: 450
//         },
//         concepts: [
//             { id: 1, title: "Heat Transfer", mastery: 100, description: "Perfect score! You understand conduction, convection, and radiation." },
//             { id: 2, title: "Kinetic Energy", mastery: 60, description: "Needs review. You're confusing velocity with mass effects." },
//             { id: 3, title: "Potential Energy", mastery: 90, description: "Great progress! Just one minor slip on gravitational height." },
//             { id: 4, title: "Energy Conservation", mastery: 85, description: "Strong grasp of the first law of thermodynamics." }
//         ],
//         aiInsights: {
//             greeting: "Hi Samuel! You did great on Heat Transfer.",
//             strugglePoints: ["**Question 4**", "**Question 7**"],
//             keyInsight: "You missed the question on Conduction because you picked the answer for Convection. Tip: Remember that Conduction requires direct contact between solids!",
//             prerequisite: "To improve on Kinetic Energy, I recommend reviewing..."
//         },
//         nextTopic: "Chemical Energy Fundamentals"
//         };

//         setTimeout(() => {
//         setQuizData(mockApiData);
//         setIsLoading(false);
//         }, 500); // simulate network delay
//     }, []);

//     if (isLoading) {
//         return <div className="min-h-screen flex items-center justify-center bg-slate-50">Loading results...</div>;
//     }
//     return (
//         <div className="max-w-7xl mx-auto px-6 py-8">

//             <Breadcrumbs classLevel={quizData.paths.classLevel} topic={quizData.paths.topic} />

//             <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
//                 {/* Left Column - Main Results */}
//                 <div className="lg:col-span-2 flex flex-col">
//                     <ScoreSummary data={quizData.summary} />

//                     <div className="mb-4 flex items-center gap-2">
//                         <BarChart2 className="w-6 h-6 text-emerald-500" />
//                         <h2 className="text-xl font-bold text-gray-900">Concept Mastery Breakdown</h2>
//                     </div>

//                     <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
//                         {quizData.concepts.map(concept => (
//                             <ConceptCard 
//                             key={concept.id}
//                             title={concept.title}
//                             mastery={concept.mastery}
//                             description={concept.description}
//                             />
//                         ))}
//                     </div>
//                 </div>

//                 {/* Right Column - Sidebar */}
//                 <div className="lg:col-span-1 flex flex-col">
//                     <AITutorInsights insights={quizData.aiInsights} />
//                     <PathProgress nextTopic={quizData.nextTopic} />
//                 </div>
//             </div>

//             <FooterActions />
//         </div>
//     )
// }