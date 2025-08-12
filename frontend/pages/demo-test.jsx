import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  createDemoUsers, 
  testAllDemoLogins, 
  checkDemoUsersExist,
  DEMO_USERS 
} from '../utils/demoSetup';
import toast from 'react-hot-toast';

export default function DemoTest() {
  const [isLoading, setIsLoading] = useState(false);
  const [demoStatus, setDemoStatus] = useState({});
  const [testResults, setTestResults] = useState({});
  const { user, logout } = useAuth();

  useEffect(() => {
    checkDemoStatus();
  }, []);

  const checkDemoStatus = async () => {
    setIsLoading(true);
    try {
      const status = await checkDemoUsersExist();
      setDemoStatus(status);
    } catch (error) {
      console.error('Error checking demo status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateDemoUsers = async () => {
    setIsLoading(true);
    try {
      const results = await createDemoUsers();
      setDemoStatus(results);
      toast.success('Demo users creation completed. Check console for details.');
    } catch (error) {
      toast.error('Error creating demo users: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestAllLogins = async () => {
    setIsLoading(true);
    try {
      const results = await testAllDemoLogins();
      setTestResults(results);
      toast.success('Demo login testing completed. Check console for details.');
    } catch (error) {
      toast.error('Error testing demo logins: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
    } catch (error) {
      toast.error('Logout failed: ' + error.message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200">
            <h1 className="text-2xl font-bold text-gray-900">Demo Authentication Testing</h1>
            <p className="mt-1 text-sm text-gray-600">
              Test and manage demo user accounts for development and testing purposes
            </p>
          </div>

          {/* Current User Status */}
          {user && (
            <div className="px-6 py-4 bg-blue-50 border-b border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-blue-800">Currently Logged In</h3>
                  <p className="text-sm text-blue-600">
                    {user.displayName || user.email} ({user.email})
                  </p>
                </div>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-100 border border-blue-300 rounded-md hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Logout
                </button>
              </div>
            </div>
          )}

          {/* Demo Users Info */}
          <div className="px-6 py-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Demo User Accounts</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {Object.entries(DEMO_USERS).map(([key, userData]) => (
                <div key={key} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-gray-900 capitalize">{key}</h4>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      demoStatus[key] 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {demoStatus[key] ? 'Exists' : 'Missing'}
                    </span>
                  </div>
                  <div className="space-y-1 text-xs text-gray-600">
                    <p><strong>Email:</strong> {userData.email}</p>
                    <p><strong>Password:</strong> {userData.password}</p>
                    <p><strong>Name:</strong> {userData.displayName}</p>
                    <p><strong>Role:</strong> {userData.role}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-4">
              <button
                onClick={handleCreateDemoUsers}
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {isLoading ? 'Creating...' : 'Create Demo Users'}
              </button>
              
              <button
                onClick={handleTestAllLogins}
                disabled={isLoading}
                className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
              >
                {isLoading ? 'Testing...' : 'Test All Demo Logins'}
              </button>
              
              <button
                onClick={checkDemoStatus}
                disabled={isLoading}
                className="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50"
              >
                {isLoading ? 'Checking...' : 'Check Demo Status'}
              </button>
            </div>
          </div>

          {/* Test Results */}
          {Object.keys(testResults).length > 0 && (
            <div className="px-6 py-4 border-t border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Test Results</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(testResults).map(([key, result]) => (
                  <div key={key} className={`border rounded-lg p-4 ${
                    result.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                  }`}>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-900 capitalize">{key}</h4>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        result.success 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {result.success ? 'Success' : 'Failed'}
                      </span>
                    </div>
                    {result.success ? (
                      <p className="text-xs text-green-600">
                        Login successful for {result.user?.email}
                      </p>
                    ) : (
                      <p className="text-xs text-red-600">
                        Error: {result.error}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Instructions */}
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Instructions</h3>
            <div className="text-sm text-gray-600 space-y-2">
              <p><strong>1. Create Demo Users:</strong> Click "Create Demo Users" to create test accounts in Firebase.</p>
              <p><strong>2. Test Logins:</strong> Use the demo credentials in the Login/Register components or test them here.</p>
              <p><strong>3. Check Status:</strong> Verify which demo users exist in your Firebase project.</p>
              <p><strong>4. Console Logs:</strong> Check the browser console for detailed operation logs.</p>
            </div>
          </div>

          {/* Navigation */}
          <div className="px-6 py-4 border-t border-gray-200">
            <div className="flex flex-wrap gap-4">
              <a
                href="/auth?mode=login"
                className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                Go to Login
              </a>
              <a
                href="/auth?mode=register"
                className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                Go to Register
              </a>
              <a
                href="/dashboard"
                className="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Go to Dashboard
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
