#!/usr/bin/env python3
"""
Fix user passwords with correct hashing
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

# Import from app
import sys
sys.path.append('.')
from app.models.models import User, Role
from app.core.security import get_password_hash
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_admin_user():
    """Fix the admin user password"""
    try:
        # Connect to database
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with AsyncSessionLocal() as session:
            # Check if admin user exists
            result = await session.execute(
                select(User).where(User.username == "admin@college.edu")
            )
            user = result.scalar_one_or_none()

            if user:
                logger.info(f"Found existing admin user: {user.username}")
                # Update password with correct hash
                user.hashed_password = get_password_hash("Admin123!")
                await session.commit()
                logger.info("Updated admin user password successfully!")
            else:
                # Create new admin user
                logger.info("Creating new admin user")
                admin_user = User(
                    username="admin@college.edu",
                    email="admin@college.edu",
                    name="System Administrator",
                    hashed_password=get_password_hash("Admin123!"),
                    role=Role.ADMIN,
                    is_active=True
                )
                session.add(admin_user)
                await session.commit()
                logger.info("Created new admin user successfully!")

        print("\n" + "="*50)
        print("✅ ADMIN USER FIXED!")
        print("="*50)
        print("Login credentials:")
        print("  Username: admin@college.edu")
        print("  Password: Admin123!")
        print("  Role: admin")
        print("="*50)

    except Exception as e:
        logger.error(f"Error fixing admin user: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(fix_admin_user())
