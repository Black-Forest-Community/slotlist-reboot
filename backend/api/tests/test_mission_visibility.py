"""
API Tests for Mission Visibility and Permissions

Tests that verify mission visibility controls work correctly:
- Public missions: visible to everyone
- Community missions: visible to community members
- Private missions: visible to assigned users and editors
- Hidden missions: only visible to creator and admins
"""

from django.test import TestCase, Client
from api.models import User, Permission, Community, Mission, MissionSlot, MissionSlotGroup
from api.auth import generate_jwt
from datetime import datetime, timedelta, timezone
import json


class MissionVisibilityTests(TestCase):
    """Test mission visibility controls"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test communities
        self.community_a = Community.objects.create(
            name='Community A',
            tag='CA',
            slug='community-a',
        )
        
        self.community_b = Community.objects.create(
            name='Community B',
            tag='CB',
            slug='community-b',
        )
        
        # Create test users
        self.creator = User.objects.create(
            steam_id='76561198000000001',
            nickname='Creator',
            active=True,
            community=self.community_a
        )
        
        self.community_member = User.objects.create(
            steam_id='76561198000000002',
            nickname='CommunityMember',
            active=True,
            community=self.community_a
        )
        
        self.other_community_member = User.objects.create(
            steam_id='76561198000000003',
            nickname='OtherCommunityMember',
            active=True,
            community=self.community_b
        )
        
        self.no_community_user = User.objects.create(
            steam_id='76561198000000004',
            nickname='NoCommunityUser',
            active=True,
            community=None
        )
        
        self.admin_user = User.objects.create(
            steam_id='76561198000000005',
            nickname='AdminUser',
            active=True,
            community=None
        )
        
        # Give admin user admin permissions
        Permission.objects.create(
            user=self.admin_user,
            permission='admin.mission'
        )
        
        # Create missions with different visibility levels
        now = datetime.now(timezone.utc)
        future_time = now + timedelta(days=7)
        
        self.public_mission = Mission.objects.create(
            slug='public-mission',
            title='Public Mission',
            description='A public mission',
            short_description='A public mission',
            detailed_description='',
            start_time=future_time,
            end_time=future_time + timedelta(hours=3),
            visibility='public',
            creator=self.creator,
            community=self.community_a
        )
        
        self.community_mission = Mission.objects.create(
            slug='community-mission',
            title='Community Mission',
            description='A community mission',
            short_description='A community mission',
            detailed_description='',
            start_time=future_time,
            end_time=future_time + timedelta(hours=3),
            visibility='community',
            creator=self.creator,
            community=self.community_a
        )
        
        self.private_mission = Mission.objects.create(
            slug='private-mission',
            title='Private Mission',
            description='A private mission',
            short_description='A private mission',
            detailed_description='',
            start_time=future_time,
            end_time=future_time + timedelta(hours=3),
            visibility='private',
            creator=self.creator,
            community=self.community_a
        )
        
        self.hidden_mission = Mission.objects.create(
            slug='hidden-mission',
            title='Hidden Mission',
            description='A hidden mission',
            short_description='A hidden mission',
            detailed_description='',
            start_time=future_time,
            end_time=future_time + timedelta(hours=3),
            visibility='hidden',
            creator=self.creator,
            community=self.community_a
        )
        
        # Create slot group and slot for private mission (for testing slot assignment visibility)
        self.private_slot_group = MissionSlotGroup.objects.create(
            mission=self.private_mission,
            title='Alpha',
            order_number=0
        )
        
        self.private_slot = MissionSlot.objects.create(
            slot_group=self.private_slot_group,
            title='Squad Leader',
            order_number=0
        )
    
    def _get_token(self, user):
        """Generate JWT token for a user"""
        return generate_jwt(user)
    
    def _auth_headers(self, user):
        """Get authorization headers for a user"""
        token = self._get_token(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {token}'}
    
    def test_public_mission_visible_to_everyone(self):
        """Public missions should be visible to all users, even unauthenticated"""
        # Unauthenticated request
        response = self.client.get('/api/v1/missions/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertIn('public-mission', mission_slugs)
        
        # Authenticated users from different communities
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.community_member))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertIn('public-mission', mission_slugs)
        
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.other_community_member))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertIn('public-mission', mission_slugs)
        
        # Get specific mission
        response = self.client.get(f'/api/v1/missions/{self.public_mission.slug}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['mission']['slug'], 'public-mission')
    
    def test_community_mission_visible_to_community_members_only(self):
        """Community missions should only be visible to community members"""
        # Community member should see it
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.community_member))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertIn('community-mission', mission_slugs)
        
        # Other community member should NOT see it
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.other_community_member))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertNotIn('community-mission', mission_slugs)
        
        # User without community should NOT see it
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.no_community_user))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertNotIn('community-mission', mission_slugs)
        
        # Unauthenticated should NOT see it
        response = self.client.get('/api/v1/missions/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertNotIn('community-mission', mission_slugs)
    
    def test_private_mission_visible_to_assigned_users(self):
        """Private missions should be visible to users with slots and editors"""
        # Assign a slot to other_community_member
        self.private_slot.assignee = self.other_community_member
        self.private_slot.save()
        
        # User with assigned slot should see it
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.other_community_member))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertIn('private-mission', mission_slugs)
        
        # User without slot should NOT see it
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.no_community_user))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertNotIn('private-mission', mission_slugs)
        
        # Creator should always see it
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.creator))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertIn('private-mission', mission_slugs)
    
    def test_private_mission_visible_to_editors(self):
        """Private missions should be visible to users with editor permissions"""
        # Give editor permission to no_community_user
        Permission.objects.create(
            user=self.no_community_user,
            permission=f'mission.{self.private_mission.slug}.editor'
        )
        
        # Editor should see the mission
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.no_community_user))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertIn('private-mission', mission_slugs)
    
    def test_hidden_mission_only_visible_to_creator_and_admin(self):
        """Hidden missions should only be visible to creator and admins"""
        # Creator should see it
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.creator))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertIn('hidden-mission', mission_slugs)
        
        # Admin should see it
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.admin_user))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertIn('hidden-mission', mission_slugs)
        
        # Community member should NOT see it
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.community_member))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertNotIn('hidden-mission', mission_slugs)
        
        # Other users should NOT see it
        response = self.client.get('/api/v1/missions/', **self._auth_headers(self.no_community_user))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertNotIn('hidden-mission', mission_slugs)
        
        # Unauthenticated should NOT see it
        response = self.client.get('/api/v1/missions/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mission_slugs = [m['slug'] for m in data['missions']]
        self.assertNotIn('hidden-mission', mission_slugs)
    
    def test_get_specific_mission_respects_visibility(self):
        """Getting a specific mission should respect visibility rules"""
        # Public mission - anyone can access
        response = self.client.get(f'/api/v1/missions/{self.public_mission.slug}')
        self.assertEqual(response.status_code, 200)
        
        # Community mission - only community members
        response = self.client.get(
            f'/api/v1/missions/{self.community_mission.slug}',
            **self._auth_headers(self.community_member)
        )
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(
            f'/api/v1/missions/{self.community_mission.slug}',
            **self._auth_headers(self.other_community_member)
        )
        self.assertEqual(response.status_code, 403)
        
        # Hidden mission - only creator and admin
        response = self.client.get(
            f'/api/v1/missions/{self.hidden_mission.slug}',
            **self._auth_headers(self.creator)
        )
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(
            f'/api/v1/missions/{self.hidden_mission.slug}',
            **self._auth_headers(self.community_member)
        )
        self.assertEqual(response.status_code, 403)
        
        response = self.client.get(
            f'/api/v1/missions/{self.hidden_mission.slug}',
            **self._auth_headers(self.admin_user)
        )
        self.assertEqual(response.status_code, 200)
    
    def test_mission_slots_respect_visibility(self):
        """Getting mission slots should respect visibility rules"""
        # Public mission slots - accessible to anyone
        response = self.client.get(f'/api/v1/missions/{self.public_mission.slug}/slots')
        self.assertEqual(response.status_code, 200)
        
        # Hidden mission slots - only creator and admin
        response = self.client.get(f'/api/v1/missions/{self.hidden_mission.slug}/slots')
        self.assertEqual(response.status_code, 403)
        
        response = self.client.get(
            f'/api/v1/missions/{self.hidden_mission.slug}/slots',
            **self._auth_headers(self.creator)
        )
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(
            f'/api/v1/missions/{self.hidden_mission.slug}/slots',
            **self._auth_headers(self.admin_user)
        )
        self.assertEqual(response.status_code, 200)
    
    def test_only_creator_and_admin_can_change_visibility(self):
        """Only mission creator and admins can update mission visibility"""
        # Creator can update
        response = self.client.patch(
            f'/api/v1/missions/{self.public_mission.slug}',
            data=json.dumps({'visibility': 'private'}),
            content_type='application/json',
            **self._auth_headers(self.creator)
        )
        self.assertEqual(response.status_code, 200)
        self.public_mission.refresh_from_db()
        self.assertEqual(self.public_mission.visibility, 'private')
        
        # Reset for next test
        self.public_mission.visibility = 'public'
        self.public_mission.save()
        
        # Admin can update
        response = self.client.patch(
            f'/api/v1/missions/{self.public_mission.slug}',
            data=json.dumps({'visibility': 'hidden'}),
            content_type='application/json',
            **self._auth_headers(self.admin_user)
        )
        self.assertEqual(response.status_code, 200)
        self.public_mission.refresh_from_db()
        self.assertEqual(self.public_mission.visibility, 'hidden')
        
        # Reset for next test
        self.public_mission.visibility = 'public'
        self.public_mission.save()
        
        # Other users cannot update
        response = self.client.patch(
            f'/api/v1/missions/{self.public_mission.slug}',
            data=json.dumps({'visibility': 'hidden'}),
            content_type='application/json',
            **self._auth_headers(self.community_member)
        )
        self.assertEqual(response.status_code, 403)
        self.public_mission.refresh_from_db()
        self.assertEqual(self.public_mission.visibility, 'public')
    
    def test_editor_can_see_but_not_change_visibility(self):
        """Users with editor permission can see mission but can't change visibility without being creator/admin"""
        # Give editor permission
        Permission.objects.create(
            user=self.community_member,
            permission=f'mission.{self.hidden_mission.slug}.editor'
        )
        
        # Editor can see the mission
        response = self.client.get(
            f'/api/v1/missions/{self.hidden_mission.slug}',
            **self._auth_headers(self.community_member)
        )
        self.assertEqual(response.status_code, 200)
        
        # But editor cannot change visibility (requires creator or admin.mission)
        response = self.client.patch(
            f'/api/v1/missions/{self.hidden_mission.slug}',
            data=json.dumps({'visibility': 'public'}),
            content_type='application/json',
            **self._auth_headers(self.community_member)
        )
        self.assertEqual(response.status_code, 403)
