import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = () => {
  const { token } = useAuth();

  // If there is no token, kick them to the login page
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // If there is a token, render the child routes
  return <Outlet />;
};

export default ProtectedRoute;