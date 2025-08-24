import React, { useState, useEffect } from 'react';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';
import SequenceBuilder from './SequenceBuilder';

interface IntegrationStep {
  id?: number;
  name: string;
  integration_type: string;
  api_endpoint: string;
  http_method: string;
  sequence_order: number;
  auth_type: string;
  auth_config: any;
  depends_on_fields: Record<string, string>;
  output_fields: string[];
  is_active: boolean;
  timeout_seconds?: number;
  retry_count?: number;
  retry_delay_seconds?: number;
  rate_limit_per_minute?: number;
  request_headers?: Record<string, string>;
  request_schema?: { template?: any } | any;
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
  steps: IntegrationStep[];
  created_at?: string;
  updated_at?: string;
}

interface SequencesManagerProps {
  lenderId: number;
}

const SequencesManager: React.FC<SequencesManagerProps> = ({ lenderId }) => {
  const [sequences, setSequences] = useState<IntegrationSequence[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingSequence, setEditingSequence] = useState<IntegrationSequence | null>(null);
  const [viewingSequence, setViewingSequence] = useState<IntegrationSequence | null>(null);
  const [deletingSequence, setDeletingSequence] = useState<IntegrationSequence | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Load sequences
  const loadSequences = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.get<IntegrationSequence[]>(`/lenders/${lenderId}/integration-sequences`);
      if (response.data) {
        // Filter out inactive sequences for display
        const activeSequences = response.data.filter(seq => seq.is_active);
        setSequences(activeSequences);
        console.log('Loaded sequences:', response.data.length, 'Active:', activeSequences.length);
      }
    } catch (error) {
      console.error('Failed to load sequences:', error);
      toast.error('Failed to load sequences');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSequences();
  }, [lenderId]);

  // Create new sequence
  const handleCreateSequence = async (sequence: IntegrationSequence) => {
    try {
      await apiService.post(`/lenders/${lenderId}/integration-sequences`, sequence);
      toast.success('Sequence created successfully');
      setShowCreateModal(false);
      loadSequences();
    } catch (error) {
      console.error('Failed to create sequence:', error);
      toast.error('Failed to create sequence');
    }
  };

  // Update existing sequence
  const handleUpdateSequence = async (sequence: IntegrationSequence) => {
    if (!editingSequence?.id) return;
    
    try {
      await apiService.put(`/lenders/${lenderId}/integration-sequences/${editingSequence.id}`, sequence);
      toast.success('Sequence updated successfully');
      setEditingSequence(null);
      loadSequences();
    } catch (error) {
      console.error('Failed to update sequence:', error);
      toast.error('Failed to update sequence');
    }
  };

  // Delete sequence
  const handleDeleteSequence = async () => {
    if (!deletingSequence?.id) return;
    
    try {
      setIsDeleting(true);
      await apiService.delete(`/lenders/${lenderId}/integration-sequences/${deletingSequence.id}`);
      toast.success('Sequence deleted successfully');
      setDeletingSequence(null);
      await loadSequences(); // Wait for the load to complete
    } catch (error) {
      console.error('Failed to delete sequence:', error);
      toast.error('Failed to delete sequence');
    } finally {
      setIsDeleting(false);
    }
  };

  // Toggle sequence active status
  const toggleSequenceStatus = async (sequence: IntegrationSequence) => {
    try {
      const updatedSequence = { ...sequence, is_active: !sequence.is_active };
      await apiService.put(`/lenders/${lenderId}/integration-sequences/${sequence.id}`, updatedSequence);
      toast.success(`Sequence ${updatedSequence.is_active ? 'activated' : 'deactivated'} successfully`);
      loadSequences();
    } catch (error) {
      console.error('Failed to toggle sequence status:', error);
      toast.error('Failed to update sequence status');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSequenceTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'lead_submission': 'bg-blue-100 text-blue-800',
      'status_check': 'bg-green-100 text-green-800',
      'document_upload': 'bg-purple-100 text-purple-800',
      'approval_workflow': 'bg-orange-100 text-orange-800',
      'default': 'bg-gray-100 text-gray-800'
    };
    return colors[type] || colors.default;
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white shadow rounded-lg p-6">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/4"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Integration Sequences</h2>
          <p className="text-sm text-gray-600">
            Manage multiple integration sequences for this lender
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Sequence
        </button>
      </div>

      {/* Sequences Grid */}
      {sequences.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No sequences</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating your first integration sequence.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Create Sequence
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sequences.map((sequence) => (
            <div key={sequence.id} className="bg-white shadow rounded-lg p-6 border border-gray-200">
              {/* Sequence Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900 truncate">
                    {sequence.name}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                    {sequence.description || 'No description'}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSequenceTypeColor(sequence.sequence_type)}`}>
                    {sequence.sequence_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                  <div className={`w-2 h-2 rounded-full ${sequence.is_active ? 'bg-green-400' : 'bg-gray-400'}`} />
                </div>
              </div>

              {/* Sequence Details */}
              <div className="space-y-3 mb-4">
                <div className="flex items-center text-sm text-gray-600">
                  <ClockIcon className="h-4 w-4 mr-2" />
                  <span>Mode: {sequence.execution_mode}</span>
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  <span>{sequence.steps.length} step{sequence.steps.length !== 1 ? 's' : ''}</span>
                </div>
                {sequence.created_at && (
                  <div className="text-xs text-gray-500">
                    Created: {formatDate(sequence.created_at)}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setViewingSequence(sequence)}
                    className="btn-secondary btn-sm"
                    title="View Sequence"
                  >
                    <EyeIcon className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setEditingSequence(sequence)}
                    className="btn-secondary btn-sm"
                    title="Edit Sequence"
                  >
                    <PencilIcon className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => toggleSequenceStatus(sequence)}
                    className={`btn-sm ${sequence.is_active ? 'btn-warning' : 'btn-success'}`}
                    title={sequence.is_active ? 'Deactivate' : 'Activate'}
                  >
                    {sequence.is_active ? <XCircleIcon className="h-4 w-4" /> : <CheckCircleIcon className="h-4 w-4" />}
                  </button>
                </div>
                <button
                  onClick={() => setDeletingSequence(sequence)}
                  className="btn-danger btn-sm"
                  title="Delete Sequence"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Sequence Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Create New Sequence</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <SequenceBuilder
              lenderId={lenderId}
              onSequenceChange={handleCreateSequence}
              onValidityChange={() => {}}
            />
          </div>
        </div>
      )}

      {/* Edit Sequence Modal */}
      {editingSequence && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Edit Sequence: {editingSequence.name}</h3>
              <button
                onClick={() => setEditingSequence(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <SequenceBuilder
              lenderId={lenderId}
              onSequenceChange={handleUpdateSequence}
              initialSequence={editingSequence}
              onValidityChange={() => {}}
            />
          </div>
        </div>
      )}

      {/* View Sequence Modal */}
      {viewingSequence && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">View Sequence: {viewingSequence.name}</h3>
              <button
                onClick={() => setViewingSequence(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="space-y-6">
              {/* Sequence Info */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Sequence Information</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Type:</span>
                    <span className="ml-2 font-medium">{viewingSequence.sequence_type}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Execution Mode:</span>
                    <span className="ml-2 font-medium">{viewingSequence.execution_mode}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Stop on Error:</span>
                    <span className="ml-2 font-medium">{viewingSequence.stop_on_error ? 'Yes' : 'No'}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Retry Failed Steps:</span>
                    <span className="ml-2 font-medium">{viewingSequence.retry_failed_steps ? 'Yes' : 'No'}</span>
                  </div>
                </div>
                {viewingSequence.description && (
                  <div className="mt-3">
                    <span className="text-gray-600">Description:</span>
                    <p className="mt-1 text-gray-900">{viewingSequence.description}</p>
                  </div>
                )}
              </div>

              {/* Steps */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Steps ({viewingSequence.steps.length})</h4>
                <div className="space-y-3">
                  {viewingSequence.steps.map((step, index) => (
                    <div key={step.id || index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-medium text-gray-900">
                          {index + 1}. {step.name}
                        </h5>
                        <div className="flex items-center space-x-2">
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800`}>
                            {step.http_method}
                          </span>
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800`}>
                            {step.integration_type}
                          </span>
                        </div>
                      </div>
                      <div className="text-sm text-gray-600">
                        <div className="mb-1">
                          <span className="font-medium">Endpoint:</span> {step.api_endpoint}
                        </div>
                        <div className="mb-1">
                          <span className="font-medium">Auth:</span> {step.auth_type}
                        </div>
                        {step.timeout_seconds && (
                          <div className="mb-1">
                            <span className="font-medium">Timeout:</span> {step.timeout_seconds}s
                          </div>
                        )}
                        {step.retry_count && step.retry_count > 0 && (
                          <div>
                            <span className="font-medium">Retries:</span> {step.retry_count} (delay: {step.retry_delay_seconds || 5}s)
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingSequence && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-4">Delete Sequence</h3>
              <div className="mt-2 px-7">
                <p className="text-sm text-gray-500 mb-3">
                  Are you sure you want to delete "{deletingSequence.name}"?
                </p>
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-left">
                  <p className="text-sm font-medium text-red-800 mb-2">This will permanently delete:</p>
                  <ul className="text-xs text-red-700 space-y-1">
                    <li>• The sequence configuration</li>
                    <li>• All {deletingSequence.steps.length} integration steps</li>
                    <li>• All execution logs and test data</li>
                    <li>• Any deployed APIs using this sequence</li>
                  </ul>
                  <p className="text-xs text-red-600 mt-2 font-medium">This action cannot be undone!</p>
                </div>
              </div>
              <div className="flex items-center justify-center space-x-3 mt-6">
                <button
                  onClick={() => setDeletingSequence(null)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteSequence}
                  disabled={isDeleting}
                  className={`btn-danger ${isDeleting ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {isDeleting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Deleting...
                    </>
                  ) : (
                    'Delete Permanently'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SequencesManager;
