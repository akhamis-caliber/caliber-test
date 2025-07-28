import React, { useState } from 'react';
import { campaignAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

export default function DebugCampaignCreation() {
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState({});
  const { user, backendToken } = useAuth();

  const testCampaignCreation = async () => {
    setIsLoading(true);
    setDebugInfo({});

    try {
      // Check authentication
      const authInfo = {
        user: user ? { email: user.email, uid: user.uid } : null,
        backendToken: backendToken ? 'Present' : 'Missing',
        localStorageToken: localStorage.getItem('authToken') ? 'Present' : 'Missing'
      };
      setDebugInfo(prev => ({ ...prev, auth: authInfo }));

      // Test API connection
      try {
        const campaignsResponse = await campaignAPI.getCampaigns();
        setDebugInfo(prev => ({ 
          ...prev, 
          apiConnection: { status: 'Success', data: campaignsResponse.data?.length || 0 }
        }));
      } catch (error) {
        setDebugInfo(prev => ({ 
          ...prev, 
          apiConnection: { 
            status: 'Failed', 
            error: error.message,
            statusCode: error.response?.status,
            responseData: error.response?.data
          }
        }));
      }

      // Test campaign creation
      const testCampaignData = {
        name: "Debug Test Campaign",
        description: "Test campaign for debugging",
        metadata: {
          goal: "awareness",
          channel: "display",
          ctr_sensitivity: true,
          analysis_level: "domain"
        },
        max_score: 100.0
      };

      setDebugInfo(prev => ({ ...prev, requestData: testCampaignData }));

      const response = await campaignAPI.createCampaign(testCampaignData);
      
      setDebugInfo(prev => ({ 
        ...prev, 
        creationResult: { 
          status: 'Success', 
          campaignId: response.data?.campaign_id,
          response: response.data
        }
      }));

      toast.success('Campaign created successfully!');
      
      // Clean up - delete the test campaign
      if (response.data?.campaign_id) {
        try {
          await campaignAPI.deleteCampaign(response.data.campaign_id);
          setDebugInfo(prev => ({ 
            ...prev, 
            cleanup: { status: 'Success' }
          }));
        } catch (cleanupError) {
          setDebugInfo(prev => ({ 
            ...prev, 
            cleanup: { status: 'Failed', error: cleanupError.message }
          }));
        }
      }

    } catch (error) {
      console.error('Debug test failed:', error);
      setDebugInfo(prev => ({ 
        ...prev, 
        creationResult: { 
          status: 'Failed', 
          error: error.message,
          statusCode: error.response?.status,
          responseData: error.response?.data
        }
      }));
      toast.error(`Debug test failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-xl font-bold mb-4">Campaign Creation Debug</h2>
      
      <button
        onClick={testCampaignCreation}
        disabled={isLoading}
        className="mb-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {isLoading ? 'Testing...' : 'Test Campaign Creation'}
      </button>

      {Object.keys(debugInfo).length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Debug Information:</h3>
          
          {debugInfo.auth && (
            <div className="p-3 bg-gray-100 rounded">
              <h4 className="font-medium">Authentication:</h4>
              <pre className="text-sm mt-1">{JSON.stringify(debugInfo.auth, null, 2)}</pre>
            </div>
          )}

          {debugInfo.apiConnection && (
            <div className="p-3 bg-gray-100 rounded">
              <h4 className="font-medium">API Connection:</h4>
              <pre className="text-sm mt-1">{JSON.stringify(debugInfo.apiConnection, null, 2)}</pre>
            </div>
          )}

          {debugInfo.requestData && (
            <div className="p-3 bg-gray-100 rounded">
              <h4 className="font-medium">Request Data:</h4>
              <pre className="text-sm mt-1">{JSON.stringify(debugInfo.requestData, null, 2)}</pre>
            </div>
          )}

          {debugInfo.creationResult && (
            <div className="p-3 bg-gray-100 rounded">
              <h4 className="font-medium">Creation Result:</h4>
              <pre className="text-sm mt-1">{JSON.stringify(debugInfo.creationResult, null, 2)}</pre>
            </div>
          )}

          {debugInfo.cleanup && (
            <div className="p-3 bg-gray-100 rounded">
              <h4 className="font-medium">Cleanup:</h4>
              <pre className="text-sm mt-1">{JSON.stringify(debugInfo.cleanup, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
} 