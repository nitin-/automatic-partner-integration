import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  ChartBarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowTrendingUpIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';

interface DashboardMetrics {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  avg_response_time_ms: number;
  total_leads: number;
  period_days: number;
}

interface LenderPerformance {
  lender_id: number;
  lender_name: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  avg_response_time_ms: number;
  total_leads: number;
}

interface ErrorAnalysis {
  error_type: string;
  count: number;
  examples: Array<{
    error_message: string;
    request_time: string;
    lender_name: string;
  }>;
}

interface IntegrationHealth {
  integration_id: number;
  integration_name: string;
  lender_name: string;
  health: 'healthy' | 'warning' | 'critical' | 'unknown';
  total_recent_requests: number;
  successful_recent_requests: number;
  success_rate: number;
  last_successful: string | null;
  last_failed: string | null;
  status: string;
}

interface ResponseTimeTrend {
  date: string;
  avg_response_time_ms: number;
  request_count: number;
}

const AnalyticsDashboard: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState(30);
  const [selectedLender, setSelectedLender] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'errors' | 'health' | 'trends'>('overview');

  // Fetch comprehensive analytics
  const { data: analyticsData, isLoading, error } = useQuery(
    ['analytics', selectedPeriod, selectedLender],
    () => apiService.get<{
      dashboard_metrics: DashboardMetrics;
      lender_performance: LenderPerformance[];
      error_analysis: ErrorAnalysis[];
      integration_health: IntegrationHealth[];
      response_time_trends: ResponseTimeTrend[];
    }>('/analytics/comprehensive-analytics', {
      params: {
        days: selectedPeriod,
        lender_id: selectedLender
      }
    }),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'performance', name: 'Performance', icon: ArrowTrendingUpIcon },
    { id: 'errors', name: 'Errors', icon: ExclamationTriangleIcon },
    { id: 'health', name: 'Health', icon: CheckCircleIcon },
    { id: 'trends', name: 'Trends', icon: ClockIcon },
  ];

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'healthy': return <CheckCircleIcon className="w-4 h-4" />;
      case 'warning': return <ExclamationTriangleIcon className="w-4 h-4" />;
      case 'critical': return <XCircleIcon className="w-4 h-4" />;
      default: return <EyeIcon className="w-4 h-4" />;
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  const formatPercentage = (num: number) => {
    return `${num.toFixed(1)}%`;
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <XCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Failed to load analytics</h3>
        <p className="mt-1 text-sm text-gray-500">
          Please try again later.
        </p>
      </div>
    );
  }

  const metrics = analyticsData?.data?.dashboard_metrics;
  const lenderPerformance = analyticsData?.data?.lender_performance || [];
  const errorAnalysis = analyticsData?.data?.error_analysis || [];
  const integrationHealth = analyticsData?.data?.integration_health || [];
  const responseTimeTrends = analyticsData?.data?.response_time_trends || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Integration Analytics</h1>
            <p className="text-gray-500">Monitor your lender integration performance and insights</p>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(parseInt(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={1}>Last 24 hours</option>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
            <select
              value={selectedLender || ''}
              onChange={(e) => setSelectedLender(e.target.value ? parseInt(e.target.value) : null)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Lenders</option>
              {lenderPerformance.map((lender) => (
                <option key={lender.lender_id} value={lender.lender_id}>
                  {lender.lender_name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white shadow rounded-lg">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white p-6 rounded-lg border border-gray-200">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <ChartBarIcon className="h-8 w-8 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">Total Requests</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {formatNumber(metrics?.total_requests || 0)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg border border-gray-200">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <CheckCircleIcon className="h-8 w-8 text-green-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">Success Rate</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {formatPercentage(metrics?.success_rate || 0)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg border border-gray-200">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <ClockIcon className="h-8 w-8 text-yellow-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">Avg Response Time</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {formatDuration(metrics?.avg_response_time_ms || 0)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg border border-gray-200">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <ArrowTrendingUpIcon className="h-8 w-8 text-purple-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">Total Leads</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {formatNumber(metrics?.total_leads || 0)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Top Performing Lenders */}
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Top Performing Lenders</h3>
                <div className="space-y-4">
                  {lenderPerformance.slice(0, 5).map((lender) => (
                    <div key={lender.lender_id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">{lender.lender_name}</p>
                        <p className="text-sm text-gray-500">
                          {formatNumber(lender.total_requests)} requests • {formatNumber(lender.total_leads)} leads
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-gray-900">{formatPercentage(lender.success_rate)}</p>
                        <p className="text-sm text-gray-500">{formatDuration(lender.avg_response_time_ms)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Critical Alerts */}
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Critical Alerts</h3>
                <div className="space-y-4">
                  {integrationHealth.filter(h => h.health === 'critical').slice(0, 3).map((integration) => (
                    <div key={integration.integration_id} className="flex items-center p-4 bg-red-50 border border-red-200 rounded-lg">
                      <XCircleIcon className="h-5 w-5 text-red-600 mr-3" />
                      <div>
                        <p className="font-medium text-red-900">{integration.integration_name}</p>
                        <p className="text-sm text-red-700">
                          {integration.lender_name} • {formatPercentage(integration.success_rate)} success rate
                        </p>
                      </div>
                    </div>
                  ))}
                  {integrationHealth.filter(h => h.health === 'critical').length === 0 && (
                    <p className="text-gray-500 text-center py-4">No critical alerts</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Performance Tab */}
          {activeTab === 'performance' && (
            <div className="space-y-6">
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Lender Performance</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Lender
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Requests
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Success Rate
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Avg Response Time
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Leads
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {lenderPerformance.map((lender) => (
                        <tr key={lender.lender_id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{lender.lender_name}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{formatNumber(lender.total_requests)}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{formatPercentage(lender.success_rate)}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{formatDuration(lender.avg_response_time_ms)}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{formatNumber(lender.total_leads)}</div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Errors Tab */}
          {activeTab === 'errors' && (
            <div className="space-y-6">
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Error Analysis</h3>
                <div className="space-y-4">
                  {errorAnalysis.map((error) => (
                    <div key={error.error_type} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">{error.error_type}</h4>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          {error.count} occurrences
                        </span>
                      </div>
                      <div className="space-y-2">
                        {error.examples.map((example, index) => (
                          <div key={index} className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                            <p className="font-medium">{example.lender_name}</p>
                            <p className="text-gray-500">{example.error_message}</p>
                            <p className="text-xs text-gray-400">{new Date(example.request_time).toLocaleString()}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                  {errorAnalysis.length === 0 && (
                    <p className="text-gray-500 text-center py-4">No errors found</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Health Tab */}
          {activeTab === 'health' && (
            <div className="space-y-6">
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Integration Health</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {integrationHealth.map((integration) => (
                    <div key={integration.integration_id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">{integration.integration_name}</h4>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getHealthColor(integration.health)}`}>
                          {getHealthIcon(integration.health)}
                          <span className="ml-1">{integration.health}</span>
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mb-2">{integration.lender_name}</p>
                      <div className="space-y-1 text-sm">
                        <p>Success Rate: {formatPercentage(integration.success_rate)}</p>
                        <p>Recent Requests: {integration.total_recent_requests}</p>
                        {integration.last_successful && (
                          <p>Last Success: {new Date(integration.last_successful).toLocaleString()}</p>
                        )}
                        {integration.last_failed && (
                          <p>Last Failure: {new Date(integration.last_failed).toLocaleString()}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Trends Tab */}
          {activeTab === 'trends' && (
            <div className="space-y-6">
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Response Time Trends</h3>
                <div className="space-y-4">
                  {responseTimeTrends.map((trend) => (
                    <div key={trend.date} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">{new Date(trend.date).toLocaleDateString()}</p>
                        <p className="text-sm text-gray-500">{formatNumber(trend.request_count)} requests</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-gray-900">{formatDuration(trend.avg_response_time_ms)}</p>
                        <p className="text-sm text-gray-500">avg response time</p>
                      </div>
                    </div>
                  ))}
                  {responseTimeTrends.length === 0 && (
                    <p className="text-gray-500 text-center py-4">No trend data available</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
