from django.core.management.base import BaseCommand, CommandError
from api.import_utils import (
    fetch_mission_data,
    import_mission,
    preview_import,
    MissionAlreadyExistsError,
    CreatorNotFoundError,
    APIFetchError,
)


class Command(BaseCommand):
    help = 'Import a mission from slotlist.info API by slug'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Mission slug to import')
        parser.add_argument(
            '--creator-uid',
            type=str,
            required=False,
            help='UUID of the user to set as mission creator (optional, uses original creator if not specified)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be imported without saving',
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing mission with new data from API (re-imports media content in body fields)',
        )

    def handle(self, *args, **options):
        slug = options['slug']
        creator_uid = options.get('creator_uid')
        dry_run = options['dry_run']
        update_existing = options['update']

        self.stdout.write(f'Importing mission: {slug}')
        if update_existing:
            self.stdout.write(self.style.WARNING('Update mode: Existing mission will be updated with new data'))
        
        # Fetch mission data
        try:
            self.stdout.write(f'Fetching mission from https://api.slotlist.info/v1/missions/{slug}')
            self.stdout.write(f'Fetching slots from https://api.slotlist.info/v1/missions/{slug}/slots')
            mission_data, slots_data = fetch_mission_data(slug)
        except APIFetchError as e:
            raise CommandError(str(e))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be saved'))
            self._preview_import(mission_data, slots_data)
            return
        
        # Import the mission
        try:
            self.stdout.write('\nImporting mission...')
            mission = import_mission(slug, creator_uid, mission_data, slots_data, update_existing=update_existing)
            
            action = 'updated' if update_existing else 'imported'
            self.stdout.write(self.style.SUCCESS(
                f'Successfully {action} mission: {mission.title} ({mission.slug})'
            ))
            self.stdout.write(f'Mission UID: {mission.uid}')
        except MissionAlreadyExistsError as e:
            raise CommandError(str(e))
        except CreatorNotFoundError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f'Failed to import mission: {e}')

    def _preview_import(self, mission_data, slots_data):
        """Preview what would be imported"""
        preview = preview_import(mission_data, slots_data)
        
        self.stdout.write('\n=== MISSION DATA ===')
        self.stdout.write(f"Title: {preview['mission']['title']}")
        self.stdout.write(f"Slug: {preview['mission']['slug']}")
        self.stdout.write(f"Description: {preview['mission']['description'][:100]}...")
        self.stdout.write(f"Visibility: {preview['mission']['visibility']}")
        self.stdout.write(f"Community: {preview['mission']['community']['name']} ({preview['mission']['community']['slug']})")
        
        self.stdout.write('\n=== SLOT GROUPS ===')
        self.stdout.write(f"Total: {preview['totals']['slot_groups']} groups, {preview['totals']['slots']} slots")
        
        for group in preview['slot_groups']:
            self.stdout.write(f"\n{group['title']} ({group['slot_count']} slots)")
            for slot in group['slots']:
                self.stdout.write(f"  - {slot['title']}: {slot['assignee']}")
