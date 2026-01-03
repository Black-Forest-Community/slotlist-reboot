from ninja import Router
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from api.models import Community
from api.schemas import CommunityCreateSchema, CommunityUpdateSchema, CommunityApplicationStatusSchema, CommunityPermissionCreateSchema
from api.auth import has_permission, has_approved_community, RequiresCommunityMembership

router = Router()


@router.get('/slugAvailable', auth=None)
def check_slug_availability(request, slug: str):
    """Check if a community slug is available"""
    # Check if a community with this slug already exists
    exists = Community.objects.filter(slug=slug).exists()
    
    return {
        'available': not exists
    }


@router.get('/', auth=None)
def list_communities(request, limit: int = 25, offset: int = 0):
    """List all communities with pagination"""
    total = Community.objects.count()
    communities = Community.objects.all()[offset:offset + limit]
    return {
        'communities': [
            {
                'uid': community.uid,
                'name': community.name,
                'tag': community.tag,
                'slug': community.slug,
                'website': community.website,
                'logoUrl': community.logo_url,
                'gameServers': community.game_servers,
                'voiceComms': community.voice_comms,
                'repositories': community.repositories
            }
            for community in communities
        ],
        'total': total
    }


@router.get('/{slug}', auth=None)
def get_community(request, slug: str):
    """Get a single community by slug"""
    community = get_object_or_404(Community, slug=slug)

    # Check if user is authenticated and has community
    is_authenticated_with_community = False
    if hasattr(request, 'auth') and request.auth:
        user_uid = request.auth.get('user', {}).get('uid')
        if user_uid:
            has_community, _ = has_approved_community(user_uid)
            is_authenticated_with_community = has_community

    # If not authenticated with community, return basic info only
    if not is_authenticated_with_community:
        return {
            'community': {
                'uid': community.uid,
                'name': community.name,
                'tag': community.tag,
                'slug': community.slug,
                'website': community.website,
                'logoUrl': community.logo_url,
                # Don't include members, leaders, or detailed resources
                'members': [],
                'leaders': []
            }
        }

    # Get members and leaders (full data for authenticated users with community)
    from api.models import User, Permission

    members = []
    leaders = []

    # Get all users in this community
    community_users = User.objects.filter(community=community).select_related('community')

    for user in community_users:
        user_data = {
            'uid': user.uid,
            'nickname': user.nickname,
            'steamId': user.steam_id,
        }

        # Check if user is a leader (has community.{slug}.leader permission)
        is_leader = Permission.objects.filter(
            user=user,
            permission=f'community.{slug}.leader'
        ).exists()

        if is_leader:
            leaders.append(user_data)
        else:
            members.append(user_data)

    return {
        'community': {
            'uid': community.uid,
            'name': community.name,
            'tag': community.tag,
            'slug': community.slug,
            'website': community.website,
            'logoUrl': community.logo_url,
            'gameServers': community.game_servers,
            'voiceComms': community.voice_comms,
            'repositories': community.repositories,
            'members': members,
            'leaders': leaders
        }
    }


