from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, func
from typing import List, Optional
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_permission
from ..core.audit import log_audit_event, AUDIT_ACTIONS
from ..models.models import User, Program, PO, Course, CO, CO_PO_Map, ClassSection, Enrollment
from ..schemas.program import (
    ProgramCreate, ProgramUpdate, ProgramResponse,
    POCreate, POUpdate, POResponse,
    CourseCreate, CourseUpdate, CourseResponse,
    COCreate, COUpdate, COResponse,
    COPOMappingCreate, COPOMappingUpdate, COPOMappingResponse,
    COPOMatrixResponse, ClassSectionCreate, ClassSectionUpdate, ClassSectionResponse,
    EnrollmentCreate, EnrollmentResponse
)
from ..schemas.common import Response, BulkOperationResponse

router = APIRouter()

# ==================== PROGRAMS ====================

@router.get("/", response_model=List[ProgramResponse])
async def get_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all programs with optional filtering"""
    query = select(Program)
    
    if search:
        query = query.where(Program.name.ilike(f"%{search}%"))
    if year:
        query = query.where(Program.year == year)
    
    query = query.offset(skip).limit(limit).order_by(Program.name)
    result = await db.execute(query)
    programs = result.scalars().all()
    
    return [ProgramResponse.from_orm(program) for program in programs]

@router.post("/", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program(
    program_data: ProgramCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_programs"))
):
    """Create a new program"""
    # Check if program already exists
    existing = await db.execute(
        select(Program).where(
            and_(Program.name == program_data.name, Program.year == program_data.year)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Program with this name and year already exists"
        )
    
    program = Program(**program_data.dict())
    db.add(program)
    await db.commit()
    await db.refresh(program)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="program",
        entity_id=program.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json=program_data.dict(),
        reason="Created new program"
    )
    
    return ProgramResponse.from_orm(program)

@router.get("/{program_id}", response_model=ProgramResponse)
async def get_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get program by ID"""
    result = await db.execute(select(Program).where(Program.id == program_id))
    program = result.scalar_one_or_none()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    return ProgramResponse.from_orm(program)

@router.put("/{program_id}", response_model=ProgramResponse)
async def update_program(
    program_id: int,
    program_data: ProgramUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_programs"))
):
    """Update program"""
    result = await db.execute(select(Program).where(Program.id == program_id))
    program = result.scalar_one_or_none()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    before_data = {"name": program.name, "year": program.year}
    update_data = program_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(program, field, value)
    
    await db.commit()
    await db.refresh(program)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="program",
        entity_id=program.id,
        action=AUDIT_ACTIONS["UPDATE"],
        before_json=before_data,
        after_json=update_data,
        reason="Updated program"
    )
    
    return ProgramResponse.from_orm(program)

@router.delete("/{program_id}")
async def delete_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_programs"))
):
    """Delete program"""
    result = await db.execute(select(Program).where(Program.id == program_id))
    program = result.scalar_one_or_none()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Check if program has courses
    courses_result = await db.execute(select(Course).where(Course.program_id == program_id))
    if courses_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete program with associated courses"
        )
    
    before_data = {"name": program.name, "year": program.year}
    await db.delete(program)
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="program",
        entity_id=program_id,
        action=AUDIT_ACTIONS["DELETE"],
        before_json=before_data,
        reason="Deleted program"
    )
    
    return Response(message="Program deleted successfully")

# ==================== PROGRAM OUTCOMES (POs) ====================

