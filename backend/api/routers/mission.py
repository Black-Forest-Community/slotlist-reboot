from ninja import Router
from django.shortcuts import get_object_or_404
from django.db import models
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from django.utils.text import slugify
from pydantic import BaseModel
from api.models import Mission, Community, User, MissionSlotGroup, MissionSlot, ArmaThreeDLC, MissionSlotRegistration
from api.schemas import (
    MissionCreateSchema, MissionUpdateSchema, MissionDuplicateSchema,
    MissionSlotGroupCreateSchema, MissionSlotGroupUpdateSchema,
    MissionSlotCreateSchema, MissionSlotUpdateSchema,
    MissionBannerImageSchema, MissionSlotAssignSchema,
    MissionPermissionCreateSchema
)
from api.auth import has_permission, generate_jwt

router = Router()


def validate_dlc_list(dlc_list, field_name='required_dlcs'):
    """Validate a DLC list and raise error if invalid."""
    # Allow None or empty list
    if not dlc_list:
        return
    
    if not ArmaThreeDLC.validate_dlc_list(dlc_list):
        invalid_dlcs = [dlc for dlc in dlc_list if dlc not in ArmaThreeDLC.get_valid_dlcs()]
        from ninja.errors import HttpError
        raise HttpError(400, f'Invalid {field_name}: {", ".join(invalid_dlcs)}. Valid options: {", ".join(ArmaThreeDLC.get_valid_dlcs())}')


@router.get('/', auth=None)
def list_missions(request, limit: int = 25, offset: int = 0, includeEnded: bool = False, startDate: int = None, endDate: int = None):
    """List all missions with pagination"""
    query = Mission.objects.select_related('creator', 'community').all()
    
    # Date range filtering for calendar
    # When startDate and endDate are provided (calendar view), return just array
    is_calendar_query = startDate is not None and endDate is not None
    
    if is_calendar_query:
        from datetime import datetime as dt, timezone
        start_dt = dt.fromtimestamp(startDate / 1000, tz=timezone.utc)
        end_dt = dt.fromtimestamp(endDate / 1000, tz=timezone.utc)
        query = query.filter(start_time__gte=start_dt, start_time__lte=end_dt)
    elif not includeEnded:
        query = query.filter(end_time__gte=datetime.utcnow()) | query.filter(end_time__isnull=True)
    
    # Get total count before applying pagination
    total = query.count()
    
    # Apply pagination
    missions = query.order_by('-start_time')[offset:offset + limit]
    
    # Get current user if authenticated
    current_user_uid = None
    if hasattr(request, 'auth') and request.auth:
        current_user_uid = request.auth.get('user', {}).get('uid')
    
    # Calculate slot counts for each mission
    result_missions = []
    for mission in missions:
        # Get all slots for this mission
        from django.db.models import Count, Q
        slots = MissionSlot.objects.filter(slot_group__mission=mission)
        
        total_slots = slots.count()
        assigned_slots = slots.filter(assignee__isnull=False).count()
        external_slots = slots.filter(external_assignee__isnull=False).exclude(external_assignee='').count()
        unassigned_slots = slots.filter(assignee__isnull=True, external_assignee__isnull=True).count() + \
                          slots.filter(assignee__isnull=True, external_assignee='').count()
        
        # Open slots are those without assignee, external_assignee, and no restricted community
        open_slots = slots.filter(
            assignee__isnull=True,
            restricted_community__isnull=True
        ).filter(
            Q(external_assignee__isnull=True) | Q(external_assignee='')
        ).count()
        
        # Check if current user is assigned to any slot
        is_assigned_to_any_slot = False
        is_registered_for_any_slot = False
        if current_user_uid:
            is_assigned_to_any_slot = slots.filter(assignee__uid=current_user_uid).exists()
            # Registration status would need to check a separate registration table if it exists
            # For now, keeping it as False
        
        result_missions.append({
            'uid': str(mission.uid),
            'slug': mission.slug,
            'title': mission.title,
            'description': mission.description,
            'briefingTime': mission.briefing_time.isoformat() if mission.briefing_time else None,
            'slottingTime': mission.slotting_time.isoformat() if mission.slotting_time else None,
            'startTime': mission.start_time.isoformat() if mission.start_time else None,
            'endTime': mission.end_time.isoformat() if mission.end_time else None,
            'visibility': mission.visibility,
            'detailsMap': mission.details_map,
            'detailsGameMode': mission.details_game_mode,
            'requiredDLCs': mission.required_dlcs,
            'bannerImageUrl': mission.banner_image_url,
            'slotCounts': {
                'total': total_slots,
                'assigned': assigned_slots,
                'external': external_slots,
                'unassigned': unassigned_slots,
                'open': open_slots
            },
            'isAssignedToAnySlot': is_assigned_to_any_slot,
            'isRegisteredForAnySlot': is_registered_for_any_slot,
            'creator': {
                'uid': str(mission.creator.uid),
                'nickname': mission.creator.nickname,
                'steamId': mission.creator.steam_id,
            },
            'community': {
                'uid': str(mission.community.uid),
                'name': mission.community.name,
                'tag': mission.community.tag,
                'slug': mission.community.slug,
                'website': mission.community.website,
                'logoUrl': mission.community.logo_url,
            } if mission.community else None
        })
    
    # Calendar queries return just the array for backwards compatibility
    if is_calendar_query:
        return result_missions
    
    return {
        'missions': result_missions,
        'total': total
    }


@router.get('/slugAvailable', auth=None)
def check_slug_availability(request, slug: str):
    """Check if a mission slug is available"""
    # Check if a mission with this slug already exists
    exists = Mission.objects.filter(slug=slug).exists()
    
    return {
        'available': not exists
    }


