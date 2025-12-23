"""
Django Ninja permission classes and utilities for mission visibility.
"""
from typing import Any, Optional
from django.http import HttpRequest
from django.db import models
from django.db.models import Q, Exists, OuterRef
from api.models import Mission, MissionSlot
from api.auth import has_permission, decode_jwt


class CanViewMission:
    """
    Django Ninja permission class to check if user can view a mission.
    
    Usage:
        @router.get('/{slug}', auth=CanViewMission())
        def get_mission(request, slug: str):
            mission = get_object_or_404(Mission, slug=slug)
            # User is authorized to view this mission
            ...
    
    Visibility rules:
    - public: everyone can see
    - community: only community members can see
    - private: only assigned users, editors, creator, and admins can see
    - hidden: only creator and admins can see
    """
    
    def __call__(self, request: HttpRequest, mission: Mission) -> bool:
        """Check if the current user can view the mission."""
        # Get current user info - manually decode JWT for auth=None endpoints
        current_user_uid = None
        current_user_community_uid = None
        permissions = []
        
        # Try to get auth from request.auth first (if endpoint uses auth)
        if hasattr(request, 'auth') and request.auth:
            current_user_uid = request.auth.get('user', {}).get('uid')
            user_community = request.auth.get('user', {}).get('community')
            if user_community:
                current_user_community_uid = user_community.get('uid')
            permissions = request.auth.get('permissions', [])
        else:
            # Manually decode JWT from Authorization header for auth=None endpoints
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                payload = decode_jwt(token)
                if payload:
                    current_user_uid = payload.get('user', {}).get('uid')
                    user_community = payload.get('user', {}).get('community')
                    if user_community:
                        current_user_community_uid = user_community.get('uid')
                    permissions = payload.get('permissions', [])
        
        # Public missions are always visible
        if mission.visibility == 'public':
            return True
        
        # Unauthenticated users can only see public missions
        if not current_user_uid:
            return False
        
        # Creator can always see their own missions
        if str(mission.creator.uid) == str(current_user_uid):
            return True
        
        # Admins can see all missions
        if has_permission(permissions, 'admin.mission'):
            return True
        
        # Editors can see the mission regardless of visibility
        if has_permission(permissions, f'mission.{mission.slug}.editor'):
            return True
        
        # Community missions: only visible to community members
        if mission.visibility == 'community':
            if mission.community and current_user_community_uid:
                return str(mission.community.uid) == str(current_user_community_uid)
            return False
        
        # Hidden missions: only creator, admins, and editors (already checked above)
        if mission.visibility == 'hidden':
            return False
        
        # Private missions: visible to assigned users
        if mission.visibility == 'private':
            # Check if user is assigned to any slot
            slots = MissionSlot.objects.filter(
                slot_group__mission=mission,
                assignee__uid=current_user_uid
            )
            if slots.exists():
                return True
            
            return False
        
        return False


def can_view_mission(mission: Mission, request: HttpRequest) -> bool:
    """
    Functional check if the current user can view a mission.
    
    This is a convenience function that wraps the CanViewMission class
    for use in filter operations and other non-decorator contexts.
    
    Args:
        mission: The Mission instance to check
        request: The HTTP request object
        
    Returns:
        bool: True if user can view the mission, False otherwise
    """
    checker = CanViewMission()
    return checker(request, mission)


def filter_missions_by_visibility(missions, request: HttpRequest):
    """
    Filter a queryset or list of missions based on visibility rules.
    
    Args:
        missions: QuerySet or list of Mission objects
        request: The HTTP request object
        
    Returns:
        List of Mission objects that the user can view
    """
    return [mission for mission in missions if can_view_mission(mission, request)]


class MissionVisibilityQuerySet(models.QuerySet):
    """
    Custom QuerySet for filtering missions by visibility at the database level.
    
    This provides more efficient filtering than Python-level filtering,
    especially for large datasets.
    
    Example usage:
        # Get user info from request
        user_uid, community_uid, permissions = get_user_info_from_request(request)
        
        # Filter missions at database level
        visible_missions = Mission.objects.visible_to_user(
            user_uid=user_uid,
            community_uid=community_uid,
            permissions=permissions
        )
    """
    
    def visible_to_user(
        self,
        user_uid: Optional[str] = None,
        community_uid: Optional[str] = None,
        permissions: Optional[list] = None
    ):
        """
        Filter missions based on visibility rules for a specific user.
        
        Args:
            user_uid: UUID of the current user (None for unauthenticated)
            community_uid: UUID of the user's community (None if no community)
            permissions: List of permission strings the user has
            
        Returns:
            QuerySet of missions the user can view
        """
        if permissions is None:
            permissions = []
        
        # Always include public missions
        q = Q(visibility='public')
        
        # If user is authenticated, add more conditions
        if user_uid:
            # User can see their own missions
            q |= Q(creator__uid=user_uid)
            
            # Admins can see all missions
            if has_permission(permissions, 'admin.mission'):
                return self.all()
            
            # Community missions visible to community members
            if community_uid:
                q |= Q(visibility='community', community__uid=community_uid)
            
            # Private missions where user is assigned to a slot
            user_assigned_subquery = MissionSlot.objects.filter(
                slot_group__mission=OuterRef('pk'),
                assignee__uid=user_uid
            )
            q |= Q(visibility='private', pk__in=Exists(user_assigned_subquery))
            
            # Missions where user has editor permission
            # Note: Editor permissions are dynamic (mission.{slug}.editor)
            # These need to be checked at Python level for each mission
            # or we can build a complex Q object for known editor slugs
            editor_slugs = []
            for perm in permissions:
                if perm.startswith('mission.') and perm.endswith('.editor'):
                    slug = perm.split('.')[1]
                    editor_slugs.append(slug)
            
            if editor_slugs:
                q |= Q(slug__in=editor_slugs)
        
        return self.filter(q)


def get_user_info_from_request(request: HttpRequest) -> tuple:
    """
    Extract user information from request for use with QuerySet filtering.
    
    Args:
        request: The HTTP request object
        
    Returns:
        Tuple of (user_uid, community_uid, permissions)
    """
    current_user_uid = None
    current_user_community_uid = None
    permissions = []
    
    # Try to get auth from request.auth first (if endpoint uses auth)
    if hasattr(request, 'auth') and request.auth:
        current_user_uid = request.auth.get('user', {}).get('uid')
        user_community = request.auth.get('user', {}).get('community')
        if user_community:
            current_user_community_uid = user_community.get('uid')
        permissions = request.auth.get('permissions', [])
    else:
        # Manually decode JWT from Authorization header for auth=None endpoints
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = decode_jwt(token)
            if payload:
                current_user_uid = payload.get('user', {}).get('uid')
                user_community = payload.get('user', {}).get('community')
                if user_community:
                    current_user_community_uid = user_community.get('uid')
                permissions = payload.get('permissions', [])
    
    return current_user_uid, current_user_community_uid, permissions
