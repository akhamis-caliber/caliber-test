import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { tokenService, TokenResponse, RefreshResponse } from './tokenService';
import { useUIStore } from '@/store';

// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const authHeader = tokenService.getAuthHeader();
    if (authHeader.Authorization) {
      config.headers.Authorization = authHeader.Authorization;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // If error is 401 and we haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Try to refresh the token
        const refreshToken = tokenService.getRefreshToken();
        if (refreshToken) {
          const refreshResponse = await axios.post<RefreshResponse>(
            `${API_BASE_URL}/auth/refresh`,
            { refresh_token: refreshToken }
          );

          // Update tokens
          tokenService.updateTokens(refreshResponse.data);

          // Retry original request with new token
          const authHeader = tokenService.getAuthHeader();
          if (authHeader.Authorization) {
            originalRequest.headers.Authorization = authHeader.Authorization;
          }
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        tokenService.clearTokens();
        if (typeof window !== 'undefined') {
          window.location.href = '/auth';
        }
      }
    }

    return Promise.reject(error);
  }
);

// API response types
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  errors?: string[];
}

export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

// Generic API functions
export const apiClient = {
  // GET request
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await api.get<ApiResponse<T>>(url, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  },

  // POST request
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await api.post<ApiResponse<T>>(url, data, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  },

  // PUT request
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await api.put<ApiResponse<T>>(url, data, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  },

  // PATCH request
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await api.patch<ApiResponse<T>>(url, data, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  },

  // DELETE request
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await api.delete<ApiResponse<T>>(url, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  },

  // Handle API errors
  handleError(error: any): Error {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;
      
      if (axiosError.response) {
        // Server responded with error status
        const status = axiosError.response.status;
        const data = axiosError.response.data as any;
        
        let message = 'An error occurred';
        
        if (data?.message) {
          message = data.message;
        } else if (data?.detail) {
          message = data.detail;
        } else if (data?.error) {
          message = data.error;
        } else {
          switch (status) {
            case 400:
              message = 'Bad request';
              break;
            case 401:
              message = 'Unauthorized';
              break;
            case 403:
              message = 'Forbidden';
              break;
            case 404:
              message = 'Not found';
              break;
            case 422:
              message = 'Validation error';
              break;
            case 500:
              message = 'Internal server error';
              break;
            default:
              message = `Error ${status}`;
          }
        }
        
        return new Error(message);
      } else if (axiosError.request) {
        // Request was made but no response received
        return new Error('No response from server. Please check your connection.');
      } else {
        // Something else happened
        return new Error(axiosError.message || 'An error occurred');
      }
    }
    
    // Non-axios error
    return error instanceof Error ? error : new Error('An unknown error occurred');
  }
};

// Authentication API functions
export const authAPI = {
  // Firebase token verification and login
  async verifyFirebaseToken(firebaseToken: string): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/firebase/verify', {
      firebase_token: firebaseToken
    });
    return response.data;
  },

  // Refresh access token
  async refreshToken(refreshToken: string): Promise<RefreshResponse> {
    const response = await apiClient.post<RefreshResponse>('/auth/refresh', {
      refresh_token: refreshToken
    });
    return response.data;
  },

  // Logout
  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      // Even if logout fails on backend, clear local tokens
      console.warn('Backend logout failed, clearing local tokens');
    } finally {
      tokenService.clearTokens();
    }
  },

  // Get current user profile
  async getProfile(): Promise<any> {
    const response = await apiClient.get('/auth/profile');
    return response.data;
  },

  // Update user profile
  async updateProfile(userData: Partial<any>): Promise<any> {
    const response = await apiClient.put('/auth/profile', userData);
    return response.data;
  }
};

// Campaign API functions
export const campaignAPI = {
  // Get campaigns with pagination
  async getCampaigns(params?: {
    page?: number;
    limit?: number;
    status?: string;
    search?: string;
  }): Promise<PaginatedResponse<any>> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.status) queryParams.append('status', params.status);
    if (params?.search) queryParams.append('search', params.search);
    
    const response = await apiClient.get<PaginatedResponse<any>>(`/campaigns?${queryParams}`);
    return response.data;
  },

  // Get single campaign
  async getCampaign(id: string): Promise<any> {
    const response = await apiClient.get<any>(`/campaigns/${id}`);
    return response.data;
  },

  // Create campaign
  async createCampaign(campaignData: any): Promise<any> {
    const response = await apiClient.post<any>('/campaigns', campaignData);
    return response.data;
  },

  // Update campaign
  async updateCampaign(id: string, campaignData: any): Promise<any> {
    const response = await apiClient.put<any>(`/campaigns/${id}`, campaignData);
    return response.data;
  },

  // Delete campaign
  async deleteCampaign(id: string): Promise<void> {
    await apiClient.delete(`/campaigns/${id}`);
  }
};

// Report API functions
export const reportAPI = {
  // Get reports with pagination
  async getReports(params?: {
    page?: number;
    limit?: number;
    campaign_id?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<PaginatedResponse<any>> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.campaign_id) queryParams.append('campaign_id', params.campaign_id);
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);
    
    const response = await apiClient.get<PaginatedResponse<any>>(`/reports?${queryParams}`);
    return response.data;
  },

  // Generate report
  async generateReport(reportData: any): Promise<any> {
    const response = await apiClient.post<any>('/reports/generate', reportData);
    return response.data;
  }
};

// Organization API functions
export const organizationAPI = {
  // Get organization info
  async getOrganization(): Promise<any> {
    const response = await apiClient.get('/organization');
    return response.data;
  },

  // Update organization
  async updateOrganization(orgData: any): Promise<any> {
    const response = await apiClient.put('/organization', orgData);
    return response.data;
  },

  // Get organization members
  async getMembers(): Promise<any[]> {
    const response = await apiClient.get<any[]>('/organization/members');
    return response.data;
  },

  // Invite member
  async inviteMember(email: string, role: string): Promise<any> {
    const response = await apiClient.post('/organization/members/invite', {
      email,
      role
    });
    return response.data;
  }
};

// Export everything
export default apiClient;
export { api, authAPI, campaignAPI, reportAPI, organizationAPI };



