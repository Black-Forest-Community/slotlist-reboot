from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from ninja import Schema, Field


class CommunitySchema(Schema):
    uid: UUID
    name: str
    tag: str
    slug: str
    website: Optional[str] = None
    logo_url: Optional[str] = Field(None, alias='logoUrl', serialization_alias='logoUrl')
    game_servers: Optional[List[Any]] = Field(None, alias='gameServers', serialization_alias='gameServers')
    voice_comms: Optional[List[Any]] = Field(None, alias='voiceComms', serialization_alias='voiceComms')
    repositories: Optional[List[Any]] = None
    
    class Config:
        populate_by_name = True
        from_attributes = True


class UserSchema(Schema):
    uid: UUID
    nickname: str
    steam_id: Optional[str] = Field(None, alias='steamId', serialization_alias='steamId')
    community: Optional[CommunitySchema] = None
    active: Optional[bool] = None
    
    class Config:
        populate_by_name = True
        from_attributes = True


class UserDetailSchema(UserSchema):
    missions: Optional[List['MissionSchema']] = []


class PermissionSchema(Schema):
    uid: UUID
    permission: str
    
    class Config:
        populate_by_name = True
        from_attributes = True


class MissionSlotGroupSchema(Schema):
    uid: UUID
    title: str
    description: str = ''
    order_number: int = Field(alias='orderNumber', serialization_alias='orderNumber')
    
    class Config:
        populate_by_name = True
        from_attributes = True


class MissionSlotSchema(Schema):
    uid: UUID
    slot_group_uid: UUID = Field(alias='slotGroupUid', serialization_alias='slotGroupUid')
    title: str
    description: str = ''
    detailed_description: str = Field('', alias='detailedDescription', serialization_alias='detailedDescription')
    order_number: int = Field(alias='orderNumber', serialization_alias='orderNumber')
    required_dlcs: Optional[List[str]] = Field(None, alias='requiredDLCs', serialization_alias='requiredDLCs')
    external_assignee: Optional[str] = Field(None, alias='externalAssignee', serialization_alias='externalAssignee')
    registration_count: int = Field(0, alias='registrationCount', serialization_alias='registrationCount')
    assignee: Optional[UserSchema] = None
    restricted_community: Optional[CommunitySchema] = Field(None, alias='restrictedCommunity', serialization_alias='restrictedCommunity')
    blocked: bool = False
    reserve: bool = False
    auto_assignable: bool = Field(True, alias='autoAssignable', serialization_alias='autoAssignable')
    
    class Config:
        populate_by_name = True
        from_attributes = True
    
    @staticmethod
    def resolve_slot_group_uid(obj):
        """Resolve slot_group_uid from the slot_group relation"""
        if hasattr(obj, 'slot_group') and obj.slot_group:
            return obj.slot_group.uid
        return getattr(obj, 'slot_group_uid', None)
    
    @staticmethod
    def resolve_registration_count(obj):
        """Resolve registration_count from registrations relation"""
        # Check if it's already set as an attribute (e.g., from annotation)
        if hasattr(obj, '_registration_count'):
            return obj._registration_count
        # Otherwise count pending registrations
        if hasattr(obj, 'registrations'):
            return obj.registrations.filter(status='pending').count()
        return 0


class MissionSlotRegistrationSchema(Schema):
    uid: UUID
    slot_uid: UUID = Field(alias='slotUid', serialization_alias='slotUid')
    user: UserSchema
    comment: Optional[str] = None
    status: str
    confirmed: bool = False
    created_at: Optional[datetime] = Field(None, alias='createdAt', serialization_alias='createdAt')
    
    class Config:
        populate_by_name = True
        from_attributes = True
    
    @staticmethod
    def resolve_slot_uid(obj):
        """Resolve slot_uid from the slot relation"""
        if hasattr(obj, 'slot') and obj.slot:
            return obj.slot.uid
        return getattr(obj, 'slot_uid', None)
    
    @staticmethod
    def resolve_confirmed(obj):
        """Resolve confirmed from status"""
        return getattr(obj, 'status', '') == 'confirmed'


