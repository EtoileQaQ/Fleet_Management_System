# FleetPulse - Fleet Management SaaS

A modern fleet management system built with FastAPI, PostgreSQL (PostGIS), Redis, Celery, and React.

## 🚀 Features

- **User Authentication**: JWT-based authentication with refresh tokens
- **Role-Based Access Control (RBAC)**: ADMIN, RH (write access), VIEWER (read-only)
- **Vehicle Management**: Full CRUD operations for fleet vehicles
- **Driver Management**: Manage drivers and assign them to vehicles
- **GPS Tracking**: Real-time GPS position ingestion with PostGIS
- **Tachograph Integration**: Upload and parse .DDD/.TGD tachograph files
- **Driver Activities**: Track driving, rest, work, and break periods
- **Real-time Status**: Online/Offline indicators based on GPS pings
- **Async Architecture**: Fully asynchronous database operations with SQLAlchemy 2.0
- **Background Tasks**: Celery workers for async task processing
- **Modern UI**: React frontend with a sleek dark theme

## 🏗️ Tech Stack

### Backend
- **Python 3.11** with FastAPI
- **SQLAlchemy 2.0** (Async) + GeoAlchemy2
- **PostgreSQL** with PostGIS extension
- **Redis** for caching and Celery broker
- **Celery** for background tasks
- **Alembic** for database migrations
- **Pydantic v2** for data validation

### Frontend
- **React 18** with React Router
- **TanStack Query** for data fetching
- **Zustand** for state management
- **Lucide React** for icons

## 📦 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### 1. Clone and Start Services

```bash
# Clone the repository
git clone <repository-url>
cd fleet-management

# Start all services
docker-compose up -d --build
```

### 2. Run Database Migrations

```bash
# Connect to the API container and run migrations
docker-compose exec api alembic upgrade head
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/api/v1/docs
- **API ReDoc**: http://localhost:8000/api/v1/redoc

### 4. Initial Setup

1. Open http://localhost:3000
2. Click "First time? Set up admin account"
3. Create your admin account with email and password
4. Start managing your fleet!

## 🔧 Development

### Backend Development

```bash
# Install dependencies locally (optional)
cd backend
pip install -r requirements.txt

# Run tests
docker-compose exec api pytest -v

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Load Testing (Simulate 100 trucks)

```bash
# Run load test for telematics endpoint
docker-compose exec api python scripts/load_test.py --trucks 100 --duration 60 --interval 60
```

## 📚 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/setup` | Initial admin setup |
| POST | `/api/v1/auth/login` | Login (OAuth2 form) |
| POST | `/api/v1/auth/login/json` | Login (JSON body) |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/auth/register` | Register user (Admin only) |

### Vehicles
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/vehicles` | List all vehicles |
| GET | `/api/v1/vehicles/{id}` | Get vehicle by ID |
| POST | `/api/v1/vehicles` | Create vehicle |
| PUT | `/api/v1/vehicles/{id}` | Update vehicle |
| DELETE | `/api/v1/vehicles/{id}` | Delete vehicle |
| PATCH | `/api/v1/vehicles/{id}/status` | Update vehicle status |
| GET | `/api/v1/vehicles/by-plate/{plate}` | Get by registration plate |

### Drivers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/drivers` | List all drivers |
| GET | `/api/v1/drivers/{id}` | Get driver by ID |
| POST | `/api/v1/drivers` | Create driver |
| PUT | `/api/v1/drivers/{id}` | Update driver |
| DELETE | `/api/v1/drivers/{id}` | Delete driver |
| POST | `/api/v1/drivers/{id}/assign-vehicle/{vehicle_id}` | Assign vehicle |
| POST | `/api/v1/drivers/{id}/unassign-vehicle` | Unassign vehicle |

