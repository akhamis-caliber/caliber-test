import { User } from '@/types';

// Token storage keys
const ACCESS_TOKEN_KEY = 'caliber_access_token';
const REFRESH_TOKEN_KEY = 'caliber_refresh_token';
const USER_DATA_KEY = 'caliber_user_data';

// Token expiration buffer (5 minutes before actual expiration)
const TOKEN_EXPIRATION_BUFFER = 5 * 60 * 1000;

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

class TokenService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private userData: User | null = null;
  private tokenExpiry: number | null = null;

  constructor() {
    this.loadTokensFromStorage();
  }

  // Load tokens from localStorage on initialization
  private loadTokensFromStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      this.accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
      this.refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
      
      const userDataStr = localStorage.getItem(USER_DATA_KEY);
      if (userDataStr) {
        this.userData = JSON.parse(userDataStr);
      }

      // Check if we have expiry info
      if (this.accessToken) {
        const payload = this.decodeToken(this.accessToken);
        if (payload && payload.exp) {
          this.tokenExpiry = payload.exp * 1000; // Convert to milliseconds
        }
      }
    } catch (error) {
      console.error('Error loading tokens from storage:', error);
      this.clearTokens();
    }
  }

  // Save tokens to localStorage
  private saveTokensToStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      if (this.accessToken) {
        localStorage.setItem(ACCESS_TOKEN_KEY, this.accessToken);
      }
      if (this.refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, this.refreshToken);
      }
      if (this.userData) {
        localStorage.setItem(USER_DATA_KEY, JSON.stringify(this.userData));
      }
    } catch (error) {
      console.error('Error saving tokens to storage:', error);
    }
  }

  // Decode JWT token (without verification - for client-side expiry check only)
  private decodeToken(token: string): any {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Error decoding token:', error);
      return null;
    }
  }

  // Check if token is expired or about to expire
  isTokenExpired(): boolean {
    if (!this.tokenExpiry) return true;
    
    const now = Date.now();
    return now >= (this.tokenExpiry - TOKEN_EXPIRATION_BUFFER);
  }

  // Check if token is valid
  isTokenValid(): boolean {
    return !!(this.accessToken && !this.isTokenExpired());
  }

  // Get current access token
  getAccessToken(): string | null {
    return this.accessToken;
  }

  // Get current refresh token
  getRefreshToken(): string | null {
    return this.refreshToken;
  }

  // Get current user data
  getUserData(): User | null {
    return this.userData;
  }

  // Set tokens from backend response
  setTokens(tokenResponse: TokenResponse): void {
    this.accessToken = tokenResponse.access_token;
    this.refreshToken = tokenResponse.refresh_token;
    this.userData = tokenResponse.user;

    // Calculate expiry time
    if (tokenResponse.expires_in) {
      this.tokenExpiry = Date.now() + (tokenResponse.expires_in * 1000);
    } else {
      // Fallback: decode token to get expiry
      const payload = this.decodeToken(tokenResponse.access_token);
      if (payload && payload.exp) {
        this.tokenExpiry = payload.exp * 1000;
      }
    }

    this.saveTokensToStorage();
  }

  // Update tokens after refresh
  updateTokens(refreshResponse: RefreshResponse): void {
    this.accessToken = refreshResponse.access_token;
    this.refreshToken = refreshResponse.refresh_token;

    // Calculate new expiry time
    if (refreshResponse.expires_in) {
      this.tokenExpiry = Date.now() + (refreshResponse.expires_in * 1000);
    } else {
      // Fallback: decode token to get expiry
      const payload = this.decodeToken(refreshResponse.access_token);
      if (payload && payload.exp) {
        this.tokenExpiry = payload.exp * 1000;
      }
    }

    this.saveTokensToStorage();
  }

  // Update user data
  updateUserData(userData: Partial<User>): void {
    if (this.userData) {
      this.userData = { ...this.userData, ...userData };
      this.saveTokensToStorage();
    }
  }

  // Clear all tokens and user data
  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    this.userData = null;
    this.tokenExpiry = null;

    if (typeof window !== 'undefined') {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_DATA_KEY);
    }
  }

  // Get authorization header for API requests
  getAuthHeader(): { Authorization: string } | {} {
    if (this.isTokenValid()) {
      return { Authorization: `Bearer ${this.accessToken}` };
    }
    return {};
  }

  // Check if user has specific role
  hasRole(role: string): boolean {
    return this.userData?.role === role;
  }

  // Check if user has any of the specified roles
  hasAnyRole(roles: string[]): boolean {
    return roles.includes(this.userData?.role || '');
  }

  // Check if user is admin
  isAdmin(): boolean {
    return this.hasRole('admin');
  }

  // Check if user can edit (admin or user role)
  canEdit(): boolean {
    return this.hasAnyRole(['admin', 'user']);
  }

  // Check if user can view (any authenticated user)
  canView(): boolean {
    return !!this.userData;
  }
}

// Export singleton instance
export const tokenService = new TokenService();

// Export utility functions
export const getAuthHeader = () => tokenService.getAuthHeader();
export const isTokenValid = () => tokenService.isTokenValid();
export const isTokenExpired = () => tokenService.isTokenExpired();
export const hasRole = (role: string) => tokenService.hasRole(role);
export const hasAnyRole = (roles: string[]) => tokenService.hasAnyRole(roles);
export const isAdmin = () => tokenService.isAdmin();
export const canEdit = () => tokenService.canEdit();
export const canView = () => tokenService.canView();



