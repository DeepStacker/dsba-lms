#!/usr/bin/env python3
"""
Seed script for Apollo LMS - Creates demo data for development and testing
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import json

from app.core.database import Base, get_db
from app.models.models import (
    User, Program, PO, Course, CO, CO_PO_Map, ClassSection,
    Enrollment, Question, QuestionOption, Exam, ExamQuestion,
    Attempt, Response, InternalComponent, InternalScore,
    AuditLog, LockWindow
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Sample data
PROGRAMS_DATA = [
    {"name": "Computer Science Engineering", "year": 2023},
    {"name": "Electrical Engineering", "year": 2023},
]

PO_DATA = [
    {"code": "PO1", "title": "Engineering Knowledge", "program_index": 0},
    {"code": "PO2", "title": "Problem Analysis", "program_index": 0},
    {"code": "PO3", "title": "Design & Development", "program_index": 0},
    {"code": "PO4", "title": "Engineering Ethics", "program_index": 0},
    {"code": "PO5", "title": "Modern Tool Usage", "program_index": 0},
    {"code": "PO6", "title": "Team Leadership", "program_index": 0},
]

COURSE_DATA = [
    {"code": "CS101", "name": "Introduction to Programming", "credits": 4, "program_index": 0},
    {"code": "CS201", "name": "Data Structures & Algorithms", "credits": 4, "program_index": 0},
    {"code": "CS301", "name": "Database Management Systems", "credits": 3, "program_index": 0},
    {"code": "CS401", "name": "Software Engineering", "credits": 4, "program_index": 0},
]

CO_DATA = [
    {"code": "CO1.1", "title": "Understand basic programming concepts", "course_index": 0},
    {"code": "CO1.2", "title": "Write simple programs", "course_index": 0},
    {"code": "CO1.3", "title": "Debug and test programs", "course_index": 0},
]

CO_PO_MAPPING = [
    {"co_index": 0, "po_index": 0, "weight": 0.8},
    {"co_index": 0, "po_index": 1, "weight": 0.6},
    {"co_index": 1, "po_index": 1, "weight": 0.9},
    {"co_index": 1, "po_index": 2, "weight": 0.7},
]

USER_DATA = [
    {"username": "admin.hod", "email": "admin@college.edu", "name": "Dr. Admin", "role": "admin",
     "phone": "+1234567890", "hashed_password": pwd_context.hash("admin123")},
    {"username": "teacher.cs", "email": "teacher.cs@college.edu", "name": "Prof. John Smith", "role": "teacher",
     "phone": "+1234567891", "hashed_password": pwd_context.hash("teacher123")},
    {"username": "student.1", "email": "student1@college.edu", "name": "Alice Johnson", "role": "student",
     "phone": "+1234567892", "hashed_password": pwd_context.hash("student123")},
    {"username": "student.2", "email": "student2@college.edu", "name": "Bob Wilson", "role": "student",
     "phone": "+1234567893", "hashed_password": pwd_context.hash("student123")},
    {"username": "student.3", "email": "student3@college.edu", "name": "Charlie Brown", "role": "student",
     "phone": "+1234567894", "hashed_password": pwd_context.hash("student123")},
]

CLASS_SECTIONS_DATA = [
    {"course_index": 0, "name": "CS101-A", "term": "Fall", "year": 2023},
    {"course_index": 1, "name": "CS201-A", "term": "Fall", "year": 2023},
]

ENROLLMENTS_DATA = [
    {"student_index": 2, "class_index": 0},
    {"student_index": 3, "class_index": 0},
    {"student_index": 4, "class_index": 1},
]

QUESTION_DATA = [
    {
        "text": "What is the output of print(2 + 3)?",
        "type": "mcq",
        "max_marks": 1,
        "co_index": 0,
        "creator_index": 1,
        "options": [
            {"text": "5", "is_correct": True},
            {"text": "23", "is_correct": False},
            {"text": "Error", "is_correct": False}
        ]
    },
    {
        "text": "Explain the difference between stack and queue data structures.",
        "type": "descriptive",
        "max_marks": 5,
        "co_index": 1,
        "creator_index": 1,
        "model_answer": "A stack is LIFO (Last In First Out) while queue is FIFO (First In First Out). In stack, elements are added and removed from the same end (top). In queue, elements are added at rear and removed from front."
    },
    {
        "text": "What is the time complexity of insertion sort in worst case?",
        "type": "numeric",
        "max_marks": 1,
        "co_index": 1,
        "creator_index": 1
    }
]

EXAM_DATA = {
    "class_index": 0,
    "title": "Programming Fundamentals Quiz",
    "start_at": datetime.utcnow() + timedelta(hours=1),
    "end_at": datetime.utcnow() + timedelta(hours=3),
    "join_window_sec": 300,
    "settings_json": {"max_attempts": 1},
    "status": "published"
}

EXAM_QUESTIONS_DATA = [
    {"question_index": 0, "order": 1, "marks_override": None},
    {"question_index": 1, "order": 2, "marks_override": None},
    {"question_index": 2, "order": 3, "marks_override": None}
]

ATTEMPT_DATA = {
    "student_index": 2,
    "started_at": datetime.utcnow() + timedelta(hours=1, minutes=5),
    "submitted_at": datetime.utcnow() + timedelta(hours=2, minutes=30),
    "status": "submitted",
    "autosubmitted": False
}

RESPONSE_DATA = [
    {
        "question_index": 0,
        "answer_json": {"selected_option": 0},
        "final_score": 1
    },
    {
        "question_index": 1,
        "answer_json": {"answer": "Stack uses LIFO principle while queue uses FIFO. Stack has one open end, queue has different ends for insertion and deletion."},
        "final_score": 4
    },
    {
        "question_index": 2,
        "answer_json": {"answer": "O(n^2)"},
        "final_score": 1
    }
]

INTERNAL_COMPONENTS_DATA = [
    {"course_index": 0, "name": "Semester 1", "weight_percent": 100},
]

INTERNAL_SCORES_DATA = [
    {"student_index": 2, "component_index": 0, "raw_score": 98, "max_score": 100},
    {"student_index": 3, "component_index": 0, "raw_score": 92, "max_score": 100},
]

class SeedManager:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.programs = []
        self.pos = []
        self.courses = []
        self.cos = []
        self.users = []
        self.class_sections = []
        self.questions = []
        self.exam = None
        self.attempt = None
        self.exam_questions = []
        self.responses = []
        self.internal_components = []
        self.internal_scores = []

    async def seed_all(self):
        await self.seed_users()
        await self.seed_programs()
        await self.seed_po()
        await self.seed_course()
        await self.seed_co()
        await self.seed_co_po_map()
        await self.seed_class_sections()
        await self.seed_enrollments()
        await self.seed_questions()
        await self.seed_exam()
        await self.seed_attempts()
        await self.seed_responses()
        await self.seed_internal_components()
        await self.seed_internal_scores()
        await self.seed_lock_windows()

        print("✅ All demo data seeded successfully!")
        print("\n--- Demo Credentials ---")
        print("Admin: admin@college.edu / admin123")
        print("Teacher: teacher.cs@college.edu / teacher123")
        print("Students: student1-3@college.edu / student123")

    async def seed_users(self):
        print("Seeding users...")
        for user_data in USER_DATA:
            user = User(**user_data)
            self.db.add(user)
            self.users.append(user)
        await self.db.commit()

    async def seed_programs(self):
        print("Seeding programs...")
        for prog_data in PROGRAMS_DATA:
            program = Program(**prog_data)
            self.db.add(program)
            self.programs.append(program)
        await self.db.commit()

    async def seed_po(self):
        print("Seeding program outcomes...")
        for po_data in PO_DATA:
            if po_data["program_index"] < len(self.programs):
                po = PO(
                    program_id=self.programs[po_data["program_index"]].id,
                    code=po_data["code"],
                    title=po_data["title"],
                    version=1
                )
                self.db.add(po)
                self.pos.append(po)
        await self.db.commit()

    async def seed_course(self):
        print("Seeding courses...")
        for course_data in COURSE_DATA:
            if course_data["program_index"] < len(self.programs):
                course = Course(
                    program_id=self.programs[course_data["program_index"]].id,
                    code=course_data["code"],
                    title=course_data["name"],
                    credits=course_data["credits"]
                )
                self.db.add(course)
                self.courses.append(course)
        await self.db.commit()

    async def seed_co(self):
        print("Seeding course outcomes...")
        for co_data in CO_DATA:
            if co_data["course_index"] < len(self.courses):
                co = CO(
                    course_id=self.courses[co_data["course_index"]].id,
                    code=co_data["code"],
                    title=co_data["title"],
                    bloom="understand",
                    version=1
                )
                self.db.add(co)
                self.cos.append(co)
        await self.db.commit()

    async def seed_co_po_map(self):
        print("Seeding CO-PO mappings...")
        for mapping in CO_PO_MAPPING:
            if (mapping["co_index"] < len(self.cos) and
                mapping["po_index"] < len(self.pos)):
                co_po_map = CO_PO_Map(
                    co_id=self.cos[mapping["co_index"]].id,
                    po_id=self.pos[mapping["po_index"]].id,
                    weight=mapping["weight"]
                )
                self.db.add(co_po_map)
        await self.db.commit()

    async def seed_class_sections(self):
        print("Seeding class sections...")
        for class_data in CLASS_SECTIONS_DATA:
            if class_data["course_index"] < len(self.courses):
                class_section = ClassSection(
                    course_id=self.courses[class_data["course_index"]].id,
                    name=class_data["name"],
                    term=class_data["term"],
                    year=class_data["year"]
                )
                self.db.add(class_section)
                self.class_sections.append(class_section)
        await self.db.commit()

    async def seed_enrollments(self):
        print("Seeding enrollments...")
        for enroll_data in ENROLLMENTS_DATA:
            if (enroll_data["student_index"] < len(self.users) and
                enroll_data["class_index"] < len(self.class_sections)):
                enrollment = Enrollment(
                    class_id=self.class_sections[enroll_data["class_index"]].id,
                    student_id=self.users[enroll_data["student_index"]].id
                )
                self.db.add(enrollment)
        await self.db.commit()

    async def seed_questions(self):
        print("Seeding questions...")
        for question_data in QUESTION_DATA:
            if (question_data["co_index"] < len(self.cos) and
                question_data["creator_index"] < len(self.users)):

                question = Question(
                    text=question_data["text"],
                    type=question_data["type"],
                    max_marks=question_data["max_marks"],
                    co_id=self.cos[question_data["co_index"]].id,
                    created_by=self.users[question_data["creator_index"]].id,
                    model_answer=question_data.get("model_answer", ""),
                    meta={"generated": False, "difficulty": "easy"}
                )
                self.db.add(question)
                self.questions.append(question)

                # Add options if present
                if "options" in question_data:
                    for option_data in question_data["options"]:
                        option = QuestionOption(
                            question_id=question.id,  # Will be set after commit
                            text=option_data["text"],
                            is_correct=option_data["is_correct"]
                        )
                        self.db.add(option)

        await self.db.commit()

        # Update question_id for options after commit
        for question, question_data in zip(self.questions, QUESTION_DATA):
            if "options" in question_data:
                for option_data in question_data["options"]:
                    option = QuestionOption(
                        question_id=question.id,
                        text=option_data["text"],
                        is_correct=option_data["is_correct"]
                    )
                    self.db.add(option)

        await self.db.commit()

    async def seed_exam(self):
        print("Seeding exams...")
        if self.class_sections:
            self.exam = Exam(
                class_id=self.class_sections[0].id,
                title=EXAM_DATA["title"],
                start_at=EXAM_DATA["start_at"],
                end_at=EXAM_DATA["end_at"],
                join_window_sec=EXAM_DATA["join_window_sec"],
                settings_json=EXAM_DATA["settings_json"],
                status=EXAM_DATA["status"]
            )
            self.db.add(self.exam)
            await self.db.commit()

    async def seed_attempts(self):
        print("Seeding attempts...")
        if self.exam and len(self.users) > 2:
            self.attempt = Attempt(
                exam_id=self.exam.id,
                student_id=self.users[2].id,
                started_at=ATTEMPT_DATA["started_at"],
                submitted_at=ATTEMPT_DATA["submitted_at"],
                status=ATTEMPT_DATA["status"],
                autosubmitted=ATTEMPT_DATA["autosubmitted"]
            )
            self.db.add(self.attempt)
            await self.db.commit()

    async def seed_responses(self):
        print("Seeding responses...")
        if self.attempt and self.questions:
            for response_data, question in zip(RESPONSE_DATA, self.questions):
                response = Response(
                    attempt_id=self.attempt.id,
                    question_id=question.id,
                    answer_json=response_data["answer_json"],
                    final_score=response_data["final_score"]
                )
                self.db.add(response)
                self.responses.append(response)

            await self.db.commit()

    async def seed_internal_components(self):
        print("Seeding internal components...")
        for component_data in INTERNAL_COMPONENTS_DATA:
            if component_data["course_index"] < len(self.courses):
                component = InternalComponent(
                    course_id=self.courses[component_data["course_index"]].id,
                    name=component_data["name"],
                    weight_percent=component_data["weight_percent"]
                )
                self.db.add(component)
                self.internal_components.append(component)
        await self.db.commit()

    async def seed_internal_scores(self):
        print("Seeding internal scores...")
        for score_data in INTERNAL_SCORES_DATA:
            if (score_data["student_index"] < len(self.users) and
                score_data["component_index"] < len(self.internal_components)):
                score = InternalScore(
                    student_id=self.users[score_data["student_index"]].id,
                    course_id=self.courses[score_data["course_index"]].id,
                    component_id=self.internal_components[score_data["component_index"]].id,
                    raw_score=score_data["raw_score"],
                    max_score=score_data["max_score"]
                )
                self.db.add(score)
                self.internal_scores.append(score)
        await self.db.commit()

    async def seed_lock_windows(self):
        print("Seeding lock windows...")
        lock_window = LockWindow(
            scope="exam_results",
            starts_at=datetime.utcnow() - timedelta(days=7),
            ends_at=datetime.utcnow() + timedelta(days=7),
            status="active",
            policy_json={
                "default_days": 7,
                "weekly_lock_saturday": True,
                "override_requires_auditor": False
            }
        )
        self.db.add(lock_window)
        await self.db.commit()


async def main():
    # Use the same database URL as the application
    from app.core.config import settings
    engine = create_async_engine(str(settings.database_url))

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        seed_manager = SeedManager(session)
        await seed_manager.seed_all()


if __name__ == "__main__":
    print("🚀 Starting Apollo LMS seed process...")
    asyncio.run(main())