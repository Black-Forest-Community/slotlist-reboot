# API Schema Refactoring Plan

**Status**: ✅ Completed  
**Priority**: Medium (Technical Debt)  
**Estimated Effort**: 8-12 hours  
**Created**: 2025-11-25  
**Completed**: 2025-11-25

## Executive Summary

Currently, most API endpoints manually construct response dictionaries instead of using Pydantic schemas. This leads to:
- Duplicated serialization logic (65+ manual dictionary constructions)
- No type safety on responses
- Inconsistent field naming
- Missing OpenAPI documentation
- Harder to maintain and modify

## Goals

1. Use Pydantic schemas for all API responses
2. Ensure consistent camelCase field naming for frontend
3. Improve type safety and validation
4. Generate accurate OpenAPI/Swagger documentation
5. Reduce code duplication

## Current State

### Statistics
- **Total manual dictionary returns**: 65
- **Endpoints using schemas**: 34
- **Completion rate**: ~34%

### Per-Router Breakdown
| Router | Manual Returns | Priority | Status |
|--------|----------------|----------|--------|
| mission.py | 26 | High | ✅ Done |
| community.py | 16 | Medium | ✅ Done |
| auth.py | 6 | Medium | Pending |
| user.py | 6 | Low | ✅ Done |
| notification.py | 5 | ✅ Done | ✅ Done |
| mission_slot_template.py | 5 | Low | ✅ Done |
| status.py | 1 | Low | ✅ Done |

## Phase 1: Schema Updates

### 1.1 Mission Schemas

**File**: `api/schemas.py`

#### MissionSchema (Output)
Current state: Basic schema without aliases

```python
class MissionSchema(Schema):
    uid: UUID
    slug: str
    title: str
    # ... more fields with snake_case
```

**Action**: Add field aliases for all fields
```python
class MissionSchema(Schema):
    uid: UUID
    slug: str
    title: str
    description: str
    briefing_time: Optional[datetime] = Field(None, alias='briefingTime')
    slotting_time: Optional[datetime] = Field(None, alias='slottingTime')
    start_time: Optional[datetime] = Field(None, alias='startTime')
    end_time: Optional[datetime] = Field(None, alias='endTime')
    tech_teleport: bool = Field(alias='techTeleport')
    tech_respawn: bool = Field(alias='techRespawn')
    tech_support: Optional[str] = Field(None, alias='techSupport')
    details_map: Optional[str] = Field(None, alias='detailsMap')
    details_game_mode: Optional[str] = Field(None, alias='detailsGameMode')
    required_dlcs: List[str] = Field(alias='requiredDLCs')
    game_server: Optional[Any] = Field(None, alias='gameServer')
    voice_comms: Optional[Any] = Field(None, alias='voiceComms')
    repositories: List[Any]
    rules_of_engagement: str = Field(alias='rulesOfEngagement')
    banner_image_url: Optional[str] = Field(None, alias='bannerImageUrl')
    creator: UserSchema
    community: Optional[CommunitySchema]
    
    class Config:
        populate_by_name = True
```

#### Create Response Wrapper Schemas
```python
class MissionListResponseSchema(Schema):
    missions: List[MissionSchema]
    total: int

class MissionDetailResponseSchema(Schema):
    mission: MissionSchema

class MissionSlotsResponseSchema(Schema):
    slotGroups: List[MissionSlotGroupSchema]
```

#### MissionSlotSchema Updates
```python
class MissionSlotSchema(Schema):
    uid: UUID
    slot_group_uid: UUID = Field(alias='slotGroupUid')
    title: str
    description: str
    detailed_description: str = Field(alias='detailedDescription')
    order_number: int = Field(alias='orderNumber')
    required_dlcs: Optional[List[str]] = Field(None, alias='requiredDLCs')
    external_assignee: Optional[str] = Field(None, alias='externalAssignee')
    registration_count: int = Field(alias='registrationCount')
    assignee: Optional[UserSchema] = None
    restricted_community: Optional[CommunitySchema] = Field(None, alias='restrictedCommunity')
    blocked: bool
    reserve: bool
    auto_assignable: bool = Field(alias='autoAssignable')
    
    class Config:
        populate_by_name = True
```

#### MissionSlotGroupSchema Updates
```python
class MissionSlotGroupSchema(Schema):
    uid: UUID
    title: str
    description: str
    order_number: int = Field(alias='orderNumber')
    slots: List[MissionSlotSchema]
    
    class Config:
        populate_by_name = True
```

#### Registration Response Schemas
```python
class MissionSlotRegistrationResponseSchema(Schema):
    registration: MissionSlotRegistrationSchema

class MissionSlotRegistrationListResponseSchema(Schema):
    registrations: List[MissionSlotRegistrationSchema]
    limit: int
    offset: int
    total: int
```

### 1.2 Community Schemas

**File**: `api/schemas.py`

