import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { campaignAPI } from '../../services/api';
import toast from 'react-hot-toast';

const steps = [
  { id: 1, name: 'Campaign Type', description: 'Select Trade Desk or PulsePoint' },
  { id: 2, name: 'Campaign Goal', description: 'Choose Awareness or Action' },
  { id: 3, name: 'Channel', description: 'Select CTV, Display, Video, or Audio' },
  { id: 4, name: 'CTR Sensitivity', description: 'Is CTR sensitivity important?' },
  { id: 5, name: 'Analysis Level', description: 'Domain or Supply Vendor level' },
  { id: 6, name: 'Template', description: 'Save as reusable template' },
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

export default function NewCampaign() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    campaignType: '',
    goal: '',
    channel: '',
    ctrSensitivity: '',
    analysisLevel: '',
    saveAsTemplate: false,
  });
  const [submitting, setSubmitting] = useState(false);

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

  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      
      // Transform wizard data into proper campaign format with metadata
      const campaignData = {
        name: `${formData.campaignType} ${formData.goal} Campaign`, // Generate name from wizard data
        description: `${formData.campaignType} campaign focused on ${formData.goal} through ${formData.channel} channel. CTR sensitivity: ${formData.ctrSensitivity}, Analysis level: ${formData.analysisLevel}`,
        template_id: null,
        scoring_criteria: null,
        target_score: null,
        max_score: 100.0,
        min_score: 0.0,
        metadata: {
          goal: formData.goal,
          channel: formData.channel,
          ctr_sensitivity: formData.ctrSensitivity === 'yes',
          analysis_level: formData.analysisLevel
        }
      };
      
      const response = await campaignAPI.createCampaign(campaignData);
      
      toast.success('Campaign created successfully!');
      
      // If save as template is selected, we could save this configuration
      if (formData.saveAsTemplate) {
        // TODO: Implement template saving functionality
        console.log('Template saving not yet implemented');
      }
      
      // Redirect to the upload page with the campaign ID
      if (response.data?.campaign_id) {
        router.push(`/upload?campaign_id=${response.data.campaign_id}`);
      } else {
        router.push('/campaigns');
      }
    } catch (err) {
      console.error('Failed to create campaign:', err);
      console.error('Error response:', err.response?.data);
      console.error('Error status:', err.response?.status);
      console.error('Error message:', err.message);
      
      // Show more detailed error message
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create campaign. Please try again.';
      toast.error(`Failed to create campaign: ${errorMessage}`);
    } finally {
      setSubmitting(false);
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
            <h3 className="text-lg font-medium text-gray-900">Select Campaign Type</h3>
            <div className="grid grid-cols-1 gap-4">
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
        );

      case 2:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Select Campaign Goal</h3>
            <div className="grid grid-cols-1 gap-4">
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
        );

      case 3:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Select Channel</h3>
            <div className="grid grid-cols-1 gap-4">
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
        );

      case 4:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">CTR Sensitivity</h3>
            <p className="text-sm text-gray-500">
              Is Click-Through Rate (CTR) sensitivity important for this campaign?
            </p>
            <div className="grid grid-cols-1 gap-4">
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
        );

      case 5:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Select Analysis Level</h3>
            <div className="grid grid-cols-1 gap-4">
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
        );

      case 6:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Save as Template</h3>
            <p className="text-sm text-gray-500">
              Save this campaign configuration as a reusable template for future campaigns.
            </p>
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
            
            {/* Campaign Summary */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-3">Campaign Summary</h4>
              <div className="space-y-2 text-sm">
                <div><span className="font-medium">Type:</span> {formData.campaignType}</div>
                <div><span className="font-medium">Goal:</span> {formData.goal}</div>
                <div><span className="font-medium">Channel:</span> {formData.channel}</div>
                <div><span className="font-medium">CTR Sensitivity:</span> {formData.ctrSensitivity}</div>
                <div><span className="font-medium">Analysis Level:</span> {formData.analysisLevel}</div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1: return formData.campaignType;
      case 2: return formData.goal;
      case 3: return formData.channel;
      case 4: return formData.ctrSensitivity;
      case 5: return formData.analysisLevel;
      case 6: return true;
      default: return false;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Link href="/campaigns" className="text-gray-400 hover:text-gray-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Link>
              <h1 className="ml-4 text-2xl font-bold text-gray-900">New Campaign</h1>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
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
                disabled={submitting}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Creating...' : 'Create Campaign'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 