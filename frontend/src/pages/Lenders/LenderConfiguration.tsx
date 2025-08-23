import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  BuildingOfficeIcon,
  CogIcon,
  ArrowPathIcon,
  PlayIcon,
  CheckCircleIcon,
  XCircleIcon,
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
  
  const [activeTab, setActiveTab] = useState<'overview' | 'sequences' | 'mappings' | 'testing'>('sequences');
  const [fieldMappings, setFieldMappings] = useState<FieldMapping[]>([]);
  const [integrationSequence, setIntegrationSequence] = useState<IntegrationSequence | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [sequenceValid, setSequenceValid] = useState(true);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

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
      onError: (error) => {
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
      onError: (error) => {
        toast.error('Failed to save integration sequence');
        console.error('Save sequence error:', error);
      },
    }
  );

  // Test integration mutation with improved cache management
  const testIntegrationMutation = useMutation(
    (testData: any) => apiService.post(`/lenders/${id}/test-integration`, testData),
    {
      onSuccess: (data) => {
        toast.success('Integration test completed successfully!');
        const runId = (data?.data && (data as any).data?.run_id) || (data as any)?.data?.run_id;
        if (runId) setSelectedRunId(runId);
        // Invalidate and refetch all related queries
        queryClient.invalidateQueries(['runs', id]);
        queryClient.invalidateQueries(['run', id, runId]);
        queryClient.invalidateQueries(['lender', id]);
        // Refetch to ensure UI is up to date
        refetchLender();
      },
      onError: (error) => {
        toast.error('Integration test failed');
        console.error('Test error:', error);
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
    if (sequenceData?.data) {
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

  const handleTestIntegration = async () => {
    const testData = {
      full_name: 'John Doe',
      email: 'john@example.com',
      phone: '+1-555-123-4567',
      date_of_birth: '1990-01-15',
      address: {
        street: '123 Main St',
        city: 'New York',
        state: 'NY',
        zip_code: '10001'
      },
      loan_amount: '50000',
      loan_type: 'personal',
      employment_status: 'employed',
      annual_income: '75000'
    };

    await testIntegrationMutation.mutateAsync(testData);
  };

  const TestingTab: React.FC = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Run Sample Test</h3>
        <button
          onClick={handleTestIntegration}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          <PlayIcon className="w-4 h-4 mr-2" /> Run Test
        </button>
      </div>
      <p className="text-sm text-gray-500">This sends a sample payload to the integration test endpoint.</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Recent Runs</h4>
          {/* runs list (omitted for brevity) */}
        </div>
        <div className="md:col-span-2">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Run Details</h4>
          {/* run details (omitted for brevity) */}
        </div>
      </div>
    </div>
  );

  const tabs = [
    { id: 'overview', name: 'Overview', icon: BuildingOfficeIcon },
    { id: 'sequences', name: 'Integration Sequences', icon: ArrowPathIcon },
    { id: 'mappings', name: 'Field Mappings', icon: CogIcon },
    { id: 'testing', name: 'Testing', icon: PlayIcon },
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
                            <PlayIcon className="h-6 w-6 text-gray-400" />
                          </div>
                          <div className="ml-3">
                            <p className="text-sm font-medium text-gray-900">Ready for Testing</p>
                            <p className="text-sm text-gray-500">
                              {fieldMappings.length > 0 ? 'Ready' : 'Configure mappings first'}
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
                    <SequenceBuilder
                      lenderId={parseInt(id!)}
                      onSequenceChange={(seq) => { setIntegrationSequence(seq); setIsDirty(true); }}
                      initialSequence={integrationSequence || undefined}
                      onValidityChange={(ok) => setSequenceValid(ok)}
                    />
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
            } else if (activeTab === 'testing') {
              return <TestingTab />;
            }
            return null;
          })()}
        </div>
      </div>
    </div>
  );
};

export default LenderConfiguration;
