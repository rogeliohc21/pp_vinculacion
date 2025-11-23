import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict

from app.database import db

# Test user data
TEST_USER = {
    "username": "test@example.com",
    "email": "test@example.com",
    "password": "Test123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "estudiante"
}

# Database is reset inside the async_client fixture (app lifespan). No autouse fixture needed.

@pytest_asyncio.fixture
async def auth_token(async_client: AsyncClient) -> Dict:
    """Get auth token fixture"""
    # First register the user
    await async_client.post("/api/auth/register", json=TEST_USER)
    
    # Then login to get token
    response = await async_client.post(
        "/api/auth/login",
        data={
            "username": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
    )
    return response.json()

    @pytest.mark.asyncio
    async def test_register(async_client: AsyncClient):
        """Test user registration"""
        response = await async_client.post("/api/auth/register", json=TEST_USER)
        print("\nRegistro response:", response.status_code)
        print("Registro body:", response.json())
        assert response.status_code in [201, 400]  # 400 if user already exists
        if response.status_code == 201:
            data = response.json()
            assert data["email"] == TEST_USER["email"]
            assert "_id" in data  # MongoDB usa _id@pytest.mark.asyncio
async def test_login(async_client: AsyncClient):
    """Test user login"""
    # Ensure user exists first
    await async_client.post("/api/auth/register", json=TEST_USER)
    
    response = await async_client.post(
        "/api/auth/login",
        data={
        "username": TEST_USER["email"],
        "password": TEST_USER["password"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_me(async_client: AsyncClient, auth_token: Dict):
    """Test get user profile"""
    access_token = auth_token["access_token"]
    response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER["email"]