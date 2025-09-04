import React, { useState, useEffect } from 'react';
import { DataTable } from '../common/DataTable';
import { Button } from '../common/Button';
import { Modal, ConfirmDialog } from '../common/Modal';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Card } from '../common/Card';
import { UserGroupIcon, PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline';
import { usersApi } from '../../utils/api';
import { UserRole } from '../../enums';
import toast from 'react-hot-toast';

interface User {
  id: number;
  username: string;
  email: string;
  name: string;
  role: string;
  department?: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

interface UserFormData {
  username: string;
  email: string;
  name: string;
  role: string;
  department: string;
  password?: string;
}

export const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [formData, setFormData] = useState<UserFormData>({
    username: '',
    email: '',
    name: '',
    role: UserRole.STUDENT,
    department: '',
    password: ''
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const columns = [
    {
      key: 'name',
      header: 'Name',
      sortable: true,
      render: (value: string, user: User) => (
        <div>
          <div className="font-medium text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">{user.email}</div>
        </div>
      )
    },
    {
      key: 'role',
      header: 'Role',
      sortable: true,
      render: (value: string) => (
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          value === 'admin' ? 'bg-purple-100 text-purple-800' :
          value === 'teacher' ? 'bg-blue-100 text-blue-800' :
          value === 'student' ? 'bg-green-100 text-green-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {value.charAt(0).toUpperCase() + value.slice(1)}
        </span>
      )
    },
    {
      key: 'department',
      header: 'Department',
      sortable: true
    },
    {
      key: 'is_active',
      header: 'Status',
      sortable: true,
      render: (value: boolean) => (
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {value ? 'Active' : 'Inactive'}
        </span>
      )
    },
    {
      key: 'created_at',
      header: 'Created',
      sortable: true,
      render: (value: string) => new Date(value).toLocaleDateString()
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (_: any, user: User) => (
        <div className="flex space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleEditUser(user)}
          >
            <PencilIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleDeleteUser(user)}
          >
            <TrashIcon className="h-4 w-4 text-red-500" />
          </Button>
        </div>
      )
    }
  ];

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await usersApi.getUsers();
      setUsers(response.data || []);
    } catch (error) {
      toast.error('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.name.trim()) errors.name = 'Name is required';
    if (!formData.email.trim()) errors.email = 'Email is required';
    if (!formData.username.trim()) errors.username = 'Username is required';
    if (!formData.role) errors.role = 'Role is required';
    if (!selectedUser && !formData.password) errors.password = 'Password is required';

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (formData.email && !emailRegex.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreateUser = () => {
    setFormData({
      username: '',
      email: '',
      name: '',
      role: UserRole.STUDENT,
      department: '',
      password: ''
    });
    setFormErrors({});
    setSelectedUser(null);
    setShowCreateModal(true);
  };

  const handleEditUser = (user: User) => {
    setFormData({
      username: user.username,
      email: user.email,
      name: user.name,
      role: user.role,
      department: user.department || '',
      password: ''
    });
    setFormErrors({});
    setSelectedUser(user);
    setShowEditModal(true);
  };

  const handleDeleteUser = (user: User) => {
    setSelectedUser(user);
    setShowDeleteDialog(true);
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    try {
      if (selectedUser) {
        await usersApi.updateUser(selectedUser.id, formData);
        toast.success('User updated successfully');
        setShowEditModal(false);
      } else {
        await usersApi.createUser(formData);
        toast.success('User created successfully');
        setShowCreateModal(false);
      }
      fetchUsers();
    } catch (error) {
      toast.error(selectedUser ? 'Failed to update user' : 'Failed to create user');
    }
  };

  const handleDelete = async () => {
    if (!selectedUser) return;

    try {
      await usersApi.deleteUser(selectedUser.id);
      toast.success('User deleted successfully');
      setShowDeleteDialog(false);
      fetchUsers();
    } catch (error) {
      toast.error('Failed to delete user');
    }
  };

  const UserForm = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <Input
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            error={formErrors.name}
            placeholder="Enter full name"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <Input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            error={formErrors.email}
            placeholder="Enter email address"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <Input
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            error={formErrors.username}
            placeholder="Enter username"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
          <Select
            value={formData.role}
            onChange={(value) => setFormData({ ...formData, role: value })}
            error={formErrors.role}
            options={[
              { value: UserRole.ADMIN, label: 'Admin' },
              { value: UserRole.TEACHER, label: 'Teacher' },
              { value: UserRole.STUDENT, label: 'Student' },
              { value: UserRole.COORDINATOR, label: 'Coordinator' }
            ]}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
          <Input
            value={formData.department}
            onChange={(e) => setFormData({ ...formData, department: e.target.value })}
            placeholder="Enter department"
          />
        </div>
        {!selectedUser && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <Input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              error={formErrors.password}
              placeholder="Enter password"
            />
          </div>
        )}
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button
          variant="secondary"
          onClick={() => {
            setShowCreateModal(false);
            setShowEditModal(false);
          }}
        >
          Cancel
        </Button>
        <Button variant="primary" onClick={handleSubmit}>
          {selectedUser ? 'Update User' : 'Create User'}
        </Button>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
          <p className="text-gray-600 mt-1">Manage system users and their roles</p>
        </div>
        <Button
          variant="primary"
          onClick={handleCreateUser}
          className="flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Create User
        </Button>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <UserGroupIcon className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">All Users</h2>
          </div>
          <div className="text-sm text-gray-500">
            Total: {users.length} users
          </div>
        </div>

        <DataTable
          data={users}
          columns={columns}
          loading={loading}
          emptyMessage="No users found"
        />
      </Card>

      {/* Create User Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New User"
        size="lg"
      >
        <UserForm />
      </Modal>

      {/* Edit User Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit User"
        size="lg"
      >
        <UserForm />
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDelete}
        title="Delete User"
        message={`Are you sure you want to delete ${selectedUser?.name}? This action cannot be undone.`}
        confirmText="Delete"
        confirmVariant="danger"
      />
    </div>
  );
};