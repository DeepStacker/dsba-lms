/* eslint-disable react-refresh/only-export-components */

import React, { createContext, useContext, useEffect } from 'react';
import { useAuthStore } from '../stores/useAuthStore';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (userData: Partial<User>) => void;
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
  const {
    user,
    token,
    isAuthenticated,
    isLoading,
    login: storeLogin,
    logout: storeLogout,
    updateUser,
    refreshAuth,
    initializeAuth
  } = useAuthStore();

  // Initialize auth on mount
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  const login = async (username: string, password: string): Promise<void> => {
    await storeLogin(username, password);
  };

  const logout = async (): Promise<void> => {
    await storeLogout();
  };

  const updateProfile = (userData: Partial<User>) => {
    updateUser(userData);
  };

  const changePassword = async (currentPassword: string, newPassword: string): Promise<void> => {
    // This would need to be implemented with the actual API
    // For now, just validate parameters
    if (!currentPassword || !newPassword) {
      throw new Error('Both current and new password are required');
    }
    if (currentPassword === newPassword) {
      throw new Error('New password must be different from current password');
    }
    if (newPassword.length < 8) {
      throw new Error('New password must be at least 8 characters long');
    }

    // TODO: Implement actual password change API call
    console.log('Password change not yet implemented');
  };

  const refreshUser = async (): Promise<void> => {
    await refreshAuth();
  };

  const value: AuthContextType = {
    user,
    loading: isLoading,
    isAuthenticated,
    token,
    login,
    logout,
    updateProfile,
    changePassword,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};