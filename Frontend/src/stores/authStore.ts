import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient, ApiError } from '@/services/api';

export type UserRole = 'admin' | 'user';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (email: string, password: string, name: string, role?: UserRole) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      login: async (email: string, password: string) => {
        try {
          const response = await apiClient.login(email, password);
          
          if (response.success && response.token && response.user) {
            // Sauvegarder le token dans l'API client
            apiClient.setToken(response.token);
            
            // Mapper l'utilisateur de l'API vers notre format
            const user: User = {
              id: response.user.id,
              email: response.user.email,
              name: response.user.name,
              role: response.user.role as UserRole,
            };
            
            set({ user, isAuthenticated: true });
            return { success: true };
          } else {
            return { 
              success: false, 
              error: response.error || 'Email ou mot de passe incorrect' 
            };
          }
        } catch (error) {
          if (error instanceof ApiError) {
            return { 
              success: false, 
              error: error.getUserMessage()
            };
          }
          return { 
            success: false, 
            error: error instanceof Error ? error.message : 'Erreur de connexion' 
          };
        }
      },
      register: async (email: string, password: string, name: string, role: UserRole = 'user') => {
        try {
          const response = await apiClient.register(email, password, name, role);
          
          if (response.success && response.token && response.user) {
            // Sauvegarder le token dans l'API client
            apiClient.setToken(response.token);
            
            // Mapper l'utilisateur de l'API vers notre format
            const user: User = {
              id: response.user.id,
              email: response.user.email,
              name: response.user.name,
              role: response.user.role as UserRole,
            };
            
            set({ user, isAuthenticated: true });
            return { success: true };
          } else {
            return { 
              success: false, 
              error: response.error || 'Erreur lors de l\'inscription' 
            };
          }
        } catch (error) {
          if (error instanceof ApiError) {
            return { 
              success: false, 
              error: error.getUserMessage()
            };
          }
          return { 
            success: false, 
            error: error instanceof Error ? error.message : 'Erreur lors de l\'inscription' 
          };
        }
      },
      logout: async () => {
        try {
          await apiClient.logout();
        } catch (error) {
          // Ignorer les erreurs de logout
        } finally {
          // Toujours nettoyer l'état local
          apiClient.setToken(null);
          set({ user: null, isAuthenticated: false });
        }
      },
    }),
    {
      name: 'rag-auth',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);