import { useState } from 'react';
import { useRouter } from 'next/router';
import { 
  XMarkIcon,
  CheckIcon
} from '@heroicons/react/24/outline';
import Step1Basics from './Step1Basics';
import Step2Template from './Step2Template';
import Step3Criteria from './Step3Criteria';
import Step4Review from './Step4Review';
import Step5Budget from './Step5Budget';
import Step6Confirmation from './Step6Confirmation';

const STEPS = [
  { id: 1, name: 'Basics', component: Step1Basics },
  { id: 2, name: 'Template', component: Step2Template },
  { id: 3, name: 'Criteria', component: Step3Criteria },
  { id: 4, name: 'Review', component: Step4Review },
  { id: 5, name: 'Budget', component: Step5Budget },
  { id: 6, name: 'Confirm', component: Step6Confirmation }
];

export default function CampaignWizard({ onClose, onComplete, initialData }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [campaignData, setCampaignData] = useState(() => initialData || {
    name: '',
    description: '',
    template_id: null,
    scoring_method: 'weighted_average',
    scoring_criteria: null,
    custom_formula: null,
    target_score: null,
    max_score: 100,
    min_score: 0
  });
  const router = useRouter();

  const handleNext = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleUpdate = (data) => {
    setCampaignData(prev => ({ ...prev, ...data }));
  };

  const handleComplete = () => {
    if (onComplete) {
      onComplete(campaignData);
    } else {
      // Default behavior: redirect to campaigns page
      router.push('/campaigns');
    }
  };

  const handleClose = () => {
    if (onClose) {
      onClose();
    } else {
      router.back();
    }
  };

  const getCurrentStepComponent = () => {
    const step = STEPS.find(s => s.id === currentStep);
    if (!step) return null;

    const Component = step.component;
    const props = {
      formData: campaignData,
      setFormData: setCampaignData,
      onNext: handleNext,
      onBack: handleBack,
      onUpdate: handleUpdate
    };

    // Add onComplete prop for the last step
    if (currentStep === STEPS.length) {
      props.onSubmit = handleComplete;
    }

    return <Component {...props} />;
  };

  const getStepStatus = (stepId) => {
    if (stepId < currentStep) return 'completed';
    if (stepId === currentStep) return 'current';
    return 'upcoming';
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Create New Campaign</h1>
            <p className="text-gray-600">Set up your campaign in a few simple steps</p>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => {
              const status = getStepStatus(step.id);
              const isLast = index === STEPS.length - 1;

              return (
                <div key={step.id} className="flex items-center">
                  <div className="flex items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                      status === 'completed'
                        ? 'bg-indigo-600 border-indigo-600 text-white'
                        : status === 'current'
                        ? 'bg-white border-indigo-600 text-indigo-600'
                        : 'bg-white border-gray-300 text-gray-500'
                    }`}>
                      {status === 'completed' ? (
                        <CheckIcon className="w-5 h-5" />
                      ) : (
                        <span className="text-sm font-medium">{step.id}</span>
                      )}
                    </div>
                    <span className={`ml-2 text-sm font-medium ${
                      status === 'completed'
                        ? 'text-indigo-600'
                        : status === 'current'
                        ? 'text-indigo-600'
                        : 'text-gray-500'
                    }`}>
                      {step.name}
                    </span>
                  </div>
                  {!isLast && (
                    <div className={`flex-1 h-0.5 mx-4 ${
                      status === 'completed' ? 'bg-indigo-600' : 'bg-gray-300'
                    }`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="min-h-96">
          {getCurrentStepComponent()}
        </div>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-500">
              Step {currentStep} of {STEPS.length}
            </div>
            <div className="text-sm text-gray-500">
              {currentStep === 1 && 'Campaign basics and scoring range'}
              {currentStep === 2 && 'Template selection or custom criteria'}
              {currentStep === 3 && 'Scoring criteria configuration'}
              {currentStep === 4 && 'Review campaign settings'}
              {currentStep === 5 && 'Budget and timeline configuration'}
              {currentStep === 6 && 'Final confirmation and submission'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 