class MissionSchema(Schema):
    uid: UUID
    slug: str
    title: str
    description: str
    detailed_description: str = Field('', alias='detailedDescription', serialization_alias='detailedDescription')
    collapsed_description: Optional[str] = Field(None, alias='collapsedDescription', serialization_alias='collapsedDescription')
    briefing_time: Optional[datetime] = Field(None, alias='briefingTime', serialization_alias='briefingTime')
    slotting_time: Optional[datetime] = Field(None, alias='slottingTime', serialization_alias='slottingTime')
    start_time: Optional[datetime] = Field(None, alias='startTime', serialization_alias='startTime')
    end_time: Optional[datetime] = Field(None, alias='endTime', serialization_alias='endTime')
    visibility: str
    tech_teleport: bool = Field(False, alias='techTeleport', serialization_alias='techTeleport')
    tech_respawn: bool = Field(False, alias='techRespawn', serialization_alias='techRespawn')
    tech_support: Optional[str] = Field(None, alias='techSupport', serialization_alias='techSupport')
    details_map: Optional[str] = Field(None, alias='detailsMap', serialization_alias='detailsMap')
    details_game_mode: Optional[str] = Field(None, alias='detailsGameMode', serialization_alias='detailsGameMode')
    required_dlcs: Optional[List[str]] = Field(None, alias='requiredDLCs', serialization_alias='requiredDLCs')
    game_server: Optional[Any] = Field(None, alias='gameServer', serialization_alias='gameServer')
    voice_comms: Optional[Any] = Field(None, alias='voiceComms', serialization_alias='voiceComms')
    repositories: Optional[List[Any]] = None
    rules_of_engagement: str = Field('', alias='rulesOfEngagement', serialization_alias='rulesOfEngagement')
    banner_image_url: Optional[str] = Field(None, alias='bannerImageUrl', serialization_alias='bannerImageUrl')
    creator: UserSchema
    community: Optional[CommunitySchema] = None
    
    class Config:
        populate_by_name = True
        from_attributes = True
    
    @staticmethod
    def resolve_tech_teleport(obj):
        """Compute tech_teleport from tech_support string"""
        tech_support = getattr(obj, 'tech_support', None)
        if tech_support and isinstance(tech_support, str):
            return 'teleport' in tech_support.lower()
        return False
    
    @staticmethod
    def resolve_tech_respawn(obj):
        """Compute tech_respawn from tech_support string"""
        tech_support = getattr(obj, 'tech_support', None)
        if tech_support and isinstance(tech_support, str):
            return 'respawn' in tech_support.lower()
        return False
    
    @staticmethod
    def resolve_rules_of_engagement(obj):
        """Map rules field to rules_of_engagement"""
        return getattr(obj, 'rules', '') or ''


# Mission Response Schemas
class MissionDetailResponseSchema(Schema):
    mission: MissionSchema


class MissionCreateResponseSchema(Schema):
    """Response schema for mission creation (includes token)"""
    token: str
    mission: MissionSchema


class MissionListItemSchema(Schema):
    """Simplified mission schema for list view with slot counts"""
    uid: UUID
    slug: str
    title: str
    description: str
    briefing_time: Optional[datetime] = Field(None, alias='briefingTime', serialization_alias='briefingTime')
    slotting_time: Optional[datetime] = Field(None, alias='slottingTime', serialization_alias='slottingTime')
    start_time: Optional[datetime] = Field(None, alias='startTime', serialization_alias='startTime')
    end_time: Optional[datetime] = Field(None, alias='endTime', serialization_alias='endTime')
    visibility: str
    details_map: Optional[str] = Field(None, alias='detailsMap', serialization_alias='detailsMap')
    details_game_mode: Optional[str] = Field(None, alias='detailsGameMode', serialization_alias='detailsGameMode')
    required_dlcs: Optional[List[str]] = Field(None, alias='requiredDLCs', serialization_alias='requiredDLCs')
    banner_image_url: Optional[str] = Field(None, alias='bannerImageUrl', serialization_alias='bannerImageUrl')
    creator: UserSchema
    community: Optional[CommunitySchema] = None
    slot_counts: Optional[dict] = Field(None, alias='slotCounts', serialization_alias='slotCounts')
    is_assigned_to_any_slot: Optional[bool] = Field(False, alias='isAssignedToAnySlot', serialization_alias='isAssignedToAnySlot')
    is_registered_for_any_slot: Optional[bool] = Field(False, alias='isRegisteredForAnySlot', serialization_alias='isRegisteredForAnySlot')
    
    class Config:
        populate_by_name = True
        from_attributes = True


