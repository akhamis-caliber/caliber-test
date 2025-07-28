import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { campaignAPI } from '../services/api';

export default function TestAuth() {
  const { user, login, register, backendToken, isFirebaseAvailable } = useAuth();
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [authStatus, setAuthStatus] = useState('');

  const testCredentials = {
    email: 'test@example.com',
    password: 'testpassword123',
    fullName: 'Test User'
  };

  const handleAutoLogin = async () => {
    setLoading(true);
    setError('');
    setAuthStatus('Attempting to log in...');

    try {
      console.log('Starting login process...');
      const result = await login(testCredentials.email, testCredentials.password);
      console.log('Login result:', result);
      
      if (result.success) {
        setAuthStatus('Login successful!');
      } else {
        setError(result.error);
        setAuthStatus('Login failed');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Login error: ' + err.message);
      setAuthStatus('Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoRegister = async () => {
    setLoading(true);
    setError('');
    setAuthStatus('Attempting to register...');

    try {
      const result = await register(testCredentials.email, testCredentials.password, testCredentials.fullName);
      if (result.success) {
        setAuthStatus('Registration successful!');
      } else {
        setError(result.error);
        setAuthStatus('Registration failed');
      }
    } catch (err) {
      setError('Registration error: ' + err.message);
      setAuthStatus('Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const testCampaignsAPI = async () => {
    setLoading(true);
    setError('');
    setAuthStatus('Testing campaigns API...');

    try {
      const response = await campaignAPI.getCampaigns();
      setCampaigns(response.data || []);
      setAuthStatus('Campaigns API test successful!');
    } catch (err) {
      setError('Campaigns API error: ' + (err.response?.data?.detail || err.message));
      setAuthStatus('Campaigns API test failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && backendToken) {
      setAuthStatus('User is authenticated with backend token');
    } else if (user) {
      setAuthStatus('User is authenticated but no backend token');
    } else {
      setAuthStatus('User is not authenticated');
    }
  }, [user, backendToken]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Authentication Test Page</h1>
        
        {/* Authentication Status */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Authentication Status</h2>
          <div className="space-y-2">
            <p><strong>User:</strong> {user ? 'Logged in' : 'Not logged in'}</p>
            <p><strong>Backend Token:</strong> {backendToken ? 'Present' : 'Missing'}</p>
            <p><strong>Firebase Available:</strong> {isFirebaseAvailable ? 'Yes' : 'No'}</p>
            <p><strong>Status:</strong> {authStatus}</p>
            {user && (
              <div className="mt-4 p-3 bg-gray-50 rounded">
                <p><strong>User Email:</strong> {user.email}</p>
                <p><strong>User ID:</strong> {user.uid}</p>
                <p><strong>Display Name:</strong> {user.displayName || 'N/A'}</p>
              </div>
            )}
          </div>
        </div>

        {/* Authentication Actions */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Authentication Actions</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium mb-2">Test Credentials:</h3>
              <p className="text-sm text-gray-600">
                Email: {testCredentials.email}<br/>
                Password: {testCredentials.password}
              </p>
            </div>
            
            <div className="flex space-x-4">
              <button
                onClick={handleAutoLogin}
                disabled={loading}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Logging in...' : 'Auto Login'}
              </button>
              
              <button
                onClick={handleAutoRegister}
                disabled={loading}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Registering...' : 'Auto Register'}
              </button>
            </div>
          </div>
        </div>

        {/* API Test */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">API Test</h2>
          <button
            onClick={testCampaignsAPI}
            disabled={loading || !user || !backendToken}
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50"
          >
            {loading ? 'Testing...' : 'Test Campaigns API'}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <h3 className="text-red-800 font-medium">Error:</h3>
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Campaigns Display */}
        {campaigns.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Campaigns ({campaigns.length})</h2>
            <div className="space-y-2">
              {campaigns.map((campaign, index) => (
                <div key={index} className="border rounded p-3">
                  <p><strong>Name:</strong> {campaign.name}</p>
                  <p><strong>Status:</strong> {campaign.status}</p>
                  <p><strong>ID:</strong> {campaign.id}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {campaigns.length === 0 && user && backendToken && !loading && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-blue-800 font-medium">No Campaigns Found</h3>
            <p className="text-blue-700">The API is working correctly, but there are no campaigns in the database.</p>
          </div>
        )}
      </div>
    </div>
  );
} 