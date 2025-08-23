import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  PlayIcon,
  EyeIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';

interface ApiTest {
  id: number;
  name: string;
  description: string;
  lender_name: string;
  endpoint: string;
  method: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  last_run: string;
  success_rate: number;
  avg_response_time: number;
  created_at: string;
}

const ApiTests: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    lender: '',
  });

  // Fetch API tests
  const { data, isLoading, error } = useQuery(
    ['api-tests', searchTerm, filters],
    () => apiService.get<{ tests: ApiTest[] }>('/api-tests', {
      search: searchTerm || undefined,
      ...filters,
    })
  );

  // Run test
  const runTestMutation = useMutation(
    (testId: number) => apiService.post(`/api-tests/${testId}/run`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['api-tests']);
        toast.success('Test started successfully');
      },
      onError: () => {
        toast.error('Failed to start test');
      },
    }
  );

  // Delete test
  const deleteMutation = useMutation(
    (testId: number) => apiService.delete(`/api-tests/${testId}`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['api-tests']);
        toast.success('Test deleted successfully');
      },
      onError: () => {
        toast.error('Failed to delete test');
      },
    }
  );

  const handleRunTest = (testId: number) => {
    runTestMutation.mutate(testId);
  };

  const handleDelete = (testId: number, testName: string) => {
    if (window.confirm(`Are you sure you want to delete "${testName}"?`)) {
      deleteMutation.mutate(testId);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'running':
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
      case 'running':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-white shadow rounded-lg p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Tests</h1>
          <p className="text-gray-600">Manage and run your API integration tests</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">Failed to load API tests. Please try again.</p>
        </div>
      </div>
    );
  }

  const tests = data?.data?.tests || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Tests</h1>
          <p className="text-gray-600">Manage and run your API integration tests</p>
        </div>
        <button className="btn-primary">
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Test
        </button>
      </div>

      {/* Search and Filters */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search tests..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
            <select
              value={filters.lender}
              onChange={(e) => setFilters(prev => ({ ...prev, lender: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Lenders</option>
              <option value="chase">Chase Bank</option>
              <option value="wells-fargo">Wells Fargo</option>
              <option value="bank-of-america">Bank of America</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tests List */}
      <div className="space-y-4">
        {tests.map((test) => (
          <div key={test.id} className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <div className="mr-4">
                  {getStatusIcon(test.status)}
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900">{test.name}</h3>
                  <p className="text-sm text-gray-500">{test.description}</p>
                </div>
              </div>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(test.status)}`}>
                {test.status.charAt(0).toUpperCase() + test.status.slice(1)}
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div>
                <span className="text-sm text-gray-500">Lender:</span>
                <p className="text-sm font-medium text-gray-900">{test.lender_name}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Endpoint:</span>
                <p className="text-sm font-medium text-gray-900">{test.method} {test.endpoint}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Success Rate:</span>
                <p className="text-sm font-medium text-gray-900">{test.success_rate}%</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Avg Response:</span>
                <p className="text-sm font-medium text-gray-900">{test.avg_response_time}ms</p>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Last run: {new Date(test.last_run).toLocaleDateString()}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleRunTest(test.id)}
                  disabled={test.status === 'running'}
                  className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <PlayIcon className="h-4 w-4 mr-2" />
                  {test.status === 'running' ? 'Running...' : 'Run Test'}
                </button>
                <button className="btn-secondary">
                  <EyeIcon className="h-4 w-4 mr-2" />
                  View Results
                </button>
                <button
                  onClick={() => handleDelete(test.id, test.name)}
                  className="btn-secondary text-red-600 hover:text-red-700"
                >
                  <TrashIcon className="h-4 w-4 mr-2" />
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {tests.length === 0 && (
        <div className="text-center py-12">
          <PlayIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No tests found</h3>
          <p className="text-gray-500">Get started by creating your first API test.</p>
        </div>
      )}
    </div>
  );
};

export default ApiTests;
