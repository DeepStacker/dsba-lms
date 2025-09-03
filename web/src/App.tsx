import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import MainLayout from './layouts/MainLayout';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';

// Loading Spinner Component
const LoadingSpinner: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
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
  const { user, isAuthenticated, loading } = useAuth();

  // Show loading spinner while auth is being initialized
  if (loading) {
    return <LoadingSpinner />;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  // Check role permissions
  if (allowedRoles.length > 0 && user && !allowedRoles.includes(user.role)) {
    // Redirect to dashboard with error or appropriate fallback
    return <Navigate to="/unauthorized" replace />;
  }

  return <MainLayout>{children}</MainLayout>;
};

// Role-based route wrappers - ready for future use
// Currently using basic ProtectedRoute for simplicity

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected Routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      {/* Role-specific routes - simplified for now */}
      <Route
        path="/users"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <div className="p-6">
              <h1 className="text-2xl font-bold mb-6">User Management</h1>
              <p>User management features coming soon...</p>
            </div>
          </ProtectedRoute>
        }
      />

      <Route
        path="/programs"
        element={
          <ProtectedRoute allowedRoles={['admin', 'teacher']}>
            <div className="p-6">
              <h1 className="text-2xl font-bold mb-6">Program Management</h1>
              <p>Program and course management coming soon...</p>
            </div>
          </ProtectedRoute>
        }
      />

      <Route
        path="/exams"
        element={
          <ProtectedRoute allowedRoles={['admin', 'teacher', 'student']}>
            <div className="p-6">
              <h1 className="text-2xl font-bold mb-6">Exam Management</h1>
              <p>Exam creation, management, and attempt features coming soon...</p>
            </div>
          </ProtectedRoute>
        }
      />

      <Route
        path="/questions"
        element={
          <ProtectedRoute allowedRoles={['admin', 'teacher']}>
            <div className="p-6">
              <h1 className="text-2xl font-bold mb-6">Question Bank</h1>
              <p>Question bank management and AI generation coming soon...</p>
            </div>
          </ProtectedRoute>
        }
      />

      <Route
        path="/analytics"
        element={
          <ProtectedRoute allowedRoles={['admin', 'teacher']}>
            <div className="p-6">
              <h1 className="text-2xl font-bold mb-6">Analytics</h1>
              <p>CO/PO attainment analytics and reports coming soon...</p>
            </div>
          </ProtectedRoute>
        }
      />

      <Route
        path="/audit"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <div className="p-6">
              <h1 className="text-2xl font-bold mb-6">Audit Logs</h1>
              <p>Audit log viewer and compliance reports coming soon...</p>
            </div>
          </ProtectedRoute>
        }
      />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h1 className="text-6xl font-bold text-gray-900">404</h1>
            <p className="text-gray-600 mt-4">Page not found</p>
            <button
              onClick={() => window.location.href = '/dashboard'}
              className="mt-6 text-blue-600 hover:text-blue-500 font-medium"
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
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#ffffff',
              color: '#374151',
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
      </AuthProvider>
    </Router>
  );
};

export default App;