@router.get("/{program_id}/pos", response_model=List[POResponse])
async def get_program_pos(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all POs for a program"""
    result = await db.execute(
        select(PO).where(PO.program_id == program_id).order_by(PO.code)
    )
    pos = result.scalars().all()
    return [POResponse.from_orm(po) for po in pos]

@router.post("/{program_id}/pos", response_model=POResponse, status_code=status.HTTP_201_CREATED)
async def create_po(
    program_id: int,
    po_data: POCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_pos"))
):
    """Create a new PO for a program"""
    # Verify program exists
    program_result = await db.execute(select(Program).where(Program.id == program_id))
    if not program_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Check if PO code already exists for this program
    existing = await db.execute(
        select(PO).where(
            and_(PO.program_id == program_id, PO.code == po_data.code)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PO with this code already exists for this program"
        )
    
    po_data.program_id = program_id
    po = PO(**po_data.dict())
    db.add(po)
    await db.commit()
    await db.refresh(po)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="po",
        entity_id=po.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json=po_data.dict(),
        reason="Created new PO"
    )
    
    return POResponse.from_orm(po)

@router.put("/pos/{po_id}", response_model=POResponse)
async def update_po(
    po_id: int,
    po_data: POUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_pos"))
):
    """Update PO"""
    result = await db.execute(select(PO).where(PO.id == po_id))
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    
    before_data = {"code": po.code, "title": po.title, "version": po.version}
    update_data = po_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(po, field, value)
    
    await db.commit()
    await db.refresh(po)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="po",
        entity_id=po.id,
        action=AUDIT_ACTIONS["UPDATE"],
        before_json=before_data,
        after_json=update_data,
        reason="Updated PO"
    )
    
    return POResponse.from_orm(po)

@router.delete("/pos/{po_id}")
async def delete_po(
    po_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_pos"))
):
    """Delete PO"""
    result = await db.execute(select(PO).where(PO.id == po_id))
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    
    # Check if PO has CO mappings
    mappings_result = await db.execute(select(CO_PO_Map).where(CO_PO_Map.po_id == po_id))
    if mappings_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete PO with existing CO mappings"
        )
    
    before_data = {"code": po.code, "title": po.title}
    await db.delete(po)
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="po",
        entity_id=po_id,
        action=AUDIT_ACTIONS["DELETE"],
        before_json=before_data,
        reason="Deleted PO"
    )
    
    return Response(message="PO deleted successfully")

# ==================== COURSES ====================

@router.get("/{program_id}/courses", response_model=List[CourseResponse])
async def get_program_courses(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all courses for a program"""
    result = await db.execute(
        select(Course).where(Course.program_id == program_id).order_by(Course.code)
    )
    courses = result.scalars().all()
    return [CourseResponse.from_orm(course) for course in courses]

@router.post("/{program_id}/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    program_id: int,
    course_data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_courses"))
):
    """Create a new course for a program"""
    # Verify program exists
    program_result = await db.execute(select(Program).where(Program.id == program_id))
    if not program_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Check if course code already exists for this program
    existing = await db.execute(
        select(Course).where(
            and_(Course.program_id == program_id, Course.code == course_data.code)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course with this code already exists for this program"
        )
    
    course_data.program_id = program_id
    course = Course(**course_data.dict())
    db.add(course)
    await db.commit()
    await db.refresh(course)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="course",
        entity_id=course.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json=course_data.dict(),
        reason="Created new course"
    )
    
    return CourseResponse.from_orm(course)

@router.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_courses"))
):
    """Update course"""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    before_data = {"code": course.code, "title": course.title, "credits": course.credits}
    update_data = course_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(course, field, value)
    
    await db.commit()
    await db.refresh(course)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="course",
        entity_id=course.id,
        action=AUDIT_ACTIONS["UPDATE"],
        before_json=before_data,
        after_json=update_data,
        reason="Updated course"
    )
    
    return CourseResponse.from_orm(course)

@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_courses"))
):
    """Delete course"""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if course has COs or class sections
    cos_result = await db.execute(select(CO).where(CO.course_id == course_id))
    classes_result = await db.execute(select(ClassSection).where(ClassSection.course_id == course_id))
    
    if cos_result.scalar_one_or_none() or classes_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete course with associated COs or class sections"
        )
    
    before_data = {"code": course.code, "title": course.title}
    await db.delete(course)
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="course",
        entity_id=course_id,
        action=AUDIT_ACTIONS["DELETE"],
        before_json=before_data,
        reason="Deleted course"
    )
    
    return Response(message="Course deleted successfully")

# ==================== COURSE OUTCOMES (COs) ====================

