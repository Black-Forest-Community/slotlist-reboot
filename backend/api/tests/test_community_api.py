"""
API Compatibility Tests for Community Endpoints

Tests that verify the Django Ninja API behaves exactly like the legacy TypeScript/Hapi.js API
for all community-related endpoints.
"""

from django.test import TestCase, Client
from api.models import User, Permission, Community, CommunityApplication
import json
import jwt
import time
from django.conf import settings


class CommunityAPICompatibilityTests(TestCase):
    """Test community endpoints for compatibility with legacy API"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users
        self.test_user = User.objects.create(
            uid='test-user-uid',
            steamId='76561198012345678',
            nickname='TestUser',
            active=True
        )
        
        self.founder_user = User.objects.create(
            uid='founder-user-uid',
            steamId='76561198087654321',
            nickname='FounderUser',
            active=True
        )
        
        # Create test community
        self.test_community = Community.objects.create(
            uid='test-community-uid',
            name='Test Community',
            tag='TC',
            slug='test-community',
            website='https://test-community.com',
            founder=self.founder_user
        )
        
        # Create founder permission
        Permission.objects.create(
            uid='founder-permission-uid',
            permission=f'community.{self.test_community.slug}.founder',
            user=self.founder_user,
            community=self.test_community
        )
        
        # Create JWT tokens
        self.test_token = self._create_token(self.test_user, [])
        self.founder_token = self._create_token(
            self.founder_user, 
            [f'community.{self.test_community.slug}.founder']
        )
    
    def _create_token(self, user, permissions):
        """Helper to create JWT token"""
        return jwt.encode(
            {
                'uid': user.uid,
                'nickname': user.nickname,
                'steamId': user.steamId,
                'permissions': permissions,
                'iat': int(time.time()),
                'exp': int(time.time()) + settings.JWT_EXPIRES_IN
            },
            settings.JWT_SECRET,
            algorithm='HS256'
        )
    
    def test_get_community_list_no_auth(self):
        """Test GET /api/v1/communities - Returns paginated community list"""
        response = self.client.get('/api/v1/communities')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain pagination data and communities
        data = response.json()
        self.assertIn('communities', data)
        self.assertIn('limit', data)
        self.assertIn('offset', data)
        self.assertIn('count', data)
        self.assertIn('total', data)
        self.assertIn('moreAvailable', data)
    
    def test_get_community_list_with_pagination(self):
        """Test GET /api/v1/communities with pagination parameters"""
        response = self.client.get('/api/v1/communities?limit=5&offset=0')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should respect pagination
        data = response.json()
        self.assertEqual(data['limit'], 5)
        self.assertEqual(data['offset'], 0)
    
    def test_get_community_list_with_search(self):
        """Test GET /api/v1/communities with search parameter"""
        response = self.client.get('/api/v1/communities?search=Test')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain filtered communities
        data = response.json()
        self.assertGreaterEqual(data['count'], 1)
    
    def test_check_slug_available_true(self):
        """Test GET /api/v1/communities/slugAvailable - Available slug returns true"""
        response = self.client.get('/api/v1/communities/slugAvailable?slug=available-slug-123')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should indicate slug is available
        data = response.json()
        self.assertIn('available', data)
        self.assertTrue(data['available'])
    
    def test_check_slug_available_false(self):
        """Test GET /api/v1/communities/slugAvailable - Taken slug returns false"""
        response = self.client.get(f'/api/v1/communities/slugAvailable?slug={self.test_community.slug}')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should indicate slug is not available
        data = response.json()
        self.assertIn('available', data)
        self.assertFalse(data['available'])
    
    def test_create_community_authenticated(self):
        """Test POST /api/v1/communities - Creates new community"""
        response = self.client.post(
            '/api/v1/communities',
            data=json.dumps({
                'name': 'New Community',
                'tag': 'NC',
                'slug': 'new-community-slug',
                'website': 'https://new-community.com'
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 201 Created
        self.assertIn(response.status_code, [200, 201])
        
        # Response should contain community and new token
        data = response.json()
        self.assertIn('community', data)
        self.assertIn('token', data)
        self.assertEqual(data['community']['slug'], 'new-community-slug')
        
        # Cleanup
        Community.objects.filter(slug='new-community-slug').delete()
    
    def test_create_community_unauthenticated(self):
        """Test POST /api/v1/communities without auth - Should return 401"""
        response = self.client.post(
            '/api/v1/communities',
            data=json.dumps({
                'name': 'New Community',
                'tag': 'NC',
                'slug': 'new-community-2',
                'website': 'https://new-community.com'
            }),
            content_type='application/json'
        )
        
        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, 401)
    
    def test_create_community_duplicate_slug(self):
        """Test POST /api/v1/communities with duplicate slug - Should return 409"""
        response = self.client.post(
            '/api/v1/communities',
            data=json.dumps({
                'name': 'Duplicate Community',
                'tag': 'DC',
                'slug': self.test_community.slug,
                'website': 'https://duplicate.com'
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 409 Conflict
        self.assertEqual(response.status_code, 409)
    
    def test_get_community_details(self):
        """Test GET /api/v1/communities/{communitySlug} - Returns community details"""
        response = self.client.get(f'/api/v1/communities/{self.test_community.slug}')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain community details
        data = response.json()
        self.assertIn('community', data)
        self.assertEqual(data['community']['slug'], self.test_community.slug)
        self.assertEqual(data['community']['name'], self.test_community.name)
    
    def test_get_community_details_not_found(self):
        """Test GET /api/v1/communities/{communitySlug} with invalid slug - Should return 404"""
        response = self.client.get('/api/v1/communities/invalid-slug-99999')
        
        # Should return 404 Not Found
        self.assertEqual(response.status_code, 404)
    
    def test_patch_community_as_founder(self):
        """Test PATCH /api/v1/communities/{communitySlug} - Founder can update community"""
        response = self.client.patch(
            f'/api/v1/communities/{self.test_community.slug}',
            data=json.dumps({'name': 'Updated Community Name'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.founder_token}'
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain updated community
        data = response.json()
        self.assertIn('community', data)
        self.assertEqual(data['community']['name'], 'Updated Community Name')
        
        # Verify in database
        self.test_community.refresh_from_db()
        self.assertEqual(self.test_community.name, 'Updated Community Name')
    
    def test_patch_community_as_non_founder(self):
        """Test PATCH /api/v1/communities/{communitySlug} without permission - Should return 403"""
        response = self.client.patch(
            f'/api/v1/communities/{self.test_community.slug}',
            data=json.dumps({'name': 'Unauthorized Update'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_delete_community_as_founder(self):
        """Test DELETE /api/v1/communities/{communitySlug} - Founder can delete community"""
        # Create a community to delete
        delete_community = Community.objects.create(
            uid='delete-community-uid',
            name='Delete Community',
            tag='DC',
            slug='delete-community',
            founder=self.founder_user
        )
        
        # Create founder permission for delete community
        Permission.objects.create(
            uid='delete-founder-permission-uid',
            permission=f'community.{delete_community.slug}.founder',
            user=self.founder_user,
            community=delete_community
        )
        
        founder_token_delete = self._create_token(
            self.founder_user, 
            [f'community.{delete_community.slug}.founder']
        )
        
        response = self.client.delete(
            f'/api/v1/communities/{delete_community.slug}',
            HTTP_AUTHORIZATION=f'Bearer {founder_token_delete}'
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain success indicator and new token
        data = response.json()
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('token', data)
        
        # Verify community is deleted
        self.assertFalse(Community.objects.filter(slug=delete_community.slug).exists())
    
    def test_delete_community_as_non_founder(self):
        """Test DELETE /api/v1/communities/{communitySlug} without permission - Should return 403"""
        response = self.client.delete(
            f'/api/v1/communities/{self.test_community.slug}',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_get_community_members_list(self):
        """Test GET /api/v1/communities/{communitySlug}/members - Returns member list"""
        response = self.client.get(f'/api/v1/communities/{self.test_community.slug}/members')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain pagination data and members
        data = response.json()
        self.assertIn('members', data)
        self.assertIn('limit', data)
        self.assertIn('offset', data)
        self.assertIn('count', data)
        self.assertIn('total', data)
        self.assertIn('moreAvailable', data)
    
    def test_get_community_missions_list(self):
        """Test GET /api/v1/communities/{communitySlug}/missions - Returns mission list"""
        response = self.client.get(f'/api/v1/communities/{self.test_community.slug}/missions')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain pagination data and missions
        data = response.json()
        self.assertIn('missions', data)
        self.assertIn('limit', data)
        self.assertIn('offset', data)
        self.assertIn('count', data)
        self.assertIn('total', data)
        self.assertIn('moreAvailable', data)
    
    def test_create_community_application(self):
        """Test POST /api/v1/communities/{communitySlug}/applications - Creates application"""
        response = self.client.post(
            f'/api/v1/communities/{self.test_community.slug}/applications',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 200 or 201
        self.assertIn(response.status_code, [200, 201])
        
        # Response should contain status
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'submitted')
        
        # Cleanup
        CommunityApplication.objects.filter(
            user=self.test_user,
            community=self.test_community
        ).delete()
    
    def test_get_community_application_status(self):
        """Test GET /api/v1/communities/{communitySlug}/applications/status - Returns application status"""
        # Create an application
        app = CommunityApplication.objects.create(
            uid='test-app-uid',
            user=self.test_user,
            community=self.test_community,
            status='submitted'
        )
        
        response = self.client.get(
            f'/api/v1/communities/{self.test_community.slug}/applications/status',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain application
        data = response.json()
        self.assertIn('application', data)
        self.assertEqual(data['application']['status'], 'submitted')
        
        # Cleanup
        app.delete()
