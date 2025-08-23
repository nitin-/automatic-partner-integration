import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  UserIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'admin' | 'user' | 'viewer';
  is_active: boolean;
  last_login: string;
  created_at: string;
}

const Users: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    role: '',
    is_active: '',
  });

  // Fetch users
  const { data, isLoading, error } = useQuery(
    ['users', searchTerm, filters],
    () => apiService.get<{ users: User[] }>('/users', {
      search: searchTerm || undefined,
      ...filters,
    })
  );

  // Toggle user status
  const toggleStatusMutation = useMutation(
    (userId: number) => apiService.patch(`/users/${userId}/toggle-status`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['users']);
        toast.success('User status updated successfully');
      },
      onError: () => {
        toast.error('Failed to update user status');
      },
    }
  );

  // Delete user
  const deleteMutation = useMutation(
    (userId: number) => apiService.delete(`/users/${userId}`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['users']);
        toast.success('User deleted successfully');
      },
      onError: () => {
        toast.error('Failed to delete user');
      },
    }
  );

  const handleToggleStatus = (userId: number) => {
    toggleStatusMutation.mutate(userId);
  };

  const handleDelete = (userId: number, userName: string) => {
    if (window.confirm(`Are you sure you want to delete "${userName}"?`)) {
      deleteMutation.mutate(userId);
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800';
      case 'user':
        return 'bg-blue-100 text-blue-800';
      case 'viewer':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
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
          <h1 className="text-2xl font-bold text-gray-900">Users</h1>
          <p className="text-gray-600">Manage user accounts and permissions</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">Failed to load users. Please try again.</p>
        </div>
      </div>
    );
  }

  const users = data?.data?.users || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Users</h1>
          <p className="text-gray-600">Manage user accounts and permissions</p>
        </div>
        <button className="btn-primary">
          <PlusIcon className="h-5 w-5 mr-2" />
          Add User
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
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filters.role}
              onChange={(e) => setFilters(prev => ({ ...prev, role: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Roles</option>
              <option value="admin">Admin</option>
              <option value="user">User</option>
              <option value="viewer">Viewer</option>
            </select>
            <select
              value={filters.is_active}
              onChange={(e) => setFilters(prev => ({ ...prev, is_active: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Statuses</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>
        </div>
      </div>

      {/* Users List */}
      <div className="space-y-4">
        {users.map((user) => (
          <div key={user.id} className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <div className="mr-4">
                  <UserIcon className="h-8 w-8 text-gray-400" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900">
                    {user.first_name} {user.last_name}
                  </h3>
                  <p className="text-sm text-gray-500">@{user.username}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(user.role)}`}>
                  {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                </span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  user.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="flex items-center">
                <EnvelopeIcon className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-sm text-gray-900">{user.email}</span>
              </div>
              <div>
                <span className="text-sm text-gray-500">Last Login:</span>
                <p className="text-sm text-gray-900">
                  {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Created:</span>
                <p className="text-sm text-gray-900">
                  {new Date(user.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <button className="btn-secondary">
                  <EyeIcon className="h-4 w-4 mr-2" />
                  View Profile
                </button>
                <button className="btn-secondary">
                  <PencilIcon className="h-4 w-4 mr-2" />
                  Edit
                </button>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleToggleStatus(user.id)}
                  className={`btn-secondary ${
                    user.is_active ? 'text-orange-600 hover:text-orange-700' : 'text-green-600 hover:text-green-700'
                  }`}
                >
                  {user.is_active ? 'Deactivate' : 'Activate'}
                </button>
                <button
                  onClick={() => handleDelete(user.id, user.username)}
                  className="btn-secondary text-red-600 hover:text-red-700"
                >
                  <TrashIcon className="h-4 w-4 mr-2" />
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {users.length === 0 && (
        <div className="text-center py-12">
          <UserIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No users found</h3>
          <p className="text-gray-500">Get started by adding your first user.</p>
        </div>
      )}
    </div>
  );
};

export default Users;
