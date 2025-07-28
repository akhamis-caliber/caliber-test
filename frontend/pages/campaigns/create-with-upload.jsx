import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { campaignAPI, reportAPI } from '../../services/api';
import FileUpload from '../../components/FileUpload/FileUpload';
import toast from 'react-hot-toast';

const steps = [
  { id: 1, name: 'Campaign Setup', description: 'Configure your campaign' },
  { id: 2, name: 'Upload Dataset', description: 'Upload your data for scoring' },
  { id: 3, name: 'Review & Create', description: 'Review and create campaign' },
];

const campaignTypes = [
  { id: 'trade-desk', name: 'Trade Desk', description: 'Google Marketing Platform' },
  { id: 'pulsepoint', name: 'PulsePoint', description: 'Taboola advertising platform' },
];

const campaignGoals = [
  { id: 'awareness', name: 'Awareness', description: 'Brand visibility and reach' },
  { id: 'action', name: 'Action', description: 'Conversions and engagement' },
];

const channels = [
  { id: 'ctv', name: 'CTV', description: 'Connected TV advertising' },
  { id: 'display', name: 'Display', description: 'Banner and display ads' },
  { id: 'video', name: 'Video', description: 'Video advertising' },
  { id: 'audio', name: 'Audio', description: 'Audio and podcast ads' },
];

const analysisLevels = [
  { id: 'domain', name: 'Domain-level', description: 'Analyze by website domain' },
  { id: 'supply-vendor', name: 'Supply Vendor-level', description: 'Analyze by supply vendor' },
];

