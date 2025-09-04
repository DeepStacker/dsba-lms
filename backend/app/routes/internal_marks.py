from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, text
from typing import List, Optional, Dict, Any
import pandas as pd
import io
from datetime import datetime
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_permission
from ..core.audit import log_audit_event, AUDIT_ACTIONS
from ..models.models import (
    User, Course, ClassSection, Enrollment, InternalComponent, InternalScore
)
from ..schemas.common import Response as CommonResponse, BulkOperationResponse
from pydantic import BaseModel, validator

router = APIRouter()

# ==================== INTERNAL MARKS MODELS ====================

class InternalComponentBase(BaseModel):
    name: str
    weight_percent: float

    @validator('weight_percent')
    def validate_weight(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Weight must be between 0 and 100')
        return v

class InternalComponentCreate(InternalComponentBase):
    course_id: int

class InternalComponentUpdate(BaseModel):
    name: Optional[str] = None
    weight_percent: Optional[float] = None

    @validator('weight_percent')
    def validate_weight(cls, v):
        if v is not None and (v <= 0 or v > 100):
            raise ValueError('Weight must be between 0 and 100')
        return v

class InternalComponentResponse(InternalComponentBase):
    id: int
    course_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class InternalScoreBase(BaseModel):
    raw_score: float
    max_score: float

    @validator('raw_score')
    def validate_raw_score(cls, v, values):
        if v < 0:
            raise ValueError('Raw score cannot be negative')
        return v

    @validator('max_score')
    def validate_max_score(cls, v):
        if v <= 0:
            raise ValueError('Max score must be positive')
        return v

class InternalScoreCreate(InternalScoreBase):
    student_id: int
    course_id: int
    component_id: int

class InternalScoreUpdate(BaseModel):
    raw_score: Optional[float] = None
    max_score: Optional[float] = None

class InternalScoreResponse(InternalScoreBase):
    id: int
    student_id: int
    course_id: int
    component_id: int
    created_at: datetime
    student_name: Optional[str] = None
    component_name: Optional[str] = None
    percentage: Optional[float] = None

    class Config:
        from_attributes = True

class BulkScoreUpload(BaseModel):
    scores: List[InternalScoreCreate]

class StudentInternalSummary(BaseModel):
    student_id: int
    student_name: str
    course_id: int
    course_name: str
    component_scores: List[Dict[str, Any]]
    total_weighted_score: float
    total_possible_score: float
    percentage: float
    grade: Optional[str] = None

# ==================== INTERNAL COMPONENTS CRUD ====================

@router.get("/components/course/{course_id}", response_model=List[InternalComponentResponse])
async def get_course_components(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all internal components for a course"""
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get components
    result = await db.execute(
        select(InternalComponent)
        .where(InternalComponent.course_id == course_id)
        .order_by(InternalComponent.name)
    )
    
    components = result.scalars().all()
    return [InternalComponentResponse.from_orm(comp) for comp in components]

@router.post("/components", response_model=InternalComponentResponse, status_code=status.HTTP_201_CREATED)
async def create_internal_component(
    component_data: InternalComponentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_courses"))
):
    """Create a new internal component"""
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == component_data.course_id))
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if total weight doesn't exceed 100%
    existing_weight_result = await db.execute(
        select(func.sum(InternalComponent.weight_percent))
        .where(InternalComponent.course_id == component_data.course_id)
    )
    
    existing_weight = existing_weight_result.scalar() or 0
    if existing_weight + component_data.weight_percent > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Total weight would exceed 100%. Current total: {existing_weight}%"
        )
    
    # Create component
    component = InternalComponent(**component_data.dict())
    db.add(component)
    await db.commit()
    await db.refresh(component)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="internal_component",
        entity_id=component.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json=component_data.dict(),
        reason="Created internal component"
    )
    
    return InternalComponentResponse.from_orm(component)

@router.put("/components/{component_id}", response_model=InternalComponentResponse)
async def update_internal_component(
    component_id: int,
    component_data: InternalComponentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_courses"))
):
    """Update internal component"""
    result = await db.execute(select(InternalComponent).where(InternalComponent.id == component_id))
    component = result.scalar_one_or_none()
    
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    # Check weight constraint if weight is being updated
    if component_data.weight_percent is not None:
        existing_weight_result = await db.execute(
            select(func.sum(InternalComponent.weight_percent))
            .where(
                and_(
                    InternalComponent.course_id == component.course_id,
                    InternalComponent.id != component_id
                )
            )
        )
        
        other_weights = existing_weight_result.scalar() or 0
        if other_weights + component_data.weight_percent > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total weight would exceed 100%. Other components total: {other_weights}%"
            )
    
    before_data = {"name": component.name, "weight_percent": component.weight_percent}
    update_data = component_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(component, field, value)
    
    await db.commit()
    await db.refresh(component)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="internal_component",
        entity_id=component_id,
        action=AUDIT_ACTIONS["UPDATE"],
        before_json=before_data,
        after_json=update_data,
        reason="Updated internal component"
    )
    
    return InternalComponentResponse.from_orm(component)

@router.delete("/components/{component_id}")
async def delete_internal_component(
    component_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_courses"))
):
    """Delete internal component"""
    result = await db.execute(select(InternalComponent).where(InternalComponent.id == component_id))
    component = result.scalar_one_or_none()
    
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    # Check if component has scores
    scores_result = await db.execute(
        select(InternalScore).where(InternalScore.component_id == component_id)
    )
    if scores_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete component with existing scores"
        )
    
    before_data = {"name": component.name, "weight_percent": component.weight_percent}
    await db.delete(component)
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="internal_component",
        entity_id=component_id,
        action=AUDIT_ACTIONS["DELETE"],
        before_json=before_data,
        reason="Deleted internal component"
    )
    
    return CommonResponse(message="Component deleted successfully")

# ==================== INTERNAL SCORES CRUD ====================

@router.get("/scores/course/{course_id}", response_model=List[InternalScoreResponse])
async def get_course_scores(
    course_id: int,
    component_id: Optional[int] = None,
    student_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get internal scores for a course"""
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Build query
    query = select(
        InternalScore,
        User.name.label('student_name'),
        InternalComponent.name.label('component_name')
    ).join(
        User, InternalScore.student_id == User.id
    ).join(
        InternalComponent, InternalScore.component_id == InternalComponent.id
    ).where(InternalScore.course_id == course_id)
    
    # Apply filters
    if component_id:
        query = query.where(InternalScore.component_id == component_id)
    if student_id:
        query = query.where(InternalScore.student_id == student_id)
    
    # Check permissions for student access
    if current_user.role.value == "student":
        query = query.where(InternalScore.student_id == current_user.id)
    
    query = query.order_by(User.name, InternalComponent.name)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    scores_data = result.all()
    
    # Format response
    scores = []
    for score, student_name, component_name in scores_data:
        score_dict = InternalScoreResponse.from_orm(score).dict()
        score_dict['student_name'] = student_name
        score_dict['component_name'] = component_name
        score_dict['percentage'] = round((score.raw_score / score.max_score) * 100, 2)
        scores.append(InternalScoreResponse(**score_dict))
    
    return scores

@router.post("/scores", response_model=InternalScoreResponse, status_code=status.HTTP_201_CREATED)
async def create_internal_score(
    score_data: InternalScoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade_students"))
):
    """Create a new internal score"""
    # Verify student, course, and component exist
    student_result = await db.execute(select(User).where(User.id == score_data.student_id))
    course_result = await db.execute(select(Course).where(Course.id == score_data.course_id))
    component_result = await db.execute(select(InternalComponent).where(InternalComponent.id == score_data.component_id))
    
    if not student_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Student not found")
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")
    if not component_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Component not found")
    
    # Check if score already exists
    existing_result = await db.execute(
        select(InternalScore).where(
            and_(
                InternalScore.student_id == score_data.student_id,
                InternalScore.course_id == score_data.course_id,
                InternalScore.component_id == score_data.component_id
            )
        )
    )
    
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Score already exists for this student and component"
        )
    
    # Validate score
    if score_data.raw_score > score_data.max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Raw score cannot exceed max score"
        )
    
    # Create score
    score = InternalScore(**score_data.dict())
    db.add(score)
    await db.commit()
    await db.refresh(score)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="internal_score",
        entity_id=score.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json=score_data.dict(),
        reason="Created internal score"
    )
    
    return InternalScoreResponse.from_orm(score)

