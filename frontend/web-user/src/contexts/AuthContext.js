import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../utils/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Check if user is already logged in on app start
  useEffect(() => {
    const checkAuthStatus = async () => {
      const token = localStorage.getItem('access_token');
      const userData = localStorage.getItem('user');
      
      if (token && userData) {
        try {
          // Restore user state from localStorage
          const user = JSON.parse(userData);
          setUser(user);
          setIsAuthenticated(true);
        
        } catch (error) {
          // If user data is corrupted, clear it
          localStorage.removeItem('user');
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setUser(null);
          setIsAuthenticated(false);
        }
      }
      setLoading(false);
    };

    checkAuthStatus();
  }, []);

  const validateToken = async () => {
    try {
      await api.get('/profile');
      return true;
    } catch (error) {
      if (error.response?.status === 401) {
        // Token is invalid, try to refresh
        try {
          await refreshToken();
          return true;
        } catch (refreshError) {
          // Refresh failed, clear auth data
          localStorage.removeItem('user');
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setUser(null);
          setIsAuthenticated(false);
          return false;
        }
      }
      return false;
    }
  };

  const login = async (email, password) => {
    try {
      // Clear any existing auth data before login to prevent conflicts
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      
      const response = await api.post('/auth/login', { email, password });
      
      // Check if the response contains the expected fields for successful login
      if (response.data.access_token && response.data.refresh_token && response.data.user) {
        const { access_token, refresh_token, user: userData } = response.data;
        
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        localStorage.setItem('user', JSON.stringify(userData));
        
        setUser(userData);
        setIsAuthenticated(true);
        
        return { success: true };
      } else {
        // Login failed - response doesn't contain expected fields
        return { 
          success: false, 
          error: response.data.detail || 'Login failed' 
        };
      }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await api.post('/auth/register', userData);
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        await api.post('/auth/logout', {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
      // Continue with logout even if the API call fails
    } finally {
      // Always clear local auth data
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const refreshToken = async () => {
    try {
      const refresh_token = localStorage.getItem('refresh_token');
      if (!refresh_token) {
        throw new Error('No refresh token available');
      }

      const response = await api.post('/auth/refresh', { refresh_token });
      const { access_token, refresh_token: new_refresh_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      if (new_refresh_token) {
        localStorage.setItem('refresh_token', new_refresh_token);
      }
      
      return access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Clear all auth data on refresh failure
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    }
  };

  const requestPasswordReset = async (email) => {
    try {
      const response = await api.post('/auth/request-password-reset', { email });
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Password reset request failed' 
      };
    }
  };

  const confirmPasswordReset = async (resetToken, newPassword) => {
    try {
      const response = await api.post('/auth/confirm-password-reset', {
        reset_token: resetToken,
        new_password: newPassword
      });
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Password reset confirmation failed' 
      };
    }
  };

  const clearAuthData = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    register,
    logout,
    refreshToken,
    validateToken,
    requestPasswordReset,
    confirmPasswordReset,
    clearAuthData
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 