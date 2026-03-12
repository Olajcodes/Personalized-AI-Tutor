import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import HeroSection from '../components/HeroSection';
import AIRecommendation from '../components/AIRecommendation';
import DashboardStats from '../components/DashboardStats';
import LearningMap from '../components/LearningMap';
import LearningTasks from '../components/LearningTasks';
import Leaderboard from '../components/Leaderboard';
import Footer from '../components/Footer';
import { useAuth } from '../context/AuthContext';
import { useUser } from '../context/UserContext';

export default function Dashboard() {
    const { token } = useAuth();
    const { userData, studentData } = useUser();
    const navigate = useNavigate();

    const fullName = userData ? `${userData.first_name || ''} ${userData.last_name || ''}`.trim() : 'Student';
    const activeId = studentData?.user_id || userData?.id;
    const currentLevel = studentData?.sss_level || 'SSS1';
    const currentTerm = studentData?.current_term || 1;
    const enrolledSubjects = studentData?.subjects || [];

    const [activeSubject, setActiveSubject] = useState(null);
    const [mapData, setMapData] = useState({ nodes: [], edges: [], next_step: null });
    const [isLoadingMap, setIsLoadingMap] = useState(false);
    const [mapError, setMapError] = useState('');

    const apiUrl = import.meta.env.VITE_API_URL;

    useEffect(() => {
        if (studentData && (!studentData.subjects || studentData.subjects.length === 0)) {
            navigate('/class-selection');
        }
    }, [studentData, navigate]);

    useEffect(() => {
        if (!activeId || !token || !activeSubject) {
            return;
        }

        const fetchLearningMap = async () => {
            setIsLoadingMap(true);
            setMapError('');

            try {
                const queryParams = new URLSearchParams({
                    student_id: activeId,
                    subject: activeSubject,
                    term: currentTerm,
                });

                const response = await fetch(`${apiUrl}/learning/course/bootstrap?${queryParams.toString()}`, {
                    method: 'GET',
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    throw new Error('Failed to fetch learning map');
                }

                const data = await response.json();
                setMapData({
                    nodes: Array.isArray(data?.nodes) ? data.nodes : [],
                    edges: Array.isArray(data?.edges) ? data.edges : [],
                    next_step: data?.next_step || null,
                });
                setMapError(data?.map_error || '');
            } catch (err) {
                console.error('Map fetch error:', err);
                setMapData({ nodes: [], edges: [], next_step: null });
                setMapError(err.message || 'Learning map unavailable.');
            } finally {
                setIsLoadingMap(false);
            }
        };

        fetchLearningMap();
    }, [activeId, activeSubject, currentLevel, currentTerm, token, apiUrl]);

    const apiLeaderboardData = [
        { id: 'u1', rank: 1, name: 'Sarah Jenkins', points: '4,250' },
        { id: 'u2', rank: 2, name: 'Marcus Thorne', points: '3,900' },
        { id: 'u3', rank: 3, name: fullName, points: '3,450', isCurrentUser: true },
    ];

    return (
        <div className="min-h-screen bg-[#F8FAFC] font-sans">
            <main className="max-w-9xl mx-auto px-6 py-8">
                <div className="mb-8 flex flex-col gap-6 lg:flex-row">
                    <HeroSection
                        enrolledSubjects={enrolledSubjects}
                        activeSubject={activeSubject}
                        onSelectSubject={setActiveSubject}
                        hasStartedLearning={false}
                    />
                    <AIRecommendation
                        activeSubject={activeSubject}
                        recommendation={activeSubject ? mapData?.next_step : null}
                    />
                </div>

                <DashboardStats />

                {!activeSubject ? (
                    <div className="mb-8 flex w-full flex-col items-center justify-center rounded-3xl border border-slate-200 bg-white p-16 text-center shadow-sm">
                        <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-indigo-50 text-indigo-400 shadow-inner">
                            <svg className="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"></path></svg>
                        </div>
                        <h3 className="mb-3 text-2xl font-bold text-slate-800">Your Learning Map is Waiting</h3>
                        <p className="mx-auto max-w-md text-lg text-slate-500">Select a subject from the top section to generate your personalized AI curriculum map.</p>
                    </div>
                ) : isLoadingMap ? (
                    <div className="mb-8 flex w-full flex-col items-center rounded-3xl border border-slate-200 bg-white p-16 text-center font-medium text-indigo-500 shadow-sm animate-pulse">
                        <div className="mb-4 h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
                        Generating your personalized {activeSubject} path...
                    </div>
                ) : mapError ? (
                    <div className="mb-8 flex w-full flex-col items-center justify-center rounded-3xl border border-rose-200 bg-white p-16 text-center shadow-sm">
                        <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-rose-50 text-rose-400 shadow-inner">
                            <svg className="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v4m0 4h.01M5.07 19h13.86c1.54 0 2.5-1.67 1.73-3L13.73 4c-.77-1.33-2.69-1.33-3.46 0L3.34 16c-.77 1.33.19 3 1.73 3z"></path></svg>
                        </div>
                        <h3 className="mb-3 text-2xl font-bold text-slate-800">Learning Map Unavailable</h3>
                        <p className="mx-auto max-w-md text-lg text-slate-500">{mapError}</p>
                    </div>
                ) : (
                    <LearningMap
                        classLevel={currentLevel}
                        subject={activeSubject}
                        mapData={mapData}
                        onSelectTopic={(topicId) => navigate(`/lesson/${topicId}`)}
                    />
                )}

                <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
                    <LearningTasks />
                    <Leaderboard items={apiLeaderboardData} leagueName="Gold League" />
                </div>

                <Footer />
            </main>
        </div>
    );
}
