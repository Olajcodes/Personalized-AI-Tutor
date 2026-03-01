import React from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import OnboardingGuard from "./components/OnboardingGuard";

import Navbar from "./components/Navbar";
import TeacherSidebar from "./components/TeacherSidebar";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ExplainMistakePage from "./pages/ExplainMistakePage";
import ProfilePage from "./pages/ProfilePage";
import ConceptAnalyticsPage from "./pages/ConceptAnalyticsPage";

import ClassSelection from "./components/ClassSelection";
import SubjectSelection from "./components/SubjectSelection";
import LearningPreferences from "./components/LearningPreferences";
import AssessmentSplash from "./components/AssessmentSplash";

import Completed from "./components/Completed";
import InProgress from "./components/In-progress";
import Quizzes from "./components/Quizzes";

import Dashboard from "./pages/Dashboard";
import LessonPage from "./pages/LessonPage";
import ModuleQuizPage from "./pages/ModuleQuizPage";
import QuizResult from "./pages/QuizResult";

const StudentLayout = () => (
  <div className="min-h-screen bg-slate-50 flex flex-col">
    <Navbar />
    <div className="flex-1">
      <Outlet />
    </div>
  </div>
);

const TeacherLayout = () => (
  <div className="flex min-h-screen bg-slate-50">
    <TeacherSidebar />
    <div className="flex-1 h-screen overflow-y-auto">
      <Outlet />
    </div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/ClassSelection" element={<Navigate to="/classselection" replace />} />
          <Route path="/classselection" element={<ClassSelection />} />
          <Route path="/SubjectSelection" element={<Navigate to="/subjectselection" replace />} />
          <Route path="/subjectselection" element={<SubjectSelection />} />
          <Route path="/LearningPreferences" element={<Navigate to="/learningpreferences" replace />} />
          <Route path="/learningpreferences" element={<LearningPreferences />} />
          <Route path="/AssessmentSplash" element={<Navigate to="/assessmentsplash" replace />} />
          <Route path="/assessmentsplash" element={<AssessmentSplash />} />

          <Route element={<OnboardingGuard />}>
            <Route element={<StudentLayout />}>
              <Route path="/mastery-path" element={<ExplainMistakePage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/quiz/:quizId" element={<Quizzes />} />
              <Route path="/quiz/:quizId/in-progress" element={<InProgress />} />
              <Route path="/quiz/:quizId/completed" element={<Completed />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/learning-path" element={<LessonPage />} />
              <Route path="/module-quiz" element={<ModuleQuizPage />} />
              <Route path="/quiz-result" element={<QuizResult />} />
            </Route>
          </Route>

          <Route path="/teacher" element={<TeacherLayout />}>
            <Route index element={<Navigate to="analytics" replace />} />
            <Route path="analytics" element={<ConceptAnalyticsPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
