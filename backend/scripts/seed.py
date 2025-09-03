#!/usr/bin/env python3
"""
Database seeding script for DSBA LMS
Populates the database with sample data for testing
"""

import sys
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import text

# Import directly from the app modules
from app.models.models import Base, User, Program, Course, CO, PO, CO_PO_Map, Question, QuestionOption, Exam, ClassSection, Enrollment
from app.core.config import settings
from app.core.security import get_password_hash
from app.core.database import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample data
SAMPLE_USERS = [
    {
        "username": "admin",
        "email": "admin@college.edu",
        "name": "System Administrator",
        "role": "admin",
        "password": "Admin123!",  # In production, use secure password
    },
    {
        "username": "john_teacher",
        "email": "john.doe@college.edu",
        "name": "John Doe",
        "role": "teacher",
        "password": "Teacher123!",
        "phone": "+1234567890",
    },
    {
        "username": "sarah_teacher",
        "email": "sarah.wilson@college.edu",
        "name": "Sarah Wilson",
        "role": "teacher",
        "password": "Teacher123!",
        "phone": "+1234567891",
    },
    {
        "username": "alice_student",
        "email": "alice.smith@college.edu",
        "name": "Alice Smith",
        "role": "student",
        "password": "Student123!",
    },
    {
        "username": "bob_student",
        "email": "bob.johnson@college.edu",
        "name": "Bob Johnson",
        "role": "student",
        "password": "Student123!",
    },
    {
        "username": "charlie_student",
        "email": "charlie.brown@college.edu",
        "name": "Charlie Brown",
        "role": "student",
        "password": "Student123!",
    },
]

SAMPLE_PROGRAMS = [
    {
        "name": "Bachelor of Computer Science",
        "year": 2024,
    },
    {
        "name": "Master of Computer Applications",
        "year": 2024,
    },
]

SAMPLE_COURSES = [
    {
        "code": "CS101",
        "title": "Introduction to Computer Science",
        "credits": 4.0,
        "program_id": 1,
    },
    {
        "code": "CS201",
        "title": "Data Structures and Algorithms",
        "credits": 4.0,
        "program_id": 1,
    },
    {
        "code": "DB301",
        "title": "Database Management Systems",
        "credits": 3.0,
        "program_id": 1,
    },
    {
        "code": "AI401",
        "title": "Artificial Intelligence",
        "credits": 4.0,
        "program_id": 1,
    },
]

SAMPLE_POS = [
    {
        "code": "PO-1",
        "title": "Engineering knowledge: Apply the knowledge of mathematics, science, engineering fundamentals, and an engineering specialization to the solution of complex engineering problems",
        "program_id": 1,
    },
    {
        "code": "PO-2",
        "title": "Problem analysis: Identify, formulate, review research literature, and analyze complex engineering problems reaching substantiated conclusions",
        "program_id": 1,
    },
    {
        "code": "PO-3",
        "title": "Design/development of solutions: Design solutions for complex engineering problems and design system components or processes that meet the specified needs",
        "program_id": 1,
    },
]

SAMPLE_COS = [
    {
        "course_id": 1,
        "code": "CO-1.1",
        "title": "Understand basic programming concepts",
        "bloom": "Knowledge",
    },
    {
        "course_id": 1,
        "code": "CO-1.2",
        "title": "Implement basic algorithms",
        "bloom": "Application",
    },
    {
        "course_id": 2,
        "code": "CO-2.1",
        "title": "Analyze algorithm complexity",
        "bloom": "Analysis",
    },
    {
        "course_id": 2,
        "code": "CO-2.2",
        "title": "Implement advanced data structures",
        "bloom": "Application",
    },
]

SAMPLE_QUESTIONS = [
    {
        "type": "mcq",
        "text": "What is the time complexity of binary search algorithm?",
        "co_id": 3,
        "max_marks": 1.0,
        "creator_id": 2,
    },
    {
        "type": "mcq",
        "text": "Which data structure follows LIFO principle?",
        "co_id": 4,
        "max_marks": 1.0,
        "creator_id": 2,
    },
    {
        "type": "descriptive",
        "text": "Explain the concept of inheritance in object-oriented programming with examples.",
        "co_id": 2,
        "max_marks": 5.0,
        "model_answer": "Inheritance is a fundamental concept in OOP that allows a class to inherit properties and methods from another class. The class that inherits is called the subclass or derived class, while the class being inherited from is called the superclass or base class.",
        "rubric_json": {
            "criteria": ["Understanding", "Example Quality", "Explanation Clarity", "Code Example"]
        },
        "creator_id": 2,
    },
]

SAMPLE_QUESTION_OPTIONS = [
    # Options for question 1
    {"question_id": 1, "text": "O(1)", "is_correct": False},
    {"question_id": 1, "text": "O(log n)", "is_correct": True},
    {"question_id": 1, "text": "O(n)", "is_correct": False},
    {"question_id": 1, "text": "O(n²)", "is_correct": False},

    # Options for question 2
    {"question_id": 2, "text": "Queue", "is_correct": False},
    {"question_id": 2, "text": "Stack", "is_correct": True},
    {"question_id": 2, "text": "Array", "is_correct": False},
    {"question_id": 2, "text": "Linked List", "is_correct": False},
]

