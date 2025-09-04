import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { jwtDecode } from 'jwt-decode';
import { authApi } from '../utils/api';
import { User } from '../types';
import toast from 'react-hot-toast';

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
  updateUser: (userData: Partial<User>) => void;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  initializeAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        try {
          set({ isLoading: true, error: null });

          const response = await authApi.login(username, password);
          
          if (response.access_token && response.user) {
            const { access_token, refresh_token, user } = response;
            
            set({
              user,
              token: access_token,
              refreshToken: refresh_token,
              isAuthenticated: true,
              isLoading: false,
              error: null
            });

            // Store tokens in localStorage for persistence
            localStorage.setItem('accessToken', access_token);
            localStorage.setItem('refreshToken', refresh_token);

            toast.success(`Welcome back, ${user.name}!`);
          } else {
            throw new Error('Invalid response from server');
          }
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Login failed';
          set({ 
            isLoading: false, 
            error: message,
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false
          });
          toast.error(message);
          throw error;
        }
      },

      logout: async () => {
        try {
          // Try to logout on server
          if (get().token) {
            await authApi.logout();
          }
        } catch (error) {
          console.warn('Server logout failed:', error);
        } finally {
          // Always clear local state
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false,
            error: null
          });

          // Clear localStorage
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');

          toast.success('Logged out successfully');
        }
      },

      refreshAuth: async () => {
        try {
          const { refreshToken } = get();
          
          if (!refreshToken) {
            throw new Error('No refresh token available');
          }

          const response = await authApi.refreshToken(refreshToken);
          
          if (response.access_token && response.refresh_token) {
            set({
              token: response.access_token,
              refreshToken: response.refresh_token,
              error: null
            });

            // Update localStorage
            localStorage.setItem('accessToken', response.access_token);
            localStorage.setItem('refreshToken', response.refresh_token);

            // Refresh user data
            try {
              const userData = await authApi.getCurrentUser();
              set({ user: userData });
            } catch (userError) {
              console.warn('Failed to refresh user data:', userError);
            }
          } else {
            throw new Error('Invalid refresh response');
          }
        } catch (error) {
          console.error('Token refresh failed:', error);
          
          // Clear auth state on refresh failure
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false,
            error: 'Session expired. Please login again.'
          });

          // Clear localStorage
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');

          throw error;
        }
      },

      updateUser: (userData: Partial<User>) => {
        const currentUser = get().user;
        if (currentUser) {
          set({
            user: { ...currentUser, ...userData }
          });
        }
      },

      clearError: () => {
        set({ error: null });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      initializeAuth: async () => {
        try {
          set({ isLoading: true });

          const storedToken = localStorage.getItem('accessToken');
          const storedRefreshToken = localStorage.getItem('refreshToken');

          if (!storedToken || !storedRefreshToken) {
            set({ isLoading: false });
            return;
          }

          // Check if token is valid
          try {
            const decodedToken: any = jwtDecode(storedToken);
            const currentTime = Date.now() / 1000;

            // If token is expired, try to refresh
            if (decodedToken.exp < currentTime) {
              await get().refreshAuth();
            } else {
              // Token is valid, set auth state
              set({
                token: storedToken,
                refreshToken: storedRefreshToken,
                isAuthenticated: true
              });

              // Get current user data
              try {
                const userData = await authApi.getCurrentUser();
                set({ user: userData });
              } catch (userError) {
                console.warn('Failed to get user data:', userError);
                // Token might be invalid, try refresh
                await get().refreshAuth();
              }
            }
          } catch (tokenError) {
            console.warn('Invalid token:', tokenError);
            // Clear invalid tokens
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            set({
              token: null,
              refreshToken: null,
              isAuthenticated: false
            });
          }
        } catch (error) {
          console.error('Auth initialization failed:', error);
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false,
            error: null
          });
        } finally {
          set({ isLoading: false });
        }
      }
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
);