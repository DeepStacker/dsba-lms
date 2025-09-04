import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuthStore } from './stores/useAuthStore';
import MainLayout from './layouts/MainLayout';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import UserManagement from './pages/UserManagement';
import ProgramManagement from './pages/ProgramManagement';
import ExamManagement from './pages/ExamManagement';
import QuestionBank from './pages/QuestionBank';
import Analytics from './pages/Analytics';
import { ExamInterface } from './components/exam/ExamInterface';

// Loading Spinner Component
const LoadingSpinner: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      <p className="mt-4 text-gray-600">Loading...</p>
    </div>
  </div>
);

// Protected Route Component
interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
  redirectTo?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles = [],
  redirectTo = '/login'
}) => {
  const { user, isAuthenticated, isLoading } = useAuthStore();

  // Show loading spinner while auth is being initialized
  if (isLoading) {
    return <LoadingSpinner />;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !user) {
    return <Navigate to={redirectTo} replace />;
  }

  // Check role permissions
  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
          <p className="text-gray-600 mb-6">You don't have permission to access this page.</p>
          <button
            onClick={() => window.location.href = '/dashboard'}
            className="text-blue-600 hover:text-blue-500 font-medium"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return <MainLayout>{children}</MainLayout>;
};

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<LoginPage />} />

      {/* Student Exam Interface (Special Route) */}
      <Route
        path="/exam/:examId"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <ExamInterface />
          </ProtectedRoute>
        }
      />

      {/* Protected Routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      {/* Admin Routes */}
      <Route
        path="/users"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <UserManagement />
          </ProtectedRoute>
        }
      />

      {/* Admin & Teacher Routes */}
      <Route
        path="/programs"
        element={
          <ProtectedRoute allowedRoles={['admin', 'teacher']}>
            <ProgramManagement />
          </ProtectedRoute>
        }
      />

      <Route
        path="/questions"
        element={
          <ProtectedRoute allowedRoles={['admin', 'teacher']}>
            <QuestionBank />
          </ProtectedRoute>
        }
      />

      <Route
        path="/analytics"
        element={
          <ProtectedRoute allowedRoles={['admin', 'teacher']}>
            <Analytics />
          </ProtectedRoute>
        }
      />

      {/* All Roles Routes */}
      <Route
        path="/exams"
        element={
          <ProtectedRoute>
            <ExamManagement />
          </ProtectedRoute>
        }
      />

      {/* Admin Only Routes */}
      <Route
        path="/audit"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <div className="p-6">
              <h1 className="text-2xl font-bold mb-6">Audit Logs</h1>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-gray-600">
                  Comprehensive audit log viewer and compliance reports will be available here.
                  This includes user actions, grade changes, exam activities, and system events.
                </p>
              </div>
            </div>
          </ProtectedRoute>
        }
      />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      
      {/* 404 Page */}
      <Route path="*" element={
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <h1 className="text-6xl font-bold text-gray-900">404</h1>
            <p className="text-gray-600 mt-4 mb-6">Page not found</p>
            <button
              onClick={() => window.location.href = '/dashboard'}
              className="text-blue-600 hover:text-blue-500 font-medium"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      } />
    </Routes>
  );
};

const App: React.FC = () => {
  const { initializeAuth } = useAuthStore();

  // Initialize authentication on app start
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return (
    <Router>
      <AppRoutes />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#ffffff',
            color: '#374151',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10B981',
              secondary: '#ffffff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#EF4444',
              secondary: '#ffffff',
            },
          },
        }}
      />
    </Router>
  );
};

export default App;