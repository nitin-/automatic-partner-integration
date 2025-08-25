import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Link } from 'react-router-dom';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  PlayIcon,
  PauseIcon,
  CogIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';

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

interface LendersResponse {
  lenders: Lender[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

const Lenders: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    is_active: '',
    auth_type: '',
  });
  const [pagination, setPagination] = useState({
    page: 1,
    size: 10,
  });

  // Fetch lenders
  const { data, isLoading, error } = useQuery(
    ['lenders', pagination, searchTerm, filters],
    () => {
      const isActiveParam =
        filters.is_active === ''
          ? undefined
          : filters.is_active === 'true'
            ? true
            : filters.is_active === 'false'
              ? false
              : undefined;
      const authTypeParam = filters.auth_type || undefined;
      return apiService.get<LendersResponse>('/lenders', {
        ...pagination,
        search: searchTerm || undefined,
        is_active: isActiveParam,
        auth_type: authTypeParam,
      });
    }
  );

  // Toggle lender status
  const toggleStatusMutation = useMutation(
    (lenderId: number) => apiService.patch(`/lenders/${lenderId}/toggle-status`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['lenders']);
        toast.success('Lender status updated successfully');
      },
      onError: () => {
        toast.error('Failed to update lender status');
      },
    }
  );

  // Delete lender
  const deleteMutation = useMutation(
    (lenderId: number) => apiService.delete(`/lenders/${lenderId}`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['lenders']);
        toast.success('Lender deleted successfully');
      },
      onError: () => {
        toast.error('Failed to delete lender');
      },
    }
  );

  const handleToggleStatus = (lenderId: number) => {
    toggleStatusMutation.mutate(lenderId);
  };

  const handleDelete = (lenderId: number, lenderName: string) => {
    if (window.confirm(`Are you sure you want to delete "${lenderName}"?`)) {
      deleteMutation.mutate(lenderId);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load lenders</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Lenders</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage lender integrations and API configurations
          </p>
        </div>
        <Link
          to="/lenders/new"
          className="btn-primary flex items-center"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Add Lender
        </Link>
      </div>

      {/* Search and Filters */}
      <div className="card">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {/* Search */}
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search lenders..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field pl-10"
              />
            </div>

            {/* Status Filter */}
            <select
              value={filters.is_active}
              onChange={(e) => handleFilterChange('is_active', e.target.value)}
              className="input-field"
            >
              <option value="">All Status</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>

            {/* Auth Type Filter */}
            <select
              value={filters.auth_type}
              onChange={(e) => handleFilterChange('auth_type', e.target.value)}
              className="input-field"
            >
              <option value="">All Auth Types</option>
              <option value="bearer">Bearer Token</option>
              <option value="api_key">API Key</option>
              <option value="oauth2">OAuth2</option>
              <option value="basic">Basic Auth</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <button type="submit" className="btn-primary">
              <FunnelIcon className="h-4 w-4 mr-2" />
              Apply Filters
            </button>
            <span className="text-sm text-gray-500">
              {data?.data?.total || 0} lenders found
            </span>
          </div>
        </form>
      </div>

      {/* Lenders Table */}
      <div className="card">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="loading-spinner"></div>
          </div>
        ) : data?.data?.lenders?.length === 0 ? (
          <div className="text-center py-12">
            <div className="mx-auto h-12 w-12 text-gray-400">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No lenders found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating your first lender integration.
            </p>
            <div className="mt-6">
              <Link
                to="/lenders/new"
                className="btn-primary"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Add Your First Lender
              </Link>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="table-header">Name</th>
                  <th className="table-header">Base URL</th>
                  <th className="table-header">Auth Type</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Rate Limit</th>
                  <th className="table-header">Created</th>
                  <th className="table-header">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data?.data?.lenders?.map((lender) => (
                  <tr key={lender.id} className="hover:bg-gray-50">
                    <td className="table-cell">
                      <div>
                        <div className="font-medium text-gray-900">{lender.name}</div>
                        {lender.description && (
                          <div className="text-sm text-gray-500 truncate max-w-xs">
                            {lender.description}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="table-cell">
                      <div className="text-sm text-gray-900 truncate max-w-xs">
                        {lender.base_url}
                      </div>
                    </td>
                    <td className="table-cell">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {lender.auth_type}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        lender.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {lender.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className="text-sm text-gray-900">
                        {lender.rate_limit ? `${lender.rate_limit}/min` : 'Unlimited'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className="text-sm text-gray-500">
                        {new Date(lender.created_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="table-cell">
                      <div className="flex items-center space-x-2">
                        <Link
                          to={`/lenders/${lender.id}`}
                          className="text-blue-600 hover:text-blue-900"
                          title="View Details"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </Link>
                        <Link
                          to={`/lenders/${lender.id}/configure`}
                          className="text-green-600 hover:text-green-900"
                          title="Configure Integration"
                        >
                          <CogIcon className="h-4 w-4" />
                        </Link>
                        <Link
                          to={`/lenders/${lender.id}/edit`}
                          className="text-gray-600 hover:text-gray-900"
                          title="Edit"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </Link>
                        <button
                          onClick={() => handleToggleStatus(lender.id)}
                          className={`${
                            lender.is_active
                              ? 'text-orange-600 hover:text-orange-900'
                              : 'text-green-600 hover:text-green-900'
                          }`}
                          title={lender.is_active ? 'Deactivate' : 'Activate'}
                        >
                          {lender.is_active ? (
                            <PauseIcon className="h-4 w-4" />
                          ) : (
                            <PlayIcon className="h-4 w-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleDelete(lender.id, lender.name)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {data && data.data && data.data.pages > 1 && (
          <div className="flex items-center justify-between mt-6">
            <div className="text-sm text-gray-500">
              Showing {((pagination.page - 1) * pagination.size) + 1} to{' '}
              {Math.min(pagination.page * pagination.size, data.data.total ?? 0)} of{' '}
              {data.data.total ?? 0} results
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                disabled={pagination.page === 1}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-sm text-gray-500">
                Page {pagination.page} of {data.data.pages ?? 0}
              </span>
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                disabled={pagination.page === (data.data.pages ?? 0)}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Lenders;
