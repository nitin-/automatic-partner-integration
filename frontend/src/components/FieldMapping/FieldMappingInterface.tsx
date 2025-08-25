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
  is_custom: boolean;
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
  const [showCustomFieldModal, setShowCustomFieldModal] = useState(false);
  const [customFieldData, setCustomFieldData] = useState({
    name: '',
    display_name: '',
    description: '',
    field_type: 'string',
    default_value: ''
  });

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

  // Load target fields from step configurations
  const loadTargetFieldsFromStepConfigs = useCallback(async () => {
    try {
      setLoadingTargetFields(true);
      setTargetFieldsError(null);
      
      const response = await apiService.get<{
        fields: ApiResponseField[];
        total_steps: number;
        custom_fields_count: number;
        unique_fields_count: number;
      }>(`/lenders/${lenderId}/enhanced-request-fields`);
      
      if (response.data?.fields) {
        setTargetFields(response.data.fields);
        toast.success(`Loaded ${response.data.fields.length} fields (${response.data.custom_fields_count} custom) from ${response.data.total_steps} integration steps`);
      } else {
        setTargetFields([]);
        toast('No request field data found. Configure integration steps first to populate target fields.', { icon: 'ℹ️' });
      }
    } catch (error: any) {
      console.error('Failed to load target fields:', error);
      setTargetFieldsError(error.response?.data?.message || 'Failed to load target fields from step configurations');
      toast.error('Failed to load target fields from step configurations');
      
      // Fallback to sample fields if API call fails
      setTargetFields([
        { field: 'customer_name', count: 1, frequency: 100, is_custom: false },
        { field: 'email_address', count: 1, frequency: 100, is_custom: false },
        { field: 'mobile_number', count: 1, frequency: 100, is_custom: false },
        { field: 'birth_date', count: 1, frequency: 100, is_custom: false },
        { field: 'residential_address', count: 1, frequency: 100, is_custom: false },
        { field: 'city_name', count: 1, frequency: 100, is_custom: false },
        { field: 'state_code', count: 1, frequency: 100, is_custom: false },
        { field: 'postal_code', count: 1, frequency: 100, is_custom: false },
        { field: 'requested_amount', count: 1, frequency: 100, is_custom: false },
        { field: 'product_type', count: 1, frequency: 100, is_custom: false },
        { field: 'employment_type', count: 1, frequency: 100, is_custom: false },
        { field: 'income_amount', count: 1, frequency: 100, is_custom: false },
        { field: 'social_security_number', count: 1, frequency: 100, is_custom: false },
        { field: 'account_number', count: 1, frequency: 100, is_custom: false },
        { field: 'bank_routing', count: 1, frequency: 100, is_custom: false }
      ]);
    } finally {
      setLoadingTargetFields(false);
    }
  }, [lenderId]);

  useEffect(() => {
    setSourceFields(sampleSourceFields);
    // Load target fields from step configurations on component mount
    loadTargetFieldsFromStepConfigs();
  }, [lenderId, sampleSourceFields, loadTargetFieldsFromStepConfigs]);

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
    
    // Handle custom field creation
    if (field === 'target_field' && value === '__create_custom__') {
      setShowCustomFieldModal(true);
    }
  };

  const createCustomField = async () => {
    try {
      if (!customFieldData.name || !customFieldData.display_name) {
        toast.error('Field name and display name are required');
        return;
      }
      
      const response = await apiService.post(`/lenders/${lenderId}/custom-target-fields`, {
        ...customFieldData,
        lender_id: lenderId
      });
      
      if (response.success) {
        toast.success('Custom field created successfully');
        setShowCustomFieldModal(false);
        setCustomFieldData({
          name: '',
          display_name: '',
          description: '',
          field_type: 'string',
          default_value: ''
        });
        
        // Refresh target fields
        loadTargetFieldsFromStepConfigs();
      }
    } catch (error: any) {
      console.error('Failed to create custom field:', error);
      toast.error(error.response?.data?.message || 'Failed to create custom field');
    }
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
            <h3 className="text-sm font-medium text-blue-900">Request Fields</h3>
            <p className="text-sm text-blue-700 mt-1">
              Target fields are automatically loaded from integration steps for this lender.
              {targetFields.length > 0 ? (
                <> Currently showing {targetFields.length} unique fields from recent integration steps.</>
              ) : (
                <> No request field data found. Configure integration steps first to populate target fields.</>
              )}
            </p>
          </div>
          <button
            onClick={loadTargetFieldsFromStepConfigs}
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
                View Sample Request Structure
              </summary>
              <div className="mt-2 p-3 bg-white border border-blue-200 rounded-md">
                <p className="text-xs text-gray-600 mb-2">
                  This shows the structure of recent integration steps to help you understand available fields:
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
                    Target Field (Request Field)
                  </label>
                  <button
                    type="button"
                    onClick={loadTargetFieldsFromStepConfigs}
                    disabled={loadingTargetFields}
                    className="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Refresh fields from step configurations"
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
                    <option value="">No fields available - configure integration steps first</option>
                  ) : (
                    <>
                      <optgroup label="Step Fields">
                        {targetFields.filter(field => !field.is_custom).map((field) => (
                          <option key={field.field} value={field.field}>
                            {field.field} ({field.frequency.toFixed(1)}% frequency)
                          </option>
                        ))}
                      </optgroup>
                      {targetFields.some(field => field.is_custom) && (
                        <optgroup label="Custom Fields">
                          {targetFields.filter(field => field.is_custom).map((field) => (
                            <option key={field.field} value={field.field}>
                              {field.field} (Custom)
                            </option>
                          ))}
                        </optgroup>
                      )}
                      <option value="__create_custom__">+ Create Custom Field</option>
                    </>
                  )}
                </select>
                {targetFields.length > 0 && (
                  <p className="mt-1 text-xs text-gray-500">
                    {targetFields.length} fields from {targetFields.reduce((sum, f) => sum + f.count, 0)} integration steps
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

      {/* Custom Field Creation Modal */}
      {showCustomFieldModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
          <div className="relative p-8 border w-full max-w-md max-h-full">
            <div className="relative bg-white rounded-lg shadow dark:bg-gray-700">
              <div className="flex justify-between items-start p-4 rounded-t border-b dark:border-gray-600">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Create Custom Field
                </h3>
                <button
                  type="button"
                  className="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm p-1.5 ml-auto inline-flex items-center dark:hover:bg-gray-600 dark:hover:text-white"
                  onClick={() => setShowCustomFieldModal(false)}
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path></svg>
                </button>
              </div>
              <div className="p-6 space-y-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Field Name (API)
                  </label>
                  <input
                    type="text"
                    id="name"
                    value={customFieldData.name}
                    onChange={(e) => setCustomFieldData({ ...customFieldData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., custom_loan_amount"
                  />
                </div>
                <div>
                  <label htmlFor="display_name" className="block text-sm font-medium text-gray-700">
                    Display Name (User-friendly)
                  </label>
                  <input
                    type="text"
                    id="display_name"
                    value={customFieldData.display_name}
                    onChange={(e) => setCustomFieldData({ ...customFieldData, display_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Loan Amount"
                  />
                </div>
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                    Description (Optional)
                  </label>
                  <textarea
                    id="description"
                    value={customFieldData.description}
                    onChange={(e) => setCustomFieldData({ ...customFieldData, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Describe the purpose of this custom field"
                  />
                </div>
                <div>
                  <label htmlFor="field_type" className="block text-sm font-medium text-gray-700">
                    Field Type
                  </label>
                  <select
                    id="field_type"
                    value={customFieldData.field_type}
                    onChange={(e) => setCustomFieldData({ ...customFieldData, field_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="string">String</option>
                    <option value="number">Number</option>
                    <option value="boolean">Boolean</option>
                    <option value="object">Object</option>
                    <option value="array">Array</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="default_value" className="block text-sm font-medium text-gray-700">
                    Default Value (JSON)
                  </label>
                  <input
                    type="text"
                    id="default_value"
                    value={customFieldData.default_value}
                    onChange={(e) => setCustomFieldData({ ...customFieldData, default_value: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder='{"amount": 12345.67}'
                  />
                </div>
              </div>
              <div className="flex items-center p-6 space-x-2 rounded-b border-t dark:border-gray-600">
                <button
                  onClick={createCustomField}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Create Custom Field
                </button>
                <button
                  onClick={() => setShowCustomFieldModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FieldMappingInterface;
