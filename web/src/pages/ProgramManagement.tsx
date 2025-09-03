import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { DataTable } from '../components/common/DataTable';
import { SearchFilter } from '../components/common/SearchFilter';
import { Modal, ConfirmDialog, FormDialog } from '../components/common/Modal';
import { Select } from '../components/common/Select';
import { Input } from '../components/common/Input';
import { Textarea } from '../components/common/Textarea';
import { FileUpload } from '../components/common/FileUpload';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  BookOpenIcon,

  DocumentCheckIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface Program {
  id: string;
  name: string;
  code: string;
  department: string;
  duration: number;
  durationType: 'semesters' | 'years';
  totalCredits: number;
  description: string;
  status: 'active' | 'inactive';
  syllabus?: string;
  createdAt: string;
  updatedAt: string;
  courseCount: number;
  enrolledStudents: number;
}

interface Course {
  id: string;
  programId: string;
  name: string;
  code: string;
  credits: number;
  semester: number;
  courseType: 'core' | 'elective' | 'lab';
  description: string;
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
  const [selectedProgram, setSelectedProgram] = useState<string | null>(null);
  const [deletingProgram, setDeletingProgram] = useState<Program | null>(null);

  const [programFormData, setProgramFormData] = useState({
    name: '',
    code: '',
    department: '',
    duration: 4,
    durationType: 'semesters' as 'semesters' | 'years',
    totalCredits: 120,
    description: '',
    syllabus: ''
  });

  const [courseFormData, setCourseFormData] = useState({
    name: '',
    code: '',
    credits: 3,
    semester: 1,
    courseType: 'core' as 'core' | 'elective' | 'lab',
    description: ''
  });

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Mock data
  useEffect(() => {
    setLoading(true);
    const mockPrograms: Program[] = [
      {
        id: '1',
        name: 'Bachelor of Computer Science',
        code: 'BCS',
        department: 'Computer Science',
        duration: 8,
        durationType: 'semesters',
        totalCredits: 144,
        description: 'Comprehensive program covering computer science fundamentals and advanced topics',
        status: 'active',
        createdAt: '2023-01-01',
        updatedAt: '2024-01-15',
        courseCount: 28,
        enrolledStudents: 150
      },
      {
        id: '2',
        name: 'Master of Business Administration',
        code: 'MBA',
        department: 'Management',
        duration: 4,
        durationType: 'semesters',
        totalCredits: 96,
        description: 'Professional management education program',
        status: 'active',
        createdAt: '2023-02-01',
        updatedAt: '2024-01-20',
        courseCount: 18,
        enrolledStudents: 80
      }
    ];

    const mockCourses: Course[] = [
      {
        id: '1',
        programId: '1',
        name: 'Data Structures and Algorithms',
        code: 'CS101',
        credits: 4,
        semester: 3,
        courseType: 'core',
        description: 'Fundamental data structures and algorithms'
      },
      {
        id: '2',
        programId: '1',
        name: 'Database Management Systems',
        code: 'CS201',
        credits: 3,
        semester: 5,
        courseType: 'core',
        description: 'Database design and SQL programming'
      }
    ];

    setTimeout(() => {
      setPrograms(mockPrograms);
      setCourses(mockCourses);
      setLoading(false);
    }, 1000);
  }, []);

