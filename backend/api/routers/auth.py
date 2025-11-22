from ninja import Router
from ninja.security import HttpBearer
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpRequest
from typing import Optional
from api.models import User
from api.schemas import AuthResponseSchema, ErrorResponseSchema
from api.auth import generate_jwt, get_or_create_user_from_django_user, decode_jwt
from api.steam_auth import steam_service
from pydantic import BaseModel


class JWTAuth(HttpBearer):
    """JWT Authentication for Django Ninja that supports both JWT and Bearer prefixes"""
    
    openapi_scheme: str = "bearer"
    
    def __call__(self, request: HttpRequest) -> Optional[dict]:
        """
        Override __call__ to handle JWT prefix in addition to Bearer.
        This is called before authenticate() to extract the token from headers.
        """
        auth_header = request.headers.get('Authorization', '')
        
        # Handle JWT prefix (legacy format)
        if auth_header.startswith('JWT '):
            token = auth_header[4:].strip()
            return self.authenticate(request, token)
        
        # Handle Bearer prefix (standard format)
        elif auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
            return self.authenticate(request, token)
        
        return None
    
    def authenticate(self, request: HttpRequest, token: str) -> Optional[dict]:
        """
        Authenticate the request using JWT token.
        """
        # Decode and verify the token
        payload = decode_jwt(token)
        if payload:
            return payload
        
        print(f"JWT authentication failed for token: {token[:50]}...")
        return None


router = Router()


class DevLoginSchema(BaseModel):
    nickname: str
    steam_id: str = None


class DjangoLoginSchema(BaseModel):
    username: str
    password: str


class SteamLoginSchema(BaseModel):
    url: str


@router.get('/steam', auth=None)
def get_steam_login_url(request):
    """
    Get Steam OpenID login URL
    
    Returns the URL to redirect the user to for Steam authentication.
    The frontend should redirect the user to this URL to begin the Steam login process.
    
    **Authentication:** None required
    
    **Returns:**
    - `url` (str): Steam OpenID URL to redirect user to for authentication
    
    **Example Response:**
    ```json
    {
        "url": "https://steamcommunity.com/openid/login?openid.ns=..."
    }
    ```
    """
    # Get the return URL from frontend (where Steam should redirect after auth)
    # In production, this should be configured based on your frontend URL
    frontend_url = request.GET.get('return_url', settings.JWT_ISSUER)
    realm = settings.JWT_ISSUER
    
    login_url = steam_service.get_login_url(frontend_url, realm)
    
    return {'url': login_url}


@router.post('/steam', response={200: AuthResponseSchema, 400: ErrorResponseSchema, 403: ErrorResponseSchema}, auth=None)
def verify_steam_login(request, payload: SteamLoginSchema):
    """
    Verify Steam OpenID authentication and return JWT
    
    After Steam redirects the user back to your frontend with OpenID parameters,
    send the full callback URL to this endpoint to verify the authentication and
    receive a JWT token.
    
    **Authentication:** None required
    
    **Request Body:**
    - `url` (str): Full callback URL with OpenID parameters from Steam
    
    **Returns:**
    - `token` (str): JWT token for authenticated user
    - `user` (object): User information
    
    **Example Request:**
    ```json
    {
        "url": "https://yoursite.com/auth/callback?openid.ns=..."
    }
    ```
    
    **Example Response:**
    ```json
    {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {
            "uid": "123e4567-e89b-12d3-a456-426614174000",
            "nickname": "PlayerName",
            "steam_id": "76561198...",
            "active": true
        }
    }
    ```
    
    **Errors:**
    - `400`: Invalid OpenID response
    - `403`: User account is deactivated
    """
    # Extract return URL from the openid response
    return_url = request.GET.get('return_url', settings.JWT_ISSUER)
    
    print(f"Received URL from frontend: {payload.url[:200]}...")
    print(f"Return URL: {return_url}")
    
    # Verify Steam login and get Steam ID
    steam_id = steam_service.verify_and_get_steam_id(payload.url, return_url)
    
    if not steam_id:
        return 400, {'detail': 'Invalid Steam OpenID response'}
    
    # Get or create user
    try:
        user = User.objects.get(steam_id=steam_id)
        print(f"Found existing user: {user.nickname} ({user.uid})")
        
        # Check if user is active
        if not user.active:
            return 403, {'detail': 'User account is deactivated'}
            
    except User.DoesNotExist:
        print(f"Creating new user for Steam ID: {steam_id}")
        # Get user info from Steam API
        steam_info = steam_service.get_steam_user_info(steam_id)
        print(f"Steam info: {steam_info}")
        
        # Create new user
        user = User.objects.create(
            steam_id=steam_id,
            nickname=steam_info['nickname'],
            active=True
        )
        print(f"Created new user: {user.nickname} ({user.uid})")
    
    # Generate JWT
    token = generate_jwt(user)
    
    return {
        'token': token,
        'user': {
            'uid': user.uid,
            'nickname': user.nickname,
            'steam_id': user.steam_id,
            'community': None,
            'active': user.active
        }
    }


