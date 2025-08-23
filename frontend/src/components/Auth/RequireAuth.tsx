import React from 'react';
import { Navigate } from 'react-router-dom';

interface Props {
  children: React.ReactNode;
}

const RequireAuth: React.FC<Props> = ({ children }) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

export default RequireAuth;


