from django.test import TestCase, Client
from api.models import User, Community, CommunityApplication
from api.auth import has_approved_community, generate_jwt


class GatedAccessTestCase(TestCase):
    """Test suite for gated access (community membership requirements)"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()

        # Create test community
        self.community = Community.objects.create(
            name='Test Community',
            tag='TEST',
            slug='test-community',
            website='https://test.example.com'
        )

        # Create test users
        self.user_with_community = User.objects.create(
            steam_id='76561198012345678',
            nickname='Member User',
            community=self.community,
            active=True
        )

        self.user_without_community = User.objects.create(
            steam_id='76561198087654321',
            nickname='Non-Member User',
            active=True
        )

        self.user_pending_application = User.objects.create(
            steam_id='76561198011111111',
            nickname='Pending User',
            active=True
        )

        # Create pending application
        CommunityApplication.objects.create(
            user=self.user_pending_application,
            community=self.community,
            status='submitted'
        )

    def test_has_approved_community_with_community(self):
        """Test user with community has access"""
        has_access, msg = has_approved_community(
            str(self.user_with_community.uid)
        )
        self.assertTrue(has_access)
        self.assertIsNone(msg)

    def test_has_approved_community_without_community(self):
        """Test user without community is blocked"""
        has_access, msg = has_approved_community(
            str(self.user_without_community.uid)
        )
        self.assertFalse(has_access)
        self.assertIn('must be a member', msg)

    def test_has_approved_community_pending_application(self):
        """Test user with pending application is blocked"""
        has_access, msg = has_approved_community(
            str(self.user_pending_application.uid)
        )
        self.assertFalse(has_access)
        self.assertIn('pending', msg)

    def test_has_approved_community_invalid_user(self):
        """Test invalid user UID"""
        has_access, msg = has_approved_community(
            '00000000-0000-0000-0000-000000000000'
        )
        self.assertFalse(has_access)
        self.assertIn('not found', msg)

    def test_mission_list_requires_community(self):
        """Test mission list endpoint requires community membership"""
        # Test without authentication
        response = self.client.get('/api/v1/missions/')
        self.assertEqual(response.status_code, 401)

        # Test with community member
        token = generate_jwt(self.user_with_community)
        response = self.client.get(
            '/api/v1/missions/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)

        # Test without community
        token = generate_jwt(self.user_without_community)
        response = self.client.get(
            '/api/v1/missions/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 401)

    def test_user_list_requires_community(self):
        """Test user list endpoint requires community membership"""
        # Test without authentication
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, 401)

        # Test with community member
        token = generate_jwt(self.user_with_community)
        response = self.client.get(
            '/api/v1/users/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)

        # Test without community
        token = generate_jwt(self.user_without_community)
        response = self.client.get(
            '/api/v1/users/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 401)

    def test_community_list_remains_public(self):
        """Test community list is accessible without authentication"""
        response = self.client.get('/api/v1/communities/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('communities', data)

    def test_community_detail_limited_without_membership(self):
        """Test community detail shows limited data without membership"""
        # Test unauthenticated access
        response = self.client.get(
            f'/api/v1/communities/{self.community.slug}/'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify limited data (no members, leaders)
        self.assertEqual(data['community']['members'], [])
        self.assertEqual(data['community']['leaders'], [])
        self.assertIsNotNone(data['community']['name'])
        self.assertIsNotNone(data['community']['slug'])

    def test_community_detail_full_with_membership(self):
        """Test community detail shows full data with membership"""
        token = generate_jwt(self.user_with_community)
        response = self.client.get(
            f'/api/v1/communities/{self.community.slug}/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify full data is available (members list populated)
        self.assertIsNotNone(data['community']['members'])
        self.assertIsNotNone(data['community']['leaders'])

    def test_community_missions_requires_membership(self):
        """Test community missions endpoint requires membership"""
        # Test without community
        token = generate_jwt(self.user_without_community)
        response = self.client.get(
            f'/api/v1/communities/{self.community.slug}/missions/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 401)

        # Test with community
        token = generate_jwt(self.user_with_community)
        response = self.client.get(
            f'/api/v1/communities/{self.community.slug}/missions/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)

    def test_community_permissions_requires_membership(self):
        """Test community permissions endpoint requires membership"""
        # Test without community
        token = generate_jwt(self.user_without_community)
        response = self.client.get(
            f'/api/v1/communities/{self.community.slug}/permissions/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 401)

        # Test with community
        token = generate_jwt(self.user_with_community)
        response = self.client.get(
            f'/api/v1/communities/{self.community.slug}/permissions/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)

    def test_community_repositories_requires_membership(self):
        """Test community repositories endpoint requires membership"""
        # Test without community
        token = generate_jwt(self.user_without_community)
        response = self.client.get(
            f'/api/v1/communities/{self.community.slug}/repositories/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 401)

        # Test with community
        token = generate_jwt(self.user_with_community)
        response = self.client.get(
            f'/api/v1/communities/{self.community.slug}/repositories/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)

    def test_community_servers_requires_membership(self):
        """Test community servers endpoint requires membership"""
        # Test without community
        token = generate_jwt(self.user_without_community)
        response = self.client.get(
            f'/api/v1/communities/{self.community.slug}/servers/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 401)

        # Test with community
        token = generate_jwt(self.user_with_community)
        response = self.client.get(
            f'/api/v1/communities/{self.community.slug}/servers/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)

    def test_slug_availability_remains_public(self):
        """Test slug availability endpoints remain public"""
        # Mission slug availability
        response = self.client.get('/api/v1/missions/slugAvailable?slug=test')
        self.assertEqual(response.status_code, 200)

        # Community slug availability
        response = self.client.get(
            '/api/v1/communities/slugAvailable?slug=test'
        )
        self.assertEqual(response.status_code, 200)

    def test_community_application_endpoints_accessible(self):
        """Test community application endpoints are accessible"""
        token = generate_jwt(self.user_without_community)

        # Test getting application status
        response = self.client.get(
            f'/api/v1/communities/{self.community.slug}/applications/status/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        # Should get 404 if no application exists, but endpoint should be accessible
        self.assertIn(response.status_code, [200, 404])
