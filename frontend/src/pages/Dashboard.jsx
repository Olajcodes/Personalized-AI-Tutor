import React, { useEffect, useMemo, useState } from "react";
import { Flame, Star, CheckCircle2, Clock } from "lucide-react";

import HeroSection from "../components/HeroSection";
import AIRecommendation from "../components/AIRecommendation";
import StatCard from "../components/StatCard";
import LearningMap from "../components/LearningMap";
import LearningTasks from "../components/LearningTasks";
import Leaderboard from "../components/Leaderboard";
import Footer from "../components/Footer";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

const formatStudyTime = (seconds = 0) => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
};

export default function Dashboard() {
  const { token, userId, user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [stats, setStats] = useState(null);
  const [profile, setProfile] = useState(null);
  const [mapNodes, setMapNodes] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [recommendedTopic, setRecommendedTopic] = useState(null);
  const [topics, setTopics] = useState([]);

  useEffect(() => {
    let active = true;
    (async () => {
      if (!token || !userId) return;
      setLoading(true);
      setError("");
      try {
        const [me, studentProfile, studentStats, board] = await Promise.all([
          api.getUserMe(token),
          api.getProfile(token),
          api.getStudentStats(token),
          api.getLeaderboard(token, 10),
        ]);
        if (!active) return;
        refreshUser(me);
        setProfile(studentProfile);
        setStats(studentStats);
        setLeaderboard(
          (board || []).map((item, idx) => ({
            id: item.student_id || idx,
            rank: idx + 1,
            name: item.student_name,
            points: item.total_mastery_points,
            isCurrentUser: item.student_id === userId,
          })),
        );

        const primarySubject = studentProfile.subjects?.[0] || "math";
        const [mastery, topicList] = await Promise.all([
          api.getMastery(token, {
            student_id: userId,
            subject: primarySubject,
            term: studentProfile.current_term,
            view: "concept",
          }),
          api.listTopics({
            student_id: userId,
            subject: primarySubject,
            term: studentProfile.current_term,
          }),
        ]);
        if (!active) return;
        setTopics(topicList || []);

        const nodes = (mastery.mastery || []).slice(0, 5).map((item, idx) => ({
          id: item.concept_id || idx,
          status: item.score >= 0.85 ? "mastered" : idx === 0 ? "current" : "locked",
          title: item.concept_id,
          details: `${Math.round(item.score * 100)}% MASTERY`,
        }));
        setMapNodes(nodes);

        if (topicList?.length) {
          setRecommendedTopic(topicList[0]);
        }
      } catch (err) {
        if (!active) return;
        setError(err.message || "Failed to load dashboard");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [token, userId, refreshUser]);

  const userName = useMemo(() => {
    if (user?.display_name) return user.display_name;
    if (user?.first_name || user?.last_name) return `${user.first_name || ""} ${user.last_name || ""}`.trim();
    return "Student";
  }, [user]);

  if (!token || !userId) {
    return <div className="p-8 text-slate-700">You are not authenticated.</div>;
  }

  if (loading) {
    return <div className="p-8 text-slate-700">Loading dashboard...</div>;
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] font-sans">
      <main className="max-w-9xl mx-auto px-6 py-8">
        {error && <div className="mb-6 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">{error}</div>}

        <div className="flex flex-col lg:flex-row gap-6 mb-8">
          <HeroSection
            userName={userName}
            recentModules={3}
            currentSubject={`${profile?.sss_level || "SSS"} ${profile?.subjects?.[0] || "math"}`}
            hasStartedLearning={Boolean(profile)}
          />
          <AIRecommendation
            topic={recommendedTopic?.title || "No recommendation yet"}
            confidenceScore={82}
            nextConcept={topics[1]?.title || topics[0]?.title || "Next concept"}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={Flame}
            iconBg="bg-orange-50"
            iconColor="text-orange-500"
            title="Study Streak"
            value={`${stats?.current_streak || 0} Days`}
            subtext={`Best: ${stats?.max_streak || 0} days`}
            subtextColor="text-orange-500"
          />
          <StatCard
            icon={Star}
            iconBg="bg-yellow-50"
            iconColor="text-yellow-500"
            title="Mastery Points"
            value={`${stats?.total_mastery_points || 0}`}
            subtext="+0 today"
            subtextColor="text-gray-400"
          />
          <StatCard
            icon={CheckCircle2}
            iconBg="bg-green-50"
            iconColor="text-green-500"
            title="Concepts Mastered"
            value={`${mapNodes.filter((n) => n.status === "mastered").length} / ${mapNodes.length || 0}`}
          />
          <StatCard
            icon={Clock}
            iconBg="bg-blue-50"
            iconColor="text-blue-500"
            title="Study Time"
            value={formatStudyTime(stats?.total_study_time_seconds || 0)}
            subtext="Total"
            subtextColor="text-gray-400"
          />
        </div>

        <LearningMap classLevel={profile?.sss_level || "SSS"} subject={profile?.subjects?.[0] || "math"} nodes={mapNodes} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <LearningTasks />
          <Leaderboard items={leaderboard} leagueName="Class League" />
        </div>

        <Footer />
      </main>
    </div>
  );
}
