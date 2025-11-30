"""
Utility functions for importing missions from slotlist.info API.

This module provides shared functionality for importing missions that can be used
by both management commands and API endpoints.
"""
import requests
from typing import Dict, Any, Optional, Tuple
from django.db import transaction
from api.models import (
    Mission, MissionSlotGroup, MissionSlot,
    Community, User
)


class MissionImportError(Exception):
    """Base exception for mission import errors"""
    pass


class MissionAlreadyExistsError(MissionImportError):
    """Raised when attempting to import a mission that already exists"""
    pass


class CreatorNotFoundError(MissionImportError):
    """Raised when the specified creator user does not exist"""
    pass


class APIFetchError(MissionImportError):
    """Raised when fetching data from slotlist.info API fails"""
    pass


def fetch_mission_data(slug: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Fetch mission and slot data from slotlist.info API.
    
    Args:
        slug: Mission slug to fetch
        
    Returns:
        Tuple of (mission_data, slots_data)
        
    Raises:
        APIFetchError: If the API request fails
    """
    mission_url = f'https://api.slotlist.info/v1/missions/{slug}'
    slots_url = f'https://api.slotlist.info/v1/missions/{slug}/slots'
    
    try:
        mission_response = requests.get(mission_url, timeout=30)
        mission_response.raise_for_status()
        mission_data = mission_response.json()['mission']
        
        slots_response = requests.get(slots_url, timeout=30)
        slots_response.raise_for_status()
        slots_data = slots_response.json()['slotGroups']
        
        return mission_data, slots_data
    except requests.RequestException as e:
        raise APIFetchError(f'Failed to fetch mission data: {e}')


def get_or_create_community(community_data: Dict[str, Any]) -> Optional[Community]:
    """
    Get or create community from API data.
    
    Args:
        community_data: Community data from API (can be None)
        
    Returns:
        Community instance or None if community_data is None
    """
    if not community_data:
        return None
        
    community, created = Community.objects.get_or_create(
        uid=community_data['uid'],
        defaults={
            'name': community_data['name'],
            'tag': community_data['tag'],
            'slug': community_data['slug'],
            'website': community_data.get('website'),
            'logo_url': community_data.get('logoUrl'),
        }
    )
    return community


def get_or_create_user(user_data: Dict[str, Any]) -> Optional[User]:
    """
    Get or create user from API data.
    
    Args:
        user_data: User data from API
        
    Returns:
        User instance or None if user_data is None
    """
    if not user_data:
        return None
    
    # Get or create the user's community first if they have one
    user_community = None
    if user_data.get('community'):
        user_community = get_or_create_community(user_data['community'])
        
    user, created = User.objects.get_or_create(
        uid=user_data['uid'],
        defaults={
            'nickname': user_data['nickname'],
            'steam_id': f'imported_{user_data["uid"]}',  # Placeholder since API doesn't expose steam_id
            'community': user_community,
        }
    )
    
    # Update community for existing users if it's different
    if not created and user_community and user.community != user_community:
        user.community = user_community
        user.save(update_fields=['community'])
    
    return user


def import_mission(
    slug: str,
    creator_uid: Optional[str] = None,
    mission_data: Optional[Dict[str, Any]] = None,
    slots_data: Optional[Dict[str, Any]] = None,
    update_existing: bool = False
) -> Mission:
    """
    Import a mission from slotlist.info API data.
    
    This function performs the actual import in a database transaction.
    If mission_data and slots_data are not provided, they will be fetched
    from the API.
    
    Args:
        slug: Mission slug
        creator_uid: Optional UUID of the user to set as mission creator.
                    If not provided, uses the original creator from API data.
        mission_data: Optional mission data (if already fetched)
        slots_data: Optional slots data (if already fetched)
        update_existing: If True, update mission if it already exists.
                        If False, raise MissionAlreadyExistsError.
        
    Returns:
        Created or updated Mission instance
        
    Raises:
        MissionAlreadyExistsError: If mission with slug already exists and update_existing is False
        CreatorNotFoundError: If creator user not found
        APIFetchError: If fetching from API fails
    """
    # Fetch data if not provided
    if mission_data is None or slots_data is None:
        mission_data, slots_data = fetch_mission_data(slug)
    
    # Get creator user
    if creator_uid:
        # Use specified creator
        try:
            creator = User.objects.get(uid=creator_uid)
        except User.DoesNotExist:
            raise CreatorNotFoundError(f'Creator user with UID {creator_uid} not found')
    else:
        # Use original creator from API data
        creator = get_or_create_user(mission_data['creator'])
        if not creator:
            raise CreatorNotFoundError('Could not determine mission creator from API data')
    
    # Check if mission already exists
    existing_mission = Mission.objects.filter(slug=mission_data['slug']).first()
    if existing_mission:
        if update_existing:
            return _update_mission(existing_mission, mission_data, slots_data, creator)
        else:
            raise MissionAlreadyExistsError(f'Mission with slug {mission_data["slug"]} already exists')
    
    # Import in transaction
    with transaction.atomic():
        # Get or create community
        community = get_or_create_community(mission_data['community'])
        
        # Create mission
        mission = Mission.objects.create(
            slug=mission_data['slug'],
            title=mission_data['title'],
            description=mission_data['description'],
            short_description=mission_data['description'],
            detailed_description=mission_data.get('detailedDescription', ''),
            collapsed_description=mission_data.get('collapsedDescription'),
            briefing_time=mission_data.get('briefingTime'),
            slotting_time=mission_data.get('slottingTime'),
            start_time=mission_data.get('startTime'),
            end_time=mission_data.get('endTime'),
            visibility=mission_data.get('visibility', 'public'),
            tech_support=mission_data.get('techSupport'),
            rules=mission_data.get('rules'),
            required_dlcs=mission_data.get('requiredDLCs', []),
            banner_image_url=mission_data.get('bannerImageUrl'),
            game_server=mission_data.get('gameServer'),
            voice_comms=mission_data.get('voiceComms'),
            repositories=mission_data.get('repositories', []),
            creator=creator,
            community=community,
        )
        
        # Import slot groups and slots
        _import_slots(mission, slots_data)
        
    return mission


def _update_mission(
    mission: Mission,
    mission_data: Dict[str, Any],
    slots_data: list,
    creator: User
) -> Mission:
    """
    Update an existing mission with new data from slotlist.info API.
    
    This function updates the mission's content fields including body fields
    that may contain media (images). It preserves slot assignments and registrations.
    
    Args:
        mission: Existing Mission instance to update
        mission_data: Mission data from API
        slots_data: Slots data from API
        creator: User to set as creator
        
    Returns:
        Updated Mission instance
    """
    from api.models import MissionSlotRegistration
    
    with transaction.atomic():
        # Get or create community
        community = get_or_create_community(mission_data['community'])
        
        # Update mission fields - including body fields with media content
        mission.title = mission_data['title']
        mission.description = mission_data['description']
        mission.short_description = mission_data['description']
        mission.detailed_description = mission_data.get('detailedDescription', '')
        mission.collapsed_description = mission_data.get('collapsedDescription')
        mission.briefing_time = mission_data.get('briefingTime')
        mission.slotting_time = mission_data.get('slottingTime')
        mission.start_time = mission_data.get('startTime')
        mission.end_time = mission_data.get('endTime')
        mission.visibility = mission_data.get('visibility', 'public')
        mission.tech_support = mission_data.get('techSupport')
        mission.rules = mission_data.get('rules')
        mission.required_dlcs = mission_data.get('requiredDLCs', [])
        mission.banner_image_url = mission_data.get('bannerImageUrl')
        mission.game_server = mission_data.get('gameServer')
        mission.voice_comms = mission_data.get('voiceComms')
        mission.repositories = mission_data.get('repositories', [])
        mission.creator = creator
        mission.community = community
        mission.save()
        
        # Update slots - preserve existing assignments where possible
        _update_slots(mission, slots_data)
        
    return mission


def _update_slots(mission: Mission, slot_groups_data: list) -> None:
    """
    Update slot groups and slots for a mission, preserving existing assignments.
    
    This function synchronizes slots from the API data while preserving
    existing slot assignments and registrations where possible.
    
    Args:
        mission: Mission instance to update slots for
        slot_groups_data: List of slot group data from API
    """
    from api.models import MissionSlotRegistration
    
    # Build lookup of existing slot groups and slots by UID
    existing_groups = {str(g.uid): g for g in mission.slot_groups.all()}
    existing_slots = {}
    for group in mission.slot_groups.all():
        for slot in group.slots.all():
            existing_slots[str(slot.uid)] = slot
    
    # Track which groups and slots we've seen in the API data
    seen_group_uids = set()
    seen_slot_uids = set()
    
    for group_data in slot_groups_data:
        group_uid = group_data['uid']
        seen_group_uids.add(group_uid)
        
        if group_uid in existing_groups:
            # Update existing group
            slot_group = existing_groups[group_uid]
            slot_group.title = group_data['title']
            slot_group.description = group_data.get('description')
            slot_group.order_number = group_data['orderNumber']
            slot_group.save()
        else:
            # Create new group
            slot_group = MissionSlotGroup.objects.create(
                uid=group_uid,
                mission=mission,
                title=group_data['title'],
                description=group_data.get('description'),
                order_number=group_data['orderNumber'],
            )
        
        # Process slots in this group
        for slot_data in group_data['slots']:
            slot_uid = slot_data['uid']
            seen_slot_uids.add(slot_uid)
            
            # Get restricted community if any
            restricted_community = None
            if slot_data.get('restrictedCommunity'):
                restricted_community = get_or_create_community(
                    slot_data['restrictedCommunity']
                )
            
            if slot_uid in existing_slots:
                # Update existing slot - preserve assignee and registration
                slot = existing_slots[slot_uid]
                slot.slot_group = slot_group
                slot.title = slot_data['title']
                slot.description = slot_data.get('description')
                slot.detailed_description = slot_data.get('detailedDescription')
                slot.order_number = slot_data['orderNumber']
                slot.required_dlcs = slot_data.get('requiredDLCs', [])
                slot.restricted_community = restricted_community
                slot.blocked = slot_data.get('blocked', False)
                slot.reserve = slot_data.get('reserve', False)
                slot.auto_assignable = slot_data.get('autoAssignable', True)
                # Note: We don't update assignee/external_assignee to preserve local assignments
                # But we do update if the API has assignment info and slot is currently unassigned
                if slot.assignee is None and slot.external_assignee is None:
                    if slot_data.get('assignee'):
                        slot.assignee = get_or_create_user(slot_data['assignee'])
                    elif slot_data.get('externalAssignee'):
                        slot.external_assignee = slot_data.get('externalAssignee')
                slot.save()
            else:
                # Create new slot
                assignee = None
                if slot_data.get('assignee'):
                    assignee = get_or_create_user(slot_data['assignee'])
                
                slot = MissionSlot.objects.create(
                    uid=slot_uid,
                    slot_group=slot_group,
                    title=slot_data['title'],
                    description=slot_data.get('description'),
                    detailed_description=slot_data.get('detailedDescription'),
                    order_number=slot_data['orderNumber'],
                    required_dlcs=slot_data.get('requiredDLCs', []),
                    external_assignee=slot_data.get('externalAssignee'),
                    assignee=assignee,
                    restricted_community=restricted_community,
                    blocked=slot_data.get('blocked', False),
                    reserve=slot_data.get('reserve', False),
                    auto_assignable=slot_data.get('autoAssignable', True),
                )
                
                # Create registration if there's an assignee
                if assignee and slot_data.get('registrationUid'):
                    MissionSlotRegistration.objects.create(
                        uid=slot_data['registrationUid'],
                        user=assignee,
                        slot=slot,
                    )
    
    # Note: We don't delete slot groups or slots that are no longer in the API
    # to preserve any local-only slots that may have been added


def _import_slots(mission: Mission, slot_groups_data: list) -> None:
    """
    Import slot groups and slots for a mission.
    
    Args:
        mission: Mission instance to add slots to
        slot_groups_data: List of slot group data from API
    """
    for group_data in slot_groups_data:
        # Create slot group
        slot_group = MissionSlotGroup.objects.create(
            uid=group_data['uid'],
            mission=mission,
            title=group_data['title'],
            description=group_data.get('description'),
            order_number=group_data['orderNumber'],
        )
        
        # Create slots
        for slot_data in group_data['slots']:
            # Get restricted community if any
            restricted_community = None
            if slot_data.get('restrictedCommunity'):
                restricted_community = get_or_create_community(
                    slot_data['restrictedCommunity']
                )
            
            # Get assignee if any
            assignee = None
            if slot_data.get('assignee'):
                assignee = get_or_create_user(slot_data['assignee'])
            
            # Create slot
            slot = MissionSlot.objects.create(
                uid=slot_data['uid'],
                slot_group=slot_group,
                title=slot_data['title'],
                description=slot_data.get('description'),
                detailed_description=slot_data.get('detailedDescription'),
                order_number=slot_data['orderNumber'],
                required_dlcs=slot_data.get('requiredDLCs', []),
                external_assignee=slot_data.get('externalAssignee'),
                assignee=assignee,
                restricted_community=restricted_community,
                blocked=slot_data.get('blocked', False),
                reserve=slot_data.get('reserve', False),
                auto_assignable=slot_data.get('autoAssignable', True),
            )
            
            # Create registration if there's an assignee
            if assignee and slot_data.get('registrationUid'):
                from api.models import MissionSlotRegistration
                MissionSlotRegistration.objects.create(
                    uid=slot_data['registrationUid'],
                    user=assignee,
                    slot=slot,
                )


def preview_import(mission_data: Dict[str, Any], slots_data: list) -> Dict[str, Any]:
    """
    Generate a preview of what would be imported without saving to database.
    
    Args:
        mission_data: Mission data from API
        slots_data: Slots data from API
        
    Returns:
        Dictionary with preview information
    """
    community_info = None
    if mission_data.get('community'):
        community_info = {
            'name': mission_data['community']['name'],
            'slug': mission_data['community']['slug'],
        }
    
    preview = {
        'mission': {
            'title': mission_data['title'],
            'slug': mission_data['slug'],
            'description': mission_data['description'],
            'visibility': mission_data['visibility'],
            'community': community_info,
        },
        'slot_groups': [],
        'totals': {
            'slot_groups': len(slots_data),
            'slots': sum(len(group['slots']) for group in slots_data),
        }
    }
    
    for group in slots_data:
        slots = []
        for slot in group['slots']:
            slot_info = {'title': slot['title']}
            
            # Add assignee info if present
            if slot.get('assignee'):
                slot_info['assignee'] = slot['assignee']['nickname']
            elif slot.get('externalAssignee'):
                slot_info['assignee'] = f"External: {slot['externalAssignee']}"
            else:
                slot_info['assignee'] = 'Unassigned'
            
            slots.append(slot_info)
        
        group_preview = {
            'title': group['title'],
            'slot_count': len(group['slots']),
            'slots': slots
        }
        preview['slot_groups'].append(group_preview)
    
    return preview
