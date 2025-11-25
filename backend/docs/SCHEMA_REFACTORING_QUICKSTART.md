# Schema Refactoring Quick Start

This is a condensed guide for when you're ready to start the refactoring outlined in `SCHEMA_REFACTORING_PLAN.md`.

## Quick Reference

**Total Work**: ~8-12 hours  
**Approach**: Incremental, one router at a time  
**Status**: ✅ Notification router done (proof of concept)

## Start Here: Mission Router (Highest Priority)

### Step 1: Update Schemas (30 min)

Open `api/schemas.py` and update `MissionSchema`:

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
    # ... add all fields with proper aliases
    
    class Config:
        populate_by_name = True
```

Add response wrappers:
```python
class MissionListResponseSchema(Schema):
    missions: List[MissionSchema]
    total: int

class MissionDetailResponseSchema(Schema):
    mission: MissionSchema
```

### Step 2: Update First Endpoint (15 min)

Start with `get_mission` in `api/routers/mission.py`:

**Before:**
```python
@router.get('/{slug}', auth=None)
def get_mission(request, slug: str):
    mission = get_object_or_404(Mission, slug=slug)
    return {
        'mission': {
            'uid': mission.uid,
            'slug': mission.slug,
            # ... 30+ lines of manual mapping
        }
    }
```

**After:**
```python
@router.get('/{slug}', auth=None, response=MissionDetailResponseSchema)
def get_mission(request, slug: str):
    mission = get_object_or_404(Mission, slug=slug)
    return {'mission': mission}
```

### Step 3: Test (10 min)

```bash
# In Docker
docker compose exec backend python manage.py shell

# Test the endpoint
from api.routers.mission import router
# ... manual testing

# Or test with curl
curl http://localhost:8022/api/v1/missions/some-mission-slug
```

### Step 4: Repeat for Other Endpoints

Use this pattern for each endpoint:
1. Add/update schema
2. Change endpoint to use `response=Schema`
3. Replace manual dict with model instance
4. Test

## Common Patterns

### Pattern 1: Single Object Response
```python
@router.get('/{id}', response=ItemDetailResponseSchema)
def get_item(request, id: int):
    item = get_object_or_404(Item, id=id)
    return {'item': item}  # Schema handles serialization
```

### Pattern 2: List Response
```python
@router.get('/', response=ItemListResponseSchema)
def list_items(request, limit: int = 25, offset: int = 0):
    total = Item.objects.count()
    items = Item.objects.all()[offset:offset+limit]
    return {
        'items': items,
        'total': total,
        'limit': limit,
        'offset': offset
    }
```

### Pattern 3: Nested Objects
Django Ninja handles relationships automatically:
```python
class MissionSchema(Schema):
    creator: UserSchema  # Automatically serializes related user
    community: Optional[CommunitySchema]
```

## Field Alias Cheat Sheet

Common snake_case → camelCase conversions:
- `created_at` → `createdAt`
- `updated_at` → `updatedAt`
- `user_uid` → `userUid`
- `slot_group_uid` → `slotGroupUid`
- `banner_image_url` → `bannerImageUrl`
- `briefing_time` → `briefingTime`
- `tech_support` → `techSupport`
- `required_dlcs` → `requiredDLCs`

## Testing Checklist

For each refactored endpoint:
- [ ] Response structure matches old format
- [ ] All fields present
- [ ] Correct camelCase naming
- [ ] Null values handled correctly
- [ ] Frontend still works
- [ ] OpenAPI docs updated

## Troubleshooting

### "Field X not in response"
- Check if field alias is correct
- Ensure `Config.populate_by_name = True`
- Verify model has the field

### "Cannot serialize X"
- Add schema for nested object
- Use `Optional[Schema]` for nullable relations
- Check if datetime fields need special handling

### "Frontend getting wrong field names"
- Verify Field alias matches frontend expectation
- Check if old manual dict had different naming

## Next Steps After Mission Router

1. Community router (16 endpoints)
2. Auth router (6 endpoints)  
3. User router (6 endpoints)
4. Mission slot template router (5 endpoints)
5. Status router (1 endpoint)

## Time Estimates Per Router

- Mission: 4-5 hours (complex, many endpoints)
- Community: 3-4 hours
- Auth: 1 hour
- User: 1-2 hours
- Others: <1 hour each

## Commit Strategy

Option A: One commit per router
```
feat: refactor mission router to use Pydantic schemas
feat: refactor community router to use Pydantic schemas
```

Option B: One commit per endpoint (more granular)
```
feat: use schema for GET /missions/{slug}
feat: use schema for GET /missions
```

**Recommended**: Option A (easier to review, test, and rollback)

## Ready to Start?

1. Create feature branch: `git checkout -b refactor/api-schemas`
2. Open `backend/api/schemas.py`
3. Start with Mission schemas
4. Work through mission router endpoints one by one
5. Test thoroughly
6. Commit when mission router is done
7. Move to next router

Good luck! 🚀