class MissionListResponseSchema(Schema):
    """Response schema for mission list"""
    missions: List[MissionListItemSchema]
    total: int


class MissionSlotGroupWithSlotsSchema(MissionSlotGroupSchema):
    slots: List[MissionSlotSchema]


class MissionSlotsResponseSchema(Schema):
    slot_groups: List[MissionSlotGroupWithSlotsSchema] = Field(alias='slotGroups', serialization_alias='slotGroups')


class MissionSlotGroupDetailResponseSchema(Schema):
    slot_group: MissionSlotGroupWithSlotsSchema = Field(alias='slotGroup', serialization_alias='slotGroup')


class MissionSlotListResponseSchema(Schema):
    slots: List[MissionSlotSchema]


class MissionSlotDetailResponseSchema(Schema):
    slot: MissionSlotSchema


class MissionSlotRegistrationResponseSchema(Schema):
    registration: MissionSlotRegistrationSchema


class MissionSlotRegistrationListResponseSchema(Schema):
    registrations: List[MissionSlotRegistrationSchema]
    limit: int
    offset: int
    total: int


class MissionSlotTemplateSchema(Schema):
    uid: UUID
    title: str
    creator: UserSchema
    community: Optional[CommunitySchema] = None
    slot_groups: List[Any] = Field(default_factory=list, alias='slotGroups', serialization_alias='slotGroups')
    created_at: Optional[datetime] = Field(None, alias='createdAt', serialization_alias='createdAt')
    updated_at: Optional[datetime] = Field(None, alias='updatedAt', serialization_alias='updatedAt')
    
    class Config:
        populate_by_name = True
        from_attributes = True


class MissionSlotTemplateListResponseSchema(Schema):
    slot_templates: List[MissionSlotTemplateSchema] = Field(alias='slotTemplates', serialization_alias='slotTemplates')
    total: int


class MissionSlotTemplateDetailResponseSchema(Schema):
    slot_template: MissionSlotTemplateSchema = Field(alias='slotTemplate', serialization_alias='slotTemplate')


class MissionAccessSchema(Schema):
    uid: UUID
    mission: MissionSchema
    user: Optional[UserSchema] = None
    community: Optional[CommunitySchema] = None
    
    class Config:
        populate_by_name = True
        from_attributes = True


class CommunityApplicationSchema(Schema):
    uid: UUID
    user: UserSchema
    community: CommunitySchema
    status: str
    created_at: Optional[datetime] = Field(None, alias='createdAt', serialization_alias='createdAt')
    updated_at: Optional[datetime] = Field(None, alias='updatedAt', serialization_alias='updatedAt')
    
    class Config:
        populate_by_name = True
        from_attributes = True


class CommunityApplicationResponseSchema(Schema):
    application: CommunityApplicationSchema


class CommunityApplicationListResponseSchema(Schema):
    applications: List[CommunityApplicationSchema]
    total: int


class CommunityWithMembersSchema(CommunitySchema):
    """Extended community schema with members and leaders"""
    members: Optional[List[UserSchema]] = []
    leaders: Optional[List[UserSchema]] = []


class CommunityDetailResponseSchema(Schema):
    community: CommunityWithMembersSchema


class CommunityListResponseSchema(Schema):
    communities: List[CommunitySchema]
    total: int


class CommunityMissionsResponseSchema(Schema):
    missions: List[MissionListItemSchema]
    total: int


class PermissionWithUserSchema(PermissionSchema):
    """Permission schema with user details"""
    user: Optional[UserSchema] = None


class PermissionResponseSchema(Schema):
    permission: PermissionWithUserSchema


class PermissionListResponseSchema(Schema):
    permissions: List[PermissionWithUserSchema]
    total: int


class UserWithDetailsSchema(UserSchema):
    """Extended user schema with missions and permissions"""
    missions: Optional[List[MissionListItemSchema]] = []
    permissions: Optional[List[PermissionSchema]] = []


class UserDetailResponseSchema(Schema):
    user: UserWithDetailsSchema