@router.post('/', response={200: dict, 403: dict})
def create_community(request, payload: CommunityCreateSchema):
    """Create a new community"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.community'):
        return 403, {'detail': 'Forbidden'}
    
    # Generate slug from name
    slug = slugify(payload.name)
    
    community = Community.objects.create(
        name=payload.name,
        tag=payload.tag,
        slug=slug,
        website=payload.website,
        game_servers=payload.game_servers or [],
        voice_comms=payload.voice_comms or [],
        repositories=payload.repositories or []
    )
    
    return {
        'community': {
            'uid': community.uid,
            'name': community.name,
            'tag': community.tag,
            'slug': community.slug,
            'website': community.website,
            'logoUrl': community.logo_url,
            'gameServers': community.game_servers,
            'voiceComms': community.voice_comms,
            'repositories': community.repositories,
            'members': [],
            'leaders': []
        }
    }


@router.patch('/{slug}', response={200: dict, 403: dict})
def update_community(request, slug: str, payload: CommunityUpdateSchema):
    """Update a community"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.community'):
        return 403, {'detail': 'Forbidden'}
    
    community = get_object_or_404(Community, slug=slug)
    
    if payload.name is not None:
        community.name = payload.name
    if payload.tag is not None:
        community.tag = payload.tag
    if payload.website is not None:
        community.website = payload.website
    if payload.game_servers is not None:
        community.game_servers = payload.game_servers
    if payload.voice_comms is not None:
        community.voice_comms = payload.voice_comms
    if payload.repositories is not None:
        community.repositories = payload.repositories
    
    community.save()
    
    # Get members and leaders for updated response
    from api.models import User, Permission
    
    members = []
    leaders = []
    
    community_users = User.objects.filter(community=community).select_related('community')
    
    for user in community_users:
        user_data = {
            'uid': user.uid,
            'nickname': user.nickname,
            'steamId': user.steam_id,
        }
        
        is_leader = Permission.objects.filter(
            user=user,
            permission=f'community.{slug}.leader'
        ).exists()
        
        if is_leader:
            leaders.append(user_data)
        else:
            members.append(user_data)
    
    return {
        'community': {
            'uid': community.uid,
            'name': community.name,
            'tag': community.tag,
            'slug': community.slug,
            'website': community.website,
            'logoUrl': community.logo_url,
            'gameServers': community.game_servers,
            'voiceComms': community.voice_comms,
            'repositories': community.repositories,
            'members': members,
            'leaders': leaders
        }
    }


@router.delete('/{slug}', response={200: dict, 403: dict})
def delete_community(request, slug: str):
    """Delete a community"""
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, 'admin.community'):
        return 403, {'detail': 'Forbidden'}
    
    community = get_object_or_404(Community, slug=slug)
    community.delete()
    
    return {'success': True}


@router.get('/{slug}/missions', auth=RequiresCommunityMembership())
def get_community_missions(request, slug: str, limit: int = 10, offset: int = 0, includeEnded: bool = False):
    """Get missions for a community"""
    from api.models import Mission
    from datetime import datetime
    
    community = get_object_or_404(Community, slug=slug)
    
    # Filter missions by community
    missions_query = Mission.objects.filter(community=community)
    
    # Filter out ended missions unless includeEnded is True
    if not includeEnded:
        missions_query = missions_query.filter(end_time__gt=datetime.now())
    
    total = missions_query.count()
    missions = missions_query.select_related('creator', 'community')[offset:offset + limit]
    
    return {
        'missions': [
            {
                'uid': mission.uid,
                'slug': mission.slug,
                'title': mission.title,
                'briefingTime': mission.briefing_time.isoformat() if mission.briefing_time else None,
                'slottingTime': mission.slotting_time.isoformat() if mission.slotting_time else None,
                'startTime': mission.start_time.isoformat() if mission.start_time else None,
                'endTime': mission.end_time.isoformat() if mission.end_time else None,
                'visibility': mission.visibility,
                'creator': {
                    'uid': mission.creator.uid,
                    'nickname': mission.creator.nickname,
                } if mission.creator else None,
                'community': {
                    'uid': mission.community.uid,
                    'name': mission.community.name,
                    'tag': mission.community.tag,
                    'slug': mission.community.slug,
                } if mission.community else None,
            }
            for mission in missions
        ],
        'total': total
    }


@router.get('/{slug}/permissions', auth=RequiresCommunityMembership())
def get_community_permissions(request, slug: str, limit: int = 10, offset: int = 0):
    """Get permissions for a community"""
    from api.models import Permission, User
    
    community = get_object_or_404(Community, slug=slug)
    
    # Get all permissions for users in this community
    permissions_query = Permission.objects.filter(
        user__community=community
    ).select_related('user')
    
    total = permissions_query.count()
    permissions = permissions_query[offset:offset + limit]
    
    return {
        'permissions': [
            {
                'uid': perm.uid,
                'permission': perm.permission,
                'user': {
                    'uid': perm.user.uid,
                    'nickname': perm.user.nickname,
                }
            }
            for perm in permissions
        ],
        'total': total
    }


