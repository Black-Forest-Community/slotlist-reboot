# Mission Import

Import missions from the legacy slotlist.info API into your Django backend. Available via both CLI and REST API.

## Architecture

The import functionality is built with shared utilities that can be used by both the management command and the API endpoint:

```
import_utils.py (Core Logic)
├── fetch_mission_data()
├── import_mission()
└── preview_import()
       ↓              ↓
  CLI Command    API Endpoint
```

## API Endpoint

### POST /api/v1/missions/import

Import or preview a mission from slotlist.info.

**Authentication:** Required (JWT Bearer token)

**Request:**
```json
{
  "slug": "bf-mm-20251028",
  "creator_uid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "dry_run": false
}
```

**Response (Preview - dry_run=true):**
```json
{
  "preview": {
    "mission": {
      "title": "BF Operation Mountain Shade II",
      "slug": "bf-mm-20251028",
      "description": "Folgt",
      "visibility": "public",
      "community": {
        "name": "Black Forest",
        "slug": "black-forest"
      }
    },
    "slot_groups": [
      {
        "title": "Wagen 1",
        "slot_count": 5,
        "slots": ["Assistant Team Leader", "Combat Life Saver", ...]
      }
    ],
    "totals": {
      "slot_groups": 3,
      "slots": 15
    }
  }
}
```

**Response (Success - dry_run=false):**
```json
{
  "success": true,
  "message": "Successfully imported mission: BF Operation Mountain Shade II",
  "mission_uid": "2d05cd89-74c5-4bbc-9559-84328abb803a",
  "mission_slug": "bf-mm-20251028",
  "mission_title": "BF Operation Mountain Shade II"
}
```

**Error Responses:**
```json
// Mission already exists
{
  "detail": "Mission with slug bf-mm-20251028 already exists"
}

// Creator not found
{
  "detail": "Creator user with UID a1b2c3d4... not found"
}

// API fetch error
{
  "detail": "Failed to fetch mission data: ..."
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/missions/import \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "bf-mm-20251028",
    "creator_uid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "dry_run": true
  }'
```

## Management Command

### Usage

```bash
python manage.py import_mission <mission-slug> [--creator-uid <user-uuid>] [--dry-run]
```

### Arguments

- `slug` - Mission slug to import from slotlist.info (required)
- `--creator-uid` - UUID of user to set as mission creator (optional, uses original creator if not specified)
- `--dry-run` - Preview import without saving (optional)

### Examples

**Preview import:**
```bash
python manage.py import_mission bf-mm-20251028 --dry-run
```

**Actually import (uses original creator):**
```bash
python manage.py import_mission bf-mm-20251028
```

**Import with custom creator:**
```bash
python manage.py import_mission bf-mm-20251028 \
  --creator-uid a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Output

**Dry run:**
```
Importing mission: bf-mm-20251028
Fetching mission from https://api.slotlist.info/v1/missions/bf-mm-20251028
Fetching slots from https://api.slotlist.info/v1/missions/bf-mm-20251028/slots
DRY RUN - No changes will be saved

=== MISSION DATA ===
Title: BF Operation Mountain Shade II
Slug: bf-mm-20251028
Description: Folgt...
Visibility: public
Community: Black Forest (black-forest)

=== SLOT GROUPS ===
Total: 3 groups, 15 slots

Wagen 1 (5 slots)
  - Assistant Team Leader
  - Combat Life Saver
  ...
```

**Actual import:**
```
Importing mission: bf-mm-20251028
...

Importing mission...
  Created mission: BF Operation Mountain Shade II

Successfully imported mission: BF Operation Mountain Shade II (bf-mm-20251028)
Mission UID: 2d05cd89-74c5-4bbc-9559-84328abb803a
```

## What Gets Imported

### Mission Data
- Title, slug, description
- Times (briefing, slotting, start, end)
- Game server and voice comms configuration
- Required DLCs
- Repositories
- Visibility settings

### Community Data
- Community name, tag, slug
- Website and logo URLs
- Creates community if it doesn't exist

### User Data
- User nickname and UUID
- Community membership
- Creates users if they don't exist
- **Note:** Steam IDs are placeholders (`imported_<uuid>`) since the API doesn't expose them

### Slot Groups
- Title, description, order
- Preserves original UUIDs

### Slots
- Title, description, detailed description
- Order
- Required DLCs
- Restricted community
- Assignee (user or external name)
- Blocked/reserve/auto-assignable flags
- Preserves original UUIDs

### Slot Registrations
- Creates registrations for assigned users
- Preserves original UUIDs

## Technical Details

### Shared Functions (import_utils.py)

**fetch_mission_data(slug)**
- Fetches data from slotlist.info API
- Returns tuple of (mission_data, slots_data)
- Raises APIFetchError on failure

**import_mission(slug, creator_uid, mission_data, slots_data)**
- Imports mission into database
- Atomic transaction (all-or-nothing)
- Returns Mission instance
- Raises:
  - MissionAlreadyExistsError
  - CreatorNotFoundError

**preview_import(mission_data, slots_data)**
- Generates preview dictionary
- No database interaction
- Returns structured preview data

### Custom Exceptions

- `MissionImportError` - Base exception
  - `MissionAlreadyExistsError` - Mission slug exists
  - `CreatorNotFoundError` - Creator user not found
  - `APIFetchError` - API request failed

## Notes

- **UUIDs preserved**: All UUIDs from original system maintained
- **Creator optional**: If not specified with --creator-uid, uses original creator from API
- **User Steam IDs**: Imported users get placeholder Steam IDs (`imported_<uuid>`) since API doesn't expose them
- **Idempotent**: Running twice fails (mission exists)
- **Atomic**: Transaction ensures all-or-nothing
- **No updates**: Only creates, never updates existing

## Troubleshooting

### Mission already exists

```
Mission with slug bf-mm-20251028 already exists
```

**Solution:** Mission imported already. Delete first to re-import.

### Creator not found

```
Creator user with UID a1b2c3d4... not found
```

**Solution:** Verify user UUID exists in database.

### Network errors

```
Failed to fetch mission data: ...
```

**Solution:** Check internet connection and mission exists on slotlist.info.

## API Sources

Data fetched from:
- `GET https://api.slotlist.info/v1/missions/<slug>`
- `GET https://api.slotlist.info/v1/missions/<slug>/slots`