class UserListResponseSchema(Schema):
    users: List[UserSchema]
    limit: int
    offset: int
    count: int
    total: int
    more_available: bool = Field(alias='moreAvailable', serialization_alias='moreAvailable')


class UserMissionsResponseSchema(Schema):
    missions: List[MissionListItemSchema]
    limit: int
    offset: int
    count: int
    total: int
    more_available: bool = Field(alias='moreAvailable', serialization_alias='moreAvailable')


class NotificationSchema(Schema):
    uid: UUID
    notification_type: str = Field(..., alias='notificationType', serialization_alias='notificationType')
    title: Optional[str] = None
    message: str
    additional_data: Optional[Any] = Field(None, alias='additionalData', serialization_alias='additionalData')
    read: bool
    created_at: datetime = Field(..., alias='createdAt', serialization_alias='createdAt')
    
    class Config:
        populate_by_name = True
        from_attributes = True


class NotificationListResponseSchema(Schema):
    notifications: List['NotificationSchema']
    limit: int
    offset: int
    total: int


class NotificationDetailResponseSchema(Schema):
    notification: NotificationSchema


# Input Schemas for creating/updating
class MissionCreateSchema(Schema):
    title: str
    slug: Optional[str] = None
    description: Optional[str] = ''
    detailed_description: Optional[str] = Field('', alias='detailedDescription')
    collapsed_description: Optional[str] = Field(None, alias='collapsedDescription')
    briefing_time: Optional[datetime] = Field(None, alias='briefingTime')
    slotting_time: Optional[datetime] = Field(None, alias='slottingTime')
    start_time: Optional[datetime] = Field(None, alias='startTime')
    end_time: Optional[datetime] = Field(None, alias='endTime')
    visibility: str = 'hidden'
    tech_teleport: bool = Field(False, alias='techTeleport')
    tech_respawn: bool = Field(False, alias='techRespawn')
    details_map: Optional[str] = Field(None, alias='detailsMap')
    details_game_mode: Optional[str] = Field(None, alias='detailsGameMode')
    required_dlcs: Optional[List[str]] = Field(None, alias='requiredDLCs')
    game_server: Optional[Any] = Field(None, alias='gameServer')
    voice_comms: Optional[Any] = Field(None, alias='voiceComms')
    repositories: Optional[List[Any]] = None
    rules_of_engagement: Optional[str] = Field('', alias='rulesOfEngagement')
    community_uid: Optional[UUID] = None
    
    class Config:
        populate_by_name = True


class MissionUpdateSchema(Schema):
    title: Optional[str] = None
    description: Optional[str] = None
    detailed_description: Optional[str] = Field(None, alias='detailedDescription')
    collapsed_description: Optional[str] = Field(None, alias='collapsedDescription')
    briefing_time: Optional[datetime] = Field(None, alias='briefingTime')
    slotting_time: Optional[datetime] = Field(None, alias='slottingTime')
    start_time: Optional[datetime] = Field(None, alias='startTime')
    end_time: Optional[datetime] = Field(None, alias='endTime')
    visibility: Optional[str] = None
    tech_support: Optional[str] = Field(None, alias='techSupport')
    tech_teleport: Optional[bool] = Field(None, alias='techTeleport')
    tech_respawn: Optional[bool] = Field(None, alias='techRespawn')
    details_map: Optional[str] = Field(None, alias='detailsMap')
    details_game_mode: Optional[str] = Field(None, alias='detailsGameMode')
    required_dlcs: Optional[List[str]] = Field(None, alias='requiredDLCs')
    game_server: Optional[Any] = Field(None, alias='gameServer')
    voice_comms: Optional[Any] = Field(None, alias='voiceComms')
    repositories: Optional[List[Any]] = None
    rules_of_engagement: Optional[str] = Field(None, alias='rulesOfEngagement')
    
    class Config:
        populate_by_name = True


class MissionDuplicateSchema(Schema):
    slug: str
    title: Optional[str] = None
    briefing_time: Optional[datetime] = Field(None, alias='briefingTime')
    slotting_time: Optional[datetime] = Field(None, alias='slottingTime')
    start_time: Optional[datetime] = Field(None, alias='startTime')
    end_time: Optional[datetime] = Field(None, alias='endTime')
    visibility: Optional[str] = 'hidden'
    add_to_community: Optional[bool] = Field(False, alias='addToCommunity')
    
    class Config:
        populate_by_name = True


