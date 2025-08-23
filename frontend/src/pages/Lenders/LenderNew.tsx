import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';

const LenderNew: React.FC = () => {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: '',
    base_url: '',
    description: '',
    api_version: '',
    contact_email: '',
    auth_type: 'bearer',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload: any = {
        name: form.name.trim(),
        base_url: form.base_url.trim(),
        description: form.description || undefined,
        api_version: form.api_version || undefined,
        contact_email: form.contact_email || undefined,
        auth_type: form.auth_type || 'bearer',
      };
      const res = await apiService.post<{ id: number }>('/lenders', payload);
      const createdId = (res.data as any)?.id || (res as any)?.id; // handle either shape
      toast.success('Lender created successfully');
      if (createdId) {
        navigate(`/lenders/${createdId}`);
      } else {
        navigate('/lenders');
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.message || 'Failed to create lender');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Create New Lender</h1>
        <p className="text-gray-600">Provide basic details to add a new lender</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-4 max-w-2xl">
        <div>
          <label className="block text-sm font-medium text-gray-700">Name<span className="text-red-500">*</span></label>
          <input
            name="name"
            value={form.name}
            onChange={handleChange}
            required
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Acme Lender"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Base URL<span className="text-red-500">*</span></label>
          <input
            name="base_url"
            value={form.base_url}
            onChange={handleChange}
            required
            type="url"
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="https://api.example.com"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">API Version</label>
          <input
            name="api_version"
            value={form.api_version}
            onChange={handleChange}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="v1"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Description</label>
          <input
            name="description"
            value={form.description}
            onChange={handleChange}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Short description"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Contact Email</label>
          <input
            name="contact_email"
            type="email"
            value={form.contact_email}
            onChange={handleChange}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="ops@example.com"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Auth Type</label>
          <select
            name="auth_type"
            value={form.auth_type}
            onChange={handleChange}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="bearer">Bearer</option>
            <option value="api_key">API Key</option>
            <option value="oauth2">OAuth2</option>
            <option value="basic">Basic Auth</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">Leave auth config empty for now; you can configure details later.</p>
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? 'Creating...' : 'Create Lender'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default LenderNew;


