import axios, { AxiosResponse } from 'axios';
import toast from 'react-hot-toast';

// API base configuration
// If REACT_APP_API_URL is not set, use relative base to leverage CRA dev proxy and avoid mixed content.
const RAW_API_BASE = process.env.REACT_APP_API_URL;
const API_BASE_URL = RAW_API_BASE ? RAW_API_BASE.replace(/\/$/, '') : '';

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error?.response?.status === 401) {
      try { localStorage.removeItem('auth_token'); } catch {}
      if (typeof window !== 'undefined') {
        // redirect to login
        window.location.href = '/login';
      }
    }
    const message = error.response?.data?.message || error.message || 'An error occurred';
    toast.error(message);
    return Promise.reject(error);
  }
);

// Generic API response type
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data: T;
  errors?: string[];
  pagination?: {
    page: number;
    size: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  timestamp: string;
}

// Pagination parameters
export interface PaginationParams {
  page?: number;
  size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// Generic API functions
export const apiService = {
  // GET request
  get: async <T>(url: string, params?: any): Promise<ApiResponse<T>> => {
    const response: AxiosResponse<ApiResponse<T>> = await api.get(url, { params });
    return response.data;
  },

  // POST request
  post: async <T>(url: string, data?: any): Promise<ApiResponse<T>> => {
    const response: AxiosResponse<ApiResponse<T>> = await api.post(url, data);
    return response.data;
  },

  // PUT request
  put: async <T>(url: string, data?: any): Promise<ApiResponse<T>> => {
    const response: AxiosResponse<ApiResponse<T>> = await api.put(url, data);
    return response.data;
  },

  // PATCH request
  patch: async <T>(url: string, data?: any): Promise<ApiResponse<T>> => {
    const response: AxiosResponse<ApiResponse<T>> = await api.patch(url, data);
    return response.data;
  },

  // DELETE request
  delete: async <T>(url: string): Promise<ApiResponse<T>> => {
    const response: AxiosResponse<ApiResponse<T>> = await api.delete(url);
    return response.data;
  },

  // File upload
  upload: async <T>(url: string, file: File, onProgress?: (progress: number) => void): Promise<ApiResponse<T>> => {
    const formData = new FormData();
    formData.append('file', file);

    const response: AxiosResponse<ApiResponse<T>> = await api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },
};

// Health check
export const healthService = {
  check: () => apiService.get('/health'),
  detailed: () => apiService.get('/health/detailed'),
};

export default apiService;
