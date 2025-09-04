from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class BulkGradeUploadItem(BaseModel):
    student_id: int = Field(..., description="Student ID")
    question_id: Optional[int] = Field(None, description="Question ID (optional, for per question grading)")
    score: float = Field(..., ge=0, description="Score for the item")
    max_score: float = Field(..., ge=0, description="Maximum possible score for the item")
    notes: Optional[str] = Field(None, description="Optional notes for this grade")

class BulkGradeUploadRequest(BaseModel):
    exam_id: Optional[int] = Field(None, description="Exam ID (optional, if grading individual questions within an exam)")
    class_id: Optional[int] = Field(None, description="Class ID (optional, if uploading overall internal marks for a class)")
    component_id: Optional[int] = Field(None, description="Internal Component ID (required for internal marks upload)")
    grades: List[BulkGradeUploadItem] = Field(..., description="List of grade items to upload")
    overwrite_existing: bool = Field(False, description="Whether to overwrite existing grades")
    
class BulkGradeUploadResponse(BaseModel):
    message: str
    total_records: int
    processed_records: int
    failed_records: int
    details: List[Dict[str, Any]] = Field([], description="Details of processed records, including errors")

class BulkMarksUploadPreview(BaseModel):
    filename: str
    columns: List[str]
    preview_data: List[Dict[str, Any]]
    suggested_mapping: Dict[str, str]
    message: str