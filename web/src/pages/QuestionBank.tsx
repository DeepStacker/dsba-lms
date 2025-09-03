import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { DataTable } from '../components/common/DataTable';
import { SearchFilter } from '../components/common/SearchFilter';
import { Modal } from '../components/common/Modal';
import { Select } from '../components/common/Select';
import { Input } from '../components/common/Input';
import { Textarea } from '../components/common/Textarea';
import { FileUpload } from '../components/common/FileUpload';
import { questionsApi, aiApi } from '../utils/api';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  SparklesIcon,
  PhotoIcon,
  DocumentTextIcon,
  CodeBracketIcon,
  QuestionMarkCircleIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface Question {
  id: string;
  text: string;
  type: 'mcq' | 'descriptive' | 'coding';
  subject: string;
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
  marks: number;
  options?: string[];
  correctAnswer?: string;
  modelAnswer?: string;
  rubricJson?: string;
  tags: string[];
  createdBy: string;
  createdAt: string;
  usageCount: number;
}

const QuestionBank: React.FC = () => {
  const { user } = useAuth();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [showAIGeneratorModal, setShowAIGeneratorModal] = useState(false);
  const [diGenerating, setAIGenerating] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);

  const [questionFormData, setQuestionFormData] = useState({
    text: '',
    type: 'mcq' as 'mcq' | 'descriptive' | 'coding',
    subject: '',
    topic: '',
    difficulty: 'medium' as 'easy' | 'medium' | 'hard',
    marks: 5,
    options: [''] as string[],
    correctAnswer: '',
    modelAnswer: '',
    rubricJson: '',
    tags: [] as string[]
  });

  const [aiGeneratorData, setAiGeneratorData] = useState({
    topic: '',
    subject: '',
    difficulty: 'medium' as 'easy' | 'medium' | 'hard',
    type: 'mcq' as 'mcq' | 'descriptive' | 'coding',
    count: 5,
    syllabus: '',
    learningObjectives: '',
    bloomLevel: 'understand' as 'knowledge' | 'comprehension' | 'application' | 'analysis' | 'synthesis' | 'evaluation'
  });

  useEffect(() => {
    fetchQuestions();
  }, []);

  const fetchQuestions = async () => {
    try {
      setLoading(true);
      const response = await questionsApi.getQuestions({ limit: 200 });
      if (response) {
        setQuestions(response.map((q: any) => ({
          id: String(q.id),
          text: q.text,
          type: q.type,
          subject: q.subject,
          topic: q.topic,
          difficulty: q.difficulty,
          marks: q.usage_count || 5,
          options: q.options || [],
          correctAnswer: q.correct_answer,
          modelAnswer: q.model_answer,
          rubricJson: q.rubric_json,
          tags: q.tags || [],
          createdBy: q.created_by,
          createdAt: q.created_at,
          usageCount: q.usage_count || 0
        })));
      }
    } catch (error) {
      toast.error('Failed to fetch questions');
    } finally {
      setLoading(false);
    }
  };

  const validateQuestionForm = () => {
    const errors: Record<string, string> = {};
    if (!questionFormData.text.trim()) errors.text = 'Question text is required';
    if (!questionFormData.subject.trim()) errors.subject = 'Subject is required';
    if (!questionFormData.topic.trim()) errors.topic = 'Topic is required';
    if (questionFormData.marks <= 0) errors.marks = 'Marks must be greater than 0';

    if (questionFormData.type === 'mcq') {
      if (questionFormData.options.length < 2) errors.options = 'MCQ needs at least 2 options';
      if (!questionFormData.correctAnswer.trim()) errors.correctAnswer = 'Correct answer is required';
    } else if (questionFormData.type === 'descriptive') {
      if (!questionFormData.modelAnswer?.trim()) errors.modelAnswer = 'Model answer is required';
    }

    // Validate new errors
    if (questionFormData.type === 'descriptive' && !questionFormData.modelAnswer?.trim()) {
      errors.modelAnswer = 'Model answer is required for descriptive questions';
    }
    if (questionFormData.type === 'coding' && !questionFormData.modelAnswer?.trim()) {
      errors.modelAnswer = 'Model answer is required for coding questions';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const resetQuestionForm = () => {
    setQuestionFormData({
      text: '',
      type: 'mcq',
      subject: '',
      topic: '',
      difficulty: 'medium',
      marks: 5,
      options: [''],
      correctAnswer: '',
      modelAnswer: '',
      rubricJson: '',
      tags: []
    });
    setFormErrors({});
    setEditingQuestion(null);
  };

  const handleCreateQuestion = async () => {
    if (!validateQuestionForm()) return;

    try {
      setLoading(true);
      const questionData = {
        text: questionFormData.text,
        type: questionFormData.type,
        subject: questionFormData.subject,
        topic: questionFormData.topic,
        difficulty: questionFormData.difficulty,
        marks: questionFormData.marks,
        options: questionFormData.options.filter(opt => opt.trim()),
        correct_answer: questionFormData.correctAnswer,
        model_answer: questionFormData.modelAnswer,
        rubric_json: questionFormData.rubricJson || '{}',
        tags: questionFormData.tags
      };

      await questionsApi.createQuestion(questionData);
      toast.success('Question created successfully!');
      setShowQuestionModal(false);
      resetQuestionForm();
      fetchQuestions();
    } catch (error) {
      toast.error('Failed to create question');
    } finally {
      setLoading(false);
    }
  };

  const handleAIGeneration = async () => {
    try {
      setAIGenerating(true);
      const aiConfig = {
        topic: aiGeneratorData.topic,
        subject: aiGeneratorData.subject,
        difficulty: aiGeneratorData.difficulty,
        type: aiGeneratorData.type,
        count: aiGeneratorData.count,
        syllabus: aiGeneratorData.syllabus,
        learning_objectives: aiGeneratorData.learningObjectives.split(','),
        bloom_level: aiGeneratorData.bloomLevel
      };

      const generatedQuestions = await aiApi.generateQuestions(
        aiGeneratorData.syllabus,
        aiGeneratorData.learningObjectives.split(','),
        aiConfig
      );

      // Process and save generated questions
      for (const q of generatedQuestions.questions || []) {
        try {
          const questionData = {
            text: q.text,
            type: q.type || aiGeneratorData.type,
            subject: aiGeneratorData.subject,
            topic: aiGeneratorData.topic,
            difficulty: aiGeneratorData.difficulty,
            marks: q.marks || 5,
            options: q.options || [],
            correct_answer: q.correct_answer || '',
            model_answer: q.model_answer || '',
            rubric_json: q.rubric_json || '{}',
            tags: [...(q.tags || []), 'ai-generated']
          };
          await questionsApi.createQuestion(questionData);
        } catch (error) {
          console.warn('Failed to save generated question:', error);
        }
      }

      toast.success(`Generated ${aiGeneratorData.count} questions successfully!`);
      setShowAIGeneratorModal(false);
      fetchQuestions();
    } catch (error) {
      toast.error('Failed to generate questions');
    } finally {
      setAIGenerating(false);
    }
  };

  const columns = [
    {
      key: 'text',
      header: 'Question',
      render: (value: string, question: Question) => (
        <div className="max-w-xs">
          <p className="text-sm text-gray-900 truncate">{value}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
              question.type === 'mcq' ? 'bg-blue-100 text-blue-800' :
              question.type === 'descriptive' ? 'bg-green-100 text-green-800' :
              'bg-purple-100 text-purple-800'
            }`}>
              {question.type.toUpperCase()}
            </span>
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
              question.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
              question.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {question.difficulty}
            </span>
          </div>
        </div>
      )
    },
    {
      key: 'subject',
      header: 'Subject',
      sortable: true
    },
    {
      key: 'topic',
      header: 'Topic',
      sortable: true
    },
    {
      key: 'marks',
      header: 'Marks',
      sortable: true
    },
    {
      key: 'usageCount',
      header: 'Usage',
      render: (value: number) => (
        <div className="flex items-center gap-1">
          <DocumentTextIcon className="h-4 w-4 text-gray-400" />
          <span>{value}</span>
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
            onClick={() => {/* View question details */}}
            className="text-blue-600 hover:text-blue-900 p-1"
            title="View"
          >
            <EyeIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => setEditingQuestion(question)}
            className="text-indigo-600 hover:text-indigo-900 p-1"
            title="Edit"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => {/* Delete question */}}
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
    { key: 'type', label: 'Type', type: 'select' as const, options: [
      { value: 'mcq', label: 'MCQ' },
      { value: 'descriptive', label: 'Descriptive' },
      { value: 'coding', label: 'Coding' }
    ]},
    { key: 'difficulty', label: 'Difficulty', type: 'select' as const, options: [
      { value: 'easy', label: 'Easy' },
      { value: 'medium', label: 'Medium' },
      { value: 'hard', label: 'Hard' }
    ]},
    { key: 'subject', label: 'Subject', type: 'text' as const }
  ];

  const addOption = () => {
    setQuestionFormData(prev => ({
      ...prev,
      options: [...prev.options, '']
    }));
  };

  const removeOption = (index: number) => {
    setQuestionFormData(prev => ({
      ...prev,
      options: prev.options.filter((_, i) => i !== index)
    }));
  };

  const updateOption = (index: number, value: string) => {
    setQuestionFormData(prev => ({
      ...prev,
      options: prev.options.map((opt, i) => i === index ? value : opt)
    }));
  };

  // Mock form errors for file upload
  // This will be removed when integrating with an API service
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Question Bank</h1>
          <p className="text-gray-600 mt-1">Manage and generate questions for exams</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={() => {
              resetQuestionForm();
              setShowAIGeneratorModal(true);
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
          <div className="text-2xl font-bold text-gray-900">{questions.length}</div>
          <p className="text-sm text-gray-600">Total Questions</p>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-blue-900">
            {questions.filter(q => q.type === 'mcq').length}
          </div>
          <p className="text-sm text-gray-600">MCQ Questions</p>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-green-900">
            {questions.filter(q => q.type === 'descriptive').length}
          </div>
          <p className="text-sm text-gray-600">Descriptive</p>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-purple-900">
            {questions.filter(q => q.type === 'coding').length}
          </div>
          <p className="text-sm text-gray-600">Coding Questions</p>
        </Card>
      </div>

      {/* Search and Filters */}
      <SearchFilter
        onSearch={(query) => console.log('Searching questions:', query)}
        onFilter={(filters) => console.log('Applied filters:', filters)}
        filterOptions={filterOptions}
      />

      {/* Questions Table */}
      <Card className="p-6">
        <DataTable
          data={questions}
          columns={columns}
          loading={loading}
          itemsPerPage={15}
          emptyMessage="No questions found"
        />
      </Card>

      {/* AI Generator Modal */}
      <Modal
        isOpen={showAIGeneratorModal}
        onClose={() => {
          setShowAIGeneratorModal(false);
          setAIGenerating(false);
        }}
        title="AI Question Generator"
        size="xl"
      >
        <div className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <SparklesIcon className="h-6 w-6 text-blue-500 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-blue-800">AI-Powered Generation</h4>
                <p className="text-sm text-blue-700 mt-1">
                  Generate high-quality questions tailored to your curriculum using our advanced AI models.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Topic"
              value={aiGeneratorData.topic}
              onChange={(e) => setAiGeneratorData(prev => ({ ...prev, topic: e.target.value }))}
              required
            />
            <Input
              label="Subject"
              value={aiGeneratorData.subject}
              onChange={(e) => setAiGeneratorData(prev => ({ ...prev, subject: e.target.value }))}
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Select
              label="Difficulty"
              options={[
                { value: 'easy', label: 'Easy' },
                { value: 'medium', label: 'Medium' },
                { value: 'hard', label: 'Hard' }
              ]}
              value={aiGeneratorData.difficulty}
              onChange={(value) => setAiGeneratorData(prev => ({ ...prev, difficulty: value as 'easy' | 'medium' | 'hard' }))}
            />
            <Select
              label="Question Type"
              options={[
                { value: 'mcq', label: 'Multiple Choice' },
                { value: 'descriptive', label: 'Descriptive' },
                { value: 'coding', label: 'Coding' }
              ]}
              value={aiGeneratorData.type}
              onChange={(value) => setAiGeneratorData(prev => ({ ...prev, type: value as 'mcq' | 'descriptive' | 'coding' }))}
            />
            <Input
              label="Number of Questions"
              type="number"
              value={aiGeneratorData.count.toString()}
              onChange={(e) => setAiGeneratorData(prev => ({ ...prev, count: parseInt(e.target.value) || 5 }))}
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Textarea
              label="Syllabus Context"
              value={aiGeneratorData.syllabus}
              onChange={(e) => setAiGeneratorData(prev => ({ ...prev, syllabus: e.target.value }))}
              rows={3}
              placeholder="Provide syllabus context, key concepts, and learning objectives..."
            />
            <Textarea
              label="Learning Objectives"
              value={aiGeneratorData.learningObjectives}
              onChange={(e) => setAiGeneratorData(prev => ({ ...prev, learningObjectives: e.target.value }))}
              rows={3}
              placeholder="List specific learning objectives (comma-separated)..."
            />
          </div>

          <Select
            label="Bloom's Taxonomy Level"
            options={[
              { value: 'knowledge', label: 'Knowledge' },
              { value: 'comprehension', label: 'Comprehension' },
              { value: 'application', label: 'Application' },
              { value: 'analysis', label: 'Analysis' },
              { value: 'synthesis', label: 'Synthesis' },
              { value: 'evaluation', label: 'Evaluation' }
            ]}
            value={aiGeneratorData.bloomLevel}
            onChange={(value) => setAiGeneratorData(prev => ({ ...prev, bloomLevel: value as any }))}
          />

          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button
              variant="secondary"
              onClick={() => {
                setShowAIGeneratorModal(false);
                setAIGenerating(false);
              }}
              disabled={diGenerating}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleAIGeneration}
              isLoading={diGenerating}
              className="flex items-center gap-2"
            >
              <SparklesIcon className="h-5 w-5" />
              Generate Questions
            </Button>
          </div>
        </div>
      </Modal>

      {/* Manual Question Creation Modal */}
      <Modal
        isOpen={showQuestionModal}
        onClose={() => {
          setShowQuestionModal(false);
          resetQuestionForm();
        }}
        title={editingQuestion ? 'Edit Question' : 'Create New Question'}
        size="xl"
      >
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Subject"
              value={questionFormData.subject}
              onChange={(e) => setQuestionFormData(prev => ({ ...prev, subject: e.target.value }))}
              error={formErrors.subject}
              required
            />
            <Input
              label="Topic"
              value={questionFormData.topic}
              onChange={(e) => setQuestionFormData(prev => ({ ...prev, topic: e.target.value }))}
              error={formErrors.topic}
              required
            />
          </div>

          <Select
            label="Question Type"
            options={[
              { value: 'mcq', label: 'Multiple Choice (MCQ)' },
              { value: 'descriptive', label: 'Descriptive/Essay' },
              { value: 'coding', label: 'Coding/Program' }
            ]}
            value={questionFormData.type}
            onChange={(value) => {
              setQuestionFormData(prev => ({
                ...prev,
                type: value as 'mcq' | 'descriptive' | 'coding',
                options: value === 'mcq' ? ['', ''] : []
              }));
            }}
          />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Select
              label="Difficulty"
              options={[
                { value: 'easy', label: 'Easy' },
                { value: 'medium', label: 'Medium' },
                { value: 'hard', label: 'Hard' }
              ]}
              value={questionFormData.difficulty}
              onChange={(value) => setQuestionFormData(prev => ({ ...prev, difficulty: value as 'easy' | 'medium' | 'hard' }))}
            />
            <Input
              label="Marks"
              type="number"
              value={questionFormData.marks.toString()}
              onChange={(e) => setQuestionFormData(prev => ({ ...prev, marks: parseInt(e.target.value) || 0 }))}
              error={formErrors.marks}
              required
            />
          </div>

          <Textarea
            label="Question Text"
            value={questionFormData.text}
            onChange={(e) => setQuestionFormData(prev => ({ ...prev, text: e.target.value }))}
            error={formErrors.text}
            rows={3}
            required
          />

          {/* MCQ Options */}
          {questionFormData.type === 'mcq' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700">Options</label>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={addOption}
                  type="button"
                >
                  Add Option
                </Button>
              </div>
              {questionFormData.options.map((option, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="flex items-center min-w-0 flex-1 gap-2">
                    <input
                      type="radio"
                      name="correctAnswer"
                      checked={questionFormData.correctAnswer === option}
                      onChange={() => setQuestionFormData(prev => ({ ...prev, correctAnswer: option }))}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <Input
                      value={option}
                      onChange={(e) => updateOption(index, e.target.value)}
                      placeholder={`Option ${index + 1}`}
                      className="flex-1"
                    />
                  </div>
                  {questionFormData.options.length > 2 && (
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => removeOption(index)}
                      type="button"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Model Answer for Descriptive/Coding */}
          {(questionFormData.type === 'descriptive' || questionFormData.type === 'coding') && (
            <Textarea
              label={questionFormData.type === 'coding' ? 'Sample Solution' : 'Model Answer'}
              value={questionFormData.modelAnswer}
              onChange={(e) => setQuestionFormData(prev => ({ ...prev, modelAnswer: e.target.value }))}
              error={formErrors.modelAnswer}
              rows={questionFormData.type === 'coding' ? 6 : 4}
              placeholder={questionFormData.type === 'coding' ? 'Provide sample code solution...' : 'Provide model answer...'}
              required
            />
          )}

          <div className="flex justify-end gap-3 pt-4 border-t">
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
              onClick={handleCreateQuestion}
              isLoading={loading}
              type="submit"
            >
              {editingQuestion ? 'Update Question' : 'Create Question'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default QuestionBank;
