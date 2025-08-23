import React from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import {
  BuildingOfficeIcon,
  CogIcon,
  DocumentTextIcon,
  CodeBracketIcon,
  ChartBarIcon,
  UserGroupIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';
import { healthService } from '../../services/api';

interface DashboardStats {
  lenders: number;
  apiConfigs: number;
  apiTemplates: number;
  generatedApis: number;
  apiTests: number;
  users: number;
}

interface SystemHealth {
  status: 'healthy' | 'unhealthy';
  database: 'healthy' | 'unhealthy';
  redis: 'healthy' | 'unhealthy';
  version: string;
}

const Dashboard: React.FC = () => {
  // Fetch dashboard statistics
  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>(
    'dashboard-stats',
    async () => {
      // In a real implementation, you'd have a dedicated stats endpoint
      // For now, we'll simulate the data
      return {
        lenders: 12,
        apiConfigs: 45,
        apiTemplates: 8,
        generatedApis: 23,
        apiTests: 67,
        users: 5,
      };
    }
  );

  // Fetch system health
  const { data: health, isLoading: healthLoading } = useQuery(
    'system-health',
    () => healthService.check(),
    { refetchInterval: 30000 } // Refresh every 30 seconds
  );

  const quickActions = [
    {
      name: 'Add Lender',
      href: '/lenders',
      icon: BuildingOfficeIcon,
      description: 'Configure a new lender integration',
      color: 'bg-blue-500',
    },
    {
      name: 'Create API Config',
      href: '/api-configs',
      icon: CogIcon,
      description: 'Set up API endpoint configuration',
      color: 'bg-green-500',
    },
    {
      name: 'Generate API Client',
      href: '/generated-apis',
      icon: CodeBracketIcon,
      description: 'Generate client code for a lender',
      color: 'bg-purple-500',
    },
    {
      name: 'Run API Tests',
      href: '/api-tests',
      icon: ChartBarIcon,
      description: 'Execute API integration tests',
      color: 'bg-orange-500',
    },
  ];

  const recentActivity = [
    {
      id: 1,
      type: 'api_generated',
      message: 'Generated Python client for Chase Bank API',
      timestamp: '2 hours ago',
      status: 'success',
    },
    {
      id: 2,
      type: 'lender_added',
      message: 'Added Wells Fargo as new lender',
      timestamp: '4 hours ago',
      status: 'success',
    },
    {
      id: 3,
      type: 'test_failed',
      message: 'API test failed for Bank of America endpoint',
      timestamp: '6 hours ago',
      status: 'error',
    },
    {
      id: 4,
      type: 'config_updated',
      message: 'Updated authentication config for Citi Bank',
      timestamp: '1 day ago',
      status: 'success',
    },
  ];

  if (statsLoading || healthLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Welcome to the Lender API Integration Framework
        </p>
      </div>

      {/* System Health */}
      <div className="card">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">System Health</h2>
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${
            (health?.data as SystemHealth)?.status === 'healthy' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {(health?.data as SystemHealth)?.status || 'Unknown'}
          </div>
        </div>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="text-sm">
            <span className="text-gray-500">Database:</span>
            <span className={`ml-2 ${(health?.data as SystemHealth)?.database === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
              {(health?.data as SystemHealth)?.database || 'Unknown'}
            </span>
          </div>
          <div className="text-sm">
            <span className="text-gray-500">Redis:</span>
            <span className={`ml-2 ${(health?.data as SystemHealth)?.redis === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
              {(health?.data as SystemHealth)?.redis || 'Unknown'}
            </span>
          </div>
          <div className="text-sm">
            <span className="text-gray-500">Version:</span>
            <span className="ml-2 text-gray-900">{(health?.data as SystemHealth)?.version || 'Unknown'}</span>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BuildingOfficeIcon className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Lenders</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.lenders || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CogIcon className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">API Configs</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.apiConfigs || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CodeBracketIcon className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Generated APIs</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.generatedApis || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DocumentTextIcon className="h-8 w-8 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Templates</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.apiTemplates || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-8 w-8 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">API Tests</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.apiTests || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <UserGroupIcon className="h-8 w-8 text-indigo-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Users</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.users || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              to={action.href}
              className="group relative rounded-lg border border-gray-200 p-4 hover:border-gray-300 hover:shadow-sm transition-all duration-200"
            >
              <div className="flex items-center">
                <div className={`flex-shrink-0 rounded-lg p-2 ${action.color}`}>
                  <action.icon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-900 group-hover:text-blue-600">
                    {action.name}
                  </h3>
                  <p className="text-xs text-gray-500">{action.description}</p>
                </div>
                <ArrowRightIcon className="ml-auto h-4 w-4 text-gray-400 group-hover:text-blue-600" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {recentActivity.map((activity) => (
            <div key={activity.id} className="flex items-center space-x-3">
              <div className={`flex-shrink-0 w-2 h-2 rounded-full ${
                activity.status === 'success' ? 'bg-green-400' : 'bg-red-400'
              }`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-900">{activity.message}</p>
                <p className="text-xs text-gray-500">{activity.timestamp}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
