from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_permission
from ..core.security import get_password_hash, verify_password
from ..core.audit import log_audit_event, AUDIT_ACTIONS
from ..models.models import User
from ..schemas.user import UserCreate, UserUpdate, UserResponse, UserList, ChangePassword
from ..schemas.common import Response as CommonResponse

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
            summary="Create new user", tags=["Users"])
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user (Admin only)"""
    # Check if user has admin privileges
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create users"
        )

    # Check if user already exists
    existing_user = await db.execute(
        "SELECT id FROM users WHERE email = $1", (user_data.email,)
    )
    if existing_user.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Create new user
    password_hash = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    user_dict.pop("password")
    user_dict["hashed_password"] = password_hash
    user_dict["created_by"] = current_user.id

    result = await db.execute("""
        INSERT INTO users (email, name, role, hashed_password, is_active, created_by)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, email, name, role, is_active, created_at
    """, (
        user_dict["email"],
        user_dict["name"],
        user_dict["role"],
        user_dict["hashed_password"],
        user_dict.get("is_active", True),
        user_dict["created_by"]
    ))

    user = result.fetchone()
    return UserResponse(**user)

@router.get("/", response_model=UserList, summary="List users", tags=["Users"])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of users (Admin only for full list, others see only themselves)"""
    if current_user.role == "admin":
        query = """
            SELECT id, email, name, role, is_active, created_at, last_login
            FROM users
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (name ILIKE $1 OR email ILIKE $1)"
            params.append(f"%{search}%")

        query += " ORDER BY name LIMIT $%d OFFSET $%d" % (len(params) + 1, len(params) + 2)
        params.extend([limit, skip])

        result = await db.execute(query, params)
        users = result.fetchall()

        count = await db.execute("SELECT COUNT(*) FROM users WHERE name ILIKE $1 OR email ILIKE $1", (f"%{search}%" if search else "%",))
        total = count.fetchone()[0]

        return UserList(users=[UserResponse(**dict(user)) for user in users], total=total, skip=skip, limit=limit)

    else:
        # Non-admin users can only see their own data
        result = await db.execute("""
            SELECT id, email, name, role, is_active, created_at, last_login
            FROM users WHERE id = $1
        """, (current_user.id,))

        user = result.fetchone()
        return UserList(users=[UserResponse(**dict(user))], total=1, skip=skip, limit=limit)

@router.get("/me", response_model=UserResponse, summary="Get current user", tags=["Users"])
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(**current_user.__dict__)

@router.put("/me", response_model=UserResponse, summary="Update current user", tags=["Users"])
async def update_current_user(
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user profile"""
    update_dict = {k: v for k, v in user_data.dict().items() if v is not None}
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Build dynamic update query
    set_fields = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(update_dict.keys())])
    values = list(update_dict.values()) + [current_user.id]

    result = await db.execute(f"""
        UPDATE users SET {set_fields}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ${len(values)}
        RETURNING id, email, name, role, is_active, created_at, last_login
    """, values)

    updated_user = result.fetchone()
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**dict(updated_user))

@router.post("/change-password", summary="Change password", tags=["Users"])
async def change_password(
    password_data: ChangePassword,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change current user's password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash new password
    hashed_new_password = get_password_hash(password_data.new_password)

    # Update password
    await db.execute("""
        UPDATE users SET hashed_password = $1, updated_at = CURRENT_TIMESTAMP
        WHERE id = $2
    """, (hashed_new_password, current_user.id))

    return Response(message="Password changed successfully")

@router.delete("/{user_id}", summary="Delete user", tags=["Users"])
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete user (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users"
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    result = await db.execute("DELETE FROM users WHERE id = $1 RETURNING id", (user_id,))
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="User not found")

    return Response(message="User deleted successfully")

# Bulk import/export endpoints - commented out for now due to missing dependencies
# TODO: Implement bulk operations when all dependencies are available
# @router.post("/import", summary="Import users from CSV", tags=["Users"])
# async def import_users_csv(
#     file: UploadFile = File(...),
#     role: str = "student",
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(require_permission("write_user"))
# ):
#     """Import users from CSV file (Admin only)"""
#
#     if not file.filename.endswith('.csv'):
#         raise HTTPException(status_code=400, detail="File must be CSV format")
#
#     try:
#         csv_data = await file.read()
#         result = await import_users_from_csv(
#             csv_data=csv_data,
#             db=db,
#             current_user=current_user,
#             role=role
#         )
#
#         if result["errors"]:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Import failed: {', '.join(result['errors'][:3])}"
#             )
#
#         return {
#             "message": f"Successfully imported {result['imported_count']} users",
#             "imported_count": result["imported_count"],
#             "skipped_count": result["skipped_count"]
#         }
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")

# @router.get("/export", summary="Export users to CSV", tags=["Users"])
# async def export_users_csv(
#     role: Optional[str] = None,
#     is_active: Optional[bool] = None,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(require_permission("write_user"))
# ):
#     """Export users to CSV file (Admin only)"""
#
#     try:
#         filters = {}
#         if role:
#             filters["role"] = role
#         if is_active is not None:
#             filters["is_active"] = is_active
#
#         csv_data = await export_users_to_csv(
#             db=db,
#             current_user=current_user,
#             **filters
#         )
#
#         await log_audit_event(
#             db=db,
#             actor_id=current_user.id,
#             entity_type="user",
#             entity_id=None,
#             action=AUDIT_ACTIONS["BULK_EXPORT"],
#             reason="User export to CSV"
#         )
#
#         return FastAPIResponse(
#             content=csv_data,
#             media_type='text/csv',
#             headers={"Content-Disposition": "attachment; filename=users_export.csv"}
#         )
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

# @router.post("/reset-password-bulk", summary="Reset passwords for multiple users", tags=["Users"])
# async def reset_password_bulk(
#     user_ids: List[int],
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(require_role(["admin"]))
# ):
#     """Reset passwords for multiple users (Admin only)"""
#
#     try:
#         reset_users = []
#         for user_id in user_ids:
#             if user_id == current_user.id:
#                 continue  # Cannot reset own password via bulk
#
#             result = await db.execute(
#                 select(User).where(User.id == user_id, User.is_active == True)
#             )
#             user = result.scalar_one_or_none()
#
#             if user:
#                 temp_password = f"TempPw{user_id}{user.username}"
#                 hashed_password = get_password_hash(temp_password)
#
#                 await db.execute("""
#                     UPDATE users
#                     SET hashed_password = $1, updated_at = NOW()
#                     WHERE id = $2
#                 """, (hashed_password, user_id))
#
#                 reset_users.append({
#                     "id": user.id,
#                     "username": user.username,
#                     "email": user.email,
#                     "temp_password": temp_password
#                 })
#
#         await db.commit()
#
#         if reset_users:
#             await log_audit_event(
#                 db=db,
#                 actor_id=current_user.id,
#                 entity_type="user",
#                 entity_id=None,
#                 action=AUDIT_ACTIONS["BULK_UPDATE"],
#                 reason=f"Bulk password reset for {len(reset_users)} users"
#             )
#
#         return {
#             "message": f"Reset passwords for {len(reset_users)} users",
#             "reset_users": reset_users
#         }
#
#     except Exception as e:
#         await db.rollback()
#         raise HTTPException(status_code=500, detail=f"Bulk reset error: {str(e)}")
