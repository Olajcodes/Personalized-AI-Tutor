export const analyticsData = {
  stats: {
    classMastery: { value: "78.4%", trend: "+3.2% vs last week", icon: "⭐" },
    velocity: { value: "4.2", subtitle: "Concepts per student / month", icon: "⚡" },
    interventions: { value: "124", subtitle: "Auto-assigned practices", icon: "🤖" }
  },
  heatmap: {
    concepts: ["PHOTOSYNTHESIS BASICS", "CELL STRUCTURE", "ENERGY FLOW", "LIGHT REACTIONS", "CARBON CYCLE"],
    students: [
      { id: 1, name: "Alex Rivera", scores: [94, 88, 32, 64, null] },
      { id: 2, name: "Bela Chen", scores: [45, 92, 98, 28, 71] },
      { id: 3, name: "Chris Jordan", scores: [82, 85, 91, 86, 93] },
      { id: 4, name: "Dana Smith", scores: [61, 74, 48, null, 31] }
    ]
  },
  alerts: [
    {
      id: 1,
      student: "Alex Rivera",
      avatar: "https://i.pravatar.cc/150?img=11",
      tag: "CRITICAL PLATEAU",
      tagColor: "text-rose-600 bg-rose-50",
      reason: "Repeated prerequisite failures in Energy Transformation causing 0% progress in photosynthesis modules.",
      actionText: "Review Progress"
    },
    {
      id: 2,
      student: "Bela Chen",
      avatar: "https://i.pravatar.cc/150?img=5",
      tag: "INCONSISTENT MASTERY",
      tagColor: "text-amber-600 bg-amber-50",
      reason: "High score on quizzes but 0% engagement on required reading. Probability of guessing identified.",
      actionText: "Validate Concepts"
    }
  ],
  interventions: [
    {
      id: 1,
      type: "GROUP",
      typeColor: "bg-indigo-100 text-indigo-700",
      target: "6 students struggling with Photosynthesis Prereqs",
      actionSecondary: "Dismiss",
      actionPrimary: "Approve Bridge Quiz"
    },
    {
      id: 2,
      type: "SOLO",
      typeColor: "bg-amber-100 text-amber-700",
      target: "Alex Rivera needs Cell Structure 101 recap",
      actionSecondary: "Modify",
      actionPrimary: "Assign Practice"
    }
  ]
};