import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  BuildingOfficeIcon,
  CogIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  CloudArrowUpIcon,
  DocumentDuplicateIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import FieldMappingInterface from '../../components/FieldMapping/FieldMappingInterface';
import SequenceBuilder from '../../components/Sequences/SequenceBuilder';
import toast from 'react-hot-toast';

interface Lender {
  id: number;
  name: string;
  description: string;
  contact_email: string;
  contact_phone: string;
  status: string;
  created_at: string;
}

interface FieldMapping {
  id?: number;
  name: string;
  source_field: string;
  target_field: string;
  transformation_type: string;
  transformation_config: any;
  is_required: boolean;
  is_active: boolean;
  validation_rules?: any;
  default_value?: string;
  fallback_value?: string;
}

interface IntegrationSequence {
  id?: number;
  name: string;
  description: string;
  sequence_type: string;
  execution_mode: string;
  condition_config: any;
  stop_on_error: boolean;
  retry_failed_steps: boolean;
  is_active: boolean;
  steps: any[];
}

const LenderConfiguration: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [activeTab, setActiveTab] = useState<'overview' | 'sequences' | 'mappings' | 'deploy'>('sequences');
  const [fieldMappings, setFieldMappings] = useState<FieldMapping[]>([]);
  const [integrationSequence, setIntegrationSequence] = useState<IntegrationSequence | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [sequenceValid, setSequenceValid] = useState(true);


  // Fetch lender data with better caching and refetch options
  const { data: lender, isLoading: lenderLoading, refetch: refetchLender, error: lenderError } = useQuery(
    ['lender', id],
    () => apiService.get<Lender>(`/lenders/${id}`),
    {
      enabled: !!id,
      staleTime: 30000, // 30 seconds
      cacheTime: 300000, // 5 minutes
      refetchOnMount: true,
      refetchOnWindowFocus: false,
      retry: (failureCount: number, error: any) => {
        if (error?.response?.status === 404) return false;
        return failureCount < 3;
      },
    }
  );

  // Fetch field mappings with better caching
  const { 
    data: mappingsData, 
    isLoading: mappingsLoading,
    refetch: refetchMappings,
    error: mappingsError
  } = useQuery(
    ['field-mappings', id],
    () => apiService.get<FieldMapping[]>(`/lenders/${id}/field-mappings`),
    {
      enabled: !!id,
      staleTime: 10000, // 10 seconds
      cacheTime: 300000, // 5 minutes
      refetchOnMount: true,
      retry: (failureCount: number, error: any) => {
        if (error?.response?.status === 404) return false;
        return failureCount < 3;
      },
    }
  );

  // Fetch integration sequence with better caching
  const { 
    data: sequenceData, 
    isLoading: sequenceLoading,
    refetch: refetchSequence,
    error: sequenceError
  } = useQuery(
    ['integration-sequence', id],
    () => apiService.get<IntegrationSequence>(`/lenders/${id}/integration-sequence`),
    {
      enabled: !!id,
      staleTime: 10000, // 10 seconds
      cacheTime: 300000, // 5 minutes
      refetchOnMount: true,
      retry: (failureCount: number, error: any) => {
        if (error?.response?.status === 404) return false;
        return failureCount < 3;
      },
    }
  );

  // Save field mappings mutation with improved cache management
  const saveMappingsMutation = useMutation(
    (mappings: FieldMapping[]) => apiService.post(`/lenders/${id}/field-mappings`, { mappings }),
    {
      onSuccess: () => {
        toast.success('Field mappings saved successfully!');
        // Invalidate and refetch related queries
        queryClient.invalidateQueries(['field-mappings', id]);
        queryClient.invalidateQueries(['lender', id]);
        // Refetch to ensure UI is up to date
        refetchMappings();
        refetchLender();
      },
      onError: (error: any) => {
        toast.error('Failed to save field mappings');
        console.error('Save mappings error:', error);
      },
    }
  );

  // Save integration sequence mutation with improved cache management
  const saveSequenceMutation = useMutation(
    (sequence: IntegrationSequence) => apiService.post(`/lenders/${id}/integration-sequence`, sequence),
    {
      onSuccess: () => {
        toast.success('Integration sequence saved successfully!');
        // Invalidate and refetch related queries
        queryClient.invalidateQueries(['integration-sequence', id]);
        queryClient.invalidateQueries(['lender', id]);
        // Refetch to ensure UI is up to date
        refetchSequence();
        refetchLender();
        setIsDirty(false);
      },
      onError: (error: any) => {
        toast.error('Failed to save integration sequence');
        console.error('Save sequence error:', error);
      },
    }
  );



  // Improved useEffect for field mappings with better state synchronization
  useEffect(() => {
    if (mappingsData?.data) {
      setFieldMappings(mappingsData.data);
    }
  }, [mappingsData?.data]);

  // Improved useEffect for integration sequence with better state synchronization
  useEffect(() => {
    console.log('LenderConfiguration: sequenceData changed:', sequenceData);
    if (sequenceData?.data) {
      console.log('LenderConfiguration: Setting integrationSequence to:', sequenceData.data);
      setIntegrationSequence(sequenceData.data);
      setIsDirty(false);
    }
  }, [sequenceData?.data]);

  // Add a manual refresh function
  const handleRefresh = useCallback(async () => {
    try {
      await Promise.all([
        refetchLender(),
        refetchMappings(),
        refetchSequence()
      ]);
      toast.success('Data refreshed successfully!');
    } catch (error) {
      toast.error('Failed to refresh data');
      console.error('Refresh error:', error);
    }
  }, [refetchLender, refetchMappings, refetchSequence]);

  // Debug function to log current state
  const logCurrentState = useCallback(() => {
    console.log('=== Current State Debug ===');
    console.log('Lender:', lender?.data);
    console.log('Field Mappings:', fieldMappings);
    console.log('Integration Sequence:', integrationSequence);
    console.log('Is Dirty:', isDirty);
    console.log('Sequence Valid:', sequenceValid);
    console.log('Loading States:', { lenderLoading, mappingsLoading, sequenceLoading });
    console.log('==========================');
  }, [lender?.data, fieldMappings, integrationSequence, isDirty, sequenceValid, lenderLoading, mappingsLoading, sequenceLoading]);

  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [isDirty]);

  const handleSaveMappings = async () => {
    setIsSaving(true);
    try {
      await saveMappingsMutation.mutateAsync(fieldMappings);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveSequence = async () => {
    if (!integrationSequence) return;
    
    setIsSaving(true);
    try {
      await saveSequenceMutation.mutateAsync(integrationSequence);
      setIsDirty(false);
    } finally {
      setIsSaving(false);
    }
  };



        const DeployTab: React.FC = () => {
    const [isDeploying, setIsDeploying] = useState(false);
    const [deploymentStatus, setDeploymentStatus] = useState<string | null>(null);
    
    // Fetch deployed APIs from database
    const { 
      data: deployedApisData, 
      isLoading: deployedApisLoading,
      refetch: refetchDeployedApis,
      error: deployedApisError
    } = useQuery(
      ['deployed-apis', id],
      () => apiService.get<Array<{ 
        id: string; 
        step_name: string; 
        step_config: any;
        api_signature: any;
        status: string;
        deployed_at: string;
        last_executed_at?: string;
        execution_count: number;
        error_count: number;
      }>>(`/deployments/lender/${id}/deployed-apis`),
      {
        enabled: !!id,
        staleTime: 5000, // 5 seconds - deployments change frequently
        cacheTime: 30000, // 30 seconds
        refetchOnMount: true,
        retry: (failureCount: number, error: any) => {
          if (error?.response?.status === 404) return false;
          return failureCount < 3;
        },
      }
    );
    
    // Fetch integration deployment from database
    const { 
      data: integrationDeploymentData, 
      isLoading: integrationDeploymentLoading,
      refetch: refetchIntegrationDeployment,
      error: integrationDeploymentError
    } = useQuery(
      ['integration-deployment', id],
      () => apiService.get<{
        id: string;
        lender_id: number;
        sequence_config: any;
        field_mappings: any;
        api_signature: any;
        status: string;
        deployed_at: string;
        last_executed_at?: string;
        execution_count: number;
        error_count: number;
      }>(`/deployments/lender/${id}/integration-deployment`),
      {
        enabled: !!id,
        staleTime: 5000, // 5 seconds
        cacheTime: 30000, // 30 seconds
        refetchOnMount: true,
        retry: (failureCount: number, error: any) => {
          if (error?.response?.status === 404) return false;
          return failureCount < 3;
        },
      }
    );

    // Derived state from database queries
    const deployedApis = deployedApisData?.data || [];
    const integrationDeployment = integrationDeploymentData?.data || null;

    // Function to clear all deployment data
    const clearDeploymentData = async () => {
      try {
        // Clear integration deployment
        if (integrationDeployment) {
          await apiService.delete(`/deployments/integration/${integrationDeployment.id}`);
        }
        
        // Clear all step APIs
        for (const api of deployedApis) {
          await apiService.delete(`/deployments/step-api/${api.id}`);
        }
        
        // Refresh data from database
        refetchDeployedApis();
        refetchIntegrationDeployment();
        
        setDeploymentStatus(null);
        toast.success('All deployments cleared successfully');
      } catch (error) {
        toast.error('Failed to clear some deployments');
        console.error('Clear deployment error:', error);
      }
    };

    // Function to refresh deployment data from backend
    const refreshDeploymentData = async () => {
      try {
        // Refetch all deployment data
        await Promise.all([
          refetchDeployedApis(),
          refetchIntegrationDeployment()
        ]);
        toast.success('Deployment data refreshed from database');
      } catch (error) {
        toast.error('Failed to refresh deployment data');
        console.error('Refresh error:', error);
      }
    };

    // Function to generate comprehensive API documentation
    const generateAPIDocumentation = () => {
      let docs = `# API Documentation for ${lender?.data?.name || 'Lender'} Integration\n\n`;
      
      if (integrationDeployment?.api_signature) {
        docs += `## Main Integration Endpoint\n\n`;
        docs += `**Method:** ${integrationDeployment.api_signature.method}\n`;
        docs += `**Endpoint:** ${integrationDeployment.api_signature.endpoint}\n`;
        docs += `**Description:** ${integrationDeployment.api_signature.description}\n\n`;
        docs += `**cURL Command:**\n\`\`\`bash\n${integrationDeployment.api_signature.curl_command}\n\`\`\`\n\n`;
        docs += `**Response Format:** ${integrationDeployment.api_signature.response_format}\n`;
        docs += `**Authentication:** ${integrationDeployment.api_signature.authentication}\n\n`;
      }
      
      if (deployedApis.length > 0) {
        docs += `## Individual Step APIs\n\n`;
        deployedApis.forEach((api: any, index: number) => {
          if (api.api_signature) {
            docs += `### ${index + 1}. ${api.step_name}\n\n`;
            docs += `**Method:** ${api.api_signature.method}\n`;
            docs += `**Endpoint:** ${api.api_signature.endpoint}\n\n`;
            docs += `**cURL Command:**\n\`\`\`bash\n${api.api_signature.curl_command}\n\`\`\`\n\n`;
            
            if (Object.keys(api.api_signature.headers || {}).length > 0) {
              docs += `**Headers:**\n\`\`\`json\n${JSON.stringify(api.api_signature.headers, null, 2)}\n\`\`\`\n\n`;
            }
            
            if (Object.keys(api.api_signature.example_request || {}).length > 0) {
              docs += `**Example Request Body:**\n\`\`\`json\n${JSON.stringify(api.api_signature.example_request, null, 2)}\n\`\`\`\n\n`;
            }
            
            docs += `**Response Format:** ${api.api_signature.response_format}\n`;
            docs += `**Authentication:** ${api.api_signature.authentication}\n\n`;
            docs += `---\n\n`;
          }
        });
      }
      
      docs += `\n*Generated on ${new Date().toLocaleString()}*\n`;
      return docs;
    };

    const handleDeployIntegration = async () => {
      if (!integrationSequence || !fieldMappings.length) {
        toast.error('Please configure both field mappings and integration sequence before deploying');
        return;
      }

      setIsDeploying(true);
      setDeploymentStatus('Deploying integration sequence...');

      try {
        // Deploy the main integration sequence
        const deploymentResponse = await apiService.post<{ 
          id: string;
          endpoint_url: string;
          api_signature?: any;
        }>('/deployments/deploy-integration', {
          lender_id: parseInt(id!),
          sequence_config: integrationSequence,
          field_mappings: fieldMappings
        });

        setDeploymentStatus('Integration sequence deployed successfully!');
        toast.success('Integration sequence deployed successfully');

        // Deploy individual step APIs
        if (integrationSequence.steps && integrationSequence.steps.length > 0) {
          setDeploymentStatus('Deploying individual step APIs...');
          
          for (const step of integrationSequence.steps) {
            try {
              await apiService.post<{ id: string; name: string; endpoint_url: string }>('/deployments/deploy-step-api', {
                lender_id: parseInt(id!),
                step_config: step,
                step_name: step.name || step.step_type,
                sequence_id: deploymentResponse.data.id
              });
            } catch (error) {
              console.error(`Failed to deploy step ${step.name}:`, error);
            }
          }
          
          setDeploymentStatus(`Deployment complete! ${integrationSequence.steps.length} step APIs deployed.`);
          toast.success(`${integrationSequence.steps.length} step APIs deployed successfully`);
        }

        // Refresh data from database
        refetchDeployedApis();
        refetchIntegrationDeployment();

      } catch (error) {
        setDeploymentStatus('Deployment failed. Please check the configuration and try again.');
        toast.error('Failed to deploy integration');
        console.error('Deployment error:', error);
      } finally {
        setIsDeploying(false);
      }
    };

    const handleDeployStep = async (step: any) => {
      try {
        await apiService.post<{ id: string; name: string; endpoint_url: string }>('/deployments/deploy-step-api', {
          lender_id: parseInt(id!),
          step_config: step,
          step_name: step.name || step.step_type
        });
        
        toast.success(`Step API "${step.name || step.step_type}" deployed successfully`);
        
        // Refresh deployed APIs from database
        refetchDeployedApis();
      } catch (error) {
        toast.error(`Failed to deploy step API "${step.name || step.step_type}"`);
        console.error('Step deployment error:', error);
      }
    };

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Deploy Integration</h3>
            <p className="text-sm text-gray-500">Deploy your integration sequence as a production API with individual step endpoints</p>
          </div>
          <div className="flex items-center space-x-3">
            {/* Copy API Documentation Button */}
            {(integrationDeployment || deployedApis.length > 0) && (
              <button
                onClick={() => {
                  const apiDocs = generateAPIDocumentation();
                  navigator.clipboard.writeText(apiDocs);
                  toast.success('API documentation copied to clipboard!');
                }}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <DocumentDuplicateIcon className="w-4 h-4 mr-2" />
                Copy API Docs
              </button>
            )}
            
            {/* Refresh Deployment Data Button */}
            {(integrationDeployment || deployedApis.length > 0) && (
              <button
                onClick={refreshDeploymentData}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <ArrowPathIcon className="w-4 h-4 mr-2" />
                Refresh
              </button>
            )}
            
            {/* Clear Deployment Data Button */}
            {(integrationDeployment || deployedApis.length > 0) && (
              <button
                onClick={clearDeploymentData}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 border-red-300"
              >
                <TrashIcon className="w-4 h-4 mr-2" />
                Clear
              </button>
            )}
            
            <button
              onClick={handleDeployIntegration}
              disabled={isDeploying || !integrationSequence || !fieldMappings.length}
              className={`inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white ${
                isDeploying || !integrationSequence || !fieldMappings.length
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700'
              }`}
            >
              {isDeploying ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <CloudArrowUpIcon className="w-4 h-4 mr-2" />
              )}
              {isDeploying ? 'Deploying...' : 'Deploy Integration'}
            </button>
          </div>
        </div>

        {/* Deployment Status */}
        {deploymentStatus && (
          <div className={`p-4 rounded-lg ${
            deploymentStatus.includes('failed') || deploymentStatus.includes('error')
              ? 'bg-red-50 border border-red-200'
              : deploymentStatus.includes('complete') || deploymentStatus.includes('successfully')
              ? 'bg-green-50 border border-green-200'
              : 'bg-blue-50 border border-blue-200'
          }`}>
            <div className="flex items-center">
              {deploymentStatus.includes('failed') || deploymentStatus.includes('error') ? (
                <XCircleIcon className="h-5 w-5 text-red-400 mr-2" />
              ) : deploymentStatus.includes('complete') || deploymentStatus.includes('successfully') ? (
                <CheckCircleIcon className="h-5 w-5 text-green-400 mr-2" />
              ) : (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              )}
              <p className={`text-sm ${
                deploymentStatus.includes('failed') || deploymentStatus.includes('error')
                  ? 'text-red-800'
                  : deploymentStatus.includes('complete') || deploymentStatus.includes('successfully')
                  ? 'text-green-800'
                  : 'text-blue-800'
              }`}>
                {deploymentStatus}
              </p>
            </div>
          </div>
        )}

        {/* Persistence Status */}
        {(integrationDeployment || deployedApis.length > 0) && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <CheckCircleIcon className="h-4 w-4 text-blue-500 mr-2" />
                <p className="text-sm text-blue-800">
                  Deployment data is automatically saved and will persist across sessions
                </p>
              </div>
              <div className="flex items-center space-x-2 text-xs text-blue-600">
                <span>• {deployedApis.length} step APIs deployed</span>
                {integrationDeployment && <span>• Integration deployed</span>}
              </div>
            </div>
          </div>
        )}

        {/* Integration API Signature */}
        {integrationDeployment && integrationDeployment.api_signature && (
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="bg-blue-50 px-4 py-3 border-b border-gray-200">
              <h4 className="text-sm font-medium text-gray-900">Integration API Signature</h4>
              <p className="text-xs text-gray-600">Complete integration sequence endpoint for frontend developers</p>
            </div>
            
            <div className="p-4 bg-gray-50">
              {/* Method and Endpoint */}
              <div className="mb-4">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {integrationDeployment.api_signature.method}
                  </span>
                  <span className="text-sm font-mono text-gray-700">{integrationDeployment.api_signature.endpoint}</span>
                </div>
                <p className="text-sm text-gray-600">{integrationDeployment.api_signature.description}</p>
              </div>
              
              {/* Curl Command */}
              <div className="mb-4">
                <h6 className="text-xs font-medium text-gray-700 mb-2">cURL Command:</h6>
                <div className="bg-gray-900 text-green-400 p-3 rounded text-xs font-mono overflow-x-auto">
                  <pre className="whitespace-pre-wrap">{integrationDeployment.api_signature.curl_command}</pre>
                </div>
                <button
                  onClick={() => navigator.clipboard.writeText(integrationDeployment.api_signature!.curl_command)}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  Copy to clipboard
                </button>
              </div>
              
              {/* Additional Info */}
              <div className="flex items-center space-x-4 text-xs text-gray-600">
                <span>Response Format: {integrationDeployment.api_signature.response_format}</span>
                <span>Authentication: {integrationDeployment.api_signature.authentication}</span>
              </div>
            </div>
          </div>
        )}

        {/* Prerequisites Check */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Deployment Prerequisites</h4>
          <div className="space-y-2">
            <div className="flex items-center">
              <CheckCircleIcon className={`h-4 w-4 mr-2 ${
                fieldMappings.length > 0 ? 'text-green-500' : 'text-gray-400'
              }`} />
              <span className={`text-sm ${
                fieldMappings.length > 0 ? 'text-gray-900' : 'text-gray-500'
              }`}>
                Field Mappings: {fieldMappings.length} configured
              </span>
            </div>
            <div className="flex items-center">
              <CheckCircleIcon className={`h-4 w-4 mr-2 ${
                integrationSequence ? 'text-green-500' : 'text-gray-400'
              }`} />
              <span className={`text-sm ${
                integrationSequence ? 'text-gray-900' : 'text-gray-500'
              }`}>
                Integration Sequence: {integrationSequence ? 'Configured' : 'Not configured'}
              </span>
            </div>
          </div>
        </div>

        {/* Persistence Information */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Data Persistence</h4>
          <div className="space-y-2 text-sm text-blue-800">
            <p>✓ All deployed APIs and integration data are automatically saved to your browser's local storage</p>
            <p>✓ Data persists across browser sessions, tab refreshes, and navigation</p>
            <p>✓ Use the Clear button to remove all deployment data if needed</p>
            <p>✓ Future versions will include backend persistence for team collaboration</p>
          </div>
        </div>

        {/* Integration Sequence Overview */}
        {integrationSequence && (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Integration Sequence</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Sequence Name:</span>
                <span className="text-sm font-medium text-gray-900">{integrationSequence.name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Steps:</span>
                <span className="text-sm font-medium text-gray-900">{integrationSequence.steps?.length || 0} steps</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Execution Mode:</span>
                <span className="text-sm font-medium text-gray-900">{integrationSequence.execution_mode}</span>
              </div>
            </div>
          </div>
        )}

        {/* Individual Step Deployment */}
        {integrationSequence?.steps && integrationSequence.steps.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Individual Step APIs</h4>
            <p className="text-sm text-gray-500 mb-3">
              Each step in your integration sequence can be deployed as a standalone API endpoint
            </p>
            <div className="space-y-2">
              {integrationSequence.steps.map((step, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-blue-600">{index + 1}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {step.name || step.step_type || `Step ${index + 1}`}
                      </p>
                      <p className="text-xs text-gray-500">
                        {step.step_type} • {step.description || 'No description'}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeployStep(step)}
                    className="inline-flex items-center px-3 py-1.5 border border-blue-300 shadow-sm text-xs font-medium rounded text-blue-700 bg-blue-50 hover:bg-blue-100"
                  >
                    <CloudArrowUpIcon className="w-3 h-3 mr-1" />
                    Deploy Step
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Deployed APIs List */}
        {deployedApis.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Deployed APIs</h4>
            <div className="space-y-4">
              {deployedApis.map((api: any, index: number) => (
                <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                  {/* API Header */}
                  <div className="bg-green-50 px-4 py-3 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <CheckCircleIcon className="h-5 w-5 text-green-500" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{api.step_name}</p>
                          <p className="text-xs text-gray-500">API ID: {api.id}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Deployed
                        </span>
                        <a
                          href={api.endpoint_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 hover:text-blue-800 underline"
                        >
                          View API
                        </a>
                      </div>
                    </div>
                  </div>
                  
                  {/* API Signature Section */}
                  {api.api_signature && (
                    <div className="p-4 bg-gray-50">
                      <h5 className="text-sm font-medium text-gray-900 mb-3">API Signature for Frontend Developers</h5>
                      
                      {/* Method and Endpoint */}
                      <div className="mb-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {api.api_signature.method}
                          </span>
                          <span className="text-sm font-mono text-gray-700">{api.api_signature.endpoint}</span>
                        </div>
                      </div>
                      
                      {/* Curl Command */}
                      <div className="mb-4">
                        <h6 className="text-xs font-medium text-gray-700 mb-2">cURL Command:</h6>
                        <div className="bg-gray-900 text-green-400 p-3 rounded text-xs font-mono overflow-x-auto">
                          <pre className="whitespace-pre-wrap">{api.api_signature.curl_command}</pre>
                        </div>
                        <button
                          onClick={() => navigator.clipboard.writeText(api.api_signature!.curl_command)}
                          className="mt-2 text-xs text-blue-600 hover:text-blue-800 underline"
                        >
                          Copy to clipboard
                        </button>
                      </div>
                      
                      {/* Request Details */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Headers */}
                        {Object.keys(api.api_signature.headers || {}).length > 0 && (
                          <div>
                            <h6 className="text-xs font-medium text-gray-700 mb-2">Headers:</h6>
                            <div className="bg-white border border-gray-200 p-2 rounded text-xs">
                              <pre className="whitespace-pre-wrap">{JSON.stringify(api.api_signature.headers, null, 2)}</pre>
                            </div>
                          </div>
                        )}
                        
                        {/* Request Schema */}
                        {Object.keys(api.api_signature.example_request || {}).length > 0 && (
                          <div>
                            <h6 className="text-xs font-medium text-gray-700 mb-2">Example Request Body:</h6>
                            <div className="bg-white border border-gray-200 p-2 rounded text-xs">
                              <pre className="whitespace-pre-wrap">{JSON.stringify(api.api_signature.example_request, null, 2)}</pre>
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {/* Additional Info */}
                      <div className="flex items-center space-x-4 text-xs text-gray-600">
                        <span>Response Format: {api.api_signature.response_format}</span>
                        <span>Authentication: {api.api_signature.authentication}</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: BuildingOfficeIcon },
    { id: 'sequences', name: 'Integration Sequences', icon: ArrowPathIcon },
    { id: 'mappings', name: 'Field Mappings', icon: CogIcon },
    { id: 'deploy', name: 'Deploy', icon: CloudArrowUpIcon },
  ];

  if (lenderLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading lender configuration...</p>
        </div>
      </div>
    );
  }

  if (lenderError) {
    return (
      <div className="text-center py-8">
        <XCircleIcon className="mx-auto h-12 w-12 text-red-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading lender</h3>
        <p className="mt-1 text-sm text-gray-500">
          {lenderError?.response?.data?.message || lenderError?.message || 'Failed to load lender data'}
        </p>
        <div className="mt-6 space-x-3">
          <button
            onClick={() => refetchLender()}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <ArrowPathIcon className="w-4 h-4 mr-2" />
            Retry
          </button>
          <button
            onClick={() => navigate('/lenders')}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            Back to Lenders
          </button>
        </div>
      </div>
    );
  }

  if (!lender?.data) {
    return (
      <div className="text-center py-8">
        <XCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Lender not found</h3>
        <p className="mt-1 text-sm text-gray-500">
          The lender you're looking for doesn't exist.
        </p>
        <div className="mt-6">
          <button
            onClick={() => navigate('/lenders')}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Back to Lenders
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{lender.data.name}</h1>
            <p className="text-gray-500">{lender.data.description}</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRefresh}
              disabled={lenderLoading || mappingsLoading || sequenceLoading}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ArrowPathIcon className={`w-4 h-4 mr-2 ${(lenderLoading || mappingsLoading || sequenceLoading) ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            {process.env.NODE_ENV === 'development' && (
              <button
                onClick={logCurrentState}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-600 bg-gray-50 hover:bg-gray-100"
              >
                <CogIcon className="w-4 h-4 mr-2" />
                Debug
              </button>
            )}
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              lender.data.status === 'active' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              {lender.data.status === 'active' ? (
                <CheckCircleIcon className="w-4 h-4 mr-1" />
              ) : (
                <XCircleIcon className="w-4 h-4 mr-1" />
              )}
              {lender.data.status}
            </span>
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
          {(() => {
            if (activeTab === 'overview') {
              return (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Lender Information</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Contact Email</label>
                        <p className="mt-1 text-sm text-gray-900">{lender.data.contact_email}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Contact Phone</label>
                        <p className="mt-1 text-sm text-gray-900">{lender.data.contact_phone}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Created</label>
                        <p className="mt-1 text-sm text-gray-900">
                          {new Date(lender.data.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Integration Status</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <CogIcon className="h-6 w-6 text-gray-400" />
                          </div>
                          <div className="ml-3">
                            <p className="text-sm font-medium text-gray-900">Field Mappings</p>
                            <p className="text-sm text-gray-500">
                              {fieldMappings.length} mappings configured
                            </p>
                          </div>
                        </div>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <ArrowPathIcon className="h-6 w-6 text-gray-400" />
                          </div>
                          <div className="ml-3">
                            <p className="text-sm font-medium text-gray-900">Integration Sequence</p>
                            <p className="text-sm text-gray-500">
                              {integrationSequence ? 'Configured' : 'Not configured'}
                            </p>
                          </div>
                        </div>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <CloudArrowUpIcon className="h-6 w-6 text-gray-400" />
                          </div>
                          <div className="ml-3">
                            <p className="text-sm font-medium text-gray-900">Ready for Deployment</p>
                            <p className="text-sm text-gray-500">
                              {fieldMappings.length > 0 && integrationSequence ? 'Ready' : 'Configure mappings and sequence first'}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            } else if (activeTab === 'sequences') {
              return (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">Integration Sequence</h3>
                      <p className="text-sm text-gray-500">Configure multi-step API integration sequence</p>
                    </div>
                    <div className="flex items-center space-x-3">
                      {sequenceLoading && (
                        <div className="flex items-center text-sm text-gray-500">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                          Loading...
                        </div>
                      )}
                      <button
                        onClick={handleSaveSequence}
                        disabled={isSaving || !integrationSequence || !sequenceValid || sequenceLoading}
                        className={`flex items-center space-x-1 px-4 py-2 text-sm font-medium text-white border border-transparent rounded-md ${isSaving || !integrationSequence || !sequenceValid || sequenceLoading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}
                      >
                        {isSaving ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        ) : (
                          <CheckCircleIcon className="w-4 h-4" />
                        )}
                        <span>{isSaving ? 'Saving...' : 'Save Sequence'}</span>
                      </button>
                    </div>
                  </div>

                  {sequenceLoading ? (
                    <div className="flex items-center justify-center h-32">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
                        <p className="text-gray-500">Loading integration sequence...</p>
                      </div>
                    </div>
                  ) : sequenceError ? (
                    <div className="text-center py-8">
                      <XCircleIcon className="mx-auto h-12 w-12 text-red-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading sequence</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        {sequenceError?.response?.data?.message || sequenceError?.message || 'Failed to load integration sequence'}
                      </p>
                      <button
                        onClick={() => refetchSequence()}
                        className="mt-4 inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                      >
                        <ArrowPathIcon className="w-4 h-4 mr-2" />
                        Retry
                      </button>
                    </div>
                  ) : (
                    <div>
                      <SequenceBuilder
                        lenderId={parseInt(id!)}
                        onSequenceChange={(seq) => { setIntegrationSequence(seq); setIsDirty(true); }}
                        initialSequence={sequenceData?.data || integrationSequence || undefined}
                        onValidityChange={(ok) => setSequenceValid(ok)}
                      />
                    </div>
                  )}
                </div>
              );
            } else if (activeTab === 'mappings') {
              return (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">Field Mappings</h3>
                      <p className="text-sm text-gray-500">Configure how your fields map to lender fields with transformations</p>
                    </div>
                    <div className="flex items-center space-x-3">
                      {mappingsLoading && (
                        <div className="flex items-center text-sm text-gray-500">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                          Loading...
                        </div>
                      )}
                      <button
                        onClick={handleSaveMappings}
                        disabled={isSaving || mappingsLoading}
                        className="flex items-center space-x-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50"
                      >
                        {isSaving ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        ) : (
                          <CheckCircleIcon className="w-4 h-4" />
                        )}
                        <span>{isSaving ? 'Saving...' : 'Save Mappings'}</span>
                      </button>
                    </div>
                  </div>

                  {mappingsLoading ? (
                    <div className="flex items-center justify-center h-32">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
                        <p className="text-gray-500">Loading field mappings...</p>
                      </div>
                    </div>
                  ) : mappingsError ? (
                    <div className="text-center py-8">
                      <XCircleIcon className="mx-auto h-12 w-12 text-red-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading mappings</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        {mappingsError?.response?.data?.message || mappingsError?.message || 'Failed to load field mappings'}
                      </p>
                      <button
                        onClick={() => refetchMappings()}
                        className="mt-4 inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                      >
                        <ArrowPathIcon className="w-4 h-4 mr-2" />
                        Retry
                      </button>
                    </div>
                  ) : (
                    <FieldMappingInterface
                      lenderId={parseInt(id!)}
                      onMappingChange={setFieldMappings}
                      initialMappings={fieldMappings}
                    />
                  )}
                </div>
              );
            } else if (activeTab === 'deploy') {
              return <DeployTab />;
            }
            return null;
          })()}
        </div>
      </div>
    </div>
  );
};

export default LenderConfiguration;
