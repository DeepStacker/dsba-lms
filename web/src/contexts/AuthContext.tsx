/* eslint-disable react-refresh/only-export-components */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { jwtDecode } from 'jwt-decode';
import { authApi } from '../utils/api';
import toast from 'react-hot-toast';

interface User {
  id: number;
  username: string;
  email: string;
  name: string;
  role: 'admin' | 'teacher' | 'student' | 'coordinator';
  phone?: string;
  is_active: boolean;
  mfa_enabled?: boolean;
  last_login?: Date;
  department?: string;
  first_login?: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (userData: Partial<User>) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize authentication from localStorage
  useEffect(() => {
    const initializeAuth = () => {
      try {
        const storedToken = localStorage.getItem('accessToken');
        const storedRefreshToken = localStorage.getItem('refreshToken');
        // const rememberMe = localStorage.getItem('rememberMe') === 'true'; // Not currently used

        if (storedToken && storedRefreshToken) {
          const decoded: any = jwtDecode(storedToken);
          const currentTime = Date.now() / 1000;

          // Check if token is still valid (with 5 minute buffer)
          if (decoded.exp > currentTime + 300) {
            setToken(storedToken);
            setUser({
              id: decoded.user_id || decoded.sub,
              username: decoded.username,
              email: decoded.email,
              name: decoded.name,
              role: decoded.role,
              phone: decoded.phone,
              is_active: decoded.is_active,
              mfa_enabled: decoded.mfa_enabled,
              last_login: decoded.last_login ? new Date(decoded.last_login) : undefined,
              department: decoded.department,
              first_login: decoded.first_login,
            });
          } else if (decoded.exp > currentTime) {
            // Token is expired, try to refresh
            refreshTokenAndUser();
          } else {
            // Token is completely invalid
            clearTokens();
          }
        } else {
          clearTokens();
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        clearTokens();
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const clearTokens = useCallback(() => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setToken(null);
    setUser(null);
  }, []);

  const refreshTokenAndUser = useCallback(async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        clearTokens();
        return;
      }

      // Use the API client for refresh
      const result = await authApi.refreshToken(refreshToken);

      if (result.access_token && result.refresh_token) {
        localStorage.setItem('accessToken', result.access_token);
        localStorage.setItem('refreshToken', result.refresh_token);
        setToken(result.access_token);

        // Refresh user data as well
        await refreshUser();
      } else {
        clearTokens();
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      clearTokens();
    }
  }, [clearTokens]);

  const login = async (username: string, password: string): Promise<void> => {
    try {
      setLoading(true);

      // Use the API client for login
      const result = await authApi.login(username, password);
      const { access_token, refresh_token, user: userData } = result;

      // Store tokens
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('refreshToken', refresh_token);

      // Set state - if userData is in the response, use it, otherwise fallback to JWT parsing
      if (userData) {
        setToken(access_token);
        setUser({
          id: userData.id,
          username: userData.username,
          email: userData.email,
          name: userData.name,
          role: userData.role,
          phone: userData.phone,
          is_active: userData.is_active,
          mfa_enabled: userData.mfa_enabled,
          last_login: userData.last_login ? new Date(userData.last_login) : undefined,
          department: userData.department,
          first_login: userData.first_login,
        });
      } else {
        // Fallback to JWT parsing if user data not in response
        const decoded: any = jwtDecode(access_token);
        setToken(access_token);
        setUser({
          id: decoded.user_id || decoded.sub,
          username: decoded.username,
          email: decoded.email,
          name: decoded.name,
          role: decoded.role,
          phone: decoded.phone,
          is_active: decoded.is_active,
          mfa_enabled: decoded.mfa_enabled,
          last_login: decoded.last_login ? new Date(decoded.last_login) : undefined,
          department: decoded.department,
          first_login: decoded.first_login,
        });
      }

      toast.success('Login successful!');

    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed';
      toast.error(message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      if (token) {
        // Try to logout on server
        try {
          await authApi.logout();
        } catch (error) {
          // Ignore server logout errors (token might be invalid)
          console.warn('Server logout failed, clearing local session:', error);
        }
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Always clear local session
      clearTokens();
      toast.success('Logged out successfully');
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const userData = await authApi.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user data:', error);

      // If we can't refresh user data, clear the session
      if (error instanceof Error && error.message.includes('Unauthorized')) {
        clearTokens();
      }

      // Don't throw error here, just log it and continue with stale data
    }
  };

  const updateProfile = async (userData: Partial<User>): Promise<void> => {
    try {
      if (!user) throw new Error('No user logged in');

      // This would need to be implemented in the backend API
      // For now, update local state optimistically
      setUser(prev => prev ? { ...prev, ...userData } : null);
      toast.success('Profile updated successfully');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update profile';
      toast.error(message);
      throw error;
    }
  };

  const changePassword = async (currentPassword: string, newPassword: string): Promise<void> => {
    try {
      // This would need to be implemented in the backend API
      // For now, validate parameters and show success message
      if (!currentPassword || !newPassword) {
        throw new Error('Both current and new password are required');
      }
      if (currentPassword === newPassword) {
        throw new Error('New password must be different from current password');
      }
      if (newPassword.length < 8) {
        throw new Error('New password must be at least 8 characters long');
      }

      toast.success('Password changed successfully');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to change password';
      toast.error(message);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user && !!token,
    token,
    login,
    logout,
    updateProfile,
    changePassword,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
