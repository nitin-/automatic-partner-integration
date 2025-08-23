import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Link } from 'react-router-dom';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  CodeBracketIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';
import GenerateApiModal from './GenerateApiModal';

interface GeneratedApi {
  id: number;
  name: string;
  description: string;
  version: string;
  language: string;
  framework: string;
  file_path: string;
  file_size: number;
  is_valid: boolean;
  test_status: string;
  generation_time: number;
  created_at: string;
  lender: {
    id: number;
    name: string;
  };
}

interface GeneratedApisResponse {
  generated_apis: GeneratedApi[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

const GeneratedApis: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    lender_id: '',
    language: '',
    framework: '',
    is_valid: '',
    test_status: '',
  });
  const [pagination, setPagination] = useState({
    page: 1,
    size: 10,
  });
  const [showGenerateModal, setShowGenerateModal] = useState(false);

  // Fetch generated APIs
  const { data, isLoading, error } = useQuery(
    ['generated-apis', pagination, searchTerm, filters],
    () => apiService.get<GeneratedApisResponse>('/generated-apis', {
      ...pagination,
      search: searchTerm || undefined,
      ...filters,
    })
  );

  // Validate API
  const validateMutation = useMutation(
    (apiId: number) => apiService.post(`/generated-apis/${apiId}/validate`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['generated-apis']);
        toast.success('API validation completed');
      },
      onError: () => {
        toast.error('Failed to validate API');
      },
    }
  );

  // Delete API
  const deleteMutation = useMutation(
    (apiId: number) => apiService.delete(`/generated-apis/${apiId}`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['generated-apis']);
        toast.success('Generated API deleted successfully');
      },
      onError: () => {
        toast.error('Failed to delete generated API');
      },
    }
  );

  const handleValidate = (apiId: number) => {
    validateMutation.mutate(apiId);
  };

  const handleDelete = (apiId: number, apiName: string) => {
    if (window.confirm(`Are you sure you want to delete "${apiName}"?`)) {
      deleteMutation.mutate(apiId);
    }
  };

  const handleDownload = async (apiId: number, fileName: string) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/generated-apis/${apiId}/download`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success('API file downloaded successfully');
      } else {
        toast.error('Failed to download API file');
      }
    } catch (error) {
      toast.error('Failed to download API file');
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <ClockIcon className="h-4 w-4 text-yellow-500" />;
      default:
        return <ClockIcon className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'passed':
        return 'Passed';
      case 'failed':
        return 'Failed';
      case 'pending':
        return 'Pending';
      default:
        return 'Unknown';
    }
  };

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load generated APIs</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Generated APIs</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage and download generated API client code
          </p>
        </div>
        <button
          onClick={() => setShowGenerateModal(true)}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Generate API
        </button>
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
                placeholder="Search APIs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field pl-10"
              />
            </div>

            {/* Language Filter */}
            <select
              value={filters.language}
              onChange={(e) => handleFilterChange('language', e.target.value)}
              className="input-field"
            >
              <option value="">All Languages</option>
              <option value="python">Python</option>
              <option value="typescript">TypeScript</option>
              <option value="javascript">JavaScript</option>
              <option value="java">Java</option>
              <option value="csharp">C#</option>
            </select>

            {/* Status Filter */}
            <select
              value={filters.test_status}
              onChange={(e) => handleFilterChange('test_status', e.target.value)}
              className="input-field"
            >
              <option value="">All Status</option>
              <option value="passed">Passed</option>
              <option value="failed">Failed</option>
              <option value="pending">Pending</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <button type="submit" className="btn-primary">
              <FunnelIcon className="h-4 w-4 mr-2" />
              Apply Filters
            </button>
            <span className="text-sm text-gray-500">
              {data?.data?.total || 0} APIs found
            </span>
          </div>
        </form>
      </div>

      {/* Generated APIs Table */}
      <div className="card">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="loading-spinner"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="table-header">Name</th>
                  <th className="table-header">Lender</th>
                  <th className="table-header">Language</th>
                  <th className="table-header">Framework</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">File Size</th>
                  <th className="table-header">Generated</th>
                  <th className="table-header">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data?.data?.generated_apis?.map((api) => (
                  <tr key={api.id} className="hover:bg-gray-50">
                    <td className="table-cell">
                      <div>
                        <div className="font-medium text-gray-900">{api.name}</div>
                        {api.description && (
                          <div className="text-sm text-gray-500 truncate max-w-xs">
                            {api.description}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="table-cell">
                      <span className="text-sm text-gray-900">{api.lender.name}</span>
                    </td>
                    <td className="table-cell">
                      <div className="flex items-center">
                        <CodeBracketIcon className="h-4 w-4 text-gray-400 mr-2" />
                        <span className="text-sm text-gray-900 capitalize">{api.language}</span>
                      </div>
                    </td>
                    <td className="table-cell">
                      <span className="text-sm text-gray-900">{api.framework}</span>
                    </td>
                    <td className="table-cell">
                      <div className="flex items-center">
                        {getStatusIcon(api.test_status)}
                        <span className="ml-2 text-sm text-gray-900">
                          {getStatusText(api.test_status)}
                        </span>
                      </div>
                    </td>
                    <td className="table-cell">
                      <span className="text-sm text-gray-500">
                        {api.file_size ? `${(api.file_size / 1024).toFixed(1)} KB` : 'N/A'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className="text-sm text-gray-500">
                        {new Date(api.created_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="table-cell">
                      <div className="flex items-center space-x-2">
                        <Link
                          to={`/generated-apis/${api.id}`}
                          className="text-blue-600 hover:text-blue-900"
                          title="View Details"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </Link>
                        <button
                          onClick={() => handleDownload(api.id, `${api.name}.${api.language}`)}
                          className="text-green-600 hover:text-green-900"
                          title="Download"
                        >
                          <ArrowDownTrayIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleValidate(api.id)}
                          className="text-purple-600 hover:text-purple-900"
                          title="Validate"
                        >
                          <CheckCircleIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(api.id, api.name)}
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
        {data?.data?.pages && data.data.pages > 1 && (
          <div className="flex items-center justify-between mt-6">
            <div className="text-sm text-gray-500">
              Showing {((pagination.page - 1) * pagination.size) + 1} to{' '}
              {Math.min(pagination.page * pagination.size, data.data.total || 0)} of{' '}
              {data.data.total || 0} results
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
                Page {pagination.page} of {data.data.pages}
              </span>
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                disabled={pagination.page === (data.data.pages || 1)}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Generate API Modal */}
      {showGenerateModal && (
        <GenerateApiModal
          isOpen={showGenerateModal}
          onClose={() => setShowGenerateModal(false)}
          onSuccess={() => {
            setShowGenerateModal(false);
            queryClient.invalidateQueries(['generated-apis']);
            toast.success('API generation started successfully');
          }}
        />
      )}
    </div>
  );
};

export default GeneratedApis;