@router.put("/scores/{score_id}", response_model=InternalScoreResponse)
async def update_internal_score(
    score_id: int,
    score_data: InternalScoreUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade_students"))
):
    """Update internal score"""
    result = await db.execute(select(InternalScore).where(InternalScore.id == score_id))
    score = result.scalar_one_or_none()
    
    if not score:
        raise HTTPException(status_code=404, detail="Score not found")
    
    before_data = {"raw_score": score.raw_score, "max_score": score.max_score}
    update_data = score_data.dict(exclude_unset=True)
    
    # Validate updated score
    new_raw_score = update_data.get('raw_score', score.raw_score)
    new_max_score = update_data.get('max_score', score.max_score)
    
    if new_raw_score > new_max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Raw score cannot exceed max score"
        )
    
    for field, value in update_data.items():
        setattr(score, field, value)
    
    await db.commit()
    await db.refresh(score)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="internal_score",
        entity_id=score_id,
        action=AUDIT_ACTIONS["UPDATE"],
        before_json=before_data,
        after_json=update_data,
        reason="Updated internal score"
    )
    
    return InternalScoreResponse.from_orm(score)

@router.delete("/scores/{score_id}")
async def delete_internal_score(
    score_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade_students"))
):
    """Delete internal score"""
    result = await db.execute(select(InternalScore).where(InternalScore.id == score_id))
    score = result.scalar_one_or_none()
    
    if not score:
        raise HTTPException(status_code=404, detail="Score not found")
    
    before_data = {"raw_score": score.raw_score, "max_score": score.max_score}
    await db.delete(score)
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="internal_score",
        entity_id=score_id,
        action=AUDIT_ACTIONS["DELETE"],
        before_json=before_data,
        reason="Deleted internal score"
    )
    
    return CommonResponse(message="Score deleted successfully")

