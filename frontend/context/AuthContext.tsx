import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { onAuthStateChanged, User as FirebaseUser, signOut } from 'firebase/auth';
import { auth } from '@/services/firebase';
import { useAuthStore } from '@/store';
import { User } from '@/types';
import { tokenService, TokenResponse } from '@/services/tokenService';
import { authAPI } from '@/services/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  
  // Actions
  login: (firebaseToken: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const {
    user,
    loading,
    setUser,
    setLoading,
    logout: logoutStore,
  } = useAuthStore();

  // Initialize authentication state
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        setLoading(true);
        
        // Check if we have valid tokens
        if (tokenService.isTokenValid()) {
          const userData = tokenService.getUserData();
          if (userData) {
            setUser(userData);
            setLoading(false);
            return;
          }
        }
        
        // Listen for Firebase auth state changes
        const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
          if (firebaseUser) {
            try {
              // Get Firebase ID token
              const idToken = await firebaseUser.getIdToken();
              
              // Verify with backend and get JWT tokens
              const tokenResponse = await authAPI.verifyFirebaseToken(idToken);
              
              // Store tokens and user data
              tokenService.setTokens(tokenResponse);
              
              // Update store
              setUser(tokenResponse.user);
            } catch (error) {
              console.error('Backend authentication failed:', error);
              // Sign out from Firebase if backend auth fails
              await signOut(auth);
            }
          } else {
            // Clear everything when Firebase user signs out
            tokenService.clearTokens();
            setUser(null);
          }
          setLoading(false);
        });

        return unsubscribe;
      } catch (error) {
        console.error('Auth initialization failed:', error);
        setLoading(false);
      }
    };

    initializeAuth();
  }, [setUser, setLoading]);

  const login = async (firebaseToken: string) => {
    try {
      // Verify with backend and get JWT tokens
      const tokenResponse = await authAPI.verifyFirebaseToken(firebaseToken);
      
      // Store tokens and user data
      tokenService.setTokens(tokenResponse);
      
      // Update store
      setUser(tokenResponse.user);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Sign out from Firebase
      await signOut(auth);
      
      // Clear backend tokens
      await authAPI.logout();
      
      // Clear store
      logoutStore();
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout fails, clear local state
      logoutStore();
    }
  };

  const refreshUser = async () => {
    try {
      if (tokenService.isTokenValid()) {
        const userData = await authAPI.getProfile();
        if (userData) {
          tokenService.updateUserData(userData);
          setUser(userData);
        }
      }
    } catch (error) {
      console.error('Failed to refresh user data:', error);
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
