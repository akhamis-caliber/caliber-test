import { useState, useEffect, useCallback } from 'react';
import { useAuthStore } from '@/store';
import { ApiResponse, UseApiOptions, UseApiResult } from '@/types';

// Generic API hook with loading, error, and data management
export function useApi<T>(
  apiCall: () => Promise<ApiResponse<T>>,
  options: UseApiOptions = {}
): UseApiResult<T> {
  const [data, setData] = useState<T | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const { enabled = true, refetchOnWindowFocus = false, retry = 3, retryDelay = 1000 } = options;

  const fetchData = useCallback(async () => {
    if (!enabled) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiCall();
      if (response.success) {
        setData(response.data);
      } else {
        throw new Error(response.message || 'API call failed');
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error occurred');
      setError(error);
      
      // Retry logic
      if (retry > 0) {
        setTimeout(() => {
          fetchData();
        }, retryDelay);
      }
    } finally {
      setLoading(false);
    }
  }, [apiCall, enabled, retry, retryDelay]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Refetch on window focus if enabled
  useEffect(() => {
    if (refetchOnWindowFocus) {
      const handleFocus = () => fetchData();
      window.addEventListener('focus', handleFocus);
      return () => window.removeEventListener('focus', handleFocus);
    }
  }, [refetchOnWindowFocus, fetchData]);

  return { data, loading, error, refetch };
}

// Hook for authenticated API calls
export function useAuthenticatedApi<T>(
  apiCall: (token: string) => Promise<ApiResponse<T>>,
  options: UseApiOptions = {}
): UseApiResult<T> {
  const { backendToken } = useAuthStore();
  
  const authenticatedApiCall = useCallback(async () => {
    if (!backendToken) {
      throw new Error('No authentication token available');
    }
    return apiCall(backendToken);
  }, [apiCall, backendToken]);

  return useApi(authenticatedApiCall, {
    ...options,
    enabled: options.enabled !== false && !!backendToken,
  });
}

// Hook for paginated API calls
export function usePaginatedApi<T>(
  apiCall: (page: number, size: number) => Promise<ApiResponse<T[]>>,
  initialPage = 1,
  initialSize = 10,
  options: UseApiOptions = {}
) {
  const [page, setPage] = useState(initialPage);
  const [size, setSize] = useState(initialSize);
  const [total, setTotal] = useState(0);
  
  const paginatedApiCall = useCallback(async () => {
    const response = await apiCall(page, size);
    if (response.success && Array.isArray(response.data)) {
      // Assuming the response includes pagination metadata
      // You might need to adjust this based on your actual API response structure
      return response;
    }
    throw new Error('Invalid paginated response');
  }, [apiCall, page, size]);

  const result = useApi(paginatedApiCall, options);

  const goToPage = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const changeSize = useCallback((newSize: number) => {
    setSize(newSize);
    setPage(1); // Reset to first page when changing size
  }, []);

  const hasNextPage = page * size < total;
  const hasPrevPage = page > 1;

  return {
    ...result,
    page,
    size,
    total,
    goToPage,
    changeSize,
    hasNextPage,
    hasPrevPage,
  };
}

// Hook for real-time data updates (WebSocket-like behavior)
export function useRealtimeApi<T>(
  apiCall: () => Promise<ApiResponse<T>>,
  interval = 5000,
  options: UseApiOptions = {}
) {
  const result = useApi(apiCall, options);

  useEffect(() => {
    if (!options.enabled) return;

    const intervalId = setInterval(() => {
      result.refetch();
    }, interval);

    return () => clearInterval(intervalId);
  }, [interval, options.enabled, result.refetch]);

  return result;
}

// Hook for optimistic updates
export function useOptimisticApi<T, U>(
  apiCall: (data: U) => Promise<ApiResponse<T>>,
  updateLocalData: (data: U) => void,
  rollbackLocalData: () => void
) {
  const [isOptimistic, setIsOptimistic] = useState(false);

  const optimisticUpdate = useCallback(async (data: U) => {
    setIsOptimistic(true);
    
    try {
      // Apply optimistic update
      updateLocalData(data);
      
      // Make actual API call
      const response = await apiCall(data);
      
      if (!response.success) {
        // Rollback on failure
        rollbackLocalData();
        throw new Error(response.message || 'API call failed');
      }
      
      return response;
    } catch (error) {
      // Rollback on error
      rollbackLocalData();
      throw error;
    } finally {
      setIsOptimistic(false);
    }
  }, [apiCall, updateLocalData, rollbackLocalData]);

  return {
    optimisticUpdate,
    isOptimistic,
  };
}

// Hook for form submission with loading state
export function useFormSubmit<T, U>(
  submitApiCall: (data: U) => Promise<ApiResponse<T>>,
  onSuccess?: (data: T) => void,
  onError?: (error: Error) => void
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const submit = useCallback(async (data: U) => {
    setLoading(true);
    setError(null);

    try {
      const response = await submitApiCall(data);
      
      if (response.success) {
        onSuccess?.(response.data);
        return { success: true, data: response.data };
      } else {
        const error = new Error(response.message || 'Submission failed');
        setError(error);
        onError?.(error);
        return { success: false, error };
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error occurred');
      setError(error);
      onError?.(error);
      return { success: false, error };
    } finally {
      setLoading(false);
    }
  }, [submitApiCall, onSuccess, onError]);

  const reset = useCallback(() => {
    setError(null);
  }, []);

  return {
    submit,
    loading,
    error,
    reset,
  };
}



