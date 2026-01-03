"""
API Compatibility Tests for User Endpoints

Tests that verify the Django Ninja API behaves exactly like the legacy TypeScript/Hapi.js API
for all user-related endpoints.
"""

from django.test import TestCase, Client
from api.models import User, Permission, Community
import json
import jwt
import time
from django.conf import settings


class UserAPICompatibilityTests(TestCase):
    """Test user endpoints for compatibility with legacy API"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create test community
        self.test_community = Community.objects.create(
            uid='c0000000-0000-0000-0000-000000000001',
            name='Test Community',
            tag='TEST',
            slug='test-community'
        )

        # Create test users WITH community
        self.test_user1 = User.objects.create(
            uid='a0000000-0000-0000-0000-000000000001',
            steam_id='76561198012345678',
            nickname='TestUser1',
            active=True,
            community=self.test_community
        )

        self.test_user2 = User.objects.create(
            uid='a0000000-0000-0000-0000-000000000002',
            steam_id='76561198087654321',
            nickname='TestUser2',
            active=True,
            community=self.test_community
        )

        self.admin_user = User.objects.create(
            uid='a0000000-0000-0000-0000-000000000003',
            steam_id='76561198011111111',
            nickname='AdminUser',
            active=True,
            community=self.test_community
        )

        # Create admin permission
        Permission.objects.create(
            uid='b0000000-0000-0000-0000-000000000001',
            permission='admin.user',
            user=self.admin_user
        )

        # Create JWT tokens
        self.test_token = self._create_token(self.test_user1, [])
        self.admin_token = self._create_token(self.admin_user, ['admin.user'])
    
    def _create_token(self, user, permissions):
        """Helper to create JWT token"""
        payload = {
            'user': {
                'uid': str(user.uid),
                'nickname': user.nickname,
                'steam_id': user.steam_id,
                'community': {
                    'uid': str(user.community.uid),
                    'name': user.community.name,
                    'tag': user.community.tag,
                    'slug': user.community.slug
                } if user.community else None,
                'active': user.active
            },
            'permissions': permissions,
            'iat': int(time.time()),
            'exp': int(time.time()) + settings.JWT_EXPIRES_IN,
            'iss': settings.JWT_ISSUER,
            'aud': settings.JWT_AUDIENCE,
            'sub': str(user.uid)
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    def test_get_user_list_no_auth(self):
        """Test GET /api/v1/users - Requires authentication and community membership"""
        response = self.client.get('/api/v1/users/')

        # Should return 401 Unauthorized (requires community membership)
        self.assertEqual(response.status_code, 401)

    def test_get_user_list_with_auth(self):
        """Test GET /api/v1/users - Returns paginated user list with auth"""
        response = self.client.get(
            '/api/v1/users/',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Response should contain pagination data and users
        data = response.json()
        self.assertIn('users', data)
        self.assertIn('limit', data)
        self.assertIn('offset', data)
        self.assertIn('count', data)
        self.assertIn('total', data)
        self.assertIn('moreAvailable', data)

        # Should have at least our test users
        self.assertGreaterEqual(data['count'], 2)
    
    def test_get_user_list_with_pagination(self):
        """Test GET /api/v1/users with pagination parameters"""
        response = self.client.get(
            '/api/v1/users/?limit=1&offset=0',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Response should respect pagination
        data = response.json()
        self.assertEqual(data['limit'], 1)
        self.assertEqual(data['offset'], 0)
        self.assertEqual(data['count'], 1)

    def test_get_user_list_with_search(self):
        """Test GET /api/v1/users with search parameter"""
        response = self.client.get(
            '/api/v1/users/?search=TestUser1',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Response should contain filtered users
        data = response.json()
        self.assertGreaterEqual(data['count'], 1)

        # Check that result contains our search term
        if data['count'] > 0:
            user_nicknames = [u['nickname'] for u in data['users']]
            self.assertTrue(any('TestUser1' in nick for nick in user_nicknames))

    def test_get_user_details(self):
        """Test GET /api/v1/users/{userUid} - Returns user details"""
        response = self.client.get(
            f'/api/v1/users/{self.test_user1.uid}/',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Response should contain user details
        data = response.json()
        self.assertIn('user', data)
        self.assertEqual(str(data['user']['uid']), str(self.test_user1.uid))
        self.assertEqual(data['user']['nickname'], self.test_user1.nickname)

    def test_get_user_details_not_found(self):
        """Test GET /api/v1/users/{userUid} with invalid UID - Should return 404"""
        response = self.client.get(
            '/api/v1/users/invalid-uid-12345/',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )

        # Should return 404 Not Found
        self.assertEqual(response.status_code, 404)
    
    def test_patch_user_details_as_admin(self):
        """Test PATCH /api/v1/users/{userUid} - Admin can modify user details"""
        response = self.client.patch(
            f'/api/v1/users/{self.test_user1.uid}/',
            data=json.dumps({'nickname': 'ModifiedNickname'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain updated user
        data = response.json()
        self.assertIn('user', data)
        self.assertEqual(data['user']['nickname'], 'ModifiedNickname')
        
        # Verify in database
        self.test_user1.refresh_from_db()
        self.assertEqual(self.test_user1.nickname, 'ModifiedNickname')
    
    def test_patch_user_details_as_non_admin(self):
        """Test PATCH /api/v1/users/{userUid} without admin permission - Should return 403"""
        response = self.client.patch(
            f'/api/v1/users/{self.test_user2.uid}/',
            data=json.dumps({'nickname': 'ModifiedNickname'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_patch_user_deactivate_as_admin(self):
        """Test PATCH /api/v1/users/{userUid} - Admin can deactivate user"""
        response = self.client.patch(
            f'/api/v1/users/{self.test_user1.uid}/',
            data=json.dumps({'active': False}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Verify in database
        self.test_user1.refresh_from_db()
        self.assertFalse(self.test_user1.active)
        
        # Reactivate for cleanup
        self.test_user1.active = True
        self.test_user1.save()
    
    def test_delete_user_as_admin(self):
        """Test DELETE /api/v1/users/{userUid} - Admin can delete user"""
        # Create a user to delete
        delete_user = User.objects.create(
            uid='a0000000-0000-0000-0000-000000000099',
            steam_id='76561198099999999',
            nickname='DeleteUser2',
            active=True
        )
        
        response = self.client.delete(
            f'/api/v1/users/{delete_user.uid}/',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should contain success indicator
        data = response.json()
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        
        # Verify user is deleted
        self.assertFalse(User.objects.filter(uid=delete_user.uid).exists())
    
    def test_delete_user_as_non_admin(self):
        """Test DELETE /api/v1/users/{userUid} without admin permission - Should return 403"""
        response = self.client.delete(
            f'/api/v1/users/{self.test_user2.uid}/',
            HTTP_AUTHORIZATION=f'Bearer {self.test_token}'
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_delete_user_not_found(self):
        """Test DELETE /api/v1/users/{userUid} with invalid UID - Should return 404"""
        response = self.client.delete(
            '/api/v1/users/invalid-uid-99999/',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        
        # Should return 404 Not Found
        self.assertEqual(response.status_code, 404)
    
    def test_get_user_missions_list(self):
        """Test GET /api/v1/users/{userUid}/missions - Returns user's missions"""
        response = self.client.get(f'/api/v1/users/{self.test_user1.uid}/missions/')
        
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
    
    def test_get_user_missions_list_with_pagination(self):
        """Test GET /api/v1/users/{userUid}/missions with pagination parameters"""
        response = self.client.get(f'/api/v1/users/{self.test_user1.uid}/missions/?limit=5&offset=0')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should respect pagination
        data = response.json()
        self.assertEqual(data['limit'], 5)
        self.assertEqual(data['offset'], 0)
    
    def test_get_user_missions_not_found(self):
        """Test GET /api/v1/users/{userUid}/missions with invalid UID - Should return 404"""
        response = self.client.get('/api/v1/users/invalid-uid-12345/missions/')
        
        # Should return 404 Not Found
        self.assertEqual(response.status_code, 404)
