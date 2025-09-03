import { jwtDecode } from 'jwt-decode';

// API Configuration
export const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';
export const AI_SERVICE_URL = (import.meta as any).env?.VITE_AI_SERVICE_URL || 'http://localhost:8001';

// API Endpoints
export const API_ENDPOINTS = {
  // Authentication
  auth: {
    login: '/auth/login',
    logout: '/auth/logout',
    refresh: '/auth/refresh',
    register: '/auth/register',
    forgotPassword: '/auth/forgot-password',
    resetPassword: '/auth/reset-password',
    setupAccount: '/auth/setup-account',
    enableMFA: '/auth/mfa/enable',
    verifyMFA: '/auth/mfa/verify',
  },

  // Users
  users: {
    me: '/users/me',
    changePassword: '/users/me/change-password',
    updateProfile: '/users/me',
    list: '/users',
    create: '/users',
    get: (id: number) => `/users/${id}`,
    update: (id: number) => `/users/${id}`,
    delete: (id: number) => `/users/${id}`,
    bulkImport: '/users/bulk-import',
    bulkResetPassword: '/users/bulk-reset-password',
  },

  // Programs and Courses
  programs: {
    list: '/programs',
    create: '/programs',
    get: (id: number) => `/programs/${id}`,
    update: (id: number) => `/programs/${id}`,
    delete: (id: number) => `/programs/${id}`,
  },

  courses: {
    list: '/courses',
    create: '/courses',
    get: (id: number) => `/courses/${id}`,
    update: (id: number) => `/courses/${id}`,
    delete: (id: number) => `/courses/${id}`,
    classes: (id: number) => `/courses/${id}/classes`,
  },

  // Classes and Enrollments
  classes: {
    list: '/classes',
    create: '/classes',
    get: (id: number) => `/classes/${id}`,
    update: (id: number) => `/classes/${id}`,
    delete: (id: number) => `/classes/${id}`,
    enrollments: (id: number) => `/classes/${id}/enrollments`,
    enroll: (id: number) => `/classes/${id}/enroll`,
    unenroll: (id: number) => `/classes/${id}/unenroll`,
  },

  // CO/PO Management
  outcomes: {
    cos: '/outcomes/cos',
    pos: '/outcomes/pos',
    mappings: '/outcomes/mappings',
    co: (id: number) => `/outcomes/cos/${id}`,
    po: (id: number) => `/outcomes/pos/${id}`,
    map: (coId: number, poId: number) => `/outcomes/mappings/co/${coId}/po/${poId}`,
  },

  // Question Bank
  questions: {
    list: '/questions',
    create: '/questions',
    get: (id: number) => `/questions/${id}`,
    update: (id: number) => `/questions/${id}`,
    delete: (id: number) => `/questions/${id}`,
    options: (id: number) => `/questions/${id}/options`,
    search: '/questions/search',
    bulkImport: '/questions/bulk-import',
    stats: (courseId: number) => `/questions/stats/course/${courseId}`,
  },

  // Exams
  exams: {
    list: '/exams',
    create: '/exams',
    get: (id: number) => `/exams/${id}`,
    update: (id: number) => `/exams/${id}`,
    delete: (id: number) => `/exams/${id}`,
    publish: (id: number) => `/exams/${id}/publish`,
    results: (id: number) => `/exams/${id}/results`,
    start: (id: number) => `/exams/${id}/start`,
    end: (id: number) => `/exams/${id}/end`,
    monitor: (id: number) => `/exams/${id}/monitor`,
    questions: (id: number) => `/exams/${id}/questions`,
    bulkAddQuestions: (id: number) => `/exams/${id}/questions/bulk`,
  },

  // Student Exam Operations
  student: {
    exams: '/student/exams',
    join: (id: number) => `/student/exams/${id}/join`,
    submit: (id: number) => `/student/exams/${id}/submit`,
    answer: `/student/answers`,
    results: (id: number) => `/student/results/${id}`,
    dashboard: '/student/dashboard',
  },

  // Grading
  grading: {
    list: '/grading',
    aiGrade: (id: number) => `/grading/ai/descriptive/${id}`,
    bulkAIGrade: '/grading/bulk/ai',
    teacherOverride: (id: number) => `/grading/override/${id}`,
    bulkOverride: '/grading/bulk/override',
    progress: (id: number) => `/grading/exam/${id}/progress`,
  },

  // Analytics & Reports
  analytics: {
    system: '/analytics/system',
    course: (id: number) => `/analytics/course/${id}`,
    exam: (id: number) => `/analytics/exam/${id}`,
    student: (id: number) => `/analytics/student/${id}`,
    sgpacgpa: (id: number) => `/analytics/student/${id}/sgpa-cgpa`,
    coAttainment: `/analytics/co-attainment`,
    poAttainment: `/analytics/po-attainment`,
  },

  // AI Services
  ai: {
    gradeDescriptive: '/ai/grade/descriptive',
    gradeCoding: '/ai/grade/coding',
    gradeBulk: '/ai/grade/bulk',
    generateQuestions: '/ai/questions/generate',
    generateContent: '/ai/content/generate',
    analyzePerformance: '/ai/analyze/performance',
    studyPlan: '/ai/study-plan/create',
    doubtBot: '/ai/doubt-bot/query',
  },

  // Audit & Security
  audit: {
    logs: '/audit/logs',
    export: '/audit/export',
  },

  // Notifications
  notifications: {
    list: '/notifications',
    send: '/notifications/send',
    bulk: '/notifications/bulk-send',
    templates: '/notifications/templates',
  },

  // Files & Uploads
  files: {
    upload: '/files/upload',
    download: (fileName: string) => `/files/download/${fileName}`,
    list: '/files',
    delete: (fileName: string) => `/files/${fileName}`,
  },
};

