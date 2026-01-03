# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Slotlist-reboot is an ArmA 3 mission planning and slotlist management system with a dual-architecture setup:

- **Backend**: Django 5.2 + Django Ninja API (rewrite of original Hapi.js/TypeScript backend)
- **Frontend**: Vue.js 2 + Vuex + Bootstrap (legacy stack from 2017)
- **Database**: PostgreSQL with unmanaged Django models for schema compatibility

**Key Feature**: The Django backend maintains 100% API compatibility with the original TypeScript backend and uses the same database schema.

## Development Commands

### Backend (Django)
```bash
cd backend

# Setup (first time)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Development
python manage.py runserver                           # Start dev server (port 8000)
python manage.py check                              # Validate configuration
python manage.py createsuperuser                    # Create admin user

# Testing
./run_compatibility_tests.sh                        # Run all API compatibility tests
python manage.py test                               # Run all tests
python manage.py test api.tests.test_auth_api       # Run specific test module
coverage run --source='api' manage.py test api.tests && coverage report  # Test with coverage

# Database
python manage.py dbshell                            # Access PostgreSQL shell
python manage.py shell                              # Django shell

# Production
gunicorn slotlist_backend.wsgi:application          # Production WSGI server
```

### Frontend (Vue.js)
```bash
cd frontend

# Setup (first time)
yarn install

# Development  
yarn dev                                             # Start dev server with hot reload
yarn build                                          # Build for production
yarn lint                                           # Run ESLint (xo)

# Docker
docker build -t slotlist-frontend .
docker run -p 4000:4000 slotlist-frontend
```

### Docker Compose (Full Stack)
```bash
cd backend
docker-compose up                                    # Start PostgreSQL + Django backend
docker-compose down                                 # Stop services
```

## Architecture

### Backend Architecture
- **Framework**: Django 5.2 with Django Ninja for REST API
- **Models** (`api/models.py`): Unmanaged Django models matching original database schema
- **Routers** (`api/routers/`): API endpoints organized by resource (auth, user, mission, community, notification)
- **Schemas** (`api/schemas.py`): Pydantic models for request/response validation
- **Auth** (`api/auth.py`): JWT + Steam OpenID authentication
- **Main API** (`api/api.py`): Django Ninja configuration with route registration

**Critical**: All models use `managed = False` and `db_column` mappings to preserve compatibility with the original TypeScript/Sequelize database schema. Never enable Django migrations for these models.

### Frontend Architecture
- **Framework**: Vue.js 2 with legacy build system (webpack 2.2.0)
- **State Management**: Vuex with modules (auth, communities, missions, users, notifications)
- **Routing**: Vue Router with history mode
- **Components**: Organized by feature (missions/, communities/, users/, etc.)
- **Styling**: Bootstrap 4 alpha + custom CSS
- **Build**: Custom webpack configuration in `build/` directory

### Database Models
Core entities and relationships:
- **User**: Steam-authenticated users with permissions
- **Community**: Organizations/clans with members
- **Mission**: Events with datetime, visibility, and slot management
- **MissionSlotGroup**: Organized groups of slots within missions
- **MissionSlot**: Individual assignable positions with DLC requirements
- **Permission**: Hierarchical permission system for communities and missions
- **Notification**: User notification system

### Authentication Flow
1. Frontend initiates Steam OpenID via `GET /api/v1/auth/steam`
2. User authenticates with Steam
3. Steam redirects to frontend with OpenID response
4. Frontend sends OpenID data to `POST /api/v1/auth/steam`
5. Backend validates with Steam API and issues JWT token
6. JWT token used for authenticated API requests

## Configuration

### Backend Environment Variables (.env)
```bash
# Required
DJANGO_SECRET_KEY=your-secret-key
CONFIG_JWT_SECRET=your-jwt-secret
CONFIG_STEAM_API_SECRET=your-steam-api-key
DB_DATABASE=slotlist
DB_USERNAME=postgres
DB_PASSWORD=your-password

# Optional
DEBUG=True
ALLOWED_HOSTS=*
DB_HOST=localhost
DB_PORT=5432
```

### Frontend Build Configuration
- **Development**: `build/webpack.dev.js` - Uses hardcoded API URLs for slotlist.online
- **Production**: `build/webpack.prod.js` - Production build configuration
- **Environment**: Variables injected via webpack DefinePlugin as `process.env`

## Testing Strategy

### Backend Tests
- **API Compatibility Tests**: Verify Django API matches original TypeScript API behavior
- **Test Categories**: Authentication (13 tests), Users (14 tests), Communities (18 tests), Status (1 test)
- **Coverage**: Run `coverage run --source='api' manage.py test api.tests && coverage report`

### Frontend Tests
No test suite currently configured. The frontend uses an older stack without modern testing setup.

## Key Development Notes

### Backend Development
- Models are unmanaged - never run Django migrations on production tables
- Use Django admin at `/admin/` for data management
- API documentation available at `/api/docs` (Swagger UI)
- Steam API key required for authentication to work
- All API endpoints maintain compatibility with original backend

### Frontend Development
- Legacy Vue.js 2 stack with older dependencies
- Hot module reloading available via `yarn dev`
- Build process generates static files for nginx serving
- Internationalization support via vue-i18n (German/English)
- Vuex store modules organized by feature area

### Database Considerations
- PostgreSQL required (no SQLite support due to JSON fields)
- Schema managed externally - Django models are read-only representations
- Existing production databases can be used without migration
- Both TypeScript and Django backends can operate on same database

## Project Status
The original slotlist site was scheduled for shutdown on December 31, 2025. This reboot represents a modernization effort with the Django backend providing a more maintainable foundation while preserving full compatibility.