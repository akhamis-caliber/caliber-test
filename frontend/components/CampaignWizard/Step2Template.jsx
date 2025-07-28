import { useState, useEffect } from 'react';
import { 
  DocumentDuplicateIcon, 
  PlusIcon,
  CheckIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { campaignAPI } from '../../services/api';

export default function Step2Template({ data, onNext, onBack, onUpdate }) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState(data.template_id || null);
  const [useCustom, setUseCustom] = useState(!data.template_id);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await campaignAPI.getTemplates();
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateSelect = (templateId) => {
    setSelectedTemplate(templateId);
    setUseCustom(false);
    
    // Update parent component
    onUpdate({
      ...data,
      template_id: templateId,
      scoring_criteria: templates.find(t => t.id === templateId)?.default_criteria || null
    });
  };

  const handleCustomSelect = () => {
    setSelectedTemplate(null);
    setUseCustom(true);
    
    // Update parent component
    onUpdate({
      ...data,
      template_id: null,
      scoring_criteria: null
    });
  };

  const handleNext = () => {
    onNext();
  };

  const handleBack = () => {
    onBack();
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center mr-4">
            <DocumentDuplicateIcon className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Template Selection</h2>
            <p className="text-gray-600">Choose a template or create custom scoring criteria</p>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {/* Custom Option */}
        <div 
          className={`border-2 rounded-lg p-6 cursor-pointer transition-colors ${
            useCustom 
              ? 'border-indigo-500 bg-indigo-50' 
              : 'border-gray-200 hover:border-gray-300'
          }`}
          onClick={handleCustomSelect}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center mr-4 ${
                useCustom ? 'border-indigo-500 bg-indigo-500' : 'border-gray-300'
              }`}>
                {useCustom && <CheckIcon className="w-4 h-4 text-white" />}
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <PlusIcon className="w-5 h-5 mr-2" />
                  Custom Scoring Criteria
                </h3>
                <p className="text-gray-600 mt-1">
                  Create your own scoring criteria from scratch
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Available Templates */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Available Templates</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <div
                key={template.id}
                className={`border-2 rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedTemplate === template.id 
                    ? 'border-indigo-500 bg-indigo-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleTemplateSelect(template.id)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center">
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mr-3 ${
                      selectedTemplate === template.id ? 'border-indigo-500 bg-indigo-500' : 'border-gray-300'
                    }`}>
                      {selectedTemplate === template.id && <CheckIcon className="w-3 h-3 text-white" />}
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">{template.name}</h4>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {template.category}
                      </span>
                    </div>
                  </div>
                </div>
                
                <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                
                {/* Template Criteria Preview */}
                <div className="space-y-2">
                  <p className="text-xs font-medium text-gray-700">Scoring Criteria:</p>
                  {template.default_criteria?.slice(0, 3).map((criteria, index) => (
                    <div key={index} className="flex justify-between text-xs text-gray-600">
                      <span>{criteria.criterion_name}</span>
                      <span className="font-medium">{Math.round(criteria.weight * 100)}%</span>
                    </div>
                  ))}
                  {template.default_criteria?.length > 3 && (
                    <p className="text-xs text-gray-500">
                      +{template.default_criteria.length - 3} more criteria
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Template Details */}
        {selectedTemplate && !useCustom && (
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center mb-3">
              <InformationCircleIcon className="w-5 h-5 text-gray-400 mr-2" />
              <h4 className="font-medium text-gray-900">Selected Template Details</h4>
            </div>
            
            {(() => {
              const template = templates.find(t => t.id === selectedTemplate);
              return template ? (
                <div className="space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-700">{template.name}</p>
                    <p className="text-sm text-gray-600">{template.description}</p>
                  </div>
                  
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">Scoring Criteria:</p>
                    <div className="space-y-2">
                      {template.default_criteria?.map((criteria, index) => (
                        <div key={index} className="flex justify-between items-center text-sm">
                          <span className="text-gray-600">{criteria.criterion_name}</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-gray-500">{criteria.min_score}-{criteria.max_score} pts</span>
                            <span className="font-medium text-gray-900">{Math.round(criteria.weight * 100)}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : null;
            })()}
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between pt-6">
          <button
            type="button"
            onClick={handleBack}
            className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Back
          </button>
          
          <button
            type="button"
            onClick={handleNext}
            disabled={!selectedTemplate && !useCustom}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next: Scoring Criteria
          </button>
        </div>
      </div>
    </div>
  );
} 