from pydantic import BaseModel
from typing import Optional, Any, Dict

class Response(BaseModel):
    message: str
    data: Optional[Any] = None
    success: bool = True

class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    size: int
    pages: int

class ErrorResponse(BaseModel):
    message: str
    details: Optional[Dict[str, Any]] = None
    success: bool = False

class APIResponse(BaseModel):
    data: Optional[Any] = None
    message: Optional[str] = None
    success: bool = True
    errors: Optional[list[str]] = None