@router.get('/{slug}', auth=None)
def get_mission(request, slug: str):
    """Get a single mission by slug"""
    mission = get_object_or_404(Mission.objects.select_related('creator', 'community'), slug=slug)
    
    mission_data = {
        'uid': mission.uid,
        'slug': mission.slug,
        'title': mission.title,
        'description': mission.description,
        'detailedDescription': mission.detailed_description,
        'collapsedDescription': mission.collapsed_description,
        'briefingTime': mission.briefing_time,
        'slottingTime': mission.slotting_time,
        'startTime': mission.start_time,
        'endTime': mission.end_time,
        'visibility': mission.visibility,
        'techTeleport': bool(mission.tech_support and 'teleport' in mission.tech_support.lower()) if mission.tech_support else False,
        'techRespawn': bool(mission.tech_support and 'respawn' in mission.tech_support.lower()) if mission.tech_support else False,
        'techSupport': mission.tech_support,
        'detailsMap': mission.details_map,
        'detailsGameMode': mission.details_game_mode,
        'requiredDLCs': mission.required_dlcs,
        'gameServer': mission.game_server,
        'voiceComms': mission.voice_comms,
        'repositories': mission.repositories,
        'rulesOfEngagement': mission.rules or '',
        'bannerImageUrl': mission.banner_image_url,
        'creator': {
            'uid': mission.creator.uid,
            'nickname': mission.creator.nickname,
            'steamId': mission.creator.steam_id,
        },
        'community': {
            'uid': mission.community.uid,
            'name': mission.community.name,
            'tag': mission.community.tag,
            'slug': mission.community.slug,
            'website': mission.community.website,
            'logoUrl': mission.community.logo_url,
            'gameServers': mission.community.game_servers,
            'voiceComms': mission.community.voice_comms,
            'repositories': mission.community.repositories
        } if mission.community else None
    }
    
    return {'mission': mission_data}