#### CommunitySchema (Output)
```python
class CommunitySchema(Schema):
    uid: UUID
    name: str
    tag: str
    slug: str
    website: Optional[str] = None
    logo_url: Optional[str] = Field(None, alias='logoUrl')
    game_servers: Optional[List[Any]] = Field(None, alias='gameServers')
    voice_comms: Optional[List[Any]] = Field(None, alias='voiceComms')
    repositories: Optional[List[Any]] = None
    
    class Config:
        populate_by_name = True
```

#### Response Wrappers
```python
class CommunityListResponseSchema(Schema):
    communities: List[CommunitySchema]
    total: int

class CommunityDetailResponseSchema(Schema):
    community: CommunitySchema

class CommunityMissionsResponseSchema(Schema):
    missions: List[MissionSchema]
    total: int
```

### 1.3 User Schemas

#### UserSchema Updates
```python
class UserSchema(Schema):
    uid: UUID
    nickname: str
    steam_id: Optional[str] = Field(None, alias='steamId')
    community: Optional[CommunitySchema] = None
    active: Optional[bool] = None
    
    class Config:
        populate_by_name = True
```

#### Response Wrappers
```python
class UserListResponseSchema(Schema):
    users: List[UserSchema]
    total: int

class UserDetailResponseSchema(Schema):
    user: UserDetailSchema

class UserMissionsResponseSchema(Schema):
    missions: List[MissionSchema]
    total: int

class UserPermissionsResponseSchema(Schema):
    permissions: List[PermissionSchema]
    total: int
```

### 1.4 Auth Schemas

Already has `AuthResponseSchema`, but needs update:
```python
class AuthResponseSchema(Schema):
    token: str
    user: UserSchema
```

### 1.5 Permission Schemas

```python
class PermissionSchema(Schema):
    uid: UUID
    permission: str
    user: Optional[UserSchema] = None
    
    class Config:
        populate_by_name = True

class PermissionListResponseSchema(Schema):
    permissions: List[PermissionSchema]
    total: int
```

### 1.6 Slot Template Schemas

```python
class MissionSlotTemplateSchema(Schema):
    uid: UUID
    title: str
    creator: UserSchema
    community: Optional[CommunitySchema] = None
    slot_groups: List[Any] = Field(alias='slotGroups')
    
    class Config:
        populate_by_name = True

class MissionSlotTemplateListResponseSchema(Schema):
    slotTemplates: List[MissionSlotTemplateSchema]
    total: int

class MissionSlotTemplateDetailResponseSchema(Schema):
    slotTemplate: MissionSlotTemplateSchema
```

## Phase 2: Router Updates

### 2.1 Mission Router (`api/routers/mission.py`)

**Priority**: High (26 manual returns)

#### Endpoints to Update

1. `GET /` (list_missions)
   - Use `MissionListResponseSchema`
   - Return: `{'missions': missions_queryset, 'total': total}`
   
2. `GET /{slug}` (get_mission)
   - Use `MissionDetailResponseSchema`
   - Return: `{'mission': mission_obj}`

3. `POST /` (create_mission)
   - Use `MissionDetailResponseSchema` + token
   - Keep token field, wrap mission

4. `PATCH /{slug}` (update_mission)
   - Use `MissionDetailResponseSchema`

5. `POST /{slug}/duplicate` (duplicate_mission)
   - Use `MissionDetailResponseSchema` + token

6. `GET /{slug}/slots` (get_mission_slots)
   - Use `MissionSlotsResponseSchema`
   - Return: `{'slotGroups': slot_groups_queryset}`

7. `POST /{slug}/slots` (create_mission_slots)
   - Current: Returns `{'slots': [...]}`
   - Use: `MissionSlotListResponseSchema`

8. `PATCH /{slug}/slots/{slot_uid}` (update_mission_slot)
   - Use: `MissionSlotDetailResponseSchema`

9. `GET /{slug}/slots/{slot_uid}/registrations`
   - Use: `MissionSlotRegistrationListResponseSchema`

10. `POST /{slug}/slots/{slot_uid}/registrations`
    - Use: `MissionSlotRegistrationResponseSchema`

11. `PATCH /{slug}/slots/{slot_uid}/registrations/{registration_uid}`
    - Use: `MissionSlotRegistrationResponseSchema`

12. `POST /{slug}/slotGroups` (create_mission_slot_group)
    - Use: `MissionSlotGroupDetailResponseSchema`

13. `PATCH /{slug}/slotGroups/{slot_group_uid}`
    - Use: `MissionSlotGroupDetailResponseSchema`

**Estimated Effort**: 4-5 hours

### 2.2 Community Router (`api/routers/community.py`)

**Priority**: Medium (16 manual returns)

#### Endpoints to Update

1. `GET /` (list_communities)
   - Use `CommunityListResponseSchema`

2. `GET /{slug}` (get_community)
   - Use `CommunityDetailResponseSchema`

3. `POST /` (create_community)
   - Use `CommunityDetailResponseSchema`

