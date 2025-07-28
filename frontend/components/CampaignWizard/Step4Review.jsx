import { useState } from 'react';
import { 
  CheckCircleIcon, 
  DocumentTextIcon,
  ChartBarIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function Step4Review({ data, onBack, onComplete }) {
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateCampaign = async () => {
    setIsCreating(true);
    try {
      // TODO: Replace with actual API call
      // const response = await campaignAPI.createCampaign(data);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast.success('Campaign created successfully!');
      onComplete();
    } catch (error) {
      console.error('Error creating campaign:', error);
      toast.error('Failed to create campaign. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleBack = () => {
    onBack();
  };

  const getScoringMethodLabel = (method) => {
    const methods = {
      'weighted_average': 'Weighted Average',
      'simple_average': 'Simple Average',
      'custom_formula': 'Custom Formula'
    };
    return methods[method] || method;
  };

  const calculateTotalWeight = () => {
    if (!data.scoring_criteria) return 0;
    return data.scoring_criteria.reduce((sum, criterion) => sum + (criterion.weight || 0), 0);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center mr-4">
            <CheckCircleIcon className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Review & Create</h2>
            <p className="text-gray-600">Review your campaign settings before creating</p>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {/* Campaign Basics */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <DocumentTextIcon className="w-5 h-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Campaign Basics</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-700">Campaign Name</p>
              <p className="text-sm text-gray-900">{data.name}</p>
            </div>
            
            <div>
              <p className="text-sm font-medium text-gray-700">Description</p>
              <p className="text-sm text-gray-900">{data.description || 'No description provided'}</p>
            </div>
            
            <div>
              <p className="text-sm font-medium text-gray-700">Target Score</p>
              <p className="text-sm text-gray-900">{data.target_score || 'Not set'}</p>
            </div>
            
            <div>
              <p className="text-sm font-medium text-gray-700">Score Range</p>
              <p className="text-sm text-gray-900">{data.min_score} - {data.max_score}</p>
            </div>
          </div>
        </div>

        {/* Template Selection */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <DocumentTextIcon className="w-5 h-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Template Selection</h3>
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-700">Template</p>
            <p className="text-sm text-gray-900">
              {data.template_id ? `Template ID: ${data.template_id}` : 'Custom scoring criteria'}
            </p>
          </div>
        </div>

        {/* Scoring Configuration */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <ChartBarIcon className="w-5 h-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Scoring Configuration</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-gray-700">Scoring Method</p>
              <p className="text-sm text-gray-900">{getScoringMethodLabel(data.scoring_method)}</p>
            </div>
            
            {data.scoring_criteria && data.scoring_criteria.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-medium text-gray-700">Scoring Criteria</p>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">Total Weight:</span>
                    <span className={`text-sm font-bold ${
                      Math.abs(calculateTotalWeight() - 1.0) <= 0.01 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {Math.round(calculateTotalWeight() * 100)}%
                    </span>
                  </div>
                </div>
                
                <div className="space-y-3">
                  {data.scoring_criteria.map((criterion, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">{criterion.criterion_name}</h4>
                        <span className="text-sm font-medium text-indigo-600">
                          {Math.round(criterion.weight * 100)}%
                        </span>
                      </div>
                      
                      {criterion.description && (
                        <p className="text-sm text-gray-600 mb-2">{criterion.description}</p>
                      )}
                      
                      <div className="flex items-center justify-between text-sm text-gray-500">
                        <span>Score Range: {criterion.min_score} - {criterion.max_score}</span>
                        <span className={criterion.is_required ? 'text-green-600' : 'text-gray-400'}>
                          {criterion.is_required ? 'Required' : 'Optional'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Weight Validation Warning */}
                {Math.abs(calculateTotalWeight() - 1.0) > 0.01 && (
                  <div className="flex items-center mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-2" />
                    <div>
                      <p className="text-sm font-medium text-red-800">Weight Validation Warning</p>
                      <p className="text-sm text-red-700">
                        Total weight is {Math.round(calculateTotalWeight() * 100)}%. It should equal 100%.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Summary */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <InformationCircleIcon className="w-5 h-5 text-blue-400 mr-2" />
            <h3 className="text-lg font-medium text-blue-900">Campaign Summary</h3>
          </div>
          
          <div className="space-y-2 text-sm text-blue-800">
            <p>• Campaign will be created with <strong>{data.scoring_criteria?.length || 0} scoring criteria</strong></p>
            <p>• Scoring method: <strong>{getScoringMethodLabel(data.scoring_method)}</strong></p>
            <p>• Score range: <strong>{data.min_score} - {data.max_score}</strong></p>
            {data.target_score && (
              <p>• Target score: <strong>{data.target_score}</strong></p>
            )}
            <p>• Campaign will be created in <strong>Draft</strong> status</p>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex justify-between pt-6">
          <button
            type="button"
            onClick={handleBack}
            disabled={isCreating}
            className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Back
          </button>
          
          <button
            type="button"
            onClick={handleCreateCampaign}
            disabled={isCreating || Math.abs(calculateTotalWeight() - 1.0) > 0.01}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isCreating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Creating Campaign...
              </>
            ) : (
              <>
                <CheckCircleIcon className="w-5 h-5 mr-2" />
                Create Campaign
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
} 