import { API_URL } from '../config/runtime';

const parseJsonResponse = async (response, fallbackMessage) => {
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

export const fetchUserProfile = async (token) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 20000);

  try {
    const response = await fetch(`${API_URL}/users/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return await parseJsonResponse(response, 'Failed to fetch user profile.');
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
};

export const updateUserProfile = async (token, profileData) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 20000);

  try {
    const response = await fetch(`${API_URL}/users/me`, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profileData),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return await parseJsonResponse(response, 'Failed to update profile.');
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('The server is taking too long. Please try again.');
    }
    throw error;
  }
};

export const fetchStudentProfile = async (token) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 20000);

  try {
    const response = await fetch(`${API_URL}/students/profile`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return await parseJsonResponse(response, 'Failed to fetch student profile.');
  } catch (error) {
    clearTimeout(timeoutId);
    console.warn('fetchStudentProfile Error:', error.message);
    throw error;
  }
};
