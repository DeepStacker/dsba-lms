import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.models.models import User, Base
from app.core.database import engine
from app.core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

async def create_tables_if_needed():
    """Create tables if they don't exist"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Tables created/verified")
    except Exception as e:
        print(f"Error creating tables: {e}")

async def create_admin_user():
    try:
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Check if admin already exists
            result = await session.execute(select(User).filter(User.username == "admin"))
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                print("✅ Admin user already exists")
                print(f"Username: {existing_admin.username}")
                print(f"Email: {existing_admin.email}")
                print("Password: Admin123!")
                return

            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@college.edu",
                name="System Administrator",
                role="admin",
                hashed_password=get_password_hash("Admin123!"),
                is_active=True
            )

            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

            print("✅ Admin user created successfully!")
            print("Login credentials:")
            print("Username: admin")
            print("Password: Admin123!")
            print("Email: admin@college.edu")
            print("Role: admin")

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("🔧 Setting up DSBA LMS Database...")
    await create_tables_if_needed()
    await create_admin_user()

if __name__ == "__main__":
    asyncio.run(main())