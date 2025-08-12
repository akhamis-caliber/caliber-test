// Demo Setup Utility
// This file contains utilities for setting up and testing demo authentication

import { firebaseAuth } from '../services/firebase';

// Demo user credentials for testing
export const DEMO_USERS = {
  admin: {
    email: 'admin@demo.com',
    password: 'Admin123!',
    displayName: 'Demo Admin',
    role: 'admin'
  },
  user: {
    email: 'user@demo.com',
    password: 'User123!',
    displayName: 'Demo User',
    role: 'user'
  },
  manager: {
    email: 'manager@demo.com',
    password: 'Manager123!',
    displayName: 'Demo Manager',
    role: 'manager'
  }
};

// Function to create demo users (for development/testing purposes)
export const createDemoUsers = async () => {
  const results = {};
  
  for (const [key, userData] of Object.entries(DEMO_USERS)) {
    try {
      console.log(`Creating demo user: ${key}`);
      const result = await firebaseAuth.signUpWithEmail(
        userData.email, 
        userData.password, 
        userData.displayName
      );
      
      if (result.success) {
        results[key] = { success: true, user: result.user };
        console.log(`✅ Demo user ${key} created successfully`);
      } else {
        results[key] = { success: false, error: result.error };
        console.log(`❌ Demo user ${key} creation failed:`, result.error);
      }
    } catch (error) {
      results[key] = { success: false, error: error.message };
      console.log(`❌ Demo user ${key} creation error:`, error.message);
    }
  }
  
  return results;
};

// Function to test demo user login
export const testDemoLogin = async (userType = 'admin') => {
  const userData = DEMO_USERS[userType];
  if (!userData) {
    throw new Error(`Invalid user type: ${userType}`);
  }
  
  try {
    console.log(`Testing demo login for: ${userType}`);
    const result = await firebaseAuth.signInWithEmail(userData.email, userData.password);
    
    if (result.success) {
      console.log(`✅ Demo login successful for ${userType}:`, result.user.email);
      return { success: true, user: result.user };
    } else {
      console.log(`❌ Demo login failed for ${userType}:`, result.error);
      return { success: false, error: result.error };
    }
  } catch (error) {
    console.log(`❌ Demo login error for ${userType}:`, error.message);
    return { success: false, error: error.message };
  }
};

// Function to test all demo logins
export const testAllDemoLogins = async () => {
  const results = {};
  
  for (const userType of Object.keys(DEMO_USERS)) {
    results[userType] = await testDemoLogin(userType);
  }
  
  return results;
};

// Function to get demo user info for display
export const getDemoUserInfo = (userType) => {
  const userData = DEMO_USERS[userType];
  if (!userData) {
    return null;
  }
  
  return {
    ...userData,
    password: '••••••••', // Hide actual password
    description: `Demo ${userType} account for testing purposes`
  };
};

// Function to check if demo users exist
export const checkDemoUsersExist = async () => {
  const results = {};
  
  for (const userType of Object.keys(DEMO_USERS)) {
    try {
      const result = await testDemoLogin(userType);
      results[userType] = result.success;
    } catch (error) {
      results[userType] = false;
    }
  }
  
  return results;
};

// Export for use in components
export default {
  DEMO_USERS,
  createDemoUsers,
  testDemoLogin,
  testAllDemoLogins,
  getDemoUserInfo,
  checkDemoUsersExist
};
