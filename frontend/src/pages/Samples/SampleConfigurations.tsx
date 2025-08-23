import React, { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import {
  BuildingOfficeIcon,
  PlayIcon,
  PlusIcon,
  EyeIcon,
  CogIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';

interface SampleLender {
  name: string;
  description: string;
  contact_email: string;
  contact_phone: string;
  status: string;
  integration_pattern: string;
  field_mappings: any[];
  integration_sequence: any;
}

interface TestResult {
  lender_name: string;
  integration_pattern: string;
  input_data: any;
  transformed_data: any;
  api_response: any;
  sequence_result: any;
  field_mappings_used: number;
  transformation_count: number;
}

const SampleConfigurations: React.FC = () => {
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  // Fetch sample lenders
  const { data: sampleLenders, isLoading } = useQuery(
    ['sample-lenders'],
    () => apiService.get('/samples/sample-lenders'),
    {
      onError: (error) => {
        toast.error('Failed to load sample lenders');
        console.error('Error loading sample lenders:', error);
      }
    }
  );

  // Test sample lender mutation
  const testLenderMutation = useMutation(
    (lenderName: string) => apiService.post(`/samples/sample-lenders/${lenderName}/test`, {}),
    {
      onSuccess: (data) => {
        setTestResult(data.data as TestResult);
        toast.success('Sample lender test completed successfully!');
      },
      onError: (error) => {
        toast.error('Failed to test sample lender');
        console.error('Error testing lender:', error);
      }
    }
  );

  // Create sample lender mutation
  const createLenderMutation = useMutation(
    (lenderName: string) => apiService.post(`/samples/sample-lenders/${lenderName}/create`),
    {
      onSuccess: (data) => {
        toast.success('Sample lender created successfully!');
      },
      onError: (error) => {
        toast.error('Failed to create sample lender');
        console.error('Error creating lender:', error);
      }
    }
  );

  const handleTestLender = async (lenderName: string) => {
    setIsTesting(true);
    try {
      await testLenderMutation.mutateAsync(lenderName);
    } finally {
      setIsTesting(false);
    }
  };

  const handleCreateLender = async (lenderName: string) => {
    if (window.confirm(`Are you sure you want to create the sample lender "${lenderName}"?`)) {
      await createLenderMutation.mutateAsync(lenderName);
    }
  };

  const getPatternColor = (pattern: string) => {
    switch (pattern) {
      case 'simple': return 'bg-green-100 text-green-800';
      case 'complex': return 'bg-blue-100 text-blue-800';
      case 'real_time': return 'bg-purple-100 text-purple-800';
      case 'document_based': return 'bg-orange-100 text-orange-800';
      case 'instant': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPatternIcon = (pattern: string) => {
    switch (pattern) {
      case 'simple': return <CheckCircleIcon className="w-4 h-4" />;
      case 'complex': return <CogIcon className="w-4 h-4" />;
      case 'real_time': return <ArrowPathIcon className="w-4 h-4" />;
      case 'document_based': return <EyeIcon className="w-4 h-4" />;
      case 'instant': return <PlayIcon className="w-4 h-4" />;
      default: return <BuildingOfficeIcon className="w-4 h-4" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const lenders = sampleLenders?.data || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Sample Lender Configurations</h1>
            <p className="text-gray-500">
              Test and explore different integration patterns with pre-configured sample lenders
            </p>
          </div>
        </div>
      </div>

      {/* Sample Lenders Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.isArray(lenders) ? lenders.map((lender: SampleLender) => (
          <div key={lender.name} className="bg-white shadow rounded-lg overflow-hidden">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">{lender.name}</h3>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPatternColor(lender.integration_pattern)}`}>
                  {getPatternIcon(lender.integration_pattern)}
                  <span className="ml-1">{lender.integration_pattern.replace('_', ' ')}</span>
                </span>
              </div>
              
              <p className="text-sm text-gray-500 mb-4">{lender.description}</p>
              
              <div className="space-y-2 mb-4">
                <div className="flex items-center text-sm text-gray-600">
                  <BuildingOfficeIcon className="w-4 h-4 mr-2" />
                  {lender.contact_email}
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <CogIcon className="w-4 h-4 mr-2" />
                  {lender.field_mappings.length} field mappings
                </div>
                {lender.integration_sequence && (
                  <div className="flex items-center text-sm text-gray-600">
                    <ArrowPathIcon className="w-4 h-4 mr-2" />
                    {lender.integration_sequence.steps.length} integration steps
                  </div>
                )}
              </div>
              
              <div className="flex space-x-2">
                <button
                  onClick={() => handleTestLender(lender.name)}
                  disabled={isTesting}
                  className="flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {isTesting ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <PlayIcon className="w-4 h-4 mr-1" />
                  )}
                  <span>{isTesting ? 'Testing...' : 'Test'}</span>
                </button>
                <button
                  onClick={() => handleCreateLender(lender.name)}
                  className="flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium text-blue-600 bg-white border border-blue-600 rounded-md hover:bg-blue-50"
                >
                  <PlusIcon className="w-4 h-4 mr-1" />
                  <span>Create</span>
                </button>
              </div>
            </div>
          </div>
        )) : null}
      </div>

      {/* Test Results */}
      {testResult && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Test Results</h2>
            <button
              onClick={() => setTestResult(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <XCircleIcon className="w-6 h-6" />
            </button>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Lender Info */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Lender Information</h3>
              <div className="space-y-2">
                <p><span className="font-medium">Name:</span> {testResult.lender_name}</p>
                <p><span className="font-medium">Pattern:</span> {testResult.integration_pattern}</p>
                <p><span className="font-medium">Field Mappings:</span> {testResult.field_mappings_used}</p>
                <p><span className="font-medium">Transformations:</span> {testResult.transformation_count}</p>
              </div>
            </div>
            
            {/* API Response */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">API Response</h3>
              <div className="bg-gray-50 p-3 rounded border">
                <pre className="text-sm text-gray-700 overflow-x-auto">
                  {JSON.stringify(testResult.api_response, null, 2)}
                </pre>
              </div>
            </div>
          </div>
          
          {/* Input Data */}
          <div className="mt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Input Data</h3>
            <div className="bg-gray-50 p-3 rounded border">
              <pre className="text-sm text-gray-700 overflow-x-auto">
                {JSON.stringify(testResult.input_data, null, 2)}
              </pre>
            </div>
          </div>
          
          {/* Transformed Data */}
          <div className="mt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Transformed Data</h3>
            <div className="bg-gray-50 p-3 rounded border">
              <pre className="text-sm text-gray-700 overflow-x-auto">
                {JSON.stringify(testResult.transformed_data, null, 2)}
              </pre>
            </div>
          </div>
          
          {/* Sequence Result */}
          {testResult.sequence_result && (
            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Integration Sequence</h3>
              <div className="bg-gray-50 p-3 rounded border">
                <pre className="text-sm text-gray-700 overflow-x-auto">
                  {JSON.stringify(testResult.sequence_result, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Integration Patterns Info */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Integration Patterns</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center mb-2">
              <CheckCircleIcon className="w-5 h-5 text-green-600 mr-2" />
              <h3 className="font-medium text-gray-900">Simple</h3>
            </div>
            <p className="text-sm text-gray-500">Single API call with basic field mapping</p>
          </div>
          
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center mb-2">
              <CogIcon className="w-5 h-5 text-blue-600 mr-2" />
              <h3 className="font-medium text-gray-900">Complex</h3>
            </div>
            <p className="text-sm text-gray-500">Multi-step validation and submission process</p>
          </div>
          
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center mb-2">
              <ArrowPathIcon className="w-5 h-5 text-purple-600 mr-2" />
              <h3 className="font-medium text-gray-900">Real-time</h3>
            </div>
            <p className="text-sm text-gray-500">Instant approval with multiple API calls</p>
          </div>
          
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center mb-2">
              <EyeIcon className="w-5 h-5 text-orange-600 mr-2" />
              <h3 className="font-medium text-gray-900">Document-based</h3>
            </div>
            <p className="text-sm text-gray-500">Application with document upload requirements</p>
          </div>
          
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center mb-2">
              <PlayIcon className="w-5 h-5 text-red-600 mr-2" />
              <h3 className="font-medium text-gray-900">Instant</h3>
            </div>
            <p className="text-sm text-gray-500">Immediate approval with minimal data</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SampleConfigurations;
