from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .database import AsyncSessionLocal, create_tables
from .security import get_password_hash
from ..models.models import User, Role, Program, PO, Course, CO, CO_PO_Map, InternalComponent
import asyncio
import logging

logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database with tables and seed data"""
    
    # Create all tables
    await create_tables()
    logger.info("Database tables created")
    
    # Seed initial data
    async with AsyncSessionLocal() as db:
        await seed_initial_data(db)
    
    logger.info("Database initialization completed")

async def seed_initial_data(db: AsyncSession):
    """Seed database with initial data"""
    
    # Check if admin user already exists
    admin_result = await db.execute(
        select(User).where(User.role == Role.ADMIN)
    )
    admin_user = admin_result.scalar_one_or_none()
    
    if not admin_user:
        # Create default admin user
        admin_user = User(
            username="admin",
            email="admin@dsba.edu",
            name="System Administrator",
            role=Role.ADMIN,
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            first_login=False,
            department="Administration"
        )
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        logger.info("Default admin user created: admin/admin123")
    
    # Create sample program if none exists
    program_result = await db.execute(select(Program))
    existing_program = program_result.scalar_one_or_none()
    
    if not existing_program:
        # Create sample program
        program = Program(
            name="Computer Science and Engineering",
            year=2024
        )
        db.add(program)
        await db.commit()
        await db.refresh(program)
        
        # Create sample POs
        pos_data = [
            {"code": "PO1", "title": "Engineering knowledge"},
            {"code": "PO2", "title": "Problem analysis"},
            {"code": "PO3", "title": "Design/development of solutions"},
            {"code": "PO4", "title": "Conduct investigations of complex problems"},
            {"code": "PO5", "title": "Modern tool usage"},
        ]
        
        created_pos = []
        for po_data in pos_data:
            po = PO(
                program_id=program.id,
                code=po_data["code"],
                title=po_data["title"],
                version=1
            )
            db.add(po)
            created_pos.append(po)
        
        await db.commit()
        
        # Create sample course
        course = Course(
            program_id=program.id,
            code="CS101",
            title="Introduction to Programming",
            credits=4.0
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)
        
        # Create sample COs
        cos_data = [
            {"code": "CO1", "title": "Understand basic programming concepts", "bloom": "Understanding"},
            {"code": "CO2", "title": "Apply programming constructs", "bloom": "Applying"},
            {"code": "CO3", "title": "Analyze program logic", "bloom": "Analyzing"},
        ]
        
        created_cos = []
        for co_data in cos_data:
            co = CO(
                course_id=course.id,
                code=co_data["code"],
                title=co_data["title"],
                bloom=co_data["bloom"],
                version=1
            )
            db.add(co)
            created_cos.append(co)
        
        await db.commit()
        
        # Create sample CO-PO mappings
        mappings = [
            (created_cos[0], created_pos[0], 0.8),  # CO1 -> PO1
            (created_cos[0], created_pos[1], 0.2),  # CO1 -> PO2
            (created_cos[1], created_pos[1], 0.6),  # CO2 -> PO2
            (created_cos[1], created_pos[2], 0.4),  # CO2 -> PO3
            (created_cos[2], created_pos[1], 0.3),  # CO3 -> PO2
            (created_cos[2], created_pos[3], 0.7),  # CO3 -> PO4
        ]
        
        for co, po, weight in mappings:
            mapping = CO_PO_Map(
                co_id=co.id,
                po_id=po.id,
                weight=weight
            )
            db.add(mapping)
        
        # Create sample internal components
        components_data = [
            {"name": "Class Tests", "weight_percent": 40.0},
            {"name": "Assignments", "weight_percent": 20.0},
            {"name": "Lab Work", "weight_percent": 30.0},
            {"name": "Attendance", "weight_percent": 10.0},
        ]
        
        for comp_data in components_data:
            component = InternalComponent(
                course_id=course.id,
                name=comp_data["name"],
                weight_percent=comp_data["weight_percent"]
            )
            db.add(component)
        
        await db.commit()
        logger.info("Sample program, course, COs, POs, and mappings created")
    
    # Create sample teacher if none exists
    teacher_result = await db.execute(
        select(User).where(User.role == Role.TEACHER)
    )
    teacher_user = teacher_result.scalar_one_or_none()
    
    if not teacher_user:
        teacher_user = User(
            username="teacher1",
            email="teacher1@dsba.edu",
            name="Dr. John Smith",
            role=Role.TEACHER,
            hashed_password=get_password_hash("teacher123"),
            is_active=True,
            first_login=False,
            department="Computer Science"
        )
        db.add(teacher_user)
        await db.commit()
        logger.info("Sample teacher created: teacher1/teacher123")
    
    # Create sample student if none exists
    student_result = await db.execute(
        select(User).where(User.role == Role.STUDENT)
    )
    student_user = student_result.scalar_one_or_none()
    
    if not student_user:
        student_user = User(
            username="student1",
            email="student1@dsba.edu",
            name="Alice Johnson",
            role=Role.STUDENT,
            hashed_password=get_password_hash("student123"),
            is_active=True,
            first_login=False,
            department="Computer Science"
        )
        db.add(student_user)
        await db.commit()
        logger.info("Sample student created: student1/student123")

if __name__ == "__main__":
    asyncio.run(init_database())