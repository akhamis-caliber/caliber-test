import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  register: (userData) => api.post('/api/auth/register', userData),
  verifyToken: (token) => api.post('/api/auth/verify', { token }),
  getCurrentUser: () => api.get('/api/auth/me'),
};

// Campaign API
export const campaignAPI = {
  getCampaigns: () => api.get('/api/campaigns'),
  getCampaign: (id) => api.get(`/api/campaigns/${id}`),
  createCampaign: (campaignData) => api.post('/api/campaigns', campaignData),
  updateCampaign: (id, campaignData) => api.put(`/api/campaigns/${id}`, campaignData),
  deleteCampaign: (id) => api.delete(`/api/campaigns/${id}`),
  getTemplates: () => api.get('/api/campaigns/templates'),
  getCampaignStats: (id) => api.get(`/api/campaigns/${id}/stats`),
  getCampaignResults: (id) => api.get(`/api/campaigns/${id}/results`),
};

// Report API
export const reportAPI = {
  getReports: () => api.get('/api/reports'),
  getReport: (id) => api.get(`/api/reports/${id}`),
  uploadFile: (formData) => api.post('/api/reports/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  getReportStatus: (id) => api.get(`/api/reports/${id}/status`),
  downloadReport: (id) => api.get(`/api/reports/${id}/download`),
  linkReportToCampaign: (reportId, campaignId) => api.put(`/api/reports/${reportId}/link-campaign`, { campaign_id: campaignId }),
  updateReportCampaign: (reportId, campaignId) => api.put(`/api/reports/${reportId}`, { campaign_id: campaignId }),
};

// Scoring API
export const scoringAPI = {
  // Report scoring
  scoreReport: (reportId, config) => api.post(`/api/scoring/score-report/${reportId}`, { config }),
  scoreReportBackground: (reportId, config) => api.post(`/api/scoring/score-report/${reportId}`, { config, background: true }),
  
  // Scoring jobs
  getScoringJobs: (params) => api.get('/api/scoring/scoring-jobs', { params }),
  getScoringJob: (jobId) => api.get(`/api/scoring/scoring-jobs/${jobId}`),
  
  // Campaign scoring
  scoreAllCampaignReports: (campaignId, config) => api.post(`/api/campaigns/${campaignId}/score-all-reports`, { config }),
  getCampaignScoringAnalytics: (campaignId) => api.get(`/api/campaigns/${campaignId}/scoring-analytics`),
  getCampaignScoringPerformance: (campaignId) => api.get(`/api/campaigns/${campaignId}/scoring-performance`),
  getCampaignScoringHistory: (campaignId, params) => api.get(`/api/scoring/campaigns/${campaignId}/scoring-history`, { params }),
  
  // Detailed scoring results for scoring results page
  getDetailedScoringResults: (campaignId, params) => api.get(`/api/scoring/detailed-results/${campaignId}`, { params }),
  generateWhitelist: (campaignId, percentage = 25) => api.post(`/api/scoring/generate-lists/${campaignId}`, { list_type: 'whitelist', percentage }),
  generateBlacklist: (campaignId, percentage = 25) => api.post(`/api/scoring/generate-lists/${campaignId}`, { list_type: 'blacklist', percentage }),
  
  // Method comparison
  compareScoringMethods: (campaignId, methods) => api.post(`/api/scoring/campaigns/${campaignId}/compare-methods`, { methods }),
  
  // Metric analysis
  analyzeMetric: (metricName, params) => api.get(`/api/scoring/metrics/${metricName}/analysis`, { params }),
  
  // Legacy endpoints
  getResults: (reportId) => api.get(`/api/scoring/results/${reportId}`),
  getInsights: (reportId) => api.get(`/api/scoring/insights/${reportId}`),
};

// AI API
export const aiAPI = {
  generateInsights: (data) => api.post('/api/ai/insights', data),
  chat: (message) => api.post('/api/ai/chat', { message }),
};

// Dashboard API
export const dashboardAPI = {
  getStats: () => api.get('/api/dashboard/stats'),
  getRecentActivity: () => api.get('/api/dashboard/activity'),
  getScoringTrends: () => api.get('/api/dashboard/trends'),
  getQuickStats: () => api.get('/api/dashboard/quick-stats'),
};

// User API
export const userAPI = {
  getProfile: () => api.get('/api/user/profile'),
  updateProfile: (userData) => api.put('/api/user/profile', userData),
  changePassword: (passwordData) => api.put('/api/user/password', passwordData),
  getSettings: () => api.get('/api/user/settings'),
  updateSettings: (settings) => api.put('/api/user/settings', settings),
};

export default api; 