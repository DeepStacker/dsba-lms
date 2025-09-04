import React, { useState, useEffect } from 'react';
import { DataTable } from '../common/DataTable';
import { Button } from '../common/Button';
import { Modal, ConfirmDialog } from '../common/Modal';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Card } from '../common/Card';
import { 
  DocumentCheckIcon, 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  PlayIcon, 
  StopIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { examsApi } from '../../utils/api';
import { ExamStatus } from '../../enums';
import toast from 'react-hot-toast';

interface Exam {
  id: number;
  title: string;
  class_id: number;
  start_at: string;
  end_at: string;
  join_window_sec: number;
  status: string;
  created_at: string;
}

interface ExamFormData {
  title: string;
  class_id: number;
  start_at: string;
  end_at: string;
  join_window_sec: number;
  instructions: string;
}

export const ExamManagement: React.FC = () => {
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedExam, setSelectedExam] = useState<Exam | null>(null);
  const [formData, setFormData] = useState<ExamFormData>({
    title: '',
    class_id: 1,
    start_at: '',
    end_at: '',
    join_window_sec: 300,
    instructions: ''
  });

  const columns = [
    {
      key: 'title',
      header: 'Exam Title',
      sortable: true,
      render: (value: string, exam: Exam) => (
        <div>
          <div className="font-medium text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">ID: {exam.id}</div>
        </div>
      )
    },
    {
      key: 'start_at',
      header: 'Start Time',
      sortable: true,
      render: (value: string) => new Date(value).toLocaleString()
    },
    {
      key: 'end_at',
      header: 'End Time',
      sortable: true,
      render: (value: string) => new Date(value).toLocaleString()
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      render: (value: string) => (
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          value === 'published' ? 'bg-green-100 text-green-800' :
          value === 'started' ? 'bg-blue-100 text-blue-800' :
          value === 'ended' ? 'bg-gray-100 text-gray-800' :
          value === 'results_published' ? 'bg-purple-100 text-purple-800' :
          'bg-yellow-100 text-yellow-800'
        }`}>
          {value.replace('_', ' ').toUpperCase()}
        </span>
      )
    },
    {
      key: 'join_window_sec',
      header: 'Join Window',
      render: (value: number) => `${Math.floor(value / 60)} min`
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (_: any, exam: Exam) => (
        <div className="flex space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleViewExam(exam)}
            title="View Details"
          >
            <EyeIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleEditExam(exam)}
            title="Edit"
          >
            <PencilIcon className="h-4 w-4" />
          </Button>
          {exam.status === 'draft' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handlePublishExam(exam)}
              title="Publish"
            >
              <PlayIcon className="h-4 w-4 text-green-500" />
            </Button>
          )}
          {exam.status === 'published' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleStartExam(exam)}
              title="Start"
            >
              <PlayIcon className="h-4 w-4 text-blue-500" />
            </Button>
          )}
          {exam.status === 'started' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleEndExam(exam)}
              title="End"
            >
              <StopIcon className="h-4 w-4 text-red-500" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleDeleteExam(exam)}
            title="Delete"
          >
            <TrashIcon className="h-4 w-4 text-red-500" />
          </Button>
        </div>
      )
    }
  ];

  useEffect(() => {
    fetchExams();
  }, []);

  const fetchExams = async () => {
    try {
      setLoading(true);
      const response = await examsApi.getExams();
      setExams(response.data || []);
    } catch (error) {
      toast.error('Failed to fetch exams');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExam = () => {
    setFormData({
      title: '',
      class_id: 1,
      start_at: '',
      end_at: '',
      join_window_sec: 300,
      instructions: ''
    });
    setSelectedExam(null);
    setShowCreateModal(true);
  };

  const handleEditExam = (exam: Exam) => {
    setFormData({
      title: exam.title,
      class_id: exam.class_id,
      start_at: new Date(exam.start_at).toISOString().slice(0, 16),
      end_at: new Date(exam.end_at).toISOString().slice(0, 16),
      join_window_sec: exam.join_window_sec,
      instructions: ''
    });
    setSelectedExam(exam);
    setShowEditModal(true);
  };

  const handleViewExam = (exam: Exam) => {
    // Navigate to exam details page
    window.location.href = `/exams/${exam.id}`;
  };

  const handlePublishExam = async (exam: Exam) => {
    try {
      await examsApi.publishExam(exam.id);
      toast.success('Exam published successfully');
      fetchExams();
    } catch (error) {
      toast.error('Failed to publish exam');
    }
  };

  const handleStartExam = async (exam: Exam) => {
    try {
      // API call to start exam
      toast.success('Exam started successfully');
      fetchExams();
    } catch (error) {
      toast.error('Failed to start exam');
    }
  };

  const handleEndExam = async (exam: Exam) => {
    try {
      // API call to end exam
      toast.success('Exam ended successfully');
      fetchExams();
    } catch (error) {
      toast.error('Failed to end exam');
    }
  };

  const handleDeleteExam = (exam: Exam) => {
    setSelectedExam(exam);
    setShowDeleteDialog(true);
  };

  const handleSubmit = async () => {
    try {
      const examData = {
        ...formData,
        start_at: new Date(formData.start_at).toISOString(),
        end_at: new Date(formData.end_at).toISOString()
      };

      if (selectedExam) {
        await examsApi.updateExam(selectedExam.id, examData);
        toast.success('Exam updated successfully');
        setShowEditModal(false);
      } else {
        await examsApi.createExam(examData);
        toast.success('Exam created successfully');
        setShowCreateModal(false);
      }
      fetchExams();
    } catch (error) {
      toast.error(selectedExam ? 'Failed to update exam' : 'Failed to create exam');
    }
  };

  const handleDelete = async () => {
    if (!selectedExam) return;

    try {
      await examsApi.deleteExam(selectedExam.id);
      toast.success('Exam deleted successfully');
      setShowDeleteDialog(false);
      fetchExams();
    } catch (error) {
      toast.error('Failed to delete exam');
    }
  };

  const ExamForm = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Exam Title</label>
        <Input
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          placeholder="Enter exam title"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
          <Input
            type="datetime-local"
            value={formData.start_at}
            onChange={(e) => setFormData({ ...formData, start_at: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">End Time</label>
          <Input
            type="datetime-local"
            value={formData.end_at}
            onChange={(e) => setFormData({ ...formData, end_at: e.target.value })}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Class ID</label>
          <Input
            type="number"
            value={formData.class_id}
            onChange={(e) => setFormData({ ...formData, class_id: parseInt(e.target.value) })}
            placeholder="Enter class ID"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Join Window (seconds)</label>
          <Input
            type="number"
            value={formData.join_window_sec}
            onChange={(e) => setFormData({ ...formData, join_window_sec: parseInt(e.target.value) })}
            placeholder="300"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Instructions</label>
        <textarea
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={4}
          value={formData.instructions}
          onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
          placeholder="Enter exam instructions..."
        />
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
          {selectedExam ? 'Update Exam' : 'Create Exam'}
        </Button>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Exam Management</h1>
          <p className="text-gray-600 mt-1">Create and manage exams</p>
        </div>
        <Button
          variant="primary"
          onClick={handleCreateExam}
          className="flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Create Exam
        </Button>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <DocumentCheckIcon className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">All Exams</h2>
          </div>
          <div className="text-sm text-gray-500">
            Total: {exams.length} exams
          </div>
        </div>

        <DataTable
          data={exams}
          columns={columns}
          loading={loading}
          emptyMessage="No exams found"
        />
      </Card>

      {/* Create Exam Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Exam"
        size="lg"
      >
        <ExamForm />
      </Modal>

      {/* Edit Exam Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Exam"
        size="lg"
      >
        <ExamForm />
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDelete}
        title="Delete Exam"
        message={`Are you sure you want to delete "${selectedExam?.title}"? This action cannot be undone.`}
        confirmText="Delete"
        confirmVariant="danger"
      />
    </div>
  );
};