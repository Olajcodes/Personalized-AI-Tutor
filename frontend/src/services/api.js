import { API_URL } from '../config/runtime';

const DEFAULT_TIMEOUT_MS = 20000;

const buildHeaders = (token, extraHeaders = {}) => ({
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
  'Content-Type': 'application/json',
  ...extraHeaders,
});

const createTimeoutSignal = (timeoutMs = DEFAULT_TIMEOUT_MS) => {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  return { controller, timeoutId };
};

export const parseJsonResponse = async (response, fallbackMessage) => {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    const preview = (await response.text().catch(() => '')).slice(0, 120).trim();
    throw new Error(
      `${fallbackMessage} The app received HTML instead of API JSON. Check VITE_API_URL. ${preview}`
    );
  }

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload?.detail || fallbackMessage);
  }

  return payload;
};

export const apiFetchJson = async (
  path,
  {
    token,
    method = 'GET',
    body,
    headers = {},
    timeoutMs = DEFAULT_TIMEOUT_MS,
    signal,
  } = {},
) => {
  const url = path.startsWith('http') ? path : `${API_URL}${path}`;
  const timeout = signal ? null : createTimeoutSignal(timeoutMs);

  try {
    const response = await fetch(url, {
      method,
      headers: buildHeaders(token, headers),
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: signal || timeout?.controller.signal,
    });

    if (timeout) {
      window.clearTimeout(timeout.timeoutId);
    }
    return await parseJsonResponse(response, `Request failed for ${method} ${path}.`);
  } catch (error) {
    if (timeout) {
      window.clearTimeout(timeout.timeoutId);
    }
    if (error?.name === 'AbortError') {
      throw new Error('The server is taking too long. Please try again.');
    }
    throw error;
  }
};

export const fetchUserProfile = async (token) =>
  apiFetchJson('/users/me', {
    token,
  });

export const updateUserProfile = async (token, profileData) =>
  apiFetchJson('/users/me', {
    token,
    method: 'PUT',
    body: profileData,
  });

export const fetchStudentProfile = async (token) => {
  try {
    return await apiFetchJson('/students/profile', { token });
  } catch (error) {
    console.warn('fetchStudentProfile Error:', error.message);
    throw error;
  }
};

export const fetchStudentProfileStatus = async (token) => {
  try {
    return await apiFetchJson('/students/profile/status', { token });
  } catch (error) {
    console.warn('fetchStudentProfileStatus Error:', error.message);
    throw error;
  }
};

export const updateStudentProfile = async (token, payload) =>
  apiFetchJson('/students/profile', {
    token,
    method: 'PUT',
    body: payload,
  });

export const setupStudentProfile = async (token, payload) =>
  apiFetchJson('/students/profile/setup', {
    token,
    method: 'POST',
    body: payload,
  });

export const updateStudentPreferences = async (token, userId, payload) =>
  apiFetchJson(`/users/${userId}/preferences`, {
    token,
    method: 'PUT',
    body: payload,
  });

export const fetchDiagnosticStatus = async (token, studentId) =>
  apiFetchJson(`/learning/diagnostic/status?student_id=${encodeURIComponent(studentId)}`, {
    token,
  });

export const startDiagnosticSession = async (token, payload) =>
  apiFetchJson('/learning/diagnostic/start', {
    token,
    method: 'POST',
    body: payload,
    timeoutMs: 30000,
  });

export const submitDiagnosticSession = async (token, payload) =>
  apiFetchJson('/learning/diagnostic/submit', {
    token,
    method: 'POST',
    body: payload,
    timeoutMs: 30000,
  });
