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
import { questionsApi } from '../utils/api';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  SparklesIcon,
  DocumentTextIcon,
  QuestionMarkCircleIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface Question {
  id: string;
  text: string;
  type: 'mcq' | 'msq' | 'tf' | 'numeric' | 'descriptive' | 'coding';
  maxMarks: number;
  course: string;
  coMapping: string;
  difficulty: 'easy' | 'medium' | 'hard';
  createdBy: string;
  createdAt: string;
  options?: QuestionOption[];
}

interface QuestionOption {
  id: string;
  text: string;
  isCorrect: boolean;
}

const QuestionBank: React.FC = () => {
  const { user } = useAuth();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [showAIModal, setShowAIModal] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});
  const [currentQuestions, setCurrentQuestions] = useState<Question[]>([]);

  const [questionFormData, setQuestionFormData] = useState({
    text: '',
    type: 'mcq' as Question['type'],
    maxMarks: 1,
    courseId: '',
    coMapping: '',
    difficulty: 'medium' as Question['difficulty'],
    modelAnswer: '',
    options: [
      { text: '', isCorrect: false },
      { text: '', isCorrect: false },
      { text: '', isCorrect: false },
      { text: '', isCorrect: false }
    ]
  });

  const [aiFormData, setAiFormData] = useState({
    courseId: '',
    topics: '',
    questionType: 'mcq' as Question['type'],
    difficulty: 'medium' as Question['difficulty'],
    count: 5,
    maxMarks: 1
  });

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchQuestions();
  }, []);

  useEffect(() => {
    let filteredQuestions = [...questions];

    if (searchQuery.trim()) {
      filteredQuestions = filteredQuestions.filter(question =>
        question.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        question.course.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    Object.entries(activeFilters).forEach(([key, value]) => {
      if (value && value !== '') {
        filteredQuestions = filteredQuestions.filter(question => {
          if (key === 'type') {
            return question.type === value;
          } else if (key === 'difficulty') {
            return question.difficulty === value;
          } else if (key === 'course') {
            return question.course.toLowerCase().includes(value.toLowerCase());
          }
          return true;
        });
      }
    });

    setCurrentQuestions(filteredQuestions);
  }, [questions, searchQuery, activeFilters]);

  const fetchQuestions = async () => {
    try {
      setLoading(true);
      // Mock data for demonstration
      const mockQuestions: Question[] = [
        {
          id: '1',
          text: 'What is the time complexity of binary search?',
          type: 'mcq',
          maxMarks: 2,
          course: 'Data Structures and Algorithms',
          coMapping: 'CO1',
          difficulty: 'medium',
          createdBy: 'Dr. John Doe',
          createdAt: '2024-01-08T00:00:00Z',
          options: [
            { id: '1', text: 'O(n)', isCorrect: false },
            { id: '2', text: 'O(log n)', isCorrect: true },
            { id: '3', text: 'O(n²)', isCorrect: false },
            { id: '4', text: 'O(1)', isCorrect: false }
          ]
        },
        {
          id: '2',
          text: 'Explain the concept of database normalization and its benefits.',
          type: 'descriptive',
          maxMarks: 10,
          course: 'Database Management Systems',
          coMapping: 'CO2',
          difficulty: 'hard',
          createdBy: 'Dr. Jane Smith',
          createdAt: '2024-01-09T00:00:00Z'
        },
        {
          id: '3',
          text: 'Which of the following are valid HTTP methods? (Select all that apply)',
          type: 'msq',
          maxMarks: 3,
          course: 'Web Development',
          coMapping: 'CO3',
          difficulty: 'easy',
          createdBy: 'Prof. Mike Johnson',
          createdAt: '2024-01-10T00:00:00Z',
          options: [
            { id: '1', text: 'GET', isCorrect: true },
            { id: '2', text: 'POST', isCorrect: true },
            { id: '3', text: 'DELETE', isCorrect: true },
            { id: '4', text: 'SEND', isCorrect: false }
          ]
        }
      ];
      setQuestions(mockQuestions);
    } catch (error) {
      toast.error('Failed to fetch questions');
      console.error('Error fetching questions:', error);
    } finally {
      setLoading(false);
    }
  };

  const validateQuestionForm = () => {
    const errors: Record<string, string> = {};

    if (!questionFormData.text.trim()) {
      errors.text = 'Question text is required';
    }
    if (!questionFormData.courseId) {
      errors.courseId = 'Course selection is required';
    }
    if (questionFormData.maxMarks <= 0) {
      errors.maxMarks = 'Max marks must be greater than 0';
    }
    if (['mcq', 'msq'].includes(questionFormData.type)) {
      const hasCorrectOption = questionFormData.options.some(opt => opt.isCorrect);
      if (!hasCorrectOption) {
        errors.options = 'At least one correct option is required';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreateQuestion = async () => {
    if (!validateQuestionForm()) return;

    try {
      setLoading(true);
      // Mock question creation
      const newQuestion: Question = {
        id: String(Date.now()),
        text: questionFormData.text,
        type: questionFormData.type,
        maxMarks: questionFormData.maxMarks,
        course: 'Selected Course', // Would be resolved from courseId
        coMapping: questionFormData.coMapping,
        difficulty: questionFormData.difficulty,
        createdBy: user?.name || 'Unknown',
        createdAt: new Date().toISOString(),
        options: ['mcq', 'msq'].includes(questionFormData.type) ? questionFormData.options : undefined
      };

      setQuestions(prev => [newQuestion, ...prev]);
      toast.success('Question created successfully!');
      setShowQuestionModal(false);
      resetQuestionForm();
    } catch (error: any) {
      console.error('Error creating question:', error);
      toast.error('Failed to create question');
    } finally {
      setLoading(false);
    }
  };

  const handleAIGeneration = async () => {
    try {
      setLoading(true);
      // Mock AI generation
      const generatedQuestions: Question[] = Array.from({ length: aiFormData.count }, (_, index) => ({
        id: String(Date.now() + index),
        text: `AI Generated Question ${index + 1}: What is the concept related to ${aiFormData.topics}?`,
        type: aiFormData.questionType,
        maxMarks: aiFormData.maxMarks,
        course: 'Selected Course',
        coMapping: 'CO1',
        difficulty: aiFormData.difficulty,
        createdBy: 'AI Assistant',
        createdAt: new Date().toISOString(),
        options: ['mcq', 'msq'].includes(aiFormData.questionType) ? [
          { id: '1', text: 'Option A', isCorrect: true },
          { id: '2', text: 'Option B', isCorrect: false },
          { id: '3', text: 'Option C', isCorrect: false },
          { id: '4', text: 'Option D', isCorrect: false }
        ] : undefined
      }));

      setQuestions(prev => [...generatedQuestions, ...prev]);
      toast.success(`${aiFormData.count} questions generated successfully!`);
      setShowAIModal(false);
      resetAIForm();
    } catch (error) {
      toast.error('Failed to generate questions');
    } finally {
      setLoading(false);
    }
  };

  const resetQuestionForm = () => {
    setQuestionFormData({
      text: '',
      type: 'mcq',
      maxMarks: 1,
      courseId: '',
      coMapping: '',
      difficulty: 'medium',
      modelAnswer: '',
      options: [
        { text: '', isCorrect: false },
        { text: '', isCorrect: false },
        { text: '', isCorrect: false },
        { text: '', isCorrect: false }
      ]
    });
    setFormErrors({});
    setEditingQuestion(null);
  };

  const resetAIForm = () => {
    setAiFormData({
      courseId: '',
      topics: '',
      questionType: 'mcq',
      difficulty: 'medium',
      count: 5,
      maxMarks: 1
    });
  };

  const getQuestionTypeLabel = (type: Question['type']) => {
    const typeLabels = {
      mcq: 'Multiple Choice',
      msq: 'Multiple Select',
      tf: 'True/False',
      numeric: 'Numeric',
      descriptive: 'Descriptive',
      coding: 'Coding'
    };
    return typeLabels[type] || type;
  };

  const getDifficultyBadge = (difficulty: Question['difficulty']) => {
    const difficultyConfig = {
      easy: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      hard: 'bg-red-100 text-red-800'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${difficultyConfig[difficulty]}`}>
        {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
      </span>
    );
  };

  const questionColumns = [
    {
      key: 'text',
      header: 'Question',
      render: (value: string, question: Question) => (
        <div>
          <div className="font-medium text-gray-900 line-clamp-2">{value}</div>
          <div className="text-sm text-gray-500">{question.course}</div>
        </div>
      ),
      sortable: true
    },
    {
      key: 'type',
      header: 'Type',
      render: (value: string) => (
        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
          {getQuestionTypeLabel(value as Question['type'])}
        </span>
      ),
      filterable: true
    },
    {
      key: 'difficulty',
      header: 'Difficulty',
      render: (value: string) => getDifficultyBadge(value as Question['difficulty']),
      filterable: true
    },
    {
      key: 'maxMarks',
      header: 'Max Marks',
      render: (value: number) => (
        <span className="font-medium text-gray-900">{value}</span>
      ),
      sortable: true
    },
    {
      key: 'coMapping',
      header: 'CO Mapping',
      render: (value: string) => (
        <span className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full">
          {value}
        </span>
      )
    },
    {
      key: 'createdBy',
      header: 'Created By',
      render: (value: string, question: Question) => (
        <div>
          <div className="text-sm font-medium text-gray-900">{value}</div>
          <div className="text-xs text-gray-500">
            {new Date(question.createdAt).toLocaleDateString()}
          </div>
        </div>
      ),
      sortable: true
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (value: any, question: Question) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => {}}
            className="text-blue-600 hover:text-blue-900 p-1"
            title="Edit"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => {}}
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
    { 
      key: 'type', 
      label: 'Type', 
      type: 'select' as const, 
      options: [
        { value: 'mcq', label: 'Multiple Choice' },
        { value: 'msq', label: 'Multiple Select' },
        { value: 'tf', label: 'True/False' },
        { value: 'numeric', label: 'Numeric' },
        { value: 'descriptive', label: 'Descriptive' },
        { value: 'coding', label: 'Coding' }
      ]
    },
    { 
      key: 'difficulty', 
      label: 'Difficulty', 
      type: 'select' as const, 
      options: [
        { value: 'easy', label: 'Easy' },
        { value: 'medium', label: 'Medium' },
        { value: 'hard', label: 'Hard' }
      ]
    },
    { key: 'course', label: 'Course', type: 'text' as const }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Question Bank</h1>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={() => {
              resetAIForm();
              setShowAIModal(true);
            }}
            className="flex items-center gap-2"
          >
            <SparklesIcon className="h-5 w-5" />
            AI Generate
          </Button>
          <Button
            variant="primary"
            onClick={() => {
              resetQuestionForm();
              setShowQuestionModal(true);
            }}
            className="flex items-center gap-2"
          >
            <PlusIcon className="h-5 w-5" />
            Add Question
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <QuestionMarkCircleIcon className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Total Questions</h3>
              <p className="text-2xl font-bold text-gray-900">{questions.length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <DocumentTextIcon className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">MCQ Questions</h3>
              <p className="text-2xl font-bold text-gray-900">
                {questions.filter(q => q.type === 'mcq').length}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <SparklesIcon className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">AI Generated</h3>
              <p className="text-2xl font-bold text-gray-900">
                {questions.filter(q => q.createdBy === 'AI Assistant').length}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <span className="text-2xl">📝</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Descriptive</h3>
              <p className="text-2xl font-bold text-gray-900">
                {questions.filter(q => q.type === 'descriptive').length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Search and Filters */}
      <SearchFilter
        onSearch={setSearchQuery}
        onFilter={setActiveFilters}
        filterOptions={filterOptions}
        placeholder="Search questions..."
        className="mb-4"
      />

      {/* Questions Table */}
      <Card className="p-6">
        <DataTable
          data={currentQuestions}
          columns={questionColumns}
          loading={loading}
          itemsPerPage={10}
          emptyMessage="No questions found"
        />
      </Card>

      {/* Create/Edit Question Modal */}
      <Modal
        isOpen={showQuestionModal}
        onClose={() => {
          setShowQuestionModal(false);
          resetQuestionForm();
        }}
        title={editingQuestion ? 'Edit Question' : 'Create New Question'}
        size="lg"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleCreateQuestion();
          }}
          className="space-y-4"
        >
          <Textarea
            label="Question Text"
            value={questionFormData.text}
            onChange={(e) => setQuestionFormData(prev => ({ ...prev, text: e.target.value }))}
            error={formErrors.text}
            placeholder="Enter your question here..."
            rows={3}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Question Type"
              value={questionFormData.type}
              onChange={(value) => setQuestionFormData(prev => ({ ...prev, type: value as Question['type'] }))}
              options={[
                { value: 'mcq', label: 'Multiple Choice' },
                { value: 'msq', label: 'Multiple Select' },
                { value: 'tf', label: 'True/False' },
                { value: 'numeric', label: 'Numeric' },
                { value: 'descriptive', label: 'Descriptive' },
                { value: 'coding', label: 'Coding' }
              ]}
              required
            />

            <Select
              label="Course"
              value={questionFormData.courseId}
              onChange={(value) => setQuestionFormData(prev => ({ ...prev, courseId: value }))}
              options={[
                { value: '1', label: 'Data Structures and Algorithms' },
                { value: '2', label: 'Database Management Systems' },
                { value: '3', label: 'Web Development' }
              ]}
              error={formErrors.courseId}
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <Input
              label="Max Marks"
              type="number"
              value={String(questionFormData.maxMarks)}
              onChange={(e) => setQuestionFormData(prev => ({ ...prev, maxMarks: parseInt(e.target.value) }))}
              error={formErrors.maxMarks}
              required
            />

            <Input
              label="CO Mapping"
              value={questionFormData.coMapping}
              onChange={(e) => setQuestionFormData(prev => ({ ...prev, coMapping: e.target.value }))}
              placeholder="e.g., CO1"
            />

            <Select
              label="Difficulty"
              value={questionFormData.difficulty}
              onChange={(value) => setQuestionFormData(prev => ({ ...prev, difficulty: value as Question['difficulty'] }))}
              options={[
                { value: 'easy', label: 'Easy' },
                { value: 'medium', label: 'Medium' },
                { value: 'hard', label: 'Hard' }
              ]}
            />
          </div>

          {/* Options for MCQ/MSQ */}
          {['mcq', 'msq'].includes(questionFormData.type) && (
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700">Options</label>
              {formErrors.options && (
                <p className="text-sm text-red-600">{formErrors.options}</p>
              )}
              {questionFormData.options.map((option, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <input
                    type={questionFormData.type === 'mcq' ? 'radio' : 'checkbox'}
                    name="correctOption"
                    checked={option.isCorrect}
                    onChange={(e) => {
                      const newOptions = [...questionFormData.options];
                      if (questionFormData.type === 'mcq') {
                        // For MCQ, only one option can be correct
                        newOptions.forEach((opt, i) => {
                          opt.isCorrect = i === index ? e.target.checked : false;
                        });
                      } else {
                        // For MSQ, multiple options can be correct
                        newOptions[index].isCorrect = e.target.checked;
                      }
                      setQuestionFormData(prev => ({ ...prev, options: newOptions }));
                    }}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <Input
                    value={option.text}
                    onChange={(e) => {
                      const newOptions = [...questionFormData.options];
                      newOptions[index].text = e.target.value;
                      setQuestionFormData(prev => ({ ...prev, options: newOptions }));
                    }}
                    placeholder={`Option ${index + 1}`}
                    className="flex-1"
                  />
                </div>
              ))}
            </div>
          )}

          {/* Model Answer for Descriptive */}
          {questionFormData.type === 'descriptive' && (
            <Textarea
              label="Model Answer"
              value={questionFormData.modelAnswer}
              onChange={(e) => setQuestionFormData(prev => ({ ...prev, modelAnswer: e.target.value }))}
              placeholder="Enter the model answer for grading reference..."
              rows={4}
            />
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => {
                setShowQuestionModal(false);
                resetQuestionForm();
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
              {editingQuestion ? 'Update Question' : 'Create Question'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* AI Generation Modal */}
      <Modal
        isOpen={showAIModal}
        onClose={() => {
          setShowAIModal(false);
          resetAIForm();
        }}
        title="AI Question Generation"
        size="md"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAIGeneration();
          }}
          className="space-y-4"
        >
          <Select
            label="Course"
            value={aiFormData.courseId}
            onChange={(value) => setAiFormData(prev => ({ ...prev, courseId: value }))}
            options={[
              { value: '1', label: 'Data Structures and Algorithms' },
              { value: '2', label: 'Database Management Systems' },
              { value: '3', label: 'Web Development' }
            ]}
            required
          />

          <Textarea
            label="Topics"
            value={aiFormData.topics}
            onChange={(e) => setAiFormData(prev => ({ ...prev, topics: e.target.value }))}
            placeholder="Enter topics separated by commas (e.g., binary search, sorting algorithms, time complexity)"
            rows={3}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Question Type"
              value={aiFormData.questionType}
              onChange={(value) => setAiFormData(prev => ({ ...prev, questionType: value as Question['type'] }))}
              options={[
                { value: 'mcq', label: 'Multiple Choice' },
                { value: 'msq', label: 'Multiple Select' },
                { value: 'tf', label: 'True/False' },
                { value: 'descriptive', label: 'Descriptive' }
              ]}
            />

            <Select
              label="Difficulty"
              value={aiFormData.difficulty}
              onChange={(value) => setAiFormData(prev => ({ ...prev, difficulty: value as Question['difficulty'] }))}
              options={[
                { value: 'easy', label: 'Easy' },
                { value: 'medium', label: 'Medium' },
                { value: 'hard', label: 'Hard' }
              ]}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Number of Questions"
              type="number"
              value={String(aiFormData.count)}
              onChange={(e) => setAiFormData(prev => ({ ...prev, count: parseInt(e.target.value) }))}
              min="1"
              max="20"
              required
            />

            <Input
              label="Max Marks per Question"
              type="number"
              value={String(aiFormData.maxMarks)}
              onChange={(e) => setAiFormData(prev => ({ ...prev, maxMarks: parseInt(e.target.value) }))}
              min="1"
              required
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => {
                setShowAIModal(false);
                resetAIForm();
              }}
              type="button"
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              type="submit"
              isLoading={loading}
              className="flex items-center gap-2"
            >
              <SparklesIcon className="h-4 w-4" />
              Generate Questions
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default QuestionBank;