"""
Bulk operations service for CSV/XLSX import/export functionality
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
import io
import uuid
from datetime import datetime
import re
import csv
import logging

from ..models import User, Question, QuestionOption, Program, Course, CO, PO, CO_PO_Map, Enrollment
from ..core.security import get_password_hash
from ..core.audit import create_audit_log

logger = logging.getLogger(__name__)


class BulkOperationsError(Exception):
    pass


class BulkOperationsService:
    """Service for handling bulk operations like user import, grade upload, etc."""

    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user

    async def import_users_from_csv(self, csv_data: bytes,
                                  role: str = "student",
                                  notify_users: bool = True) -> Dict[str, Any]:
        """Import users from CSV data"""

        try:
            # Parse CSV data
            df = pd.read_csv(io.BytesIO(csv_data))

            # Validate required columns
            required_columns = ["username", "email", "name"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise BulkOperationsError(f"Missing required columns: {missing_columns}")

            # Validate data
            validation_errors = self._validate_user_import_data(df)
            if validation_errors:
                return {
                    "success": False,
                    "imported_count": 0,
                    "errors": validation_errors
                }

            # Import users
            imported_users = []
            skipped = 0

            for index, row in df.iterrows():
                username = row["username"]
                email = row["email"].lower().strip()
                name = row["name"]

                # Check if user already exists
                existing_user = await self.db.execute(
                    select(User).where(or_(User.username == username, User.email == email))
                )

                if existing_user.scalar_one_or_none():
                    skipped += 1
                    continue

                # Generate initial password
                temp_password = str(uuid.uuid4())[:8]  # Simple temp password
                hashed_password = get_password_hash(temp_password)

                # Create user
                user = User(
                    username=username,
                    email=email,
                    name=name,
                    role=role,
                    hashed_password=hashed_password,
                    is_active=True,
                    created_by=self.current_user.id
                )

                self.db.add(user)
                imported_users.append({
                    "username": username,
                    "email": email,
                    "temp_password": temp_password
                })

            await self.db.commit()

            # Create audit log
            await create_audit_log(
                db=self.db,
                actor_id=self.current_user.id,
                entity_type="user",
                entity_id=None,
                action="bulk_import",
                before_json=None,
                after_json={
                    "role": role,
                    "count": len(imported_users),
                    "total_records": len(df),
                    "skipped_existing": skipped
                },
                reason=f"Bulk import of {len(imported_users)} users"
            )

            return {
                "success": True,
                "imported_count": len(imported_users),
                "skipped_count": skipped,
                "total_records": len(df),
                "users": imported_users
            }

        except BulkOperationsError as e:
            logger.error(f"Bulk import validation error: {str(e)}")
            return {
                "success": False,
                "imported_count": 0,
                "errors": [str(e)]
            }
        except Exception as e:
            logger.error(f"Bulk import error: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "imported_count": 0,
                "errors": [f"Import failed: {str(e)}"]
            }

    async def export_users_to_csv(self, filters: Optional[Dict[str, Any]] = None) -> bytes:
        """Export users to CSV"""

        try:
            query = select(User)

            # Apply filters
            if filters:
                if filters.get("role"):
                    query = query.where(User.role == filters["role"])
                if filters.get("is_active") is not None:
                    query = query.where(User.is_active == filters["is_active"])
                if filters.get("created_after"):
                    query = query.where(User.created_at >= filters["created_after"])

            result = await self.db.execute(query)
            users = result.scalars().all()

            # Convert to DataFrame
            user_data = []
            for user in users:
                user_data.append({
                    "username": user.username,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role.value,
                    "is_active": user.is_active,
                    "mfa_enabled": user.mfa_enabled,
                    "last_login": user.last_login,
                    "created_at": user.created_at
                })

            df = pd.DataFrame(user_data)

            # Export to CSV
            buffer = io.BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Bulk export users error: {str(e)}")
            raise BulkOperationsError(f"Export failed: {str(e)}")

    async def import_questions_from_csv(self, csv_data: bytes,
                                      course_id: int,
                                      co_id: Optional[int] = None) -> Dict[str, Any]:
        """Import questions from CSV"""

        try:
            df = pd.read_csv(io.BytesIO(csv_data))

            # Validate required columns
            required_columns = ["text", "type", "max_marks"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise BulkOperationsError(f"Missing required columns: {missing_columns}")

            imported_questions = []

            for index, row in df.iterrows():
                question_type = row["type"].lower().strip()
                if question_type not in ["mcq", "msq", "tf", "numeric", "descriptive", "coding", "file_upload"]:
                    continue  # Skip invalid types

                # Create question
                question = Question(
                    text=row["text"],
                    type=question_type,
                    max_marks=row["max_marks"],
                    co_id=co_id,
                    created_by=self.current_user.id,
                    model_answer=row.get("model_answer"),
                    meta={"imported": True, "source": "bulk_import"}
                )

                self.db.add(question)
                imported_questions.append({
                    "id": question.id,
                    "text": question.text,
                    "type": question.type
                })

                # Handle options for MCQ/MSQ questions
                if question_type in ["mcq", "msq"] and "options" in df.columns:
                    options = str(row.get("options", "")).split(";")
                    for i, option_text in enumerate(options):
                        if option_text.strip():
                            is_correct = 0
                            if "correct_option" in df.columns:
                                correct_answers = str(row.get("correct_option", "")).split(";")
                                is_correct = i + 1 in map(int, correct_answers)

                            option = QuestionOption(
                                question=question,
                                text=option_text.strip(),
                                is_correct=is_correct
                            )
                            self.db.add(option)

            await self.db.commit()

            # Add to audit log
            await create_audit_log(
                db=self.db,
                actor_id=self.current_user.id,
                entity_type="question",
                entity_id=None,
                action="bulk_import",
                before_json=None,
                after_json={
                    "course_id": course_id,
                    "co_id": co_id,
                    "count": len(df),
                    "imported_count": len(imported_questions)
                },
                reason=f"Bulk import of {len(imported_questions)} questions"
            )

            return {
                "success": True,
                "imported_count": len(imported_questions),
                "total_records": len(df)
            }

        except Exception as e:
            logger.error(f"Bulk import questions error: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "imported_count": 0,
                "errors": [str(e)]
            }

    async def upload_grades_from_csv(self, csv_data: bytes,
                                   exam_id: int) -> Dict[str, Any]:
        """Upload grades from CSV"""

        try:
            df = pd.read_csv(io.BytesIO(csv_data))

            required_columns = ["student_email", "final_score"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise BulkOperationsError(f"Missing required columns: {missing_columns}")

            updated_count = 0

            for index, row in df.iterrows():
                student_email = row["student_email"].lower().strip()
                final_score = row.get("final_score")

                # Find student and their attempt
                result = await self.db.execute("""
                    UPDATE responses
                    SET final_score = $1, teacher_score = $1, updated_at = $2
                    WHERE attempt_id IN (
                        SELECT a.id FROM attempts a
                        JOIN users u ON u.id = a.student_id
                        WHERE u.email = $3 AND a.exam_id = $4
                    )
                """, (final_score, datetime.utcnow(), student_email, exam_id))

                if result:
                    updated_count += 1

            await self.db.commit()

            # Create audit log
            await create_audit_log(
                db=self.db,
                actor_id=self.current_user.id,
                entity_type="grade",
                entity_id=None,
                action="bulk_upload",
                before_json=None,
                after_json={
                    "exam_id": exam_id,
                    "updated_count": updated_count,
                    "total_records": len(df)
                },
                reason=f"Bulk upload of {updated_count} grades"
            )

            return {
                "success": True,
                "updated_count": updated_count,
                "total_records": len(df)
            }

        except Exception as e:
            logger.error(f"Bulk grade upload error: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "updated_count": 0,
                "errors": [str(e)]
            }

    def _validate_user_import_data(self, df: pd.DataFrame) -> List[str]:
        """Validate user import data"""

        errors = []

        # Check for duplicate emails in CSV
        duplicate_emails = df[df.duplicated(["email"], keep=False)]
        if not duplicate_emails.empty:
            errors.append("Duplicate emails found in CSV data")

        # Check for duplicate usernames in CSV
        duplicate_usernames = df[df.duplicated(["username"], keep=False)]
        if not duplicate_usernames.empty:
            errors.append("Duplicate usernames found in CSV data")

        # Validate email format
        email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        for index, row in df.iterrows():
            email = row.get("email", "")
            if not email_pattern.match(str(email)):
                errors.append(f"Invalid email format at row {index + 1}: {email}")

        # Check required fields
        for index, row in df.iterrows():
            if pd.isna(row.get("username")) or str(row.get("username")).strip() == "":
                errors.append(f"Missing username at row {index + 1}")
            if pd.isna(row.get("email")) or str(row.get("email")).strip() == "":
                errors.append(f"Missing email at row {index + 1}")
            if pd.isna(row.get("name")) or str(row.get("name")).strip() == "":
                errors.append(f"Missing name at row {index + 1}")

        return errors[:10]  # Limit to first 10 errors to avoid too many


async def import_users_from_csv(csv_data: bytes, db: AsyncSession, current_user: User,
                               **kwargs) -> Dict[str, Any]:
    """Convenience function for user import"""
    service = BulkOperationsService(db, current_user)
    return await service.import_users_from_csv(csv_data, **kwargs)


async def export_users_to_csv(db: AsyncSession, current_user: User,
                             **filters) -> bytes:
    """Convenience function for user export"""
    service = BulkOperationsService(db, current_user)
    return await service.export_users_to_csv(filters)


async def import_questions_from_csv(csv_data: bytes, db: AsyncSession, current_user: User,
                                   course_id: int, co_id: Optional[int] = None) -> Dict[str, Any]:
    """Convenience function for question import"""
    service = BulkOperationsService(db, current_user)
    return await service.import_questions_from_csv(csv_data, course_id, co_id)


async def upload_grades_from_csv(csv_data: bytes, db: AsyncSession, current_user: User,
                                exam_id: int) -> Dict[str, Any]:
    """Convenience function for grade upload"""
    service = BulkOperationsService(db, current_user)
    return await service.upload_grades_from_csv(csv_data, exam_id)