import React, { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';

interface Lender {
  id: number;
  name: string;
  base_url: string;
  auth_type: string;
}

interface Template {
  id: number;
  name: string;
  template_type: string;
  category: string;
  language: string;
}

interface GenerateApiModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const GenerateApiModal: React.FC<GenerateApiModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState({
    lender_id: '',
    template_id: '',
    language: 'python',
    framework: 'fastapi',
  });

  // Fetch lenders
  const { data: lendersData } = useQuery(
    'lenders',
    () => apiService.get<{ lenders: Lender[] }>('/lenders', { size: 100 })
  );

  // Fetch templates
  const { data: templatesData } = useQuery(
    'templates',
    () => apiService.get<{ templates: Template[] }>('/api-templates', { size: 100 })
  );

  // Generate API mutation
  const generateMutation = useMutation(
    (data: any) => apiService.post('/generated-apis/generate', data),
    {
      onSuccess: () => {
        onSuccess();
        onClose();
      },
      onError: () => {
        toast.error('Failed to start API generation');
      },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    generateMutation.mutate(formData);
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const getLanguageOptions = () => {
    const templates = templatesData?.data?.templates || [];
    const languages = Array.from(new Set(templates.map(t => t.language)));
    return languages.map(lang => ({
      value: lang,
      label: lang.charAt(0).toUpperCase() + lang.slice(1),
    }));
  };

  const getFrameworkOptions = (language: string) => {
    const frameworks = {
      python: ['fastapi', 'django', 'flask'],
      typescript: ['express', 'nestjs', 'fastify'],
      javascript: ['express', 'koa', 'hapi'],
      java: ['spring', 'quarkus', 'micronaut'],
      csharp: ['aspnet', 'dotnet'],
    };
    return (frameworks[language as keyof typeof frameworks] || []).map(fw => ({
      value: fw,
      label: fw.charAt(0).toUpperCase() + fw.slice(1),
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Generate API Client
              </h3>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Lender Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Lender *
                </label>
                <select
                  value={formData.lender_id}
                  onChange={(e) => handleInputChange('lender_id', e.target.value)}
                  className="input-field"
                  required
                >
                  <option value="">Choose a lender...</option>
                  {lendersData?.data?.lenders?.map((lender) => (
                    <option key={lender.id} value={lender.id}>
                      {lender.name} ({lender.base_url})
                    </option>
                  ))}
                </select>
              </div>

              {/* Template Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template (Optional)
                </label>
                <select
                  value={formData.template_id}
                  onChange={(e) => handleInputChange('template_id', e.target.value)}
                  className="input-field"
                >
                  <option value="">Use default template</option>
                  {templatesData?.data?.templates?.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name} ({template.template_type})
                    </option>
                  ))}
                </select>
              </div>

              {/* Language Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Programming Language *
                </label>
                <select
                  value={formData.language}
                  onChange={(e) => handleInputChange('language', e.target.value)}
                  className="input-field"
                  required
                >
                  {getLanguageOptions().map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Framework Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Framework *
                </label>
                <select
                  value={formData.framework}
                  onChange={(e) => handleInputChange('framework', e.target.value)}
                  className="input-field"
                  required
                >
                  {getFrameworkOptions(formData.language).map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Generation Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                <h4 className="text-sm font-medium text-blue-900 mb-2">
                  Generation Process
                </h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• API client will be generated in the background</li>
                  <li>• You'll be notified when generation is complete</li>
                  <li>• Generated code will be available for download</li>
                  <li>• Automatic validation will be performed</li>
                </ul>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={generateMutation.isLoading || !formData.lender_id}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {generateMutation.isLoading ? (
                    <>
                      <div className="loading-spinner mr-2"></div>
                      Generating...
                    </>
                  ) : (
                    'Generate API'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GenerateApiModal;