### Tachograph
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tachograph/upload` | Upload .DDD/.TGD file |
| GET | `/api/v1/tachograph/activities/{driver_id}` | Get driver activities |
| GET | `/api/v1/tachograph/summary/{driver_id}` | Get activity summary |
| POST | `/api/v1/tachograph/fuse-gps/{driver_id}` | Associate GPS with activities |

### Telematics
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/telematics/position` | Ingest single GPS position |
| POST | `/api/v1/telematics/position/batch` | Ingest batch of positions |
| GET | `/api/v1/telematics/status/{vehicle_id}` | Get vehicle online status |
| GET | `/api/v1/telematics/status` | Get all vehicles status |
| GET | `/api/v1/telematics/stats/online` | Get online/offline counts |
| POST | `/api/v1/telematics/ping` | Lightweight device ping |

## 🔐 User Roles

| Role | Permissions |
|------|-------------|
| ADMIN | Full access + user management |
| RH | Read + Write (create, update, delete) |
| VIEWER | Read only |

## 📁 Project Structure

```
fleet-management/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── scripts/
│   │   └── load_test.py
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models/
│       │   ├── user.py
│       │   ├── driver.py
│       │   ├── vehicle.py
│       │   ├── gps_position.py
│       │   └── driver_activity.py
│       ├── schemas/
│       │   ├── tachograph.py
│       │   └── telematics.py
│       ├── services/
│       │   ├── tachograph_parser.py
│       │   ├── telematics_service.py
│       │   └── activity_service.py
│       ├── api/
│       │   ├── deps.py
│       │   ├── auth.py
│       │   ├── drivers.py
│       │   ├── vehicles.py
│       │   ├── tachograph.py
│       │   └── telematics.py
│       ├── core/
│       │   ├── security.py
│       │   └── rbac.py
│       ├── celery_worker/
│       └── tests/
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── public/
    └── src/
        ├── api/
        │   ├── tachograph.js
        │   └── telematics.js
        ├── components/
        ├── pages/
        │   └── Upload.js
        └── store/
```

## 🧪 Running Tests

```bash
# Run all tests
docker-compose exec api pytest -v

# Run with coverage
docker-compose exec api pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec api pytest app/tests/test_auth.py -v
```

## 🗄️ Database

The application uses PostgreSQL with PostGIS for geospatial data. The GPS positions table is designed for time-series data and can be converted to a TimescaleDB hypertable for better performance at scale.

### Tables
- `users` - User accounts with roles
- `drivers` - Fleet drivers with tachograph card info
- `vehicles` - Fleet vehicles with real-time tracking fields
- `gps_positions` - GPS tracking data with PostGIS geometry
- `driver_activities` - Parsed tachograph activities (driving, rest, work)

### Telematics Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  GPS Tracker    │────▶│  POST /position  │────▶│  gps_positions  │
│  (Vehicle)      │     │  (Telematics)    │     │  (PostgreSQL)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  Update Vehicle  │
                        │  last_seen +     │
                        │  current_position│
                        └──────────────────┘
```

### Tachograph Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  .DDD/.TGD File │────▶│  POST /upload    │────▶│  Parse File     │
│  (Upload)       │     │  (Tachograph)    │     │  (Parser)       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                 ┌─────────────────┐
                                                 │ driver_activities│
                                                 │  (PostgreSQL)   │
                                                 └─────────────────┘
```

## 🔮 Future Enhancements

- [ ] Real-time GPS tracking with WebSockets
- [ ] Map visualization for vehicle positions
- [ ] Geofencing alerts
- [ ] Trip history and reports
- [ ] Fuel consumption tracking
- [ ] Maintenance scheduling
- [ ] TimescaleDB integration for time-series optimization
- [x] Tachograph file parsing
- [x] Driver activity tracking
- [x] Real-time vehicle status indicators

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | - |
| REDIS_URL | Redis connection string | - |
| SECRET_KEY | JWT secret key | - |
| ACCESS_TOKEN_EXPIRE_MINUTES | Access token expiry | 30 |
| REFRESH_TOKEN_EXPIRE_DAYS | Refresh token expiry | 7 |

## 📄 License

MIT License
