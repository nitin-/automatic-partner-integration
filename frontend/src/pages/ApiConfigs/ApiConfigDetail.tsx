import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  CogIcon,
  GlobeAltIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  PencilIcon,
  PlayIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';

interface ApiConfig {
  id: number;
  name: string;
  description: string;
  lender_name: string;
  endpoint: string;
  method: string;
  is_active: boolean;
  auth_required: boolean;
  rate_limit: number;
  timeout: number;
  created_at: string;
  updated_at: string;
}

const ApiConfigDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const { data: config, isLoading, error } = useQuery(
    ['api-config', id],
    () => apiService.get<ApiConfig>(`/api-configs/${id}`),
    { enabled: !!id }
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="bg-white shadow rounded-lg p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-3 bg-gray-200 rounded w-1/4"></div>
        </div>
      </div>
    );
  }

  if (error || !config?.data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Configuration Details</h1>
          <p className="text-gray-600">View detailed information about an API configuration</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">Failed to load API configuration. Please try again.</p>
        </div>
      </div>
    );
  }

  const configData = config.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{configData.name}</h1>
          <p className="text-gray-600">{configData.description}</p>
        </div>
        <div className="flex space-x-3">
          <button className="btn-primary">
            <PencilIcon className="h-5 w-5 mr-2" />
            Edit
          </button>
          <button className="btn-secondary">
            <PlayIcon className="h-5 w-5 mr-2" />
            Test
          </button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <CogIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Status</p>
              <div className="flex items-center">
                {configData.is_active ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                ) : (
                  <XCircleIcon className="h-5 w-5 text-red-500 mr-2" />
                )}
                <span className={`text-lg font-semibold ${
                  configData.is_active ? 'text-green-600' : 'text-red-600'
                }`}>
                  {configData.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <DocumentTextIcon className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Method</p>
              <span className="text-lg font-semibold text-gray-900">{configData.method}</span>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <GlobeAltIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Lender</p>
              <span className="text-lg font-semibold text-gray-900">{configData.lender_name}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration Details */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Configuration Details</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">Endpoint</label>
              <div className="flex items-center mt-1">
                <GlobeAltIcon className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-sm text-gray-900 font-mono">{configData.endpoint}</span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Authentication Required</label>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${
                configData.auth_required 
                  ? 'bg-red-100 text-red-800' 
                  : 'bg-green-100 text-green-800'
              }`}>
                {configData.auth_required ? 'Required' : 'Not Required'}
              </span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Rate Limit</label>
              <span className="text-sm text-gray-900">{configData.rate_limit} requests/minute</span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Timeout</label>
              <span className="text-sm text-gray-900">{configData.timeout} seconds</span>
            </div>
          </div>
        </div>

        {/* Metadata */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Metadata</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">Created</label>
              <div className="flex items-center mt-1">
                <ClockIcon className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-sm text-gray-900">
                  {new Date(configData.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Last Updated</label>
              <div className="flex items-center mt-1">
                <ClockIcon className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-sm text-gray-900">
                  {new Date(configData.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Configuration ID</label>
              <span className="text-sm text-gray-900 font-mono">#{configData.id}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors text-left">
            <PencilIcon className="h-6 w-6 text-blue-600 mr-3" />
            <div>
              <h4 className="font-medium text-gray-900">Edit Configuration</h4>
              <p className="text-sm text-gray-500">Modify settings and parameters</p>
            </div>
          </button>
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-colors text-left">
            <PlayIcon className="h-6 w-6 text-green-600 mr-3" />
            <div>
              <h4 className="font-medium text-gray-900">Test Endpoint</h4>
              <p className="text-sm text-gray-500">Verify API connectivity</p>
            </div>
          </button>
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-colors text-left">
            <DocumentTextIcon className="h-6 w-6 text-purple-600 mr-3" />
            <div>
              <h4 className="font-medium text-gray-900">View Documentation</h4>
              <p className="text-sm text-gray-500">API specifications and examples</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ApiConfigDetail;
