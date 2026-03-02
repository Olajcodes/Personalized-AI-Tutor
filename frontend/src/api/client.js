const DEFAULT_TIMEOUT_MS = Number(import.meta.env.VITE_REQUEST_TIMEOUT_MS || 30000);

const BACKEND_BASE_URL = (
  import.meta.env.VITE_BACKEND_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const API_PREFIX = "/api/v1";

export const SUBJECTS = ["math", "english", "civic"];
export const LEVELS = ["SSS1", "SSS2", "SSS3"];
export const TERMS = [1, 2, 3];

function buildUrl(path, query) {
  const url = new URL(`${BACKEND_BASE_URL}${API_PREFIX}${path}`);
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") return;
      if (Array.isArray(value)) {
        value.forEach((item) => url.searchParams.append(key, String(item)));
      } else {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
}

async function request(path, { method = "GET", token, body, query, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const headers = { "Content-Type": "application/json" };
    if (token) headers.Authorization = `Bearer ${token}`;

    const response = await fetch(buildUrl(path, query), {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
      ? await response.json().catch(() => null)
      : await response.text().catch(() => null);

    if (!response.ok) {
      const detail =
        typeof payload === "object" && payload !== null
          ? payload.detail || JSON.stringify(payload)
          : payload || `Request failed with status ${response.status}`;
      throw new Error(detail);
    }
    return payload;
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error(`Request timeout after ${timeoutMs}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export function decodeJwt(token) {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(window.atob(base64));
  } catch {
    return {};
  }
}

export function normalizeUserId(authPayload) {
  if (!authPayload) return null;
  return (
    authPayload.user_id ||
    authPayload.student_id ||
    authPayload.id ||
    decodeJwt(authPayload.access_token || "").user_id ||
    decodeJwt(authPayload.access_token || "").student_id ||
    null
  );
}

export const api = {
  authRegister: (payload) => request("/auth/register", { method: "POST", body: payload }),
  authLogin: (payload) => request("/auth/login", { method: "POST", body: payload }),
  getMetadataSubjects: () => request("/metadata/subjects"),
  getMetadataLevels: () => request("/metadata/levels"),
  getUserMe: (token) => request("/users/me", { token }),
  updateUserMe: (token, payload) => request("/users/me", { method: "PUT", token, body: payload }),
  setupProfile: (token, payload) => request("/students/profile/setup", { method: "POST", token, body: payload }),
  getProfileStatus: (token) => request("/students/profile/status", { token }),
  getProfile: (token) => request("/students/profile", { token }),
  updateProfile: (token, payload) => request("/students/profile", { method: "PUT", token, body: payload }),
  updatePreferences: (token, userId, payload) =>
    request(`/users/${userId}/preferences`, { method: "PUT", token, body: payload }),
  getStudentStats: (token) => request("/students/stats", { token }),
  getLeaderboard: (token, limit = 10) => request("/students/leaderboard", { token, query: { limit } }),
  getMastery: (token, query) => request("/learning/mastery", { token, query }),
  listTopics: (query, token) => request("/learning/topics", { query, token }),
  getTopicLesson: (topicId, studentId, token) =>
    request(`/learning/topics/${topicId}/lesson`, { token, query: { student_id: studentId } }),
  logActivity: (token, payload) => request("/learning/activity/log", { method: "POST", token, body: payload }),
  startSession: (token, payload) => request("/tutor/sessions/start", { method: "POST", token, body: payload }),
  getSessionHistory: (token, sessionId, studentId) =>
    request(`/tutor/sessions/${sessionId}/history`, { token, query: { student_id: studentId } }),
  endSession: (token, sessionId, studentId, payload) =>
    request(`/tutor/sessions/${sessionId}/end`, { method: "POST", token, query: { student_id: studentId }, body: payload }),
  tutorChat: (token, payload) => request("/tutor/chat", { method: "POST", token, body: payload }),
  tutorHint: (token, payload) => request("/tutor/hint", { method: "POST", token, body: payload }),
  tutorExplainMistake: (token, payload) => request("/tutor/explain-mistake", { method: "POST", token, body: payload }),
  quizGenerate: (token, payload) => request("/learning/quizzes/generate", { method: "POST", token, body: payload }),
  quizSubmit: (token, quizId, payload) =>
    request(`/learning/quizzes/${quizId}/submit`, { method: "POST", token, body: payload }),
  quizResults: (token, quizId, studentId, attemptId) =>
    request(`/learning/quizzes/${quizId}/results`, {
      token,
      query: { student_id: studentId, attempt_id: attemptId },
    }),
  diagnosticStart: (token, payload) => request("/learning/diagnostic/start", { method: "POST", token, body: payload }),
  diagnosticSubmit: (token, payload) => request("/learning/diagnostic/submit", { method: "POST", token, body: payload }),
};
