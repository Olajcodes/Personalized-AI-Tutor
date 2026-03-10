import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { fetchUserProfile, fetchStudentProfile } from '../services/api'; 

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const { token } = useAuth();
  const [userData, setUserData] = useState(null);
  const [studentData, setStudentData] = useState(null); 
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      if (!token) {
        setUserData(null);
        setStudentData(null);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        // Fetch BOTH endpoints at the same time to make it load twice as fast!
        const [userResponse, studentResponse] = await Promise.all([
          fetchUserProfile(token),
          fetchStudentProfile(token)
        ]);
        
        setUserData(userResponse);
        setStudentData(studentResponse);
        
      } catch (error) {
        console.error("UserContext Error:", error);
        
        if (
          error.message === "Student profile not found" || 
          error.detail === "Student profile not found" ||
          (error.response && error.response.status === 404)
        ) {
          
          // 👇 THE FIX: Check what page the user is currently on 👇
          const currentPath = window.location.pathname;
          
          // Add all the routes that make up your onboarding flow here so the bouncer ignores them
          const isCurrentlyOnboarding = 
            currentPath === '/signup' ||
            currentPath === '/login' ||
            currentPath === '/class-selection' || 
            currentPath === '/subject-selection' || 
            currentPath === '/learning-preferences';

          // Only redirect them if they are trying to access a protected page (like Dashboard or Lesson)
          if (!isCurrentlyOnboarding) {
            console.warn("Incomplete profile detected. Redirecting to onboarding...");
            window.location.href = '/class-selection';
          }
          
          return;
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, [token]);

  const updateLocalUser = (newUserData) => {
    setUserData(prev => ({ ...prev, ...newUserData }));
  };

  const updateLocalStudent = (newStudentData) => {
    setStudentData(prev => ({ ...prev, ...newStudentData }));
  };

  return (
    <UserContext.Provider value={{ userData, studentData, isLoading, updateLocalUser, updateLocalStudent }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);