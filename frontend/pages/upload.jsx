import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useAuth } from '../context/AuthContext';
import { reportAPI } from '../services/api';
import { campaignAPI } from '../services/api';

const requiredColumns = ['Domain', 'Impressions', 'CTR', 'Conversions', 'Total Spend'];

export default function UploadPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [file, setFile] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState('');

  // Fetch campaigns on component mount
  React.useEffect(() => {
    const fetchCampaigns = async () => {
      try {
        const response = await campaignAPI.getCampaigns();
        setCampaigns(response.data || []);
        // Set first campaign as default if available
        if (response.data && response.data.length > 0) {
          setSelectedCampaignId(response.data[0].id.toString());
        }
      } catch (err) {
        console.error('Failed to fetch campaigns:', err);
        setError('Failed to load campaigns. Please try again.');
      }
    };

    if (user) {
      fetchCampaigns();
    }
  }, [user]);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (!selectedFile) return;

    // Validate file type
    const allowedTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    if (!allowedTypes.includes(selectedFile.type)) {
      setError('Please select a CSV or Excel file');
      return;
    }

    // Validate file size (10MB max)
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setFile(selectedFile);
    setError('');
    setValidationErrors([]);

    // Read and preview the file
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target.result;
        const lines = text.split('\n');
        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
        const data = lines.slice(1, 6).map(line => {
          const values = line.split(',').map(v => v.trim().replace(/"/g, ''));
          const row = {};
          headers.forEach((header, index) => {
            row[header] = values[index] || '';
          });
          return row;
        }).filter(row => Object.values(row).some(val => val !== ''));

        setPreviewData({ headers, data });
        validateColumns(headers);
      } catch (err) {
        setError('Error reading file. Please check the file format.');
      }
    };
    reader.readAsText(selectedFile);
  };

  const validateColumns = (headers) => {
    const errors = [];
    
    // Enhanced column matching logic with abbreviations and variations
    const isColumnMatch = (header, requiredCol) => {
      const headerLower = header.toLowerCase();
      const colLower = requiredCol.toLowerCase();
      
      // Direct match
      if (headerLower === colLower) return true;
      
      // Contains match
      if (headerLower.includes(colLower) || colLower.includes(headerLower)) return true;
      
      // Abbreviation and variation match
      const columnVariations = {
        'ctr': ['click through rate', 'click-through rate', 'clickthrough rate', 'click rate'],
        'total spend': ['budget', 'total budget', 'spend', 'total spend', 'cost', 'total cost'],
        'conversions': ['conversion', 'total conversions', 'converted', 'total converted'],
        'impressions': ['impression', 'total impressions', 'views', 'total views'],
        'domain': ['website', 'site', 'url', 'domain name', 'website name']
      };
      
      if (columnVariations[colLower]) {
        return columnVariations[colLower].some(variation => headerLower.includes(variation));
      }
      
      return false;
    };
    
    const missingColumns = requiredColumns.filter(col => 
      !headers.some(header => isColumnMatch(header, col))
    );

    if (missingColumns.length > 0) {
      errors.push(`Missing required columns: ${missingColumns.join(', ')}`);
    }

    setValidationErrors(errors);
  };

  const handleUpload = async () => {
    if (!file || validationErrors.length > 0 || !selectedCampaignId || !user) {
      if (!selectedCampaignId) {
        setError('Please select a campaign');
      }
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('campaign_id', selectedCampaignId);
      formData.append('user_id', user.uid || user.id);
      
      const response = await reportAPI.uploadFile(formData);
      const reportId = response.data.report_id;
      
      // Poll for status
      let status = 'queued';
      while (status === 'queued' || status === 'processing') {
        await new Promise(res => setTimeout(res, 2000));
        const statusRes = await reportAPI.getReportStatus(reportId);
        status = statusRes.data.status;
      }
      
      router.push('/scoring-results');
    } catch (err) {
      console.error('Upload error details:', {
        message: err.message,
        status: err.response?.status,
        data: err.response?.data,
        config: err.config
      });
      
      let errorMessage = 'Upload failed. Please try again.';
      
      if (err.response?.status === 401) {
        errorMessage = 'Authentication required. Please log in again.';
      } else if (err.response?.status === 400) {
        errorMessage = err.response?.data?.detail || 'Invalid file format or data.';
      } else if (err.response?.status === 422) {
        // Handle 422 validation errors - they return complex objects
        if (err.response?.data?.detail) {
          if (Array.isArray(err.response.data.detail)) {
            // Multiple validation errors
            errorMessage = err.response.data.detail.map(error => 
              `${error.loc?.join('.') || 'Field'}: ${error.msg}`
            ).join('; ');
          } else if (typeof err.response.data.detail === 'object') {
            // Single validation error object
            errorMessage = `${err.response.data.detail.loc?.join('.') || 'Field'}: ${err.response.data.detail.msg}`;
          } else {
            // String error
            errorMessage = err.response.data.detail;
          }
        } else {
          errorMessage = 'Validation error occurred. Please check your input.';
        }
      } else if (err.response?.status === 413) {
        errorMessage = 'File too large. Maximum size is 10MB.';
      } else if (err.response?.status === 404) {
        errorMessage = 'Campaign not found. Please select a valid campaign.';
      } else if (err.response?.data?.detail) {
        // Handle other error responses
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else {
          errorMessage = 'An error occurred during upload.';
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (value) => {
    if (!value || value === '') return '0';
    const num = parseFloat(value);
    if (isNaN(num)) return value;
    return num.toLocaleString();
  };

  const formatPercentage = (value) => {
    if (!value || value === '') return '0%';
    const num = parseFloat(value);
    if (isNaN(num)) return value;
    // Handle both decimal and percentage formats
    if (num > 1) {
      return `${num.toFixed(2)}%`;
    } else {
      return `${(num * 100).toFixed(2)}%`;
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Authentication Required</h2>
          <p className="text-gray-600 mb-4">Please log in to upload files.</p>
          <Link href="/login" className="btn-primary">
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Link href="/dashboard" className="text-gray-400 hover:text-gray-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Link>
              <h1 className="ml-4 text-2xl font-bold text-gray-900">Upload Report</h1>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-6">Upload Campaign Report</h2>
          
          {/* Campaign Selection */}
          <div className="mb-6">
            <label htmlFor="campaign" className="block text-sm font-medium text-gray-700 mb-2">
              Select Campaign *
            </label>
            <select
              id="campaign"
              value={selectedCampaignId}
              onChange={(e) => setSelectedCampaignId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              required
            >
              <option value="">Select a campaign...</option>
              {campaigns.map((campaign) => (
                <option key={campaign.id} value={campaign.id}>
                  {campaign.name}
                </option>
              ))}
            </select>
            {campaigns.length === 0 && (
              <p className="mt-1 text-sm text-gray-500">
                No campaigns found. <Link href="/campaigns/new" className="text-indigo-600 hover:text-indigo-500">Create a campaign first</Link>.
              </p>
            )}
          </div>

          {/* File Upload */}
          <div className="mb-6">
            <label htmlFor="file" className="block text-sm font-medium text-gray-700 mb-2">
              Upload File *
            </label>
            <input
              type="file"
              id="file"
              accept=".csv,.xls,.xlsx"
              onChange={handleFileChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              Supported formats: CSV, Excel (.xls, .xlsx). Max size: 10MB
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* File Preview */}
          {previewData && (
            <div className="mb-6">
              <h3 className="text-md font-medium text-gray-900 mb-3">File Preview</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {previewData.headers.map((header, index) => (
                        <th key={index} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {previewData.data.map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {previewData.headers.map((header, colIndex) => (
                          <td key={colIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {header.toLowerCase().includes('impressions') || header.toLowerCase().includes('spend') || header.toLowerCase().includes('conversions')
                              ? formatNumber(row[header])
                              : header.toLowerCase().includes('ctr') || header.toLowerCase().includes('rate')
                              ? formatPercentage(row[header])
                              : row[header]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Column Validation */}
              {validationErrors.length > 0 && (
                <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-yellow-800">
                        Column Validation
                      </h3>
                      <div className="mt-2 text-sm text-yellow-700">
                        <ul className="list-disc pl-5 space-y-1">
                          {validationErrors.map((error, index) => (
                            <li key={index}>{error}</li>
                          ))}
                        </ul>
                        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
                          <h4 className="text-sm font-medium text-blue-800 mb-2">Required Columns:</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-blue-700">
                            <div><strong>Domain:</strong> website, site, url, domain name</div>
                            <div><strong>Impressions:</strong> views, total views, impression</div>
                            <div><strong>CTR:</strong> click through rate, click rate</div>
                            <div><strong>Conversions:</strong> conversion, converted</div>
                            <div><strong>Total Spend:</strong> budget, spend, cost</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Upload Button */}
          <div className="flex justify-end space-x-4">
            <Link
              href="/dashboard"
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </Link>
            <button
              onClick={handleUpload}
              disabled={loading || !file || validationErrors.length > 0 || !selectedCampaignId}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Uploading...' : 'Upload Report'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 