# GitHub Copilot Instructions

This repository contains slotlist-reboot, an ArmA 3 mission planning and slotlist management system.

Dont write summary markdowns after your work!

## Project Structure

This is a dual-stack application with separate backend and frontend:

- `backend/` - Django 5.2 + Django Ninja REST API
- `frontend/` - Vue.js 2 application with legacy build system

## Key Architecture Principles

### Backend (Django)

- **API Compatibility**: Maintains 100% compatibility with original TypeScript/Hapi.js backend
- **Unmanaged Models**: All Django models use `managed = False` to preserve existing database schema
- **Database Columns**: Use `db_column` attributes to map to camelCase database columns (e.g., `createdAt`, `updatedAt`)
- **Authentication**: JWT tokens with Steam OpenID integration

### Frontend (Vue.js 2)

- **Legacy Stack**: Uses Vue.js 2, Vuex, webpack 2.2.0 from 2017
- **Component Organization**: Features organized in directories (missions/, communities/, users/)
- **State Management**: Vuex modules for each major feature area
- **Styling**: Bootstrap 4 alpha with custom CSS

## Code Style Guidelines

### Backend Python Code

- Follow Django conventions and PEP 8
- Use Django Ninja for API endpoints with Pydantic schemas
- All models must maintain compatibility with existing database schema
- Never modify database schema - models are read-only representations
- Use descriptive function and variable names
- Include docstrings for complex business logic

### Frontend JavaScript/Vue Code

- Follow existing code style (uses XO linter)
- Use Vue.js 2 patterns - no Composition API
- Maintain consistency with existing component structure
- Use Vuex for state management, not direct component state
- Follow existing naming conventions for components and files

## Important Constraints

### Development Environment

- **NEVER** start services (docker-compose, runserver, yarn dev) - assume they are already running locally
- Services run via root `docker-compose.yml` during local development
- Backend runs on port 8022, frontend on port 3000
- Use existing running services for testing and validation

### Database Management

- **NEVER** run Django migrations on production tables
- **NEVER** modify model Meta classes to enable management
- **NEVER** change `db_column` mappings - they match the original schema
- Use raw SQL or external tools for schema changes if absolutely necessary

### API Compatibility

- All API endpoints must maintain compatibility with original backend
- Response formats must match exactly - use existing test suite to verify
- Don't change URL patterns or HTTP methods
- Preserve existing error response formats

### Authentication

- Steam OpenID is the only authentication method
- JWT tokens are required for authenticated endpoints
- Use existing permission system for authorization
- Don't implement alternative authentication methods

## Development Patterns

### Adding New API Endpoints

1. Define Pydantic schemas in `api/schemas.py`
2. Add router function in appropriate `api/routers/` file
3. Register router in `api/api.py`
4. Add comprehensive tests in `api/tests/`
5. Verify compatibility with existing frontend code

### Adding New Frontend Features

1. Create components in appropriate feature directory
2. Add Vuex actions/mutations if state management needed
3. Update router configuration if new routes required
4. Follow existing component patterns and naming
5. Use existing API integration patterns

### Working with Models

- Use Django ORM for queries but respect unmanaged nature
- Join queries across models are safe and encouraged
- Use select_related() and prefetch_related() for performance
- Filter and aggregate operations work normally
- Avoid direct database modifications through Django

## Testing Requirements

### Backend Tests

- Run full compatibility test suite: `./run_compatibility_tests.sh`
- Add tests for new endpoints in appropriate test files
- Maintain API compatibility - tests will fail if responses change
- Use test database for isolated testing

### Frontend Testing

- No automated test suite currently exists
- Manual testing required for UI changes
- Test across different user permission levels
- Verify Steam authentication flow works

## Common Patterns

### Django Model Queries

```python
# Good - using ORM with proper relationships
missions = Mission.objects.select_related('creator', 'community').filter(visibility='public')

# Good - filtering with related models
users = User.objects.filter(community__slug='example-community')
```

### Vue.js Component Structure

