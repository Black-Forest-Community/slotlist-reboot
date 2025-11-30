import json
from unittest.mock import patch, Mock
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO

from api.models import Mission, MissionSlotGroup, MissionSlot, Community, User


class ImportMissionCommandTest(TestCase):
    """Tests for the import_mission management command"""

    def setUp(self):
        """Set up test data"""
        # Create a test creator user
        self.creator = User.objects.create(
            nickname='TestCreator',
            steam_id='test_steam_id_123'
        )

    def _get_mock_mission_response(self, detailed_description='Detailed test description',
                                   banner_image_url=None, title='Test Mission'):
        """Returns mock mission API response"""
        return {
            'mission': {
                'uid': 'test-mission-uid-123',
                'slug': 'test-mission',
                'title': title,
                'description': 'Test description',
                'detailedDescription': detailed_description,
                'collapsedDescription': None,
                'briefingTime': '2025-10-28T18:00:00.000Z',
                'slottingTime': '2025-10-28T18:00:00.000Z',
                'startTime': '2025-10-28T18:00:00.000Z',
                'endTime': '2025-10-28T21:00:00.000Z',
                'visibility': 'public',
                'techSupport': 'Test tech support',
                'rules': 'Test rules',
                'requiredDLCs': [],
                'bannerImageUrl': banner_image_url,
                'gameServer': {
                    'hostname': 'test.server.com',
                    'port': 2302,
                    'name': 'Test Server',
                    'password': 'test123'
                },
                'voiceComms': {
                    'hostname': 'voice.server.com',
                    'port': 9987,
                    'name': 'Test TS',
                    'password': None
                },
                'repositories': [],
                'community': {
                    'uid': 'test-community-uid',
                    'name': 'Test Community',
                    'tag': 'TC',
                    'slug': 'test-community',
                    'website': 'https://test.com',
                    'logoUrl': None
                },
                'creator': {
                    'uid': str(self.creator.uid),
                    'nickname': self.creator.nickname,
                    'community': {
                        'uid': 'test-community-uid',
                        'name': 'Test Community',
                        'tag': 'TC',
                        'slug': 'test-community',
                        'website': 'https://test.com',
                        'logoUrl': None
                    }
                }
            }
        }

    def _get_mock_slots_response(self):
        """Returns mock slots API response"""
        return {
            'slotGroups': [
                {
                    'uid': 'test-group-uid-1',
                    'missionUid': 'test-mission-uid-123',
                    'title': 'Test Group 1',
                    'orderNumber': 1,
                    'description': None,
                    'slots': [
                        {
                            'uid': 'test-slot-uid-1',
                            'slotGroupUid': 'test-group-uid-1',
                            'title': 'Team Leader',
                            'orderNumber': 1,
                            'difficulty': 3,
                            'description': 'TL',
                            'detailedDescription': None,
                            'restrictedCommunity': None,
                            'reserve': False,
                            'blocked': False,
                            'autoAssignable': True,
                            'requiredDLCs': [],
                            'assignee': {
                                'uid': str(self.creator.uid),
                                'nickname': self.creator.nickname,
                                'community': None
                            },
                            'externalAssignee': None,
                            'registrationCount': 1,
                            'registrationUid': 'test-registration-uid-1'
                        },
                        {
                            'uid': 'test-slot-uid-2',
                            'slotGroupUid': 'test-group-uid-1',
                            'title': 'Rifleman',
                            'orderNumber': 2,
                            'difficulty': 0,
                            'description': None,
                            'detailedDescription': None,
                            'restrictedCommunity': None,
                            'reserve': False,
                            'blocked': False,
                            'autoAssignable': True,
                            'requiredDLCs': [],
                            'assignee': None,
                            'externalAssignee': 'External Player',
                            'registrationCount': 0
                        }
                    ]
                }
            ]
        }

    @patch('api.import_utils.requests.get')
    def test_dry_run(self, mock_get):
        """Test dry run doesn't save anything"""
        # Setup mocks
        mission_response = Mock()
        mission_response.json.return_value = self._get_mock_mission_response()
        mission_response.raise_for_status = Mock()
        
        slots_response = Mock()
        slots_response.json.return_value = self._get_mock_slots_response()
        slots_response.raise_for_status = Mock()
        
        mock_get.side_effect = [mission_response, slots_response]
        
        # Run command with dry-run
        out = StringIO()
        call_command('import_mission', 'test-mission', '--dry-run', stdout=out)
        
        # Verify nothing was saved
        self.assertEqual(Mission.objects.count(), 0)
        self.assertEqual(MissionSlotGroup.objects.count(), 0)
        self.assertEqual(MissionSlot.objects.count(), 0)
        
        # Verify output contains preview
        output = out.getvalue()
        self.assertIn('DRY RUN', output)
        self.assertIn('Test Mission', output)
        self.assertIn('Team Leader', output)

    @patch('api.import_utils.requests.get')
    def test_import_mission_success(self, mock_get):
        """Test successful mission import"""
        # Setup mocks
        mission_response = Mock()
        mission_response.json.return_value = self._get_mock_mission_response()
        mission_response.raise_for_status = Mock()
        
        slots_response = Mock()
        slots_response.json.return_value = self._get_mock_slots_response()
        slots_response.raise_for_status = Mock()
        
        mock_get.side_effect = [mission_response, slots_response]
        
        # Run command
        out = StringIO()
        call_command('import_mission', 'test-mission', stdout=out)
        
        # Verify mission was created
        self.assertEqual(Mission.objects.count(), 1)
        mission = Mission.objects.first()
        self.assertEqual(mission.slug, 'test-mission')
        self.assertEqual(mission.title, 'Test Mission')
        self.assertEqual(mission.creator, self.creator)
        
        # Verify community was created
        self.assertEqual(Community.objects.count(), 1)
        community = Community.objects.first()
        self.assertEqual(community.slug, 'test-community')
        
        # Verify slot groups and slots were created
        self.assertEqual(MissionSlotGroup.objects.count(), 1)
        self.assertEqual(MissionSlot.objects.count(), 2)
        
        slot_group = MissionSlotGroup.objects.first()
        self.assertEqual(slot_group.title, 'Test Group 1')
        
        # Verify output
        output = out.getvalue()
        self.assertIn('Successfully imported', output)

    @patch('api.import_utils.requests.get')
    def test_mission_already_exists(self, mock_get):
        """Test error when mission already exists"""
        # Create existing mission
        community = Community.objects.create(
            name='Test Community',
            tag='TC',
            slug='test-community'
        )
        Mission.objects.create(
            slug='test-mission',
            title='Existing Mission',
            description='Test',
            short_description='Test',
            detailed_description='Test',
            creator=self.creator,
            community=community
        )
        
        # Setup mocks
        mission_response = Mock()
        mission_response.json.return_value = self._get_mock_mission_response()
        mission_response.raise_for_status = Mock()
        
        slots_response = Mock()
        slots_response.json.return_value = self._get_mock_slots_response()
        slots_response.raise_for_status = Mock()
        
        mock_get.side_effect = [mission_response, slots_response]
        
        # Attempt to import should fail
        with self.assertRaises(CommandError) as context:
            call_command('import_mission', 'test-mission')
        
        self.assertIn('already exists', str(context.exception))

    @patch('api.import_utils.requests.get')
    def test_network_error(self, mock_get):
        """Test error handling for network failures"""
        # Setup mock to raise exception
        mock_get.side_effect = Exception('Network error')
        
        # Attempt to import should fail gracefully
        with self.assertRaises(CommandError) as context:
            call_command('import_mission', 'test-mission')
        
        self.assertIn('Failed to fetch', str(context.exception))

    @patch('api.import_utils.requests.get')
    def test_update_existing_mission(self, mock_get):
        """Test updating an existing mission with --update flag"""
        # Create existing mission with old data
        community = Community.objects.create(
            uid='test-community-uid',
            name='Test Community',
            tag='TC',
            slug='test-community'
        )
        existing_mission = Mission.objects.create(
            slug='test-mission',
            title='Old Title',
            description='Old description',
            short_description='Old description',
            detailed_description='Old detailed description',
            creator=self.creator,
            community=community
        )
        
        # Setup mocks with updated data including media content
        updated_detailed = '<p>Updated description with <img src="https://slotlist-info.storage.googleapis.com/images/test.png"></p>'
        mission_response = Mock()
        mission_response.json.return_value = self._get_mock_mission_response(
            detailed_description=updated_detailed,
            banner_image_url='https://slotlist-info.storage.googleapis.com/banners/test.jpg',
            title='Updated Test Mission'
        )
        mission_response.raise_for_status = Mock()
        
        slots_response = Mock()
        slots_response.json.return_value = self._get_mock_slots_response()
        slots_response.raise_for_status = Mock()
        
        mock_get.side_effect = [mission_response, slots_response]
        
        # Run command with --update flag
        out = StringIO()
        call_command('import_mission', 'test-mission', '--update', stdout=out)
        
        # Verify mission was updated (not duplicated)
        self.assertEqual(Mission.objects.count(), 1)
        mission = Mission.objects.first()
        self.assertEqual(mission.slug, 'test-mission')
        self.assertEqual(mission.title, 'Updated Test Mission')
        self.assertEqual(mission.detailed_description, updated_detailed)
        self.assertEqual(mission.banner_image_url, 'https://slotlist-info.storage.googleapis.com/banners/test.jpg')
        
        # Verify output
        output = out.getvalue()
        self.assertIn('Successfully updated', output)

    @patch('api.import_utils.requests.get')
    def test_update_imports_media_content(self, mock_get):
        """Test that update properly imports media content in body fields"""
        # Create existing mission without media
        community = Community.objects.create(
            uid='test-community-uid',
            name='Test Community',
            tag='TC',
            slug='test-community'
        )
        Mission.objects.create(
            slug='test-mission',
            title='Test Mission',
            description='Test',
            short_description='Test',
            detailed_description='No images here',
            creator=self.creator,
            community=community
        )
        
        # Setup mocks with media content in body fields
        detailed_with_images = '''
        <h2>Mission Briefing</h2>
        <p>Here is the situation map:</p>
        <img src="https://slotlist-info.storage.googleapis.com/images/missions/situation-map.png">
        <p>And here is the weather forecast:</p>
        <img src="https://slotlist-info.storage.googleapis.com/images/missions/weather.jpg">
        '''
        
        mission_response = Mock()
        mission_response.json.return_value = self._get_mock_mission_response(
            detailed_description=detailed_with_images
        )
        mission_response.raise_for_status = Mock()
        
        slots_response = Mock()
        slots_response.json.return_value = self._get_mock_slots_response()
        slots_response.raise_for_status = Mock()
        
        mock_get.side_effect = [mission_response, slots_response]
        
        # Run command with --update flag
        out = StringIO()
        call_command('import_mission', 'test-mission', '--update', stdout=out)
        
        # Verify mission was updated with media content
        mission = Mission.objects.first()
        self.assertIn('slotlist-info.storage.googleapis.com', mission.detailed_description)
        self.assertIn('situation-map.png', mission.detailed_description)
        self.assertIn('weather.jpg', mission.detailed_description)
