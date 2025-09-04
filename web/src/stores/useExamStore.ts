import { create } from 'zustand';
import { examsApi, studentApi } from '../utils/api';
import { Exam, Attempt, Response, ProctorLog } from '../types';
import toast from 'react-hot-toast';

interface ExamState {
  // Current exam data
  currentExam: Exam | null;
  currentAttempt: Attempt | null;
  examQuestions: any[];
  responses: Record<number, any>;
  
  // Exam lists
  exams: Exam[];
  studentExams: any[];
  
  // UI state
  isLoading: boolean;
  error: string | null;
  currentQuestionIndex: number;
  timeRemaining: number;
  isSubmitting: boolean;
  
  // WebSocket connection
  websocket: WebSocket | null;
  
  // Proctoring
  proctorLogs: ProctorLog[];
  proctorStats: {
    tabSwitches: number;
    focusLosses: number;
    networkDrops: number;
    pastes: number;
    riskScore: number;
  };

  // Actions
  loadExams: (params?: any) => Promise<void>;
  loadStudentExams: () => Promise<void>;
  loadExam: (examId: number) => Promise<void>;
  joinExam: (examId: number, sessionData?: any) => Promise<void>;
  submitResponse: (questionId: number, answer: any) => Promise<void>;
  submitExam: () => Promise<void>;
  setCurrentQuestion: (index: number) => void;
  updateTimeRemaining: (time: number) => void;
  connectWebSocket: (examId: number, attemptId: number) => void;
  disconnectWebSocket: () => void;
  logProctorEvent: (eventType: string, payload?: any) => void;
  clearExamState: () => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useExamStore = create<ExamState>((set, get) => ({
  // Initial state
  currentExam: null,
  currentAttempt: null,
  examQuestions: [],
  responses: {},
  exams: [],
  studentExams: [],
  isLoading: false,
  error: null,
  currentQuestionIndex: 0,
  timeRemaining: 0,
  isSubmitting: false,
  websocket: null,
  proctorLogs: [],
  proctorStats: {
    tabSwitches: 0,
    focusLosses: 0,
    networkDrops: 0,
    pastes: 0,
    riskScore: 0
  },

  loadExams: async (params = {}) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await examsApi.getExams(params);
      
      set({ 
        exams: response || [],
        isLoading: false 
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load exams';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
    }
  },

  loadStudentExams: async () => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await studentApi.getStudentExams();
      
      set({ 
        studentExams: response || [],
        isLoading: false 
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load student exams';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
    }
  },

  loadExam: async (examId: number) => {
    try {
      set({ isLoading: true, error: null });
      
      const examResponse = await examsApi.getExam(examId);
      
      if (examResponse) {
        set({ 
          currentExam: examResponse,
          isLoading: false 
        });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load exam';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
    }
  },

  joinExam: async (examId: number, sessionData = {}) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await studentApi.joinExam(examId, sessionData.sessionToken);
      
      if (response) {
        set({
          currentAttempt: response.attempt,
          examQuestions: response.questions || [],
          timeRemaining: response.timeRemaining || 0,
          isLoading: false
        });

        // Connect WebSocket for real-time monitoring
        if (response.attempt) {
          get().connectWebSocket(examId, response.attempt.id);
        }

        toast.success('Successfully joined exam');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to join exam';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
      throw error;
    }
  },

  submitResponse: async (questionId: number, answer: any) => {
    try {
      const { currentAttempt, responses } = get();
      
      if (!currentAttempt) {
        throw new Error('No active attempt');
      }

      // Update local state immediately
      set({
        responses: {
          ...responses,
          [questionId]: answer
        }
      });

      // Submit to server
      await studentApi.submitAnswer({
        attempt_id: currentAttempt.id,
        question_id: questionId,
        answer_json: answer
      });

    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save response';
      console.error('Response submission error:', error);
      // Don't show toast for auto-save errors to avoid spam
    }
  },

  submitExam: async () => {
    try {
      const { currentExam, currentAttempt } = get();
      
      if (!currentExam || !currentAttempt) {
        throw new Error('No active exam or attempt');
      }

      set({ isSubmitting: true });

      await studentApi.submitExam(currentExam.id);

      // Disconnect WebSocket
      get().disconnectWebSocket();

      // Clear exam state
      get().clearExamState();

      toast.success('Exam submitted successfully');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to submit exam';
      set({ isSubmitting: false });
      toast.error(message);
      throw error;
    }
  },

  setCurrentQuestion: (index: number) => {
    set({ currentQuestionIndex: index });
  },

  updateTimeRemaining: (time: number) => {
    set({ timeRemaining: time });
    
    // Auto-submit when time runs out
    if (time <= 0) {
      const { currentAttempt } = get();
      if (currentAttempt && currentAttempt.status === 'in_progress') {
        get().submitExam();
      }
    }
  },

  connectWebSocket: (examId: number, attemptId: number) => {
    try {
      const wsUrl = `ws://localhost:8000/api/v1/exams/${examId}/attempts/${attemptId}/ws`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        set({ websocket: ws });
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'time_update':
              set({ timeRemaining: data.timeRemaining });
              break;
            case 'exam_ended':
              get().submitExam();
              break;
            case 'proctor_alert':
              console.warn('Proctoring alert:', data.payload);
              break;
            default:
              console.log('WebSocket message:', data);
          }
        } catch (error) {
          console.error('WebSocket message parsing error:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        set({ websocket: null });
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        set({ websocket: null });
      };

    } catch (error) {
      console.error('WebSocket connection error:', error);
    }
  },

  disconnectWebSocket: () => {
    const { websocket } = get();
    if (websocket) {
      websocket.close();
      set({ websocket: null });
    }
  },

  logProctorEvent: (eventType: string, payload = {}) => {
    const { websocket, proctorStats } = get();
    
    // Update local stats
    const newStats = { ...proctorStats };
    switch (eventType) {
      case 'tab_switch':
        newStats.tabSwitches += 1;
        break;
      case 'focus_loss':
        newStats.focusLosses += 1;
        break;
      case 'network_drop':
        newStats.networkDrops += 1;
        break;
      case 'paste':
        newStats.pastes += 1;
        break;
    }
    
    // Calculate risk score
    newStats.riskScore = (
      newStats.tabSwitches * 2 +
      newStats.focusLosses * 1 +
      newStats.networkDrops * 3 +
      newStats.pastes * 5
    );

    set({ proctorStats: newStats });

    // Send to server via WebSocket
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'proctor_event',
        event_type: eventType,
        payload,
        timestamp: new Date().toISOString()
      }));
    }
  },

  clearExamState: () => {
    get().disconnectWebSocket();
    
    set({
      currentExam: null,
      currentAttempt: null,
      examQuestions: [],
      responses: {},
      currentQuestionIndex: 0,
      timeRemaining: 0,
      isSubmitting: false,
      proctorLogs: [],
      proctorStats: {
        tabSwitches: 0,
        focusLosses: 0,
        networkDrops: 0,
        pastes: 0,
        riskScore: 0
      }
    });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  }
}));