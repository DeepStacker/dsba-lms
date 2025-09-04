from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime

class Response(BaseModel):
    message: str
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None

class BulkOperationResponse(BaseModel):
    success_count: int
    error_count: int
    total_count: int
    errors: List[str] = []
    warnings: List[str] = []

class FileUploadResponse(BaseModel):
    filename: str
    size: int
    content_type: str
    url: Optional[str] = None

class ExportResponse(BaseModel):
    filename: str
    download_url: str
    expires_at: datetime
    format: str  # csv, pdf, xlsx

class ValidationError(BaseModel):
    field: str
    message: str
    code: str

class APIError(BaseModel):
    message: str
    errors: List[ValidationError] = []
    timestamp: datetime
    path: str