@router.get("/courses/{course_id}/cos", response_model=List[COResponse])
async def get_course_cos(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all COs for a course"""
    result = await db.execute(
        select(CO).where(CO.course_id == course_id).order_by(CO.code)
    )
    cos = result.scalars().all()
    return [COResponse.from_orm(co) for co in cos]

@router.post("/courses/{course_id}/cos", response_model=COResponse, status_code=status.HTTP_201_CREATED)
async def create_co(
    course_id: int,
    co_data: COCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("define_cos"))
):
    """Create a new CO for a course"""
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if CO code already exists for this course
    existing = await db.execute(
        select(CO).where(
            and_(CO.course_id == course_id, CO.code == co_data.code)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CO with this code already exists for this course"
        )
    
    co_data.course_id = course_id
    co = CO(**co_data.dict())
    db.add(co)
    await db.commit()
    await db.refresh(co)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="co",
        entity_id=co.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json=co_data.dict(),
        reason="Created new CO"
    )
    
    return COResponse.from_orm(co)

@router.put("/cos/{co_id}", response_model=COResponse)
async def update_co(
    co_id: int,
    co_data: COUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("define_cos"))
):
    """Update CO"""
    result = await db.execute(select(CO).where(CO.id == co_id))
    co = result.scalar_one_or_none()
    
    if not co:
        raise HTTPException(status_code=404, detail="CO not found")
    
    before_data = {"code": co.code, "title": co.title, "bloom": co.bloom, "version": co.version}
    update_data = co_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(co, field, value)
    
    await db.commit()
    await db.refresh(co)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="co",
        entity_id=co.id,
        action=AUDIT_ACTIONS["UPDATE"],
        before_json=before_data,
        after_json=update_data,
        reason="Updated CO"
    )
    
    return COResponse.from_orm(co)

@router.delete("/cos/{co_id}")
async def delete_co(
    co_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("define_cos"))
):
    """Delete CO"""
    result = await db.execute(select(CO).where(CO.id == co_id))
    co = result.scalar_one_or_none()
    
    if not co:
        raise HTTPException(status_code=404, detail="CO not found")
    
    # Check if CO has PO mappings or questions
    mappings_result = await db.execute(select(CO_PO_Map).where(CO_PO_Map.co_id == co_id))
    if mappings_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete CO with existing PO mappings or questions"
        )
    
    before_data = {"code": co.code, "title": co.title}
    await db.delete(co)
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="co",
        entity_id=co_id,
        action=AUDIT_ACTIONS["DELETE"],
        before_json=before_data,
        reason="Deleted CO"
    )
    
    return Response(message="CO deleted successfully")

# ==================== CO-PO MAPPINGS ====================

@router.get("/courses/{course_id}/co-po-matrix", response_model=COPOMatrixResponse)
async def get_co_po_matrix(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get CO-PO mapping matrix for a course"""
    # Get course with program
    course_result = await db.execute(
        select(Course).options(selectinload(Course.program)).where(Course.id == course_id)
    )
    course = course_result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get COs for the course
    cos_result = await db.execute(
        select(CO).where(CO.course_id == course_id).order_by(CO.code)
    )
    cos = cos_result.scalars().all()
    
    # Get POs for the program
    pos_result = await db.execute(
        select(PO).where(PO.program_id == course.program_id).order_by(PO.code)
    )
    pos = pos_result.scalars().all()
    
    # Get all CO-PO mappings
    mappings_result = await db.execute(
        select(CO_PO_Map).join(CO).where(CO.course_id == course_id)
    )
    mappings = mappings_result.scalars().all()
    
    # Create mapping dictionary for quick lookup
    mapping_dict = {(m.co_id, m.po_id): m.weight for m in mappings}
    
    # Build matrix
    matrix = []
    for co in cos:
        row = []
        for po in pos:
            weight = mapping_dict.get((co.id, po.id), 0.0)
            row.append(weight)
        matrix.append(row)
    
    return COPOMatrixResponse(
        course_id=course_id,
        course_name=course.title,
        cos=[COResponse.from_orm(co) for co in cos],
        pos=[POResponse.from_orm(po) for po in pos],
        mappings=[COPOMappingResponse.from_orm(m) for m in mappings],
        matrix=matrix
    )

@router.post("/co-po-mappings", response_model=COPOMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_co_po_mapping(
    mapping_data: COPOMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("map_co_po"))
):
    """Create CO-PO mapping"""
    # Verify CO and PO exist
    co_result = await db.execute(select(CO).where(CO.id == mapping_data.co_id))
    po_result = await db.execute(select(PO).where(PO.id == mapping_data.po_id))
    
    if not co_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="CO not found")
    if not po_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="PO not found")
    
    # Check if mapping already exists
    existing = await db.execute(
        select(CO_PO_Map).where(
            and_(CO_PO_Map.co_id == mapping_data.co_id, CO_PO_Map.po_id == mapping_data.po_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CO-PO mapping already exists"
        )
    
    mapping = CO_PO_Map(**mapping_data.dict())
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="co_po_mapping",
        entity_id=mapping.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json=mapping_data.dict(),
        reason="Created CO-PO mapping"
    )
    
    return COPOMappingResponse.from_orm(mapping)

@router.put("/co-po-mappings/{mapping_id}", response_model=COPOMappingResponse)
async def update_co_po_mapping(
    mapping_id: int,
    mapping_data: COPOMappingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("map_co_po"))
):
    """Update CO-PO mapping"""
    result = await db.execute(select(CO_PO_Map).where(CO_PO_Map.id == mapping_id))
    mapping = result.scalar_one_or_none()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="CO-PO mapping not found")
    
    before_data = {"weight": mapping.weight}
    update_data = mapping_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(mapping, field, value)
    
    await db.commit()
    await db.refresh(mapping)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="co_po_mapping",
        entity_id=mapping.id,
        action=AUDIT_ACTIONS["UPDATE"],
        before_json=before_data,
        after_json=update_data,
        reason="Updated CO-PO mapping"
    )
    
    return COPOMappingResponse.from_orm(mapping)

