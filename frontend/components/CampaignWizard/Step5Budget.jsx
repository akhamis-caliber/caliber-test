import React, { useState, useEffect } from 'react';
import { 
  CurrencyDollarIcon,
  CalendarIcon,
  ChartBarIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

export default function Step5Budget({ formData, setFormData, onNext, onBack }) {
  const [errors, setErrors] = useState({});
  const [budgetBreakdown, setBudgetBreakdown] = useState({
    media: 0,
    creative: 0,
    technology: 0,
    management: 0
  });

  useEffect(() => {
    // Initialize form data if not present
    if (!formData.budget) {
      setFormData(prev => ({
        ...prev,
        budget: {
          totalBudget: '',
          currency: 'USD',
          startDate: '',
          endDate: '',
          dailyBudget: '',
          budgetBreakdown: {
            media: 0,
            creative: 0,
            technology: 0,
            management: 0
          }
        }
      }));
    }
  }, [formData.budget, setFormData]);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.budget?.totalBudget || formData.budget.totalBudget <= 0) {
      newErrors.totalBudget = 'Total budget is required and must be greater than 0';
    }

    if (!formData.budget?.startDate) {
      newErrors.startDate = 'Start date is required';
    }

    if (!formData.budget?.endDate) {
      newErrors.endDate = 'End date is required';
    }

    if (formData.budget?.startDate && formData.budget?.endDate) {
      const startDate = new Date(formData.budget.startDate);
      const endDate = new Date(formData.budget.endDate);
      
      if (endDate <= startDate) {
        newErrors.endDate = 'End date must be after start date';
      }
    }

    if (!formData.budget?.dailyBudget || formData.budget.dailyBudget <= 0) {
      newErrors.dailyBudget = 'Daily budget is required and must be greater than 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateForm()) {
      onNext();
    }
  };

  const handleBudgetChange = (field, value) => {
    const newBudget = {
      ...formData.budget,
      [field]: value
    };

    // Calculate daily budget if total budget and dates are available
    if (newBudget.totalBudget && newBudget.startDate && newBudget.endDate) {
      const startDate = new Date(newBudget.startDate);
      const endDate = new Date(newBudget.endDate);
      const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
      newBudget.dailyBudget = (newBudget.totalBudget / daysDiff).toFixed(2);
    }

    setFormData(prev => ({
      ...prev,
      budget: newBudget
    }));
  };

  const handleBreakdownChange = (category, value) => {
    const newBreakdown = {
      ...budgetBreakdown,
      [category]: parseFloat(value) || 0
    };
    
    setBudgetBreakdown(newBreakdown);
    
    // Update form data
    setFormData(prev => ({
      ...prev,
      budget: {
        ...prev.budget,
        budgetBreakdown: newBreakdown
      }
    }));
  };

  const calculateTotalBreakdown = () => {
    return Object.values(budgetBreakdown).reduce((sum, value) => sum + value, 0);
  };

  const getBudgetUtilization = () => {
    const total = formData.budget?.totalBudget || 0;
    const breakdown = calculateTotalBreakdown();
    return total > 0 ? (breakdown / total) * 100 : 0;
  };

  const getUtilizationColor = (utilization) => {
    if (utilization > 100) return 'text-red-600';
    if (utilization > 90) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Budget & Timeline</h2>
        <p className="text-gray-600">Set your campaign budget and timeline</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Budget Section */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <CurrencyDollarIcon className="w-5 h-5 mr-2" />
              Budget Configuration
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Total Budget *
                </label>
                <div className="relative">
                  <select
                    value={formData.budget?.currency || 'USD'}
                    onChange={(e) => handleBudgetChange('currency', e.target.value)}
                    className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                  >
                    <option value="USD">$</option>
                    <option value="EUR">€</option>
                    <option value="GBP">£</option>
                  </select>
                  <input
                    type="number"
                    value={formData.budget?.totalBudget || ''}
                    onChange={(e) => handleBudgetChange('totalBudget', parseFloat(e.target.value))}
                    className={`w-full pl-12 pr-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                      errors.totalBudget ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="0.00"
                    min="0"
                    step="0.01"
                  />
                </div>
                {errors.totalBudget && (
                  <p className="mt-1 text-sm text-red-600">{errors.totalBudget}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Daily Budget *
                </label>
                <input
                  type="number"
                  value={formData.budget?.dailyBudget || ''}
                  onChange={(e) => handleBudgetChange('dailyBudget', parseFloat(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                    errors.dailyBudget ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                />
                {errors.dailyBudget && (
                  <p className="mt-1 text-sm text-red-600">{errors.dailyBudget}</p>
                )}
              </div>
            </div>
          </div>

          {/* Budget Breakdown */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <ChartBarIcon className="w-5 h-5 mr-2" />
              Budget Breakdown
            </h3>

            <div className="space-y-4">
              {Object.entries(budgetBreakdown).map(([category, value]) => (
                <div key={category}>
                  <label className="block text-sm font-medium text-gray-700 mb-2 capitalize">
                    {category} Budget
                  </label>
                  <input
                    type="number"
                    value={value}
                    onChange={(e) => handleBreakdownChange(category, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="0.00"
                    min="0"
                    step="0.01"
                  />
                </div>
              ))}

              <div className="pt-4 border-t border-gray-200">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">Total Breakdown:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {formData.budget?.currency === 'USD' ? '$' : formData.budget?.currency === 'EUR' ? '€' : '£'}
                    {calculateTotalBreakdown().toFixed(2)}
                  </span>
                </div>
                
                <div className="mt-2">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600">Budget Utilization:</span>
                    <span className={`font-medium ${getUtilizationColor(getBudgetUtilization())}`}>
                      {getBudgetUtilization().toFixed(1)}%
                    </span>
                  </div>
                  <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        getBudgetUtilization() > 100 ? 'bg-red-500' :
                        getBudgetUtilization() > 90 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(getBudgetUtilization(), 100)}%` }}
                    ></div>
                  </div>
                </div>

                {getBudgetUtilization() > 100 && (
                  <div className="mt-2 flex items-center text-sm text-red-600">
                    <ExclamationTriangleIcon className="w-4 h-4 mr-1" />
                    Budget breakdown exceeds total budget
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Timeline Section */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <CalendarIcon className="w-5 h-5 mr-2" />
              Campaign Timeline
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Start Date *
                </label>
                <input
                  type="date"
                  value={formData.budget?.startDate || ''}
                  onChange={(e) => handleBudgetChange('startDate', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                    errors.startDate ? 'border-red-300' : 'border-gray-300'
                  }`}
                  min={new Date().toISOString().split('T')[0]}
                />
                {errors.startDate && (
                  <p className="mt-1 text-sm text-red-600">{errors.startDate}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  End Date *
                </label>
                <input
                  type="date"
                  value={formData.budget?.endDate || ''}
                  onChange={(e) => handleBudgetChange('endDate', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                    errors.endDate ? 'border-red-300' : 'border-gray-300'
                  }`}
                  min={formData.budget?.startDate || new Date().toISOString().split('T')[0]}
                />
                {errors.endDate && (
                  <p className="mt-1 text-sm text-red-600">{errors.endDate}</p>
                )}
              </div>

              {formData.budget?.startDate && formData.budget?.endDate && (
                <div className="p-4 bg-blue-50 rounded-md">
                  <h4 className="text-sm font-medium text-blue-900 mb-2">Campaign Duration</h4>
                  <div className="text-sm text-blue-700">
                    {(() => {
                      const startDate = new Date(formData.budget.startDate);
                      const endDate = new Date(formData.budget.endDate);
                      const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
                      return `${daysDiff} day${daysDiff !== 1 ? 's' : ''}`;
                    })()}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Budget Summary */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Budget Summary</h3>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Budget:</span>
                <span className="text-sm font-medium text-gray-900">
                  {formData.budget?.currency === 'USD' ? '$' : formData.budget?.currency === 'EUR' ? '€' : '£'}
                  {formData.budget?.totalBudget?.toLocaleString() || '0.00'}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Daily Budget:</span>
                <span className="text-sm font-medium text-gray-900">
                  {formData.budget?.currency === 'USD' ? '$' : formData.budget?.currency === 'EUR' ? '€' : '£'}
                  {formData.budget?.dailyBudget || '0.00'}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Campaign Duration:</span>
                <span className="text-sm font-medium text-gray-900">
                  {formData.budget?.startDate && formData.budget?.endDate ? 
                    (() => {
                      const startDate = new Date(formData.budget.startDate);
                      const endDate = new Date(formData.budget.endDate);
                      const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
                      return `${daysDiff} days`;
                    })() : 'Not set'
                  }
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-6">
        <button
          onClick={onBack}
          className="px-6 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Back
        </button>
        <button
          onClick={handleNext}
          className="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Next
        </button>
      </div>
    </div>
  );
} 