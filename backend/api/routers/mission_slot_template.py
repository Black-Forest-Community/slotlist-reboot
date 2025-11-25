from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from typing import Optional, Any, List as ListType
from uuid import UUID
from api.models import MissionSlotTemplate, User, Community
from api.schemas import MissionSlotTemplateListResponseSchema, MissionSlotTemplateDetailResponseSchema
from api.auth import has_permission

router = Router()


class MissionSlotTemplateCreateSchema(Schema):
    title: str
    slotGroups: ListType[Any]
    communityUid: Optional[UUID] = None


class MissionSlotTemplateUpdateSchema(Schema):
    title: Optional[str] = None
    slotGroups: Optional[ListType[Any]] = None
    communityUid: Optional[UUID] = None


@router.get('/', auth=None, response=MissionSlotTemplateListResponseSchema)
def list_mission_slot_templates(request, limit: int = 25, offset: int = 0):
    """List all mission slot templates with pagination"""
    total = MissionSlotTemplate.objects.count()
    templates = list(MissionSlotTemplate.objects.select_related('creator', 'community').all()[offset:offset + limit])
    
    return {
        'slot_templates': templates,
        'total': total
    }


@router.get('/{uid}', auth=None, response=MissionSlotTemplateDetailResponseSchema)
def get_mission_slot_template(request, uid: UUID):
    """Get a single mission slot template by UID"""
    template = get_object_or_404(MissionSlotTemplate.objects.select_related('creator', 'community'), uid=uid)
    
    # Ensure each slot group has a slots array
    slot_groups = template.slot_groups or []
    # Make a copy to avoid modifying the original
    slot_groups_copy = []
    for group in slot_groups:
        if isinstance(group, dict):
            # It's already a dict, ensure it has slots
            group_copy = dict(group)
            if 'slots' not in group_copy:
                group_copy['slots'] = []
            slot_groups_copy.append(group_copy)
        else:
            # Skip non-dict items
            continue
    
    # Set the processed slot_groups
    template._slot_groups_processed = slot_groups_copy
    
    return {'slot_template': template}


@router.post('/', response=MissionSlotTemplateDetailResponseSchema)
def create_mission_slot_template(request, payload: MissionSlotTemplateCreateSchema):
    """Create a new mission slot template"""
    if not request.auth:
        return 401, {'detail': 'Authentication required'}
    
    user_uid = request.auth.get('user', {}).get('uid')
    if not user_uid:
        return 401, {'detail': 'Invalid authentication'}
    
    user = get_object_or_404(User, uid=user_uid)
    
    community = None
    if payload.communityUid:
        community = get_object_or_404(Community, uid=payload.communityUid)
    
    template = MissionSlotTemplate.objects.create(
        title=payload.title,
        slot_groups=payload.slotGroups,
        creator=user,
        community=community
    )
    
    # Reload with related objects
    template = MissionSlotTemplate.objects.select_related('creator', 'community').get(uid=template.uid)
    
    return {'slot_template': template}


@router.delete('/{uid}')
def delete_mission_slot_template(request, uid: UUID):
    """Delete a mission slot template"""
    template = get_object_or_404(MissionSlotTemplate, uid=uid)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(template.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.slotTemplate')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Forbidden'}
    
    template.delete()
    return {'success': True}


@router.patch('/{uid}', response={200: MissionSlotTemplateDetailResponseSchema, 401: dict, 403: dict})
def update_mission_slot_template(request, uid: UUID, payload: MissionSlotTemplateUpdateSchema):
    """Update a mission slot template"""
    if not request.auth:
        return 401, {'detail': 'Authentication required'}
    
    template = get_object_or_404(MissionSlotTemplate, uid=uid)
    
    # Check permissions
    user_uid = request.auth.get('user', {}).get('uid')
    permissions = request.auth.get('permissions', [])
    
    is_creator = str(template.creator.uid) == user_uid
    is_admin = has_permission(permissions, 'admin.slotTemplate')
    
    if not is_creator and not is_admin:
        return 403, {'detail': 'Forbidden'}
    
    # Update fields
    if payload.title is not None:
        template.title = payload.title
    if payload.slotGroups is not None:
        template.slot_groups = payload.slotGroups
    if payload.communityUid is not None:
        community = get_object_or_404(Community, uid=payload.communityUid)
        template.community = community
    
    template.save()
    
    # Reload with related objects
    template = MissionSlotTemplate.objects.select_related('creator', 'community').get(uid=uid)
    
    return {'slot_template': template}
