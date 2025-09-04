import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { DataTable } from '../components/common/DataTable';
import { SearchFilter } from '../components/common/SearchFilter';
import { Modal } from '../components/common/Modal';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { Textarea } from '../components/common/Textarea';
import { ExamMonitorCard } from '../components/exam/ExamMonitorCard';
import { examsApi } from '../utils/api';
import {
  PlusIcon,
  PlayIcon,
  StopIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  ClockIcon,
  DocumentCheckIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface Exam {
  id: string;
  title: string;
  course: string;
  startTime: string;
  endTime: string;
  duration: number;
  status: 'draft' | 'published' | 'active' | 'ended';
  totalStudents: number;
  joinedStudents: number;
  submittedStudents: number;
  createdAt: string;
}

const ExamManagement: React.FC = () => {
  const { user } = useAuth();
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(false);
  const [showExamModal, setShowExamModal] = useState(false);
  const [editingExam, setEditingExam] = useState<Exam | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});
  const [currentExams, setCurrentExams] = useState<Exam[]>([]);
  const [activeTab, setActiveTab] = useState<'list' | 'monitor'>('list');

  const [examFormData, setExamFormData] = useState({
    title: '',
    courseId: '',
    startTime: '',
    endTime: '',
    duration: 60,
    instructions: '',
    settings: {
      maxAttempts: 1,
      showResultsImmediately: false,
      allowReview: true,
      randomizeQuestions: false,
      timeLimitEnforced: true,
      proctoringEnabled: false
    }
  });

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchExams();
  }, []);

  useEffect(() => {
    let filteredExams = [...exams];

    if (searchQuery.trim()) {
      filteredExams = filteredExams.filter(exam =>
        exam.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        exam.course.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    Object.entries(activeFilters).forEach(([key, value]) => {
      if (value && value !== '') {
        filteredExams = filteredExams.filter(exam => {
          if (key === 'status') {
            return exam.status === value;
          } else if (key === 'course') {
            return exam.course.toLowerCase().includes(value.toLowerCase());
          }
          return true;
        });
      }
    });

    setCurrentExams(filteredExams);
  }, [exams, searchQuery, activeFilters]);

  const fetchExams = async () => {
    try {
      setLoading(true);
      // Mock data for demonstration
      const mockExams: Exam[] = [
        {
          id: '1',
          title: 'CS101 Midterm Examination',
          course: 'Data Structures and Algorithms',
          startTime: '2024-01-16T10:00:00Z',
          endTime: '2024-01-16T12:00:00Z',
          duration: 120,
          status: 'published',
          totalStudents: 45,
          joinedStudents: 42,
          submittedStudents: 38,
          createdAt: '2024-01-10T00:00:00Z'
        },
        {
          id: '2',
          title: 'Database Systems Quiz',
          course: 'Database Management Systems',
          startTime: '2024-01-17T14:00:00Z',
          endTime: '2024-01-17T15:00:00Z',
          duration: 60,
          status: 'active',
          totalStudents: 38,
          joinedStudents: 35,
          submittedStudents: 12,
          createdAt: '2024-01-12T00:00:00Z'
        },
        {
          id: '3',
          title: 'Web Development Final',
          course: 'Web Development',
          startTime: '2024-01-20T09:00:00Z',
          endTime: '2024-01-20T12:00:00Z',
          duration: 180,
          status: 'draft',
          totalStudents: 32,
          joinedStudents: 0,
          submittedStudents: 0,
          createdAt: '2024-01-15T00:00:00Z'
        }
      ];
      setExams(mockExams);
    } catch (error) {
      toast.error('Failed to fetch exams');
      console.error('Error fetching exams:', error);
    } finally {
      setLoading(false);
    }
  };

  const validateExamForm = () => {
    const errors: Record<string, string> = {};

    if (!examFormData.title.trim()) {
      errors.title = 'Exam title is required';
    }
    if (!examFormData.courseId) {
      errors.courseId = 'Course selection is required';
    }
    if (!examFormData.startTime) {
      errors.startTime = 'Start time is required';
    }
    if (!examFormData.endTime) {
      errors.endTime = 'End time is required';
    }
    if (examFormData.duration <= 0) {
      errors.duration = 'Duration must be greater than 0';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreateExam = async () => {
    if (!validateExamForm()) return;

    try {
      setLoading(true);
      // Mock exam creation
      const newExam: Exam = {
        id: String(Date.now()),
        title: examFormData.title,
        course: 'Selected Course', // Would be resolved from courseId
        startTime: examFormData.startTime,
        endTime: examFormData.endTime,
        duration: examFormData.duration,
        status: 'draft',
        totalStudents: 0,
        joinedStudents: 0,
        submittedStudents: 0,
        createdAt: new Date().toISOString()
      };

      setExams(prev => [newExam, ...prev]);
      toast.success('Exam created successfully!');
      setShowExamModal(false);
      resetExamForm();
    } catch (error: any) {
      console.error('Error creating exam:', error);
      toast.error('Failed to create exam');
    } finally {
      setLoading(false);
    }
  };

  const handleStartExam = async (examId: string) => {
    try {
      setLoading(true);
      // Mock start exam
      setExams(prev => prev.map(exam => 
        exam.id === examId ? { ...exam, status: 'active' as const } : exam
      ));
      toast.success('Exam started successfully!');
    } catch (error) {
      toast.error('Failed to start exam');
    } finally {
      setLoading(false);
    }
  };

  const handleEndExam = async (examId: string) => {
    try {
      setLoading(true);
      // Mock end exam
      setExams(prev => prev.map(exam => 
        exam.id === examId ? { ...exam, status: 'ended' as const } : exam
      ));
      toast.success('Exam ended successfully!');
    } catch (error) {
      toast.error('Failed to end exam');
    } finally {
      setLoading(false);
    }
  };

  const resetExamForm = () => {
    setExamFormData({
      title: '',
      courseId: '',
      startTime: '',
      endTime: '',
      duration: 60,
      instructions: '',
      settings: {
        maxAttempts: 1,
        showResultsImmediately: false,
        allowReview: true,
        randomizeQuestions: false,
        timeLimitEnforced: true,
        proctoringEnabled: false
      }
    });
    setFormErrors({});
    setEditingExam(null);
  };

  const getStatusBadge = (status: Exam['status']) => {
    const statusConfig = {
      draft: 'bg-gray-100 text-gray-800',
      published: 'bg-blue-100 text-blue-800',
      active: 'bg-green-100 text-green-800',
      ended: 'bg-red-100 text-red-800'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusConfig[status]}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const examColumns = [
    {
      key: 'title',
      header: 'Exam Title',
      render: (value: string, exam: Exam) => (
        <div>
          <div className="font-medium text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">{exam.course}</div>
        </div>
      ),
      sortable: true
    },
    {
      key: 'status',
      header: 'Status',
      render: (value: string) => getStatusBadge(value as Exam['status']),
      filterable: true
    },
    {
      key: 'startTime',
      header: 'Start Time',
      render: (value: string) => new Date(value).toLocaleString(),
      sortable: true
    },
    {
      key: 'duration',
      header: 'Duration',
      render: (value: number) => `${value} min`,
      sortable: true
    },
    {
      key: 'totalStudents',
      header: 'Students',
      render: (value: number, exam: Exam) => (
        <div className="text-center">
          <div className="text-sm font-medium">{exam.joinedStudents}/{value}</div>
          <div className="text-xs text-gray-500">joined</div>
        </div>
      ),
      sortable: true
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (value: any, exam: Exam) => (
        <div className="flex items-center gap-2">
          {exam.status === 'draft' && (
            <button
              onClick={() => handleStartExam(exam.id)}
              className="text-green-600 hover:text-green-900 p-1"
              title="Start Exam"
            >
              <PlayIcon className="h-4 w-4" />
            </button>
          )}
          {exam.status === 'active' && (
            <button
              onClick={() => handleEndExam(exam.id)}
              className="text-red-600 hover:text-red-900 p-1"
              title="End Exam"
            >
              <StopIcon className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={() => {}}
            className="text-blue-600 hover:text-blue-900 p-1"
            title="View Details"
          >
            <EyeIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => {}}
            className="text-yellow-600 hover:text-yellow-900 p-1"
            title="Edit"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
        </div>
      )
    }
  ];

  const filterOptions = [
    { 
      key: 'status', 
      label: 'Status', 
      type: 'select' as const, 
      options: [
        { value: 'draft', label: 'Draft' },
        { value: 'published', label: 'Published' },
        { value: 'active', label: 'Active' },
        { value: 'ended', label: 'Ended' }
      ]
    },
    { key: 'course', label: 'Course', type: 'text' as const }
  ];

  const activeExams = exams.filter(exam => exam.status === 'active');

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Exam Management</h1>
        <div className="flex gap-3">
          <Button
            variant="primary"
            onClick={() => {
              resetExamForm();
              setShowExamModal(true);
            }}
            className="flex items-center gap-2"
          >
            <PlusIcon className="h-5 w-5" />
            Create Exam
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <DocumentCheckIcon className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Total Exams</h3>
              <p className="text-2xl font-bold text-gray-900">{exams.length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <PlayIcon className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Active Exams</h3>
              <p className="text-2xl font-bold text-gray-900">
                {exams.filter(e => e.status === 'active').length}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <ClockIcon className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Scheduled</h3>
              <p className="text-2xl font-bold text-gray-900">
                {exams.filter(e => e.status === 'published').length}
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
              <h3 className="text-sm font-medium text-gray-500">Total Participants</h3>
              <p className="text-2xl font-bold text-gray-900">
                {exams.reduce((acc, exam) => acc + exam.totalStudents, 0)}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('list')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'list'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Exam List
          </button>
          <button
            onClick={() => setActiveTab('monitor')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'monitor'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Live Monitor ({activeExams.length})
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'list' ? (
        <>
          <SearchFilter
            onSearch={setSearchQuery}
            onFilter={setActiveFilters}
            filterOptions={filterOptions}
            placeholder="Search exams..."
            className="mb-4"
          />

          <Card className="p-6">
            <DataTable
              data={currentExams}
              columns={examColumns}
              loading={loading}
              itemsPerPage={10}
              emptyMessage="No exams found"
            />
          </Card>
        </>
      ) : (
        <div className="space-y-6">
          {activeExams.length === 0 ? (
            <Card className="p-8 text-center">
              <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No Active Exams</h3>
              <p className="mt-1 text-sm text-gray-500">
                Start an exam to monitor it in real-time.
              </p>
            </Card>
          ) : (
            activeExams.map((exam) => (
              <ExamMonitorCard
                key={exam.id}
                examTitle={exam.title}
                stats={{
                  totalStudents: exam.totalStudents,
                  joined: exam.joinedStudents,
                  active: exam.joinedStudents - exam.submittedStudents,
                  submitted: exam.submittedStudents,
                  flagged: 2 // Mock data
                }}
                timeRemaining="45:32" // Mock data
                status="active"
                onEndExam={() => handleEndExam(exam.id)}
                onViewDetails={() => {}}
              />
            ))
          )}
        </div>
      )}

      {/* Create/Edit Exam Modal */}
      <Modal
        isOpen={showExamModal}
        onClose={() => {
          setShowExamModal(false);
          resetExamForm();
        }}
        title={editingExam ? 'Edit Exam' : 'Create New Exam'}
        size="lg"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleCreateExam();
          }}
          className="space-y-4"
        >
          <Input
            label="Exam Title"
            value={examFormData.title}
            onChange={(e) => setExamFormData(prev => ({ ...prev, title: e.target.value }))}
            error={formErrors.title}
            required
          />

          <Select
            label="Course"
            value={examFormData.courseId}
            onChange={(value) => setExamFormData(prev => ({ ...prev, courseId: value }))}
            options={[
              { value: '1', label: 'Data Structures and Algorithms' },
              { value: '2', label: 'Database Management Systems' },
              { value: '3', label: 'Web Development' }
            ]}
            error={formErrors.courseId}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Start Time"
              type="datetime-local"
              value={examFormData.startTime}
              onChange={(e) => setExamFormData(prev => ({ ...prev, startTime: e.target.value }))}
              error={formErrors.startTime}
              required
            />

            <Input
              label="End Time"
              type="datetime-local"
              value={examFormData.endTime}
              onChange={(e) => setExamFormData(prev => ({ ...prev, endTime: e.target.value }))}
              error={formErrors.endTime}
              required
            />
          </div>

          <Input
            label="Duration (minutes)"
            type="number"
            value={String(examFormData.duration)}
            onChange={(e) => setExamFormData(prev => ({ ...prev, duration: parseInt(e.target.value) }))}
            error={formErrors.duration}
            required
          />

          <Textarea
            label="Instructions"
            value={examFormData.instructions}
            onChange={(e) => setExamFormData(prev => ({ ...prev, instructions: e.target.value }))}
            placeholder="Enter exam instructions for students..."
            rows={3}
          />

          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => {
                setShowExamModal(false);
                resetExamForm();
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
              {editingExam ? 'Update Exam' : 'Create Exam'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ExamManagement;