export default function CreateCampaignWithUpload() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    campaignType: '',
    goal: '',
    channel: '',
    ctrSensitivity: '',
    analysisLevel: '',
    saveAsTemplate: false,
    campaignName: '',
    description: '',
  });
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleFileUploadSuccess = (uploadData) => {
    setUploadedFile(uploadData);
    toast.success('File uploaded successfully!');
    // Auto-advance to next step
    setTimeout(() => {
      handleNext();
    }, 1000);
  };

  const handleSubmit = async () => {
    if (!uploadedFile) {
      toast.error('Please upload a dataset first');
      return;
    }

    setIsSubmitting(true);
    try {
      // Create campaign
      const campaignData = {
        name: formData.campaignName || `${formData.campaignType} ${formData.goal} Campaign`,
        description: formData.description || `${formData.campaignType} campaign focused on ${formData.goal} through ${formData.channel} channel. CTR sensitivity: ${formData.ctrSensitivity}, Analysis level: ${formData.analysisLevel}`,
        template_id: null,
        scoring_criteria: {
          campaign_type: formData.campaignType,
          goal: formData.goal,
          channel: formData.channel,
          ctr_sensitivity: formData.ctrSensitivity,
          analysis_level: formData.analysisLevel,
        },
        target_score: null,
        max_score: 100.0,
        min_score: 0.0
      };
      
      const campaignResponse = await campaignAPI.createCampaign(campaignData);
      const campaignId = campaignResponse.data.id;

      // Link the uploaded file to the campaign
      if (uploadedFile.report_id) {
        await reportAPI.linkReportToCampaign(uploadedFile.report_id, campaignId);
      }

      toast.success('Campaign created successfully with dataset!');
      
      // Redirect to campaign details or dashboard
      router.push(`/campaigns/${campaignId}`);
    } catch (err) {
      console.error('Error creating campaign:', err);
      toast.error('Failed to create campaign. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateFormData = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h3 className="text-lg font-medium text-gray-900">Campaign Configuration</h3>
              <p className="text-sm text-gray-500">Set up your campaign parameters</p>
            </div>

            {/* Campaign Name */}
            <div>
              <label htmlFor="campaignName" className="block text-sm font-medium text-gray-700 mb-2">
                Campaign Name
              </label>
              <input
                type="text"
                id="campaignName"
                value={formData.campaignName}
                onChange={(e) => updateFormData('campaignName', e.target.value)}
                placeholder="Enter campaign name"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {/* Campaign Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => updateFormData('description', e.target.value)}
                placeholder="Enter campaign description"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {/* Campaign Type */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Campaign Type</h4>
              <div className="grid grid-cols-1 gap-3">
                {campaignTypes.map((type) => (
                  <label
                    key={type.id}
                    className={`relative flex cursor-pointer rounded-lg border p-4 shadow-sm focus:outline-none ${
                      formData.campaignType === type.id
                        ? 'border-indigo-500 ring-2 ring-indigo-500'
                        : 'border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="campaignType"
                      value={type.id}
                      checked={formData.campaignType === type.id}
                      onChange={(e) => updateFormData('campaignType', e.target.value)}
                      className="sr-only"
                    />
                    <div className="flex flex-1">
                      <div className="flex flex-col">
                        <span className="block text-sm font-medium text-gray-900">
                          {type.name}
                        </span>
                        <span className="mt-1 flex items-center text-sm text-gray-500">
                          {type.description}
                        </span>
                      </div>
                    </div>
                    <div className={`ml-3 flex h-5 w-5 items-center justify-center rounded-full ${
                      formData.campaignType === type.id
                        ? 'border-2 border-indigo-500 bg-indigo-500'
                        : 'border-2 border-gray-300'
                    }`}>
                      {formData.campaignType === type.id && (
                        <div className="h-2 w-2 rounded-full bg-white" />
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Campaign Goal */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Campaign Goal</h4>
              <div className="grid grid-cols-1 gap-3">
                {campaignGoals.map((goal) => (
                  <label
                    key={goal.id}
                    className={`relative flex cursor-pointer rounded-lg border p-4 shadow-sm focus:outline-none ${
                      formData.goal === goal.id
                        ? 'border-indigo-500 ring-2 ring-indigo-500'
                        : 'border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="goal"
                      value={goal.id}
                      checked={formData.goal === goal.id}
                      onChange={(e) => updateFormData('goal', e.target.value)}
                      className="sr-only"
                    />
                    <div className="flex flex-1">
                      <div className="flex flex-col">
                        <span className="block text-sm font-medium text-gray-900">
                          {goal.name}
                        </span>
                        <span className="mt-1 flex items-center text-sm text-gray-500">
                          {goal.description}
                        </span>
                      </div>
                    </div>
                    <div className={`ml-3 flex h-5 w-5 items-center justify-center rounded-full ${
                      formData.goal === goal.id
                        ? 'border-2 border-indigo-500 bg-indigo-500'
                        : 'border-2 border-gray-300'
                    }`}>
                      {formData.goal === goal.id && (
                        <div className="h-2 w-2 rounded-full bg-white" />
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Channel */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Channel</h4>
              <div className="grid grid-cols-1 gap-3">
                {channels.map((channel) => (
                  <label
                    key={channel.id}
                    className={`relative flex cursor-pointer rounded-lg border p-4 shadow-sm focus:outline-none ${
                      formData.channel === channel.id
                        ? 'border-indigo-500 ring-2 ring-indigo-500'
                        : 'border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="channel"
                      value={channel.id}
                      checked={formData.channel === channel.id}
                      onChange={(e) => updateFormData('channel', e.target.value)}
                      className="sr-only"
                    />
                    <div className="flex flex-1">
                      <div className="flex flex-col">
                        <span className="block text-sm font-medium text-gray-900">
                          {channel.name}
                        </span>
                        <span className="mt-1 flex items-center text-sm text-gray-500">
                          {channel.description}
                        </span>
                      </div>
                    </div>
                    <div className={`ml-3 flex h-5 w-5 items-center justify-center rounded-full ${
                      formData.channel === channel.id
                        ? 'border-2 border-indigo-500 bg-indigo-500'
                        : 'border-2 border-gray-300'
                    }`}>
                      {formData.channel === channel.id && (
                        <div className="h-2 w-2 rounded-full bg-white" />
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* CTR Sensitivity */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">CTR Sensitivity</h4>
              <p className="text-sm text-gray-500 mb-3">
                Is Click-Through Rate (CTR) sensitivity important for this campaign?
              </p>
              <div className="grid grid-cols-1 gap-3">
                {[
                  { id: 'yes', name: 'Yes', description: 'CTR is a key performance metric' },
                  { id: 'no', name: 'No', description: 'CTR is not a primary concern' },
                ].map((option) => (
                  <label
                    key={option.id}
                    className={`relative flex cursor-pointer rounded-lg border p-4 shadow-sm focus:outline-none ${
                      formData.ctrSensitivity === option.id
                        ? 'border-indigo-500 ring-2 ring-indigo-500'
                        : 'border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="ctrSensitivity"
                      value={option.id}
                      checked={formData.ctrSensitivity === option.id}
                      onChange={(e) => updateFormData('ctrSensitivity', e.target.value)}
                      className="sr-only"
                    />
                    <div className="flex flex-1">
                      <div className="flex flex-col">
                        <span className="block text-sm font-medium text-gray-900">
                          {option.name}
                        </span>
                        <span className="mt-1 flex items-center text-sm text-gray-500">
                          {option.description}
                        </span>
                      </div>
                    </div>
                    <div className={`ml-3 flex h-5 w-5 items-center justify-center rounded-full ${
                      formData.ctrSensitivity === option.id
                        ? 'border-2 border-indigo-500 bg-indigo-500'
                        : 'border-2 border-gray-300'
                    }`}>
                      {formData.ctrSensitivity === option.id && (
                        <div className="h-2 w-2 rounded-full bg-white" />
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Analysis Level */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Analysis Level</h4>
              <div className="grid grid-cols-1 gap-3">
                {analysisLevels.map((level) => (
                  <label
                    key={level.id}
                    className={`relative flex cursor-pointer rounded-lg border p-4 shadow-sm focus:outline-none ${
                      formData.analysisLevel === level.id
                        ? 'border-indigo-500 ring-2 ring-indigo-500'
                        : 'border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="analysisLevel"
                      value={level.id}
                      checked={formData.analysisLevel === level.id}
                      onChange={(e) => updateFormData('analysisLevel', e.target.value)}
                      className="sr-only"
                    />
                    <div className="flex flex-1">
                      <div className="flex flex-col">
                        <span className="block text-sm font-medium text-gray-900">
                          {level.name}
                        </span>
                        <span className="mt-1 flex items-center text-sm text-gray-500">
                          {level.description}
                        </span>
                      </div>
                    </div>
                    <div className={`ml-3 flex h-5 w-5 items-center justify-center rounded-full ${
                      formData.analysisLevel === level.id
                        ? 'border-2 border-indigo-500 bg-indigo-500'
                        : 'border-2 border-gray-300'
                    }`}>
                      {formData.analysisLevel === level.id && (
                        <div className="h-2 w-2 rounded-full bg-white" />
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h3 className="text-lg font-medium text-gray-900">Upload Dataset</h3>
              <p className="text-sm text-gray-500">Upload your data file for scoring analysis</p>
            </div>

            <FileUpload
              campaignId={null} // Will be set after campaign creation
              userId={1} // This should come from auth context
              onUploadSuccess={handleFileUploadSuccess}
            />

            {uploadedFile && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-md">
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-green-800">
                    File uploaded successfully: {uploadedFile.filename}
                  </span>
                </div>
              </div>
            )}
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h3 className="text-lg font-medium text-gray-900">Review & Create</h3>
              <p className="text-sm text-gray-500">Review your campaign and dataset before creating</p>
            </div>

            {/* Campaign Summary */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Campaign Summary</h4>
              <div className="space-y-2 text-sm">
                <div><span className="font-medium">Name:</span> {formData.campaignName || `${formData.campaignType} ${formData.goal} Campaign`}</div>
                <div><span className="font-medium">Type:</span> {formData.campaignType}</div>
                <div><span className="font-medium">Goal:</span> {formData.goal}</div>
                <div><span className="font-medium">Channel:</span> {formData.channel}</div>
                <div><span className="font-medium">CTR Sensitivity:</span> {formData.ctrSensitivity}</div>
                <div><span className="font-medium">Analysis Level:</span> {formData.analysisLevel}</div>
              </div>
            </div>

            {/* Dataset Summary */}
            {uploadedFile && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Dataset Summary</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">File:</span> {uploadedFile.filename}</div>
                  <div><span className="font-medium">Status:</span> Uploaded successfully</div>
                </div>
              </div>
            )}

            {/* Save as Template */}
            <div className="flex items-center">
              <input
                id="saveAsTemplate"
                name="saveAsTemplate"
                type="checkbox"
                checked={formData.saveAsTemplate}
                onChange={(e) => updateFormData('saveAsTemplate', e.target.checked)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label htmlFor="saveAsTemplate" className="ml-2 block text-sm text-gray-900">
                Save as reusable template
              </label>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return formData.campaignType && formData.goal && formData.channel && 
               formData.ctrSensitivity && formData.analysisLevel;
      case 2:
        return uploadedFile !== null;
      case 3:
        return true;
      default:
        return false;
    }
  };

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
              <h1 className="ml-4 text-2xl font-bold text-gray-900">Create Campaign & Upload Data</h1>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Progress Steps */}
        <nav aria-label="Progress" className="mb-8">
          <ol className="flex items-center">
            {steps.map((step, stepIdx) => (
              <li key={step.name} className={`relative ${stepIdx !== steps.length - 1 ? 'pr-8 sm:pr-20' : ''} flex-1`}>
                <div className="absolute inset-0 flex items-center" aria-hidden="true">
                  <div className={`h-0.5 w-full ${step.id < currentStep ? 'bg-indigo-600' : 'bg-gray-200'}`} />
                </div>
                <div className={`relative flex h-8 w-8 items-center justify-center rounded-full ${
                  step.id < currentStep ? 'bg-indigo-600' : step.id === currentStep ? 'bg-indigo-600' : 'bg-gray-200'
                }`}>
                  {step.id < currentStep ? (
                    <svg className="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <span className={`text-sm font-medium ${step.id === currentStep ? 'text-white' : 'text-gray-500'}`}>
                      {step.id}
                    </span>
                  )}
                </div>
                <div className="absolute top-10 left-1/2 transform -translate-x-1/2">
                  <span className={`text-xs font-medium ${step.id === currentStep ? 'text-indigo-600' : 'text-gray-500'}`}>
                    {step.name}
                  </span>
                </div>
              </li>
            ))}
          </ol>
        </nav>

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow p-6">
          {renderStepContent()}
        </div>

        {/* Navigation Buttons */}
        <div className="mt-8 flex justify-between">
          <button
            type="button"
            onClick={handleBack}
            disabled={currentStep === 1}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Back
          </button>
          
          <div className="flex space-x-3">
            {currentStep < steps.length ? (
              <button
                type="button"
                onClick={handleNext}
                disabled={!canProceed()}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Continue
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSubmit}
                disabled={isSubmitting || !uploadedFile}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creating...' : 'Create Campaign & Start Analysis'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 