@router.post('/')
def create_mission(request, payload: MissionCreateSchema):
    """Create a new mission"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    
    # Validate DLCs
    validate_dlc_list(payload.required_dlcs, 'requiredDLCs')
    
    # Get community if specified
    community = None
    if payload.community_uid:
        community = get_object_or_404(Community, uid=payload.community_uid)
    
    # Use provided slug or generate from title
    slug = payload.slug if payload.slug else slugify(payload.title)
    
    # Convert tech_teleport and tech_respawn to tech_support string
    tech_support_parts = []
    if payload.tech_teleport:
        tech_support_parts.append('teleport')
    if payload.tech_respawn:
        tech_support_parts.append('respawn')
    tech_support = ', '.join(tech_support_parts) if tech_support_parts else None
    
    # Use default datetime for required fields if not provided
    from datetime import datetime, timezone
    default_time = datetime.now(timezone.utc)

    mission = Mission.objects.create(
        slug=slug,
        title=payload.title,
        description=payload.description,
        short_description=payload.description or '',
        detailed_description=payload.detailed_description or '',
        collapsed_description=payload.collapsed_description,
        briefing_time=payload.briefing_time or default_time,
        slotting_time=payload.slotting_time or default_time,
        start_time=payload.start_time or default_time,
        end_time=payload.end_time or default_time,
        visibility=payload.visibility,
        tech_support=tech_support,
        details_map=payload.details_map,
        details_game_mode=payload.details_game_mode,
        required_dlcs=payload.required_dlcs if payload.required_dlcs is not None else [],
        game_server=payload.game_server,
        voice_comms=payload.voice_comms,
        repositories=payload.repositories if payload.repositories is not None else [],
        rules=payload.rules_of_engagement,
        creator=user,
        community=community
    )
    
    # Generate a new JWT token with the creator permission for this mission
    new_token = generate_jwt(user)
    
    return {
        'token': new_token,  # Return updated token with mission.{slug}.creator permission
        'mission': {
            'uid': mission.uid,
            'slug': mission.slug,
            'title': mission.title,
            'description': mission.description,
            'detailedDescription': mission.detailed_description,
            'collapsedDescription': mission.collapsed_description,
            'briefingTime': mission.briefing_time,
            'slottingTime': mission.slotting_time,
            'startTime': mission.start_time,
            'endTime': mission.end_time,
            'visibility': mission.visibility,
            'techTeleport': bool(mission.tech_support and 'teleport' in mission.tech_support.lower()) if mission.tech_support else False,
            'techRespawn': bool(mission.tech_support and 'respawn' in mission.tech_support.lower()) if mission.tech_support else False,
            'techSupport': mission.tech_support,
            'detailsMap': mission.details_map,
            'detailsGameMode': mission.details_game_mode,
            'requiredDLCs': mission.required_dlcs,
            'gameServer': mission.game_server,
            'voiceComms': mission.voice_comms,
            'repositories': mission.repositories,
            'rulesOfEngagement': mission.rules or '',
            'bannerImageUrl': mission.banner_image_url,
            'creator': {
                'uid': user.uid,
                'nickname': user.nickname,
                'steamId': user.steam_id,
            },
            'community': {
                'uid': community.uid,
                'name': community.name,
                'tag': community.tag,
                'slug': community.slug,
                'website': community.website,
                'logoUrl': community.logo_url,
                'gameServers': community.game_servers,
                'voiceComms': community.voice_comms,
                'repositories': community.repositories
            } if community else None
        }
    }


@router.patch('/{slug}')
def update_mission(request, slug: str, payload: MissionUpdateSchema):
    """Update a mission"""
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Forbidden'}
    
    # Validate DLCs if provided
    if payload.required_dlcs is not None:
        validate_dlc_list(payload.required_dlcs, 'requiredDLCs')
    
    # Update fields
    if payload.title is not None:
        mission.title = payload.title
    if payload.description is not None:
        mission.description = payload.description
        mission.short_description = payload.description  # Keep short_description in sync
    if payload.detailed_description is not None:
        mission.detailed_description = payload.detailed_description
    if payload.collapsed_description is not None:
        mission.collapsed_description = payload.collapsed_description
    if payload.briefing_time is not None:
        mission.briefing_time = payload.briefing_time
    if payload.slotting_time is not None:
        mission.slotting_time = payload.slotting_time
    if payload.start_time is not None:
        mission.start_time = payload.start_time
    if payload.end_time is not None:
        mission.end_time = payload.end_time
    if payload.visibility is not None:
        mission.visibility = payload.visibility
    
    # Handle tech_support - can be set directly or via tech_teleport/tech_respawn
    if payload.tech_support is not None:
        mission.tech_support = payload.tech_support
    elif payload.tech_teleport is not None or payload.tech_respawn is not None:
        # Get current tech_support settings
        current_teleport = mission.tech_support and 'teleport' in mission.tech_support.lower() if mission.tech_support else False
        current_respawn = mission.tech_support and 'respawn' in mission.tech_support.lower() if mission.tech_support else False
        
        # Update with new values if provided
        new_teleport = payload.tech_teleport if payload.tech_teleport is not None else current_teleport
        new_respawn = payload.tech_respawn if payload.tech_respawn is not None else current_respawn
        
        # Build new tech_support string
        tech_support_parts = []
        if new_teleport:
            tech_support_parts.append('teleport')
        if new_respawn:
            tech_support_parts.append('respawn')
        mission.tech_support = ', '.join(tech_support_parts) if tech_support_parts else None
    
    if payload.details_map is not None:
        mission.details_map = payload.details_map
    if payload.details_game_mode is not None:
        mission.details_game_mode = payload.details_game_mode
    if payload.required_dlcs is not None:
        mission.required_dlcs = payload.required_dlcs
    if payload.game_server is not None:
        mission.game_server = payload.game_server
    if payload.voice_comms is not None:
        mission.voice_comms = payload.voice_comms
    if payload.repositories is not None:
        mission.repositories = payload.repositories
    if payload.rules_of_engagement is not None:
        mission.rules = payload.rules_of_engagement
    
    mission.save()
    
    return {
        'mission': {
            'uid': mission.uid,
            'slug': mission.slug,
            'title': mission.title,
            'description': mission.description,
            'detailedDescription': mission.detailed_description,
            'collapsedDescription': mission.collapsed_description,
            'briefingTime': mission.briefing_time,
            'slottingTime': mission.slotting_time,
            'startTime': mission.start_time,
            'endTime': mission.end_time,
            'visibility': mission.visibility,
            'techTeleport': bool(mission.tech_support and 'teleport' in mission.tech_support.lower()) if mission.tech_support else False,
            'techRespawn': bool(mission.tech_support and 'respawn' in mission.tech_support.lower()) if mission.tech_support else False,
            'techSupport': mission.tech_support,
            'detailsMap': mission.details_map,
            'detailsGameMode': mission.details_game_mode,
            'requiredDLCs': mission.required_dlcs,
            'gameServer': mission.game_server,
            'voiceComms': mission.voice_comms,
            'repositories': mission.repositories,
            'rulesOfEngagement': mission.rules or '',
            'bannerImageUrl': mission.banner_image_url,
            'creator': {
                'uid': mission.creator.uid,
                'nickname': mission.creator.nickname,
                'steamId': mission.creator.steam_id,
            },
            'community': {
                'uid': mission.community.uid,
                'name': mission.community.name,
                'tag': mission.community.tag,
                'slug': mission.community.slug,
                'website': mission.community.website,
                'logoUrl': mission.community.logo_url,
                'gameServers': mission.community.game_servers,
                'voiceComms': mission.community.voice_comms,
                'repositories': mission.community.repositories
            } if mission.community else None
        }
    }


@router.delete('/{slug}')
def delete_mission(request, slug: str):
    """Delete a mission"""
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Forbidden'}
    
    mission.delete()
    
    return {'success': True}


@router.post('/{slug}/duplicate')
def duplicate_mission(request, slug: str, payload: MissionDuplicateSchema):
    """Duplicate an existing mission with all its slot groups and slots"""
    from django.db import transaction
    
    # Get the original mission
    original_mission = get_object_or_404(Mission.objects.select_related('creator', 'community'), slug=slug)
    
    # Get current user
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    
    # Check permissions - must be creator or admin
    permissions = request.auth.get('permissions', [])
    is_creator = str(original_mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Forbidden'}
    
    # Check if new slug is available
    if Mission.objects.filter(slug=payload.slug).exists():
        return 400, {'detail': 'Mission with this slug already exists'}
    
    # Determine community for new mission
    community = None
    if payload.add_to_community and user.community:
        community = user.community
    elif not payload.add_to_community:
        community = original_mission.community
    
    # Create the duplicated mission in a transaction
    with transaction.atomic():
        # Create new mission
        new_mission = Mission.objects.create(
            slug=payload.slug,
            title=payload.title if payload.title else original_mission.title,
            description=original_mission.description,
            short_description=original_mission.short_description,
            detailed_description=original_mission.detailed_description,
            collapsed_description=original_mission.collapsed_description,
            briefing_time=payload.briefing_time if payload.briefing_time else original_mission.briefing_time,
            slotting_time=payload.slotting_time if payload.slotting_time else original_mission.slotting_time,
            start_time=payload.start_time if payload.start_time else original_mission.start_time,
            end_time=payload.end_time if payload.end_time else original_mission.end_time,
            visibility=payload.visibility if payload.visibility else 'hidden',
            tech_support=original_mission.tech_support,
            details_map=original_mission.details_map,
            details_game_mode=original_mission.details_game_mode,
            required_dlcs=original_mission.required_dlcs,
            game_server=original_mission.game_server,
            voice_comms=original_mission.voice_comms,
            repositories=original_mission.repositories,
            rules=original_mission.rules,
            creator=user,
            community=community,
            banner_image_url=original_mission.banner_image_url
        )
        
        # Duplicate slot groups and slots
        original_slot_groups = MissionSlotGroup.objects.filter(mission=original_mission).order_by('order_number')
        
        for slot_group in original_slot_groups:
            # Create new slot group
            new_slot_group = MissionSlotGroup.objects.create(
                mission=new_mission,
                title=slot_group.title,
                description=slot_group.description,
                order_number=slot_group.order_number
            )
            
            # Duplicate slots in this group
            original_slots = MissionSlot.objects.filter(slot_group=slot_group).order_by('order_number')
            
            for slot in original_slots:
                MissionSlot.objects.create(
                    slot_group=new_slot_group,
                    title=slot.title,
                    description=slot.description,
                    detailed_description=slot.detailed_description,
                    order_number=slot.order_number,
                    required_dlcs=slot.required_dlcs,
                    restricted_community=slot.restricted_community,
                    blocked=slot.blocked,
                    reserve=slot.reserve,
                    auto_assignable=slot.auto_assignable
                    # Note: Not copying assignee or external_assignee - duplicated mission starts with empty slots
                )
    
    # Generate a new JWT token with the creator permission for this mission
    new_token = generate_jwt(user)
    
    # Return the new mission details
    return {
        'token': new_token,
        'mission': {
            'uid': new_mission.uid,
            'slug': new_mission.slug,
            'title': new_mission.title,
            'description': new_mission.description,
            'detailedDescription': new_mission.detailed_description,
            'collapsedDescription': new_mission.collapsed_description,
            'briefingTime': new_mission.briefing_time,
            'slottingTime': new_mission.slotting_time,
            'startTime': new_mission.start_time,
            'endTime': new_mission.end_time,
            'visibility': new_mission.visibility,
            'techTeleport': bool(new_mission.tech_support and 'teleport' in new_mission.tech_support.lower()) if new_mission.tech_support else False,
            'techRespawn': bool(new_mission.tech_support and 'respawn' in new_mission.tech_support.lower()) if new_mission.tech_support else False,
            'techSupport': new_mission.tech_support,
            'detailsMap': new_mission.details_map,
            'detailsGameMode': new_mission.details_game_mode,
            'requiredDLCs': new_mission.required_dlcs,
            'gameServer': new_mission.game_server,
            'voiceComms': new_mission.voice_comms,
            'repositories': new_mission.repositories,
            'rulesOfEngagement': new_mission.rules or '',
            'bannerImageUrl': new_mission.banner_image_url,
            'creator': {
                'uid': user.uid,
                'nickname': user.nickname,
                'steamId': user.steam_id,
            },
            'community': {
                'uid': community.uid,
                'name': community.name,
                'tag': community.tag,
                'slug': community.slug,
                'website': community.website,
                'logoUrl': community.logo_url,
                'gameServers': community.game_servers,
                'voiceComms': community.voice_comms,
                'repositories': community.repositories
            } if community else None
        }
    }



@router.get('/{slug}/slots', auth=None)
def get_mission_slots(request, slug: str):
    """Get all slots for a mission organized by slot groups"""
    mission = get_object_or_404(Mission.objects.select_related('creator', 'community'), slug=slug)
    
    # Get current user UID if authenticated (manually check Authorization header)
    current_user_uid = None
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        from api.auth import decode_jwt
        payload = decode_jwt(token)
        if payload:
            current_user_uid = payload.get('user', {}).get('uid')
    
    # Get all slot groups with their slots for this mission
    slot_groups = MissionSlotGroup.objects.filter(mission=mission).prefetch_related(
        'slots__assignee',
        'slots__restricted_community',
        'slots__registrations__user'
    ).order_by('order_number')
    
    result = []
    for slot_group in slot_groups:
        slots = []
        for slot in slot_group.slots.order_by('order_number'):
            # Count pending registrations for this slot (exclude confirmed/rejected)
            registration_count = slot.registrations.filter(status='pending').count()
            
            # Check if current user has a registration for this slot
            user_registration_uid = None
            if current_user_uid:
                user_registration = slot.registrations.filter(user__uid=current_user_uid).first()
                if user_registration:
                    user_registration_uid = str(user_registration.uid)
            
            slot_data = {
                'uid': str(slot.uid),
                'slotGroupUid': str(slot.slot_group.uid),
                'title': slot.title,
                'description': slot.description,
                'detailedDescription': slot.detailed_description,
                'orderNumber': slot.order_number,
                'requiredDLCs': slot.required_dlcs,
                'externalAssignee': slot.external_assignee,
                'registrationCount': registration_count,
                'registrationUid': user_registration_uid,
                'blocked': slot.blocked,
                'reserve': slot.reserve,
                'autoAssignable': slot.auto_assignable,
                'assignee': {
                    'uid': str(slot.assignee.uid),
                    'nickname': slot.assignee.nickname,
                    'steamId': slot.assignee.steam_id,
                } if slot.assignee else None,
                'restrictedCommunity': {
                    'uid': str(slot.restricted_community.uid),
                    'name': slot.restricted_community.name,
                    'tag': slot.restricted_community.tag,
                    'slug': slot.restricted_community.slug,
                } if slot.restricted_community else None
            }
            slots.append(slot_data)
        
        group_data = {
            'uid': str(slot_group.uid),
            'title': slot_group.title,
            'description': slot_group.description,
            'orderNumber': slot_group.order_number,
            'slots': slots
        }
        result.append(group_data)
    
    return {'slotGroups': result}


# Slot Registration Schemas
class SlotRegistrationCreateSchema(BaseModel):
    comment: Optional[str] = None


class SlotRegistrationUpdateSchema(BaseModel):
    confirmed: bool
    suppressNotifications: Optional[bool] = False


@router.get('/{slug}/slots/{slot_uid}/registrations', auth=None)
def get_slot_registrations(request, slug: str, slot_uid: UUID, limit: int = 10, offset: int = 0):
    """Get all registrations for a specific mission slot"""
    mission = get_object_or_404(Mission, slug=slug)
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    
    total = MissionSlotRegistration.objects.filter(slot=slot).count()
    registrations = MissionSlotRegistration.objects.filter(slot=slot).select_related('user')[offset:offset + limit]
    
    return {
        'registrations': [
            {
                'uid': str(reg.uid),
                'slotUid': str(reg.slot.uid),
                'user': {
                    'uid': str(reg.user.uid),
                    'nickname': reg.user.nickname,
                    'steamId': reg.user.steam_id,
                },
                'comment': reg.comment,
                'confirmed': reg.status == 'confirmed',
                'status': reg.status,
                'createdAt': reg.created_at.isoformat() if reg.created_at else None,
            }
            for reg in registrations
        ],
        'limit': limit,
        'offset': offset,
        'total': total
    }


@router.post('/{slug}/slots/{slot_uid}/registrations', response={200: dict, 400: dict, 403: dict})
def register_for_slot(request, slug: str, slot_uid: UUID, data: SlotRegistrationCreateSchema):
    """Register the authenticated user for a mission slot"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    
    mission = get_object_or_404(Mission, slug=slug)
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    
    # Check if user is already registered
    existing = MissionSlotRegistration.objects.filter(user=user, slot=slot).first()
    if existing:
        return 400, {'detail': 'User already registered for this slot'}
    
    # Create registration
    registration = MissionSlotRegistration.objects.create(
        user=user,
        slot=slot,
        comment=data.comment
    )
    
    return {
        'registration': {
            'uid': str(registration.uid),
            'slotUid': str(slot.uid),
            'user': {
                'uid': str(user.uid),
                'nickname': user.nickname,
                'steamId': user.steam_id,
            },
            'comment': registration.comment,
            'confirmed': False,
            'status': registration.status,
            'createdAt': registration.created_at.isoformat() if registration.created_at else None,
        }
    }


