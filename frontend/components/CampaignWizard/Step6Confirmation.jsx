import React, { useState } from 'react';
import { 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  CalendarIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  GlobeAltIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function Step6Confirmation({ formData, onSubmit, onBack }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const handleSubmit = async () => {
    if (!agreedToTerms) {
      toast.error('Please agree to the terms and conditions');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      toast.success('Campaign created successfully!');
    } catch (error) {
      toast.error('Failed to create campaign. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getCampaignDuration = () => {
    if (!formData.budget?.startDate || !formData.budget?.endDate) return 'Not set';
    const startDate = new Date(formData.budget.startDate);
    const endDate = new Date(formData.budget.endDate);
    const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
    return `${daysDiff} days`;
  };

  const getBudgetUtilization = () => {
    const total = formData.budget?.totalBudget || 0;
    const breakdown = formData.budget?.budgetBreakdown || {};
    const breakdownTotal = Object.values(breakdown).reduce((sum, value) => sum + (value || 0), 0);
    return total > 0 ? (breakdownTotal / total) * 100 : 0;
  };

  const getUtilizationStatus = () => {
    const utilization = getBudgetUtilization();
    if (utilization > 100) return { color: 'text-red-600', icon: ExclamationTriangleIcon, text: 'Over Budget' };
    if (utilization > 90) return { color: 'text-yellow-600', icon: ExclamationTriangleIcon, text: 'Near Limit' };
    return { color: 'text-green-600', icon: CheckCircleIcon, text: 'Good' };
  };

  const utilizationStatus = getUtilizationStatus();

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Confirm Campaign</h2>
        <p className="text-gray-600">Review your campaign details before creating</p>
      </div>

      {/* Campaign Summary */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <DocumentTextIcon className="w-5 h-5 mr-2" />
            Campaign Summary
          </h3>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Campaign Name</h4>
                <p className="text-sm text-gray-900">{formData.basics?.name || 'Not set'}</p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Description</h4>
                <p className="text-sm text-gray-900">{formData.basics?.description || 'Not set'}</p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Campaign Type</h4>
                <p className="text-sm text-gray-900">{formData.basics?.type || 'Not set'}</p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Industry</h4>
                <p className="text-sm text-gray-900">{formData.basics?.industry || 'Not set'}</p>
              </div>
            </div>

            {/* Template Information */}
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Template</h4>
                <p className="text-sm text-gray-900">{formData.template?.name || 'Not set'}</p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Scoring Model</h4>
                <p className="text-sm text-gray-900">{formData.template?.scoringModel || 'Not set'}</p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Custom Weights</h4>
                <p className="text-sm text-gray-900">
                  {formData.template?.useCustomWeights ? 'Yes' : 'No'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Budget & Timeline */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <CurrencyDollarIcon className="w-5 h-5 mr-2" />
            Budget & Timeline
          </h3>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                <CurrencyDollarIcon className="w-4 h-4 mr-1" />
                Total Budget
              </h4>
              <p className="text-lg font-semibold text-gray-900">
                {formData.budget?.currency === 'USD' ? '$' : formData.budget?.currency === 'EUR' ? '€' : '£'}
                {formData.budget?.totalBudget?.toLocaleString() || '0.00'}
              </p>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                <CalendarIcon className="w-4 h-4 mr-1" />
                Duration
              </h4>
              <p className="text-lg font-semibold text-gray-900">{getCampaignDuration()}</p>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                <ChartBarIcon className="w-4 h-4 mr-1" />
                Budget Status
              </h4>
              <div className="flex items-center">
                <utilizationStatus.icon className={`w-5 h-5 mr-2 ${utilizationStatus.color}`} />
                <span className={`text-lg font-semibold ${utilizationStatus.color}`}>
                  {utilizationStatus.text}
                </span>
              </div>
            </div>
          </div>

          {/* Budget Breakdown */}
          {formData.budget?.budgetBreakdown && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Budget Breakdown</h4>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(formData.budget.budgetBreakdown).map(([category, amount]) => (
                  <div key={category} className="text-center">
                    <p className="text-xs text-gray-500 uppercase tracking-wide">{category}</p>
                    <p className="text-sm font-medium text-gray-900">
                      {formData.budget?.currency === 'USD' ? '$' : formData.budget?.currency === 'EUR' ? '€' : '£'}
                      {amount?.toLocaleString() || '0.00'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Targeting Criteria */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <GlobeAltIcon className="w-5 h-5 mr-2" />
            Targeting Criteria
          </h3>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Geographic Targeting</h4>
              <div className="space-y-1">
                {formData.criteria?.geographicTargeting?.length > 0 ? (
                  formData.criteria.geographicTargeting.map((location, index) => (
                    <span key={index} className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-2 mb-1">
                      {location}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-gray-500">No geographic restrictions</p>
                )}
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Demographic Targeting</h4>
              <div className="space-y-1">
                {formData.criteria?.demographicTargeting?.length > 0 ? (
                  formData.criteria.demographicTargeting.map((demo, index) => (
                    <span key={index} className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded mr-2 mb-1">
                      {demo}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-gray-500">No demographic restrictions</p>
                )}
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Interest Targeting</h4>
              <div className="space-y-1">
                {formData.criteria?.interestTargeting?.length > 0 ? (
                  formData.criteria.interestTargeting.map((interest, index) => (
                    <span key={index} className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded mr-2 mb-1">
                      {interest}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-gray-500">No interest restrictions</p>
                )}
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Behavioral Targeting</h4>
              <div className="space-y-1">
                {formData.criteria?.behavioralTargeting?.length > 0 ? (
                  formData.criteria.behavioralTargeting.map((behavior, index) => (
                    <span key={index} className="inline-block bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded mr-2 mb-1">
                      {behavior}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-gray-500">No behavioral restrictions</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Goals */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <UserGroupIcon className="w-5 h-5 mr-2" />
            Performance Goals
          </h3>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Target CTR</h4>
              <p className="text-lg font-semibold text-gray-900">
                {formData.criteria?.targetCTR ? `${formData.criteria.targetCTR}%` : 'Not set'}
              </p>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Target Conversion Rate</h4>
              <p className="text-lg font-semibold text-gray-900">
                {formData.criteria?.targetConversionRate ? `${formData.criteria.targetConversionRate}%` : 'Not set'}
              </p>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Target CPA</h4>
              <p className="text-lg font-semibold text-gray-900">
                {formData.criteria?.targetCPA ? 
                  `${formData.budget?.currency === 'USD' ? '$' : formData.budget?.currency === 'EUR' ? '€' : '£'}${formData.criteria.targetCPA}` : 
                  'Not set'
                }
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Terms and Conditions */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              id="terms"
              type="checkbox"
              checked={agreedToTerms}
              onChange={(e) => setAgreedToTerms(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
          </div>
          <div className="ml-3 text-sm">
            <label htmlFor="terms" className="font-medium text-gray-700">
              I agree to the terms and conditions
            </label>
            <p className="text-gray-500">
              By creating this campaign, you agree to our terms of service and privacy policy. 
              You confirm that all information provided is accurate and you have the right to 
              use any content included in this campaign.
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-6">
        <button
          onClick={onBack}
          disabled={isSubmitting}
          className="px-6 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          Back
        </button>
        <button
          onClick={handleSubmit}
          disabled={isSubmitting || !agreedToTerms}
          className="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Creating Campaign...
            </div>
          ) : (
            'Create Campaign'
          )}
        </button>
      </div>
    </div>
  );
} 