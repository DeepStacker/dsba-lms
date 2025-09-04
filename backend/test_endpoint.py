#!/usr/bin/env python3
"""
Simple test script to verify users endpoint
"""
import asyncio
import aiohttp
import sys
sys.path.append('.')

from app.core.config import settings

async def test_users_endpoint():
    # Login first to get token
    login_url = "http://localhost:8000/auth/login"
    login_data = {
        "username": "admin@college.edu",
        "password": "Admin123!"
    }

    async with aiohttp.ClientSession() as session:
        # Login
        async with session.post(login_url, json=login_data) as response:
            if response.status != 200:
                print(f"Login failed: {response.status}")
                return

            auth_data = await response.json()
            token = auth_data.get("access_token")
            if not token:
                print("No access token in login response")
                return

            print("✓ Login successful")

            # Test users endpoint
            users_url = "http://localhost:8000/users"
            headers = {"Authorization": f"Bearer {token}"}

            async with session.get(users_url, headers=headers) as response:
                print(f"Users endpoint response: {response.status}")
                if response.status == 200:
                    users_data = await response.json()
                    print("✓ Users endpoint working!")
                    if "users" in users_data:
                        print(f"Found {len(users_data['users'])} users")
                        for user in users_data['users']:
                            print(f"  - {user['name']} ({user['role']})")
                    else:
                        print(f"Response: {users_data}")
                else:
                    print(f"Error: {response.status}")
                    error_text = await response.text()
                    print(f"Error details: {error_text}")

if __name__ == "__main__":
    print("Testing users endpoint...")
    print(f"Backend URL: http://localhost:8000")

    try:
        asyncio.run(test_users_endpoint())
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
