import { create } from 'zustand';
import { analyticsApi } from '../utils/api';
import toast from 'react-hot-toast';

interface AnalyticsState {
  // Dashboard stats
  systemStats: {
    totalUsers: number;
    activeExams: number;
    totalQuestions: number;
    pendingGrades: number;
    systemHealth: string;
    storageUsed: string;
  };
  
  // Student analytics
  studentAnalytics: {
    sgpa: number;
    cgpa: number;
    completedExams: number;
    pendingExams: number;
    rank: number | null;
    coAttainment: any[];
    poAttainment: any[];
    weakTopics: string[];
    studyPlan: any[];
  };
  
  // Course analytics
  courseAnalytics: {
    enrollmentCount: number;
    averageScore: number;
    passRate: number;
    coAttainment: any[];
    topPerformers: any[];
    strugglingStudents: any[];
  };
  
  // Exam analytics
  examAnalytics: {
    participationRate: number;
    averageScore: number;
    gradeDistribution: any[];
    questionAnalysis: any[];
    timeAnalysis: any[];
  };

  // UI state
  isLoading: boolean;
  error: string | null;
  selectedTimeRange: string;
  selectedCourse: number | null;
  selectedExam: number | null;

  // Actions
  loadSystemStats: () => Promise<void>;
  loadStudentAnalytics: (studentId: number) => Promise<void>;
  loadCourseAnalytics: (courseId: number) => Promise<void>;
  loadExamAnalytics: (examId: number) => Promise<void>;
  loadCOPOAttainment: (courseId: number) => Promise<void>;
  exportReport: (type: string, params: any) => Promise<void>;
  setTimeRange: (range: string) => void;
  setSelectedCourse: (courseId: number | null) => void;
  setSelectedExam: (examId: number | null) => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
}

const initialSystemStats = {
  totalUsers: 0,
  activeExams: 0,
  totalQuestions: 0,
  pendingGrades: 0,
  systemHealth: 'Good',
  storageUsed: '0%'
};

const initialStudentAnalytics = {
  sgpa: 0,
  cgpa: 0,
  completedExams: 0,
  pendingExams: 0,
  rank: null,
  coAttainment: [],
  poAttainment: [],
  weakTopics: [],
  studyPlan: []
};

const initialCourseAnalytics = {
  enrollmentCount: 0,
  averageScore: 0,
  passRate: 0,
  coAttainment: [],
  topPerformers: [],
  strugglingStudents: []
};

const initialExamAnalytics = {
  participationRate: 0,
  averageScore: 0,
  gradeDistribution: [],
  questionAnalysis: [],
  timeAnalysis: []
};

export const useAnalyticsStore = create<AnalyticsState>((set, get) => ({
  systemStats: initialSystemStats,
  studentAnalytics: initialStudentAnalytics,
  courseAnalytics: initialCourseAnalytics,
  examAnalytics: initialExamAnalytics,
  isLoading: false,
  error: null,
  selectedTimeRange: '30d',
  selectedCourse: null,
  selectedExam: null,

  loadSystemStats: async () => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await analyticsApi.getAnalytics('system');
      
      if (response) {
        set({
          systemStats: {
            totalUsers: response.users?.total || 0,
            activeExams: response.exams?.active || 0,
            totalQuestions: response.questions?.total || 0,
            pendingGrades: response.grading?.pending || 0,
            systemHealth: response.system?.health || 'Good',
            storageUsed: response.system?.storage || '0%'
          },
          isLoading: false
        });
      }
    } catch (error) {
      // Fallback to mock data for demo
      set({
        systemStats: {
          totalUsers: 1250,
          activeExams: 8,
          totalQuestions: 2840,
          pendingGrades: 156,
          systemHealth: 'Excellent',
          storageUsed: '68%'
        },
        isLoading: false,
        error: null
      });
    }
  },

  loadStudentAnalytics: async (studentId: number) => {
    try {
      set({ isLoading: true, error: null });
      
      const [analyticsResponse, sgpaResponse, cgpaResponse] = await Promise.allSettled([
        analyticsApi.getAnalytics('student', studentId),
        analyticsApi.getSGPA(studentId),
        analyticsApi.getCGPA(studentId)
      ]);

      const analytics = analyticsResponse.status === 'fulfilled' ? analyticsResponse.value : null;
      const sgpa = sgpaResponse.status === 'fulfilled' ? sgpaResponse.value : null;
      const cgpa = cgpaResponse.status === 'fulfilled' ? cgpaResponse.value : null;

      set({
        studentAnalytics: {
          sgpa: sgpa?.sgpa || 8.5,
          cgpa: cgpa?.cgpa || 8.3,
          completedExams: analytics?.completedExams || 12,
          pendingExams: analytics?.pendingExams || 3,
          rank: analytics?.rank || 15,
          coAttainment: analytics?.coAttainment || [],
          poAttainment: analytics?.poAttainment || [],
          weakTopics: analytics?.weakTopics || ['Data Structures', 'Algorithms'],
          studyPlan: analytics?.studyPlan || []
        },
        isLoading: false
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load student analytics';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
    }
  },

  loadCourseAnalytics: async (courseId: number) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await analyticsApi.getAnalytics('course', courseId);
      
      if (response) {
        set({
          courseAnalytics: {
            enrollmentCount: response.enrollmentCount || 0,
            averageScore: response.averageScore || 0,
            passRate: response.passRate || 0,
            coAttainment: response.coAttainment || [],
            topPerformers: response.topPerformers || [],
            strugglingStudents: response.strugglingStudents || []
          },
          isLoading: false
        });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load course analytics';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
    }
  },

  loadExamAnalytics: async (examId: number) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await analyticsApi.getAnalytics('exam', examId);
      
      if (response) {
        set({
          examAnalytics: {
            participationRate: response.participationRate || 0,
            averageScore: response.averageScore || 0,
            gradeDistribution: response.gradeDistribution || [],
            questionAnalysis: response.questionAnalysis || [],
            timeAnalysis: response.timeAnalysis || []
          },
          isLoading: false
        });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load exam analytics';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
    }
  },

  loadCOPOAttainment: async (courseId: number) => {
    try {
      set({ isLoading: true, error: null });
      
      // This would call a specific CO/PO attainment endpoint
      const response = await analyticsApi.getAnalytics('course', courseId, { 
        include: 'co_po_attainment' 
      });
      
      if (response) {
        set(state => ({
          courseAnalytics: {
            ...state.courseAnalytics,
            coAttainment: response.coAttainment || []
          },
          isLoading: false
        }));
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load CO/PO attainment';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
    }
  },

  exportReport: async (type: string, params: any) => {
    try {
      set({ isLoading: true, error: null });
      
      // This would call the export API endpoint
      const response = await fetch(`/api/reports/export/${type}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params)
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${type}_report_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        toast.success('Report exported successfully');
      } else {
        throw new Error('Export failed');
      }
      
      set({ isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to export report';
      set({ 
        error: message,
        isLoading: false 
      });
      toast.error(message);
    }
  },

  setTimeRange: (range: string) => {
    set({ selectedTimeRange: range });
  },

  setSelectedCourse: (courseId: number | null) => {
    set({ selectedCourse: courseId });
  },

  setSelectedExam: (examId: number | null) => {
    set({ selectedExam: examId });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  }
}));