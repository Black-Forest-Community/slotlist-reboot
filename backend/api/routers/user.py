from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List
from uuid import UUID
from api.models import User, Permission
from api.schemas import UserUpdateSchema, PermissionSchema
from api.auth import has_permission, RequiresCommunityMembership

router = Router()


@router.get('/', auth=RequiresCommunityMembership())
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
        'users': [
            {
                'uid': str(user.uid),
                'nickname': user.nickname,
                'steamId': user.steam_id,
                'community': {
                    'uid': str(user.community.uid),
                    'name': user.community.name,
                    'tag': user.community.tag,
                    'slug': user.community.slug,
                    'website': user.community.website,
                    'logoUrl': user.community.logo_url,
                    'gameServers': user.community.game_servers,
                    'voiceComms': user.community.voice_comms,
                    'repositories': user.community.repositories
                } if user.community else None,
                'active': user.active
            }
            for user in users
        ],
        'limit': limit,
        'offset': offset,
        'count': count,
        'total': total,
        'moreAvailable': (offset + limit) < total
    }


@router.get('/{user_uid}', auth=RequiresCommunityMembership())
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
    missions = Mission.objects.filter(creator=user).select_related('community').order_by('-created_at')[:10]
    
    # Get user's permissions
    user_permissions = Permission.objects.filter(user=user)
    
    return {
        'user': {
            'uid': str(user.uid),
            'nickname': user.nickname,
            'steamId': user.steam_id if include_admin_details else None,
            'community': {
                'uid': str(user.community.uid),
                'name': user.community.name,
                'tag': user.community.tag,
                'slug': user.community.slug,
                'website': user.community.website,
                'logoUrl': user.community.logo_url,
                'gameServers': user.community.game_servers,
                'voiceComms': user.community.voice_comms,
                'repositories': user.community.repositories
            } if user.community else None,
            'active': user.active if include_admin_details else None,
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


@router.patch('/{user_uid}')
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
    
    return {
        'user': {
            'uid': str(user.uid),
            'nickname': user.nickname,
            'steamId': None,
            'community': {
                'uid': str(user.community.uid),
                'name': user.community.name,
                'tag': user.community.tag,
                'slug': user.community.slug,
                'website': user.community.website,
                'logoUrl': user.community.logo_url,
                'gameServers': user.community.game_servers,
                'voiceComms': user.community.voice_comms,
                'repositories': user.community.repositories
            } if user.community else None,
            'active': None
        }
    }


@router.get('/{user_uid}/missions')
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
    missions = queryset.order_by('-created_at')[offset:offset + limit]
    
    return {
        'missions': [
            {
                'uid': str(mission.uid),
                'slug': mission.slug,
                'title': mission.title,
                'briefingTime': mission.briefing_time.isoformat() if mission.briefing_time else None,
                'slottingTime': mission.slotting_time.isoformat() if mission.slotting_time else None,
                'startTime': mission.start_time.isoformat() if mission.start_time else None,
                'endTime': mission.end_time.isoformat() if mission.end_time else None,
                'visibility': mission.visibility,
                'creator': {
                    'uid': str(mission.creator.uid),
                    'nickname': mission.creator.nickname
                } if mission.creator else None,
                'community': {
                    'uid': str(mission.community.uid),
                    'name': mission.community.name,
                    'tag': mission.community.tag,
                    'slug': mission.community.slug
                } if mission.community else None
            }
            for mission in missions
        ],
        'limit': limit,
        'offset': offset,
        'count': len(missions),
        'total': total,
        'moreAvailable': (offset + limit) < total
    }


@router.get('/{user_uid}/permissions', response=List[PermissionSchema])
def list_user_permissions(request, user_uid: UUID):
    """List permissions for a user"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.permission'):
        return 403, {'detail': 'Forbidden'}
    
    user_permissions = Permission.objects.filter(user__uid=user_uid)
    return [
        {'uid': perm.uid, 'permission': perm.permission}
        for perm in user_permissions
    ]


@router.post('/{user_uid}/permissions', response=PermissionSchema)
def create_user_permission(request, user_uid: UUID, permission: str):
    """Add a permission to a user"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.permission'):
        return 403, {'detail': 'Forbidden'}
    
    user = get_object_or_404(User, uid=user_uid)
    perm, created = Permission.objects.get_or_create(user=user, permission=permission)
    
    return {'uid': perm.uid, 'permission': perm.permission}


@router.delete('/{user_uid}/permissions/{permission_uid}')
def delete_user_permission(request, user_uid: UUID, permission_uid: UUID):
    """Remove a permission from a user"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.permission'):
        return 403, {'detail': 'Forbidden'}
    
    permission = get_object_or_404(Permission, uid=permission_uid, user__uid=user_uid)
    permission.delete()
    
    return {'success': True}
