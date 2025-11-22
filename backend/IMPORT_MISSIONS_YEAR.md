# Import Missions by Year

This management command imports all missions from slotlist.info for a specific year.

## Usage

```bash
python manage.py import_missions_year [OPTIONS]
```

## Options

- `--year YEAR`: Year to import missions from (defaults to current year: 2025)
- `--creator-uid UUID`: UUID of the user to set as mission creator for all missions (optional, uses original creator if not specified)
- `--skip-existing`: Skip missions that already exist instead of failing
- `--limit N`: Maximum number of missions to import (useful for testing)

## Examples

### Import all missions from 2025
```bash
python manage.py import_missions_year --year 2025 --skip-existing
```

### Import missions from current year with a specific creator
```bash
python manage.py import_missions_year --creator-uid "123e4567-e89b-12d3-a456-426614174000" --skip-existing
```

### Test import with limit
```bash
python manage.py import_missions_year --year 2025 --limit 5 --skip-existing
```

### Import all missions from 2024
```bash
python manage.py import_missions_year --year 2024 --skip-existing
```

## How it Works

1. Fetches all missions from the slotlist.info API (`https://api.slotlist.info/v1/missions`)
2. Filters missions by `startTime` to include only those from the specified year
3. For each mission, imports it using the existing `import_mission` utility function from `api.import_utils`
4. Handles errors gracefully:
   - Skips existing missions if `--skip-existing` is used
   - Reports failures without stopping the entire import
5. Provides a summary at the end with counts of imported, skipped, and failed missions

## Notes

- The command fetches missions in pages of 100 to handle large datasets
- Each mission is imported with its complete slot structure (groups and individual slots)
- Communities and users referenced in missions are automatically created if they don't exist
- The import process uses database transactions, so failed imports don't leave partial data
- Progress is shown for each mission being imported

## Related Commands

- `import_mission`: Import a single mission by slug
- See `IMPORT_MISSIONS.md` for more details on the import process
