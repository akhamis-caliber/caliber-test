import { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { 
  ChartBarIcon, 
  PlusIcon,
  TrashIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

export default function Step3Criteria({ data, onNext, onBack, onUpdate }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [totalWeight, setTotalWeight] = useState(0);

  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors, isValid },
    setValue,
    getValues
  } = useForm({
    mode: 'onChange',
    defaultValues: {
      scoring_method: data.scoring_method || 'weighted_average',
      scoring_criteria: data.scoring_criteria || [
        {
          criterion_name: '',
          description: '',
          weight: 0.5,
          min_score: 0,
          max_score: 100,
          is_required: true
        }
      ]
    }
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "scoring_criteria"
  });

  const watchedValues = watch();

  // Calculate total weight whenever criteria change
  useEffect(() => {
    const criteria = getValues('scoring_criteria');
    if (criteria) {
      const total = criteria.reduce((sum, criterion) => sum + (criterion.weight || 0), 0);
      setTotalWeight(total);
    }
  }, [watchedValues.scoring_criteria, getValues]);

  const addCriterion = () => {
    append({
      criterion_name: '',
      description: '',
      weight: 0.5,
      min_score: 0,
      max_score: 100,
      is_required: true
    });
  };

  const removeCriterion = (index) => {
    if (fields.length > 1) {
      remove(index);
    }
  };

  const onSubmit = async (formData) => {
    setIsSubmitting(true);
    try {
      // Validate total weight
      if (Math.abs(totalWeight - 1.0) > 0.01) {
        throw new Error('Total weight must equal 100%');
      }

      // Update parent component
      onUpdate({
        ...data,
        scoring_method: formData.scoring_method,
        scoring_criteria: formData.scoring_criteria
      });

      // Move to next step
      onNext();
    } catch (error) {
      console.error('Error in Step 3:', error);
      alert(error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBack = () => {
    // Save current state before going back
    const currentValues = getValues();
    onUpdate({
      ...data,
      scoring_method: currentValues.scoring_method,
      scoring_criteria: currentValues.scoring_criteria
    });
    onBack();
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center mr-4">
            <ChartBarIcon className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Scoring Criteria Setup</h2>
            <p className="text-gray-600">Define how your campaign will be evaluated</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Scoring Method */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Scoring Method</h3>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="radio"
                value="weighted_average"
                {...register('scoring_method')}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
              />
              <span className="ml-3 text-sm font-medium text-gray-700">Weighted Average</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="simple_average"
                {...register('scoring_method')}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
              />
              <span className="ml-3 text-sm font-medium text-gray-700">Simple Average</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="custom_formula"
                {...register('scoring_method')}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
              />
              <span className="ml-3 text-sm font-medium text-gray-700">Custom Formula</span>
            </label>
          </div>
        </div>

        {/* Scoring Criteria */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Scoring Criteria</h3>
            <button
              type="button"
              onClick={addCriterion}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <PlusIcon className="w-4 h-4 mr-1" />
              Add Criterion
            </button>
          </div>

          {/* Weight Validation */}
          <div className="mb-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Total Weight:</span>
              <span className={`text-sm font-bold ${
                Math.abs(totalWeight - 1.0) <= 0.01 ? 'text-green-600' : 'text-red-600'
              }`}>
                {Math.round(totalWeight * 100)}%
              </span>
            </div>
            {Math.abs(totalWeight - 1.0) > 0.01 && (
              <div className="flex items-center mt-2 text-sm text-red-600">
                <ExclamationTriangleIcon className="w-4 h-4 mr-1" />
                Total weight must equal 100%
              </div>
            )}
          </div>

          <div className="space-y-4">
            {fields.map((field, index) => (
              <div key={field.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-md font-medium text-gray-900">Criterion {index + 1}</h4>
                  {fields.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeCriterion(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <TrashIcon className="w-5 h-5" />
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Criterion Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Criterion Name *
                    </label>
                    <input
                      type="text"
                      {...register(`scoring_criteria.${index}.criterion_name`, {
                        required: 'Criterion name is required'
                      })}
                      className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                        errors.scoring_criteria?.[index]?.criterion_name ? 'border-red-300' : 'border-gray-300'
                      }`}
                      placeholder="e.g., Engagement Rate"
                    />
                    {errors.scoring_criteria?.[index]?.criterion_name && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.scoring_criteria[index].criterion_name.message}
                      </p>
                    )}
                  </div>

                  {/* Weight */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Weight (%) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      {...register(`scoring_criteria.${index}.weight`, {
                        required: 'Weight is required',
                        min: { value: 0, message: 'Weight must be 0 or greater' },
                        max: { value: 1, message: 'Weight must be 1 or less' }
                      })}
                      className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                        errors.scoring_criteria?.[index]?.weight ? 'border-red-300' : 'border-gray-300'
                      }`}
                      placeholder="0.5"
                    />
                    {errors.scoring_criteria?.[index]?.weight && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.scoring_criteria[index].weight.message}
                      </p>
                    )}
                  </div>

                  {/* Description */}
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Description
                    </label>
                    <textarea
                      rows={2}
                      {...register(`scoring_criteria.${index}.description`)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="Describe what this criterion measures..."
                    />
                  </div>

                  {/* Score Range */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Minimum Score
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      {...register(`scoring_criteria.${index}.min_score`, {
                        required: 'Minimum score is required',
                        min: { value: 0, message: 'Minimum score must be 0 or greater' }
                      })}
                      className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                        errors.scoring_criteria?.[index]?.min_score ? 'border-red-300' : 'border-gray-300'
                      }`}
                      placeholder="0"
                    />
                    {errors.scoring_criteria?.[index]?.min_score && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.scoring_criteria[index].min_score.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Maximum Score
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      {...register(`scoring_criteria.${index}.max_score`, {
                        required: 'Maximum score is required',
                        min: { value: 0, message: 'Maximum score must be 0 or greater' }
                      })}
                      className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                        errors.scoring_criteria?.[index]?.max_score ? 'border-red-300' : 'border-gray-300'
                      }`}
                      placeholder="100"
                    />
                    {errors.scoring_criteria?.[index]?.max_score && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.scoring_criteria[index].max_score.message}
                      </p>
                    )}
                  </div>

                  {/* Required Field */}
                  <div className="md:col-span-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        {...register(`scoring_criteria.${index}.is_required`)}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">This criterion is required</span>
                    </label>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

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
            type="submit"
            disabled={!isValid || isSubmitting || Math.abs(totalWeight - 1.0) > 0.01}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Processing...
              </>
            ) : (
              'Next: Review & Create'
            )}
          </button>
        </div>
      </form>
    </div>
  );
} 