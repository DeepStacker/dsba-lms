import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { DataTable } from '../components/common/DataTable';
import { SearchFilter } from '../components/common/SearchFilter';
import { Modal, ConfirmDialog } from '../components/common/Modal';
import { Select } from '../components/common/Select';
import { Input } from '../components/common/Input';
import { Textarea } from '../components/common/Textarea';
import { usersApi, apiClient } from '../utils/api';
import {
  UserPlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  KeyIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'teacher' | 'student';
  status: 'active' | 'inactive';
  department?: string;
  enrollmentNumber?: string;
  phoneNumber?: string;
  createdAt: string;
  lastLogin?: string;
}

const UserManagement: React.FC = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [deletingUser, setDeletingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    role: 'student' as User['role'],
    department: '',
    enrollmentNumber: '',
    phoneNumber: '',
    password: '',
    confirmPassword: ''
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Fetch users data
  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await usersApi.getUsers({ skip: 0, limit: 100 });
      if (response) {
        setUsers(response.map((user: any) => ({
          id: String(user.id),
          name: user.full_name || user.name || 'Unknown',
          email: user.email,
          role: user.role as User['role'],
          status: user.is_active ? 'active' : 'inactive',
          department: user.department,
          enrollmentNumber: user.enrollment_number,
          phoneNumber: user.phone_number,
          createdAt: user.created_at || '',
          lastLogin: user.last_login_at
        })));
      }
    } catch (error) {
      toast.error('Failed to fetch users');
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.name.trim()) {
      errors.name = 'Name is required';
    }
    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Invalid email format';
    }
    if (!editingUser && !formData.password) {
      errors.password = 'Password is required';
    }
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    if (formData.role === 'student' && !formData.enrollmentNumber) {
      errors.enrollmentNumber = 'Enrollment number is required for students';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const resetForm = () => {
    setFormData({
      name: '',
      email: '',
      role: 'student',
      department: '',
      enrollmentNumber: '',
      phoneNumber: '',
      password: '',
      confirmPassword: ''
    });
    setFormErrors({});
    setEditingUser(null);
  };

  const handleCreateUser = () => {
    if (!validateForm()) return;

    setLoading(true);
    const newUser: User = {
      id: Date.now().toString(),
      name: formData.name,
      email: formData.email,
      role: formData.role,
      status: 'active',
      department: formData.department,
      phoneNumber: formData.phoneNumber,
      createdAt: new Date().toISOString().split('T')[0]
    };

    setTimeout(() => {
      setUsers(prev => [...prev, newUser]);
      setLoading(false);
      setShowUserModal(false);
      resetForm();
      toast.success('User created successfully!');
    }, 1000);
  };

  const handleUpdateUser = () => {
    if (!validateForm()) return;
    if (!editingUser) return;

    setLoading(true);
    const updatedUser: User = {
      ...editingUser,
      name: formData.name,
      email: formData.email,
      role: formData.role,
      department: formData.department,
      phoneNumber: formData.phoneNumber
    };

    setTimeout(() => {
      setUsers(prev => prev.map(u => u.id === editingUser.id ? updatedUser : u));
      setLoading(false);
      setShowUserModal(false);
      resetForm();
      toast.success('User updated successfully!');
    }, 1000);
  };

  const handleDeleteUser = () => {
    if (!deletingUser) return;

    setLoading(true);
    setTimeout(() => {
      setUsers(prev => prev.filter(u => u.id !== deletingUser.id));
      setLoading(false);
      setShowDeleteDialog(false);
      setDeletingUser(null);
      toast.success('User deleted successfully!');
    }, 1000);
  };

  const openEditModal = (user: User) => {
    setEditingUser(user);
    setFormData({
      name: user.name,
      email: user.email,
      role: user.role,
      department: user.department || '',
      enrollmentNumber: user.enrollmentNumber || '',
      phoneNumber: user.phoneNumber || '',
      password: '',
      confirmPassword: ''
    });
    setShowUserModal(true);
  };

  const openDeleteDialog = (user: User) => {
    setDeletingUser(user);
    setShowDeleteDialog(true);
  };

  const toggleUserStatus = (user: User) => {
    const newStatus = user.status === 'active' ? 'inactive' : 'active';
    setUsers(prev => prev.map(u =>
      u.id === user.id ? { ...u, status: newStatus } : u
    ));
    toast.success(`User ${newStatus === 'active' ? 'activated' : 'deactivated'} successfully!`);
  };

  const columns = [
    {
      key: 'name',
      header: 'Name',
      render: (value: string, user: User) => (
        <div>
          <div className="font-medium text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">{user.email}</div>
        </div>
      ),
      sortable: true
    },
    {
      key: 'role',
      header: 'Role',
      render: (value: string) => (
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          value === 'admin' ? 'bg-red-100 text-red-800' :
          value === 'teacher' ? 'bg-blue-100 text-blue-800' :
          'bg-green-100 text-green-800'
        }`}>
          {value.charAt(0).toUpperCase() + value.slice(1)}
        </span>
      ),
      filterable: true
    },
    {
      key: 'department',
      header: 'Department',
      sortable: true
    },
    {
      key: 'status',
      header: 'Status',
      render: (value: string) => (
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          value === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
        }`}>
          {value.charAt(0).toUpperCase() + value.slice(1)}
        </span>
      ),
      filterable: true
    },
    {
      key: 'lastLogin',
      header: 'Last Login',
      render: (value?: string) => value ? new Date(value).toLocaleDateString() : 'Never',
      sortable: true
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (value: any, user: User) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => openEditModal(user)}
            className="text-blue-600 hover:text-blue-900 p-1"
            title="Edit"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => toggleUserStatus(user)}
            className="text-yellow-600 hover:text-yellow-900 p-1"
            title={user.status === 'active' ? 'Deactivate' : 'Activate'}
          >
            <KeyIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => openDeleteDialog(user)}
            className="text-red-600 hover:text-red-900 p-1"
            title="Delete"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      )
    }
  ];

  const filterOptions = [
    { key: 'role', label: 'Role', type: 'select' as const, options: [
      { value: 'admin', label: 'Admin' },
      { value: 'teacher', label: 'Teacher' },
      { value: 'student', label: 'Student' }
    ]},
    { key: 'status', label: 'Status', type: 'select' as const, options: [
      { value: 'active', label: 'Active' },
      { value: 'inactive', label: 'Inactive' }
    ]},
    { key: 'department', label: 'Department', type: 'text' as const }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
        <Button
          variant="primary"
          onClick={() => {
            resetForm();
            setShowUserModal(true);
          }}
          className="flex items-center gap-2"
        >
          <UserPlusIcon className="h-5 w-5" />
          Add User
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-2xl font-bold text-gray-900">{users.length}</div>
          <p className="text-sm text-gray-600">Total Users</p>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-blue-900">
            {users.filter(u => u.role === 'admin').length}
          </div>
          <p className="text-sm text-gray-600">Admins</p>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-green-900">
            {users.filter(u => u.role === 'teacher').length}
          </div>
          <p className="text-sm text-gray-600">Teachers</p>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-purple-900">
            {users.filter(u => u.role === 'student').length}
          </div>
          <p className="text-sm text-gray-600">Students</p>
        </Card>
      </div>

      {/* Search and Filters */}
      <SearchFilter
        onSearch={(query) => {
          // Implement search logic
          console.log('Searching for:', query);
        }}
        onFilter={(filters) => {
          // Implement filter logic
          console.log('Applied filters:', filters);
        }}
        filterOptions={filterOptions}
        className="mb-4"
      />

      {/* Users Table */}
      <Card className="p-6">
        <DataTable
          data={users}
          columns={columns}
          loading={loading}
          itemsPerPage={10}
          emptyMessage="No users found"
        />
      </Card>

      {/* Create/Edit User Modal */}
      <Modal
        isOpen={showUserModal}
        onClose={() => {
          setShowUserModal(false);
          resetForm();
        }}
        title={editingUser ? 'Edit User' : 'Create New User'}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            editingUser ? handleUpdateUser() : handleCreateUser();
          }}
          className="space-y-4"
        >
          <Input
            label="Full Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            error={formErrors.name}
            required
          />

          <Input
            label="Email Address"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
            error={formErrors.email}
            required
          />

          <Select
            label="Role"
            options={[
              { value: 'student', label: 'Student' },
              { value: 'teacher', label: 'Teacher' },
              { value: 'admin', label: 'Admin' }
            ]}
            value={formData.role}
            onChange={(value) => setFormData(prev => ({ ...prev, role: value as User['role'] }))}
          />

          <Input
            label="Department"
            value={formData.department}
            onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
            required
          />

          {formData.role === 'student' && (
            <Input
              label="Enrollment Number"
              value={formData.enrollmentNumber}
              onChange={(e) => setFormData(prev => ({ ...prev, enrollmentNumber: e.target.value }))}
              error={formErrors.enrollmentNumber}
              required
            />
          )}

          <Input
            label="Phone Number"
            value={formData.phoneNumber}
            onChange={(e) => setFormData(prev => ({ ...prev, phoneNumber: e.target.value }))}
          />

          {!editingUser && (
            <>
              <Input
                label="Password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                error={formErrors.password}
                required
              />

              <Input
                label="Confirm Password"
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                error={formErrors.confirmPassword}
                required
              />
            </>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => {
                setShowUserModal(false);
                resetForm();
              }}
              type="button"
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={editingUser ? handleUpdateUser : handleCreateUser}
              isLoading={loading}
              type="submit"
            >
              {editingUser ? 'Update User' : 'Create User'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDeleteUser}
        title="Delete User"
        message={`Are you sure you want to delete ${deletingUser?.name}? This action cannot be undone.`}
        confirmText="Delete"
        confirmVariant="danger"
        loading={loading}
      />
    </div>
  );
};

export default UserManagement;
