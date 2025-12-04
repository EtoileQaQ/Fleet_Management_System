import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      
      setTokens: (accessToken, refreshToken) => set({ 
        accessToken, 
        refreshToken,
        isAuthenticated: !!accessToken 
      }),
      
      login: (user, accessToken, refreshToken) => set({
        user,
        accessToken,
        refreshToken,
        isAuthenticated: true,
      }),
      
      logout: () => set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
      }),
      
      hasWritePermission: () => {
        const user = get().user;
        return user && (user.role === 'ADMIN' || user.role === 'RH');
      },
      
      hasAdminPermission: () => {
        const user = get().user;
        return user && user.role === 'ADMIN';
      },
    }),
    {
      name: 'fleet-auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);



