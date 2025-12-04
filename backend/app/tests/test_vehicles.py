import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleStatus
from app.tests.conftest import auth_headers


class TestVehicleEndpoints:
    """Test vehicle CRUD endpoints."""
    
    @pytest.fixture
    async def sample_vehicle(self, db_session: AsyncSession) -> Vehicle:
        """Create a sample vehicle for testing."""
        vehicle = Vehicle(
            registration_plate="ABC-123",
            vin="1HGBH41JXMN109186",
            brand="Toyota",
            model="Corolla",
            status=VehicleStatus.ACTIVE
        )
        db_session.add(vehicle)
        await db_session.commit()
        await db_session.refresh(vehicle)
        return vehicle
    
    @pytest.mark.asyncio
    async def test_create_vehicle_as_admin(
        self, client: AsyncClient, test_admin_user: User, admin_token: str
    ):
        """Test creating a vehicle as admin."""
        response = await client.post(
            "/api/v1/vehicles",
            json={
                "registration_plate": "XYZ-789",
                "vin": "2HGBH41JXMN109186",
                "brand": "Honda",
                "model": "Civic",
                "status": "ACTIVE"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 201
        data = response.json()
        assert data["registration_plate"] == "XYZ-789"
        assert data["brand"] == "Honda"
        assert data["status"] == "ACTIVE"
    
    @pytest.mark.asyncio
    async def test_create_vehicle_as_rh(
        self, client: AsyncClient, test_rh_user: User, rh_token: str
    ):
        """Test creating a vehicle as RH user."""
        response = await client.post(
            "/api/v1/vehicles",
            json={
                "registration_plate": "DEF-456",
                "vin": "3HGBH41JXMN109186",
                "brand": "Ford",
                "model": "Focus",
                "status": "ACTIVE"
            },
            headers=auth_headers(rh_token)
        )
        assert response.status_code == 201
    
    @pytest.mark.asyncio
    async def test_create_vehicle_as_viewer_fails(
        self, client: AsyncClient, test_viewer_user: User, viewer_token: str
    ):
        """Test that viewer cannot create vehicles."""
        response = await client.post(
            "/api/v1/vehicles",
            json={
                "registration_plate": "GHI-789",
                "vin": "4HGBH41JXMN109186",
                "brand": "BMW",
                "model": "3 Series",
                "status": "ACTIVE"
            },
            headers=auth_headers(viewer_token)
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_create_vehicle_duplicate_plate(
        self, client: AsyncClient, test_admin_user: User, admin_token: str,
        sample_vehicle: Vehicle
    ):
        """Test that duplicate registration plate is rejected."""
        response = await client.post(
            "/api/v1/vehicles",
            json={
                "registration_plate": "ABC-123",  # Same as sample_vehicle
                "vin": "5HGBH41JXMN109186",
                "brand": "Nissan",
                "model": "Altima",
                "status": "ACTIVE"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 400
        assert "Registration plate already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_vehicle_invalid_vin(
        self, client: AsyncClient, test_admin_user: User, admin_token: str
    ):
        """Test that invalid VIN length is rejected."""
        response = await client.post(
            "/api/v1/vehicles",
            json={
                "registration_plate": "JKL-012",
                "vin": "SHORTVIN",  # Invalid length
                "brand": "Mazda",
                "model": "3",
                "status": "ACTIVE"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_list_vehicles(
        self, client: AsyncClient, test_viewer_user: User, viewer_token: str,
        sample_vehicle: Vehicle
    ):
        """Test listing vehicles as viewer."""
        response = await client.get(
            "/api/v1/vehicles",
            headers=auth_headers(viewer_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["registration_plate"] == "ABC-123"
    
    @pytest.mark.asyncio
    async def test_list_vehicles_with_status_filter(
        self, client: AsyncClient, test_admin_user: User, admin_token: str,
        db_session: AsyncSession
    ):
        """Test filtering vehicles by status."""
        # Create vehicles with different statuses
        active_vehicle = Vehicle(
            registration_plate="ACT-001",
            vin="6HGBH41JXMN109186",
            brand="Active",
            model="Model",
            status=VehicleStatus.ACTIVE
        )
        maintenance_vehicle = Vehicle(
            registration_plate="MNT-001",
            vin="7HGBH41JXMN109186",
            brand="Maintenance",
            model="Model",
            status=VehicleStatus.MAINTENANCE
        )
        db_session.add_all([active_vehicle, maintenance_vehicle])
        await db_session.commit()
        
        # Filter by ACTIVE
        response = await client.get(
            "/api/v1/vehicles?status=ACTIVE",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert all(v["status"] == "ACTIVE" for v in data)
    
    @pytest.mark.asyncio
    async def test_get_vehicle_by_id(
        self, client: AsyncClient, test_viewer_user: User, viewer_token: str,
        sample_vehicle: Vehicle
    ):
        """Test getting a specific vehicle."""
        response = await client.get(
            f"/api/v1/vehicles/{sample_vehicle.id}",
            headers=auth_headers(viewer_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_vehicle.id
        assert data["registration_plate"] == "ABC-123"
    
    @pytest.mark.asyncio
    async def test_get_vehicle_not_found(
        self, client: AsyncClient, test_viewer_user: User, viewer_token: str
    ):
        """Test getting non-existent vehicle."""
        response = await client.get(
            "/api/v1/vehicles/99999",
            headers=auth_headers(viewer_token)
        )
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_vehicle(
        self, client: AsyncClient, test_rh_user: User, rh_token: str,
        sample_vehicle: Vehicle
    ):
        """Test updating a vehicle."""
        response = await client.put(
            f"/api/v1/vehicles/{sample_vehicle.id}",
            json={
                "brand": "Toyota Updated",
                "model": "Camry"
            },
            headers=auth_headers(rh_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["brand"] == "Toyota Updated"
        assert data["model"] == "Camry"
        assert data["registration_plate"] == "ABC-123"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_vehicle_status(
        self, client: AsyncClient, test_admin_user: User, admin_token: str,
        sample_vehicle: Vehicle
    ):
        """Test updating vehicle status."""
        response = await client.patch(
            f"/api/v1/vehicles/{sample_vehicle.id}/status?new_status=MAINTENANCE",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "MAINTENANCE"
    
    @pytest.mark.asyncio
    async def test_delete_vehicle(
        self, client: AsyncClient, test_admin_user: User, admin_token: str,
        sample_vehicle: Vehicle
    ):
        """Test deleting a vehicle."""
        response = await client.delete(
            f"/api/v1/vehicles/{sample_vehicle.id}",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = await client.get(
            f"/api/v1/vehicles/{sample_vehicle.id}",
            headers=auth_headers(admin_token)
        )
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_vehicle_by_plate(
        self, client: AsyncClient, test_viewer_user: User, viewer_token: str,
        sample_vehicle: Vehicle
    ):
        """Test getting vehicle by registration plate."""
        response = await client.get(
            "/api/v1/vehicles/by-plate/ABC-123",
            headers=auth_headers(viewer_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["registration_plate"] == "ABC-123"
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test that unauthorized requests are rejected."""
        response = await client.get("/api/v1/vehicles")
        assert response.status_code == 401
