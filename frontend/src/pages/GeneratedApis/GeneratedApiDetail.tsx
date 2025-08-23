import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  CodeBracketIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  PencilIcon,
  DocumentTextIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';

interface GeneratedApi {
  id: number;
  name: string;
  description: string;
  lender_name: string;
  language: string;
  framework: string;
  version: string;
  status: 'generating' | 'completed' | 'failed';
  download_url: string;
  created_at: string;
  updated_at: string;
}

const GeneratedApiDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const { data: api, isLoading, error } = useQuery(
    ['generated-api', id],
    () => apiService.get<GeneratedApi>(`/generated-apis/${id}`),
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

  if (error || !api?.data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Generated API Details</h1>
          <p className="text-gray-600">View detailed information about a generated API</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">Failed to load generated API. Please try again.</p>
        </div>
      </div>
    );
  }

  const apiData = api.data;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'generating':
        return <ClockIcon className="h-5 w-5 text-blue-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'generating':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{apiData.name}</h1>
          <p className="text-gray-600">{apiData.description}</p>
        </div>
        <div className="flex space-x-3">
          {apiData.status === 'completed' && (
            <a
              href={apiData.download_url}
              download
              className="btn-primary"
            >
              <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
              Download
            </a>
          )}
          <button className="btn-secondary">
            <PencilIcon className="h-5 w-5 mr-2" />
            Regenerate
          </button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <CodeBracketIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Status</p>
              <div className="flex items-center">
                {getStatusIcon(apiData.status)}
                <span className={`ml-2 text-lg font-semibold ${getStatusColor(apiData.status).replace('bg-', 'text-').replace('-100', '-600')}`}>
                  {apiData.status.charAt(0).toUpperCase() + apiData.status.slice(1)}
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
              <p className="text-sm font-medium text-gray-500">Language</p>
              <span className="text-lg font-semibold text-gray-900">{apiData.language}</span>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <CodeBracketIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Framework</p>
              <span className="text-lg font-semibold text-gray-900">{apiData.framework}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API Details */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">API Details</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">Lender</label>
              <span className="text-sm text-gray-900">{apiData.lender_name}</span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Version</label>
              <span className="text-sm text-gray-900">v{apiData.version}</span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Status</label>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${getStatusColor(apiData.status)}`}>
                {apiData.status.charAt(0).toUpperCase() + apiData.status.slice(1)}
              </span>
            </div>
            
            {apiData.download_url && (
              <div>
                <label className="block text-sm font-medium text-gray-500">Download URL</label>
                <a 
                  href={apiData.download_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:text-blue-800 break-all"
                >
                  {apiData.download_url}
                </a>
              </div>
            )}
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
                  {new Date(apiData.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Last Updated</label>
              <div className="flex items-center mt-1">
                <ClockIcon className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-sm text-gray-900">
                  {new Date(apiData.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">API ID</label>
              <span className="text-sm text-gray-900 font-mono">#{apiData.id}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {apiData.status === 'completed' && (
            <a
              href={apiData.download_url}
              download
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-colors text-left"
            >
              <ArrowDownTrayIcon className="h-6 w-6 text-green-600 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Download API</h4>
                <p className="text-sm text-gray-500">Get the generated code files</p>
              </div>
            </a>
          )}
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors text-left">
            <PencilIcon className="h-6 w-6 text-blue-600 mr-3" />
            <div>
              <h4 className="font-medium text-gray-900">Regenerate API</h4>
              <p className="text-sm text-gray-500">Create a new version</p>
            </div>
          </button>
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-colors text-left">
            <DocumentTextIcon className="h-6 w-6 text-purple-600 mr-3" />
            <div>
              <h4 className="font-medium text-gray-900">View Documentation</h4>
              <p className="text-sm text-gray-500">Usage examples and guides</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default GeneratedApiDetail;
