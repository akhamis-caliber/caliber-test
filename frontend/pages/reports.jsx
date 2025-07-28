import React, { useState } from 'react';
import FileUpload from '../components/FileUpload/FileUpload';
import ReportViewer from '../components/ReportViewer/ReportViewer';
import { useAuth } from '../context/AuthContext';

export default function Reports() {
  const { user } = useAuth();
  const [selectedCampaignId, setSelectedCampaignId] = useState(1); // Default campaign ID
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const handleUploadSuccess = (data) => {
    setUploadSuccess(true);
    // You could show a success message or redirect
    console.log('Upload successful:', data);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Reports</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* File Upload Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Upload New Report</h2>
          <FileUpload
            campaignId={selectedCampaignId}
            userId={user?.uid || 1}
            onUploadSuccess={handleUploadSuccess}
          />
        </div>

        {/* Reports List Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <ReportViewer
            campaignId={selectedCampaignId}
            userId={user?.uid || 1}
          />
        </div>
      </div>

      {uploadSuccess && (
        <div className="mt-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
          File uploaded successfully! Processing has started.
        </div>
      )}
    </div>
  );
} 