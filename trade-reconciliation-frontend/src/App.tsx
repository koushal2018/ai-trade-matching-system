import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Layout Components
import MainLayout from './components/layout/MainLayout';
import AuthLayout from './components/auth/AuthLayout';

// Auth Components
import Login from './components/auth/Login';

// Page Components
import Dashboard from './components/pages/Dashboard';
import DocumentUpload from './components/pages/DocumentUpload';
import Trades from './components/pages/Trades';
import AgentMonitorPage from './components/pages/agent-monitor/AgentMonitorPage';

// Error Handling and Notifications
import ErrorBoundary from './components/common/ErrorBoundary';
import { ToastProvider } from './context/ToastContext';

// Styles
import './App.css';

// Simple Auth Context for now
interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = React.useState(false);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('authToken');
    setIsAuthenticated(!!token);
    setLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    // Simple mock login - replace with actual API call
    if (username === 'admin' && password === 'password') {
      localStorage.setItem('authToken', 'mock-token');
      setIsAuthenticated(true);
    } else {
      throw new Error('Invalid credentials');
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Public Route Component
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return !isAuthenticated ? <>{children}</> : <Navigate to="/dashboard" replace />;
};

// Main App Component
const App: React.FC = () => {
  return (
    <AuthProvider>
      <ToastProvider>
        <ErrorBoundary>
          <Router>
            <div className="App">
              <Routes>
                {/* Auth Routes */}
                <Route path="/auth" element={<AuthLayout />}>
                  <Route 
                    path="login" 
                    element={
                      <PublicRoute>
                        <Login />
                      </PublicRoute>
                    } 
                  />
                </Route>
                <Route path="/login" element={<Navigate to="/auth/login" replace />} />

              {/* Protected Routes */}
              <Route 
                path="/" 
                element={
                  <ProtectedRoute>
                    <MainLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="upload" element={<DocumentUpload />} />
                <Route path="trades" element={<Trades />} />
                
                {/* Agent Monitor Route */}
                <Route 
                  path="agent-monitor" 
                  element={<AgentMonitorPage />} 
                />
                
                {/* Placeholder routes for future features */}
                <Route 
                  path="match-review" 
                  element={
                    <div className="p-6">
                      <h1 className="text-2xl font-bold mb-4">Match Review</h1>
                      <p className="text-gray-600">Coming soon...</p>
                    </div>
                  } 
                />
                <Route 
                  path="reconciliation" 
                  element={
                    <div className="p-6">
                      <h1 className="text-2xl font-bold mb-4">Reconciliation Detail</h1>
                      <p className="text-gray-600">Coming soon...</p>
                    </div>
                  } 
                />
                <Route 
                  path="reports" 
                  element={
                    <div className="p-6">
                      <h1 className="text-2xl font-bold mb-4">Reports</h1>
                      <p className="text-gray-600">Coming soon...</p>
                    </div>
                  } 
                />
                <Route 
                  path="admin" 
                  element={
                    <div className="p-6">
                      <h1 className="text-2xl font-bold mb-4">Admin Settings</h1>
                      <p className="text-gray-600">Coming soon...</p>
                    </div>
                  } 
                />
                
                {/* Catch all */}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Route>
            </Routes>
          </div>
        </Router>
        </ErrorBoundary>
      </ToastProvider>
    </AuthProvider>
  );
};

export default App;