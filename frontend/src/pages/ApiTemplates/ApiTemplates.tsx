import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';

interface ApiTemplate {
  id: number;
  name: string;
  description: string;
  language: string;
  framework: string;
  version: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const ApiTemplates: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    language: '',
    framework: '',
    is_active: '',
  });

  // Fetch API templates
  const { data, isLoading, error } = useQuery(
    ['api-templates', searchTerm, filters],
    () => apiService.get<{ templates: ApiTemplate[] }>('/api-templates', {
      search: searchTerm || undefined,
      ...filters,
    })
  );

  // Delete template
  const deleteMutation = useMutation(
    (templateId: number) => apiService.delete(`/api-templates/${templateId}`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['api-templates']);
        toast.success('Template deleted successfully');
      },
      onError: () => {
        toast.error('Failed to delete template');
      },
    }
  );

  const handleDelete = (templateId: number, templateName: string) => {
    if (window.confirm(`Are you sure you want to delete "${templateName}"?`)) {
      deleteMutation.mutate(templateId);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
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
          <h1 className="text-2xl font-bold text-gray-900">API Templates</h1>
          <p className="text-gray-600">Manage your API code generation templates</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">Failed to load API templates. Please try again.</p>
        </div>
      </div>
    );
  }

  const templates = data?.data?.templates || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Templates</h1>
          <p className="text-gray-600">Manage your API code generation templates</p>
        </div>
        <button className="btn-primary">
          <PlusIcon className="h-5 w-5 mr-2" />
          Add Template
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
                placeholder="Search templates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filters.language}
              onChange={(e) => setFilters(prev => ({ ...prev, language: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Languages</option>
              <option value="python">Python</option>
              <option value="typescript">TypeScript</option>
              <option value="java">Java</option>
              <option value="csharp">C#</option>
            </select>
            <select
              value={filters.framework}
              onChange={(e) => setFilters(prev => ({ ...prev, framework: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Frameworks</option>
              <option value="fastapi">FastAPI</option>
              <option value="express">Express</option>
              <option value="spring">Spring</option>
              <option value="aspnet">ASP.NET</option>
            </select>
          </div>
        </div>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => (
          <div key={template.id} className="bg-white shadow rounded-lg overflow-hidden">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <DocumentTextIcon className="h-8 w-8 text-blue-500 mr-3" />
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{template.name}</h3>
                    <p className="text-sm text-gray-500">{template.framework}</p>
                  </div>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  template.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {template.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              <p className="text-gray-600 mb-4">{template.description}</p>
              
              <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                <span>Language: {template.language}</span>
                <span>v{template.version}</span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex space-x-2">
                  <button className="p-2 text-gray-400 hover:text-gray-600">
                    <EyeIcon className="h-4 w-4" />
                  </button>
                  <button className="p-2 text-gray-400 hover:text-blue-600">
                    <PencilIcon className="h-4 w-4" />
                  </button>
                </div>
                <button
                  onClick={() => handleDelete(template.id, template.name)}
                  className="p-2 text-gray-400 hover:text-red-600"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {templates.length === 0 && (
        <div className="text-center py-12">
          <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No templates found</h3>
          <p className="text-gray-500">Get started by creating your first API template.</p>
        </div>
      )}
    </div>
  );
};

export default ApiTemplates;
