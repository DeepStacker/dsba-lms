import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../stores/useAuthStore';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { 
  EyeIcon, 
  EyeSlashIcon, 
  AcademicCapIcon,
  RocketLaunchIcon 
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const LoginPage: React.FC = () => {
  const { login, isAuthenticated, isLoading } = useAuthStore();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.username || !formData.password) {
      toast.error('Please fill in all fields');
      return;
    }

    try {
      setIsSubmitting(true);
      await login(formData.username, formData.password);
    } catch (error) {
      // Error is already handled in the store and toast is shown
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen text="Initializing..." />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center">
            <div className="flex items-center space-x-2">
              <AcademicCapIcon className="h-12 w-12 text-blue-600" />
              <RocketLaunchIcon className="h-8 w-8 text-purple-600" />
            </div>
          </div>
          <h1 className="mt-6 text-3xl font-bold text-gray-900">
            DSBA LMS
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            AI-Powered Learning Management System
          </p>
          <p className="text-xs text-gray-500">
            Sign in to your account to continue
          </p>
        </div>

        {/* Login Form */}
        <Card className="mt-8 shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Input
                label="Username or Email"
                type="text"
                value={formData.username}
                onChange={(value) => handleInputChange('username', value)}
                placeholder="Enter your username or email"
                disabled={isSubmitting}
                autoFocus
                required
              />
            </div>

            <div>
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={(value) => handleInputChange('password', value)}
                placeholder="Enter your password"
                disabled={isSubmitting}
                required
                rightIcon={showPassword ? EyeSlashIcon : EyeIcon}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                style={{ marginTop: '12px' }}
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            </div>

            <div>
              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full"
                isLoading={isSubmitting}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Signing in...' : 'Sign In'}
              </Button>
            </div>
          </form>

          {/* Demo Credentials */}
          <div className="mt-6 border-t border-gray-200 pt-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Demo Credentials:</h3>
            <div className="space-y-2 text-xs text-gray-600">
              <div className="flex justify-between">
                <span className="font-medium">Admin:</span>
                <span>admin@dsba.edu / admin123</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Teacher:</span>
                <span>teacher@dsba.edu / teacher123</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Student:</span>
                <span>student@dsba.edu / student123</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Features */}
        <div className="mt-8">
          <div className="grid grid-cols-1 gap-4">
            <div className="text-center">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Key Features</h3>
              <div className="flex justify-center space-x-6 text-xs text-gray-500">
                <span>🤖 AI Grading</span>
                <span>📊 CO/PO Mapping</span>
                <span>📈 Real-time Analytics</span>
                <span>🔒 Secure Exams</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-gray-500">
          <p>&copy; 2024 DSBA LMS. All rights reserved.</p>
          <p className="mt-1">Powered by AI for Educational Excellence</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;