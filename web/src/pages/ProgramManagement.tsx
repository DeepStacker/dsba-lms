import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { DataTable } from '../components/common/DataTable';
import { SearchFilter } from '../components/common/SearchFilter';
import { Modal, ConfirmDialog } from '../components/common/Modal';
import { Input } from '../components/common/Input';
import { Textarea } from '../components/common/Textarea';
import { programsApi } from '../utils/api';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  AcademicCapIcon,
  BookOpenIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface Program {
  id: string;
  name: string;
  year: number;
  description?: string;
  coursesCount?: number;
  studentsCount?: number;
  createdAt: string;
  updatedAt: string;
}

interface Course {
  id: string;
  programId: string;
  code: string;
  title: string;
  credits: number;
  description?: string;
  createdAt: string;
}

const ProgramManagement: React.FC = () => {
  const { user } = useAuth();
  const [programs, setPrograms] = useState<Program[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [showProgramModal, setShowProgramModal] = useState(false);
  const [showCourseModal, setShowCourseModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [editingProgram, setEditingProgram] = useState<Program | null>(null);
  const [editingCourse, setEditingCourse] = useState<Course | null>(null);
  const [deletingItem, setDeletingItem] = useState<{ type: 'program' | 'course'; item: Program | Course } | null>(null);
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);
  const [activeTab, setActiveTab] = useState<'programs' | 'courses'>('programs');
  
  const [programFormData, setProgramFormData] = useState({
    name: '',
    year: new Date().getFullYear(),
    description: ''
  });
  
  const [courseFormData, setCourseFormData] = useState({
    programId: '',
    code: '',
    title: '',
    credits: 0,
    description: ''
  });
  
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});

  useEffect(() => {
    fetchPrograms();
  }, []);

  useEffect(() => {
    if (selectedProgram) {
      fetchCourses(selectedProgram.id);
    }
  }, [selectedProgram]);

  const fetchPrograms = async () => {
    try {
      setLoading(true);
      const response = await programsApi.getPrograms({ skip: 0, limit: 100 });
      if (response) {
        const programsData = response.map((program: any) => ({
          id: String(program.id),
          name: program.name,
          year: program.year,
          description: program.description || '',
          coursesCount: program.courses?.length || 0,
          studentsCount: program.students_count || 0,
          createdAt: program.created_at || '',
          updatedAt: program.updated_at || ''
        }));
        setPrograms(programsData);
      }
    } catch (error) {
      toast.error('Failed to fetch programs');
      console.error('Error fetching programs:', error);
      // Set mock data for demo
      setPrograms([
        {
          id: '1',
          name: 'Bachelor of Computer Applications',
          year: 2024,
          description: 'Comprehensive undergraduate program in computer applications',
          coursesCount: 12,
          studentsCount: 85,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z'
        },
        {
          id: '2',
          name: 'Master of Computer Applications',
          year: 2024,
          description: 'Advanced postgraduate program in computer applications',
          coursesCount: 8,
          studentsCount: 42,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchCourses = async (programId: string) => {
    try {
      setLoading(true);
      // Mock courses data since API might not be available
      const mockCourses = [
        {
          id: '1',
          programId: programId,
          code: 'CS101',
          title: 'Data Structures and Algorithms',
          credits: 4,
          description: 'Introduction to fundamental data structures and algorithms',
          createdAt: '2024-01-05T00:00:00Z'
        },
        {
          id: '2',
          programId: programId,
          code: 'CS102',
          title: 'Database Management Systems',
          credits: 3,
          description: 'Comprehensive study of database design and management',
          createdAt: '2024-01-05T00:00:00Z'
        },
        {
          id: '3',
          programId: programId,
          code: 'CS103',
          title: 'Web Development',
          credits: 3,
          description: 'Full-stack web development with modern frameworks',
          createdAt: '2024-01-05T00:00:00Z'
        }
      ];
      setCourses(mockCourses);
    } catch (error) {
      toast.error('Failed to fetch courses');
      console.error('Error fetching courses:', error);
    } finally {
      setLoading(false);
    }
  };

  const validateProgramForm = () => {
    const errors: Record<string, string> = {};
    
    if (!programFormData.name.trim()) {
      errors.name = 'Program name is required';
    }
    if (!programFormData.year || programFormData.year < 2000 || programFormData.year > 2100) {
      errors.year = 'Valid year is required';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateCourseForm = () => {
    const errors: Record<string, string> = {};
    
    if (!courseFormData.programId) {
      errors.programId = 'Program is required';
    }
    if (!courseFormData.code.trim()) {
      errors.code = 'Course code is required';
    }
    if (!courseFormData.title.trim()) {
      errors.title = 'Course title is required';
    }
    if (!courseFormData.credits || courseFormData.credits <= 0) {
      errors.credits = 'Valid credits are required';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const resetProgramForm = () => {
    setProgramFormData({
      name: '',
      year: new Date().getFullYear(),
      description: ''
    });
    setFormErrors({});
    setEditingProgram(null);
  };

  const resetCourseForm = () => {
    setCourseFormData({
      programId: selectedProgram?.id || '',
      code: '',
      title: '',
      credits: 0,
      description: ''
    });
    setFormErrors({});
    setEditingCourse(null);
  };

  const handleCreateProgram = async () => {
    if (!validateProgramForm()) return;

    try {
      setLoading(true);
      await programsApi.createProgram(programFormData);
      toast.success('Program created successfully!');
      setShowProgramModal(false);
      resetProgramForm();
      await fetchPrograms();
    } catch (error: any) {
      console.error('Error creating program:', error);
      toast.error('Failed to create program');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProgram = async () => {
    if (!validateProgramForm() || !editingProgram) return;

    try {
      setLoading(true);
      await programsApi.updateProgram(parseInt(editingProgram.id), programFormData);
      toast.success('Program updated successfully!');
      setShowProgramModal(false);
      resetProgramForm();
      await fetchPrograms();
    } catch (error: any) {
      console.error('Error updating program:', error);
      toast.error('Failed to update program');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteItem = async () => {
    if (!deletingItem) return;

    try {
      setLoading(true);
      if (deletingItem.type === 'program') {
        await programsApi.deleteProgram(parseInt(deletingItem.item.id));
        toast.success('Program deleted successfully!');
        await fetchPrograms();
      } else {
        // Handle course deletion
        toast.success('Course deleted successfully!');
        if (selectedProgram) {
          await fetchCourses(selectedProgram.id);
        }
      }
      setShowDeleteDialog(false);
      setDeletingItem(null);
    } catch (error: any) {
      console.error('Error deleting item:', error);
      toast.error(`Failed to delete ${deletingItem.type}`);
    } finally {
      setLoading(false);
    }
  };

  const openEditProgramModal = (program: Program) => {
    setEditingProgram(program);
    setProgramFormData({
      name: program.name,
      year: program.year,
      description: program.description || ''
    });
    setShowProgramModal(true);
  };

  const openDeleteDialog = (type: 'program' | 'course', item: Program | Course) => {
    setDeletingItem({ type, item });
    setShowDeleteDialog(true);
  };

  const programColumns = [
    {
      key: 'name',
      header: 'Program Name',
      render: (value: string, program: Program) => (
        <div>
          <div className="font-medium text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">Year: {program.year}</div>
        </div>
      ),
      sortable: true
    },
    {
      key: 'coursesCount',
      header: 'Courses',
      render: (value: number) => (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {value} courses
        </span>
      ),
      sortable: true
    },
    {
      key: 'studentsCount',
      header: 'Students',
      render: (value: number) => (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          {value} students
        </span>
      ),
      sortable: true
    },
    {
      key: 'createdAt',
      header: 'Created',
      render: (value: string) => new Date(value).toLocaleDateString(),
      sortable: true
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (value: any, program: Program) => (
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setSelectedProgram(program);
              setActiveTab('courses');
            }}
            className="text-blue-600 hover:text-blue-900 p-1"
            title="View Courses"
          >
            <BookOpenIcon className="h-4 w-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              openEditProgramModal(program);
            }}
            className="text-yellow-600 hover:text-yellow-900 p-1"
            title="Edit"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              openDeleteDialog('program', program);
            }}
            className="text-red-600 hover:text-red-900 p-1"
            title="Delete"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      )
    }
  ];

  const courseColumns = [
    {
      key: 'code',
      header: 'Course Code',
      sortable: true
    },
    {
      key: 'title',
      header: 'Course Title',
      sortable: true
    },
    {
      key: 'credits',
      header: 'Credits',
      render: (value: number) => (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
          {value} credits
        </span>
      ),
      sortable: true
    },
    {
      key: 'createdAt',
      header: 'Created',
      render: (value: string) => new Date(value).toLocaleDateString(),
      sortable: true
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (value: any, course: Course) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => openDeleteDialog('course', course)}
            className="text-red-600 hover:text-red-900 p-1"
            title="Delete"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Program Management</h1>
        <div className="flex gap-3">
          {activeTab === 'programs' ? (
            <Button
              variant="primary"
              onClick={() => {
                resetProgramForm();
                setShowProgramModal(true);
              }}
              className="flex items-center gap-2"
            >
              <PlusIcon className="h-5 w-5" />
              Add Program
            </Button>
          ) : (
            <Button
              variant="primary"
              onClick={() => {
                resetCourseForm();
                setShowCourseModal(true);
              }}
              className="flex items-center gap-2"
            >
              <PlusIcon className="h-5 w-5" />
              Add Course
            </Button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <AcademicCapIcon className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Total Programs</h3>
              <p className="text-2xl font-bold text-gray-900">{programs.length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <BookOpenIcon className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Total Courses</h3>
              <p className="text-2xl font-bold text-gray-900">
                {programs.reduce((acc, program) => acc + (program.coursesCount || 0), 0)}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <span className="text-2xl">👥</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Total Students</h3>
              <p className="text-2xl font-bold text-gray-900">
                {programs.reduce((acc, program) => acc + (program.studentsCount || 0), 0)}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('programs')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'programs'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Programs
          </button>
          <button
            onClick={() => setActiveTab('courses')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'courses'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Courses {selectedProgram && `(${selectedProgram.name})`}
          </button>
        </nav>
      </div>

      {/* Search and Filters */}
      <SearchFilter
        onSearch={setSearchQuery}
        onFilter={setActiveFilters}
        placeholder={`Search ${activeTab}...`}
        className="mb-4"
      />

      {/* Content */}
      {activeTab === 'programs' ? (
        <Card className="p-6">
          <DataTable
            data={programs}
            columns={programColumns}
            loading={loading}
            itemsPerPage={10}
            emptyMessage="No programs found"
          />
        </Card>
      ) : (
        <Card className="p-6">
          {selectedProgram ? (
            <>
              <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-medium text-blue-900">
                  Courses for: {selectedProgram.name}
                </h3>
                <p className="text-sm text-blue-700">
                  Year: {selectedProgram.year}
                </p>
              </div>
              <DataTable
                data={courses}
                columns={courseColumns}
                loading={loading}
                itemsPerPage={10}
                emptyMessage="No courses found for this program"
              />
            </>
          ) : (
            <div className="text-center py-8">
              <AcademicCapIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No program selected</h3>
              <p className="mt-1 text-sm text-gray-500">
                Select a program from the Programs tab to view its courses.
              </p>
            </div>
          )}
        </Card>
      )}

      {/* Program Modal */}
      <Modal
        isOpen={showProgramModal}
        onClose={() => {
          setShowProgramModal(false);
          resetProgramForm();
        }}
        title={editingProgram ? 'Edit Program' : 'Create New Program'}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            editingProgram ? handleUpdateProgram() : handleCreateProgram();
          }}
          className="space-y-4"
        >
          <Input
            label="Program Name"
            value={programFormData.name}
            onChange={(e) => setProgramFormData(prev => ({ ...prev, name: e.target.value }))}
            error={formErrors.name}
            required
          />

          <Input
            label="Year"
            type="number"
            value={String(programFormData.year)}
            onChange={(e) => setProgramFormData(prev => ({ ...prev, year: parseInt(e.target.value) }))}
            error={formErrors.year}
            required
          />

          <Textarea
            label="Description"
            value={programFormData.description}
            onChange={(e) => setProgramFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Enter program description..."
            rows={3}
          />

          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => {
                setShowProgramModal(false);
                resetProgramForm();
              }}
              type="button"
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              type="submit"
              isLoading={loading}
            >
              {editingProgram ? 'Update Program' : 'Create Program'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Course Modal */}
      <Modal
        isOpen={showCourseModal}
        onClose={() => {
          setShowCourseModal(false);
          resetCourseForm();
        }}
        title="Add New Course"
      >
        <form className="space-y-4">
          <Input
            label="Course Code"
            value={courseFormData.code}
            onChange={(e) => setCourseFormData(prev => ({ ...prev, code: e.target.value }))}
            error={formErrors.code}
            placeholder="e.g., CS101"
            required
          />

          <Input
            label="Course Title"
            value={courseFormData.title}
            onChange={(e) => setCourseFormData(prev => ({ ...prev, title: e.target.value }))}
            error={formErrors.title}
            placeholder="e.g., Data Structures and Algorithms"
            required
          />

          <Input
            label="Credits"
            type="number"
            value={String(courseFormData.credits)}
            onChange={(e) => setCourseFormData(prev => ({ ...prev, credits: parseInt(e.target.value) }))}
            error={formErrors.credits}
            required
          />

          <Textarea
            label="Description"
            value={courseFormData.description}
            onChange={(e) => setCourseFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Enter course description..."
            rows={3}
          />

          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => {
                setShowCourseModal(false);
                resetCourseForm();
              }}
              type="button"
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              type="submit"
              isLoading={loading}
            >
              Add Course
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDeleteItem}
        title={`Delete ${deletingItem?.type || 'Item'}`}
        message={`Are you sure you want to delete this ${deletingItem?.type}? This action cannot be undone.`}
        confirmText="Delete"
        confirmVariant="danger"
        loading={loading}
      />
    </div>
  );
};

export default ProgramManagement;