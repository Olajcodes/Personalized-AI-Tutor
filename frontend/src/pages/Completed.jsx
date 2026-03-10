import React from 'react';
import { useNavigate } from "react-router-dom"; 

export default function CompletedPage() {
  const navigate = useNavigate(); 

  const mockResults = {
    score: 10,
    totalQuestions: 12,
    percentageScore: 83,
    userName: 'Alex',
    conceptsMastery: [
      {
        concept: 'Whole Numbers',
        masteryLevel: 85,
        status: 'completed',
        icon: '✓',
        bgColor: 'bg-green-100',
        badgeColor: 'text-green-700'
      },
      {
        concept: 'Place Value',
        masteryLevel: 92,
        status: 'completed',
        icon: '✓',
        bgColor: 'bg-green-100',
        badgeColor: 'text-green-700'
      },
      {
        concept: 'Addition',
        masteryLevel: 78,
        status: 'growth',
        icon: '🚀',
        bgColor: 'bg-orange-100',
        badgeColor: 'text-orange-700'
      },
      {
        concept: 'Fractions',
        masteryLevel: 45,
        status: 'locked',
        icon: '🔒',
        bgColor: 'bg-gray-100',
        badgeColor: 'text-gray-700'
      },
      {
        concept: 'Decimals',
        masteryLevel: 32,
        status: 'locked',
        icon: '🔒',
        bgColor: 'bg-gray-100',
        badgeColor: 'text-gray-700'
      }
    ],
    aiInsights: [
      'You have mastered whole numbers and place value perfectly! These foundational skills show strong progress.',
      'Your addition skills are developing well. You\'re on the right track and with a bit more practice, you\'ll reach full mastery.',
      'Fractions will be unlocked once you complete more addition exercises. This creates a proper learning sequence.',
      'Keep maintaining your momentum! You\'re progressing faster than the average student.'
    ]
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <header className="bg-white shadow-sm" style={{ borderTop: "4px solid #0EA5E9" }}>
        <div className="container mx-auto px-6 py-4 flex items-center gap-2">
          <div className="w-8 h-8 rounded flex items-center justify-center" style={{ backgroundColor: "#7F13EC" }}>
            <span className="text-white font-bold text-sm">M</span>
          </div>
          <span className="font-bold text-gray-900">MasteryAI</span>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Assessment Complete Header */}
          <div className="mb-8">
            <p className="text-xs font-bold tracking-widest mb-2" style={{ color: '#7F13EC' }}>ASSESSMENT COMPLETE</p>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Here's Your Starting Point, <span style={{ color: '#7F13EC' }}>{mockResults.userName}!</span>
            </h1>
            <p className="text-gray-600 text-lg">
              We've analyzed your diagnostic results for ss1 Math. Your personalized<br />
              learning path is ready to help you achieve 100% mastery.
            </p>
          </div>

          {/* Three Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
            {/* Strong Areas - Green */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl p-6" style={{ border: '2px solid #86EFAC' }}>
              <div className="text-4xl mb-4">😊</div>
              <p className="text-xs font-bold text-green-700 tracking-widest mb-2">COMPLETED</p>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Strong Areas</h3>
              <p className="text-sm text-gray-700">
                You've mastered these! Keep using these<br />
                skills as your foundation.
              </p>
              <div className="mt-4 space-y-2 text-sm">
                <p className="text-gray-700">
                  <span className="font-semibold">Whole Numbers</span>
                </p>
                <p className="text-gray-700">
                  <span className="font-semibold">Place Value</span>
                </p>
              </div>
            </div>

            {/* Growth Areas - Orange */}
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-2xl p-6" style={{ border: '2px solid #FDBA74' }}>
              <div className="text-4xl mb-4">🚀</div>
              <p className="text-xs font-bold text-orange-700 tracking-widest mb-2">NEXT UP</p>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Growth Areas</h3>
              <p className="text-sm text-gray-700">
                You're still learning these. Focus<br />
                here to unlock advanced concepts.
              </p>
              <div className="mt-4 space-y-2 text-sm">
                <p className="text-gray-700">
                  <span className="font-semibold">Fractions</span>
                </p>
                <p className="text-gray-700">
                  <span className="font-semibold">Decimals</span>
                </p>
              </div>
            </div>

            {/* Locked Topics - Gray */}
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-6" style={{ border: '2px solid #D1D5DB' }}>
              <div className="text-4xl mb-4">🔒</div>
              <p className="text-xs font-bold text-gray-600 tracking-widest mb-2">LOCKED</p>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Locked Topics</h3>
              <p className="text-sm text-gray-700">
                Complete growth areas to unlock a<br />
                solid foundation for every topic.
              </p>
              <div className="mt-4 space-y-2 text-sm">
                <p className="text-gray-500">
                  <span className="font-semibold">Algebra Basics</span>
                </p>
                <p className="text-gray-500">
                  <span className="font-semibold">Geometry</span>
                </p>
              </div>
            </div>
          </div>
          
          {/* How Prerequisites Work Section */}
          <div className="rounded-2xl p-8 mb-12" style={{ backgroundColor: '#F3F0FF', borderLeft: '4px solid #7F13EC' }}>
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#7F13EC' }}>
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v2h8v-2zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-2a4 4 0 00-8 0v2h8z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">How prerequisites work</h3>
                <p className="text-gray-700 text-sm">
                  Our AI maps your path: Mastering the orange topics first ensures you have the right foundation needed to tackle the locked, advanced concepts successfully.
                </p>
              </div>
            </div>
          </div>

          {/* Start Learning Button */}
          <div className="text-center mb-12">
            <button
              onClick={() => navigate('/dashboard')}
              type="button" 
              className="text-white font-bold py-4 px-8 rounded-full text-lg transition-all hover:opacity-90 cursor-pointer"
              style={{ backgroundColor: "#7F13EC" }}
            >
              Start Learning ➤
            </button>
            <p className="text-sm text-gray-500 mt-3">
              Estimated first lesson: 12 mins
            </p>
          </div>

        </div>
      </div>
    </main>
  );
}
