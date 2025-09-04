// Mock data for DSBA LMS System
import { UserRole, ExamStatus, QuestionType, AttemptStatus, ProctorEventType } from './enums';

// Mock store data for global state
export const mockStore = {
  user: {
    id: 1,
    username: "admin@dsba.edu",
    email: "admin@dsba.edu", 
    name: "Dr. John Smith",
    role: UserRole.ADMIN as const,
    department: "Computer Science",
    is_active: true,
    first_login: false,
    created_at: "2024-01-15T08:00:00Z",
    last_login: "2024-12-19T10:30:00Z"
  },
  notifications: [
    {
      id: 1,
      title: "New Exam Published",
      message: "CS101 Final Exam has been published and is ready for students",
      read: false,
      created_at: "2024-12-19T09:15:00Z"
    },
    {
      id: 2, 
      title: "Grading Complete",
      message: "AI grading completed for Data Structures midterm exam",
      read: false,
      created_at: "2024-12-19T08:45:00Z"
    }
  ],
  systemStats: {
    totalUsers: 1247,
    activeExams: 8,
    totalQuestions: 2156,
    pendingGrades: 45,
    systemHealth: "healthy" as const
  }
};

// Mock API query responses
export const mockQuery = {
  users: [
    {
      id: 1,
      username: "admin@dsba.edu",
      email: "admin@dsba.edu",
      name: "Dr. John Smith", 
      role: UserRole.ADMIN as const,
      department: "Computer Science",
      is_active: true,
      created_at: "2024-01-15T08:00:00Z",
      last_login: "2024-12-19T10:30:00Z"
    },
    {
      id: 2,
      username: "prof.wilson@dsba.edu", 
      email: "prof.wilson@dsba.edu",
      name: "Prof. Sarah Wilson",
      role: UserRole.TEACHER as const,
      department: "Computer Science",
      is_active: true,
      created_at: "2024-02-01T09:00:00Z",
      last_login: "2024-12-19T09:45:00Z"
    },
    {
      id: 3,
      username: "student.doe@dsba.edu",
      email: "student.doe@dsba.edu", 
      name: "Jane Doe",
      role: UserRole.STUDENT as const,
      department: "Computer Science",
      is_active: true,
      created_at: "2024-08-15T10:00:00Z",
      last_login: "2024-12-19T11:20:00Z"
    }
  ],
  programs: [
    {
      id: 1,
      name: "Bachelor of Computer Applications",
      year: 2024,
      created_at: "2024-01-10T00:00:00Z"
    },
    {
      id: 2,
      name: "Master of Computer Applications", 
      year: 2024,
      created_at: "2024-01-10T00:00:00Z"
    }
  ],
  courses: [
    {
      id: 1,
      program_id: 1,
      code: "CS101",
      title: "Introduction to Programming",
      credits: 4.0,
      created_at: "2024-01-15T00:00:00Z"
    },
    {
      id: 2,
      program_id: 1,
      code: "CS201", 
      title: "Data Structures and Algorithms",
      credits: 4.0,
      created_at: "2024-01-15T00:00:00Z"
    },
    {
      id: 3,
      program_id: 1,
      code: "CS301",
      title: "Database Management Systems",
      credits: 3.0,
      created_at: "2024-01-15T00:00:00Z"
    }
  ],
  exams: [
    {
      id: 1,
      class_id: 1,
      title: "CS101 Midterm Examination",
      start_at: "2024-12-20T10:00:00Z",
      end_at: "2024-12-20T12:00:00Z", 
      join_window_sec: 300,
      status: ExamStatus.PUBLISHED as const,
      created_at: "2024-12-15T00:00:00Z"
    },
    {
      id: 2,
      class_id: 2,
      title: "Data Structures Final Exam",
      start_at: "2024-12-22T14:00:00Z",
      end_at: "2024-12-22T17:00:00Z",
      join_window_sec: 300, 
      status: ExamStatus.DRAFT as const,
      created_at: "2024-12-18T00:00:00Z"
    }
  ],
  questions: [
    {
      id: 1,
      text: "What is the time complexity of binary search algorithm?",
      type: QuestionType.MCQ as const,
      max_marks: 2.0,
      co_id: 1,
      created_by: 2,
      created_at: "2024-12-10T00:00:00Z",
      options: [
        { id: 1, question_id: 1, text: "O(n)", is_correct: false },
        { id: 2, question_id: 1, text: "O(log n)", is_correct: true },
        { id: 3, question_id: 1, text: "O(n²)", is_correct: false },
        { id: 4, question_id: 1, text: "O(1)", is_correct: false }
      ]
    },
    {
      id: 2,
      text: "Explain the concept of inheritance in object-oriented programming with examples.",
      type: QuestionType.DESCRIPTIVE as const,
      max_marks: 10.0,
      co_id: 2,
      model_answer: "Inheritance is a fundamental concept in OOP that allows a class to inherit properties and methods from another class...",
      created_by: 2,
      created_at: "2024-12-10T00:00:00Z"
    }
  ],
  attempts: [
    {
      id: 1,
      exam_id: 1,
      student_id: 3,
      started_at: "2024-12-20T10:05:00Z",
      submitted_at: "2024-12-20T11:45:00Z",
      status: AttemptStatus.SUBMITTED as const,
      autosubmitted: false
    }
  ],
  responses: [
    {
      id: 1,
      attempt_id: 1,
      question_id: 1,
      answer_json: { selected_option: 2 },
      ai_score: null,
      teacher_score: 2.0,
      final_score: 2.0,
      feedback: "Correct answer!",
      created_at: "2024-12-20T10:15:00Z"
    },
    {
      id: 2,
      attempt_id: 1, 
      question_id: 2,
      answer_json: { text: "Inheritance allows one class to acquire properties of another class..." },
      ai_score: 8.5,
      teacher_score: 9.0,
      final_score: 9.0,
      feedback: "Good explanation with examples. Could include more detail on method overriding.",
      created_at: "2024-12-20T10:25:00Z"
    }
  ],
  analytics: {
    studentPerformance: {
      sgpa: 8.5,
      cgpa: 8.3,
      totalCredits: 120,
      completedCourses: 8,
      currentSemester: "Spring 2024"
    },
    coAttainment: [
      {
        co_id: 1,
        co_code: "CO1",
        co_title: "Understand programming fundamentals",
        attainment_percentage: 85.5,
        student_count: 32,
        avg_score: 8.2
      },
      {
        co_id: 2,
        co_code: "CO2", 
        co_title: "Apply OOP concepts",
        attainment_percentage: 78.3,
        student_count: 32,
        avg_score: 7.8
      }
    ],
    systemStats: {
      totalUsers: 1247,
      activeExams: 8,
      totalQuestions: 2156,
      aiGradedResponses: 1834,
      teacherGradedResponses: 456,
      pendingGrades: 45
    }
  }
};

// Mock props data for root component
export const mockRootProps = {
  currentUser: {
    id: 1,
    username: "admin@dsba.edu",
    email: "admin@dsba.edu",
    name: "Dr. John Smith",
    role: UserRole.ADMIN as const,
    department: "Computer Science",
    is_active: true
  },
  dashboardType: "admin" as const,
  initialData: {
    stats: {
      totalUsers: 1247,
      activeExams: 8, 
      totalQuestions: 2156,
      pendingGrades: 45
    },
    recentActivities: [
      {
        id: 1,
        type: "user_created" as const,
        description: "New student Jane Doe registered",
        timestamp: "2024-12-19T09:30:00Z"
      },
      {
        id: 2,
        type: "exam_published" as const,
        description: "CS101 Final Exam published",
        timestamp: "2024-12-19T08:15:00Z"
      }
    ]
  },
  permissions: {
    canCreateUsers: true,
    canManageExams: true,
    canViewAnalytics: true,
    canExportReports: true,
    canManageSystem: true
  }
};