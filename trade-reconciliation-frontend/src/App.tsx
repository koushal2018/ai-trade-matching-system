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
                element={
                  <div className="p-6">
                    <h1 className="text-2xl font-bold mb-4">Agent Monitor</h1>
                    <div className="bg-white rounded-lg shadow p-6">
                      <h2 className="text-lg font-semibold mb-4">AI Agent Execution Status</h2>
                      <div className="space-y-4">
                        <div className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">Trade PDF Processing Agent</span>
                            <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm">Running</span>
                          </div>
                          <p className="text-sm text-gray-600">Processing uploaded trade documents...</p>
                          <div className="mt-2">
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div className="bg-blue-600 h-2 rounded-full" style={{width: '75%'}}></div>
                            </div>
                            <p className="text-xs text-gray-500 mt-1">75% complete</p>
                          </div>
                        </div>
                        
                        <div className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">Trade Matching Agent</span>
                            <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">Queued</span>
                          </div>
                          <p className="text-sm text-gray-600">Waiting for PDF processing to complete...</p>
                        </div>
                        
                        <div className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">Reconciliation Agent</span>
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">Idle</span>
                          </div>
                          <p className="text-sm text-gray-600">Ready to process matched trades...</p>
                        </div>
                      </div>
                      
                      <div className="mt-6">
                        <h3 className="text-md font-semibold mb-3">Recent Agent Logs</h3>
                        <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                          <div className="space-y-2 font-mono text-sm">
                            <div className="text-green-600">[2025-07-18 17:08:15] PDF Processing: Successfully extracted 45 trades from document_001.pdf</div>
                            <div className="text-blue-600">[2025-07-18 17:08:10] Matching: Found 42 potential matches for trade batch #123</div>
                            <div className="text-yellow-600">[2025-07-18 17:08:05] Validation: 3 trades require manual review</div>
                            <div className="text-gray-600">[2025-07-18 17:07:58] System: Agent pipeline initialized</div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-4 flex space-x-3">
                        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                          View Detailed Logs
                        </button>
                        <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
                          Export Logs
                        </button>
                        <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                          Restart Agents
                        </button>
                      </div>
                    </div>
                  </div>
                } 
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
    </AuthProvider>
  );
};

export default App;
