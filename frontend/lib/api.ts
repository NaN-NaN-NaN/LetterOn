/**
 * LetterOn API Client
 *
 * Centralized API service for communicating with the backend.
 * API host is configurable via NEXT_PUBLIC_API_URL environment variable.
 *
 * Usage:
 *   import { api } from '@/lib/api';
 *   const letters = await api.letters.getAll();
 */

// Get API URL from environment variable, fallback to localhost
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Token management utilities
 */
export const TokenManager = {
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('letteron_token');
  },

  setToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem('letteron_token', token);
  },

  removeToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('letteron_token');
  },

  hasToken(): boolean {
    return !!this.getToken();
  }
};

/**
 * Base API request function with error handling
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = TokenManager.getToken();

  const headers: HeadersInit = {
    ...options.headers,
  };

  // Add auth token if available
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Add Content-Type for JSON requests (unless it's FormData)
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    // Handle non-OK responses
    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: 'Request failed',
        message: response.statusText,
      }));

      throw new Error(error.detail || error.message || `Request failed with status ${response.status}`);
    }

    // Return parsed JSON
    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

/**
 * Authentication API
 */
export const AuthAPI = {
  /**
   * Register a new user
   */
  async register(data: { name: string; email: string; password: string }) {
    const response = await apiRequest<{
      token: string;
      user: { id: string; name: string; email: string };
    }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    // Save token
    TokenManager.setToken(response.token);
    return response;
  },

  /**
   * Login user
   */
  async login(data: { email: string; password: string }) {
    const response = await apiRequest<{
      token: string;
      user: { id: string; name: string; email: string };
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    // Save token
    TokenManager.setToken(response.token);
    return response;
  },

  /**
   * Logout user
   */
  async logout() {
    try {
      await apiRequest('/auth/logout', { method: 'POST' });
    } finally {
      // Always remove token, even if request fails
      TokenManager.removeToken();
    }
  },

  /**
   * Get current user info
   */
  async getCurrentUser() {
    return apiRequest<{ id: string; name: string; email: string }>('/auth/me');
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return TokenManager.hasToken();
  }
};

/**
 * Letters API
 */
export const LettersAPI = {
  /**
   * Upload and process letter images
   */
  async processImages(files: File[], options?: {
    includeTranslation?: boolean;
    translationLanguage?: string;
  }) {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    if (options?.includeTranslation) {
      formData.append('include_translation', 'true');
    }
    if (options?.translationLanguage) {
      formData.append('translation_language', options.translationLanguage);
    }

    return apiRequest<{
      letter_id: string;
      subject: string;
      sender: string;
      content: string;
      letterCategory: string;
      actionStatus: string;
      hasReminder: boolean;
      actionDueDate?: string;
      aiSuggestion: string;
      originalImages: string[];
    }>('/letters/process-images', {
      method: 'POST',
      body: formData,
    });
  },

  /**
   * Get all letters
   */
  async getAll(params?: {
    archived?: boolean;
    deleted?: boolean;
    flagged?: boolean;
    snoozed?: boolean;
    category?: string;
    limit?: number;
  }) {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          query.set(key, String(value));
        }
      });
    }

    const queryString = query.toString();
    return apiRequest<any[]>(`/letters${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Get a single letter
   */
  async getById(letterId: string) {
    return apiRequest<any>(`/letters/${letterId}`);
  },

  /**
   * Update a letter
   */
  async update(letterId: string, updates: {
    subject?: string;
    letterCategory?: string;
    actionStatus?: string;
    hasReminder?: boolean;
    flagged?: boolean;
    read?: boolean;
    userNote?: string;
    actionDueDate?: string;
  }) {
    return apiRequest<any>(`/letters/${letterId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  /**
   * Delete a letter
   */
  async delete(letterId: string, permanent = false) {
    return apiRequest<{ message: string }>(`/letters/${letterId}?permanent=${permanent}`, {
      method: 'DELETE',
    });
  },

  /**
   * Snooze a letter
   */
  async snooze(letterId: string, snoozeUntil: string) {
    return apiRequest<any>(`/letters/${letterId}/snooze`, {
      method: 'POST',
      body: JSON.stringify({ snooze_until: snoozeUntil }),
    });
  },

  /**
   * Archive a letter
   */
  async archive(letterId: string) {
    return apiRequest<any>(`/letters/${letterId}/archive`, {
      method: 'POST',
    });
  },

  /**
   * Restore a letter
   */
  async restore(letterId: string) {
    return apiRequest<any>(`/letters/${letterId}/restore`, {
      method: 'POST',
    });
  },

  /**
   * Translate a letter
   */
  async translate(letterId: string, targetLanguage: string) {
    return apiRequest<{
      translated_content: string;
      language: string;
    }>(`/letters/${letterId}/translate`, {
      method: 'POST',
      body: JSON.stringify({ target_language: targetLanguage }),
    });
  }
};

/**
 * Chat API
 */
export const ChatAPI = {
  /**
   * Send a chat message about a letter
   */
  async sendMessage(letterId: string, message: string) {
    return apiRequest<{
      message: string;
      conversation_history: Array<{ role: string; content: string }>;
    }>('/chat', {
      method: 'POST',
      body: JSON.stringify({
        letter_id: letterId,
        message: message,
      }),
    });
  },

  /**
   * Clear conversation history for a letter
   */
  async clearHistory(letterId: string) {
    return apiRequest<{ message: string }>(`/chat/${letterId}/history`, {
      method: 'DELETE',
    });
  }
};

/**
 * Search API
 */
export const SearchAPI = {
  /**
   * Search letters
   */
  async search(query: string, limit = 20) {
    return apiRequest<{
      results: any[];
      total: number;
      query: string;
    }>(`/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  },

  /**
   * Get search suggestions
   */
  async getSuggestions(query: string, limit = 5) {
    return apiRequest<{
      query: string;
      suggestions: string[];
    }>(`/search/suggestions?q=${encodeURIComponent(query)}&limit=${limit}`);
  }
};

/**
 * Reminders API
 */
export const RemindersAPI = {
  /**
   * Create a reminder
   */
  async create(data: {
    letter_id: string;
    reminder_time: number;
    message?: string;
  }) {
    return apiRequest<{
      id: string;
      letter_id: string;
      user_id: string;
      reminder_time: number;
      message: string;
      sent: boolean;
      created_at: number;
    }>('/reminders', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get all reminders
   */
  async getAll(params?: { sent?: boolean; limit?: number }) {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          query.set(key, String(value));
        }
      });
    }

    const queryString = query.toString();
    return apiRequest<any[]>(`/reminders${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Get a single reminder
   */
  async getById(reminderId: string) {
    return apiRequest<any>(`/reminders/${reminderId}`);
  },

  /**
   * Update a reminder
   */
  async update(reminderId: string, updates: {
    reminder_time?: number;
    message?: string;
  }) {
    return apiRequest<any>(`/reminders/${reminderId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  /**
   * Delete a reminder
   */
  async delete(reminderId: string) {
    return apiRequest<{ message: string }>(`/reminders/${reminderId}`, {
      method: 'DELETE',
    });
  }
};

/**
 * Main API export - all endpoints grouped by domain
 */
export const api = {
  auth: AuthAPI,
  letters: LettersAPI,
  chat: ChatAPI,
  search: SearchAPI,
  reminders: RemindersAPI,

  // Utility
  getApiUrl: () => API_URL,
  isConfigured: () => !!API_URL,
};

// Export for convenience
export default api;
