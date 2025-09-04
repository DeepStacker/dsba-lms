from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
import pandas as pd
import io
import logging
from datetime import datetime

from ..models.models import User, Course, ClassSection, Enrollment, InternalScore, InternalComponent
from ..core.security import get_password_hash
from ..core.audit import log_audit_event, AUDIT_ACTIONS

logger = logging.getLogger(__name__)

class BulkOperationsService:
    """Service for bulk operations like user import/export"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def import_users_from_csv(self, csv_data: bytes, role: str = "student", 
                                  created_by: int = None) -> Dict[str, Any]:
        """Import users from CSV data"""
        
        try:
            # Read CSV data
            df = pd.read_csv(io.BytesIO(csv_data))
            
            # Validate required columns
            required_columns = ['name', 'email', 'username']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    "success": False,
                    "error": f"Missing required columns: {', '.join(missing_columns)}",
                    "imported_count": 0,
                    "skipped_count": 0,
                    "errors": []
                }
            
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Check if user already exists
                    existing_user = await self.db.execute(
                        select(User).where(
                            (User.email == row['email']) | 
                            (User.username == row['username'])
                        )
                    )
                    
                    if existing_user.scalar_one_or_none():
                        skipped_count += 1
                        errors.append(f"Row {index + 1}: User with email {row['email']} or username {row['username']} already exists")
                        continue
                    
                    # Generate default password if not provided
                    password = row.get('password', f"{row['username']}123")
                    
                    # Create user
                    user = User(
                        name=row['name'],
                        email=row['email'],
                        username=row['username'],
                        role=role,
                        hashed_password=get_password_hash(password),
                        phone=row.get('phone'),
                        department=row.get('department'),
                        is_active=row.get('is_active', True),
                        first_login=True,
                        created_by=created_by
                    )
                    
                    self.db.add(user)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
                    skipped_count += 1
            
            await self.db.commit()
            
            return {
                "success": True,
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "errors": errors[:10]  # Limit errors shown
            }
            
        except Exception as e:
            logger.error(f"CSV import error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "imported_count": 0,
                "skipped_count": 0,
                "errors": []
            }
    
    async def export_users_to_csv(self, role: Optional[str] = None, 
                                 is_active: Optional[bool] = None) -> str:
        """Export users to CSV format"""
        
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        # Convert to DataFrame
        user_data = []
        for user in users:
            user_data.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "username": user.username,
                "role": user.role.value,
                "phone": user.phone,
                "department": user.department,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            })
        
        df = pd.DataFrame(user_data)
        
        # Convert to CSV
        output = io.StringIO()
        df.to_csv(output, index=False)
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    async def bulk_enroll_students(self, class_id: int, student_ids: List[int], 
                                  enrolled_by: int) -> Dict[str, Any]:
        """Bulk enroll students in a class"""
        
        # Verify class exists
        class_result = await self.db.execute(select(ClassSection).where(ClassSection.id == class_id))
        if not class_result.scalar_one_or_none():
            return {
                "success": False,
                "error": "Class section not found",
                "enrolled_count": 0,
                "skipped_count": 0,
                "errors": []
            }
        
        enrolled_count = 0
        skipped_count = 0
        errors = []
        
        for student_id in student_ids:
            try:
                # Check if student exists
                student_result = await self.db.execute(
                    select(User).where(User.id == student_id, User.role == "student")
                )
                if not student_result.scalar_one_or_none():
                    errors.append(f"Student with ID {student_id} not found")
                    skipped_count += 1
                    continue
                
                # Check if already enrolled
                existing_enrollment = await self.db.execute(
                    select(Enrollment).where(
                        Enrollment.class_id == class_id,
                        Enrollment.student_id == student_id
                    )
                )
                if existing_enrollment.scalar_one_or_none():
                    errors.append(f"Student {student_id} already enrolled in this class")
                    skipped_count += 1
                    continue
                
                # Create enrollment
                enrollment = Enrollment(
                    class_id=class_id,
                    student_id=student_id
                )
                self.db.add(enrollment)
                enrolled_count += 1
                
            except Exception as e:
                errors.append(f"Student {student_id}: {str(e)}")
                skipped_count += 1
        
        await self.db.commit()
        
        # Log audit event
        await log_audit_event(
            db=self.db,
            actor_id=enrolled_by,
            entity_type="enrollment",
            entity_id=class_id,
            action=AUDIT_ACTIONS["BULK_UPDATE"],
            after_json={
                "class_id": class_id,
                "enrolled_count": enrolled_count,
                "student_ids": student_ids[:10]  # Limit for audit log
            },
            reason=f"Bulk enrolled {enrolled_count} students in class {class_id}"
        )
        
        return {
            "success": True,
            "enrolled_count": enrolled_count,
            "skipped_count": skipped_count,
            "errors": errors[:10]
        }
    
    async def bulk_update_internal_scores(self, csv_data: bytes, 
                                        updated_by: int) -> Dict[str, Any]:
        """Bulk update internal scores from CSV"""
        
        try:
            df = pd.read_csv(io.BytesIO(csv_data))
            
            required_columns = ['student_id', 'course_id', 'component_name', 'raw_score', 'max_score']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    "success": False,
                    "error": f"Missing required columns: {', '.join(missing_columns)}",
                    "updated_count": 0,
                    "errors": []
                }
            
            updated_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Find the internal component
                    component_result = await self.db.execute(
                        select(InternalComponent).where(
                            InternalComponent.course_id == row['course_id'],
                            InternalComponent.name == row['component_name']
                        )
                    )
                    component = component_result.scalar_one_or_none()
                    
                    if not component:
                        errors.append(f"Row {index + 1}: Component '{row['component_name']}' not found for course {row['course_id']}")
                        continue
                    
                    # Check if score already exists
                    existing_score = await self.db.execute(
                        select(InternalScore).where(
                            InternalScore.student_id == row['student_id'],
                            InternalScore.component_id == component.id
                        )
                    )
                    score = existing_score.scalar_one_or_none()
                    
                    if score:
                        # Update existing score
                        score.raw_score = row['raw_score']
                        score.max_score = row['max_score']
                    else:
                        # Create new score
                        score = InternalScore(
                            student_id=row['student_id'],
                            course_id=row['course_id'],
                            component_id=component.id,
                            raw_score=row['raw_score'],
                            max_score=row['max_score']
                        )
                        self.db.add(score)
                    
                    updated_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            await self.db.commit()
            
            # Log audit event
            await log_audit_event(
                db=self.db,
                actor_id=updated_by,
                entity_type="internal_score",
                entity_id=None,
                action=AUDIT_ACTIONS["BULK_UPDATE"],
                after_json={"updated_count": updated_count},
                reason=f"Bulk updated {updated_count} internal scores"
            )
            
            return {
                "success": True,
                "updated_count": updated_count,
                "errors": errors[:10]
            }
            
        except Exception as e:
            logger.error(f"Bulk internal scores update error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "updated_count": 0,
                "errors": []
            }
    
    async def generate_user_template_csv(self, role: str = "student") -> str:
        """Generate a CSV template for user import"""
        
        template_data = {
            "name": ["John Doe", "Jane Smith"],
            "email": ["john.doe@example.com", "jane.smith@example.com"],
            "username": ["john.doe", "jane.smith"],
            "phone": ["+1234567890", "+1234567891"],
            "department": ["Computer Science", "Information Technology"],
            "password": ["john.doe123", "jane.smith123"]
        }
        
        df = pd.DataFrame(template_data)
        
        output = io.StringIO()
        df.to_csv(output, index=False)
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    async def generate_internal_scores_template_csv(self, course_id: int) -> str:
        """Generate a CSV template for internal scores import"""
        
        # Get students enrolled in the course
        students_query = """
            SELECT DISTINCT u.id, u.name, u.username
            FROM users u
            JOIN enrollments e ON u.id = e.student_id
            JOIN class_sections cs ON e.class_id = cs.id
            WHERE cs.course_id = :course_id
            AND u.role = 'student'
            ORDER BY u.name
            LIMIT 5
        """
        
        result = await self.db.execute(students_query, {"course_id": course_id})
        students = result.fetchall()
        
        # Get internal components for the course
        components_result = await self.db.execute(
            select(InternalComponent).where(InternalComponent.course_id == course_id)
        )
        components = components_result.scalars().all()
        
        template_data = []
        for student in students:
            for component in components:
                template_data.append({
                    "student_id": student.id,
                    "student_name": student.name,
                    "course_id": course_id,
                    "component_name": component.name,
                    "raw_score": 0,
                    "max_score": 100
                })
        
        df = pd.DataFrame(template_data)
        
        output = io.StringIO()
        df.to_csv(output, index=False)
        csv_content = output.getvalue()
        output.close()
        
        return csv_content