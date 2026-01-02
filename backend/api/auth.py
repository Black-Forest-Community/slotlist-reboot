import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
from django.http import HttpRequest
from ninja.security import HttpBearer
from typing import Optional, Dict, Any, Tuple
from api.models import User, Permission


def generate_jwt(user: User) -> str:
    """Generate a JWT token for a user"""
    permissions = list(Permission.objects.filter(user=user).values_list('permission', flat=True))
    
    # Note: We don't include mission.{slug}.creator permissions in the JWT.
    # Creator status is checked directly by comparing mission.creator.uid with user.uid
    # in the view functions. This prevents JWT bloat for users with many missions.
    
    payload = {
        'user': {
            'uid': str(user.uid),
            'nickname': user.nickname,
            'steam_id': user.steam_id,
            'community': {
                'uid': str(user.community.uid),
                'name': user.community.name,
                'tag': user.community.tag,
                'slug': user.community.slug
            } if user.community else None,
            'active': user.active
        },
        'permissions': permissions,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRES_IN),
        'iss': settings.JWT_ISSUER,
        'aud': settings.JWT_AUDIENCE,
        'sub': str(user.uid)
    }
    
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


def get_or_create_user_from_django_user(django_user: DjangoUser) -> User:
    """Get or create a User record from a Django User"""
    # Generate a fake Steam ID based on the Django user ID
    fake_steam_id = f"django_{django_user.id:010d}"
    
    user, created = User.objects.get_or_create(
        steam_id=fake_steam_id,
        defaults={
            'nickname': django_user.username,
            'active': django_user.is_active
        }
    )
    
    # Update nickname if it changed
    if not created and user.nickname != django_user.username:
        user.nickname = django_user.username
        user.active = django_user.is_active
        user.save()
    
    return user


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def parse_permissions(permissions: list) -> dict:
    """
    Parse a list of permissions into a nested dictionary/tree structure.
    Matches the legacy parsePermissions function.
    
    Example: ['admin.user', 'community.test.leader'] becomes:
    {
        'admin': {'user': {}},
        'community': {'test': {'leader': {}}}
    }
    """
    parsed = {}
    for perm in permissions:
        parts = perm.lower().split('.')
        current = parsed
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]
    return parsed


def find_permission(permission_tree: dict, target_permission: str or list) -> bool:
    """
    Recursively check for permission in permission tree.
    Matches the legacy findPermission function with wildcard support.
    
    Args:
        permission_tree: Parsed permission tree
        target_permission: Permission to check for (string or list of parts)
    
    Returns:
        bool: Whether the permission was found
    """
    if not permission_tree or not isinstance(permission_tree, dict) or len(permission_tree) == 0:
        return False
    
    # Convert string to list of parts
    if isinstance(target_permission, str):
        target_permission = target_permission.lower().split('.')
    
    # If we've consumed all parts, permission is found
    if len(target_permission) == 0:
        return True
    
    # Get the next part to check
    perm_part = target_permission[0]
    remaining_parts = target_permission[1:]
    
    # Check each key in the current tree level
    for current_key, next_tree in permission_tree.items():
        # Wildcard matches everything
        if current_key == '*':
            return True
        
        # Exact match or continue down the tree
        if current_key == perm_part:
            if len(remaining_parts) == 0:
                return True
            return find_permission(next_tree, remaining_parts)
    
    return False


def has_permission(permissions: list, target_permissions: str or list) -> bool:
    """
    Check if a permission list contains the required permission(s).
    Matches the legacy hasPermission function with full wildcard and admin.superadmin support.

    Args:
        permissions: List of permission strings the user has
        target_permissions: Permission(s) to check for (string or list of strings)

    Returns:
        bool: Whether the user has at least one of the target permissions
    """
    if not permissions:
        return False

    # Parse permissions into tree structure
    parsed_permissions = parse_permissions(permissions)

    # Check for global admin permissions
    if '*' in parsed_permissions or find_permission(parsed_permissions, 'admin.superadmin'):
        return True

    # Check target permissions
    if isinstance(target_permissions, list):
        # Check if user has ANY of the target permissions
        return any(find_permission(parsed_permissions, target_perm) for target_perm in target_permissions)
    else:
        # Check single permission
        return find_permission(parsed_permissions, target_permissions)


def has_approved_community(user_uid: str) -> Tuple[bool, Optional[str]]:
    """
    Check if user has an approved community membership.

    Args:
        user_uid: The user's UID as a string

    Returns:
        tuple: (has_community, status_message)
        - has_community: bool indicating if user has approved community
        - status_message: None if has community, otherwise reason for blocking
    """
    from api.models import CommunityApplication

    try:
        user = User.objects.select_related('community').get(uid=user_uid)
    except User.DoesNotExist:
        return False, 'User not found'

    # Check if user has a community assigned
    if user.community is not None:
        return True, None

    # Check if user has pending application
    pending_app = CommunityApplication.objects.filter(
        user=user,
        status='submitted'
    ).exists()

    if pending_app:
        return False, 'You have a pending community application. Please wait for approval.'

    # No community and no pending application
    return False, 'You must be a member of a community to access this content. Please apply to a community first.'


class JWTAuth(HttpBearer):
    """
    JWT authentication for Django Ninja.
    Verifies JWT token and attaches decoded payload to request.auth.
    """

    def authenticate(self, request: HttpRequest, token: str) -> Optional[dict]:
        """
        Authenticate the request using JWT token.

        Args:
            request: The HTTP request
            token: The JWT token from Authorization header

        Returns:
            Decoded JWT payload if valid, None otherwise
        """
        payload = decode_jwt(token)
        return payload


class RequiresCommunityMembership(HttpBearer):
    """
    Authentication that requires both JWT and approved community membership.
    """

    def authenticate(self, request: HttpRequest, token: str) -> Optional[dict]:
        """
        Authenticate the request and verify community membership.

        Args:
            request: The HTTP request
            token: The JWT token from Authorization header

        Returns:
            Decoded JWT payload if valid and user has community, None otherwise
        """
        # First verify JWT
        payload = decode_jwt(token)
        if not payload:
            return None

        # Then check community membership
        user_uid = payload.get('user', {}).get('uid')
        if not user_uid:
            return None

        has_community, error_msg = has_approved_community(user_uid)
        if not has_community:
            # Store error for retrieval in endpoint if needed
            request.community_membership_error = error_msg
            return None

        return payload