// HTTP Utility Functions
export interface ApiResponse<T = any> {
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  pagination?: {
    total: number;
    page: number;
    limit: number;
    pages: number;
  };
}

export class ApiClient {
  private baseURL: string;
  private authToken: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.authToken = this.getStoredToken();
  }

  private getStoredToken(): string | null {
    return localStorage.getItem('accessToken');
  }

  private async refreshToken(): Promise<void> {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await fetch(`${this.baseURL}${API_ENDPOINTS.auth.refresh}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('accessToken', data.access_token);
        localStorage.setItem('refreshToken', data.refresh_token);
        this.authToken = data.access_token;
      } else {
        // Refresh failed, clear tokens
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        this.authToken = null;
        throw new Error('Token refresh failed');
      }
    } catch (error) {
      throw error;
    }
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.authToken) {
      // Check if token is expired
      try {
        const decodedToken: any = jwtDecode(this.authToken);
        const currentTime = Date.now() / 1000;

        if (decodedToken.exp < currentTime) {
          // Token is expired, try to refresh
          await this.refreshToken();
        }
      } catch (error) {
        // Token is invalid, clear it
        this.authToken = null;
        localStorage.removeItem('accessToken');
      }
    }

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    if (response.ok) {
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        const data = await response.json();

        // Handle paginated responses
        if (data.total !== undefined) {
          return {
            data,
            pagination: {
              total: data.total,
              page: data.skip / data.limit + 1 || 1,
              limit: data.limit,
              pages: Math.ceil(data.total / data.limit),
            },
          };
        }

        return { data };
      } else {
        return { data: response.statusText as any };
      }
    } else if (response.status === 401) {
      // Unauthorized - clear tokens and redirect to login
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      this.authToken = null;
      window.location.href = '/login';
      throw new Error('Unauthorized');
    } else if (response.status === 403) {
      throw new Error('Access forbidden');
    } else {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
    }
  }

  async get<T = any>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    const headers = await this.getAuthHeaders();

    // Build URL with query parameters
    const url = new URL(`${this.baseURL}${endpoint}`);
    if (params) {
      Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== undefined) {
          url.searchParams.append(key, params[key].toString());
        }
      });
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers,
    });

    return this.handleResponse<T>(response);
  }

  async post<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    const headers = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  async put<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    const headers = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'PUT',
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  async patch<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    const headers = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'PATCH',
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  async delete<T = any>(endpoint: string): Promise<ApiResponse<T>> {
    const headers = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'DELETE',
      headers,
    });

    return this.handleResponse<T>(response);
  }

  async upload(endpoint: string, formData: FormData): Promise<ApiResponse> {
    const authHeaders = await this.getAuthHeaders();
    // Remove Content-Type for FormData
    const { 'Content-Type': _, ...headers } = authHeaders;

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers,
      body: formData,
    });

    return this.handleResponse(response);
  }
}

// Singleton instance
export const apiClient = new ApiClient();

// Helper functions
export const fetchWithErrorHandling = async <T>(
  request: Promise<ApiResponse<T>>,
  defaultErrorMessage: string = 'An error occurred'
): Promise<T> => {
  try {
    const response = await request;

    if (response.error) {
      throw new Error(response.error.message || defaultErrorMessage);
    }

    if (response.data === undefined) {
      throw new Error('No data returned from API');
    }

    return response.data;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    } else {
      throw new Error(defaultErrorMessage);
    }
  }
};

// Specific API call helpers
export const authApi = {
  async login(username: string, password: string) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.auth.login, { username, password }),
      'Login failed'
    );
  },

  async logout() {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.auth.logout),
      'Logout failed'
    );
  },

  async refreshToken(refreshToken: string) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.auth.refresh, { refresh_token: refreshToken }),
      'Token refresh failed'
    );
  },

  async getCurrentUser() {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.users.me),
      'Failed to fetch user profile'
    );
  },
};

export const usersApi = {
  async getUsers(params?: { skip?: number; limit?: number; search?: string; role?: string }) {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.users.list, params),
      'Failed to fetch users'
    );
  },

  async createUser(userData: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.users.create, userData),
      'Failed to create user'
    );
  },

  async updateUser(userId: number, userData: any) {
    return fetchWithErrorHandling(
      apiClient.put(API_ENDPOINTS.users.update(userId), userData),
      'Failed to update user'
    );
  },

  async deleteUser(userId: number) {
    return fetchWithErrorHandling(
      apiClient.delete(API_ENDPOINTS.users.delete(userId)),
      'Failed to delete user'
    );
  },

  async bulkImportUsers(file: File, role: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('role', role);

    return fetchWithErrorHandling(
      apiClient.upload(API_ENDPOINTS.users.bulkImport, formData),
      'Failed to import users'
    );
  },
};

export const examsApi = {
  async getExams(params?: { skip?: number; limit?: number; status?: string }) {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.exams.list, params),
      'Failed to fetch exams'
    );
  },

  async createExam(examData: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.exams.create, examData),
      'Failed to create exam'
    );
  },

  async getExam(examId: number) {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.exams.get(examId)),
      'Failed to fetch exam'
    );
  },

  async updateExam(examId: number, examData: any) {
    return fetchWithErrorHandling(
      apiClient.put(API_ENDPOINTS.exams.update(examId), examData),
      'Failed to update exam'
    );
  },

  async publishExam(examId: number) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.exams.publish(examId)),
      'Failed to publish exam'
    );
  },

  async deleteExam(examId: number) {
    return fetchWithErrorHandling(
      apiClient.delete(API_ENDPOINTS.exams.delete(examId)),
      'Failed to delete exam'
    );
  },

  async addQuestionsToExam(examId: number, questionsData: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.exams.bulkAddQuestions(examId), questionsData),
      'Failed to add questions to exam'
    );
  },
};

export const questionsApi = {
  async getQuestions(params?: { skip?: number; limit?: number; courseId?: number; type?: string }) {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.questions.list, params),
      'Failed to fetch questions'
    );
  },

  async searchQuestions(query: string, filters?: any) {
    const params = { query, ...filters };
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.questions.search, params),
      'Failed to search questions'
    );
  },

  async createQuestion(questionData: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.questions.create, questionData),
      'Failed to create question'
    );
  },

  async getQuestion(questionId: number) {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.questions.get(questionId)),
      'Failed to fetch question'
    );
  },

  async updateQuestion(questionId: number, questionData: any) {
    return fetchWithErrorHandling(
      apiClient.put(API_ENDPOINTS.questions.update(questionId), questionData),
      'Failed to update question'
    );
  },

  async deleteQuestion(questionId: number) {
    return fetchWithErrorHandling(
      apiClient.delete(API_ENDPOINTS.questions.delete(questionId)),
      'Failed to delete question'
    );
  },
};

export const analyticsApi = {
  async getAnalytics(type: string, id?: number, params?: any) {
    let endpoint: string;
    switch (type) {
      case 'system':
        endpoint = API_ENDPOINTS.analytics.system;
        break;
      case 'course':
        endpoint = API_ENDPOINTS.analytics.course(id!);
        break;
      case 'exam':
        endpoint = API_ENDPOINTS.analytics.exam(id!);
        break;
      case 'student':
        endpoint = API_ENDPOINTS.analytics.student(id!);
        break;
      default:
        throw new Error(`Invalid analytics type: ${type}`);
    }

    return fetchWithErrorHandling(
      apiClient.get(endpoint, params),
      'Failed to fetch analytics'
    );
  },

  async getSGPA(studentId: number, semester?: number, academicYear?: string) {
    return fetchWithErrorHandling(
      apiClient.get(`${API_ENDPOINTS.analytics.sgpacgpa(studentId)}/sgpa`, { semester, academic_year: academicYear }),
      'Failed to fetch SGPA'
    );
  },

  async getCGPA(studentId: number, semester?: number, academicYear?: string) {
    return fetchWithErrorHandling(
      apiClient.get(`${API_ENDPOINTS.analytics.sgpacgpa(studentId)}/cgpa`, { semester, academic_year: academicYear }),
      'Failed to fetch CGPA'
    );
  },
};

export const gradingApi = {
  async gradeAIDescriptive(responseId: number, gradingData: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.grading.aiGrade(responseId), gradingData),
      'Failed to get AI grading'
    );
  },

  async bulkAIGrading(examId: number, gradingConfig: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.grading.bulkAIGrade, { exam_id: examId, ...gradingConfig }),
      'Failed to start bulk AI grading'
    );
  },

  async teacherOverrideGrade(responseId: number, gradeData: any) {
    return fetchWithErrorHandling(
      apiClient.put(API_ENDPOINTS.grading.teacherOverride(responseId), gradeData),
      'Failed to override grade'
    );
  },

  async bulkTeacherOverride(gradesData: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.grading.bulkOverride, gradesData),
      'Failed to apply bulk grade overrides'
    );
  },

  async getGradingProgress(examId: number) {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.grading.progress(examId)),
      'Failed to fetch grading progress'
    );
  },
};

export const studentApi = {
  async getStudentExams() {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.student.exams),
      'Failed to fetch student exams'
    );
  },

  async joinExam(examId: number, sessionToken?: string) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.student.join(examId), { session_token: sessionToken }),
      'Failed to join exam'
    );
  },

  async submitAnswer(answerData: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.student.answer, answerData),
      'Failed to submit answer'
    );
  },

  async submitExam(examId: number) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.student.submit(examId)),
      'Failed to submit exam'
    );
  },

  async getResults(attemptId: number) {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.student.results(attemptId)),
      'Failed to fetch results'
    );
  },

  async getStudentDashboard() {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.student.dashboard),
      'Failed to fetch dashboard'
    );
  },
};

export const aiApi = {
  async generateQuestions(syllabus: string, topics: string[], config: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.ai.generateQuestions, {
        syllabus,
        topics,
        ...config
      }),
      'Failed to generate questions'
    );
  },

  async generateContent(courseId: number, contentConfig: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.ai.generateContent, {
        course_id: courseId,
        ...contentConfig
      }),
      'Failed to generate content'
    );
  },

  async createStudyPlan(studentId: number, weakTopics: string[]) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.ai.studyPlan, {
        student_id: studentId,
        weak_topics: weakTopics
      }),
      'Failed to create study plan'
    );
  },

  async queryDoubtBot(query: string, context: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.ai.doubtBot, {
        query,
        context
      }),
      'Failed to query doubt bot'
    );
  },

  async analyzePerformance(studentId: number, examIds: number[]) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.ai.analyzePerformance, {
        student_id: studentId,
        exam_ids: examIds
      }),
      'Failed to analyze performance'
    );
  },
};

export const auditApi = {
  async getAuditLogs(params?: {
    skip?: number;
    limit?: number;
    startDate?: string;
    endDate?: string;
    userId?: number;
    action?: string;
    entityType?: string;
  }) {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.audit.logs, params),
      'Failed to fetch audit logs'
    );
  },

  async exportAuditLogs(params?: any) {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.audit.export, params),
      'Failed to export audit logs'
    );
  },
};

export const notificationsApi = {
  async getNotifications(params?: {
    skip?: number;
    limit?: number;
    unread?: boolean;
  }) {
    return fetchWithErrorHandling(
      apiClient.get(API_ENDPOINTS.notifications.list, params),
      'Failed to fetch notifications'
    );
  },

  async sendNotification(notificationData: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.notifications.send, notificationData),
      'Failed to send notification'
    );
  },

  async bulkSendNotifications(notificationsData: any) {
    return fetchWithErrorHandling(
      apiClient.post(API_ENDPOINTS.notifications.bulk, notificationsData),
      'Failed to send bulk notifications'
    );
  },
};
