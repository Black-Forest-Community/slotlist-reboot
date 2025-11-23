# Merge Duplicate Users

This document describes how to use the `merge_duplicate_users` management command to handle duplicate user nicknames and merge imported users with real Steam users.

## Background

When importing missions from the slotlist.info API, users are created with placeholder Steam IDs in the format `imported_{uid}` since the API doesn't expose actual Steam IDs. When these users later log in with Steam OAuth, new user accounts are created with their real Steam IDs.

This results in duplicate users with the same nickname:
- **Imported users**: Created during mission imports with `steam_id = "imported_{uid}"`
- **Real users**: Created when users authenticate with Steam OAuth with actual Steam IDs

## Command Usage

### Check for Duplicates (Dry Run)

Preview what would be merged without making any changes:

```bash
python manage.py merge_duplicate_users --dry-run
```

### Check and Auto-Merge (Dry Run)

Preview automatic merging without making changes:

```bash
python manage.py merge_duplicate_users --dry-run --auto-merge
```

### Auto-Merge Duplicates

Automatically merge imported users into real users:

```bash
python manage.py merge_duplicate_users --auto-merge
```

## What the Command Does

1. **Finds duplicate nicknames**: Identifies all nicknames that appear more than once
2. **Categorizes users**: Separates imported users from real Steam users
3. **Safe merging**: Only merges when there is exactly ONE real user and one or more imported users
4. **Transfers data**:
   - Community membership (if target user has no community)
   - Missions created by the user (`Mission.creator`)
   - Slot assignments (`MissionSlot.assignee`)
   - Slot registrations (`MissionSlotRegistration`)
   - Handles duplicate registrations (deletes duplicates if target user already registered)
5. **Cleanup**: Deletes imported users after transferring all data

**Important Notes:**
- The **real user's Steam ID is kept** (imported users have placeholder IDs like `imported_{uid}`)
- The **imported user's community is transferred** only if the real user has no community
- If both have communities but they differ, the real user's community is kept (with a warning)

## Output

The command provides detailed output showing:
- Number of duplicate nicknames found
- For each duplicate:
  - User type (IMPORTED or REAL)
  - User UID and Steam ID
  - Number of slot assignments
  - Number of registrations
  - Community membership
  - Creation date
- What actions were taken or would be taken
- Summary of merged users

## Example Output

```
=== Checking for duplicate nicknames ===
Found 3 nicknames with duplicates

Nickname: "John Smith" (2 users)
  [IMPORTED] a1b2c3d4-... - imported_a1b2c3d4-... (slots: 5, registrations: 3, missions: 2, community: example-clan, created: 2024-01-15)
  [REAL] e5f6g7h8-... - 76561198012345678 (slots: 0, registrations: 0, missions: 0, no community, created: 2024-02-01)
  → Merging 1 imported user(s) into real user e5f6g7h8-...
    Transferred community: Example Clan (example-clan)
    Transferred 2 mission(s) from a1b2c3d4-...
    Transferred 5 slot assignment(s) from a1b2c3d4-...
    Transferred 3 registration(s) from a1b2c3d4-...
    Deleted imported user a1b2c3d4-...

Nickname: "Jane Doe" (3 users)
  [IMPORTED] i9j0k1l2-... - imported_i9j0k1l2-... (slots: 2, registrations: 1, missions: 1, community: alpha-team, created: 2024-01-10)
  [REAL] m3n4o5p6-... - 76561198087654321 (slots: 1, registrations: 2, missions: 3, community: bravo-squad, created: 2024-01-20)
  [REAL] q7r8s9t0-... - 76561198011111111 (slots: 0, registrations: 0, missions: 0, no community, created: 2024-02-15)
  ⚠ Multiple real users with same nickname - manual review required

============================================================
Merged 1 users
Skipped 1 nicknames requiring manual review
```

## Safety Features

- **Dry run mode**: Always test with `--dry-run` first
- **Manual review required**: Skips cases with multiple real users (requires manual intervention)
- **Atomic transactions**: All changes in a transaction (all-or-nothing)
- **Duplicate handling**: Smart duplicate detection for registrations

## When to Use

Run this command:
- After importing missions from slotlist.info
- When you notice users with duplicate slots
- Periodically as part of database maintenance
- Before major mission events to ensure clean user data

## Manual Review Cases

The command will skip and flag for manual review:
- **Multiple real users with same nickname**: Requires admin decision on which account to keep
- **All imported users**: No real user to merge into (users haven't logged in yet)

For these cases, you'll need to manually:
1. Contact the users to determine which account is correct
2. Manually transfer data using Django admin or SQL
3. Delete duplicate accounts
