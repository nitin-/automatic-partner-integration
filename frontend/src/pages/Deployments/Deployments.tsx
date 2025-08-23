import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  CloudArrowUpIcon,
  DocumentArrowDownIcon,
  TrashIcon,
  CogIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';

interface DeploymentTemplate {
  type: string;
  name: string;
  description: string;
  features: string[];
}

interface GeneratedApi {
  id: number;
  name: string;
  language: string;
  framework: string;
  lender: {
    id: number;
    name: string;
  };
}

const Deployments: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedApi, setSelectedApi] = useState<number | null>(null);
  const [deploymentType, setDeploymentType] = useState('docker');
  const [showGenerateModal, setShowGenerateModal] = useState(false);

  // Fetch deployment templates
  const { data: templatesData } = useQuery(
    'deployment-templates',
    () => apiService.get<{ templates: DeploymentTemplate[] }>('/deployments/deployment-templates')
  );

  // Fetch generated APIs
  const { data: apisData } = useQuery(
    'generated-apis',
    () => apiService.get<{ generated_apis: GeneratedApi[] }>('/generated-apis', { size: 100 })
  );

  // Generate deployment package
  const generateDeploymentMutation = useMutation(
    (data: { generated_api_id: number; deployment_type: string; config?: any }) =>
      apiService.post('/deployments/generate-deployment', data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['deployment-status']);
        toast.success('Deployment package generated successfully');
        setShowGenerateModal(false);
      },
      onError: () => {
        toast.error('Failed to generate deployment package');
      },
    }
  );

  // Download deployment package
  const downloadDeployment = async (apiId: number, type: string) => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/deployments/download-deployment/${apiId}?deployment_type=${type}`
      );
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `deployment_${apiId}_${type}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success('Deployment package downloaded successfully');
      } else {
        toast.error('Failed to download deployment package');
      }
    } catch (error) {
      toast.error('Failed to download deployment package');
    }
  };

  // Cleanup deployment files
  const cleanupMutation = useMutation(
    (data: { generated_api_id: number; deployment_type?: string }) => {
      const url = data.deployment_type 
        ? `/deployments/cleanup-deployment/${data.generated_api_id}?deployment_type=${data.deployment_type}`
        : `/deployments/cleanup-deployment/${data.generated_api_id}`;
      return apiService.delete(url);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['deployment-status']);
        toast.success('Deployment files cleaned up successfully');
      },
      onError: () => {
        toast.error('Failed to cleanup deployment files');
      },
    }
  );

  const handleGenerateDeployment = (apiId: number, type: string) => {
    generateDeploymentMutation.mutate({
      generated_api_id: apiId,
      deployment_type: type,
    });
  };

  const handleCleanup = (apiId: number, type?: string) => {
    if (window.confirm('Are you sure you want to cleanup deployment files?')) {
      cleanupMutation.mutate({ generated_api_id: apiId, deployment_type: type });
    }
  };

  const getStatusIcon = (available: boolean) => {
    if (available) {
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
    }
    return <XCircleIcon className="h-5 w-5 text-red-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Deployments</h1>
          <p className="mt-1 text-sm text-gray-500">
            Generate and manage deployment packages for your API clients
          </p>
        </div>
        <button
          onClick={() => setShowGenerateModal(true)}
          className="btn-primary flex items-center"
        >
          <CloudArrowUpIcon className="h-4 w-4 mr-2" />
          Generate Deployment
        </button>
      </div>

      {/* Deployment Templates */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Available Deployment Types</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {templatesData?.data?.templates?.map((template) => (
            <div
              key={template.type}
              className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-gray-900">{template.name}</h3>
                <CogIcon className="h-5 w-5 text-gray-400" />
              </div>
              <p className="text-sm text-gray-500 mb-3">{template.description}</p>
              <ul className="text-xs text-gray-600 space-y-1">
                {template.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <CheckCircleIcon className="h-3 w-3 text-green-500 mr-1" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Generated APIs with Deployment Status */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">API Deployment Status</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="table-header">API Name</th>
                <th className="table-header">Language</th>
                <th className="table-header">Framework</th>
                <th className="table-header">Docker</th>
                <th className="table-header">Kubernetes</th>
                <th className="table-header">Helm Chart</th>
                <th className="table-header">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {apisData?.data?.generated_apis?.map((api) => (
                <tr key={api.id} className="hover:bg-gray-50">
                  <td className="table-cell">
                    <div>
                      <div className="font-medium text-gray-900">{api.name}</div>
                      <div className="text-sm text-gray-500">{api.lender.name}</div>
                    </div>
                  </td>
                  <td className="table-cell">
                    <span className="text-sm text-gray-900 capitalize">{api.language}</span>
                  </td>
                  <td className="table-cell">
                    <span className="text-sm text-gray-900">{api.framework}</span>
                  </td>
                  <td className="table-cell">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(true)} {/* Placeholder - would fetch actual status */}
                      <button
                        onClick={() => downloadDeployment(api.id, 'docker')}
                        className="text-blue-600 hover:text-blue-900"
                        title="Download Docker deployment"
                      >
                        <DocumentArrowDownIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                  <td className="table-cell">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(false)} {/* Placeholder - would fetch actual status */}
                      <button
                        onClick={() => handleGenerateDeployment(api.id, 'kubernetes')}
                        className="text-green-600 hover:text-green-900"
                        title="Generate Kubernetes deployment"
                      >
                        <CloudArrowUpIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                  <td className="table-cell">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(false)} {/* Placeholder - would fetch actual status */}
                      <button
                        onClick={() => handleGenerateDeployment(api.id, 'helm')}
                        className="text-purple-600 hover:text-purple-900"
                        title="Generate Helm chart"
                      >
                        <CloudArrowUpIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                  <td className="table-cell">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleCleanup(api.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Cleanup all deployment files"
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
      </div>

      {/* Generate Deployment Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div
              className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
              onClick={() => setShowGenerateModal(false)}
            />

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    Generate Deployment Package
                  </h3>
                  <button
                    onClick={() => setShowGenerateModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XCircleIcon className="h-6 w-6" />
                  </button>
                </div>

                <form className="space-y-4">
                  {/* API Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Select API *
                    </label>
                    <select
                      value={selectedApi || ''}
                      onChange={(e) => setSelectedApi(Number(e.target.value))}
                      className="input-field"
                      required
                    >
                      <option value="">Choose an API...</option>
                      {apisData?.data?.generated_apis?.map((api) => (
                        <option key={api.id} value={api.id}>
                          {api.name} ({api.language}/{api.framework})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Deployment Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Deployment Type *
                    </label>
                    <select
                      value={deploymentType}
                      onChange={(e) => setDeploymentType(e.target.value)}
                      className="input-field"
                      required
                    >
                      {templatesData?.data?.templates?.map((template) => (
                        <option key={template.type} value={template.type}>
                          {template.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setShowGenerateModal(false)}
                      className="btn-secondary"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        if (selectedApi) {
                          handleGenerateDeployment(selectedApi, deploymentType);
                        }
                      }}
                      disabled={generateDeploymentMutation.isLoading || !selectedApi}
                      className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {generateDeploymentMutation.isLoading ? (
                        <>
                          <div className="loading-spinner mr-2"></div>
                          Generating...
                        </>
                      ) : (
                        'Generate'
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Deployments;
