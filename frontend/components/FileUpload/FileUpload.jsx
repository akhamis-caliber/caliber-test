import React, { useState } from 'react';
import axios from 'axios';

const ALLOWED_EXTENSIONS = ['csv', 'xls', 'xlsx'];
const MAX_FILE_SIZE_MB = 10;

function FileUpload({ campaignId, userId, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);

  const validateFile = (file) => {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return 'Invalid file type. Only CSV and Excel files are allowed.';
    }
    if (file.size / (1024 * 1024) > MAX_FILE_SIZE_MB) {
      return `File too large. Max size is ${MAX_FILE_SIZE_MB} MB.`;
    }
    return '';
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    const validationError = validateFile(droppedFile);
    if (validationError) {
      setError(validationError);
      setFile(null);
      setPreview(null);
      return;
    }
    setFile(droppedFile);
    setError('');
    setPreview(droppedFile.name);
  };

  const handleChange = (e) => {
    const selectedFile = e.target.files[0];
    const validationError = validateFile(selectedFile);
    if (validationError) {
      setError(validationError);
      setFile(null);
      setPreview(null);
      return;
    }
    setFile(selectedFile);
    setError('');
    setPreview(selectedFile.name);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(0);
    const formData = new FormData();
    formData.append('file', file);
    // Only add campaign_id if it's provided
    if (campaignId) {
      formData.append('campaign_id', campaignId);
    }
    formData.append('user_id', userId);
    try {
      const res = await axios.post('/api/reports/upload', formData, {
        onUploadProgress: (e) => {
          setProgress(Math.round((e.loaded * 100) / e.total));
        },
      });
      setUploading(false);
      setProgress(100);
      setFile(null);
      setPreview(null);
      if (onUploadSuccess) onUploadSuccess(res.data);
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
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-400 transition-colors"
      >
        <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
          <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <div className="mt-4">
          <label htmlFor="file-upload" className="cursor-pointer">
            <span className="mt-2 block text-sm font-medium text-gray-900">
              Drag & drop a file here, or click to select
            </span>
            <span className="mt-1 block text-xs text-gray-500">
              CSV, XLS, or XLSX up to 10MB
            </span>
          </label>
          <input
            id="file-upload"
            type="file"
            onChange={handleChange}
            accept=".csv,.xls,.xlsx"
            className="sr-only"
          />
        </div>
      </div>
      
      {preview && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-md">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="text-sm text-green-800">Selected: {preview}</span>
          </div>
        </div>
      )}
      
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="text-sm text-red-800">{error}</span>
          </div>
        </div>
      )}
      
      {uploading && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
          <div className="flex items-center">
            <svg className="animate-spin h-5 w-5 text-blue-400 mr-2" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-sm text-blue-800">Uploading: {progress}%</span>
          </div>
        </div>
      )}
      
      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {uploading ? 'Uploading...' : 'Upload File'}
      </button>
    </div>
  );
}

export default FileUpload; 