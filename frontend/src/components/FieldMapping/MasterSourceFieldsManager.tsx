import React, { useState, useEffect } from 'react';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';

interface MasterSourceField {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  field_type: string;
  is_required: boolean;
  validation_rules?: any;
  default_value?: string;
  sample_data?: any;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

interface MasterSourceFieldsManagerProps {
  onFieldChange?: () => void;
}

const MasterSourceFieldsManager: React.FC<MasterSourceFieldsManagerProps> = ({
  onFieldChange
}) => {
  const [fields, setFields] = useState<MasterSourceField[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingField, setEditingField] = useState<MasterSourceField | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    field_type: 'string',
    is_required: false,
    validation_rules: {},
    default_value: '',
    sample_data: {},
    is_active: true
  });

  const loadFields = async () => {
    try {
      setLoading(true);
      const response = await apiService.get<{data: MasterSourceField[]}>('/lenders/master-source-fields');
      if (response.success && response.data && Array.isArray(response.data)) {
        setFields(response.data);
      }
    } catch (error: any) {
      console.error('Failed to load master source fields:', error);
      toast.error('Failed to load master source fields');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFields();
  }, []);

  const handleSubmit = async () => {
    try {
      if (!formData.name || !formData.display_name) {
        toast.error('Field name and display name are required');
        return;
      }

      if (editingField) {
        // Update existing field
        await apiService.put(`/lenders/master-source-fields/${editingField.id}`, formData);
        toast.success('Field updated successfully');
      } else {
        // Create new field
        await apiService.post('/lenders/master-source-fields', formData);
        toast.success('Field created successfully');
      }

      setShowCreateModal(false);
      setEditingField(null);
      resetForm();
      loadFields();
      onFieldChange?.();
    } catch (error: any) {
      console.error('Failed to save field:', error);
      toast.error(error.response?.data?.message || 'Failed to save field');
    }
  };

  const handleEdit = (field: MasterSourceField) => {
    setEditingField(field);
    setFormData({
      name: field.name,
      display_name: field.display_name,
      description: field.description || '',
      field_type: field.field_type,
      is_required: field.is_required,
      validation_rules: field.validation_rules || {},
      default_value: field.default_value || '',
      sample_data: field.sample_data || {},
      is_active: field.is_active
    });
    setShowCreateModal(true);
  };

  const handleDelete = async (fieldId: number, fieldName: string) => {
    if (!confirm(`Are you sure you want to delete the field "${fieldName}"?`)) {
      return;
    }

    try {
      await apiService.delete(`/lenders/master-source-fields/${fieldId}`);
      toast.success('Field deleted successfully');
      loadFields();
      onFieldChange?.();
    } catch (error: any) {
      console.error('Failed to delete field:', error);
      toast.error(error.response?.data?.message || 'Failed to delete field');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      display_name: '',
      description: '',
      field_type: 'string',
      is_required: false,
      validation_rules: {},
      default_value: '',
      sample_data: {},
      is_active: true
    });
  };

  const openCreateModal = () => {
    setEditingField(null);
    resetForm();
    setShowCreateModal(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-900">Master Source Fields</h2>
        <button
          onClick={openCreateModal}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          Add Field
        </button>
      </div>

      {loading ? (
        <div className="text-center py-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading fields...</p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {fields.map((field) => (
              <li key={field.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      {field.is_active ? (
                        <EyeIcon className="h-5 w-5 text-green-500" />
                      ) : (
                        <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                      )}
                    </div>
                    <div className="ml-4">
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-gray-900">
                          {field.display_name}
                        </p>
                        <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {field.field_type}
                        </span>
                        {field.is_required && (
                          <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            Required
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500">
                        API Name: {field.name}
                      </p>
                      {field.description && (
                        <p className="text-sm text-gray-500 mt-1">
                          {field.description}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleEdit(field)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(field.id, field.display_name)}
                      className="text-red-600 hover:text-red-900"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
          <div className="relative p-8 border w-full max-w-2xl max-h-full">
            <div className="relative bg-white rounded-lg shadow">
              <div className="flex justify-between items-start p-4 rounded-t border-b">
                <h3 className="text-xl font-semibold text-gray-900">
                  {editingField ? 'Edit Field' : 'Create New Field'}
                </h3>
                <button
                  type="button"
                  className="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm p-1.5 ml-auto inline-flex items-center"
                  onClick={() => setShowCreateModal(false)}
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path>
                  </svg>
                </button>
              </div>
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Field Name (API)
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., full_name"
                      disabled={!!editingField}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Display Name
                    </label>
                    <input
                      type="text"
                      value={formData.display_name}
                      onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., Full Name"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Describe the purpose of this field"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Field Type
                    </label>
                    <select
                      value={formData.field_type}
                      onChange={(e) => setFormData({ ...formData, field_type: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="string">String</option>
                      <option value="number">Number</option>
                      <option value="boolean">Boolean</option>
                      <option value="object">Object</option>
                      <option value="array">Array</option>
                      <option value="date">Date</option>
                      <option value="email">Email</option>
                      <option value="phone">Phone</option>
                      <option value="currency">Currency</option>
                    </select>
                  </div>
                  <div className="flex items-center mt-6">
                    <input
                      type="checkbox"
                      checked={formData.is_required}
                      onChange={(e) => setFormData({ ...formData, is_required: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label className="ml-2 block text-sm text-gray-900">
                      Required Field
                    </label>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Default Value
                  </label>
                  <input
                    type="text"
                    value={formData.default_value}
                    onChange={(e) => setFormData({ ...formData, default_value: e.target.value })}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Default value for this field"
                  />
                </div>
              </div>
              <div className="flex items-center p-6 space-x-2 rounded-b border-t">
                <button
                  onClick={handleSubmit}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {editingField ? 'Update Field' : 'Create Field'}
                </button>
                <button
                  onClick={() => setShowCreateModal(false)}
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

export default MasterSourceFieldsManager;
