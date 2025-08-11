import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { User, Campaign, Report, Template, Toast } from '@/types';

// Auth Store
interface AuthState {
  user: User | null;
  backendToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  
  // Actions
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  logout: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        backendToken: null,
        isAuthenticated: false,
        loading: false,
        error: null,
        
        setUser: (user) => set((state) => ({
          user,
          isAuthenticated: !!user,
          error: null
        })),
        
        setToken: (token) => set((state) => ({
          backendToken: token,
          isAuthenticated: !!token
        })),
        
        setLoading: (loading) => set({ loading }),
        
        setError: (error) => set({ error }),
        
        logout: () => set({
          user: null,
          backendToken: null,
          isAuthenticated: false,
          error: null
        }),
        
        clearError: () => set({ error: null }),
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          user: state.user,
          backendToken: state.backendToken,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    )
  )
);

// Campaign Store
interface CampaignState {
  campaigns: Campaign[];
  currentCampaign: Campaign | null;
  templates: Template[];
  loading: boolean;
  error: string | null;
  
  // Actions
  setCampaigns: (campaigns: Campaign[]) => void;
  addCampaign: (campaign: Campaign) => void;
  updateCampaign: (id: number, updates: Partial<Campaign>) => void;
  deleteCampaign: (id: number) => void;
  setCurrentCampaign: (campaign: Campaign | null) => void;
  setTemplates: (templates: Template[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useCampaignStore = create<CampaignState>()(
  devtools(
    (set, get) => ({
      campaigns: [],
      currentCampaign: null,
      templates: [],
      loading: false,
      error: null,
      
      setCampaigns: (campaigns) => set({ campaigns }),
      
      addCampaign: (campaign) => set((state) => ({
        campaigns: [...state.campaigns, campaign]
      })),
      
      updateCampaign: (id, updates) => set((state) => ({
        campaigns: state.campaigns.map(campaign =>
          campaign.id === id ? { ...campaign, ...updates } : campaign
        ),
        currentCampaign: state.currentCampaign?.id === id 
          ? { ...state.currentCampaign, ...updates }
          : state.currentCampaign
      })),
      
      deleteCampaign: (id) => set((state) => ({
        campaigns: state.campaigns.filter(campaign => campaign.id !== id),
        currentCampaign: state.currentCampaign?.id === id ? null : state.currentCampaign
      })),
      
      setCurrentCampaign: (campaign) => set({ currentCampaign: campaign }),
      
      setTemplates: (templates) => set({ templates }),
      
      setLoading: (loading) => set({ loading }),
      
      setError: (error) => set({ error }),
      
      clearError: () => set({ error: null }),
    })
  )
);

// Report Store
interface ReportState {
  reports: Report[];
  currentReport: Report | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  setReports: (reports: Report[]) => void;
  addReport: (report: Report) => void;
  updateReport: (id: number, updates: Partial<Report>) => void;
  deleteReport: (id: number) => void;
  setCurrentReport: (report: Report | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useReportStore = create<ReportState>()(
  devtools(
    (set) => ({
      reports: [],
      currentReport: null,
      loading: false,
      error: null,
      
      setReports: (reports) => set({ reports }),
      
      addReport: (report) => set((state) => ({
        reports: [...state.reports, report]
      })),
      
      updateReport: (id, updates) => set((state) => ({
        reports: state.reports.map(report =>
          report.id === id ? { ...report, ...updates } : report
        ),
        currentReport: state.currentReport?.id === id 
          ? { ...state.currentReport, ...updates }
          : state.currentReport
      })),
      
      deleteReport: (id) => set((state) => ({
        reports: state.reports.filter(report => report.id !== id),
        currentReport: state.currentReport?.id === id ? null : state.currentReport
      })),
      
      setCurrentReport: (report) => set({ currentReport: report }),
      
      setLoading: (loading) => set({ loading }),
      
      setError: (error) => set({ error }),
      
      clearError: () => set({ error: null }),
    })
  )
);

// UI Store
interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toasts: Toast[];
  
  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleTheme: () => void;
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set, get) => ({
        sidebarOpen: false,
        theme: 'light',
        toasts: [],
        
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
        
        setSidebarOpen: (open) => set({ sidebarOpen: open }),
        
        toggleTheme: () => set((state) => ({ 
          theme: state.theme === 'light' ? 'dark' : 'light' 
        })),
        
        addToast: (toast) => {
          const id = Math.random().toString(36).substr(2, 9);
          const newToast = { ...toast, id };
          
          set((state) => ({ toasts: [...state.toasts, newToast] }));
          
          // Auto-remove toast after duration or default 5 seconds
          setTimeout(() => {
            get().removeToast(id);
          }, toast.duration || 5000);
        },
        
        removeToast: (id) => set((state) => ({
          toasts: state.toasts.filter(toast => toast.id !== id)
        })),
        
        clearToasts: () => set({ toasts: [] }),
      }),
      {
        name: 'ui-storage',
        partialize: (state) => ({
          theme: state.theme,
        }),
      }
    )
  )
);

// Organization Store
interface OrganizationState {
  currentOrganization: Organization | null;
  userOrganizations: UserOrganization[];
  loading: boolean;
  error: string | null;
  
  // Actions
  setCurrentOrganization: (org: Organization | null) => void;
  setUserOrganizations: (orgs: UserOrganization[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useOrganizationStore = create<OrganizationState>()(
  devtools(
    (set) => ({
      currentOrganization: null,
      userOrganizations: [],
      loading: false,
      error: null,
      
      setCurrentOrganization: (org) => set({ currentOrganization: org }),
      
      setUserOrganizations: (orgs) => set({ userOrganizations: orgs }),
      
      setLoading: (loading) => set({ loading }),
      
      setError: (error) => set({ error }),
      
      clearError: () => set({ error: null }),
    })
  )
);

// Root Store (combines all stores for easy access)
export const useRootStore = () => ({
  auth: useAuthStore(),
  campaign: useCampaignStore(),
  report: useReportStore(),
  ui: useUIStore(),
  organization: useOrganizationStore(),
});



