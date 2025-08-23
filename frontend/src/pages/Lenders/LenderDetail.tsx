import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  BuildingOfficeIcon,
  CogIcon,
  GlobeAltIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  PencilIcon,
  PlayIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';

interface Lender {
  id: number;
  name: string;
  description: string;
  base_url: string;
  api_version: string;
  auth_type: string;
  is_active: boolean;
  is_verified: boolean;
  rate_limit: number;
  timeout: number;
  contact_email: string;
  support_url: string;
  created_at: string;
  updated_at: string;
}

const LenderDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const { data: lender, isLoading, error } = useQuery(
    ['lender', id],
    () => apiService.get<Lender>(`/lenders/${id}`),
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

  if (error || !lender?.data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Lender Details</h1>
          <p className="text-gray-600">View detailed information about a lender</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">Failed to load lender details. Please try again.</p>
        </div>
      </div>
    );
  }

  const lenderData = lender.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{lenderData.name}</h1>
          <p className="text-gray-600">{lenderData.description}</p>
        </div>
        <div className="flex space-x-3">
          <Link
            to={`/lenders/${id}/configure`}
            className="btn-primary"
          >
            <CogIcon className="h-5 w-5 mr-2" />
            Configure
          </Link>
          <button className="btn-secondary">
            <PencilIcon className="h-5 w-5 mr-2" />
            Edit
          </button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <BuildingOfficeIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Status</p>
              <div className="flex items-center">
                {lenderData.is_active ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                ) : (
                  <XCircleIcon className="h-5 w-5 text-red-500 mr-2" />
                )}
                <span className={`text-lg font-semibold ${
                  lenderData.is_active ? 'text-green-600' : 'text-red-600'
                }`}>
                  {lenderData.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Verification</p>
              <div className="flex items-center">
                {lenderData.is_verified ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                ) : (
                  <XCircleIcon className="h-5 w-5 text-red-500 mr-2" />
                )}
                <span className={`text-lg font-semibold ${
                  lenderData.is_verified ? 'text-green-600' : 'text-red-600'
                }`}>
                  {lenderData.is_verified ? 'Verified' : 'Unverified'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <PlayIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">API Version</p>
              <span className="text-lg font-semibold text-gray-900">v{lenderData.api_version}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Basic Information */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">Base URL</label>
              <div className="flex items-center mt-1">
                <GlobeAltIcon className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-sm text-gray-900 font-mono">{lenderData.base_url}</span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Authentication Type</label>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mt-1">
                {lenderData.auth_type}
              </span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Rate Limit</label>
              <span className="text-sm text-gray-900">{lenderData.rate_limit} requests/minute</span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Timeout</label>
              <span className="text-sm text-gray-900">{lenderData.timeout} seconds</span>
            </div>
          </div>
        </div>

        {/* Contact & Support */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Contact & Support</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">Contact Email</label>
              <span className="text-sm text-gray-900">{lenderData.contact_email}</span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Support URL</label>
              <a 
                href={lenderData.support_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                {lenderData.support_url}
              </a>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Created</label>
              <div className="flex items-center mt-1">
                <ClockIcon className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-sm text-gray-900">
                  {new Date(lenderData.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Last Updated</label>
              <div className="flex items-center mt-1">
                <ClockIcon className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-sm text-gray-900">
                  {new Date(lenderData.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to={`/lenders/${id}/configure`}
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
          >
            <CogIcon className="h-6 w-6 text-blue-600 mr-3" />
            <div>
              <h4 className="font-medium text-gray-900">Configure Integration</h4>
              <p className="text-sm text-gray-500">Set up field mappings and sequences</p>
            </div>
          </Link>
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-colors text-left">
            <PlayIcon className="h-6 w-6 text-green-600 mr-3" />
            <div>
              <h4 className="font-medium text-gray-900">Test Connection</h4>
              <p className="text-sm text-gray-500">Verify API connectivity</p>
            </div>
          </button>
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-colors text-left">
            <BuildingOfficeIcon className="h-6 w-6 text-purple-600 mr-3" />
            <div>
              <h4 className="font-medium text-gray-900">Generate Client</h4>
              <p className="text-sm text-gray-500">Create API client code</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default LenderDetail;
