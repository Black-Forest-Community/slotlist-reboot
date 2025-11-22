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
    image_url: Optional[str] = None
    game_servers: Optional[List[Any]] = None
    voice_comms: Optional[List[Any]] = None
    repositories: Optional[List[Any]] = None


class UserSchema(Schema):
    uid: UUID
    nickname: str
    steam_id: Optional[str] = None
    community: Optional[CommunitySchema] = None
    active: Optional[bool] = None


class UserDetailSchema(UserSchema):
    missions: Optional[List['MissionSchema']] = []


class PermissionSchema(Schema):
    uid: UUID
    permission: str


class MissionSlotGroupSchema(Schema):
    uid: UUID
    title: str
    description: str
    order_number: int


class MissionSlotSchema(Schema):
    uid: UUID
    title: str
    description: str
    detailed_description: str
    order_number: int
    required_dlcs: Optional[List[str]] = None
    assignee: Optional[UserSchema] = None
    restricted_community: Optional[CommunitySchema] = None
    blocked: bool
    reserve: bool
    auto_assignable: bool


class MissionSlotRegistrationSchema(Schema):
    uid: UUID
    user: UserSchema
    slot: MissionSlotSchema
    comment: str


class MissionSchema(Schema):
    uid: UUID
    slug: str
    title: str
    description: str
    briefing_time: Optional[datetime] = None
    slot_list_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    visibility: str
    tech_teleport: bool
    tech_respawn: bool
    details_map: Optional[str] = None
    details_game_mode: Optional[str] = None
    details_required_dlcs: Optional[List[str]] = None
    game_server: Optional[Any] = None
    voice_comms: Optional[Any] = None
    repositories: Optional[List[Any]] = None
    rules_of_engagement: str
    image_url: Optional[str] = None
    creator: UserSchema
    community: Optional[CommunitySchema] = None


class MissionSlotTemplateSchema(Schema):
    uid: UUID
    title: str
    creator: UserSchema
    community: Optional[CommunitySchema] = None
    slot_groups: List[Any]


class MissionAccessSchema(Schema):
    uid: UUID
    mission: MissionSchema
    user: Optional[UserSchema] = None
    community: Optional[CommunitySchema] = None


class CommunityApplicationSchema(Schema):
    uid: UUID
    user: UserSchema
    community: CommunitySchema
    status: str
    application_text: str


class NotificationSchema(Schema):
    uid: UUID
    notification_type: str
    title: Optional[str] = None
    message: str
    additional_data: Optional[Any] = None
    read: bool
    created_at: datetime


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