@router.get('/{slug}/repositories', auth=RequiresCommunityMembership())
def get_community_repositories(request, slug: str):
    """Get repositories for a community"""
    community = get_object_or_404(Community, slug=slug)
    
    return {
        'repositories': community.repositories or []
    }


@router.get('/{slug}/servers', auth=RequiresCommunityMembership())
def get_community_servers(request, slug: str):
    """Get servers for a community"""
    community = get_object_or_404(Community, slug=slug)
    
    return {
        'gameServers': community.game_servers or [],
        'voiceComms': community.voice_comms or []
    }


@router.get('/{slug}/applications/status', response={200: dict, 404: dict})
def get_community_application_status(request, slug: str):
    """Get the authenticated user's application status for a community"""
    from api.models import CommunityApplication
    
    # User must be authenticated
    if not request.auth:
        return 401, {'detail': 'Authentication required'}
    
    community = get_object_or_404(Community, slug=slug)
    auth_user_uid = request.auth.get('user', {}).get('uid')
    
    if not auth_user_uid:
        return 401, {'detail': 'Invalid authentication'}
    
    # Try to find the user's application for this community
    try:
        application = CommunityApplication.objects.get(
            user__uid=auth_user_uid,
            community=community
        )
        
        return 200, {
            'application': {
                'uid': str(application.uid),
                'status': application.status,
                'createdAt': application.created_at.isoformat() if application.created_at else None,
                'updatedAt': application.updated_at.isoformat() if application.updated_at else None
            }
        }
    except CommunityApplication.DoesNotExist:
        # Return 404 when no application found
        return 404, {'message': 'Community application not found'}


@router.get('/{slug}/applications', response={200: dict, 403: dict})
def get_community_applications(request, slug: str, limit: int = 10, offset: int = 0, includeProcessed: bool = False):
    """Get all applications for a community (requires leader/recruitment permission)"""
    from api.models import CommunityApplication
    
    # Check permissions
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, f'community.{slug}.leader') and \
       not has_permission(permissions, f'community.{slug}.recruitment') and \
       not has_permission(permissions, f'community.{slug}.founder'):
        return 403, {'detail': 'Forbidden'}
    
    community = get_object_or_404(Community, slug=slug)
    
    # Build query
    applications_query = CommunityApplication.objects.filter(community=community)
    
    # Filter by status
    if not includeProcessed:
        applications_query = applications_query.filter(status='submitted')
    
    total = applications_query.count()
    applications = applications_query.select_related('user').order_by('-created_at')[offset:offset + limit]
    
    return {
        'applications': [
            {
                'uid': app.uid,
                'status': app.status,
                'createdAt': app.created_at.isoformat() if app.created_at else None,
                'updatedAt': app.updated_at.isoformat() if app.updated_at else None,
                'user': {
                    'uid': app.user.uid,
                    'nickname': app.user.nickname,
                    'steamId': app.user.steam_id,
                }
            }
            for app in applications
        ],
        'total': total
    }


@router.post('/{slug}/applications', response={200: dict, 400: dict, 401: dict})
def create_community_application(request, slug: str):
    """Submit an application to join a community"""
    from api.models import CommunityApplication, User

    # User must be authenticated
    if not request.auth:
        return 401, {'detail': 'Authentication required'}

    community = get_object_or_404(Community, slug=slug)
    auth_user_uid = request.auth.get('user', {}).get('uid')

    if not auth_user_uid:
        return 401, {'detail': 'Invalid authentication'}

    # Get the user
    user = get_object_or_404(User, uid=auth_user_uid)

    # Check if user already has an application for this community
    existing_app = CommunityApplication.objects.filter(
        user=user,
        community=community
    ).first()

    if existing_app:
        return 400, {'message': 'You have already submitted an application to this community'}

    # Create the application
    application = CommunityApplication.objects.create(
        user=user,
        community=community,
        status='submitted'
    )

    return 200, {
        'status': application.status,
        'uid': str(application.uid)
    }


