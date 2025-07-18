import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Amplify } from 'aws-amplify';
import { fetchAuthSession } from 'aws-amplify/auth';
import awsconfig from './aws-exports';
import { AMPLIFY_CONFIG } from './config';
import './App.css';

// Layouts
import MainLayout from './components/layout/MainLayout';
import AuthLayout from './components/auth/AuthLayout';

// Auth Pages
import Login from './components/auth/Login';

// Main Pages
import Dashboard from './components/pages/Dashboard';
import DocumentUpload from './components/pages/DocumentUpload';
import Trades from './components/pages/Trades';

// Configure Amplify with merged configuration
Amplify.configure({
  ...awsconfig,
  ...AMPLIFY_CONFIG
});

// Auth-protected route component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // For development, we'll just simulate authentication
        // In production, uncomment the line below:
        // await fetchAuthSession();
        setIsAuthenticated(true);
      } catch (error) {
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

function App() {
  return (
    <Router>
      <Routes>
        {/* Auth Routes */}
        <Route path="/" element={<AuthLayout />}>
          <Route path="login" element={<Login />} />
        </Route>

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="upload" element={<DocumentUpload />} />
          {/* Add more routes as you implement them */}
          <Route path="trades" element={<Trades />} />
          <Route path="matches" element={<div>Match Review - Coming Soon</div>} />
          <Route path="reconciliation" element={<div>Reconciliation Detail - Coming Soon</div>} />
          <Route path="reports" element={<div>Reports - Coming Soon</div>} />
          <Route path="admin" element={<div>Admin Settings - Coming Soon</div>} />
        </Route>

        {/* Catch-all route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;