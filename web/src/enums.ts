// Enums for DSBA LMS System

export enum UserRole {
  ADMIN = "admin",
  TEACHER = "teacher", 
  STUDENT = "student",
  COORDINATOR = "coordinator"
}

export enum QuestionType {
  MCQ = "mcq",
  MSQ = "msq", 
  TF = "tf",
  NUMERIC = "numeric",
  DESCRIPTIVE = "descriptive",
  CODING = "coding",
  FILE_UPLOAD = "file_upload"
}

export enum ExamStatus {
  DRAFT = "draft",
  PUBLISHED = "published",
  STARTED = "started", 
  ENDED = "ended",
  RESULTS_PUBLISHED = "results_published"
}

export enum AttemptStatus {
  NOT_STARTED = "not_started",
  IN_PROGRESS = "in_progress",
  SUBMITTED = "submitted",
  AUTO_SUBMITTED = "auto_submitted"
}

export enum ProctorEventType {
  TAB_SWITCH = "tab_switch",
  FOCUS_LOSS = "focus_loss",
  NETWORK_DROP = "network_drop", 
  PASTE = "paste",
  FULLSCREEN_EXIT = "fullscreen_exit"
}

export enum LockStatus {
  ACTIVE = "active",
  EXPIRED = "expired",
  OVERRIDDEN = "overridden"
}

export enum NotificationPriority {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high", 
  URGENT = "urgent"
}

export enum NotificationType {
  INFO = "info",
  SUCCESS = "success",
  WARNING = "warning",
  ERROR = "error"
}

export enum GradeType {
  O = "O",
  A_PLUS = "A+",
  A = "A", 
  B_PLUS = "B+",
  B = "B",
  C = "C",
  F = "F"
}

export enum ComponentStatus {
  IDLE = "idle",
  LOADING = "loading",
  SUCCESS = "success", 
  ERROR = "error"
}

export enum ExportFormat {
  PDF = "pdf",
  CSV = "csv",
  EXCEL = "excel",
  JSON = "json"
}

export enum RiskLevel {
  LOW = "low",
  MEDIUM = "medium", 
  HIGH = "high",
  CRITICAL = "critical"
}

export enum BloomLevel {
  REMEMBER = "remember",
  UNDERSTAND = "understand",
  APPLY = "apply",
  ANALYZE = "analyze", 
  EVALUATE = "evaluate",
  CREATE = "create"
}

export enum SortDirection {
  ASC = "asc",
  DESC = "desc"
}

export enum Theme {
  LIGHT = "light",
  DARK = "dark",
  SYSTEM = "system"
}