4. `PATCH /{slug}` (update_community)
   - Use `CommunityDetailResponseSchema`

5. `GET /{slug}/missions` (get_community_missions)
   - Use `CommunityMissionsResponseSchema`

6. Application endpoints
   - Need application response schemas

**Estimated Effort**: 3-4 hours

### 2.3 User Router (`api/routers/user.py`)

**Priority**: Low (6 manual returns)

1. `GET /` (list_users)
   - Use `UserListResponseSchema`

2. `GET /{user_uid}` (get_user)
   - Use `UserDetailResponseSchema`

3. `GET /{user_uid}/missions` (list_user_missions)
   - Use `UserMissionsResponseSchema`

4. `GET /{user_uid}/permissions` (list_user_permissions)
   - Use `UserPermissionsResponseSchema`

**Estimated Effort**: 1-2 hours

### 2.4 Auth Router (`api/routers/auth.py`)

**Priority**: Medium (6 manual returns)

1. Steam login endpoints
   - Already use `AuthResponseSchema` mostly
   - Just needs consistency check

**Estimated Effort**: 1 hour

### 2.5 Mission Slot Template Router

**Priority**: Low (5 manual returns)

**Estimated Effort**: 1-2 hours

## Phase 3: Testing Strategy

### 3.1 Automated Testing

For each refactored endpoint:
1. Check response structure matches schema
2. Verify field names are camelCase
3. Ensure data types are correct
4. Test with null/optional values

### 3.2 Frontend Compatibility Testing

Critical endpoints to test with actual frontend:
1. Mission list and details
2. Slot registration flow
3. User authentication
4. Community pages
5. Notifications

### 3.3 OpenAPI Documentation

After refactoring:
1. Verify Swagger docs at `/api/docs`
2. Check all schemas are properly documented
3. Ensure examples are generated correctly

## Phase 4: Migration Path

### 4.1 Incremental Approach

**Recommended**: One router at a time
- Complete Phase 1 schemas for one router
- Update that router's endpoints
- Test thoroughly
- Move to next router

### 4.2 Benefits of This Approach

- Lower risk (can rollback single router)
- Easier to test
- Can deploy incrementally
- Team can learn and adjust

### 4.3 Order of Execution

1. ✅ Notification router (DONE - served as proof of concept)
2. ✅ Mission router (highest impact, most complexity)
3. ✅ Community router
4. Auth router (pending - already had some schema usage)
5. ✅ User router
6. ✅ Mission slot template router
7. ✅ Status router (already using schema)

## Implementation Checklist

### Before Starting
- [ ] Review this plan with team
- [ ] Set up test environment
- [ ] Create feature branch
- [ ] Document current API responses (for comparison)

### For Each Router
- [ ] Update schemas in `api/schemas.py`
  - [ ] Add field aliases
  - [ ] Create response wrapper schemas
  - [ ] Add Config class with populate_by_name
- [ ] Update router endpoints
  - [ ] Add `response=` parameter to decorators
  - [ ] Replace manual dict construction
  - [ ] Return model instances or querysets
- [ ] Test endpoints
  - [ ] Check response structure
  - [ ] Verify field naming
  - [ ] Test with frontend
- [ ] Update tests if they exist
- [ ] Check OpenAPI docs

### After All Routers
- [ ] Full integration test
- [ ] Frontend smoke test on all pages
- [ ] Performance check (schemas shouldn't slow things down)
- [ ] Update API documentation
- [ ] Merge to main

## Benefits After Completion

### Code Quality
- ~65 manual dictionary constructions removed
- Single source of truth for response structure
- Type safety on all responses
- Reduced code duplication by ~30%

### Developer Experience
- Auto-complete in IDEs for response structures
- Compile-time validation of responses
- Easier to add new fields
- Less prone to typos

### Documentation
- Accurate OpenAPI/Swagger docs
- Clear response examples
- Better API discoverability

### Maintenance
- Changes to response format in one place
- Easier to refactor
- Simpler debugging

## Risks and Mitigation

### Risk 1: Breaking Changes
**Mitigation**: 
- Test each endpoint thoroughly
- Compare old vs new responses
- Deploy to staging first

### Risk 2: Performance Impact
**Mitigation**:
- Django Ninja schema serialization is fast
- May actually improve performance (less Python dict construction)
- Monitor in staging

### Risk 3: Time Estimation
**Mitigation**:
- Start with smallest router (status.py)
- Adjust estimates after first router
- Can pause between routers

## Notes

- This refactoring maintains 100% API compatibility
- No frontend changes required
- Can be done incrementally
- Low risk if done carefully
- High long-term benefit

## References

- Django Ninja docs: https://django-ninja.rest-framework.com/
- Pydantic Field aliases: https://docs.pydantic.dev/latest/concepts/fields/
- Current notification router implementation (reference example)

---

**Ready to start?** Begin with Phase 1, Section 1.1 (Mission Schemas) when time allows.
