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

// Firebase configuration - Updated to use caliber-auth project to match backend
const firebaseConfig = {
  apiKey: "AIzaSyDXNQNVinIkWhutIn7ScJtmf_KT9GyZwFk",
  authDomain: "caliber-auth.firebaseapp.com",
  projectId: "caliber-auth",
  storageBucket: "caliber-auth.firebasestorage.app",
  messagingSenderId: "116374690154457358557",
  appId: "1:116374690154457358557:web:421e5303e714ba0fdbbf08"
};

let app, auth, googleProvider;

// Check if Firebase configuration is valid
const isFirebaseConfigured = firebaseConfig.apiKey && 
                            firebaseConfig.authDomain &&
                            firebaseConfig.projectId;

if (isFirebaseConfigured) {
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
}

// Check if Firebase was initialized successfully
if (!auth || !googleProvider) {
  console.warn('Firebase initialization failed. Authentication will not work.');
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