@router.patch('/{slug}/applications/{application_uid}', response={200: dict, 403: dict, 400: dict})
def process_community_application(request, slug: str, application_uid: str, payload: CommunityApplicationStatusSchema):
    """Process (accept/deny) a community application"""
    from api.models import CommunityApplication, User
    
    # Check permissions
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, f'community.{slug}.leader') and \
       not has_permission(permissions, f'community.{slug}.recruitment') and \
       not has_permission(permissions, f'community.{slug}.founder'):
        return 403, {'detail': 'Forbidden'}
    
    community = get_object_or_404(Community, slug=slug)
    
    # Get the application
    application = get_object_or_404(CommunityApplication, uid=application_uid, community=community)
    
    # Get status from payload and map 'accepted' to 'approved' for backwards compatibility
    requested_status = payload.status
    if requested_status not in ['accepted', 'denied']:
        return 400, {'detail': 'status must be "accepted" or "denied"'}

    # Map 'accepted' to 'approved' to match model STATUS_CHOICES
    new_status = 'approved' if requested_status == 'accepted' else 'denied'

    # Update application status (model's save() method will handle community assignment)
    application.status = new_status
    application.save()
    
    return {
        'application': {
            'uid': application.uid,
            'status': application.status,
            'createdAt': application.created_at.isoformat() if application.created_at else None,
            'updatedAt': application.updated_at.isoformat() if application.updated_at else None,
            'user': {
                'uid': application.user.uid,
                'nickname': application.user.nickname,
                'steamId': application.user.steam_id,
            }
        }
    }


@router.delete('/{slug}/members/{member_uid}', response={200: dict, 403: dict})
def remove_community_member(request, slug: str, member_uid: str):
    """Remove a member from a community"""
    from api.models import User
    
    # Check permissions
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, f'community.{slug}.leader') and \
       not has_permission(permissions, f'community.{slug}.recruitment') and \
       not has_permission(permissions, f'community.{slug}.founder'):
        return 403, {'detail': 'Forbidden'}
    
    community = get_object_or_404(Community, slug=slug)
    
    # Get the user
    user = get_object_or_404(User, uid=member_uid)
    
    # Check if user is actually in this community
    if user.community != community:
        return 400, {'detail': 'User is not a member of this community'}
    
    # Remove user from community
    user.community = None
    user.save()
    
    return {'success': True}


@router.post('/{slug}/permissions', response={200: dict, 403: dict, 400: dict})
def create_community_permission(request, slug: str, payload: CommunityPermissionCreateSchema):
    """Create a permission for a community member"""
    from api.models import Permission, User
    
    # Check permissions
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, f'community.{slug}.leader') and not has_permission(permissions, 'admin.community'):
        return 403, {'detail': 'Forbidden'}
    
    community = get_object_or_404(Community, slug=slug)
    
    # Get required fields from payload
    user_uid = payload.userUid
    permission_str = payload.permission
    
    # Get the user
    user = get_object_or_404(User, uid=user_uid)
    
    # Check if permission already exists
    existing_permission = Permission.objects.filter(
        user=user,
        permission=permission_str
    ).first()
    
    if existing_permission:
        return 400, {'detail': 'Permission already exists'}
    
    # Create the permission
    permission = Permission.objects.create(
        user=user,
        permission=permission_str
    )
    
    return {
        'permission': {
            'uid': permission.uid,
            'permission': permission.permission,
            'user': {
                'uid': user.uid,
                'nickname': user.nickname,
            }
        }
    }


@router.delete('/{slug}/permissions/{permission_uid}', response={200: dict, 403: dict})
def delete_community_permission(request, slug: str, permission_uid: str):
    """Delete a permission for a community member"""
    from api.models import Permission
    
    # Check permissions
    permissions = request.auth.get('permissions', [])
    if not has_permission(permissions, f'community.{slug}.leader') and not has_permission(permissions, 'admin.community'):
        return 403, {'detail': 'Forbidden'}
    
    community = get_object_or_404(Community, slug=slug)
    
    # Get the permission
    permission = get_object_or_404(Permission, uid=permission_uid)
    
    # Verify the permission belongs to this community
    if not permission.permission.startswith(f'community.{slug}.'):
        return 403, {'detail': 'Permission does not belong to this community'}
    
    permission.delete()
    
    return {'success': True}
