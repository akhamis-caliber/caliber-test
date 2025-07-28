import React from 'react';
import DebugUpload from '../components/DebugUpload';
import Layout from '../components/Shared/Layout';
import { withAuth } from '../utils/authGuard';

function DebugUploadPage() {
  return (
    <Layout title="Debug Upload - Caliber" description="Debug upload functionality">
      <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Upload Debug</h1>
          <p className="mt-2 text-gray-600">
            Test and debug upload functionality
          </p>
        </div>
        
        <DebugUpload />
        
        <div className="mt-8 p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h3 className="text-lg font-medium text-yellow-800 mb-2">Debug Instructions</h3>
          <ul className="text-sm text-yellow-700 space-y-1">
            <li>• Click "Test Authentication" to verify your login status</li>
            <li>• Click "Test Upload" to test file upload functionality</li>
            <li>• Check the debug information for detailed error analysis</li>
            <li>• Monitor browser console for additional error logs</li>
            <li>• Check backend logs for any server-side issues</li>
          </ul>
        </div>
      </div>
    </Layout>
  );
}

export default withAuth(DebugUploadPage); 