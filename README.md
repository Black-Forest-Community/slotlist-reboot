# Slotlist Reboot

An ArmA 3 mission planning and slotlist management system with Django backend and Vue.js frontend.

## Quick Start with Docker Compose

### Prerequisites
- Docker and Docker Compose
- Steam API Key ([Get one here](https://steamcommunity.com/dev/apikey))

### Development Setup

**Quick Start (Recommended)**:
```bash
git clone <repository-url>
cd slotlist-reboot
./start.sh
```

The script will:
- Check for Docker/Docker Compose
- Create a development `.env` file automatically
- Start all services with proper configuration

**Manual Setup**:

1. **Clone and configure**:
```bash
git clone <repository-url>
cd slotlist-reboot
```

2. **Set up environment variables** (optional - auto-created by start.sh):
Create a `.env` file in the `backend/` directory:
```bash
# Steam API key (optional for development - use dev login instead)
CONFIG_STEAM_API_SECRET=your-steam-api-key-here

# Development defaults (auto-configured)
DEBUG=True
DJANGO_SECRET_KEY=development-django-secret-change-in-production
CONFIG_JWT_SECRET=development-secret-key-change-in-production
```

3. **Start all services**:
```bash
docker-compose up --build
```

This will start:
- **PostgreSQL** database on port 5432
- **Django API** backend on port 8000
- **Vue.js frontend** (development) on port 3000

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **API Documentation**: http://localhost:8000/api/docs
- **Django Admin**: http://localhost:8000/admin/

### Production Build

For production frontend build:
```bash
docker-compose --profile production up frontend
```
This serves the production build on port 4000.

## Development Services

### Individual Service Commands

**Backend only**:
```bash
docker-compose up db backend
```

**Frontend only** (requires backend):
```bash
docker-compose up db backend frontend-dev
```

**Database only**:
```bash
docker-compose up db
```

### Local Development (without Docker)

**Backend**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

**Frontend**:
```bash
cd frontend
yarn install
yarn dev:local  # Connects to localhost:8000 backend
```

## Architecture

### Backend (Django + Django Ninja)
- **API Framework**: Django 5.2 with Django Ninja for REST API
- **Database**: PostgreSQL with unmanaged models for schema compatibility
- **Authentication**: JWT tokens with Steam OpenID
- **API Docs**: Automatic OpenAPI/Swagger documentation

### Frontend (Vue.js 2)
- **Framework**: Vue.js 2 with Vuex state management
- **Build System**: Webpack 2 (legacy configuration)
- **Development**: Hot module reloading
- **Production**: Nginx-served static files

## Configuration

### Environment Variables

**Backend** (set in `backend/.env`):
- `CONFIG_STEAM_API_SECRET` - **Required** Steam API key
- `DJANGO_SECRET_KEY` - Django secret key
- `CONFIG_JWT_SECRET` - JWT signing secret
- `DB_*` - Database connection settings
- `DEBUG` - Enable Django debug mode

**Frontend** (set at build time):
- `BACKEND_URL` - Backend API URL (auto-configured in Docker)

### Database Schema

The Django models are configured as **unmanaged** (`managed = False`) to maintain compatibility with the original TypeScript backend database schema. This means:

- ✅ Can use existing databases without migration
- ✅ Both TypeScript and Django backends work with same DB
- ❌ Cannot use Django migrations to modify schema
- ❌ Must manage schema changes externally

## Authentication

### Steam Authentication (Production)

To enable user authentication:

1. Get a Steam API key: https://steamcommunity.com/dev/apikey
2. Set `CONFIG_STEAM_API_SECRET` in your environment
3. Users can log in via Steam OpenID

Without a valid Steam API key, authentication will not work.

### Development Authentication (Testing)

For local development and testing, you can bypass Steam authentication using the backend development endpoint.

#### Backend Development Endpoint

The backend provides a development-only login endpoint:
- **Endpoint**: `POST /api/v1/auth/dev-login`
- **Only available when**: `DEBUG=True`
- **Request body**:
  ```json
  {
    "nickname": "TestUser",
    "steam_id": "76561198000000000"  // optional, auto-generated if omitted
  }
  ```

**How to use**:
You can test authentication by making HTTP requests to the endpoint using tools like curl, Postman, or the API documentation interface:

```bash
# Example using curl
curl -X POST http://localhost:8000/api/v1/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"nickname": "TestUser"}'
```

**Features**:
- Creates user accounts automatically if they don't exist
- Generates fake Steam IDs if not provided
- Works without Steam API key
- Only available in development mode (`DEBUG=True`)
- Returns a JWT token that can be used for authenticated requests

## Testing

**Backend API Tests**:
```bash
# In backend directory
./run_compatibility_tests.sh

# Or with Docker
docker-compose exec backend python manage.py test
```

**API Coverage**:
- Authentication: 13 tests (100%)
- Users: 14 tests (92%)
- Communities: 18 tests (47%)
- Status: 1 test (100%)

## Troubleshooting

### Common Issues

**Backend won't start**:
- Check PostgreSQL is running and accessible
- Verify Steam API key is set correctly (or use development auth)
- Check logs: `docker-compose logs backend`

**Frontend can't connect to backend**:
- Ensure backend is running on port 8000
- Check CORS settings in backend
- Verify API URL configuration

**Database connection errors**:
- Ensure PostgreSQL container is healthy
- Check database credentials in environment variables
- Wait for database to fully initialize (health check)

**Can't log in / Steam authentication issues**:
- Use development authentication endpoint: `POST /api/v1/auth/dev-login` with a test nickname
- Or set Steam API key in `backend/.env`
- See the "Backend Development Endpoint" section for details on using dev authentication

### Development Tips

**Reset database**:
```bash
docker-compose down -v  # Removes volumes
docker-compose up
```

**View logs**:
```bash
docker-compose logs -f backend    # Backend logs
docker-compose logs -f frontend-dev  # Frontend logs
docker-compose logs -f db         # Database logs
```

**Shell access**:
```bash
docker-compose exec backend python manage.py shell  # Django shell
docker-compose exec backend bash                    # Backend container
docker-compose exec db psql -U postgres slotlist    # Database shell
```

## License

MIT