@router.patch('/{slug}/slots/{slot_uid}/registrations/{registration_uid}', response={200: dict, 400: dict, 403: dict})
def update_slot_registration(request, slug: str, slot_uid: UUID, registration_uid: UUID, data: SlotRegistrationUpdateSchema):
    """Update/confirm or reject a slot registration (requires permissions)"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    permissions = request.auth.get('permissions', [])
    
    mission = get_object_or_404(Mission, slug=slug)
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    registration = get_object_or_404(MissionSlotRegistration, uid=registration_uid, slot=slot)

    
    # Check permissions - user must be mission creator or have appropriate permissions
    is_creator = str(mission.creator.uid) == str(user.uid)
    has_perm = has_permission(permissions, ['mission.slot.assign', 'admin.*'])
    
    if not is_creator and not has_perm:
        return 403, {'detail': 'Insufficient permissions to update registration'}
    
    # If confirmed, assign the slot to the user and mark registration as confirmed
    if data.confirmed:
        # Check if slot is already assigned
        if slot.assignee and str(slot.assignee.uid) != str(registration.user.uid):
            return 400, {'detail': 'Slot is already assigned to another user'}
        
        # Assign the slot
        slot.assignee = registration.user
        slot.save()
        
        # Update registration status to confirmed
        registration.status = 'confirmed'
        registration.save()
        
        return {
            'registration': {
                'uid': str(registration.uid),
                'user': {
                    'uid': str(registration.user.uid),
                    'nickname': registration.user.nickname,
                    'steamId': registration.user.steam_id,
                },
                'comment': registration.comment,
                'confirmed': True,
                'status': registration.status
            }
        }
    else:
        # If confirmed is false, reject the registration and unassign slot if needed
        # If the registration was confirmed and slot is assigned to this user, unassign the slot
        if registration.status == 'confirmed' and slot.assignee and str(slot.assignee.uid) == str(registration.user.uid):
            slot.assignee = None
            slot.save()
        
        # Update registration status to rejected
        registration.status = 'rejected'
        registration.save()
        
        return {
            'registration': {
                'uid': str(registration.uid),
                'user': {
                    'uid': str(registration.user.uid),
                    'nickname': registration.user.nickname,
                    'steamId': registration.user.steam_id,
                },
                'comment': registration.comment,
                'confirmed': False,
                'status': registration.status
            }
        }


@router.delete('/{slug}/slots/{slot_uid}/registrations/{registration_uid}', response={200: dict, 403: dict})
def delete_slot_registration(request, slug: str, slot_uid: UUID, registration_uid: UUID):
    """Delete/reject a slot registration - if confirmed, also unassigns the slot"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    permissions = request.auth.get('permissions', [])
    
    mission = get_object_or_404(Mission, slug=slug)
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    registration = get_object_or_404(MissionSlotRegistration, uid=registration_uid, slot=slot)
    
    # User can delete their own registration, or mission creator/admin can delete any
    is_own_registration = str(registration.user.uid) == str(user.uid)
    is_creator = str(mission.creator.uid) == str(user.uid)
    has_perm = has_permission(permissions, ['mission.slot.assign', 'admin.*'])
    
    if not is_own_registration and not is_creator and not has_perm:
        return 403, {'detail': 'Insufficient permissions to delete this registration'}
    
    # If the registration was confirmed and slot is assigned to this user, unassign the slot
    if registration.status == 'confirmed' and slot.assignee and str(slot.assignee.uid) == str(registration.user.uid):
        slot.assignee = None
        slot.save()
    
    # Delete the registration
    registration.delete()
    
    return {'success': True}


