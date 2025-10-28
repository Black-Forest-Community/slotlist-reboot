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
    MissionSchema, MissionCreateSchema, MissionUpdateSchema, 
    MissionSlotGroupCreateSchema, MissionSlotGroupUpdateSchema,
    MissionSlotCreateSchema, MissionSlotUpdateSchema
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


@router.get('/{slug}/slots', auth=None)
def get_mission_slots(request, slug: str):
    """Get all slots for a mission organized by slot groups"""
    mission = get_object_or_404(Mission.objects.select_related('creator', 'community'), slug=slug)
    
    # Get all slot groups with their slots for this mission
    slot_groups = MissionSlotGroup.objects.filter(mission=mission).prefetch_related(
        'slots__assignee',
        'slots__restricted_community',
        'slots__registrations'
    ).order_by('order_number')
    
    result = []
    for slot_group in slot_groups:
        slots = []
        for slot in slot_group.slots.order_by('order_number'):
            # Count pending registrations for this slot
            registration_count = slot.registrations.count()
            
            slot_data = {
                'uid': str(slot.uid),
                'title': slot.title,
                'description': slot.description,
                'detailedDescription': slot.detailed_description,
                'orderNumber': slot.order_number,
                'requiredDLCs': slot.required_dlcs,
                'externalAssignee': slot.external_assignee,
                'registrationCount': registration_count,
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


@router.get('/{slug}/slots/{slot_uid}/registrations')
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
                'confirmed': False,  # All existing registrations are pending (not confirmed)
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
            'confirmed': False,  # New registrations are pending
            'createdAt': registration.created_at.isoformat() if registration.created_at else None,
        }
    }


@router.patch('/{slug}/slots/{slot_uid}/registrations/{registration_uid}', response={200: dict, 400: dict, 403: dict})
def update_slot_registration(request, slug: str, slot_uid: UUID, registration_uid: UUID, data: SlotRegistrationUpdateSchema):
    """Update/confirm a slot registration (requires permissions)"""
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
        return 403, {'detail': 'Insufficient permissions to confirm registration'}
    
    # If confirmed, assign the slot to the user
    if data.confirmed:
        # Check if slot is already assigned
        if slot.assignee:
            return 400, {'detail': 'Slot is already assigned'}
        
        # Store registration info before deletion
        registration_user = registration.user
        registration_uid_str = str(registration.uid)
        registration_comment = registration.comment
        
        slot.assignee = registration_user
        slot.save()
        
        # Delete the registration after confirming
        registration.delete()
        
        return {
            'registration': {
                'uid': registration_uid_str,
                'user': {
                    'uid': str(registration_user.uid),
                    'nickname': registration_user.nickname,
                    'steamId': registration_user.steam_id,
                },
                'comment': registration_comment,
                'confirmed': True
            }
        }
    
    return {
        'registration': {
            'uid': str(registration.uid),
            'user': {
                'uid': str(registration.user.uid),
                'nickname': registration.user.nickname,
                'steamId': registration.user.steam_id,
            },
            'comment': registration.comment,
            'confirmed': False
        }
    }


@router.delete('/{slug}/slots/{slot_uid}/registrations/{registration_uid}', response={200: dict, 403: dict})
def delete_slot_registration(request, slug: str, slot_uid: UUID, registration_uid: UUID):
    """Delete/unregister from a slot"""
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
    
    registration.delete()
    
    return {'success': True}


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



