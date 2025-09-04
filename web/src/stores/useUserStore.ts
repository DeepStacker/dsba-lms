import { create } from 'zustand';
import { usersApi } from '../utils/api';
import { User } from '../types';
import toast from 'react-hot-toast';

interface UserState {
  users: User[];
  selectedUser: User | null;
  isLoading: boolean;
  error: string | null;
  pagination: {
    total: number;
    page: number;
    limit: number;
    pages: number;
  };
  filters: {
    search: string;
    role: string;
    status: string;
  };

  // Actions
  loadUsers: (params?: any) => Promise<void>;
  createUser: (userData: any) => Promise<void>;
  updateUser: (userId: number, userData: any) => Promise<void>;
  deleteUser: (userId: number) => Promise<void>;
  selectUser: (user: User | null) => void;
  setFilters: (filters: Partial<typeof filters>) => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
  bulkImportUsers: (file: File, role: string) => Promise<void>;
}

const initialFilters = {
  search: '',
  role: '',
  status: ''
};

const initialPagination = {
  total: 0,
  page: 1,
  limit: 20,
  pages: 0
};

export const useUserStore = create<UserState>((set, get) => ({
  users: [],
  selectedUser: null,
  isLoading: false,
  error: null,
  pagination: initialPagination,
  filters: initialFilters,

  loadUsers: async (params = {}) => {
    try {
      set({ isLoading: true, error: null });
      
      const { filters, pagination } = get();
      const queryParams = {
        skip: (pagination.page - 1) * pagination.limit,
        limit: pagination.limit,
        search: filters.search || undefined,
        role: filters.role || undefined,
        ...params
      };

      const response = await usersApi.getUsers(queryParams);
      
      if (response) {
        set({
          users: Array.isArray(response) ? response : response.users || [],
          pagination: {
            total: response.total || 0,
            page: Math.floor((response.skip || 0) / (response.limit || 20)) + 1,
            limit: response.limit || 20,
            pages: Math.ceil((response.total || 0) / (response.limit || 20))
          },
          isLoading: false
        });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load users';
      set({ 
        error: message,
        isLoading: false,
        users: []
      });
      toast.error(message);
    }
  },

  createUser: async (userData: any) => {
    try {
      set({ isLoading: true, error: null });
      
      const newUser = await usersApi.createUser(userData);
      
      if (newUser) {
        // Add to local state
        set(state => ({
          users: [newUser, ...state.users],
          isLoading: false
        }));

        toast.success(`User ${newUser.name} created successfully`);
        
        // Reload users to get updated list
        await get().loadUsers();
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create user';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
      throw error;
    }
  },

  updateUser: async (userId: number, userData: any) => {
    try {
      set({ isLoading: true, error: null });
      
      const updatedUser = await usersApi.updateUser(userId, userData);
      
      if (updatedUser) {
        // Update in local state
        set(state => ({
          users: state.users.map(user => 
            user.id === userId ? updatedUser : user
          ),
          selectedUser: state.selectedUser?.id === userId ? updatedUser : state.selectedUser,
          isLoading: false
        }));

        toast.success(`User ${updatedUser.name} updated successfully`);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update user';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
      throw error;
    }
  },

  deleteUser: async (userId: number) => {
    try {
      set({ isLoading: true, error: null });
      
      await usersApi.deleteUser(userId);
      
      // Remove from local state
      set(state => ({
        users: state.users.filter(user => user.id !== userId),
        selectedUser: state.selectedUser?.id === userId ? null : state.selectedUser,
        isLoading: false
      }));

      toast.success('User deleted successfully');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete user';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
      throw error;
    }
  },

  selectUser: (user: User | null) => {
    set({ selectedUser: user });
  },

  setFilters: (newFilters: Partial<typeof initialFilters>) => {
    set(state => ({
      filters: { ...state.filters, ...newFilters },
      pagination: { ...state.pagination, page: 1 } // Reset to first page when filtering
    }));
    
    // Auto-reload with new filters
    get().loadUsers();
  },

  setError: (error: string | null) => {
    set({ error });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },

  bulkImportUsers: async (file: File, role: string) => {
    try {
      set({ isLoading: true, error: null });
      
      const result = await usersApi.bulkImportUsers(file, role);
      
      if (result) {
        toast.success(`Successfully imported ${result.imported_count || 0} users`);
        
        // Reload users list
        await get().loadUsers();
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to import users';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
      throw error;
    }
  }
}));