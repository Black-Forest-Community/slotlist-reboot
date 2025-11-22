from django.core.management.base import BaseCommand
from datetime import datetime
import requests
from api.import_utils import (
    import_mission,
    MissionAlreadyExistsError,
    APIFetchError,
)


class Command(BaseCommand):
    help = 'Import all missions from slotlist.info for a specific year (defaults to current year)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=datetime.now().year,
            help='Year to import missions from (defaults to current year)',
        )
        parser.add_argument(
            '--creator-uid',
            type=str,
            required=False,
            help='UUID of the user to set as mission creator for all missions (optional)',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip missions that already exist instead of failing',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of missions to import (useful for testing)',
        )

    def handle(self, *args, **options):
        year = options['year']
        creator_uid = options.get('creator_uid')
        skip_existing = options['skip_existing']
        limit = options.get('limit')

        self.stdout.write(f'Importing missions from year {year}...')
        
        # Fetch missions list from API
        try:
            missions = self._fetch_missions_for_year(year)
            self.stdout.write(f'Found {len(missions)} missions from {year}')
            
            if limit:
                missions = missions[:limit]
                self.stdout.write(f'Limited to {limit} missions')
        except APIFetchError as e:
            self.stdout.write(self.style.ERROR(f'Failed to fetch missions: {e}'))
            return

        # Import each mission
        imported_count = 0
        skipped_count = 0
        failed_count = 0

        for i, mission_data in enumerate(missions, 1):
            slug = mission_data['slug']
            title = mission_data['title']
            
            self.stdout.write(f'\n[{i}/{len(missions)}] Importing: {title} ({slug})')
            
            try:
                mission = import_mission(slug, creator_uid)
                self.stdout.write(self.style.SUCCESS(f'  ✓ Imported mission UID: {mission.uid}'))
                imported_count += 1
            except MissionAlreadyExistsError:
                if skip_existing:
                    self.stdout.write(self.style.WARNING(f'  ⊘ Skipped (already exists)'))
                    skipped_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed: Mission already exists'))
                    failed_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
                failed_count += 1

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'Imported: {imported_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'Skipped: {skipped_count}'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {failed_count}'))
        self.stdout.write(f'Total: {len(missions)}')

    def _fetch_missions_for_year(self, year: int):
        """
        Fetch all missions from slotlist.info for a specific year.
        
        Args:
            year: Year to filter missions by
            
        Returns:
            List of mission data dictionaries
            
        Raises:
            APIFetchError: If the API request fails
        """
        # Use date range query parameters to filter by year
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'
        
        # Note: The API returns all matching missions in a single response
        # when using date filters, regardless of limit/offset parameters
        url = f'https://api.slotlist.info/v1/missions?startDate={start_date}&endDate={end_date}'
        
        try:
            self.stdout.write(f'Fetching missions from {start_date} to {end_date}...')
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            missions = data.get('missions', [])
            return missions
            
        except requests.RequestException as e:
            raise APIFetchError(f'Failed to fetch missions: {e}')