  const validateProgramForm = () => {
    const errors: Record<string, string> = {};
    if (!programFormData.name.trim()) errors.name = 'Program name is required';
    if (!programFormData.code.trim()) errors.code = 'Program code is required';
    if (!programFormData.department.trim()) errors.department = 'Department is required';
    if (programFormData.duration <= 0) errors.duration = 'Duration must be greater than 0';
    if (programFormData.totalCredits <= 0) errors.totalCredits = 'Total credits must be greater than 0';
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateCourseForm = () => {
    const errors: Record<string, string> = {};
    if (!courseFormData.name.trim()) errors.name = 'Course name is required';
    if (!courseFormData.code.trim()) errors.code = 'Course code is required';
    if (courseFormData.credits <= 0) errors.credits = 'Credits must be greater than 0';
    if (courseFormData.semester <= 0) errors.semester = 'Semester must be greater than 0';
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const resetProgramForm = () => {
    setProgramFormData({
      name: '',
      code: '',
      department: '',
      duration: 4,
      durationType: 'semesters',
      totalCredits: 120,
      description: '',
      syllabus: ''
    });
    setFormErrors({});
    setEditingProgram(null);
  };

  const resetCourseForm = () => {
    setCourseFormData({
      name: '',
      code: '',
      credits: 3,
      semester: 1,
      courseType: 'core',
      description: ''
    });
    setFormErrors({});
    setEditingCourse(null);
  };

  const handleCreateProgram = () => {
    if (!validateProgramForm()) return;
    setLoading(true);
    const newProgram: Program = {
      id: Date.now().toString(),
      ...programFormData,
      status: 'active',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      courseCount: 0,
      enrolledStudents: 0
    };
    setTimeout(() => {
      setPrograms(prev => [...prev, newProgram]);
      setLoading(false);
      setShowProgramModal(false);
      resetProgramForm();
      toast.success('Program created successfully!');
    }, 1000);
  };

  const handleUpdateProgram = () => {
    if (!validateProgramForm()) return;
    if (!editingProgram) return;
    setLoading(true);
    const updatedProgram: Program = {
      ...editingProgram,
      ...programFormData,
      updatedAt: new Date().toISOString()
    };
    setTimeout(() => {
      setPrograms(prev => prev.map(p => p.id === editingProgram.id ? updatedProgram : p));
      setLoading(false);
      setShowProgramModal(false);
      resetProgramForm();
      toast.success('Program updated successfully!');
    }, 1000);
  };

  const handleCreateCourse = () => {
    if (!validateCourseForm()) return;
    if (!selectedProgram) return;
    setLoading(true);
    const newCourse: Course = {
      id: Date.now().toString(),
      programId: selectedProgram,
      ...courseFormData
    };
    setTimeout(() => {
      setCourses(prev => [...prev, newCourse]);
      // Update program course count
      setPrograms(prev => prev.map(p =>
        p.id === selectedProgram ? { ...p, courseCount: p.courseCount + 1 } : p
      ));
      setLoading(false);
      setShowCourseModal(false);
      resetCourseForm();
      toast.success('Course created successfully!');
    }, 1000);
  };

  const handleUpdateCourse = () => {
    if (!validateCourseForm()) return;
    if (!editingCourse) return;
    setLoading(true);
    const updatedCourse: Course = {
      ...editingCourse,
      ...courseFormData
    };
    setTimeout(() => {
      setCourses(prev => prev.map(c => c.id === editingCourse.id ? updatedCourse : c));
      setLoading(false);
      setShowCourseModal(false);
      resetCourseForm();
      toast.success('Course updated successfully!');
    }, 1000);
  };

  const handleDeleteProgram = () => {
    if (!deletingProgram) return;
    setLoading(true);
    setTimeout(() => {
      setPrograms(prev => prev.filter(p => p.id !== deletingProgram.id));
      // Also remove associated courses
      setCourses(prev => prev.filter(c => c.programId !== deletingProgram.id));
      setLoading(false);
      setShowDeleteDialog(false);
      setDeletingProgram(null);
      toast.success('Program deleted successfully!');
    }, 1000);
  };

  const openEditProgram = (program: Program) => {
    setEditingProgram(program);
    setProgramFormData({
      name: program.name,
      code: program.code,
      department: program.department,
      duration: program.duration,
      durationType: program.durationType,
      totalCredits: program.totalCredits,
      description: program.description,
      syllabus: program.syllabus || ''
    });
    setShowProgramModal(true);
  };

  const openEditCourse = (course: Course) => {
    setEditingCourse(course);
    setCourseFormData({
      name: course.name,
      code: course.code,
      credits: course.credits,
      semester: course.semester,
      courseType: course.courseType,
      description: course.description
    });
    setShowCourseModal(true);
  };

  const openDeleteProgram = (program: Program) => {
    setDeletingProgram(program);
    setShowDeleteDialog(true);
  };

  const getFilteredCourses = () => {
    return selectedProgram ? courses.filter(c => c.programId === selectedProgram) : [];
  };

  const programColumns = [
    {
      key: 'code',
      header: 'Code',
      sortable: true
    },
    {
      key: 'name',
      header: 'Program Name',
      sortable: true
    },
    {
      key: 'department',
      header: 'Department',
      sortable: true
    },
    {
      key: 'duration',
      header: 'Duration',
      render: (value: number, program: Program) => `${value} ${program.durationType}`,
      sortable: true
    },
    {
      key: 'totalCredits',
      header: 'Credits',
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
      )
    },
    {
      key: 'courseCount',
      header: 'Courses',
      render: (value: number) => (
        <div className="flex items-center gap-1">
          <BookOpenIcon className="h-4 w-4 text-gray-400" />
          <span>{value}</span>
        </div>
      )
    },
    {
      key: 'enrolledStudents',
      header: 'Students',
      render: (value: number) => (
        <div className="flex items-center gap-1">
          <span className="text-gray-400">👥</span>
          <span>{value}</span>
        </div>
      )
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (value: any, program: Program) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSelectedProgram(program.id)}
            className="text-blue-600 hover:text-blue-900 p-1"
            title="View Courses"
          >
            <EyeIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => openEditProgram(program)}
            className="text-indigo-600 hover:text-indigo-900 p-1"
            title="Edit"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => openDeleteProgram(program)}
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
      header: 'Code',
      sortable: true
    },
    {
      key: 'name',
      header: 'Course Name',
      sortable: true
    },
    {
      key: 'semester',
      header: 'Semester',
      sortable: true
    },
    {
      key: 'courseType',
      header: 'Type',
      render: (value: string) => (
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          value === 'core' ? 'bg-blue-100 text-blue-800' :
          value === 'elective' ? 'bg-green-100 text-green-800' :
          'bg-orange-100 text-orange-800'
        }`}>
          {value.charAt(0).toUpperCase() + value.slice(1)}
        </span>
      )
    },
    {
      key: 'credits',
      header: 'Credits',
      render: (value: number) => (
        <div className="flex items-center justify-between min-w-16">
          <DocumentCheckIcon className="h-4 w-4 text-gray-400" />
          <span>{value}</span>
        </div>
      )
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (value: any, course: Course) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => openEditCourse(course)}
            className="text-indigo-600 hover:text-indigo-900 p-1"
            title="Edit"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => {
              setCourses(prev => prev.filter(c => c.id !== course.id));
              // Update program course count
              setPrograms(prev => prev.map(p =>
                p.id === course.programId ? { ...p, courseCount: p.courseCount - 1 } : p
              ));
              toast.success('Course deleted successfully!');
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

  const programFilterOptions = [
    { key: 'department', label: 'Department', type: 'select' as const, options: [
      { value: 'Computer Science', label: 'Computer Science' },
      { value: 'Management', label: 'Management' },
      { value: 'Engineering', label: 'Engineering' }
    ]},
    { key: 'status', label: 'Status', type: 'select' as const, options: [
      { value: 'active', label: 'Active' },
      { value: 'inactive', label: 'Inactive' }
    ]},
    { key: 'durationType', label: 'Duration Type', type: 'select' as const, options: [
      { value: 'semesters', label: 'Semesters' },
      { value: 'years', label: 'Years' }
    ]}
  ];

  const selectedProgramData = programs.find(p => p.id === selectedProgram);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Program Management</h1>
          {selectedProgramData && (
            <p className="text-gray-600 mt-1">
              Managing: <span className="font-medium">{selectedProgramData.name}</span>
            </p>
          )}
        </div>
        <div className="flex gap-3">
          {!selectedProgram && (
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
          )}
          {selectedProgram && (
            <Button
              variant="secondary"
              onClick={() => setSelectedProgram(null)}
            >
              Back to Programs
            </Button>
          )}
          {selectedProgram && (
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

      {!selectedProgram ? (
        <>
          {/* Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="text-2xl font-bold text-gray-900">{programs.length}</div>
              <p className="text-sm text-gray-600">Total Programs</p>
            </Card>
            <Card className="p-4">
              <div className="text-2xl font-bold text-blue-900">
                {programs.reduce((acc, p) => acc + p.courseCount, 0)}
              </div>
              <p className="text-sm text-gray-600">Total Courses</p>
            </Card>
            <Card className="p-4">
              <div className="text-2xl font-bold text-green-900">
                {programs.reduce((acc, p) => acc + p.enrolledStudents, 0)}
              </div>
              <p className="text-sm text-gray-600">Enrolled Students</p>
            </Card>
            <Card className="p-4">
              <div className="text-2xl font-bold text-purple-900">
                {programs.filter(p => p.status === 'active').length}
              </div>
              <p className="text-sm text-gray-600">Active Programs</p>
            </Card>
          </div>

          {/* Search and Filters */}
          <SearchFilter
            onSearch={(query) => console.log('Searching:', query)}
            onFilter={(filters) => console.log('Applied filters:', filters)}
            filterOptions={programFilterOptions}
          />

          {/* Programs Table */}
          <Card className="p-6">
            <DataTable
              data={programs}
              columns={programColumns}
              loading={loading}
              itemsPerPage={10}
              emptyMessage="No programs found"
            />
          </Card>
        </>
      ) : (
        /* Courses View */
        <Card className="p-6">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Courses in {selectedProgramData?.name}
            </h2>
            <p className="text-gray-600 mt-1">
              {getFilteredCourses().length} courses • {getFilteredCourses().reduce((acc, c) => acc + c.credits, 0)} total credits
            </p>
          </div>
          <DataTable
            data={getFilteredCourses()}
            columns={courseColumns}
            loading={loading}
            itemsPerPage={15}
            emptyMessage="No courses found in this program"
          />
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
        size="lg"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            editingProgram ? handleUpdateProgram() : handleCreateProgram();
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Program Name"
              value={programFormData.name}
              onChange={(e) => setProgramFormData(prev => ({ ...prev, name: e.target.value }))}
              error={formErrors.name}
              required
            />

            <Input
              label="Program Code"
              value={programFormData.code}
              onChange={(e) => setProgramFormData(prev => ({ ...prev, code: e.target.value }))}
              error={formErrors.code}
              required
            />
          </div>

          <Input
            label="Department"
            value={programFormData.department}
            onChange={(e) => setProgramFormData(prev => ({ ...prev, department: e.target.value }))}
            error={formErrors.department}
            required
          />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Duration"
              type="number"
              value={programFormData.duration.toString()}
              onChange={(e) => setProgramFormData(prev => ({
                ...prev,
                duration: parseInt(e.target.value) || 0
              }))}
              error={formErrors.duration}
              required
            />

            <Select
              label="Duration Type"
              options={[
                { value: 'semesters', label: 'Semesters' },
                { value: 'years', label: 'Years' }
              ]}
              value={programFormData.durationType}
              onChange={(value) => setProgramFormData(prev => ({
                ...prev,
                durationType: value as 'semesters' | 'years'
              }))}
            />

            <Input
              label="Total Credits"
              type="number"
              value={programFormData.totalCredits.toString()}
              onChange={(e) => setProgramFormData(prev => ({
                ...prev,
                totalCredits: parseInt(e.target.value) || 0
              }))}
              error={formErrors.totalCredits}
              required
            />
          </div>

          <Textarea
            label="Description"
            value={programFormData.description}
            onChange={(e) => setProgramFormData(prev => ({ ...prev, description: e.target.value }))}
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
              onClick={editingProgram ? handleUpdateProgram : handleCreateProgram}
              isLoading={loading}
              type="submit"
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
        title={editingCourse ? 'Edit Course' : 'Add New Course'}
        size="lg"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            editingCourse ? handleUpdateCourse() : handleCreateCourse();
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Course Name"
              value={courseFormData.name}
              onChange={(e) => setCourseFormData(prev => ({ ...prev, name: e.target.value }))}
              error={formErrors.name}
              required
            />

            <Input
              label="Course Code"
              value={courseFormData.code}
              onChange={(e) => setCourseFormData(prev => ({ ...prev, code: e.target.value }))}
              error={formErrors.code}
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Semester"
              type="number"
              value={courseFormData.semester.toString()}
              onChange={(e) => setCourseFormData(prev => ({
                ...prev,
                semester: parseInt(e.target.value) || 0
              }))}
              error={formErrors.semester}
              required
            />

            <Select
              label="Course Type"
              options={[
                { value: 'core', label: 'Core' },
                { value: 'elective', label: 'Elective' },
                { value: 'lab', label: 'Lab' }
              ]}
              value={courseFormData.courseType}
              onChange={(value) => setCourseFormData(prev => ({
                ...prev,
                courseType: value as 'core' | 'elective' | 'lab'
              }))}
            />

            <Input
              label="Credits"
              type="number"
              value={courseFormData.credits.toString()}
              onChange={(e) => setCourseFormData(prev => ({
                ...prev,
                credits: parseInt(e.target.value) || 0
              }))}
              error={formErrors.credits}
              required
            />
          </div>

          <Textarea
            label="Description"
            value={courseFormData.description}
            onChange={(e) => setCourseFormData(prev => ({ ...prev, description: e.target.value }))}
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
              onClick={editingCourse ? handleUpdateCourse : handleCreateCourse}
              isLoading={loading}
              type="submit"
            >
              {editingCourse ? 'Update Course' : 'Add Course'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDeleteProgram}
        title="Delete Program"
        message={`Are you sure you want to delete "${deletingProgram?.name}"? This action cannot be undone and will also delete all associated courses.`}
        confirmText="Delete Program"
        confirmVariant="danger"
        loading={loading}
      />
    </div>
  );
};

export default ProgramManagement;