@router.post('/dev-login', response=AuthResponseSchema, auth=None)
def dev_login(request, credentials: DevLoginSchema):
    """
    Development-only login endpoint that bypasses Steam authentication
    
    **⚠️ WARNING: Only enabled when DEBUG=True. Never use in production!**
    
    This endpoint allows testing authentication flow without Steam OAuth.
    It creates or logs in a user with the provided credentials.
    
    **Authentication:** None required
    
    **Request Body:**
    - `nickname` (str): User nickname
    - `steam_id` (str, optional): Steam ID (auto-generated if not provided)
    
    **Returns:**
    - `token` (str): JWT token for authenticated user
    - `user` (object): User information
    
    **Example Request:**
    ```json
    {
        "nickname": "TestUser",
        "steam_id": "76561198000000000"
    }
    ```
    
    **Errors:**
    - `403`: Development login disabled (production mode)
    - `400`: Invalid request data
    """
    # Only allow in development mode
    if not settings.DEBUG:
        return 403, {'detail': 'Development login is only available in DEBUG mode'}
    
    # Generate a fake Steam ID if not provided
    steam_id = credentials.steam_id
    if not steam_id:
        # Generate a fake Steam ID starting with 76561198 (common Steam ID prefix)
        import random
        steam_id = f"76561198{random.randint(100000000, 999999999)}"
    
    # Get or create user
    user, created = User.objects.get_or_create(
        steam_id=steam_id,
        defaults={
            'nickname': credentials.nickname,
            'active': True
        }
    )
    
    # Update nickname if user already exists
    if not created and user.nickname != credentials.nickname:
        user.nickname = credentials.nickname
        user.save()
    
    # Check if user is active
    if not user.active:
        return 403, {'detail': 'User account is deactivated'}
    
    # Generate JWT
    token = generate_jwt(user)
    
    return {
        'token': token,
        'user': {
            'uid': user.uid,
            'nickname': user.nickname,
            'steam_id': user.steam_id,
            'community': {
                'uid': str(user.community.uid),
                'name': user.community.name,
                'tag': user.community.tag,
                'slug': user.community.slug
            } if user.community else None,
            'active': user.active
        }
    }


@router.post('/django-login', response=AuthResponseSchema, auth=None)
def django_login(request, credentials: DjangoLoginSchema):
    """
    Django username/password authentication endpoint
    
    **Only available in development mode (DEBUG=True)**
    
    Authenticates against Django's built-in user system and creates
    corresponding User records in the slotlist system.
    
    **Authentication:** None required
    
    **Request Body:**
    - `username` (str): Django username
    - `password` (str): Django password
    
    **Returns:**
    - `token` (str): JWT token for authenticated user
    - `user` (object): User information
    
    **Example Request:**
    ```json
    {
        "username": "admin",
        "password": "password123"
    }
    ```
    
    **Errors:**
    - `403`: Django login disabled (production mode)
    - `401`: Invalid credentials
    - `403`: User account is deactivated
    """
    # Only allow in development mode
    if not settings.DEBUG:
        return 403, {'detail': 'Django login is only available in DEBUG mode'}
    
    # Authenticate against Django users
    django_user = authenticate(
        request=request,
        username=credentials.username,
        password=credentials.password
    )
    
    if not django_user:
        return 401, {'detail': 'Invalid credentials'}
    
    if not django_user.is_active:
        return 403, {'detail': 'User account is deactivated'}
    
    # Get or create corresponding User record
    user = get_or_create_user_from_django_user(django_user)
    
    # Generate JWT
    token = generate_jwt(user)
    
    return {
        'token': token,
        'user': {
            'uid': user.uid,
            'nickname': user.nickname,
            'steam_id': user.steam_id,
            'community': {
                'uid': str(user.community.uid),
                'name': user.community.name,
                'tag': user.community.tag,
                'slug': user.community.slug
            } if user.community else None,
            'active': user.active
        }
    }


@router.post('/refresh', response=AuthResponseSchema, auth=JWTAuth())
def refresh_token(request):
    """
    Refresh JWT token
    
    Generates a new JWT token for the authenticated user with updated permissions
    and user information. Should be called after any user profile changes.
    
    **Authentication:** Required (JWT)
    
    **Returns:**
    - `token` (str): New JWT token
    - `user` (object): Updated user information
    
    **Example Response:**
    ```json
    {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {
            "uid": "123e4567-e89b-12d3-a456-426614174000",
            "nickname": "PlayerName",
            "steam_id": "76561198...",
            "active": true
        }
    }
    ```
    
    **Errors:**
    - `401`: Invalid or expired token
    - `403`: User account is deactivated
    """
    user_data = request.auth.get('user')
    if not user_data:
        return 401, {'detail': 'Invalid token'}
    
    
    user = get_object_or_404(User, uid=user_data['uid'])
    
    if not user.active:
        return 403, {'detail': 'User account is deactivated'}
    
    token = generate_jwt(user)
    
    return {
        'token': token,
        'user': {
            'uid': user.uid,
            'nickname': user.nickname,
            'steam_id': user.steam_id,
            'community': None,
            'active': user.active
        }
    }


