import pytest
from httpx import AsyncClient
from app.models.user import User
from app.tests.conftest import auth_headers


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_setup_first_admin(self, client: AsyncClient):
        """Test initial admin setup when no users exist."""
        response = await client.post(
            "/api/v1/auth/setup",
            json={
                "email": "firstadmin@test.com",
                "password": "securepassword123",
                "role": "ADMIN"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "firstadmin@test.com"
        assert data["role"] == "ADMIN"
        assert "password" not in data
        assert "password_hash" not in data
    
    @pytest.mark.asyncio
    async def test_setup_fails_when_users_exist(
        self, client: AsyncClient, test_admin_user: User
    ):
        """Test that setup fails when users already exist."""
        response = await client.post(
            "/api/v1/auth/setup",
            json={
                "email": "anotherlad@test.com",
                "password": "password123",
                "role": "ADMIN"
            }
        )
        assert response.status_code == 400
        assert "Setup already completed" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_admin_user: User):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin@test.com",
                "password": "adminpassword"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_json_success(self, client: AsyncClient, test_admin_user: User):
        """Test successful login with JSON body."""
        response = await client.post(
            "/api/v1/auth/login/json",
            json={
                "email": "admin@test.com",
                "password": "adminpassword"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, test_admin_user: User):
        """Test login with invalid password."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin@test.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@test.com",
                "password": "password"
            }
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user(
        self, client: AsyncClient, test_admin_user: User, admin_token: str
    ):
        """Test getting current user info."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["role"] == "ADMIN"
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, test_admin_user: User):
        """Test token refresh."""
        # First login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin@test.com",
                "password": "adminpassword"
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new tokens
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_register_user_as_admin(
        self, client: AsyncClient, test_admin_user: User, admin_token: str
    ):
        """Test user registration by admin."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "newpassword123",
                "role": "VIEWER"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "VIEWER"
    
    @pytest.mark.asyncio
    async def test_register_user_as_non_admin_fails(
        self, client: AsyncClient, test_rh_user: User, rh_token: str
    ):
        """Test that non-admin cannot register users."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "newpassword123",
                "role": "VIEWER"
            },
            headers=auth_headers(rh_token)
        )
        assert response.status_code == 403



