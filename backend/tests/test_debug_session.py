import pytest
from httpx import AsyncClient
from api import app


@pytest.mark.asyncio
async def test_check_session(client: AsyncClient, db_session):
    """Check which session is being used"""
    # Get the override function
    from config.database import get_db
    override_func = app.dependency_overrides[get_db]
    
    # Call it to see what we get
    async for session in override_func():
        print(f"DEBUG: Session from override: {session}")
        print(f"DEBUG: Session bind: {session.bind}")
        print(f"DEBUG: Session bind URL: {session.bind.url if hasattr(session.bind, 'url') else 'N/A'}")
        
        # Check if users table exists in this session
        from sqlalchemy import text
        result = await session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
        ))
        has_users = result.fetchone()
        print(f"DEBUG: Users table exists: {has_users is not None}")
        break  # Only iterate once
    
    # Now try the API call
    response = await client.post("/api/v1/auth/register", json={
        "email": "test123@example.com",
        "password": "password123",
        "name": "Test User"
    })
    
    print(f"DEBUG: Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"DEBUG: Response text: {response.text[:500]}")
