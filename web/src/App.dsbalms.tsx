import React, { useState } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Import components for preview
import { Button } from './components/common/Button';
import { Input } from './components/common/Input';
import { Modal } from './components/common/Modal';
import { DataTable } from './components/common/DataTable';
import { ExamInterface } from './components/exam/ExamInterface';
import { QuestionRenderer } from './components/exam/QuestionRenderer';

// Import icons
import { 
  ChartBarIcon, 
  DocumentDuplicateIcon, 
  RocketLaunchIcon,
  UserGroupIcon,
  AcademicCapIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

// Mock data for preview
const mockUser = {
  id: 1,
  name: 'Dr. Sarah Johnson',
  email: 'sarah.johnson@university.edu',
  role: 'admin' as const,
  username: 'sarah.johnson',
  is_active: true,
  department: 'Computer Science',
  created_at: '2024-01-15T10:00:00Z'
};

const mockExam = {
  id: 1,
  title: 'Data Structures and Algorithms - Midterm Exam',
  start_at: '2024-02-15T10:00:00Z',
  end_at: '2024-02-15T12:00:00Z',
  status: 'published' as const,
  class_id: 1,
  join_window_sec: 300
};

const mockQuestion = {
  id: 1,
  text: 'What is the time complexity of binary search in a sorted array?',
  type: 'mcq' as const,
  max_marks: 5,
  order: 1,
  options: [
    { id: 1, text: 'O(n)', is_correct: false },
    { id: 2, text: 'O(log n)', is_correct: true },
    { id: 3, text: 'O(n²)', is_correct: false },
    { id: 4, text: 'O(1)', is_correct: false }
  ],
  co: {
    code: 'CO1',
    title: 'Understand fundamental data structures'
  }
};

const mockTableData = [
  { id: 1, name: 'Alice Johnson', email: 'alice@university.edu', role: 'student', status: 'active' },
  { id: 2, name: 'Bob Smith', email: 'bob@university.edu', role: 'student', status: 'active' },
  { id: 3, name: 'Dr. Carol Wilson', email: 'carol@university.edu', role: 'teacher', status: 'active' },
  { id: 4, name: 'David Brown', email: 'david@university.edu', role: 'student', status: 'inactive' }
];

const mockTableColumns = [
  { key: 'name' as const, label: 'Name', sortable: true },
  { key: 'email' as const, label: 'Email', sortable: true },
  { key: 'role' as const, label: 'Role', sortable: true },
  { 
    key: 'status' as const, 
    label: 'Status', 
    render: (value: string) => (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
        value === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
      }`}>
        {value}
      </span>
    )
  }
];

// Component showcase sections
const ButtonShowcase: React.FC = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-900">Button Components</h2>
    
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div className="space-y-3">
        <h3 className="text-lg font-semibold">Primary Buttons</h3>
        <div className="space-y-2">
          <Button variant="primary" size="sm">Small Primary</Button>
          <Button variant="primary" size="md">Medium Primary</Button>
          <Button variant="primary" size="lg">Large Primary</Button>
        </div>
      </div>
      
      <div className="space-y-3">
        <h3 className="text-lg font-semibold">Secondary Buttons</h3>
        <div className="space-y-2">
          <Button variant="secondary" size="sm">Small Secondary</Button>
          <Button variant="secondary" size="md">Medium Secondary</Button>
          <Button variant="secondary" size="lg">Large Secondary</Button>
        </div>
      </div>
      
      <div className="space-y-3">
        <h3 className="text-lg font-semibold">Status Buttons</h3>
        <div className="space-y-2">
          <Button variant="success">Success</Button>
          <Button variant="warning">Warning</Button>
          <Button variant="danger">Danger</Button>
          <Button variant="ghost">Ghost</Button>
        </div>
      </div>
    </div>
    
    <div className="space-y-3">
      <h3 className="text-lg font-semibold">Loading & Disabled States</h3>
      <div className="flex space-x-3">
        <Button variant="primary" isLoading>Loading...</Button>
        <Button variant="secondary" disabled>Disabled</Button>
      </div>
    </div>
  </div>
);

const InputShowcase: React.FC = () => {
  const [values, setValues] = useState({
    basic: '',
    email: '',
    password: '',
    error: '',
    success: 'Valid input'
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Input Components</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <Input
            label="Basic Input"
            placeholder="Enter text here"
            value={values.basic}
            onChange={(value) => setValues(prev => ({ ...prev, basic: value }))}
          />
          
          <Input
            label="Email Input"
            type="email"
            placeholder="user@example.com"
            value={values.email}
            onChange={(value) => setValues(prev => ({ ...prev, email: value }))}
            leftIcon={UserGroupIcon}
          />
          
          <Input
            label="Password Input"
            type="password"
            placeholder="Enter password"
            value={values.password}
            onChange={(value) => setValues(prev => ({ ...prev, password: value }))}
            required
          />
        </div>
        
        <div className="space-y-4">
          <Input
            label="Input with Error"
            placeholder="This has an error"
            value={values.error}
            onChange={(value) => setValues(prev => ({ ...prev, error: value }))}
            error="This field is required"
          />
          
          <Input
            label="Input with Success"
            placeholder="This is valid"
            value={values.success}
            onChange={(value) => setValues(prev => ({ ...prev, success: value }))}
            success="Input is valid"
          />
          
          <Input
            label="Disabled Input"
            placeholder="This is disabled"
            value="Cannot edit"
            disabled
          />
        </div>
      </div>
    </div>
  );
};

const ModalShowcase: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [modalType, setModalType] = useState<'basic' | 'actions' | 'large'>('basic');

  const renderModalContent = () => {
    switch (modalType) {
      case 'basic':
        return (
          <Modal
            isOpen={isOpen}
            onClose={() => setIsOpen(false)}
            title="Basic Modal"
          >
            <p className="text-gray-700">
              This is a basic modal with a title and close button. 
              It demonstrates the modal component functionality.
            </p>
          </Modal>
        );
      
      case 'actions':
        return (
          <Modal
            isOpen={isOpen}
            onClose={() => setIsOpen(false)}
            title="Modal with Actions"
            actions={[
              { label: 'Cancel', onClick: () => setIsOpen(false), variant: 'secondary' },
              { label: 'Save', onClick: () => setIsOpen(false), variant: 'primary' },
              { label: 'Delete', onClick: () => setIsOpen(false), variant: 'danger' }
            ]}
          >
            <p className="text-gray-700">
              This modal includes action buttons in the footer.
            </p>
          </Modal>
        );
      
      case 'large':
        return (
          <Modal
            isOpen={isOpen}
            onClose={() => setIsOpen(false)}
            title="Large Modal"
            size="xl"
          >
            <div className="space-y-4">
              <p className="text-gray-700">
                This is a large modal that can contain more content.
              </p>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Example Content</h4>
                <p className="text-sm text-gray-600">
                  Large modals are useful for forms, detailed information, or complex interactions.
                </p>
              </div>
            </div>
          </Modal>
        );
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Modal Components</h2>
      
      <div className="flex space-x-3">
        <Button 
          variant="primary" 
          onClick={() => { setModalType('basic'); setIsOpen(true); }}
        >
          Basic Modal
        </Button>
        <Button 
          variant="secondary" 
          onClick={() => { setModalType('actions'); setIsOpen(true); }}
        >
          Modal with Actions
        </Button>
        <Button 
          variant="ghost" 
          onClick={() => { setModalType('large'); setIsOpen(true); }}
        >
          Large Modal
        </Button>
      </div>
      
      {renderModalContent()}
    </div>
  );
};

const DataTableShowcase: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);

  const filteredData = mockTableData.filter(item =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Data Table Component</h2>
      
      <DataTable
        data={filteredData}
        columns={mockTableColumns}
        searchable
        searchPlaceholder="Search users..."
        onSearch={setSearchQuery}
        onSort={(key, direction) => setSortConfig({ key, direction })}
        actions={[
          {
            label: 'Edit',
            onClick: (item) => alert(`Edit ${item.name}`),
            variant: 'secondary'
          },
          {
            label: 'Delete',
            onClick: (item) => alert(`Delete ${item.name}`),
            variant: 'danger',
            show: (item) => item.role !== 'admin'
          }
        ]}
        pagination={{
          page: 1,
          limit: 10,
          total: filteredData.length,
          onPageChange: (page) => console.log('Page:', page),
          onLimitChange: (limit) => console.log('Limit:', limit)
        }}
      />
    </div>
  );
};

const QuestionShowcase: React.FC = () => {
  const [response, setResponse] = useState<any>({});

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Question Renderer Component</h2>
      
      <div className="bg-gray-50 p-6 rounded-lg">
        <h3 className="text-lg font-semibold mb-4">Sample MCQ Question</h3>
        <QuestionRenderer
          question={mockQuestion}
          response={response}
          onResponseChange={setResponse}
        />
        
        {response.selectedOption && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              Selected Answer: Option {mockQuestion.options.find(opt => opt.id === response.selectedOption)?.text}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

const DashboardPreview: React.FC = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-900">Dashboard Preview</h2>
    
    {/* Stats Cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center">
          <div className="p-2 bg-blue-100 rounded-lg">
            <UserGroupIcon className="h-8 w-8 text-blue-600" />
          </div>
          <div className="ml-4">
            <h3 className="text-sm font-medium text-gray-500">Total Users</h3>
            <p className="text-2xl font-bold text-gray-900">1,234</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center">
          <div className="p-2 bg-green-100 rounded-lg">
            <DocumentDuplicateIcon className="h-8 w-8 text-green-600" />
          </div>
          <div className="ml-4">
            <h3 className="text-sm font-medium text-gray-500">Active Exams</h3>
            <p className="text-2xl font-bold text-gray-900">8</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center">
          <div className="p-2 bg-purple-100 rounded-lg">
            <AcademicCapIcon className="h-8 w-8 text-purple-600" />
          </div>
          <div className="ml-4">
            <h3 className="text-sm font-medium text-gray-500">Questions</h3>
            <p className="text-2xl font-bold text-gray-900">2,840</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center">
          <div className="p-2 bg-orange-100 rounded-lg">
            <ClockIcon className="h-8 w-8 text-orange-600" />
          </div>
          <div className="ml-4">
            <h3 className="text-sm font-medium text-gray-500">Pending Grades</h3>
            <p className="text-2xl font-bold text-gray-900">156</p>
          </div>
        </div>
      </div>
    </div>
    
    {/* Quick Actions */}
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        <Button variant="primary" className="justify-start">
          <UserGroupIcon className="h-5 w-5 mr-2" />
          Manage Users
        </Button>
        <Button variant="secondary" className="justify-start">
          <RocketLaunchIcon className="h-5 w-5 mr-2" />
          AI Question Generator
        </Button>
        <Button variant="secondary" className="justify-start">
          <DocumentDuplicateIcon className="h-5 w-5 mr-2" />
          Create Exam
        </Button>
        <Button variant="secondary" className="justify-start">
          <ChartBarIcon className="h-5 w-5 mr-2" />
          View Analytics
        </Button>
      </div>
    </div>
  </div>
);

const App: React.FC = () => {
  const [activeSection, setActiveSection] = useState('dashboard');

  const sections = [
    { id: 'dashboard', label: 'Dashboard Preview', component: DashboardPreview },
    { id: 'buttons', label: 'Buttons', component: ButtonShowcase },
    { id: 'inputs', label: 'Inputs', component: InputShowcase },
    { id: 'modals', label: 'Modals', component: ModalShowcase },
    { id: 'tables', label: 'Data Tables', component: DataTableShowcase },
    { id: 'questions', label: 'Question Renderer', component: QuestionShowcase }
  ];

  const ActiveComponent = sections.find(s => s.id === activeSection)?.component || DashboardPreview;

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">DSBA LMS</h1>
                <p className="text-gray-600">AI-Powered Learning Management System</p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <img
                    src="https://i.pravatar.cc/40?img=1"
                    alt="User Avatar"
                    className="w-10 h-10 rounded-full"
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{mockUser.name}</p>
                    <p className="text-xs text-gray-500">{mockUser.role}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Navigation */}
        <nav className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex space-x-8">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeSection === section.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {section.label}
                </button>
              ))}
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <ActiveComponent />
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="text-center text-gray-500">
              <p>&copy; 2024 DSBA LMS. AI-Powered Learning Management System.</p>
              <p className="text-sm mt-1">
                Complete implementation with real backend integration, state management, and modern UI components.
              </p>
            </div>
          </div>
        </footer>

        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#ffffff',
              color: '#374151',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            },
          }}
        />
      </div>
    </Router>
  );
};

export default App;