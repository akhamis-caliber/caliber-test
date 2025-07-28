import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { 
  DocumentTextIcon, 
  InformationCircleIcon 
} from '@heroicons/react/24/outline';

export default function Step1Basics({ data, onNext, onUpdate }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    watch
  } = useForm({
    mode: 'onChange',
    defaultValues: {
      name: data.name || '',
      description: data.description || '',
      target_score: data.target_score || '',
      max_score: data.max_score || 100,
      min_score: data.min_score || 0
    }
  });

  const watchedValues = watch();

  const onSubmit = async (formData) => {
    setIsSubmitting(true);
    try {
      // Update parent component with form data
      onUpdate({
        ...data,
        ...formData,
        target_score: formData.target_score ? parseFloat(formData.target_score) : null,
        max_score: parseFloat(formData.max_score),
        min_score: parseFloat(formData.min_score)
      });
      
      // Move to next step
      onNext();
    } catch (error) {
      console.error('Error in Step 1:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center mr-4">
            <DocumentTextIcon className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Campaign Basics</h2>
            <p className="text-gray-600">Let's start with the fundamental information about your campaign</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Campaign Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
            Campaign Name *
          </label>
          <input
            type="text"
            id="name"
            {...register('name', { 
              required: 'Campaign name is required',
              minLength: { value: 3, message: 'Name must be at least 3 characters' },
              maxLength: { value: 255, message: 'Name must be less than 255 characters' }
            })}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
              errors.name ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Enter campaign name"
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        {/* Campaign Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            id="description"
            rows={4}
            {...register('description', {
              maxLength: { value: 2000, message: 'Description must be less than 2000 characters' }
            })}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
              errors.description ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Describe your campaign goals and objectives..."
          />
          {errors.description && (
            <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
          )}
          <p className="mt-1 text-sm text-gray-500">
            {watchedValues.description?.length || 0}/2000 characters
          </p>
        </div>

        {/* Scoring Range */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center mb-4">
            <InformationCircleIcon className="w-5 h-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Scoring Range</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Minimum Score */}
            <div>
              <label htmlFor="min_score" className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Score
              </label>
              <input
                type="number"
                id="min_score"
                step="0.1"
                {...register('min_score', { 
                  required: 'Minimum score is required',
                  min: { value: 0, message: 'Minimum score must be 0 or greater' },
                  max: { value: 100, message: 'Minimum score must be 100 or less' }
                })}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                  errors.min_score ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="0"
              />
              {errors.min_score && (
                <p className="mt-1 text-sm text-red-600">{errors.min_score.message}</p>
              )}
            </div>

            {/* Maximum Score */}
            <div>
              <label htmlFor="max_score" className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Score
              </label>
              <input
                type="number"
                id="max_score"
                step="0.1"
                {...register('max_score', { 
                  required: 'Maximum score is required',
                  min: { value: 0, message: 'Maximum score must be 0 or greater' },
                  max: { value: 1000, message: 'Maximum score must be 1000 or less' }
                })}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                  errors.max_score ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="100"
              />
              {errors.max_score && (
                <p className="mt-1 text-sm text-red-600">{errors.max_score.message}</p>
              )}
            </div>

            {/* Target Score */}
            <div>
              <label htmlFor="target_score" className="block text-sm font-medium text-gray-700 mb-2">
                Target Score (Optional)
              </label>
              <input
                type="number"
                id="target_score"
                step="0.1"
                {...register('target_score', {
                  min: { value: 0, message: 'Target score must be 0 or greater' },
                  max: { value: 1000, message: 'Target score must be 1000 or less' }
                })}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                  errors.target_score ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="75"
              />
              {errors.target_score && (
                <p className="mt-1 text-sm text-red-600">{errors.target_score.message}</p>
              )}
            </div>
          </div>

          {/* Validation for score range */}
          {watchedValues.min_score && watchedValues.max_score && 
           parseFloat(watchedValues.min_score) >= parseFloat(watchedValues.max_score) && (
            <p className="mt-2 text-sm text-red-600">
              Maximum score must be greater than minimum score
            </p>
          )}

          {watchedValues.target_score && watchedValues.min_score && watchedValues.max_score && 
           (parseFloat(watchedValues.target_score) < parseFloat(watchedValues.min_score) || 
            parseFloat(watchedValues.target_score) > parseFloat(watchedValues.max_score)) && (
            <p className="mt-2 text-sm text-red-600">
              Target score must be between minimum and maximum scores
            </p>
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-end pt-6">
          <button
            type="submit"
            disabled={!isValid || isSubmitting || 
                     (watchedValues.min_score && watchedValues.max_score && 
                      parseFloat(watchedValues.min_score) >= parseFloat(watchedValues.max_score))}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Processing...
              </>
            ) : (
              'Next: Template Selection'
            )}
          </button>
        </div>
      </form>
    </div>
  );
} 