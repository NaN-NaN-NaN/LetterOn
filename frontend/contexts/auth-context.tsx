"use client"

/**
 * Authentication Context
 *
 * Provides authentication state and methods throughout the app.
 * Automatically checks for existing token on mount.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, TokenManager } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  // Check for existing session on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = useCallback(async () => {
    try {
      if (TokenManager.hasToken()) {
        const userData = await api.auth.getCurrentUser();
        setUser(userData);
      }
    } catch (error) {
      // Token is invalid, remove it
      TokenManager.removeToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const response = await api.auth.login({ email, password });
      setUser(response.user);
      toast({
        title: "Welcome back!",
        description: `Logged in as ${response.user.email}`,
      });
    } catch (error) {
      toast({
        title: "Login failed",
        description: error instanceof Error ? error.message : "Invalid credentials",
        variant: "destructive",
      });
      throw error;
    }
  }, [toast]);

  const register = useCallback(async (name: string, email: string, password: string) => {
    try {
      const response = await api.auth.register({ name, email, password });
      setUser(response.user);
      toast({
        title: "Account created!",
        description: `Welcome, ${response.user.name}!`,
      });
    } catch (error) {
      toast({
        title: "Registration failed",
        description: error instanceof Error ? error.message : "Unable to create account",
        variant: "destructive",
      });
      throw error;
    }
  }, [toast]);

  const logout = useCallback(async () => {
    try {
      await api.auth.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      toast({
        title: "Logged out",
        description: "You have been logged out successfully.",
      });
    }
  }, [toast]);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await api.auth.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      setUser(null);
      TokenManager.removeToken();
    }
  }, []);

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