@router.delete("/co-po-mappings/{mapping_id}")
async def delete_co_po_mapping(
    mapping_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("map_co_po"))
):
    """Delete CO-PO mapping"""
    result = await db.execute(select(CO_PO_Map).where(CO_PO_Map.id == mapping_id))
    mapping = result.scalar_one_or_none()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="CO-PO mapping not found")
    
    before_data = {"co_id": mapping.co_id, "po_id": mapping.po_id, "weight": mapping.weight}
    await db.delete(mapping)
    await db.commit()
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="co_po_mapping",
        entity_id=mapping_id,
        action=AUDIT_ACTIONS["DELETE"],
        before_json=before_data,
        reason="Deleted CO-PO mapping"
    )
    
    return Response(message="CO-PO mapping deleted successfully")

# ==================== CLASS SECTIONS ====================

@router.get("/courses/{course_id}/classes", response_model=List[ClassSectionResponse])
async def get_course_classes(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all class sections for a course"""
    result = await db.execute(
        select(ClassSection).where(ClassSection.course_id == course_id).order_by(ClassSection.name)
    )
    classes = result.scalars().all()
    return [ClassSectionResponse.from_orm(cls) for cls in classes]

@router.post("/courses/{course_id}/classes", response_model=ClassSectionResponse, status_code=status.HTTP_201_CREATED)
async def create_class_section(
    course_id: int,
    class_data: ClassSectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_courses"))
):
    """Create a new class section for a course"""
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Verify coordinator exists if provided
    if class_data.coordinator_id:
        coordinator_result = await db.execute(select(User).where(User.id == class_data.coordinator_id))
        if not coordinator_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Coordinator not found")
    
    class_data.course_id = course_id
    class_section = ClassSection(**class_data.dict())
    db.add(class_section)
    await db.commit()
    await db.refresh(class_section)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="class_section",
        entity_id=class_section.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json=class_data.dict(),
        reason="Created new class section"
    )
    
    return ClassSectionResponse.from_orm(class_section)

# ==================== ENROLLMENTS ====================

@router.get("/classes/{class_id}/enrollments", response_model=List[EnrollmentResponse])
async def get_class_enrollments(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all enrollments for a class"""
    result = await db.execute(
        select(Enrollment, User.name, User.email)
        .join(User, Enrollment.student_id == User.id)
        .where(Enrollment.class_id == class_id)
        .order_by(User.name)
    )
    enrollments = result.all()
    
    return [
        EnrollmentResponse(
            id=enrollment.id,
            class_id=enrollment.class_id,
            student_id=enrollment.student_id,
            enrolled_at=enrollment.enrolled_at,
            student_name=name,
            student_email=email
        )
        for enrollment, name, email in enrollments
    ]

@router.post("/classes/{class_id}/enrollments", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    class_id: int,
    enrollment_data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_courses"))
):
    """Enroll a student in a class"""
    # Verify class and student exist
    class_result = await db.execute(select(ClassSection).where(ClassSection.id == class_id))
    student_result = await db.execute(select(User).where(User.id == enrollment_data.student_id))
    
    if not class_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Class not found")
    if not student_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if already enrolled
    existing = await db.execute(
        select(Enrollment).where(
            and_(Enrollment.class_id == class_id, Enrollment.student_id == enrollment_data.student_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already enrolled in this class"
        )
    
    enrollment_data.class_id = class_id
    enrollment = Enrollment(**enrollment_data.dict())
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    
    await log_audit_event(
        db=db,
        actor_id=current_user.id,
        entity_type="enrollment",
        entity_id=enrollment.id,
        action=AUDIT_ACTIONS["CREATE"],
        after_json=enrollment_data.dict(),
        reason="Enrolled student in class"
    )
    
    return EnrollmentResponse.from_orm(enrollment)