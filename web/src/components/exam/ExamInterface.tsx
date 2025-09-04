import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useExamStore } from '../../stores/useExamStore';
import { useAuthStore } from '../../stores/useAuthStore';
import { Button } from '../common/Button';
import { Modal } from '../common/Modal';
import { QuestionRenderer } from './QuestionRenderer';
import { 
  ClockIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import clsx from 'clsx';

export const ExamInterface: React.FC = () => {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  
  const {
    currentExam,
    currentAttempt,
    examQuestions,
    responses,
    currentQuestionIndex,
    timeRemaining,
    isSubmitting,
    proctorStats,
    loadExam,
    joinExam,
    submitResponse,
    submitExam,
    setCurrentQuestion,
    updateTimeRemaining,
    logProctorEvent,
    clearExamState
  } = useExamStore();

  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [showWarning, setShowWarning] = useState(false);
  const [warningMessage, setWarningMessage] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Initialize exam
  useEffect(() => {
    if (examId && user?.role === 'student') {
      const id = parseInt(examId);
      loadExam(id);
    }
  }, [examId, user, loadExam]);

  // Timer countdown
  useEffect(() => {
    if (!currentAttempt || timeRemaining <= 0) return;

    const interval = setInterval(() => {
      updateTimeRemaining(timeRemaining - 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [timeRemaining, currentAttempt, updateTimeRemaining]);

  // Auto-save responses
  useEffect(() => {
    if (!currentAttempt || !examQuestions.length) return;

    const interval = setInterval(() => {
      const currentQuestion = examQuestions[currentQuestionIndex];
      if (currentQuestion && responses[currentQuestion.id]) {
        submitResponse(currentQuestion.id, responses[currentQuestion.id]);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [currentAttempt, examQuestions, currentQuestionIndex, responses, submitResponse]);

  // Proctoring event listeners
  useEffect(() => {
    if (!currentAttempt) return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        logProctorEvent('tab_switch');
        showProctorWarning('Tab switching detected! Please stay on the exam page.');
      }
    };

    const handleFocusLoss = () => {
      logProctorEvent('focus_loss');
      showProctorWarning('Window focus lost! Please keep the exam window active.');
    };

    const handlePaste = (e: ClipboardEvent) => {
      logProctorEvent('paste', { 
        content: e.clipboardData?.getData('text')?.substring(0, 100) || '' 
      });
      showProctorWarning('Paste operation detected!');
    };

    const handleFullscreenChange = () => {
      const isCurrentlyFullscreen = !!document.fullscreenElement;
      setIsFullscreen(isCurrentlyFullscreen);
      
      if (!isCurrentlyFullscreen && currentAttempt.status === 'in_progress') {
        logProctorEvent('fullscreen_exit');
        showProctorWarning('Please return to fullscreen mode for the exam.');
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      // Disable certain key combinations
      if (
        (e.ctrlKey && (e.key === 'c' || e.key === 'v' || e.key === 'a')) ||
        e.key === 'F12' ||
        (e.ctrlKey && e.shiftKey && e.key === 'I')
      ) {
        e.preventDefault();
        showProctorWarning('This action is not allowed during the exam.');
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleFocusLoss);
    document.addEventListener('paste', handlePaste);
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleFocusLoss);
      document.removeEventListener('paste', handlePaste);
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [currentAttempt, logProctorEvent]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearExamState();
    };
  }, [clearExamState]);

  const showProctorWarning = (message: string) => {
    setWarningMessage(message);
    setShowWarning(true);
    setTimeout(() => setShowWarning(false), 3000);
  };

  const handleJoinExam = async () => {
    if (!examId) return;
    
    try {
      await joinExam(parseInt(examId));
      
      // Request fullscreen
      if (document.documentElement.requestFullscreen) {
        await document.documentElement.requestFullscreen();
      }
    } catch (error) {
      console.error('Failed to join exam:', error);
    }
  };

  const handleResponseChange = useCallback((questionId: number, answer: any) => {
    submitResponse(questionId, answer);
  }, [submitResponse]);

  const handleSubmitExam = async () => {
    try {
      await submitExam();
      navigate('/dashboard');
    } catch (error) {
      console.error('Failed to submit exam:', error);
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const getTimeColor = () => {
    if (timeRemaining <= 300) return 'text-red-600'; // Last 5 minutes
    if (timeRemaining <= 900) return 'text-yellow-600'; // Last 15 minutes
    return 'text-gray-900';
  };

  const getQuestionStatus = (questionId: number) => {
    if (responses[questionId]) {
      return 'answered';
    }
    return 'unanswered';
  };

  // Show loading state
  if (!currentExam) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading exam...</p>
        </div>
      </div>
    );
  }

  // Show join screen
  if (!currentAttempt) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              {currentExam.title}
            </h1>
            <div className="space-y-3 text-sm text-gray-600 mb-6">
              <p><strong>Duration:</strong> {Math.floor((new Date(currentExam.end_at).getTime() - new Date(currentExam.start_at).getTime()) / 60000)} minutes</p>
              <p><strong>Questions:</strong> {examQuestions.length}</p>
              <p><strong>Start Time:</strong> {new Date(currentExam.start_at).toLocaleString()}</p>
            </div>
            
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
              <div className="flex">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mr-2" />
                <div className="text-sm text-yellow-800">
                  <p className="font-medium">Important Instructions:</p>
                  <ul className="mt-2 list-disc list-inside space-y-1">
                    <li>Do not switch tabs or leave the exam window</li>
                    <li>The exam will auto-submit when time expires</li>
                    <li>Your responses are saved automatically</li>
                    <li>Ensure stable internet connection</li>
                  </ul>
                </div>
              </div>
            </div>

            <Button
              variant="primary"
              size="lg"
              onClick={handleJoinExam}
              className="w-full"
            >
              Start Exam
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Warning Banner */}
      {showWarning && (
        <div className="fixed top-0 left-0 right-0 bg-red-600 text-white px-4 py-2 text-center z-50 animate-slide-down">
          <div className="flex items-center justify-center">
            <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
            {warningMessage}
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow-sm border-b px-6 py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">{currentExam.title}</h1>
            <p className="text-sm text-gray-600">
              Question {currentQuestionIndex + 1} of {examQuestions.length}
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Proctor Stats */}
            <div className="text-sm text-gray-600">
              Risk Score: <span className={clsx(
                'font-medium',
                proctorStats.riskScore > 10 ? 'text-red-600' : 
                proctorStats.riskScore > 5 ? 'text-yellow-600' : 'text-green-600'
              )}>
                {proctorStats.riskScore}
              </span>
            </div>
            
            {/* Timer */}
            <div className={clsx(
              'flex items-center text-lg font-mono font-bold',
              getTimeColor()
            )}>
              <ClockIcon className="h-5 w-5 mr-2" />
              {formatTime(timeRemaining)}
            </div>
          </div>
        </div>
      </div>

      {/* Question Navigation */}
      <div className="bg-white border-b px-6 py-3">
        <div className="flex flex-wrap gap-2">
          {examQuestions.map((question, index) => (
            <button
              key={question.id}
              onClick={() => setCurrentQuestion(index)}
              className={clsx(
                'w-10 h-10 rounded-md text-sm font-medium transition-colors',
                currentQuestionIndex === index
                  ? 'bg-blue-600 text-white'
                  : getQuestionStatus(question.id) === 'answered'
                  ? 'bg-green-100 text-green-800 hover:bg-green-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              {index + 1}
            </button>
          ))}
        </div>
      </div>

      {/* Question Content */}
      <div className="flex-1 p-6">
        {examQuestions.length > 0 && (
          <QuestionRenderer
            question={examQuestions[currentQuestionIndex]}
            response={responses[examQuestions[currentQuestionIndex].id]}
            onResponseChange={(response) => 
              handleResponseChange(examQuestions[currentQuestionIndex].id, response)
            }
            disabled={isSubmitting}
          />
        )}
      </div>

      {/* Navigation Footer */}
      <div className="bg-white border-t px-6 py-4">
        <div className="flex justify-between items-center">
          <Button
            variant="secondary"
            onClick={() => setCurrentQuestion(Math.max(0, currentQuestionIndex - 1))}
            disabled={currentQuestionIndex === 0}
          >
            Previous
          </Button>
          
          <div className="flex space-x-3">
            <Button
              variant="danger"
              onClick={() => setShowSubmitModal(true)}
              disabled={isSubmitting}
            >
              Submit Exam
            </Button>
            
            <Button
              variant="primary"
              onClick={() => setCurrentQuestion(Math.min(examQuestions.length - 1, currentQuestionIndex + 1))}
              disabled={currentQuestionIndex === examQuestions.length - 1}
            >
              Next
            </Button>
          </div>
        </div>
      </div>

      {/* Submit Confirmation Modal */}
      <Modal
        isOpen={showSubmitModal}
        onClose={() => setShowSubmitModal(false)}
        title="Submit Exam"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-gray-700">
            Are you sure you want to submit your exam? This action cannot be undone.
          </p>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Total Questions:</span>
                <span className="ml-2 font-medium">{examQuestions.length}</span>
              </div>
              <div>
                <span className="text-gray-600">Answered:</span>
                <span className="ml-2 font-medium text-green-600">
                  {Object.keys(responses).length}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Unanswered:</span>
                <span className="ml-2 font-medium text-red-600">
                  {examQuestions.length - Object.keys(responses).length}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Time Remaining:</span>
                <span className="ml-2 font-medium">{formatTime(timeRemaining)}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="flex justify-end space-x-3 mt-6">
          <Button
            variant="secondary"
            onClick={() => setShowSubmitModal(false)}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleSubmitExam}
            isLoading={isSubmitting}
          >
            Submit Exam
          </Button>
        </div>
      </Modal>
    </div>
  );
};