```javascript
// Follow existing component pattern
export default {
  name: 'ComponentName',
  props: {
    // Define props with types
  },
  data() {
    return {
      // Component state
    }
  },
  computed: {
    // Computed properties
  },
  methods: {
    // Component methods
  }
}
```

### Vuex Actions

```javascript
// Use existing pattern for API calls
async fetchData({ commit }, payload) {
  try {
    const response = await api.getData(payload)
    commit('SET_DATA', response.data)
    return response.data
  } catch (error) {
    // Handle errors consistently
    throw error
  }
}
```

## Environment Setup

### Backend

- Python 3.9+ required
- PostgreSQL database required (no SQLite support)
- Steam API key required for authentication
- Use virtual environment for dependencies

### Frontend

- Node.js 8.1+ (legacy requirement)
- Yarn package manager
- Webpack 2.x build system
- Environment variables injected at build time

## Debugging Tips

### Backend Issues

- Use Django admin at `/admin/` for data inspection
- API docs available at `/api/docs` for endpoint testing
- Check Steam API connectivity for auth issues
- Verify database connection and permissions

### Frontend Issues

- Vue DevTools extension highly recommended
- Check browser console for JavaScript errors
- Verify API endpoint responses in Network tab
- Test with different user permission levels

## Security Considerations

- Never log or expose JWT secrets
- Steam API keys must be kept secure
- Validate all user inputs through Pydantic schemas
- Use Django's built-in CSRF protection
- Sanitize user-generated content in frontend

## Legacy Compatibility

This project maintains compatibility with the original slotlist.online implementation:

- Database schema cannot be changed
- API responses must match original format
- Frontend must work with existing user expectations
- Both TypeScript and Django backends can operate on same database

## Build and Deployment Commands

### Backend Build

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run Django checks
python manage.py check

# Collect static files (if needed)
python manage.py collectstatic --noinput
```

### Frontend Build

```bash
# Install dependencies
cd frontend
yarn install

# Development build with hot reload
yarn dev:local        # Connects to localhost:8000 backend
yarn dev              # Connects to configured backend URL

# Production build
yarn build            # Creates optimized build in build/ directory
```

### Docker Deployment

```bash
# Start all services
docker-compose up --build

# Backend only
docker-compose up db backend

# Frontend development
docker-compose up db backend frontend-dev

# Frontend production
docker-compose --profile production up frontend
```

## Common Development Commands

### Backend Commands

**Linting and Code Quality**:

```bash
cd backend
# Django has no specific linter configured - follow PEP 8 and Django conventions
python -m py_compile <file>  # Check syntax
```

**Testing**:

```bash
cd backend
# Run full compatibility test suite
./run_compatibility_tests.sh

# Run specific test module
python manage.py test api.tests.test_auth

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

**Database**:

```bash
cd backend
# Create Django admin superuser
python manage.py createsuperuser

# Access Django shell
python manage.py shell

# Access database shell
python manage.py dbshell
```

### Frontend Commands

**Linting**:

```bash
cd frontend
# Run XO linter (ESLint wrapper)
yarn lint

# Auto-fix linting issues (when possible)
yarn lint --fix
```

**Development**:

```bash
cd frontend
# Start development server with hot reload
yarn dev:local       # For local backend at localhost:8000

# Build for production
yarn build

# Test production build locally
# (serve the build/ directory with any static server)
```

## File Organization

### Backend Structure

```
backend/
├── api/                    # API implementation
│   ├── routers/           # API endpoint routers
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── tests/             # API tests
│   └── api.py             # Main API configuration
├── slotlist_backend/      # Django project settings
│   ├── models/            # Django models (unmanaged)
│   └── settings.py        # Django configuration
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

### Frontend Structure

```
frontend/
├── src/
│   ├── components/        # Shared Vue components
│   ├── missions/          # Mission feature components
│   ├── communities/       # Community feature components
│   ├── users/             # User feature components
│   ├── store/             # Vuex store modules
│   ├── router/            # Vue Router configuration
│   └── api/               # API client functions
├── build/                 # Webpack configuration
└── package.json           # Node dependencies and scripts
```
