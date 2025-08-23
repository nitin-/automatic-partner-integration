import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ArrowsRightLeftIcon,
  CogIcon,
  PlusIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';

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

interface ApiResponseField {
  field: string;
  count: number;
  frequency: number;
}

interface FieldMappingInterfaceProps {
  lenderId: number;
  onMappingChange: (mappings: FieldMapping[]) => void;
  initialMappings?: FieldMapping[];
}

const FieldMappingInterface: React.FC<FieldMappingInterfaceProps> = ({
  lenderId,
  onMappingChange,
  initialMappings = []
}) => {
  const [mappings, setMappings] = useState<FieldMapping[]>(initialMappings);
  const [sourceFields, setSourceFields] = useState<string[]>([]);
  const [targetFields, setTargetFields] = useState<ApiResponseField[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [sampleData, setSampleData] = useState<string>('{}');
  const [lastResult, setLastResult] = useState<any>(null);
  const [loadingTargetFields, setLoadingTargetFields] = useState(false);
  const [targetFieldsError, setTargetFieldsError] = useState<string | null>(null);

  // Sample source fields (your standard fields)
  const sampleSourceFields = useMemo(() => [
    'full_name',
    'email',
    'phone',
    'date_of_birth',
    'address',
    'city',
    'state',
    'zip_code',
    'loan_amount',
    'loan_type',
    'employment_status',
    'annual_income',
    'ssn',
    'bank_account',
    'routing_number'
  ], []);

  // Load target fields from actual API responses
  const loadTargetFieldsFromApiResponses = useCallback(async () => {
    try {
      setLoadingTargetFields(true);
      setTargetFieldsError(null);
      
      const response = await apiService.get<{
        fields: ApiResponseField[];
        total_responses: number;
        unique_fields_count: number;
      }>(`/lenders/${lenderId}/api-response-fields`);
      
      if (response.data?.fields) {
        setTargetFields(response.data.fields);
        toast.success(`Loaded ${response.data.fields.length} fields from ${response.data.total_responses} API responses`);
      } else {
        setTargetFields([]);
        toast('No API response data found. Run some integrations first to populate target fields.', { icon: 'ℹ️' });
      }
    } catch (error: any) {
      console.error('Failed to load target fields:', error);
      setTargetFieldsError(error.response?.data?.message || 'Failed to load target fields from API responses');
      toast.error('Failed to load target fields from API responses');
      
      // Fallback to sample fields if API call fails
      setTargetFields([
        { field: 'customer_name', count: 1, frequency: 100 },
        { field: 'email_address', count: 1, frequency: 100 },
        { field: 'mobile_number', count: 1, frequency: 100 },
        { field: 'birth_date', count: 1, frequency: 100 },
        { field: 'residential_address', count: 1, frequency: 100 },
        { field: 'city_name', count: 1, frequency: 100 },
        { field: 'state_code', count: 1, frequency: 100 },
        { field: 'postal_code', count: 1, frequency: 100 },
        { field: 'requested_amount', count: 1, frequency: 100 },
        { field: 'product_type', count: 1, frequency: 100 },
        { field: 'employment_type', count: 1, frequency: 100 },
        { field: 'income_amount', count: 1, frequency: 100 },
        { field: 'social_security_number', count: 1, frequency: 100 },
        { field: 'account_number', count: 1, frequency: 100 },
        { field: 'bank_routing', count: 1, frequency: 100 }
      ]);
    } finally {
      setLoadingTargetFields(false);
    }
  }, [lenderId]);

  useEffect(() => {
    setSourceFields(sampleSourceFields);
    // Load target fields from API responses on component mount
    loadTargetFieldsFromApiResponses();
  }, [lenderId, sampleSourceFields, loadTargetFieldsFromApiResponses]);

  useEffect(() => {
    onMappingChange(mappings);
  }, [mappings, onMappingChange]);

  const addMapping = () => {
    const newMapping: FieldMapping = {
      name: `Mapping ${mappings.length + 1}`,
      source_field: '',
      target_field: '',
      transformation_type: 'none',
      transformation_config: {},
      is_required: false,
      is_active: true
    };
    setMappings([...mappings, newMapping]);
  };

  const updateMapping = (index: number, field: keyof FieldMapping, value: any) => {
    const updatedMappings = [...mappings];
    updatedMappings[index] = { ...updatedMappings[index], [field]: value };
    setMappings(updatedMappings);
  };

  const removeMapping = (index: number) => {
    const updatedMappings = mappings.filter((_, i) => i !== index);
    setMappings(updatedMappings);
  };

  const toggleMappingActive = (index: number) => {
    updateMapping(index, 'is_active', !mappings[index].is_active);
  };

  const getTransformationOptions = () => [
    { value: 'none', label: 'No Transformation' },
    { value: 'format_phone', label: 'Format Phone Number' },
    { value: 'format_date', label: 'Format Date' },
    { value: 'format_currency', label: 'Format Currency' },
    { value: 'split_name', label: 'Split Name' },
    { value: 'object_mapping', label: 'Object Mapping' },
    { value: 'array_format', label: 'Array Format' },
    { value: 'conditional', label: 'Conditional' }
  ];

  const renderTransformationConfig = (mapping: FieldMapping, index: number) => {
    switch (mapping.transformation_type) {
      case 'format_phone':
        return (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Format Type</label>
            <select
              value={mapping.transformation_config?.format || 'clean'}
              onChange={(e) => updateMapping(index, 'transformation_config', { format: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="clean">Clean (digits only)</option>
              <option value="dashed">Dashed (xxx-xxx-xxxx)</option>
              <option value="parentheses">Parentheses ((xxx) xxx-xxxx)</option>
            </select>
          </div>
        );

      case 'format_date':
        return (
          <div className="space-y-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Input Format</label>
              <input
                type="text"
                value={mapping.transformation_config?.input_format || '%Y-%m-%d'}
                onChange={(e) => updateMapping(index, 'transformation_config', { 
                  ...mapping.transformation_config, 
                  input_format: e.target.value 
                })}
                placeholder="%Y-%m-%d"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Output Format</label>
              <input
                type="text"
                value={mapping.transformation_config?.output_format || '%d/%m/%Y'}
                onChange={(e) => updateMapping(index, 'transformation_config', { 
                  ...mapping.transformation_config, 
                  output_format: e.target.value 
                })}
                placeholder="%d/%m/%Y"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        );

      case 'format_currency':
        return (
          <div className="space-y-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Decimal Places</label>
              <input
                type="number"
                value={mapping.transformation_config?.decimal_places || 2}
                onChange={(e) => updateMapping(index, 'transformation_config', { 
                  ...mapping.transformation_config, 
                  decimal_places: parseInt(e.target.value) 
                })}
                min="0"
                max="4"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={mapping.transformation_config?.include_symbol || false}
                onChange={(e) => updateMapping(index, 'transformation_config', { 
                  ...mapping.transformation_config, 
                  include_symbol: e.target.checked 
                })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label className="text-sm font-medium text-gray-700">Include Currency Symbol</label>
            </div>
            {mapping.transformation_config?.include_symbol && (
              <input
                type="text"
                value={mapping.transformation_config?.symbol || '$'}
                onChange={(e) => updateMapping(index, 'transformation_config', { 
                  ...mapping.transformation_config, 
                  symbol: e.target.value 
                })}
                placeholder="$"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            )}
          </div>
        );

      case 'conditional':
        return (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Conditions</label>
            <div className="space-y-2">
              {Object.entries(mapping.transformation_config?.conditions || {}).map(([key, value], i) => (
                <div key={i} className="flex space-x-2">
                  <input
                    type="text"
                    value={key}
                    onChange={(e) => {
                      const conditions = { ...mapping.transformation_config?.conditions };
                      delete conditions[key];
                      conditions[e.target.value] = value;
                      updateMapping(index, 'transformation_config', { 
                        ...mapping.transformation_config, 
                        conditions 
                      });
                    }}
                    placeholder="Source Value"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="flex items-center text-gray-500">→</span>
                  <input
                    type="text"
                    value={value as string}
                    onChange={(e) => {
                      const conditions = { ...mapping.transformation_config?.conditions };
                      conditions[key] = e.target.value;
                      updateMapping(index, 'transformation_config', { 
                        ...mapping.transformation_config, 
                        conditions 
                      });
                    }}
                    placeholder="Target Value"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => {
                      const conditions = { ...mapping.transformation_config?.conditions };
                      delete conditions[key];
                      updateMapping(index, 'transformation_config', { 
                        ...mapping.transformation_config, 
                        conditions 
                      });
                    }}
                    className="p-2 text-red-600 hover:text-red-800"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              ))}
              <button
                onClick={() => {
                  const conditions = { ...mapping.transformation_config?.conditions, '': '' };
                  updateMapping(index, 'transformation_config', { 
                    ...mapping.transformation_config, 
                    conditions 
                  });
                }}
                className="flex items-center space-x-1 text-blue-600 hover:text-blue-800"
              >
                <PlusIcon className="w-4 h-4" />
                <span>Add Condition</span>
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const testMapping = async (mapping: FieldMapping) => {
    try {
      let testData: any = {};
      try { testData = JSON.parse(sampleData || '{}'); } catch { testData = {}; }
      
      const response = await apiService.post('/field-mappings/test', {
        mapping,
        test_data: testData
      });
      
      toast.success('Mapping test completed successfully!');
      const result = (response as any)?.data?.result;
      setLastResult(result);
    } catch (error) {
      toast.error('Mapping test failed');
      console.error('Test error:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Field Mappings</h3>
          <p className="text-sm text-gray-500">
            Map your standard fields to lender-specific fields with transformations
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center space-x-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <CogIcon className="w-4 h-4" />
            <span>{showAdvanced ? 'Hide' : 'Show'} Advanced</span>
          </button>
          <button
            onClick={addMapping}
            className="flex items-center space-x-1 px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
          >
            <PlusIcon className="w-4 h-4" />
            <span>Add Mapping</span>
          </button>
        </div>
      </div>

      {/* Sample Data + Field Mapping List */}
      <div className="bg-white p-4 border rounded-lg">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Sample Input (JSON)</h4>
        <textarea value={sampleData} onChange={(e) => setSampleData(e.target.value)} rows={6} className="w-full font-mono text-sm px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder='{"full_name":"John Doe","phone":"+1-555-123-4567"}' />
        {lastResult !== null && (
          <div className="mt-3">
            <h4 className="text-sm font-medium text-gray-900 mb-1">Transform Result</h4>
            <pre className="bg-gray-50 p-2 rounded overflow-auto text-xs">{JSON.stringify(lastResult, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* Field Source Status */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-blue-900">API Response Fields</h3>
            <p className="text-sm text-blue-700 mt-1">
              Target fields are automatically loaded from actual API responses for this lender.
              {targetFields.length > 0 ? (
                <> Currently showing {targetFields.length} unique fields from recent API responses.</>
              ) : (
                <> No API response data found. Run some integrations first to populate target fields.</>
              )}
            </p>
          </div>
          <button
            onClick={loadTargetFieldsFromApiResponses}
            disabled={loadingTargetFields}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed rounded-md"
          >
            <ArrowPathIcon className={`w-4 h-4 mr-2 ${loadingTargetFields ? 'animate-spin' : ''}`} />
            {loadingTargetFields ? 'Loading...' : 'Refresh Fields'}
          </button>
        </div>
        {targetFieldsError && (
          <div className="mt-3 p-3 bg-red-100 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{targetFieldsError}</p>
          </div>
        )}
        {targetFields.length > 0 && (
          <div className="mt-3">
            <details className="text-sm">
              <summary className="cursor-pointer text-blue-700 hover:text-blue-800 font-medium">
                View Sample API Response Structure
              </summary>
              <div className="mt-2 p-3 bg-white border border-blue-200 rounded-md">
                <p className="text-xs text-gray-600 mb-2">
                  This shows the structure of recent API responses to help you understand available fields:
                </p>
                <div className="max-h-40 overflow-y-auto">
                  {targetFields.slice(0, 20).map((field) => (
                    <div key={field.field} className="flex justify-between items-center py-1 text-xs">
                      <code className="text-blue-800 bg-blue-50 px-1 rounded">{field.field}</code>
                      <span className="text-gray-500">{field.frequency.toFixed(1)}% frequency</span>
                    </div>
                  ))}
                  {targetFields.length > 20 && (
                    <p className="text-xs text-gray-500 mt-2">
                      ... and {targetFields.length - 20} more fields
                    </p>
                  )}
                </div>
              </div>
            </details>
          </div>
        )}
      </div>

      {/* Field Mapping List */}
      <div className="space-y-4">
        {mappings.map((mapping, index) => (
          <div
            key={index}
            className={`p-4 border rounded-lg ${
              mapping.is_active ? 'border-gray-300 bg-white' : 'border-gray-200 bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => toggleMappingActive(index)}
                  className={`p-1 rounded ${
                    mapping.is_active ? 'text-green-600' : 'text-gray-400'
                  }`}
                >
                  {mapping.is_active ? (
                    <EyeIcon className="w-4 h-4" />
                  ) : (
                    <EyeSlashIcon className="w-4 h-4" />
                  )}
                </button>
                <input
                  type="text"
                  value={mapping.name}
                  onChange={(e) => updateMapping(index, 'name', e.target.value)}
                  className="text-sm font-medium text-gray-900 bg-transparent border-none focus:outline-none focus:ring-0"
                  placeholder="Mapping Name"
                />
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => testMapping(mapping)}
                  className="p-1 text-blue-600 hover:text-blue-800"
                  title="Test Mapping"
                >
                  <EyeIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => removeMapping(index)}
                  className="p-1 text-red-600 hover:text-red-800"
                  title="Remove Mapping"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Field Mapping */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              {/* Source Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Source Field (Your Field)
                </label>
                <select
                  value={mapping.source_field}
                  onChange={(e) => updateMapping(index, 'source_field', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Source Field</option>
                  {sourceFields.map((field) => (
                    <option key={field} value={field}>
                      {field}
                    </option>
                  ))}
                </select>
              </div>

              {/* Arrow */}
              <div className="flex items-center justify-center">
                <ArrowsRightLeftIcon className="w-6 h-6 text-gray-400" />
              </div>

              {/* Target Field */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-gray-700">
                    Target Field (Lender Field)
                  </label>
                  <button
                    type="button"
                    onClick={loadTargetFieldsFromApiResponses}
                    disabled={loadingTargetFields}
                    className="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Refresh fields from API responses"
                  >
                    <ArrowPathIcon className={`w-3 h-3 mr-1 ${loadingTargetFields ? 'animate-spin' : ''}`} />
                    Refresh
                  </button>
                </div>
                <select
                  value={mapping.target_field}
                  onChange={(e) => updateMapping(index, 'target_field', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Target Field</option>
                  {loadingTargetFields ? (
                    <option value="">Loading fields...</option>
                  ) : targetFieldsError ? (
                    <option value="">Error: {targetFieldsError}</option>
                  ) : targetFields.length === 0 ? (
                    <option value="">No fields available - run integrations first</option>
                  ) : (
                    targetFields.map((field) => (
                      <option key={field.field} value={field.field}>
                        {field.field} ({field.frequency.toFixed(1)}% frequency)
                      </option>
                    ))
                  )}
                </select>
                {targetFields.length > 0 && (
                  <p className="mt-1 text-xs text-gray-500">
                    {targetFields.length} fields from {targetFields.reduce((sum, f) => sum + f.count, 0)} API responses
                  </p>
                )}
              </div>
            </div>

            {/* Transformation */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Transformation
              </label>
              <select
                value={mapping.transformation_type}
                onChange={(e) => updateMapping(index, 'transformation_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {getTransformationOptions().map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Transformation Configuration */}
            {mapping.transformation_type !== 'none' && (
              <div className="mb-4 p-3 bg-gray-50 rounded-md">
                {renderTransformationConfig(mapping, index)}
              </div>
            )}

            {/* Advanced Options */}
            {showAdvanced && (
              <div className="space-y-4 p-3 bg-gray-50 rounded-md">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Default Value
                    </label>
                    <input
                      type="text"
                      value={mapping.default_value || ''}
                      onChange={(e) => updateMapping(index, 'default_value', e.target.value)}
                      placeholder="Default value if source is empty"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Fallback Value
                    </label>
                    <input
                      type="text"
                      value={mapping.fallback_value || ''}
                      onChange={(e) => updateMapping(index, 'fallback_value', e.target.value)}
                      placeholder="Fallback value on error"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={mapping.is_required}
                    onChange={(e) => updateMapping(index, 'is_required', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm font-medium text-gray-700">Required Field</label>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Empty State */}
      {mappings.length === 0 && (
        <div className="text-center py-8">
          <ArrowsRightLeftIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No field mappings</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by adding your first field mapping.
          </p>
          <div className="mt-6">
            <button
              onClick={addMapping}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add Mapping
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FieldMappingInterface;
