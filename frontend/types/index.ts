// Core Types
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  firebase_uid?: string;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserOrganization {
  id: number;
  user_id: number;
  organization_id: number;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

// Enums
export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  VIEWER = 'viewer'
}

export enum CampaignStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  ARCHIVED = 'archived'
}

export enum CampaignGoal {
  AWARENESS = 'awareness',
  ACTION = 'action'
}

export enum CampaignChannel {
  CTV = 'ctv',
  DISPLAY = 'display',
  VIDEO = 'video',
  AUDIO = 'audio'
}

export enum AnalysisLevel {
  DOMAIN = 'domain',
  SUPPLY_VENDOR = 'supply-vendor'
}

export enum ReportStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

// Campaign Types
export interface Campaign {
  id: number;
  name: string;
  description?: string;
  status: CampaignStatus;
  template_type: string;
  scoring_criteria?: any;
  target_score?: number;
  max_score: number;
  min_score: number;
  total_submissions: number;
  average_score?: number;
  user_id: number;
  organization_id: number;
  metadata?: CampaignMetadata;
  created_at: string;
  updated_at?: string;
}

export interface CampaignMetadata {
  goal: CampaignGoal;
  channel: CampaignChannel;
  ctr_sensitivity: boolean;
  analysis_level: AnalysisLevel;
}

export interface CampaignCreate {
  name: string;
  description?: string;
  template_id?: number;
  scoring_criteria?: ScoringCriteria[];
  target_score?: number;
  max_score: number;
  min_score?: number;
  metadata?: CampaignMetadata;
  save_as_template?: boolean;
  template_name?: string;
}

export interface CampaignUpdate {
  name?: string;
  description?: string;
  status?: CampaignStatus;
  template_id?: number;
  scoring_criteria?: ScoringCriteria[];
  target_score?: number;
  max_score?: number;
  min_score?: number;
  metadata?: CampaignMetadata;
}

// Scoring Types
export interface ScoringCriteria {
  criterion_name: string;
  description?: string;
  weight: number;
  min_score: number;
  max_score: number;
  is_required: boolean;
}

export interface ScoringResult {
  id: number;
  report_id: number;
  metric_name: string;
  metric_value: number;
  score: number;
  weight: number;
  weighted_score: number;
  explanation?: string;
  metric_metadata?: any;
  created_at: string;
}

export interface ScoringJob {
  id: number;
  report_id: number;
  campaign_id?: number;
  user_id: number;
  status: ReportStatus;
  config: any;
  results?: any;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

// Report Types
export interface Report {
  id: number;
  filename: string;
  file_path: string;
  file_size: number;
  file_type: string;
  status: ReportStatus;
  user_id: number;
  campaign_id?: number;
  organization_id: number;
  score_data?: any;
  processed_at?: string;
  created_at: string;
  updated_at?: string;
}

// Template Types
export interface Template {
  id: number;
  name: string;
  description?: string;
  user_id: number;
  organization_id: number;
  campaign_type: string;
  goal: string;
  channel: string;
  ctr_sensitivity: boolean;
  analysis_level: string;
  scoring_criteria?: any;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface TemplateCreate {
  name: string;
  description?: string;
  campaign_type: string;
  goal: CampaignGoal;
  channel: CampaignChannel;
  ctr_sensitivity: boolean;
  analysis_level: AnalysisLevel;
  scoring_criteria?: ScoringCriteria[];
  is_public: boolean;
}

// API Response Types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Auth Types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface TokenVerification {
  valid: boolean;
  user?: User;
  message?: string;
}

// Dashboard Types
export interface DashboardStats {
  total_campaigns: number;
  active_campaigns: number;
  total_reports: number;
  completed_reports: number;
  average_score: number;
  total_templates: number;
}

export interface RecentActivity {
  id: number;
  type: 'campaign_created' | 'report_uploaded' | 'scoring_completed' | 'user_login';
  description: string;
  user_id: number;
  user_name: string;
  timestamp: string;
  metadata?: any;
}

// Form Types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'select' | 'textarea' | 'number' | 'checkbox';
  required?: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
  validation?: any;
}

// UI Types
export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

// Component Props Types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface ButtonProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

export interface InputProps extends BaseComponentProps {
  label?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url';
}

// Hook Types
export interface UseApiOptions {
  enabled?: boolean;
  refetchOnWindowFocus?: boolean;
  retry?: number;
  retryDelay?: number;
}

export interface UseApiResult<T> {
  data: T | undefined;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;



