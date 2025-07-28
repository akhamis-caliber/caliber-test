import { initializeApp } from 'firebase/app';
import { 
  getAuth, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword,
  signInWithPopup, 
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
  sendEmailVerification,
  sendPasswordResetEmail,
  updateProfile
} from 'firebase/auth';

// Check if Firebase environment variables are configured
const isFirebaseConfigured = process.env.NEXT_PUBLIC_FIREBASE_API_KEY && 
                            process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN &&
                            process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;

let app, auth, googleProvider;

if (isFirebaseConfigured) {
  // Firebase configuration
  const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
  };

  try {
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    
    // Google provider setup
    googleProvider = new GoogleAuthProvider();
    googleProvider.setCustomParameters({
      prompt: 'select_account'
    });
  } catch (error) {
    console.error('Firebase initialization failed:', error);
    auth = null;
    googleProvider = null;
  }
} else {
  console.warn('Firebase environment variables not configured. Using mock authentication.');
  auth = null;
  googleProvider = null;
}

// Auth methods
export const firebaseAuth = {
  // Email/Password authentication
  signInWithEmail: async (email, password) => {
    try {
      if (!auth) {
        return { success: false, error: 'Firebase not properly configured' };
      }
      const result = await signInWithEmailAndPassword(auth, email, password);
      return { success: true, user: result.user };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Registration
  signUpWithEmail: async (email, password, displayName) => {
    try {
      if (!auth) {
        return { success: false, error: 'Firebase not properly configured' };
      }
      const result = await createUserWithEmailAndPassword(auth, email, password);
      
      // Update profile with display name
      if (displayName) {
        await updateProfile(result.user, { displayName });
      }
      
      // Send email verification
      await sendEmailVerification(result.user);
      
      return { success: true, user: result.user };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Google authentication
  signInWithGoogle: async () => {
    try {
      if (!auth || !googleProvider) {
        return { success: false, error: 'Firebase not properly configured' };
      }
      const result = await signInWithPopup(auth, googleProvider);
      return { success: true, user: result.user };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Sign out
  signOut: async () => {
    try {
      if (!auth) {
        return { success: false, error: 'Firebase not properly configured' };
      }
      await signOut(auth);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Password reset
  resetPassword: async (email) => {
    try {
      if (!auth) {
        return { success: false, error: 'Firebase not properly configured' };
      }
      await sendPasswordResetEmail(auth, email);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Email verification
  sendEmailVerification: async (user) => {
    try {
      if (!auth) {
        return { success: false, error: 'Firebase not properly configured' };
      }
      await sendEmailVerification(user);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Auth state listener
  onAuthStateChanged: (callback) => {
    if (!auth) {
      // Return a mock unsubscribe function
      callback(null);
      return () => {};
    }
    return onAuthStateChanged(auth, callback);
  },

  // Get current user
  getCurrentUser: () => {
    return auth ? auth.currentUser : null;
  }
};

export { auth, googleProvider };
export default app; 