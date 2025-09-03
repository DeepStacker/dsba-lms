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
import { DatePicker } from '../components/common/DatePicker';
import { examsApi, questionsApi } from '../utils/api';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  PlayIcon,
  StopIcon,
  DocumentCheckIcon,
  ClockIcon,
  UsersIcon,
  ClipboardDocumentCheckIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface Exam {
  id: string;
  title: string;
  courseId: string;
  courseName: string;
  description: string;
  duration: number; // in minutes
  totalQuestions: number;
  totalMarks: number;
  status: 'draft' | 'published' | 'ongoing' | 'completed' | 'cancelled';
  scheduledAt: string;
  endsAt?: string;
  instructions: string;
  createdBy: string;
  createdAt: string;
  questionCount: number;
  attemptCount: number;
}

interface Question {
  id: number;
  text: string;
  type: 'mcq' | 'descriptive' | 'code';
  marks: number;
  difficulty: 'easy' | 'medium' | 'hard';
}

const ExamManagement: React.FC = () => {
  const { user } = useAuth();
  const [exams, setExams] = useState<Exam[]>([]);
  const [availableQuestions, setAvailableQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [showExamModal, setShowExamModal] = useState(false);
  const [showQuestionsModal, setShowQuestionsModal] = useState(false);
  const [showPublishDialog, setShowPublishDialog] = useState(false);
  const [editingExam, setEditingExam] = useState<Exam | null>(null);
  const [selectedExam, setSelectedExam] = useState<Exam | null>(null);
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);

  const [examFormData, setExamFormData] = useState({
    title: '',
    courseId: '',
    courseName: '',
    description: '',
    duration: 120,
    scheduledAt: new Date(),
    instructions: '',
    totalQuestions: 50,
    totalMarks: 100
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchExams();
    if (user?.role === 'teacher') {
      fetchAvailableQuestions();
    }
  }, [user]);

  const fetchExams = async () => {
    try {
      setLoading(true);
      const response = await examsApi.getExams();
      if (response) {
        setExams(response.map((exam: any) => ({
          id: String(exam.id),
          title: exam.title,
          courseId: exam.course_id,
          courseName: exam.course_name || 'Unknown Course',
          description: exam.description,
          duration: exam.duration_minutes,
          totalQuestions: exam.total_questions,
          totalMarks: exam.total_marks,
          status: exam.status,
          scheduledAt: exam.scheduled_at,
          endsAt: exam.ends_at,
          instructions: exam.instructions,
          createdBy: exam.created_by,
          createdAt: exam.created_at,
          questionCount: exam.questions?.length || 0,
          attemptCount: exam.attempts_count || 0
        })));
      }
    } catch (error) {
      toast.error('Failed to fetch exams');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableQuestions = async () => {
    try {
      const response = await questionsApi.getQuestions({ limit: 200 });
      if (response) {
        setAvailableQuestions(response);
      }
    } catch (error) {
      toast.error('Failed to fetch questions');
    }
  };

  const validateExamForm = () => {
    const errors: Record<string, string> = {};
    if (!examFormData.title.trim()) errors.title = 'Exam title is required';
    if (!examFormData.courseId) errors.courseId = 'Course is required';
    if (examFormData.duration <= 0) errors.duration = 'Duration must be greater than 0';
    if (examFormData.totalQuestions <= 0) errors.totalQuestions = 'Number of questions must be greater than 0';
    if (examFormData.totalMarks <= 0) errors.totalMarks = 'Total marks must be greater than 0';
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const resetExamForm = () => {
    setExamFormData({
      title: '',
      courseId: '',
      courseName: '',
      description: '',
      duration: 120,
      scheduledAt: new Date(),
      instructions: '',
      totalQuestions: 50,
      totalMarks: 100
    });
    setFormErrors({});
    setEditingExam(null);
  };

  const handleCreateExam = async () => {
    if (!validateExamForm()) return;

    try {
      setLoading(true);
      const newExamData = {
        title: examFormData.title,
        course_id: examFormData.courseId,
        description: examFormData.description,
        duration_minutes: examFormData.duration,
        total_questions: examFormData.totalQuestions,
        total_marks: examFormData.totalMarks,
        scheduled_at: examFormData.scheduledAt.toISOString(),
        instructions: examFormData.instructions
      };

      await examsApi.createExam(newExamData);
      toast.success('Exam created successfully!');
      setShowExamModal(false);
      resetExamForm();
      fetchExams();
    } catch (error) {
      toast.error('Failed to create exam');
    } finally {
      setLoading(false);
    }
  };

  const handlePublishExam = async () => {
    if (!selectedExam) return;

    try {
      setLoading(true);
      await examsApi.publishExam(parseInt(selectedExam.id));
      toast.success('Exam published successfully!');
      setShowPublishDialog(false);
      setSelectedExam(null);
      fetchExams();
    } catch (error) {
      toast.error('Failed to publish exam');
    } finally {
      setLoading(false);
    }
  };

  const handleAddQuestionsToExam = async () => {
    if (!selectedExam || selectedQuestions.length === 0) return;

    try {
      setLoading(true);
      const questionsData = { question_ids: selectedQuestions.map(id => parseInt(id)) };
      await examsApi.addQuestionsToExam(parseInt(selectedExam.id), questionsData);
      toast.success('Questions added to exam successfully!');
      setShowQuestionsModal(false);
      setSelectedQuestions([]);
      fetchExams();
    } catch (error) {
      toast.error('Failed to add questions to exam');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      key: 'title',
      header: 'Exam Title',
      sortable: true
    },
    {
      key: 'courseName',
      header: 'Course',
      sortable: true
    },
    {
      key: 'totalQuestions',
      header: 'Questions',
      render: (value: number) => (
        <div className="flex items-center gap-1">
          <DocumentCheckIcon className="h-4 w-4 text-gray-400" />
          <span>{value}</span>
        </div>
      )
    },
    {
      key: 'duration',
      header: 'Duration',
      render: (value: number) => (
        <div className="flex items-center gap-1">
          <ClockIcon className="h-4 w-4 text-gray-400" />
          <span>{value} min</span>
        </div>
      )
    },
    {
      key: 'scheduledAt',
      header: 'Scheduled',
      render: (value: string) => new Date(value).toLocaleString(),
      sortable: true
    },
    {
      key: 'status',
      header: 'Status',
      render: (value: string) => (
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          value === 'published' ? 'bg-green-100 text-green-800' :
          value === 'ongoing' ? 'bg-blue-100 text-blue-800' :
          value === 'completed' ? 'bg-purple-100 text-purple-800' :
          value === 'cancelled' ? 'bg-red-100 text-red-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {value.charAt(0).toUpperCase() + value.slice(1)}
        </span>
      )
    },
    {
      key: 'attemptCount',
      header: 'Attempts',
      render: (value: number) => (
        <div className="flex items-center gap-1">
          <UsersIcon className="h-4 w-4 text-gray-400" />
          <span>{value}</span>
        </div>
      )
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (value: any, exam: Exam) => (
        <div className="flex items-center gap-2">
          {(exam.status === 'draft' && user?.role !== 'student') && (
            <>
              <button
                onClick={() => {
                  setSelectedExam(exam);
                  setShowQuestionsModal(true);
                }}
                className="text-blue-600 hover:text-blue-900 p-1"
                title="Add Questions"
              >
                <PlusIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => {
                  setSelectedExam(exam);
                  setShowPublishDialog(true);
                }}
                className="text-green-600 hover:text-green-900 p-1"
                title="Publish Exam"
              >
                <PlayIcon className="h-4 w-4" />
              </button>
            </>
          )}
          <button
            onClick={() => {/* View exam details */}}
            className="text-indigo-600 hover:text-indigo-900 p-1"
            title="View Details"
          >
            <EyeIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => {/* Delete exam */}}
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
    { key: 'status', label: 'Status', type: 'select' as const, options: [
      { value: 'draft', label: 'Draft' },
      { value: 'published', label: 'Published' },
      { value: 'ongoing', label: 'Ongoing' },
      { value: 'completed', label: 'Completed' }
    ]},
    { key: 'courseName', label: 'Course', type: 'text' as const }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Exam Management</h1>
        {(user?.role === 'admin' || user?.role === 'teacher') && (
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
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-2xl font-bold text-gray-900">{exams.length}</div>
          <p className="text-sm text-gray-600">Total Exams</p>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-green-900">
            {exams.filter(e => e.status === 'published').length}
          </div>
          <p className="text-sm text-gray-600">Published</p>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-blue-900">
            {exams.filter(e => e.status === 'ongoing').length}
          </div>
          <p className="text-sm text-gray-600">Ongoing</p>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-purple-900">
            {exams.reduce((acc, e) => acc + e.attemptCount, 0)}
          </div>
          <p className="text-sm text-gray-600">Total Attempts</p>
        </Card>
      </div>

      {/* Search and Filters */}
      <SearchFilter
        onSearch={(query) => console.log('Searching exams:', query)}
        onFilter={(filters) => console.log('Applied filters:', filters)}
        filterOptions={filterOptions}
      />

      {/* Exams Table */}
      <Card className="p-6">
        <DataTable
          data={exams}
          columns={columns}
          loading={loading}
          itemsPerPage={10}
          emptyMessage="No exams found"
        />
      </Card>

      {/* Create Exam Modal */}
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Exam Title"
              value={examFormData.title}
              onChange={(e) => setExamFormData(prev => ({ ...prev, title: e.target.value }))}
              error={formErrors.title}
              required
            />

            <Select
              label="Course"
              options={[]} // Would be populated from available courses
              value={examFormData.courseId}
              onChange={(value) => setExamFormData(prev => ({ ...prev, courseId: String(value || '') }))}
              placeholder="Select a course"
            />
          </div>

          <Textarea
            label="Description"
            value={examFormData.description}
            onChange={(e) => setExamFormData(prev => ({ ...prev, description: e.target.value }))}
            rows={3}
          />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Duration (minutes)</label>
              <input
                type="number"
                value={examFormData.duration}
                onChange={(e) => setExamFormData(prev => ({
                  ...prev,
                  duration: parseInt(e.target.value) || 0
                }))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>

            <Input
              label="Total Questions"
              type="number"
              value={examFormData.totalQuestions.toString()}
              onChange={(e) => setExamFormData(prev => ({
                ...prev,
                totalQuestions: parseInt(e.target.value) || 0
              }))}
              required
            />

            <Input
              label="Total Marks"
              type="number"
              value={examFormData.totalMarks.toString()}
              onChange={(e) => setExamFormData(prev => ({
                ...prev,
                totalMarks: parseInt(e.target.value) || 0
              }))}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Scheduled Date & Time</label>
            <input
              type="datetime-local"
              value={examFormData.scheduledAt.toISOString().slice(0, 16)}
              onChange={(e) => setExamFormData(prev => ({
                ...prev,
                scheduledAt: new Date(e.target.value)
              }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              required
            />
          </div>

          <Textarea
            label="Instructions"
            value={examFormData.instructions}
            onChange={(e) => setExamFormData(prev => ({ ...prev, instructions: e.target.value }))}
            rows={4}
            placeholder="Enter exam instructions for students..."
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

      {/* Add Questions Modal */}
      <Modal
        isOpen={showQuestionsModal}
        onClose={() => {
          setShowQuestionsModal(false);
          setSelectedQuestions([]);
        }}
        title={`Add Questions to ${selectedExam?.title}`}
        size="xl"
      >
        <div className="space-y-4">
          <div className="border rounded-lg p-4 max-h-96 overflow-y-auto">
            {availableQuestions.map(question => (
              <div key={question.id} className="flex items-start space-x-3 p-3 border-b border-gray-200 last:border-b-0">
                <input
                  type="checkbox"
                  checked={selectedQuestions.includes(question.id.toString())}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedQuestions(prev => [...prev, question.id.toString()]);
                    } else {
                      setSelectedQuestions(prev => prev.filter(id => id !== question.id.toString()));
                    }
                  }}
                  className="mt-1"
                />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{question.text}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-gray-500">{question.type.toUpperCase()}</span>
                    <span className="text-xs text-gray-500">{question.marks} marks</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      question.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
                      question.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {question.difficulty}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-between items-center pt-4 border-t">
            <div className="text-sm text-gray-600">
              {selectedQuestions.length} questions selected
              {selectedExam && ` (${selectedExam.totalQuestions - selectedExam.questionCount} remaining)`}
            </div>
            <div className="flex gap-3">
              <Button
                variant="secondary"
                onClick={() => {
                  setShowQuestionsModal(false);
                  setSelectedQuestions([]);
                }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleAddQuestionsToExam}
                isLoading={loading}
                disabled={selectedQuestions.length === 0}
              >
                Add Questions
              </Button>
            </div>
          </div>
        </div>
      </Modal>

      {/* Publish Exam Confirmation */}
      <ConfirmDialog
        isOpen={showPublishDialog}
        onClose={() => setShowPublishDialog(false)}
        onConfirm={handlePublishExam}
        title="Publish Exam"
        message={`Are you sure you want to publish "${selectedExam?.title}"? Once published, students will be able to see and attempt the exam.`}
        confirmText="Publish Exam"
        confirmVariant="primary"
        loading={loading}
      />
    </div>
  );
};

export default ExamManagement;
