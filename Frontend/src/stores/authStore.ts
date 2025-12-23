import { create } from 'zustand';
import { persist } from 'zustand/middleware';

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
  logout: () => void;
}

// Mock users for demo
const MOCK_USERS = [
  { id: '1', email: 'admin@rag-system.io', password: 'admin', name: 'Admin User', role: 'admin' as UserRole },
  { id: '2', email: 'user@rag-system.io', password: 'user', name: 'Standard User', role: 'user' as UserRole },
];

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      login: async (email: string, password: string) => {
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 800));
        
        const foundUser = MOCK_USERS.find(
          u => u.email.toLowerCase() === email.toLowerCase() && u.password === password
        );
        
        if (foundUser) {
          const { password: _, ...userWithoutPassword } = foundUser;
          set({ user: userWithoutPassword, isAuthenticated: true });
          return { success: true };
        }
        
        return { success: false, error: 'Invalid email or password' };
      },
      logout: () => {
        set({ user: null, isAuthenticated: false });
      },
    }),
    {
      name: 'rag-auth',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
