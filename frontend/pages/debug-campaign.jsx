import React from 'react';
import DebugCampaignCreation from '../components/DebugCampaignCreation';
import Layout from '../components/Shared/Layout';
import { withAuth } from '../utils/authGuard';

function DebugCampaignPage() {
  return (
    <Layout title="Debug Campaign Creation - Caliber" description="Debug campaign creation functionality">
      <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Campaign Creation Debug</h1>
          <p className="mt-2 text-gray-600">
            Test and debug campaign creation functionality
          </p>
        </div>
        
        <DebugCampaignCreation />
        
        <div className="mt-8 p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h3 className="text-lg font-medium text-yellow-800 mb-2">Debug Instructions</h3>
          <ul className="text-sm text-yellow-700 space-y-1">
            <li>• Click "Test Campaign Creation" to run a complete test</li>
            <li>• Check the debug information for authentication status</li>
            <li>• Verify API connection and response data</li>
            <li>• Monitor browser console for detailed error logs</li>
            <li>• Check backend logs for any server-side issues</li>
          </ul>
        </div>
      </div>
    </Layout>
  );
}

export default withAuth(DebugCampaignPage); 