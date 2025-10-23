/**
 * Token Storage Utilities
 *
 * Provides secure token storage with expiration tracking.
 * Uses localStorage with key "access_token".
 *
 * Security features:
 * - Automatic token expiration (12 hours)
 * - Token validation before use
 * - Stored in localStorage as requested
 */

interface TokenData {
  token: string;
  expiresAt: number;
}

const TOKEN_KEY = 'access_token';
const TOKEN_EXPIRY_HOURS = 12;

export class TokenStorage {
  /**
   * Save token with expiration time
   * Always uses localStorage with key "access_token"
   */
  static setToken(token: string, rememberMe: boolean = true): void {
    if (typeof window === 'undefined') return;

    // Calculate expiration time (12 hours from now)
    const expiresAt = Date.now() + (TOKEN_EXPIRY_HOURS * 60 * 60 * 1000);

    const tokenData: TokenData = {
      token,
      expiresAt
    };

    // Store token in localStorage as requested
    localStorage.setItem(TOKEN_KEY, JSON.stringify(tokenData));

    console.log('[TokenStorage] Token saved to localStorage, expires:', new Date(expiresAt).toISOString());
  }

  /**
   * Get token (returns null if expired)
   * Reads from localStorage with key "access_token"
   */
  static getToken(): string | null {
    if (typeof window === 'undefined') return null;

    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) return null;

    try {
      const tokenData: TokenData = JSON.parse(stored);

      // Check if token is expired
      if (Date.now() >= tokenData.expiresAt) {
        console.log('[TokenStorage] Token expired, removing...');
        this.removeToken();
        return null;
      }

      return tokenData.token;
    } catch (error) {
      console.error('[TokenStorage] Error parsing token:', error);
      this.removeToken();
      return null;
    }
  }

  /**
   * Remove token from localStorage
   */
  static removeToken(): void {
    if (typeof window === 'undefined') return;

    localStorage.removeItem(TOKEN_KEY);
    console.log('[TokenStorage] Token removed from localStorage');
  }

  /**
   * Check if token exists and is valid
   */
  static hasValidToken(): boolean {
    return this.getToken() !== null;
  }

  /**
   * Get token expiration time
   */
  static getTokenExpiration(): Date | null {
    if (typeof window === 'undefined') return null;

    const stored =
      sessionStorage.getItem(TOKEN_KEY) ||
      localStorage.getItem(TOKEN_KEY);

    if (!stored) return null;

    try {
      const tokenData: TokenData = JSON.parse(stored);
      return new Date(tokenData.expiresAt);
    } catch {
      return null;
    }
  }

  /**
   * Get time until token expires (in milliseconds)
   */
  static getTimeUntilExpiry(): number | null {
    const expiration = this.getTokenExpiration();
    if (!expiration) return null;

    return Math.max(0, expiration.getTime() - Date.now());
  }

  /**
   * Check if token will expire soon (within 1 hour)
   */
  static isTokenExpiringSoon(): boolean {
    const timeUntilExpiry = this.getTimeUntilExpiry();
    if (timeUntilExpiry === null) return false;

    const ONE_HOUR_MS = 60 * 60 * 1000;
    return timeUntilExpiry < ONE_HOUR_MS;
  }
}

// Export for backwards compatibility
export const TokenManager = {
  getToken: () => TokenStorage.getToken(),
  setToken: (token: string, rememberMe?: boolean) => TokenStorage.setToken(token, rememberMe),
  removeToken: () => TokenStorage.removeToken(),
  hasToken: () => TokenStorage.hasValidToken(),
};
