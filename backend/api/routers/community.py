from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List
from uuid import UUID
from django.utils.text import slugify
from api.models import Community
from api.schemas import CommunitySchema, CommunityCreateSchema, CommunityUpdateSchema
from api.auth import has_permission

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
    
    # Get members and leaders
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


@router.get('/{slug}/missions', auth=None)
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


@router.get('/{slug}/permissions', auth=None)
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


@router.get('/{slug}/repositories', auth=None)
def get_community_repositories(request, slug: str):
    """Get repositories for a community"""
    community = get_object_or_404(Community, slug=slug)
    
    return {
        'repositories': community.repositories or []
    }


@router.get('/{slug}/servers', auth=None)
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
                'applicationText': application.application_text,
                'createdAt': application.created_at.isoformat() if application.created_at else None,
                'updatedAt': application.updated_at.isoformat() if application.updated_at else None
            }
        }
    except CommunityApplication.DoesNotExist:
        # Return 404 when no application found
        return 404, {'message': 'Community application not found'}


@router.post('/{slug}/applications')
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
        status='submitted',
        application_text=''  # Default empty text as the API doesn't seem to accept text in the POST
    )
    
    return {
        'status': application.status,
        'uid': str(application.uid)
    }
