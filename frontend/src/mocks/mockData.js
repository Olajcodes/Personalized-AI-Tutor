// types.js (or just a reference for your team)
export const mockData = {
  originalQuestion: {
    text: "What is the primary difference between Heat and Temperature in a closed system?",
    userAnswer: "Heat is the measure of how hot or cold an object feels.",
    correctAnswer: "Heat is the total energy of molecular motion, while temperature is the average energy.",
  },
  topicInsight: {
    topic: "JSS2 Basic Science - Topic 2.1",
    masteryRate: 65,
  },
  explanation: {
    misconception: "It's very common to think of heat and temperature as the same thing... However, you're confusing Total Energy with Average Concentration.",
    analogy: {
      title: "Think of it like a Swimming Pool vs. a Cup of Tea",
      item1: { label: "A lukewarm pool has more HEAT (total energy).", img: "/pool.jpg" },
      item2: { label: "A small cup of boiling tea has a higher TEMPERATURE (average energy).", img: "/tea.jpg" }
    },
    breakdown: [
      { term: "Temperature", definition: "tells you how fast the molecules are moving on average..." },
      { term: "Heat", definition: "is the sum total of all that movement energy..." }
    ]
  },
  practice: {
    question: "If you take 1 liter of water at 50°C and 2 liters of water at 50°C, which statement is true?",
    options: [
      { id: 'a', text: "Both have the same amount of heat energy." },
      { id: 'b', text: "Both have the same temperature, but the 2L container has more heat." },
      { id: 'c', text: "The 2L container has a higher temperature." }
    ],
    projectedMastery: 72
  }
};