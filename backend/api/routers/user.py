from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List
from uuid import UUID
from api.models import User, Permission
from api.schemas import (
    UserUpdateSchema, PermissionSchema,
    UserListResponseSchema, UserDetailResponseSchema,
    UserMissionsResponseSchema
)
from api.auth import has_permission

router = Router()


@router.get('/', response=UserListResponseSchema)
def list_users(request, limit: int = 25, offset: int = 0, search: str = None):
    """List all users with pagination"""
    queryset = User.objects.select_related('community').all()
    
    # Apply search filter if provided
    if search:
        queryset = queryset.filter(nickname__icontains=search)
    
    total = queryset.count()
    users = list(queryset[offset:offset + limit])
    count = len(users)
    
    return {
        'users': users,
        'limit': limit,
        'offset': offset,
        'count': count,
        'total': total,
        'more_available': (offset + limit) < total
    }


@router.get('/{user_uid}', response=UserDetailResponseSchema)
def get_user(request, user_uid: UUID):
    """Get a single user by UID"""
    from api.models import Mission
    
    user = get_object_or_404(User.objects.select_related('community'), uid=user_uid)
    
    # Check if requesting user has admin permissions
    include_admin_details = False
    if request.auth:
        permissions = request.auth.get('permissions', [])
        include_admin_details = has_permission(permissions, 'admin.user')
    
    # Get user's missions
    missions = list(Mission.objects.filter(creator=user).select_related('creator', 'community').order_by('-created_at')[:10])
    
    # Get user's permissions
    user_permissions = list(Permission.objects.filter(user=user))
    
    return {
        'user': {
            'uid': user.uid,
            'nickname': user.nickname,
            'steam_id': user.steam_id if include_admin_details else None,
            'community': user.community,
            'active': user.active if include_admin_details else None,
            'missions': missions,
            'permissions': user_permissions
        }
    }


@router.patch('/{user_uid}', response=UserDetailResponseSchema)
def update_user(request, user_uid: UUID, payload: UserUpdateSchema):
    """Update a user"""
    user = get_object_or_404(User.objects.select_related('community'), uid=user_uid)
    
    # Check if user can update (must be self or admin)
    auth_user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    if str(user.uid) != auth_user_uid and not has_permission(permissions, 'admin.user'):
        return 403, {'detail': 'Forbidden'}
    
    # Update user fields
    if payload.nickname is not None:
        user.nickname = payload.nickname
    
    user.save()
    
    # Reload user
    user = User.objects.select_related('community').get(uid=user_uid)
    
    return {
        'user': {
            'uid': user.uid,
            'nickname': user.nickname,
            'steam_id': None,
            'community': user.community,
            'active': None,
            'missions': [],
            'permissions': []
        }
    }


@router.get('/{user_uid}/missions', response=UserMissionsResponseSchema)
def list_user_missions(request, user_uid: UUID, limit: int = 10, offset: int = 0, includeEnded: bool = True):
    """List missions created by a user"""
    from api.models import Mission
    from django.utils import timezone
    
    # Verify user exists
    get_object_or_404(User, uid=user_uid)
    
    # Build query
    queryset = Mission.objects.filter(creator__uid=user_uid).select_related('creator', 'community')
    
    # Filter by end time if needed
    if not includeEnded:
        queryset = queryset.filter(end_time__gte=timezone.now())
    
    # Get total count
    total = queryset.count()
    
    # Apply pagination
    missions = list(queryset.order_by('-created_at')[offset:offset + limit])
    count = len(missions)
    
    return {
        'missions': missions,
        'limit': limit,
        'offset': offset,
        'count': count,
        'total': total,
        'more_available': (offset + limit) < total
    }


@router.get('/{user_uid}/permissions', response=List[PermissionSchema])
def list_user_permissions(request, user_uid: UUID):
    """List permissions for a user"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.permission'):
        return 403, {'detail': 'Forbidden'}
    
    user_permissions = list(Permission.objects.filter(user__uid=user_uid))
    return user_permissions


@router.post('/{user_uid}/permissions', response=PermissionSchema)
def create_user_permission(request, user_uid: UUID, permission: str):
    """Add a permission to a user"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.permission'):
        return 403, {'detail': 'Forbidden'}
    
    user = get_object_or_404(User, uid=user_uid)
    perm, created = Permission.objects.get_or_create(user=user, permission=permission)
    
    return perm


@router.delete('/{user_uid}/permissions/{permission_uid}')
def delete_user_permission(request, user_uid: UUID, permission_uid: UUID):
    """Remove a permission from a user"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.permission'):
        return 403, {'detail': 'Forbidden'}
    
    permission = get_object_or_404(Permission, uid=permission_uid, user__uid=user_uid)
    permission.delete()
    
    return {'success': True}