@router.post('/{slug}/slots/{slot_uid}/assign', response={200: dict, 400: dict, 403: dict})
def assign_slot(request, slug: str, slot_uid: UUID, payload: MissionSlotAssignSchema):
    """Assign a user to a mission slot"""
    current_user_uid = request.auth.get('user', {}).get('uid')
    current_user = get_object_or_404(User, uid=current_user_uid)
    permissions = request.auth.get('permissions', [])
    
    mission = get_object_or_404(Mission, slug=slug)
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    
    # Get target user from payload
    target_user_uid = payload.userUid
    force = payload.force
    suppress_notifications = payload.suppressNotifications
    
    target_user = get_object_or_404(User, uid=target_user_uid)
    
    # Check if slot is already assigned
    if slot.assignee and not force:
        return 400, {'detail': 'Slot is already assigned. Use force=true to override.'}
    
    # Check if slot is blocked
    if slot.blocked:
        return 400, {'detail': 'Slot is blocked and cannot be assigned'}
    
    # Check permissions - mission creator or admin can assign anyone
    is_creator = str(mission.creator.uid) == str(current_user_uid)
    is_admin = has_permission(permissions, 'admin.mission')
    
    # Check if user is assigning themselves
    is_self_assignment = str(target_user_uid) == str(current_user_uid)
    
    # Community slot restrictions
    if slot.restricted_community:
        if not target_user.community or str(target_user.community.uid) != str(slot.restricted_community.uid):
            if not is_creator and not is_admin:
                return 403, {'detail': 'This slot is restricted to a specific community'}
    
    # Only mission creator or admin can assign other users
    if not is_self_assignment and not is_creator and not is_admin:
        return 403, {'detail': 'Insufficient permissions to assign other users to slots'}
    
    # Assign the slot
    slot.assignee = target_user
    slot.save()
    
    # TODO: Create notification if not suppressed
    # TODO: Remove any existing registrations for this slot
    
    return {
        'slot': {
            'uid': str(slot.uid),
            'title': slot.title,
            'assignee': {
                'uid': str(target_user.uid),
                'nickname': target_user.nickname,
            }
        }
    }