@router.get('/account', auth=JWTAuth())
def get_account_details(request):
    """
    Get authenticated user's account details
    
    Returns detailed information about the currently authenticated user including
    their community association, account status, missions, and permissions.
    
    **Authentication:** Required (JWT)
    
    **Returns:**
    - `user` (object): User account details
    
    **Example Response:**
    ```json
    {
        "user": {
            "uid": "123e4567-e89b-12d3-a456-426614174000",
            "nickname": "PlayerName",
            "steamId": "76561198...",
            "community": {
                "uid": "...",
                "name": "Community Name",
                "tag": "[TAG]",
                "slug": "community-slug"
            },
            "active": true,
            "missions": [...],
            "permissions": [...]
        }
    }
    ```
    
    **Errors:**
    - `401`: Invalid or expired token
    - `403`: User account is deactivated
    """
    from api.models import Mission, Permission
    
    user_data = request.auth.get('user')
    if not user_data:
        return 401, {'detail': 'Invalid token'}
    
    user = get_object_or_404(User.objects.select_related('community'), uid=user_data['uid'])
    
    if not user.active:
        return 403, {'detail': 'User account is deactivated'}
    
    # Get user's missions
    missions = Mission.objects.filter(creator=user).select_related('community').order_by('-created_at')[:10]
    
    # Get user's permissions
    user_permissions = Permission.objects.filter(user=user)
    
    return {
        'user': {
            'uid': str(user.uid),
            'nickname': user.nickname,
            'steamId': user.steam_id,
            'community': {
                'uid': str(user.community.uid),
                'name': user.community.name,
                'tag': user.community.tag,
                'slug': user.community.slug,
            } if user.community else None,
            'active': user.active,
            'missions': [
                {
                    'uid': str(mission.uid),
                    'slug': mission.slug,
                    'title': mission.title,
                    'briefingTime': mission.briefing_time.isoformat() if mission.briefing_time else None,
                    'slottingTime': mission.slotting_time.isoformat() if mission.slotting_time else None,
                    'startTime': mission.start_time.isoformat() if mission.start_time else None,
                    'endTime': mission.end_time.isoformat() if mission.end_time else None,
                    'community': {
                        'uid': str(mission.community.uid),
                        'name': mission.community.name,
                        'tag': mission.community.tag,
                        'slug': mission.community.slug
                    } if mission.community else None
                }
                for mission in missions
            ],
            'permissions': [
                {
                    'uid': str(perm.uid),
                    'permission': perm.permission
                }
                for perm in user_permissions
            ]
        }
    }


@router.patch('/account', auth=JWTAuth())
def update_account(request, payload: dict):
    """
    Update authenticated user's account details
    
    Allows users to update their own account information such as nickname.
    
    **Authentication:** Required (JWT)
    
    **Request Body:**
    - `nickname` (str, optional): New nickname for the user
    
    **Returns:**
    - `user` (object): Updated user account details
    
    **Errors:**
    - `401`: Invalid or expired token
    - `403`: User account is deactivated
    """
    user_data = request.auth.get('user')
    if not user_data:
        return 401, {'detail': 'Invalid token'}
    
    user = get_object_or_404(User.objects.select_related('community'), uid=user_data['uid'])
    
    if not user.active:
        return 403, {'detail': 'User account is deactivated'}
    
    # Update nickname if provided
    if 'nickname' in payload:
        user.nickname = payload['nickname']
        user.save()
    
    return {
        'user': {
            'uid': str(user.uid),
            'nickname': user.nickname,
            'steamId': user.steam_id,
            'community': {
                'uid': str(user.community.uid),
                'name': user.community.name,
                'tag': user.community.tag,
                'slug': user.community.slug,
            } if user.community else None,
            'active': user.active
        }
    }


@router.post('/account/delete', auth=JWTAuth())
def delete_account(request, payload: dict):
    """
    Delete authenticated user's account
    
    Requires confirmation by providing the user's nickname. This action is irreversible.
    
    **Authentication:** Required (JWT)
    
    **Request Body:**
    - `nickname` (str): User's nickname for confirmation
    
    **Returns:**
    - `success` (bool): Whether the deletion was successful
    
    **Errors:**
    - `400`: Nickname confirmation doesn't match
    - `401`: Invalid or expired token
    """
    user_data = request.auth.get('user')
    if not user_data:
        return 401, {'detail': 'Invalid token'}
    
    user = get_object_or_404(User, uid=user_data['uid'])
    
    # Verify nickname for confirmation
    if 'nickname' not in payload or payload['nickname'] != user.nickname:
        return 400, {'detail': 'Nickname confirmation does not match'}
    
    # Delete the user
    user.delete()
    
    return {'success': True}


