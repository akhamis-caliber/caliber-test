import { api } from './api';

export interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: 'success' | 'info' | 'warning' | 'error';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  read: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationTemplate {
  id: number;
  name: string;
  title_template: string;
  message_template: string;
  type: 'success' | 'info' | 'warning' | 'error';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  is_active: boolean;
  created_at: string;
}

export interface NotificationStats {
  total_notifications: number;
  unread_count: number;
  read_count: number;
  notifications_by_type: Record<string, number>;
  notifications_by_priority: Record<string, number>;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
  page: number;
  per_page: number;
}

export interface CreateNotificationData {
  title: string;
  message: string;
  type?: 'success' | 'info' | 'warning' | 'error';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  template_name?: string;
  template_data?: Record<string, any>;
}

export interface BulkNotificationData {
  user_ids: number[];
  template_name: string;
  template_data?: Record<string, any>;
  type?: 'success' | 'info' | 'warning' | 'error';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
}

class NotificationService {
  private baseUrl = '/api/notifications';

  /**
   * Get user notifications with pagination
   */
  async getNotifications(
    page: number = 1,
    perPage: number = 20,
    unreadOnly: boolean = false,
    type?: string
  ): Promise<NotificationListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      unread_only: unreadOnly.toString(),
    });

    if (type) {
      params.append('notification_type', type);
    }

    const response = await api.get(`${this.baseUrl}/?${params.toString()}`);
    return response.data;
  }

  /**
   * Get notification statistics for the current user
   */
  async getNotificationStats(): Promise<NotificationStats> {
    const response = await api.get(`${this.baseUrl}/stats`);
    return response.data;
  }

  /**
   * Mark a notification as read
   */
  async markAsRead(notificationId: number): Promise<{ message: string }> {
    const response = await api.put(`${this.baseUrl}/${notificationId}/read`);
    return response.data;
  }

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<{ message: string }> {
    const response = await api.put(`${this.baseUrl}/read-all`);
    return response.data;
  }

  /**
   * Delete a notification
   */
  async deleteNotification(notificationId: number): Promise<{ message: string }> {
    const response = await api.delete(`${this.baseUrl}/${notificationId}`);
    return response.data;
  }

  /**
   * Create a new notification (admin only)
   */
  async createNotification(data: CreateNotificationData): Promise<Notification> {
    const response = await api.post(this.baseUrl, data);
    return response.data;
  }

  /**
   * Create bulk notifications (admin only)
   */
  async createBulkNotifications(data: BulkNotificationData): Promise<Notification[]> {
    const response = await api.post(`${this.baseUrl}/bulk`, data);
    return response.data;
  }

  /**
   * Get all notification templates
   */
  async getTemplates(): Promise<NotificationTemplate[]> {
    const response = await api.get(`${this.baseUrl}/templates`);
    return response.data;
  }

  /**
   * Create a new notification template (admin only)
   */
  async createTemplate(data: Omit<NotificationTemplate, 'id' | 'created_at'>): Promise<NotificationTemplate> {
    const response = await api.post(`${this.baseUrl}/templates`, data);
    return response.data;
  }

  /**
   * Update a notification template (admin only)
   */
  async updateTemplate(
    templateId: number,
    data: Partial<Omit<NotificationTemplate, 'id' | 'created_at'>>
  ): Promise<NotificationTemplate> {
    const response = await api.put(`${this.baseUrl}/templates/${templateId}`, data);
    return response.data;
  }

  /**
   * Delete a notification template (admin only)
   */
  async deleteTemplate(templateId: number): Promise<{ message: string }> {
    const response = await api.delete(`${this.baseUrl}/templates/${templateId}`);
    return response.data;
  }

  /**
   * System notification methods (admin only)
   */
  async notifyCampaignCompleted(userId: number, campaignName: string): Promise<{ message: string; notification: Notification }> {
    const response = await api.post(`${this.baseUrl}/system/campaign-completed`, {
      user_id: userId,
      campaign_name: campaignName,
    });
    return response.data;
  }

  async notifyDataUploadWarning(userId: number, filename: string, issues: string[]): Promise<{ message: string; notification: Notification }> {
    const response = await api.post(`${this.baseUrl}/system/data-upload-warning`, {
      user_id: userId,
      filename,
      issues,
    });
    return response.data;
  }

  async notifyScoringCompleted(userId: number, campaignName: string, score: number): Promise<{ message: string; notification: Notification }> {
    const response = await api.post(`${this.baseUrl}/system/scoring-completed`, {
      user_id: userId,
      campaign_name: campaignName,
      score,
    });
    return response.data;
  }

  async notifySystemMaintenance(userIds: number[], maintenanceTime: string): Promise<{ message: string; notifications: Notification[] }> {
    const response = await api.post(`${this.baseUrl}/system/maintenance`, {
      user_ids: userIds,
      maintenance_time: maintenanceTime,
    });
    return response.data;
  }

  /**
   * Utility method to format timestamp for display
   */
  formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) {
      return 'Just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 2592000) {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  }

  /**
   * Get notification icon based on type
   */
  getNotificationIcon(type: string): string {
    switch (type) {
      case 'success':
        return '✅';
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      case 'info':
      default:
        return 'ℹ️';
    }
  }

  /**
   * Get priority color class
   */
  getPriorityColorClass(priority: string): string {
    switch (priority) {
      case 'urgent':
        return 'text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400';
      case 'high':
        return 'text-orange-600 bg-orange-100 dark:bg-orange-900/20 dark:text-orange-400';
      case 'medium':
        return 'text-blue-600 bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400';
      case 'low':
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-300';
    }
  }
}

export const notificationService = new NotificationService();
export default notificationService;
