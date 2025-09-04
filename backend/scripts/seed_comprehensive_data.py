#!/usr/bin/env python3
"""
Comprehensive data seeder for DSBA LMS
Seeds initial data including users, programs, courses, COs, POs, and mappings
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db
from app.core.security import hash_password
from app.models.models import (
    User, Program, PO, Course, CO, CO_PO_Map, ClassSection,
    Enrollment, Question, QuestionOption
)
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession


async def seed_data():
    """Seed comprehensive initial data"""

    async for db in get_db():
        try:
            print("🌱 Starting comprehensive data seeding...")

            # 1. Create initial admin user
            admin_user = await create_admin_user(db)
            print(f"✅ Created admin user: {admin_user.name}")

            # 2. Create sample teacher
            teacher_user = await create_teacher_user(db, admin_user.id)
            print(f"✅ Created teacher user: {teacher_user.name}")

            # 3. Create sample students
            students = await create_student_users(db, admin_user.id)
            print(f"✅ Created {len(students)} student users")

            # 4. Create sample program
            program = await create_program(db, admin_user.id)
            print(f"✅ Created program: {program.name}")

            # 5. Create POs for the program
            pos = await create_program_outcomes(db, program.id)
            print(f"✅ Created {len(pos)} Program Outcomes")

            # 6. Create courses for the program
            courses = await create_courses(db, program.id, pos)
            print(f"✅ Created {len(courses)} courses")

            # 7. Create class sections
            sections = await create_class_sections(db, courses)
            print(f"✅ Created {len(sections)} class sections")

            # 8. Enroll students
            enrollments = await enroll_students(db, sections, students)
            print(f"✅ Created {len(enrollments)} enrollments")

            # 9. Create sample questions
            questions = await create_sample_questions(db, teacher_user.id)
            print(f"✅ Created {len(questions)} sample questions")

            print("\n🎉 Data seeding completed successfully!")
            print("\n📋 Summary:")
            print(f"   • 1 Admin user (admin@dsba.edu)")
            print(f"   • 1 Teacher user (teacher@dsba.edu)")
            print(f"   • {len(students)} Student users (student1@dsba.edu - student5@dsba.edu)")
            print(f"   • 1 Program ({program.name})")
            print(f"   • {len(pos)} Program Outcomes")
            print(f"   • {len(courses)} Courses")
            print(f"   • {len(sections)} Class Sections")
            print(f"   • {len(enrollments)} Enrollments")
            print(f"   • {len(questions)} Sample Questions")

            print("\n🔐 Login Credentials:")
            print("   Admin: admin@dsba.edu / admin123")
            print("   Teacher: teacher@dsba.edu / teacher123")
            print("   Students: student1@dsba.edu / student123")
            print("             (student2@dsba.edu / student123)")
            print("             (etc.)")

        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            await db.close()


async def create_admin_user(db: AsyncSession):
    """Create initial admin user"""
    admin_data = {
        "username": "admin",
        "email": "admin@dsba.edu",
        "name": "DSBA Administrator",
        "phone": "+91-9876543210",
        "role": "ADMIN",
        "department": "Academic Administration",
        "hashed_password": hash_password("admin123"),
        "is_active": True,
        "first_login": False,
        "mfa_enabled": False
    }

    admin_user = User(**admin_data)
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)
    return admin_user


async def create_teacher_user(db: AsyncSession, admin_id: int):
    """Create sample teacher user"""
    teacher_data = {
        "username": "teacher",
        "email": "teacher@dsba.edu",
        "name": "Dr. Sarah Johnson",
        "phone": "+91-9876543211",
        "role": "TEACHER",
        "department": "Computer Science",
        "hashed_password": hash_password("teacher123"),
        "is_active": True,
        "first_login": False,
        "mfa_enabled": False,
        "created_by": admin_id
    }

    teacher_user = User(**teacher_data)
    db.add(teacher_user)
    await db.commit()
    await db.refresh(teacher_user)
    return teacher_user


async def create_student_users(db: AsyncSession, admin_id: int):
    """Create sample student users"""
    students_data = [
        {
            "username": "student1",
            "email": "student1@dsba.edu",
            "name": "Alice Thompson",
            "role": "STUDENT",
            "department": "Computer Science",
            "hashed_password": hash_password("student123"),
            "is_active": True,
            "first_login": True,
            "mfa_enabled": False,
            "created_by": admin_id
        },
        {
            "username": "student2",
            "email": "student2@dsba.edu",
            "name": "Bob Williams",
            "role": "STUDENT",
            "department": "Information Technology",
            "hashed_password": hash_password("student123"),
            "is_active": True,
            "first_login": True,
            "mfa_enabled": False,
            "created_by": admin_id
        },
        {
            "username": "student3",
            "email": "student3@dsba.edu",
            "name": "Charlie Brown",
            "role": "STUDENT",
            "department": "Computer Science",
            "hashed_password": hash_password("student123"),
            "is_active": True,
            "first_login": True,
            "mfa_enabled": False,
            "created_by": admin_id
        },
        {
            "username": "student4",
            "email": "student4@dsba.edu",
            "name": "Diana Smith",
            "role": "STUDENT",
            "department": "Information Technology",
            "hashed_password": hash_password("student123"),
            "is_active": True,
            "first_login": True,
            "mfa_enabled": False,
            "created_by": admin_id
        },
        {
            "username": "student5",
            "email": "student5@dsba.edu",
            "name": "Eve Johnson",
            "role": "STUDENT",
            "department": "Computer Science",
            "hashed_password": hash_password("student123"),
            "is_active": True,
            "first_login": True,
            "mfa_enabled": False,
            "created_by": admin_id
        }
    ]

    students = []
    for student_data in students_data:
        student = User(**student_data)
        db.add(student)
        students.append(student)

    await db.commit()

    # Refresh all students
    for student in students:
        await db.refresh(student)

    return students


async def create_program(db: AsyncSession, admin_id: int):
    """Create sample academic program"""
    program_data = {
        "name": "Bachelor of Technology in Computer Science",
        "year": 2024
    }

    program = Program(**program_data)
    db.add(program)
    await db.commit()
    await db.refresh(program)
    return program


async def create_program_outcomes(db: AsyncSession, program_id: int):
    """Create Program Outcomes for the academic program"""
    po_data = [
        {
            "program_id": program_id,
            "code": "PO1",
            "title": "Engineering knowledge: Apply knowledge of mathematics, science, engineering fundamentals and an engineering specialization to the solution of complex engineering problems.",
            "version": 1
        },
        {
            "program_id": program_id,
            "code": "PO2",
            "title": "Problem analysis: Identify, formulate, research literature and solve complex engineering problems reaching substantiated conclusions using first principles of mathematics, natural sciences and engineering sciences.",
            "version": 1
        },
        {
            "program_id": program_id,
            "code": "PO3",
            "title": "Design/development of solutions: Design solutions for complex engineering problems and design systems, components or processes that meet specified needs with appropriate consideration for public health and safety, cultural, societal and environmental considerations.",
            "version": 1
        },
        {
            "program_id": program_id,
            "code": "PO4",
            "title": "Conduct investigations of complex problems: Use research-based knowledge and methodology to investigate complex engineering problems.",
            "version": 1
        },
        {
            "program_id": program_id,
            "code": "PO5",
            "title": "Modern tool usage: Create, select and apply appropriate techniques, resources and modern engineering and IT tools including prediction and modeling to complex engineering activities with an understanding of the limitations.",
            "version": 1
        },
        {
            "program_id": program_id,
            "code": "PO6",
            "title": "The engineer and society: Apply reasoning informed by contextual knowledge to assess societal, health, safety, legal and cultural issues and the consequent responsibilities relevant to professional engineering practice.",
            "version": 1
        }
    ]

    pos = []
    for po in po_data:
        po_obj = PO(**po)
        db.add(po_obj)
        pos.append(po_obj)

    await db.commit()

    # Refresh all POs
    for po in pos:
        await db.refresh(po)

    return pos


async def create_courses(db: AsyncSession, program_id: int, pos: list[PO]):
    """Create courses for the academic program"""
    courses_data = [
        {
            "program_id": program_id,
            "code": "CS101",
            "title": "Data Structures and Algorithms",
            "credits": 4.0
        },
        {
            "program_id": program_id,
            "code": "CS201",
            "title": "Database Management Systems",
            "credits": 3.0
        },
        {
            "program_id": program_id,
            "code": "CS301",
            "title": "Artificial Intelligence and Machine Learning",
            "credits": 4.0
        }
    ]

    courses = []
    for course_data in courses_data:
        course = Course(**course_data)
        db.add(course)
        courses.append(course)

    await db.commit()

    # Refresh all courses
    for course in courses:
        await db.refresh(course)

    return courses


def get_course_cos_with_po_mapping(course_code: str):
    """Get predefined COs and their PO mappings for a course"""
    mapping = {
        "CS101": {  # Data Structures and Algorithms
            "cos": [
                {
                    "code": "CO1",
                    "title": "Understand and apply basic data structures",
                    "bloom": "Understand",
                    "po_weights": {1: 0.4, 2: 0.3, 3: 0.3}
                },
                {
                    "code": "CO2",
                    "title": "Analyze and design algorithms for solving computational problems",
                    "bloom": "Analyze",
                    "po_weights": {2: 0.5, 3: 0.3, 5: 0.2}
                },
                {
                    "code": "CO3",
                    "title": "Implement and evaluate algorithms for real-world applications",
                    "bloom": "Apply",
                    "po_weights": {3: 0.4, 5: 0.4, 6: 0.2}
                }
            ]
        },
        "CS201": {  # Database Management Systems
            "cos": [
                {
                    "code": "CO1",
                    "title": "Design and implement database schemas",
                    "bloom": "Create",
                    "po_weights": {1: 0.2, 3: 0.5, 5: 0.3}
                },
                {
                    "code": "CO2",
                    "title": "Write efficient SQL queries and procedures",
                    "bloom": "Apply",
                    "po_weights": {2: 0.4, 3: 0.4, 5: 0.2}
                },
                {
                    "code": "CO3",
                    "title": "Understand database security and transaction management",
                    "bloom": "Understand",
                    "po_weights": {1: 0.3, 6: 0.4, 4: 0.3}
                }
            ]
        },
        "CS301": {  # AI and ML
            "cos": [
                {
                    "code": "CO1",
                    "title": "Apply machine learning algorithms for classification and regression",
                    "bloom": "Apply",
                    "po_weights": {2: 0.3, 3: 0.4, 5: 0.3}
                },
                {
                    "code": "CO2",
                    "title": "Design neural networks and deep learning architectures",
                    "bloom": "Create",
                    "po_weights": {3: 0.5, 4: 0.3, 5: 0.2}
                },
                {
                    "code": "CO3",
                    "title": "Evaluate AI model performance and ethical considerations",
                    "bloom": "Evaluate",
                    "po_weights": {3: 0.2, 6: 0.5, 4: 0.3}
                }
            ]
        }
    }

    return mapping.get(course_code, {"cos": []})


async def create_class_sections(db: AsyncSession, courses: list[Course]):
    """Create class sections for courses"""
    sections = []

    for i, course in enumerate(courses):
        section_data = {
            "course_id": course.id,
            "name": f"Section A{i+1}",
            "term": "Fall",
            "year": 2024
        }

        section = ClassSection(**section_data)
        db.add(section)
        sections.append(section)

    await db.commit()

    # Refresh all sections
    for section in sections:
        await db.refresh(section)

    return sections


async def enroll_students(db: AsyncSession, sections: list[ClassSection], students: list[User]):
    """Enroll students in class sections"""
    enrollments = []

    for i, student in enumerate(students):
        # Assign students to sections in a round-robin fashion
        section_index = i % len(sections)
        section = sections[section_index]

        enrollment_data = {
            "class_id": section.id,
            "student_id": student.id
        }

        enrollment = Enrollment(**enrollment_data)
        db.add(enrollment)
        enrollments.append(enrollment)

    await db.commit()

    # Refresh all enrollments
    for enrollment in enrollments:
        await db.refresh(enrollment)

    return enrollments


async def create_sample_questions(db: AsyncSession, teacher_id: int):
    """Create sample questions across different types"""

    sample_questions = [
        # MCQ Question
        {
            "type": "MCQ",
            "text": "What is the time complexity of binary search algorithm?",
            "max_marks": 5.0,
            "created_by": teacher_id,
            "options": [
                {"text": "O(log n)", "is_correct": True},
                {"text": "O(n)", "is_correct": False},
                {"text": "O(n^2)", "is_correct": False},
                {"text": "O(1)", "is_correct": False}
            ]
        },
        # Multiple Choice Question
        {
            "type": "MSQ",
            "text": "Which of the following are valid data types in Python? (Select all that apply)",
            "max_marks": 5.0,
            "created_by": teacher_id,
            "options": [
                {"text": "int", "is_correct": True},
                {"text": "str", "is_correct": True},
                {"text": "float", "is_correct": True},
                {"text": "integer", "is_correct": False},
                {"text": "list", "is_correct": True}
            ]
        },
        # True/False Question
        {
            "type": "TF",
            "text": "A binary search tree maintains sorted order of elements.",
            "max_marks": 3.0,
            "created_by": teacher_id,
            "options": [
                {"text": "True", "is_correct": True},
                {"text": "False", "is_correct": False}
            ]
        },
        # Descriptive Question
        {
            "type": "DESCRIPTIVE",
            "text": "Explain the concept of normalization in database design. Provide examples of 1NF, 2NF, and 3NF.",
            "max_marks": 15.0,
            "created_by": teacher_id,
            "model_answer": "Normalization is a process of organizing data in a database...",
            "rubric_json": {
                "criteria": [
                    {
                        "name": "Understanding",
                        "max_points": 5,
                        "description": "Demonstrates understanding of normalization concepts"
                    },
                    {
                        "name": "Examples",
                        "max_points": 7,
                        "description": "Provides accurate examples of normal forms"
                    },
                    {
                        "name": "Explanation",
                        "max_points": 3,
                        "description": "Clear and coherent explanation"
                    }
                ]
            }
        }
    ]

    created_questions = []

    for question_data in sample_questions:
        # Create question
        question_options = question_data.pop('options', [])

        question = Question(**question_data)
        db.add(question)
        await db.flush()  # Get the question ID

        # Create options if any
        for option_data in question_options:
            option = QuestionOption(
                question_id=question.id,
                text=option_data['text'],
                is_correct=option_data.get('is_correct', False)
            )
            db.add(option)

        created_questions.append(question)

    await db.commit()

    # Refresh all questions
    for question in created_questions:
        await db.refresh(question)

    return created_questions


if __name__ == "__main__":
    print("🚀 DSBA LMS Data Seeder")
    print("=" * 50)

    asyncio.run(seed_data())

    print("=" * 50)
    print("✨ System is ready!")
    print("\n🌐 Start the application with:")
    print("   Backend: cd backend && uvicorn app.main:app --reload")
    print("   Frontend: cd frontend && npm run dev")
    print("\n📱 Access the application at: http://localhost:3000")
    print("=" * 50)
