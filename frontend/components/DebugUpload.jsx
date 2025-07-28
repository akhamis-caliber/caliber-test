import React, { useState } from 'react';
import { reportAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

export default function DebugUpload() {
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState({});
  const { user, backendToken } = useAuth();

  const testUpload = async () => {
    setIsLoading(true);
    setDebugInfo({});

    try {
      // Step 1: Check authentication
      const authInfo = {
        user: user ? { email: user.email, uid: user.uid } : null,
        backendToken: backendToken ? 'Present' : 'Missing',
        localStorageToken: localStorage.getItem('authToken') ? 'Present' : 'Missing'
      };
      setDebugInfo(prev => ({ ...prev, auth: authInfo }));

      // Step 2: Create test file
      const testData = [
        ['Domain', 'Impressions', 'CTR', 'Conversions', 'Total Spend'],
        ['example.com', '1000', '0.02', '5', '100'],
        ['test.com', '2000', '0.03', '10', '200'],
        ['sample.com', '1500', '0.025', '8', '150']
      ];
      
      const csvContent = testData.map(row => row.join(',')).join('\n');
      const testFile = new File([csvContent], 'test_upload.csv', { type: 'text/csv' });

      // Step 3: Test API call
      const formData = new FormData();
      formData.append('file', testFile);
      formData.append('campaign_id', '1');
      formData.append('user_id', user?.uid || '1');

      console.log('Upload request details:');
      console.log('- File:', testFile.name, testFile.size, 'bytes');
      console.log('- Campaign ID:', '1');
      console.log('- User ID:', user?.uid || '1');
      console.log('- Auth Token:', localStorage.getItem('authToken') ? 'Present' : 'Missing');

      const response = await reportAPI.uploadFile(formData);
      
      setDebugInfo(prev => ({
        ...prev,
        success: true,
        response: response.data,
        status: response.status
      }));

      toast.success('Upload test successful!');
      console.log('Upload response:', response.data);

    } catch (error) {
      console.error('Upload test failed:', error);
      
      const errorInfo = {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        headers: error.response?.headers,
        config: {
          url: error.config?.url,
          method: error.config?.method,
          headers: error.config?.headers
        }
      };

      setDebugInfo(prev => ({
        ...prev,
        success: false,
        error: errorInfo
      }));

      toast.error(`Upload test failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const testAuthStatus = async () => {
    try {
      const token = localStorage.getItem('authToken');
      console.log('Current auth token:', token);
      
      if (token) {
        // Test token validity
        const response = await fetch('http://localhost:8000/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const userData = await response.json();
          console.log('Token is valid, user:', userData);
          toast.success('Authentication working');
        } else {
          console.log('Token is invalid, status:', response.status);
          toast.error('Authentication failed');
        }
      } else {
        console.log('No auth token found');
        toast.error('No authentication token');
      }
    } catch (error) {
      console.error('Auth test failed:', error);
      toast.error('Auth test failed');
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Upload Debug Tools</h3>
        
        <div className="space-y-4">
          <button
            onClick={testAuthStatus}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Test Authentication
          </button>
          
          <button
            onClick={testUpload}
            disabled={isLoading}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {isLoading ? 'Testing Upload...' : 'Test Upload'}
          </button>
        </div>
      </div>

      {Object.keys(debugInfo).length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Debug Information</h3>
          
          <div className="space-y-4">
            {debugInfo.auth && (
              <div>
                <h4 className="font-medium text-gray-700">Authentication Status</h4>
                <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto">
                  {JSON.stringify(debugInfo.auth, null, 2)}
                </pre>
              </div>
            )}
            
            {debugInfo.success && (
              <div>
                <h4 className="font-medium text-green-700">Upload Success</h4>
                <pre className="bg-green-50 p-2 rounded text-sm overflow-auto">
                  {JSON.stringify(debugInfo.response, null, 2)}
                </pre>
              </div>
            )}
            
            {debugInfo.error && (
              <div>
                <h4 className="font-medium text-red-700">Upload Error</h4>
                <pre className="bg-red-50 p-2 rounded text-sm overflow-auto">
                  {JSON.stringify(debugInfo.error, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
} 