from django.core.management.base import BaseCommand, CommandError
import requests
from api.import_utils import (
    fetch_mission_data,
    get_or_create_community,
    APIFetchError,
)
from api.image_utils import download_and_store_image
from api.models import Mission, MissionSlotGroup, MissionSlot, Community, User
from django.db import transaction


class Command(BaseCommand):
    help = 'Import all missions from a community (without importing users, registrations or usernames)'

    def add_arguments(self, parser):
        parser.add_argument(
            'community_slug',
            type=str,
            help='Community slug to import missions from',
        )
        parser.add_argument(
            '--creator-uid',
            type=str,
            required=False,
            help='UUID of the user to set as mission creator for all missions (uses original creator if available)',
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
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be imported without saving',
        )

    def handle(self, *args, **options):
        community_slug = options['community_slug']
        creator_uid = options.get('creator_uid')
        skip_existing = options['skip_existing']
        limit = options.get('limit')
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be saved'))

        self.stdout.write(f'Importing missions from community: {community_slug}')
        
        # Get creator if specified
        default_creator = None
        if creator_uid:
            try:
                default_creator = User.objects.get(uid=creator_uid)
                self.stdout.write(f'Using default creator: {default_creator.nickname} ({creator_uid})')
            except User.DoesNotExist:
                raise CommandError(f'Creator user with UID {creator_uid} not found')
        
        # Fetch community missions from API
        try:
            missions = self._fetch_community_missions(community_slug)
            self.stdout.write(f'Found {len(missions)} missions')
            
            if limit:
                missions = missions[:limit]
                self.stdout.write(f'Limited to {limit} missions')
        except APIFetchError as e:
            raise CommandError(f'Failed to fetch missions: {e}')

        if dry_run:
            self._preview_import(missions)
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
                # Check if mission already exists
                if Mission.objects.filter(slug=slug).exists():
                    if skip_existing:
                        self.stdout.write(self.style.WARNING(f'  ⊘ Skipped (already exists)'))
                        skipped_count += 1
                        continue
                    else:
                        self.stdout.write(self.style.ERROR(f'  ✗ Failed: Mission already exists'))
                        failed_count += 1
                        continue
                
                # Fetch full mission data
                mission_detail, slots_data = fetch_mission_data(slug)
                
                # Determine creator (will create dummy if needed)
                creator = self._determine_creator(mission_detail, default_creator, community_slug)
                
                # Import mission without users
                mission = self._import_mission_without_users(
                    mission_detail, 
                    slots_data, 
                    creator
                )
                
                self.stdout.write(self.style.SUCCESS(f'  ✓ Imported mission UID: {mission.uid}'))
                imported_count += 1
                
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

    def _fetch_community_missions(self, community_slug: str):
        """
        Fetch all missions from slotlist.info for a specific community.
        
        Args:
            community_slug: Community slug to filter missions by
            
        Returns:
            List of mission data dictionaries
            
        Raises:
            APIFetchError: If the API request fails
        """
        url = f'https://api.slotlist.info/v1/communities/{community_slug}'
        
        try:
            self.stdout.write(f'Fetching missions from {url}...')
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            missions = data.get('community', {}).get('missions', [])
            return missions
            
        except requests.RequestException as e:
            raise APIFetchError(f'Failed to fetch missions: {e}')

    def _determine_creator(self, mission_data: dict, default_creator: User = None, community_slug: str = None) -> User:
        """
        Determine the creator for a mission.
        Creates a dummy creator if none exists.
        
        Args:
            mission_data: Mission data from API
            default_creator: Default creator to use if specified
            community_slug: Community slug for dummy creator name
            
        Returns:
            User instance
        """
        # Use default creator if provided
        if default_creator:
            return default_creator
        
        # Try to find existing user by UID from API data
        if mission_data.get('creator'):
            try:
                return User.objects.get(uid=mission_data['creator']['uid'])
            except User.DoesNotExist:
                pass
        
        # Create dummy creator
        community = get_or_create_community(mission_data['community'])
        dummy_nickname = f"Import-{community.name}" if community else f"Import-{community_slug}"
        dummy_steam_id = f"import_dummy_{community_slug}"
        
        creator, created = User.objects.get_or_create(
            steam_id=dummy_steam_id,
            defaults={
                'nickname': dummy_nickname,
                'community': community,
            }
        )
        
        if created:
            self.stdout.write(self.style.WARNING(f'  Created dummy creator: {dummy_nickname}'))
        
        return creator

    def _import_mission_without_users(
        self,
        mission_data: dict,
        slots_data: list,
        creator: User
    ) -> Mission:
        """
        Import a mission without importing users, registrations or usernames.
        Only imports community, mission structure and slots.
        
        Args:
            mission_data: Mission data from API
            slots_data: Slots data from API
            creator: Creator user (required)
            
        Returns:
            Created Mission instance
        """
        with transaction.atomic():
            # Get or create community
            community = get_or_create_community(mission_data['community'])
            
            # Download and store banner image if available
            banner_image_url = mission_data.get('bannerImageUrl')
            if banner_image_url:
                self.stdout.write(f'  Downloading banner image...')
                stored_url = download_and_store_image(
                    banner_image_url, 
                    f'missions/{mission_data["slug"]}'
                )
                if stored_url:
                    banner_image_url = stored_url
            
            # Create mission
            mission = Mission.objects.create(
                slug=mission_data['slug'],
                title=mission_data['title'],
                description=mission_data['description'],
                short_description=mission_data['description'],
                detailed_description=mission_data.get('detailedDescription', ''),
                collapsed_description=mission_data.get('collapsedDescription'),
                briefing_time=mission_data.get('briefingTime'),
                slotting_time=mission_data.get('slottingTime'),
                start_time=mission_data.get('startTime'),
                end_time=mission_data.get('endTime'),
                visibility=mission_data.get('visibility', 'public'),
                tech_support=mission_data.get('techSupport'),
                rules=mission_data.get('rules'),
                required_dlcs=mission_data.get('requiredDLCs', []),
                banner_image_url=banner_image_url,
                game_server=mission_data.get('gameServer'),
                voice_comms=mission_data.get('voiceComms'),
                repositories=mission_data.get('repositories', []),
                creator=creator,
                community=community,
            )
            
            # Import slot groups and slots (without assignees)
            self._import_slots_without_users(mission, slots_data)
            
        return mission

    def _import_slots_without_users(self, mission: Mission, slot_groups_data: list) -> None:
        """
        Import slot groups and slots without importing users or registrations.
        
        Args:
            mission: Mission instance to add slots to
            slot_groups_data: List of slot group data from API
        """
        for group_data in slot_groups_data:
            # Create slot group
            slot_group = MissionSlotGroup.objects.create(
                uid=group_data['uid'],
                mission=mission,
                title=group_data['title'],
                description=group_data.get('description'),
                order_number=group_data['orderNumber'],
            )
            
            # Create slots
            for slot_data in group_data['slots']:
                # Only get restricted community if it already exists, don't create new ones
                restricted_community = None
                if slot_data.get('restrictedCommunity'):
                    restricted_community = get_or_create_community(
                        slot_data['restrictedCommunity'],
                        only_if_exists=True
                    )
                
                # Try to find existing assignee by UID, but don't create new one
                assignee = None
                if slot_data.get('assignee'):
                    try:
                        assignee = User.objects.get(uid=slot_data['assignee']['uid'])
                    except User.DoesNotExist:
                        # User doesn't exist, leave as unassigned
                        pass
                
                # Create slot without assignee (no new users or registrations)
                MissionSlot.objects.create(
                    uid=slot_data['uid'],
                    slot_group=slot_group,
                    title=slot_data['title'],
                    description=slot_data.get('description'),
                    detailed_description=slot_data.get('detailedDescription'),
                    order_number=slot_data['orderNumber'],
                    required_dlcs=slot_data.get('requiredDLCs', []),
                    external_assignee=slot_data.get('externalAssignee'),
                    assignee=assignee,
                    restricted_community=restricted_community,
                    blocked=slot_data.get('blocked', False),
                    reserve=slot_data.get('reserve', False),
                    auto_assignable=slot_data.get('autoAssignable', True),
                )

    def _preview_import(self, missions: list) -> None:
        """Preview what would be imported"""
        self.stdout.write(f'\nWould import {len(missions)} missions:')
        
        for mission_data in missions:
            community_name = mission_data.get('community', {}).get('name', 'Unknown')
            self.stdout.write(f'  - {mission_data["title"]} ({mission_data["slug"]}) - {community_name}')
