import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

export default function InProgress() {
  const navigate = useNavigate();
  const { quizId } = useParams();

  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);

    const steps = [
    {
      id: 0,
      title: 'Analyzing strengths',
      description: 'Identifying what you already know perfectly.',
      duration: 3000,
      icon: '✓',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      badgeBg: 'bg-green-500'
    },
    {
      id: 1,
      title: 'Detecting gaps',
      description: 'Spotting areas that need extra focus and revision.',
      duration: 4000,
      icon: '!',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-300',
      badgeBg: 'bg-purple-600'
    },
    {
      id: 2,
      title: 'Mapping prerequisites',
      description: 'Ensuring you have the right foundation for every topic',
      duration: 5000,
      icon: '→',
      bgColor: 'bg-gray-50',
      borderColor: 'border-gray-200',
      badgeBg: 'bg-gray-300'
    }
  ]

  /* 🔄 Progress animation + redirect */
  useEffect(() => {
    const totalTime = steps.reduce((sum, step) => sum + step.duration, 0);
    const increment = 100 / (totalTime / 100);

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            navigate(`/quiz/${quizId}/completed`);
          }, 1500);
          return 100;
        }
        return prev + increment;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [navigate, quizId]);

  /* 🧠 Step switching */
  useEffect(() => {
    if (progress < 30) setCurrentStep(0);
    else if (progress < 70) setCurrentStep(1);
    else setCurrentStep(2);
  }, [progress]);

  return (
    <main className="min-h-screen" style={{ backgroundColor: "#F3F0FF" }}>
      {/* Header */}
      <header className="bg-white border-b-2 shadow-sm" style={{ borderColor: "#7F13EC" }}>
        <div className="container mx-auto px-6 py-4 flex items-center">
          <div className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded flex items-center justify-center"
              style={{ backgroundColor: "#7F13EC" }}
            >
              <span className="text-white font-bold text-sm">M</span>
            </div>
            <span className="font-bold text-gray-900">MasteryAI</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
          <div className="container mx-auto px-6 py-20">
        <div className="max-w-2xl mx-auto">
          {/* Card */}
          <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
            {/* Brain Icon */}
            <div className="mb-8 flex justify-center">
              <div className="w-24 h-24 rounded-full flex items-center justify-center" style={{ backgroundColor: '#F3F0FF' }}>
                <svg
                  className="w-14 h-14"
                  style={{ color: '#7F13EC' }}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M12 6v6m0 0v6m0-6h6m0 0h6m0 0v6m0-6v-6m0 0h-6m0 0h-6m0 0v-6m0 6v6"
                  />
                </svg>
              </div>
            </div>


           {/* Title and Description */}
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
              Building Your Learning Path...
            </h2>

            <p className="text-gray-600 text-base mb-8 leading-relaxed">
              Our AI is analyzing your diagnostic results to<br />
              create a mastery-based journey for JSS Math.
            </p>

            {/* Status Section */}
            <div className="mb-8">
              <p className="text-xs font-bold text-gray-500 tracking-widest mb-3">GLOBAL STATUS</p>
              <p className="text-lg font-bold text-gray-900 mb-4">AI Analysis in progress</p>
              
              {/* Progress Bar */}
              <div className="relative mb-3">
                <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full transition-all duration-300"
                    style={{ backgroundColor: '#7F13EC', width: `${progress}%` }}
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <span className="text-2xl font-bold" style={{ color: '#7F13EC' }}>{Math.round(progress)}%</span>
              </div>
            </div>

            {/* Status Message */}
            <p className="text-sm text-gray-500 mb-12 italic">
              "Tailoring Algebra modules to your current level..."
            </p>

            {/* Steps */}
            <div className="space-y-3 text-left">
              {steps.map((step) => {
                let status = 'waiting'
                if (currentStep > step.id) status = 'completed'
                else if (currentStep === step.id) status = 'in-progress'

               return (
                  <div
                    key={step.id}
                    className="p-4 rounded-xl border-2 transition-all"
                    style={{
                      backgroundColor: status === 'completed' ? '#F0FDF4' : status === 'in-progress' ? '#F3F0FF' : '#F9FAFB',
                      borderColor: status === 'completed' ? '#86EFAC' : status === 'in-progress' ? '#7F13EC' : '#E5E7EB'
                    }}
                  >
                    <div className="flex items-start gap-4">
                      <div
                        className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 font-bold text-sm"
                        style={{
                          backgroundColor: status === 'completed' ? '#22C55E' : status === 'in-progress' ? '#7F13EC' : '#D1D5DB',
                          color: status === 'completed' ? '#FFFFFF' : status === 'in-progress' ? '#FFFFFF' : '#6B7280',
                          animation: status === 'in-progress' ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : 'none'
                        }}
                      >
                        {status === 'completed' ? '✓' : step.icon}
                      </div>
                      <div className="flex-1">
                        <h3 className={`font-bold text-sm mb-1 ${
                          status === 'waiting' ? 'text-gray-500' : 'text-gray-900'
                        }`}>
                          {step.title}
                        </h3>
                        <p className={`text-sm ${
                          status === 'waiting' ? 'text-gray-400' : 'text-gray-600'
                        }`}>
                          {step.description}
                        </p>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Timeline Visualization */}
            <div className="mt-12 pt-8 border-t border-gray-200">
              <p className="text-xs font-bold text-gray-500 tracking-widest mb-4">LIVE GRAPH COMPUTATION</p>
              <div className="flex items-center justify-center gap-2">
                <div
                  className={`w-3 h-3 rounded-full ${progress < 40 ? 'animate-pulse' : ''}`}
                  style={{
                    backgroundColor: progress > 20 ? '#7F13EC' : '#D1D5DB'
                  }}
                />
                <div
                  className="h-1 flex-1"
                  style={{
                    backgroundColor: progress > 30 ? '#C4B5FD' : '#E5E7EB'
                  }}
                />
                <div
                  className={`w-3 h-3 rounded-full ${progress < 70 && progress > 50 ? 'animate-pulse' : ''}`}
                  style={{
                    backgroundColor: progress > 50 ? '#7F13EC' : '#D1D5DB'
                  }}
                />
                <div
                  className="h-1 flex-1"
                  style={{
                    backgroundColor: progress > 70 ? '#C4B5FD' : '#E5E7EB'
                  }}
                />
                <div
                  className={`w-3 h-3 rounded-full ${progress > 80 ? 'animate-pulse' : ''}`}
                  style={{
                    backgroundColor: progress > 80 ? '#7F13EC' : '#D1D5DB'
                  }}
                />
              </div>
              </div>
          </div>
        </div>
      </div>
    </main>
  );
}