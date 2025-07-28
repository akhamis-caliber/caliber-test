import { createContext, useContext, useEffect, useState } from 'react';
import { firebaseAuth } from '../services/firebase';
import { backendAuth } from '../services/backendAuth';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [backendToken, setBackendToken] = useState(null);

  // Check if Firebase is properly configured
  const isFirebaseAvailable = firebaseAuth.auth && 
    process.env.NEXT_PUBLIC_FIREBASE_API_KEY && 
    process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN;

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        if (isFirebaseAvailable) {
          // Use Firebase authentication
          console.log('Using Firebase authentication');
          const unsubscribe = firebaseAuth.onAuthStateChanged(async (firebaseUser) => {
            if (firebaseUser) {
              setUser(firebaseUser);
              
              // Get Firebase ID token and verify with backend
              try {
                const idToken = await firebaseUser.getIdToken();
                const response = await authAPI.verifyToken({ token: idToken });
                
                if (response.data && response.data.access_token) {
                  setBackendToken(response.data.access_token);
                  localStorage.setItem('authToken', response.data.access_token);
                  console.log('Backend token obtained successfully');
                } else {
                  console.error('Invalid response from backend token verification');
                  setBackendToken(null);
                  localStorage.removeItem('authToken');
                }
              } catch (error) {
                console.error('Backend token verification failed:', error);
                setBackendToken(null);
                localStorage.removeItem('authToken');
              }
            } else {
              setUser(null);
              setBackendToken(null);
              localStorage.removeItem('authToken');
            }
            setLoading(false);
          });

          return unsubscribe;
        } else {
          // Use backend authentication directly
          console.log('Using backend authentication directly');
          const token = localStorage.getItem('authToken');
          if (token) {
            try {
              // Verify token with backend
              const response = await authAPI.verifyToken({ token });
              if (response.data && response.data.valid) {
                // Get user info
                const userResponse = await authAPI.getCurrentUser();
                if (userResponse.data) {
                  setUser({
                    email: userResponse.data.email,
                    uid: userResponse.data.email,
                    displayName: userResponse.data.full_name
                  });
                  setBackendToken(token);
                }
              } else {
                localStorage.removeItem('authToken');
              }
            } catch (error) {
              console.error('Token verification failed:', error);
              localStorage.removeItem('authToken');
            }
          }
          setLoading(false);
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        setLoading(false);
      }
    };

    initializeAuth();
  }, [isFirebaseAvailable]);

  const login = async (email, password) => {
    try {
      console.log('Login attempt with:', { email, isFirebaseAvailable });
      
      if (isFirebaseAvailable) {
        const result = await firebaseAuth.signInWithEmail(email, password);
        if (result.success) {
          // Backend verification will be handled in useEffect
          return { success: true, user: result.user };
        }
        return result;
      } else {
        // Use backend authentication directly
        const result = await backendAuth.login(email, password);
        if (result.success) {
          setUser(result.user);
          setBackendToken(result.token);
          console.log('Backend login successful');
        }
        return result;
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    }
  };

  const register = async (email, password, displayName) => {
    try {
      console.log('Register attempt with:', { email, displayName, isFirebaseAvailable });
      
      if (isFirebaseAvailable) {
        const result = await firebaseAuth.signUpWithEmail(email, password, displayName);
        if (result.success) {
          // Backend verification will be handled in useEffect
          return { success: true, user: result.user };
        }
        return result;
      } else {
        // Use backend authentication directly
        const result = await backendAuth.register(email, password, displayName);
        if (result.success) {
          setUser(result.user);
          setBackendToken(result.token);
          console.log('Backend registration successful');
        }
        return result;
      }
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: error.message };
    }
  };

  const loginWithGoogle = async () => {
    try {
      if (isFirebaseAvailable) {
        const result = await firebaseAuth.signInWithGoogle();
        if (result.success) {
          // Backend verification will be handled in useEffect
          return { success: true, user: result.user };
        }
        return result;
      } else {
        // Google login not available without Firebase
        return { success: false, error: 'Google login requires Firebase configuration' };
      }
    } catch (error) {
      console.error('Google login error:', error);
      return { success: false, error: error.message };
    }
  };

  const logout = async () => {
    try {
      if (isFirebaseAvailable) {
        const result = await firebaseAuth.signOut();
        if (result.success) {
          setUser(null);
          setBackendToken(null);
          localStorage.removeItem('authToken');
        }
        return result;
      } else {
        // Use backend authentication directly
        const result = backendAuth.logout();
        setUser(null);
        setBackendToken(null);
        return result;
      }
    } catch (error) {
      console.error('Logout error:', error);
      return { success: false, error: error.message };
    }
  };

  const resetPassword = async (email) => {
    try {
      if (isFirebaseAvailable) {
        return await firebaseAuth.resetPassword(email);
      } else {
        return { success: false, error: 'Password reset requires Firebase configuration' };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const sendEmailVerification = async () => {
    if (!user) return { success: false, error: 'No user logged in' };
    
    try {
      if (isFirebaseAvailable) {
        return await firebaseAuth.sendEmailVerification(user);
      } else {
        return { success: false, error: 'Email verification requires Firebase configuration' };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const value = {
    user,
    loading,
    backendToken,
    login,
    register,
    loginWithGoogle,
    logout,
    resetPassword,
    sendEmailVerification,
    isFirebaseAvailable
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 