class UserUpdateSchema(Schema):
    nickname: Optional[str] = None


class CommunityCreateSchema(Schema):
    name: str
    tag: str
    website: Optional[str] = None
    game_servers: Optional[List[Any]] = None
    voice_comms: Optional[List[Any]] = None
    repositories: Optional[List[Any]] = None


class CommunityUpdateSchema(Schema):
    name: Optional[str] = None
    tag: Optional[str] = None
    website: Optional[str] = None
    game_servers: Optional[List[Any]] = None
    voice_comms: Optional[List[Any]] = None
    repositories: Optional[List[Any]] = None


class AuthResponseSchema(Schema):
    token: str
    user: UserSchema


class ErrorResponseSchema(Schema):
    detail: str


class StatusResponseSchema(Schema):
    status: str
    uptime: Optional[int] = None
    version: str


# Mission import schemas
class MissionImportRequestSchema(Schema):
    slug: str = Field(..., description="Mission slug to import from slotlist.info")
    creator_uid: Optional[UUID] = Field(None, description="Optional UUID of the user to set as mission creator. If not provided, uses original creator from API.")
    dry_run: bool = Field(False, description="Preview import without saving")


class MissionImportPreviewSlotSchema(Schema):
    title: str
    assignee: str


class MissionImportPreviewSlotGroupSchema(Schema):
    title: str
    slot_count: int
    slots: List[MissionImportPreviewSlotSchema]


class MissionImportPreviewMissionSchema(Schema):
    title: str
    slug: str
    description: str
    visibility: str
    community: dict


class MissionImportPreviewSchema(Schema):
    mission: MissionImportPreviewMissionSchema
    slot_groups: List[MissionImportPreviewSlotGroupSchema]
    totals: dict


class MissionImportSuccessSchema(Schema):
    success: bool
    message: str
    mission_uid: UUID
    mission_slug: str
    mission_title: str


class MissionImportResponseSchema(Schema):
    """Response can be either preview or success"""
    preview: Optional[MissionImportPreviewSchema] = None
    success: Optional[bool] = None
    message: Optional[str] = None
    mission_uid: Optional[UUID] = None
    mission_slug: Optional[str] = None
    mission_title: Optional[str] = None


class MissionSlotGroupCreateSchema(Schema):
    title: str
    description: Optional[str] = None
    insertAfter: int = 0


class MissionSlotGroupUpdateSchema(Schema):
    title: Optional[str] = None
    description: Optional[str] = None
    orderNumber: Optional[int] = None


class MissionSlotCreateSchema(Schema):
    title: str
    description: Optional[str] = None
    detailedDescription: Optional[str] = None
    slotGroupUid: UUID
    requiredDLCs: Optional[List[str]] = []
    restrictedCommunityUid: Optional[UUID] = None
    blocked: bool = False
    reserve: bool = False
    autoAssignable: bool = True
    insertAfter: int = 0
    duplicate: Optional[bool] = None  # Frontend sends this flag when duplicating, we can ignore it


class MissionSlotUpdateSchema(Schema):
    title: Optional[str] = None
    description: Optional[str] = None
    detailedDescription: Optional[str] = None
    orderNumber: Optional[int] = None
    requiredDLCs: Optional[List[str]] = None
    restrictedCommunityUid: Optional[UUID] = None
    blocked: Optional[bool] = None
    reserve: Optional[bool] = None
    autoAssignable: Optional[bool] = None


class CommunityApplicationStatusSchema(Schema):
    status: str  # 'accepted' or 'denied'


class CommunityPermissionCreateSchema(Schema):
    userUid: UUID
    permission: str


class MissionBannerImageSchema(Schema):
    imageType: str
    image: str  # Base64 encoded image data


class MissionSlotAssignSchema(Schema):
    userUid: UUID
    force: Optional[bool] = False
    suppressNotifications: Optional[bool] = False


class MissionPermissionCreateSchema(Schema):
    userUid: UUID
    permission: str  # 'editor' or 'slotlist.community'
    suppressNotifications: Optional[bool] = False