@router.post('/{slug}/slots/{slot_uid}/unassign', response={200: dict, 400: dict, 403: dict})
def unassign_slot(request, slug: str, slot_uid: UUID):
    """Unassign a user from a mission slot"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    permissions = request.auth.get('permissions', [])
    
    mission = get_object_or_404(Mission, slug=slug)
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    
    if not slot.assignee:
        return 400, {'detail': 'Slot is not assigned'}
    
    # Check permissions - user must be the assignee, mission creator, or have appropriate permissions
    is_assignee = str(slot.assignee.uid) == str(user.uid)
    is_creator = str(mission.creator.uid) == str(user.uid)
    has_perm = has_permission(permissions, ['mission.slot.assign', 'admin.*'])
    
    if not is_assignee and not is_creator and not has_perm:
        return 403, {'detail': 'Insufficient permissions to unassign this slot'}
    
    slot.assignee = None
    slot.save()
    
    return {
        'slot': {
            'uid': str(slot.uid),
            'title': slot.title,
            'assignee': None
        }
    }


@router.post('/{slug}/slotGroups', response={200: dict, 400: dict, 403: dict})
def create_mission_slot_group(request, slug: str, data: MissionSlotGroupCreateSchema):
    """Create a new slot group for a mission"""
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        from ninja.errors import HttpError
        raise HttpError(403, 'Insufficient permissions to create slot groups for this mission')
    
    # Get existing slot groups to determine order numbers
    existing_groups = list(MissionSlotGroup.objects.filter(mission=mission).order_by('order_number'))
    
    # Calculate the new order number based on insertAfter
    insert_after = data.insertAfter
    new_order_number = insert_after + 1
    
    # Shift order numbers of groups that come after the insert point
    for group in existing_groups:
        if group.order_number >= new_order_number:
            group.order_number += 1
            group.save()
    
    # Create the new slot group
    slot_group = MissionSlotGroup.objects.create(
        mission=mission,
        title=data.title,
        description=data.description if data.description else '',
        order_number=new_order_number
    )
    
    return {
        'slotGroup': {
            'uid': str(slot_group.uid),
            'title': slot_group.title,
            'description': slot_group.description,
            'orderNumber': slot_group.order_number,
            'slots': []
        }
    }


@router.patch('/{slug}/slotGroups/{slot_group_uid}', response={200: dict, 400: dict, 403: dict, 404: dict})
def update_mission_slot_group(request, slug: str, slot_group_uid: UUID, data: MissionSlotGroupUpdateSchema):
    """Update a slot group"""
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        from ninja.errors import HttpError
        raise HttpError(403, 'Insufficient permissions to update slot groups for this mission')
    
    slot_group = get_object_or_404(MissionSlotGroup, uid=slot_group_uid, mission=mission)
    
    # Update fields if provided
    if data.title is not None:
        slot_group.title = data.title
    
    if data.description is not None:
        slot_group.description = data.description
    
    if data.orderNumber is not None and data.orderNumber != slot_group.order_number:
        old_order = slot_group.order_number
        new_order = data.orderNumber
        
        # Shift other groups' order numbers
        if new_order > old_order:
            # Moving down: shift groups between old and new position up
            MissionSlotGroup.objects.filter(
                mission=mission,
                order_number__gt=old_order,
                order_number__lte=new_order
            ).update(order_number=models.F('order_number') - 1)
        else:
            # Moving up: shift groups between new and old position down
            MissionSlotGroup.objects.filter(
                mission=mission,
                order_number__gte=new_order,
                order_number__lt=old_order
            ).update(order_number=models.F('order_number') + 1)
        
        slot_group.order_number = new_order
    
    slot_group.save()
    
    return {
        'slotGroup': {
            'uid': str(slot_group.uid),
            'title': slot_group.title,
            'description': slot_group.description,
            'orderNumber': slot_group.order_number
        }
    }


@router.delete('/{slug}/slotGroups/{slot_group_uid}', response={200: dict, 403: dict, 404: dict})
def delete_mission_slot_group(request, slug: str, slot_group_uid: UUID):
    """Delete a slot group and all its slots"""
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        from ninja.errors import HttpError
        raise HttpError(403, 'Insufficient permissions to delete slot groups for this mission')
    
    slot_group = get_object_or_404(MissionSlotGroup, uid=slot_group_uid, mission=mission)
    deleted_order = slot_group.order_number
    
    # Delete the slot group (slots will be cascade deleted)
    slot_group.delete()
    
    # Shift down the order numbers of groups that came after this one
    MissionSlotGroup.objects.filter(
        mission=mission,
        order_number__gt=deleted_order
    ).update(order_number=models.F('order_number') - 1)
    
    return {'success': True}


@router.post('/{slug}/slots', response={200: dict, 400: dict, 403: dict})
def create_mission_slots(request, slug: str, data: List[MissionSlotCreateSchema]):
    """Create one or more slots for a mission"""
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        from ninja.errors import HttpError
        raise HttpError(403, 'Insufficient permissions to create slots for this mission')
    
    created_slots = []
    
    for slot_data in data:
        # Validate DLCs
        if slot_data.requiredDLCs:
            validate_dlc_list(slot_data.requiredDLCs, 'requiredDLCs')
        
        # Get the slot group
        slot_group = get_object_or_404(MissionSlotGroup, uid=slot_data.slotGroupUid, mission=mission)
        
        # Get existing slots in this group to determine order numbers
        existing_slots = list(MissionSlot.objects.filter(slot_group=slot_group).order_by('order_number'))
        
        # Calculate the new order number based on insertAfter
        insert_after = slot_data.insertAfter
        new_order_number = insert_after + 1
        
        # Shift order numbers of slots that come after the insert point
        for slot in existing_slots:
            if slot.order_number >= new_order_number:
                slot.order_number += 1
                slot.save()
        
        # Get restricted community if specified
        restricted_community = None
        if slot_data.restrictedCommunityUid:
            restricted_community = get_object_or_404(Community, uid=slot_data.restrictedCommunityUid)
        
        # Create the slot
        slot = MissionSlot.objects.create(
            slot_group=slot_group,
            title=slot_data.title,
            description=slot_data.description if slot_data.description else '',
            detailed_description=slot_data.detailedDescription if slot_data.detailedDescription else '',
            order_number=new_order_number,
            required_dlcs=slot_data.requiredDLCs if slot_data.requiredDLCs else [],
            restricted_community=restricted_community,
            blocked=slot_data.blocked,
            reserve=slot_data.reserve,
            auto_assignable=slot_data.autoAssignable
        )
        
        created_slots.append({
            'uid': str(slot.uid),
            'slotGroupUid': str(slot.slot_group.uid),
            'title': slot.title,
            'description': slot.description,
            'detailedDescription': slot.detailed_description,
            'orderNumber': slot.order_number,
            'requiredDLCs': slot.required_dlcs,
            'blocked': slot.blocked,
            'reserve': slot.reserve,
            'autoAssignable': slot.auto_assignable,
            'restrictedCommunity': {
                'uid': str(restricted_community.uid),
                'name': restricted_community.name,
                'tag': restricted_community.tag,
            } if restricted_community else None
        })
    
    return {'slots': created_slots}


@router.patch('/{slug}/slots/{slot_uid}', response={200: dict, 400: dict, 403: dict, 404: dict})
def update_mission_slot(request, slug: str, slot_uid: UUID, data: MissionSlotUpdateSchema):
    """Update a mission slot"""
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        from ninja.errors import HttpError
        raise HttpError(403, 'Insufficient permissions to update slots for this mission')
    
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    
    # Update fields if provided
    if data.title is not None:
        slot.title = data.title
    
    if data.description is not None:
        slot.description = data.description
    
    if data.detailedDescription is not None:
        slot.detailed_description = data.detailedDescription
    
    if data.requiredDLCs is not None:
        validate_dlc_list(data.requiredDLCs, 'requiredDLCs')
        slot.required_dlcs = data.requiredDLCs
    
    if data.restrictedCommunityUid is not None:
        restricted_community = get_object_or_404(Community, uid=data.restrictedCommunityUid)
        slot.restricted_community = restricted_community
    
    if data.blocked is not None:
        slot.blocked = data.blocked
    
    if data.reserve is not None:
        slot.reserve = data.reserve
    
    if data.autoAssignable is not None:
        slot.auto_assignable = data.autoAssignable
    
    if data.orderNumber is not None and data.orderNumber != slot.order_number:
        old_order = slot.order_number
        new_order = data.orderNumber
        
        # Shift other slots' order numbers within the same group
        if new_order > old_order:
            MissionSlot.objects.filter(
                slot_group=slot.slot_group,
                order_number__gt=old_order,
                order_number__lte=new_order
            ).update(order_number=models.F('order_number') - 1)
        else:
            MissionSlot.objects.filter(
                slot_group=slot.slot_group,
                order_number__gte=new_order,
                order_number__lt=old_order
            ).update(order_number=models.F('order_number') + 1)
        
        slot.order_number = new_order
    
    slot.save()
    
    return {
        'slot': {
            'uid': str(slot.uid),
            'slotGroupUid': str(slot.slot_group.uid),
            'title': slot.title,
            'description': slot.description,
            'detailedDescription': slot.detailed_description,
            'orderNumber': slot.order_number,
            'requiredDLCs': slot.required_dlcs,
            'blocked': slot.blocked,
            'reserve': slot.reserve,
            'autoAssignable': slot.auto_assignable
        }
    }


@router.delete('/{slug}/slots/{slot_uid}', response={200: dict, 403: dict, 404: dict})
def delete_mission_slot(request, slug: str, slot_uid: UUID):
    """Delete a mission slot"""
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        from ninja.errors import HttpError
        raise HttpError(403, 'Insufficient permissions to delete slots for this mission')
    
    slot = get_object_or_404(MissionSlot, uid=slot_uid, slot_group__mission=mission)
    deleted_order = slot.order_number
    slot_group = slot.slot_group
    
    # Delete the slot
    slot.delete()
    
    # Shift down the order numbers of slots that came after this one in the same group
    MissionSlot.objects.filter(
        slot_group=slot_group,
        order_number__gt=deleted_order
    ).update(order_number=models.F('order_number') - 1)
    
    return {'success': True}


@router.put('/{slug}/bannerImage', response={200: dict, 403: dict, 400: dict})
def upload_mission_banner_image(request, slug: str, payload: MissionBannerImageSchema):
    """Upload a banner image for a mission"""
    import base64
    import hashlib
    import os
    from django.conf import settings
    
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Insufficient permissions to upload banner for this mission'}
    
    try:
        # Decode base64 image
        image_data = base64.b64decode(payload.image)
        
        # Validate image type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        if payload.imageType not in allowed_types:
            return 400, {'detail': f'Invalid image type. Allowed: {", ".join(allowed_types)}'}
        
        # Generate filename based on mission slug and hash
        file_hash = hashlib.md5(image_data).hexdigest()[:8]
        extension = payload.imageType.split('/')[-1]
        if extension == 'jpeg':
            extension = 'jpg'
        filename = f"{slug}-{file_hash}.{extension}"
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'mission-banners')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # Update mission with new image URL
        # Construct URL based on MEDIA_URL setting
        image_url = f"{settings.MEDIA_URL}mission-banners/{filename}"
        mission.banner_image_url = image_url
        mission.save()
        
        return {
            'success': True,
            'imageUrl': image_url
        }
        
    except Exception as e:
        return 400, {'detail': f'Failed to upload image: {str(e)}'}


@router.delete('/{slug}/bannerImage', response={200: dict, 403: dict})
def delete_mission_banner_image(request, slug: str):
    """Delete the banner image for a mission"""
    import os
    from django.conf import settings
    
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Insufficient permissions to delete banner for this mission'}
    
    # Delete file if it exists
    if mission.banner_image_url:
        # Extract filename from URL
        filename = mission.banner_image_url.split('/')[-1]
        filepath = os.path.join(settings.MEDIA_ROOT, 'mission-banners', filename)
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                # Log but don't fail if file deletion fails
                print(f"Warning: Failed to delete file {filepath}: {e}")
    
    # Clear the URL from database
    mission.banner_image_url = None
    mission.save()
    
    return {'success': True}


@router.get('/{slug}/permissions', response={200: dict, 403: dict})
def get_mission_permissions(request, slug: str, limit: int = 10, offset: int = 0):
    """Get all permissions for a mission"""
    from api.models import Permission
    
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions - mission creator or admin can view
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == str(user_uid)
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Insufficient permissions to view mission permissions'}
    
    # Get all permissions for this mission
    mission_permissions = Permission.objects.filter(
        permission__startswith=f'mission.{slug}.'
    ).select_related('user')[offset:offset + limit]
    
    total = Permission.objects.filter(permission__startswith=f'mission.{slug}.').count()
    
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
            for perm in mission_permissions
        ],
        'total': total
    }


@router.post('/{slug}/permissions', response={200: dict, 403: dict, 400: dict})
def create_mission_permission(request, slug: str, payload: MissionPermissionCreateSchema):
    """Create a permission for a mission"""
    from api.models import Permission, User
    
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions - only mission creator or admin
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == str(user_uid)
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Insufficient permissions to create mission permissions'}
    
    # Get required fields
    target_user_uid = payload.userUid
    permission_str = payload.permission
    
    # Frontend sends full permission string like "mission.{slug}.editor"
    # Backend expects just the type, but we accept both formats
    if not permission_str.startswith('mission.'):
        # If it's just the type, construct full string
        permission_type = permission_str
        valid_types = ['editor', 'slotlist.community']
        if permission_type not in valid_types:
            return 400, {'detail': f'Invalid permission type. Valid: {", ".join(valid_types)}'}
        permission_str = f'mission.{slug}.{permission_type}'
    else:
        # Verify it's for the correct mission
        if not permission_str.startswith(f'mission.{slug}.'):
            return 400, {'detail': 'Permission does not match this mission'}
    
    target_user = get_object_or_404(User, uid=target_user_uid)
    
    # Check if permission already exists
    existing = Permission.objects.filter(
        user=target_user,
        permission=permission_str
    ).first()
    
    if existing:
        return 400, {'detail': 'Permission already exists'}
    
    # Create permission
    permission = Permission.objects.create(
        user=target_user,
        permission=permission_str
    )
    
    return {
        'permission': {
            'uid': permission.uid,
            'permission': permission.permission,
            'user': {
                'uid': target_user.uid,
                'nickname': target_user.nickname,
            }
        }
    }


@router.delete('/{slug}/permissions/{permission_uid}', response={200: dict, 403: dict})
def delete_mission_permission(request, slug: str, permission_uid: UUID):
    """Delete a permission for a mission"""
    from api.models import Permission
    
    mission = get_object_or_404(Mission, slug=slug)
    
    # Check permissions - only mission creator or admin
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(mission.creator.uid) == str(user_uid)
    is_admin = has_permission(permissions, 'admin.mission')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Insufficient permissions to delete mission permissions'}
    
    # Get the permission
    permission = get_object_or_404(Permission, uid=permission_uid)
    
    # Verify it belongs to this mission
    if not permission.permission.startswith(f'mission.{slug}.'):
        return 403, {'detail': 'Permission does not belong to this mission'}
    
    permission.delete()
    
    return {'success': True}