class DatabaseSeeder:
    def __init__(self):
        self.engine = engine
        self.async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def create_tables(self):
        """Create all database tables"""
        logger.info("Creating database tables...")
        async with self.engine.begin() as conn:
            # Drop all tables first (for clean reseeding)
            await conn.execute(text("DROP TABLE IF EXISTS audit_logs CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS internal_scores CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS internal_components CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS grade_upload_batches CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS responses CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS proctor_logs CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS attempts CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS exam_questions CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS exams CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS class_sections CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS enrollments CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS question_options CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS questions CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS cos CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS co_po_maps CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS pos CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS courses CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS programs CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS lock_windows CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            await conn.commit()

            # Create tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    async def seed_users(self, session: AsyncSession):
        """Seed user data"""
        logger.info("Seeding users...")

        # Update sample users with hashed passwords
        for user_data in SAMPLE_USERS:
            user_data["hashed_password"] = get_password_hash(user_data.pop("password"))

            # Map string roles to enum
            role_mapping = {
                "admin": "admin",
                "teacher": "teacher",
                "student": "student"
            }
            user_data["role"] = role_mapping.get(user_data["role"], "student")

            user = User(**user_data, is_active=True)
            session.add(user)

        await session.commit()
        logger.info(f"Seeded {len(SAMPLE_USERS)} users")

    async def seed_programs_and_courses(self, session: AsyncSession):
        """Seed programs, courses, COs, and POs"""
        logger.info("Seeding programs and courses...")

        # Create programs
        programs = []
        for program_data in SAMPLE_PROGRAMS:
            program = Program(**program_data)
            session.add(program)
            programs.append(program)

        await session.commit()

        # Create courses
        courses = []
        for course_data in SAMPLE_COURSES:
            course = Course(**course_data)
            session.add(course)
            courses.append(course)

        await session.commit()

        # Create POs
        pos = []
        for po_data in SAMPLE_POS:
            po = PO(**po_data, version=1)
            session.add(po)
            pos.append(po)

        await session.commit()

        # Create COs
        cos = []
        for co_data in SAMPLE_COS:
            co = CO(**co_data, version=1)
            session.add(co)
            cos.append(co)

        await session.commit()

        # Create CO-PO mappings
        for i, co in enumerate(cos):
            co_po_map = CO_PO_Map(
                co_id=co.id,
                po_id=pos[i % len(pos)].id,
                weight=0.8
            )
            session.add(co_po_map)

        await session.commit()

        logger.info(f"Seeded {len(programs)} programs, {len(courses)} courses, {len(pos)} POs, {len(cos)} COs")

    async def seed_questions(self, session: AsyncSession):
        """Seed question bank"""
        logger.info("Seeding question bank...")

        # Create questions
        questions = []
        for question_data in SAMPLE_QUESTIONS:
            question = Question(**question_data)
            session.add(question)
            questions.append(question)

        await session.commit()

        # Create question options for MCQs
        for option_data in SAMPLE_QUESTION_OPTIONS:
            option = QuestionOption(**option_data)
            session.add(option)

        await session.commit()

        logger.info(f"Seeded {len(questions)} questions with options")

    async def seed_class_sections(self, session: AsyncSession):
        """Seed a sample class section"""
        logger.info("Seeding class sections...")

        # Get course and teacher
        course_result = await session.execute(select(Course).where(Course.code == "CS101"))
        course = course_result.scalar_one_or_none()

        teacher_result = await session.execute(select(User).where(User.role == "teacher"))
        teacher = teacher_result.first()

        if course and teacher:
            class_section = ClassSection(
                course_id=course.id,
                name="A",
                term="Spring",
                year=2024
            )
            session.add(class_section)
            await session.commit()
            logger.info("Created class section CS101-A")
        else:
            logger.warning("Could not create class section - missing course or teacher")

    async def run(self):
        """Run the complete seeding process"""
        logger.info("Starting database seeding...")

        async with self.async_session() as session:
            try:
                # Create tables
                await self.create_tables()

                # Seed data
                await self.seed_users(session)
                await self.seed_programs_and_courses(session)
                await self.seed_questions(session)
                await self.seed_class_sections(session)

                logger.info("Database seeding completed successfully!")

                # Print login credentials
                print("\n" + "="*50)
                print("🎉 DATABASE SEEDED SUCCESSFULLY!")
                print("="*50)
                print("Test login credentials:")
                for user in SAMPLE_USERS:
                    print(f"  {user['username']}: {user['password']} ({user['role']})")
                print()
                print("API endpoints:")
                print(f"  Backend: http://localhost:8000")
                print(f"  Frontend: http://localhost:3000")
                print(f"  Docs: http://localhost:8000/docs")
                print("="*50)

            except Exception as e:
                logger.error(f"Error during seeding: {e}")
                await session.rollback()
                raise

async def main():
    """Main entry point"""
    seeder = DatabaseSeeder()
    await seeder.run()

if __name__ == "__main__":
    asyncio.run(main())
