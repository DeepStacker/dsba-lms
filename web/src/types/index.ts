// DSBA LMS TypeScript Type Definitions

// User & Authentication Types
export interface User {
  id: number;
  username: string;
  email: string;
  name: string;
  role: 'admin' | 'teacher' | 'student' | 'coordinator';
  is_active: boolean;
  mfa_enabled?: boolean;
  created_at?: string;
  last_login?: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
}

// API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  total?: number;
  skip?: number;
  limit?: number;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  total: number;
  page: number;
  pages: number;
  skip: number;
  limit: number;
}

// Educational Content Types
export interface Program {
  id: number;
  name: string;
  year: number;
  created_at: string;
  updated_at: string;
  courses?: Course[];
  pos?: PO[];
}

export interface Course {
  id: number;
  program_id: number;
  code: string;
  title: string;
  credits: number;
  created_at: string;
  updated_at: string;
  program?: Program;
  cos?: CO[];
}

export interface PO {
  id: number;
  program_id: number;
  code: string;
  title: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface CO {
  id: number;
  course_id: number;
  code: string;
  title: string;
  bloom: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface CO_PO_Map {
  id: number;
  co_id: number;
  po_id: number;
  weight: number;
  created_at: string;
}

// Question & Assessment Types
export type QuestionType = 'mcq' | 'msq' | 'tf' | 'numeric' | 'descriptive' | 'coding' | 'file_upload';

export interface QuestionOption {
  id: number;
  question_id: number;
  text: string;
  is_correct: boolean;
}

export interface Question {
  id: number;
  text: string;
  type: QuestionType;
  max_marks: number;
  co_id?: number;
  model_answer?: string;
  meta?: Record<string, any>;
  created_by: number;
  created_at: string;
  updated_at: string;
  options?: QuestionOption[];
  creator?: User;
  co?: CO;
}

// Class & Enrollment Types
export interface ClassSection {
  id: number;
  course_id: number;
  name: string;
  term: string;
  year: number;
  created_at: string;
  updated_at: string;
  course?: Course;
  students_count?: number;
}

export interface Enrollment {
  id: number;
  class_id: number;
  student_id: number;
  enrolled_at: string;
}

// Exam Types
export type ExamStatus = 'draft' | 'published' | 'started' | 'ended' | 'results_published';

export interface Exam {
  id: number;
  class_id: number;
  title: string;
  start_at: string;
  end_at: string;
  join_window_sec: number;
  settings_json?: Record<string, any>;
  status: ExamStatus;
  created_at: string;
  updated_at: string;
  class_section?: ClassSection;
}

export interface ExamQuestion {
  id: number;
  exam_id: number;
  question_id: number;
  order: number;
  marks_override?: number;
}

// Attempt & Response Types
export type AttemptStatus = 'not_started' | 'in_progress' | 'submitted' | 'auto_submitted';

export interface Attempt {
  id: number;
  exam_id: number;
  student_id: number;
  started_at?: string;
  submitted_at?: string;
  status: AttemptStatus;
  autosubmitted: boolean;
  student?: User;
  exam?: Exam;
}

export interface Response {
  id: number;
  attempt_id: number;
  question_id: number;
  answer_json: Record<string, any>;
  ai_score?: number;
  teacher_score?: number;
  final_score?: number;
  feedback?: string;
  audit_json?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Proctoring Types
export type ProctorEventType = 'tab_switch' | 'focus_loss' | 'network_drop' | 'paste' | 'fullscreen_exit';

export interface ProctorLog {
  id: number;
  attempt_id: number;
  ts: string;
  event_type: ProctorEventType;
  payload?: Record<string, any>;
}

export interface ProctorSettings {
  enable_tab_switch_detection: boolean;
  enable_focus_loss_detection: boolean;
  enable_paste_detection: boolean;
  enable_fullscreen_monitoring: boolean;
  risk_threshold: number;
  alert_threshold: number;
}

export interface ProctorStats {
  tab_switches: number;
  focus_losses: number;
  network_drops: number;
  pastes: number;
  fullscreen_exits: number;
  total_risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

// Grading Types
export interface GradeResponse {
  response_id: number;
  ai_score?: number;
  teacher_score?: number;
  final_score?: number;
  feedback?: string;
  per_criterion?: Record<string, number>;
}

export interface AIGradeRequest {
  strictness?: number;
}

export interface TeacherGradeRequest {
  teacher_score: number;
  reason?: string;
}

export interface BulkGradeRequest {
  exam_id: number;
  strictness?: number;
}

// Analytics & Reports Types
export interface COReport {
  co_id: number;
  co_code: string;
  co_title: string;
  attainment_percentage: number;
  student_count: number;
  assessments_count: number;
  avg_score: number;
}

export interface POReport {
  po_id: number;
  po_code: string;
  po_title: string;
  attainment_percentage: number;
  co_contributions: COReport[];
  overall_weight: number;
}

export interface GradeDistribution {
  grade: string;
  score_range: string;
  count: number;
  percentage: number;
}

export interface ExamStats {
  total_participants: number;
  completed: number;
  average_score: number;
  median_score: number;
  std_deviation: number;
  grade_distribution: GradeDistribution[];
  co_attainments: COReport[];
  po_attainments: POReport[];
}

export interface SGPAReport {
  student_id: number;
  student_name: string;
  academic_year: string;
  semester: string;
  sgpa: number;
  total_credits: number;
  grade_points_earned: number;
  course_grades: Array<{
    course_id: number;
    course_code: string;
    course_title: string;
    credits: number;
    marks?: number;
    grade_point: number;
    grade: string;
  }>;
}

export interface CGPAReport extends SGPAReport {
  cgpa: number;
  semesters_included: number;
  cumulative_credits: number;
}

// Dashboard Types
export interface DashboardCard {
  title: string;
  value: string;
  icon: React.ComponentType;
  change?: string;
  changeType?: 'increase' | 'decrease' | 'neutral';
}

export interface SystemStats {
  users: {
    total: number;
    by_role: Record<string, number>;
  };
  exams: {
    total: number;
    active: number;
    completed: number;
  };
  questions: {
    total: number;
    by_type: Record<string, number>;
    by_difficulty: Record<string, number>;
  };
  assignments: {
    pending_grading: number;
    completed_today: number;
  };
}

// Form Types
export interface LoginFormData {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface UserCreateFormData {
  username: string;
  email: string;
  name: string;
  role: User['role'];
  password: string;
}

export interface ExamCreationFormData {
  title: string;
  class_id: number;
  start_at: string;
  end_at: string;
  join_window_sec: number;
  duration_minutes: number;
  instructions?: string;
  settings: {
    max_attempts: number;
    show_results_immediately: boolean;
    allow_review: boolean;
    randomize_questions: boolean;
    time_limit_enforced: boolean;
    proctoring_enabled: boolean;
  };
}

// Configuration Types
export interface GradeBand {
  from: number;
  to: number;
  grade: string;
  grade_point: number;
  description?: string;
}

export interface SystemConfig {
  grade_bands: GradeBand[];
  lock_policy: {
    default_days: number;
    weekly_lock_saturday: boolean;
    override_requires_justification: boolean;
  };
  ai_settings: {
    enabled: boolean;
    grading_strictness: number;
    fallback_enabled: boolean;
    credit_quota_monthly?: number;
  };
  security_settings: {
    mfa_required_for_admins: boolean;
    password_min_length: number;
    session_timeout_minutes: number;
  };
}

// Error Types
export interface ApiError {
  message: string;
  code: string;
  details?: Record<string, any>;
}

export type ComponentStatus = 'idle' | 'loading' | 'success' | 'error';

// Table/Sort Types
export interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

export interface TableColumn<T = any> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  render?: (value: any, item: T) => React.ReactNode;
}

// Notification Types
export interface NotificationType {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  timestamp: Date;
  read?: boolean;
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
}

// Export Types
export interface ExportOptions {
  format: 'csv' | 'excel' | 'pdf' | 'json';
  includeHeaders?: boolean;
  dateRange?: {
    from: string;
    to: string;
  };
  filters?: Record<string, any>;
}

// Real-time/WebSocket Types
export interface WebSocketMessage {
  type: 'exam_event' | 'proctor_alert' | 'grading_complete' | 'notification';
  payload: any;
  timestamp: string;
}

// Feature Flags
export interface FeatureFlags {
  ai_grading: boolean;
  proctoring_lite: boolean;
  bulk_operations: boolean;
  advanced_analytics: boolean;
  email_notifications: boolean;
  sms_alerts: boolean;
}

// Component Prop Types (common)
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
  id?: string;
}

export interface LoadingProps extends BaseComponentProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

export interface ErrorBoundaryProps extends BaseComponentProps {
  fallback?: React.ComponentType<{ error: Error; retry: () => void }>;
  onError?: (error: Error) => void;
}

// Accessibility Types
export interface AriaProps {
  'aria-label'?: string;
  'aria-describedby'?: string;
  'aria-expanded'?: boolean;
  'aria-controls'?: string;
  role?: string;
}

// Modal/Dialog Types
export interface ModalProps extends BaseComponentProps, AriaProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnBackdropClick?: boolean;
  closeOnEsc?: boolean;
}

// Filter/Search Types
export interface FilterOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

export interface SearchParams {
  query?: string;
  filters?: Record<string, any>;
  sort?: SortConfig;
  pagination?: {
    page: number;
    limit: number;
  };
}

// File Upload Types
export interface FileUploadResult {
  success: boolean;
  url?: string;
  filename: string;
  size: number;
  type: string;
  error?: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// Menu/Navigation Types
export interface MenuItem {
  id: string;
  label: string;
  icon?: React.ComponentType;
  href?: string;
  action?: () => void;
  children?: MenuItem[];
  disabled?: boolean;
  badge?: string | number;
}

// Chart/Data Visualization Types
export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
  x?: number | string;
  y?: number | string;
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'area' | 'scatter';
  data: ChartDataPoint[];
  title?: string;
  xAxis?: {
    label: string;
    format?: (value: any) => string;
  };
  yAxis?: {
    label: string;
    format?: (value: any) => string;
  };
  legend?: boolean;
  colors?: string[];
}