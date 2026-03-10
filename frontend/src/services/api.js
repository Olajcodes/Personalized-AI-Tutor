const API_URL = import.meta.env.VITE_API_URL; // Imports the url set in the environment

export const fetchUserProfile = async (token) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 20000); // 20 second timeout

  try {
    const response = await fetch(`${API_URL}/users/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) throw new Error("Failed to fetch user profile");
    
    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
};


export const updateUserProfile = async (token, profileData) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 20000); // 20s timeout

  try {
    const response = await fetch(`${API_URL}/users/me`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(profileData),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errData = await response.json().catch(() => null);
      throw new Error(errData?.detail || "Failed to update profile.");
    }
    
    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error("The server is taking too long. Please try again.");
    }
    throw error;
  }
};

// src/services/api.js

export const fetchStudentProfile = async (token) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 20000);

  try {
    const response = await fetch(`${API_URL}/students/profile`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    // 👇 Let the error be thrown so the Context can catch it!
    if (!response.ok) {
      const errData = await response.json().catch(() => null);
      
      // We throw the exact detail from the backend (e.g., "Student profile not found")
      // or default to a generic message if the backend didn't send a detail.
      throw new Error(errData?.detail || "Failed to fetch student profile");
    }
    
    return await response.json();
    
  } catch (error) {
    clearTimeout(timeoutId);
    console.warn("fetchStudentProfile Error:", error.message);
    
    // 👇 WE MUST RE-THROW THE ERROR HERE
    // If we just return null, the UserContext won't know it failed.
    throw error; 
  }
};