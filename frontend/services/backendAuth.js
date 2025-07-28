import { authAPI } from './api';

// Backend authentication service
export const backendAuth = {
  // Login with email and password
  login: async (email, password) => {
    try {
      console.log('BackendAuth: Attempting login with:', { email });
      const response = await authAPI.login({ email, password });
      console.log('BackendAuth: Login response:', response.data);
      
      if (response.data && response.data.access_token) {
        localStorage.setItem('authToken', response.data.access_token);
        const user = { 
          email, 
          uid: email, // Use email as UID for compatibility
          displayName: email.split('@')[0] // Extract name from email
        };
        console.log('BackendAuth: Login successful, user:', user);
        return { 
          success: true, 
          user,
          token: response.data.access_token
        };
      }
      console.log('BackendAuth: Invalid response from server');
      return { success: false, error: 'Invalid response from server' };
    } catch (error) {
      console.error('BackendAuth: Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message || 'Login failed' 
      };
    }
  },

  // Register with email and password
  register: async (email, password, fullName) => {
    try {
      console.log('BackendAuth: Attempting registration with:', { email, fullName });
      const response = await authAPI.register({ 
        email, 
        password, 
        full_name: fullName 
      });
      console.log('BackendAuth: Registration response:', response.data);
      
      if (response.data && response.data.access_token) {
        localStorage.setItem('authToken', response.data.access_token);
        const user = { 
          email, 
          uid: email,
          displayName: fullName
        };
        console.log('BackendAuth: Registration successful, user:', user);
        return { 
          success: true, 
          user,
          token: response.data.access_token
        };
      }
      console.log('BackendAuth: Invalid response from server');
      return { success: false, error: 'Invalid response from server' };
    } catch (error) {
      console.error('BackendAuth: Registration error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message || 'Registration failed' 
      };
    }
  },

  // Logout
  logout: () => {
    localStorage.removeItem('authToken');
    return { success: true };
  },

  // Get current user from token
  getCurrentUser: async () => {
    try {
      const token = localStorage.getItem('authToken');
      if (!token) {
        return null;
      }

      const response = await authAPI.getCurrentUser();
      if (response.data) {
        return {
          email: response.data.email,
          uid: response.data.email,
          displayName: response.data.full_name
        };
      }
      return null;
    } catch (error) {
      console.error('getCurrentUser error:', error);
      localStorage.removeItem('authToken');
      return null;
    }
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem('authToken');
  }
}; 