# ==================== BULK OPERATIONS ====================

@router.post("/scores/bulk", response_model=BulkOperationResponse)
async def bulk_create_scores(
    bulk_data: BulkScoreUpload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade_students"))
):
    """Bulk create internal scores"""
    success_count = 0
    error_count = 0
    errors = []
    
    for score_data in bulk_data.scores:
        try:
            # Verify entities exist
            student_result = await db.execute(select(User).where(User.id == score_data.student_id))
            course_result = await db.execute(select(Course).where(Course.id == score_data.course_id))
            component_result = await db.execute(select(InternalComponent).where(InternalComponent.id == score_data.component_id))
            
            if not all([student_result.scalar_one_or_none(), course_result.scalar_one_or_none(), component_result.scalar_one_or_none()]):
                errors.append(f"Invalid student, course, or component ID in score data")
                error_count += 1
                continue
            
            # Check for duplicates
            existing_result = await db.execute(
                select(InternalScore).where(
                    and_(
                        InternalScore.student_id == score_data.student_id,
                        InternalScore.course_id == score_data.course_id,
                        InternalScore.component_id == score_data.component_id
                    )
                )
            )
            
            if existing_result.scalar_one_or_none():
                errors.append(f"Score already exists for student {score_data.student_id}, component {score_data.component_id}")
                error_count += 1
                continue
            
            # Validate score
            if score_data.raw_score > score_data.max_score:
                errors.append(f"Raw score exceeds max score for student {score_data.student_id}")
                error_count += 1
                continue
            
            # Create score
            score = InternalScore(**score_data.dict())
            db.add(score)
            success_count += 1
            
        except Exception as e:
            errors.append(f"Error creating score: {str(e)}")
            error_count += 1
    
    if success_count > 0:
        await db.commit()
        
        await log_audit_event(
            db=db,
            actor_id=current_user.id,
            entity_type="internal_score",
            entity_id=None,
            action=AUDIT_ACTIONS["BULK_IMPORT"],
            after_json={
                "success_count": success_count,
                "error_count": error_count,
                "total_count": len(bulk_data.scores)
            },
            reason="Bulk internal scores upload"
        )
    
    return BulkOperationResponse(
        success_count=success_count,
        error_count=error_count,
        total_count=len(bulk_data.scores),
        errors=errors[:10]  # Limit to first 10 errors
    )

@router.post("/scores/upload")
async def upload_scores_file(
    course_id: int,
    component_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade_students"))
):
    """Upload internal scores from CSV/Excel file"""
    # Verify course and component exist
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    component_result = await db.execute(select(InternalComponent).where(InternalComponent.id == component_id))
    
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")
    if not component_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Component not found")
    
    # Validate file type
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be CSV or Excel format"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse file based on type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Validate required columns
        required_columns = ['student_id', 'raw_score', 'max_score']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {missing_columns}"
            )
        
        success_count = 0
        error_count = 0
        errors = []
        
        # Process each row
        for index, row in df.iterrows():
            try:
                student_id = int(row['student_id'])
                raw_score = float(row['raw_score'])
                max_score = float(row['max_score'])
                
                # Validate student exists
                student_result = await db.execute(select(User).where(User.id == student_id))
                if not student_result.scalar_one_or_none():
                    errors.append(f"Row {index + 1}: Student {student_id} not found")
                    error_count += 1
                    continue
                
                # Validate score
                if raw_score > max_score:
                    errors.append(f"Row {index + 1}: Raw score exceeds max score")
                    error_count += 1
                    continue
                
                # Check for duplicates
                existing_result = await db.execute(
                    select(InternalScore).where(
                        and_(
                            InternalScore.student_id == student_id,
                            InternalScore.course_id == course_id,
                            InternalScore.component_id == component_id
                        )
                    )
                )
                
                existing_score = existing_result.scalar_one_or_none()
                
                if existing_score:
                    # Update existing score
                    existing_score.raw_score = raw_score
                    existing_score.max_score = max_score
                else:
                    # Create new score
                    score = InternalScore(
                        student_id=student_id,
                        course_id=course_id,
                        component_id=component_id,
                        raw_score=raw_score,
                        max_score=max_score
                    )
                    db.add(score)
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
                error_count += 1
        
        if success_count > 0:
            await db.commit()
            
            await log_audit_event(
                db=db,
                actor_id=current_user.id,
                entity_type="internal_score",
                entity_id=None,
                action=AUDIT_ACTIONS["BULK_IMPORT"],
                after_json={
                    "course_id": course_id,
                    "component_id": component_id,
                    "filename": file.filename,
                    "success_count": success_count,
                    "error_count": error_count,
                    "total_rows": len(df)
                },
                reason="Internal scores file upload"
            )
        
        return BulkOperationResponse(
            success_count=success_count,
            error_count=error_count,
            total_count=len(df),
            errors=errors[:10]  # Limit to first 10 errors
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )

# ==================== STUDENT SUMMARIES ====================

@router.get("/summary/student/{student_id}", response_model=List[StudentInternalSummary])
async def get_student_internal_summary(
    student_id: int,
    course_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get internal marks summary for a student"""
    # Check permissions
    if current_user.role.value == "student" and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own summary"
        )
    
    # Verify student exists
    student_result = await db.execute(select(User).where(User.id == student_id))
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get student's courses
    courses_query = select(Course, ClassSection).join(
        ClassSection, Course.id == ClassSection.course_id
    ).join(
        Enrollment, ClassSection.id == Enrollment.class_id
    ).where(Enrollment.student_id == student_id)
    
    if course_id:
        courses_query = courses_query.where(Course.id == course_id)
    
    courses_result = await db.execute(courses_query)
    courses = courses_result.all()
    
    summaries = []
    
    for course, class_section in courses:
        # Get components for this course
        components_result = await db.execute(
            select(InternalComponent)
            .where(InternalComponent.course_id == course.id)
            .order_by(InternalComponent.name)
        )
        components = components_result.scalars().all()
        
        # Get scores for this student and course
        scores_result = await db.execute(
            select(InternalScore, InternalComponent.name, InternalComponent.weight_percent)
            .join(InternalComponent, InternalScore.component_id == InternalComponent.id)
            .where(
                and_(
                    InternalScore.student_id == student_id,
                    InternalScore.course_id == course.id
                )
            )
        )
        
        scores_data = scores_result.all()
        
        # Build component scores
        component_scores = []
        total_weighted_score = 0
        total_possible_score = 0
        
        for component in components:
            # Find score for this component
            score_data = next(
                (s for s, name, weight in scores_data if s.component_id == component.id),
                None
            )
            
            if score_data:
                percentage = (score_data.raw_score / score_data.max_score) * 100
                weighted_contribution = percentage * (component.weight_percent / 100)
                
                component_scores.append({
                    "component_name": component.name,
                    "raw_score": score_data.raw_score,
                    "max_score": score_data.max_score,
                    "percentage": round(percentage, 2),
                    "weight_percent": component.weight_percent,
                    "weighted_contribution": round(weighted_contribution, 2)
                })
                
                total_weighted_score += weighted_contribution
            else:
                component_scores.append({
                    "component_name": component.name,
                    "raw_score": None,
                    "max_score": None,
                    "percentage": None,
                    "weight_percent": component.weight_percent,
                    "weighted_contribution": 0
                })
            
            total_possible_score += component.weight_percent
        
        # Calculate overall percentage
        overall_percentage = (total_weighted_score / total_possible_score * 100) if total_possible_score > 0 else 0
        
        # Assign grade (simplified grading scale)
        def get_grade(percentage):
            if percentage >= 90: return "A+"
            elif percentage >= 80: return "A"
            elif percentage >= 70: return "B+"
            elif percentage >= 60: return "B"
            elif percentage >= 50: return "C+"
            elif percentage >= 40: return "C"
            else: return "F"
        
        summaries.append(StudentInternalSummary(
            student_id=student_id,
            student_name=student.name,
            course_id=course.id,
            course_name=course.title,
            component_scores=component_scores,
            total_weighted_score=round(total_weighted_score, 2),
            total_possible_score=round(total_possible_score, 2),
            percentage=round(overall_percentage, 2),
            grade=get_grade(overall_percentage)
        ))
    
    return summaries

@router.get("/summary/course/{course_id}")
async def get_course_internal_summary(
    course_id: int,
    component_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_class_analytics"))
):
    """Get internal marks summary for a course"""
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get enrolled students
    students_result = await db.execute(
        select(User.id, User.name)
        .join(Enrollment, User.id == Enrollment.student_id)
        .join(ClassSection, Enrollment.class_id == ClassSection.id)
        .where(ClassSection.course_id == course_id)
        .distinct()
        .order_by(User.name)
    )
    
    students = students_result.all()
    
    # Get components
    components_query = select(InternalComponent).where(InternalComponent.course_id == course_id)
    if component_id:
        components_query = components_query.where(InternalComponent.id == component_id)
    
    components_result = await db.execute(components_query.order_by(InternalComponent.name))
    components = components_result.scalars().all()
    
    # Build summary data
    summary_data = {
        "course_id": course_id,
        "course_name": course.title,
        "total_students": len(students),
        "components": [],
        "students": []
    }
    
    # Component statistics
    for component in components:
        scores_result = await db.execute(
            select(InternalScore.raw_score, InternalScore.max_score)
            .where(InternalScore.component_id == component.id)
        )
        
        scores = [(raw/max_score*100) for raw, max_score in scores_result.all() if max_score > 0]
        
        component_stats = {
            "component_id": component.id,
            "component_name": component.name,
            "weight_percent": component.weight_percent,
            "total_submissions": len(scores),
            "average_percentage": round(sum(scores) / len(scores), 2) if scores else 0,
            "highest_percentage": round(max(scores), 2) if scores else 0,
            "lowest_percentage": round(min(scores), 2) if scores else 0
        }
        
        summary_data["components"].append(component_stats)
    
    # Student data
    for student_id, student_name in students:
        student_scores = []
        total_weighted = 0
        total_possible = 0
        
        for component in components:
            score_result = await db.execute(
                select(InternalScore)
                .where(
                    and_(
                        InternalScore.student_id == student_id,
                        InternalScore.component_id == component.id
                    )
                )
            )
            
            score = score_result.scalar_one_or_none()
            
            if score:
                percentage = (score.raw_score / score.max_score) * 100
                weighted_contribution = percentage * (component.weight_percent / 100)
                
                student_scores.append({
                    "component_id": component.id,
                    "raw_score": score.raw_score,
                    "max_score": score.max_score,
                    "percentage": round(percentage, 2),
                    "weighted_contribution": round(weighted_contribution, 2)
                })
                
                total_weighted += weighted_contribution
            else:
                student_scores.append({
                    "component_id": component.id,
                    "raw_score": None,
                    "max_score": None,
                    "percentage": None,
                    "weighted_contribution": 0
                })
            
            total_possible += component.weight_percent
        
        overall_percentage = (total_weighted / total_possible * 100) if total_possible > 0 else 0
        
        summary_data["students"].append({
            "student_id": student_id,
            "student_name": student_name,
            "component_scores": student_scores,
            "total_weighted_score": round(total_weighted, 2),
            "overall_percentage": round(overall_percentage, 2)
        })
    
    return summary_data