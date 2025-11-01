"""
Comprehensive tests for Role-Based Access Control (RBAC) functionality.
Tests implementation of Issue #69 based on role_based_access.feature

Test scenarios cover:
- UserProfile model and role field
- Role-based decorators
- Admin endpoints for user management
- Candidate profile access control
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from active_interview_app.models import UserProfile
from active_interview_app.decorators import check_user_permission


class UserProfileModelTest(TestCase):
    """
    Test cases for UserProfile model.
    Covers scenarios from @issue-70
    """

    def test_user_profile_created_on_user_registration(self):
        """
        Test that UserProfile is automatically created when a new user
        registers.
        Scenario: Role field exists on user model with default value
        """
        user = User.objects.create_user(
            username='testuser',
            password='SecurePass123'
        )
        # Verify profile was created
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsNotNone(user.profile)
        # Verify default role is 'candidate'
        self.assertEqual(user.profile.role, 'candidate')

    def test_user_profile_supports_all_role_types(self):
        """
        Test that UserProfile supports admin, interviewer, and candidate roles.
        Scenario: User model supports all three role types
        """
        # Create admin user
        admin_user = User.objects.create_user(
            username='admin_user',
            password='pass123'
        )
        admin_user.profile.role = UserProfile.ADMIN
        admin_user.profile.save()

        # Create interviewer user
        interviewer_user = User.objects.create_user(
            username='interviewer_user',
            password='pass123'
        )
        interviewer_user.profile.role = UserProfile.INTERVIEWER
        interviewer_user.profile.save()

        # Create candidate user
        candidate_user = User.objects.create_user(
            username='candidate_user',
            password='pass123'
        )
        candidate_user.profile.role = UserProfile.CANDIDATE
        candidate_user.profile.save()

        # Verify all roles
        admin_user.refresh_from_db()
        interviewer_user.refresh_from_db()
        candidate_user.refresh_from_db()

        self.assertEqual(admin_user.profile.role, 'admin')
        self.assertEqual(interviewer_user.profile.role, 'interviewer')
        self.assertEqual(candidate_user.profile.role, 'candidate')

    def test_user_profile_str_method(self):
        """Test UserProfile __str__ method"""
        user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        expected = f"{user.username} - candidate (local)"
        self.assertEqual(str(user.profile), expected)

    def test_user_profile_auth_provider_default(self):
        """Test that auth_provider defaults to 'local'"""
        user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        self.assertEqual(user.profile.auth_provider, 'local')


class AdminUserManagementTest(TestCase):
    """
    Test cases for admin user management endpoints.
    Covers scenarios from @issue-70 and @issue-71
    """

    def setUp(self):
        """Set up test users with different roles"""
        self.client = Client()

        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123'
        )
        self.admin_user.profile.role = UserProfile.ADMIN
        self.admin_user.profile.save()

        # Create interviewer user
        self.interviewer_user = User.objects.create_user(
            username='interviewer',
            password='interviewpass123'
        )
        self.interviewer_user.profile.role = UserProfile.INTERVIEWER
        self.interviewer_user.profile.save()

        # Create candidate user
        self.candidate_user = User.objects.create_user(
            username='candidate',
            password='candidatepass123'
        )
        self.candidate_user.profile.role = UserProfile.CANDIDATE
        self.candidate_user.profile.save()

        # Create another candidate for testing
        self.other_candidate = User.objects.create_user(
            username='othercandidate',
            password='pass123'
        )

    def test_admin_can_update_user_role(self):
        """
        Test admin can update user role via PATCH endpoint.
        Scenario: Admin can update user role via PATCH endpoint
        """
        self.client.force_login(self.admin_user)

        # Update other candidate's role to interviewer
        response = self.client.patch(
            f'/api/admin/users/{self.other_candidate.id}/role/',
            data=json.dumps({'role': 'interviewer'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['role'], 'interviewer')

        # Verify in database
        self.other_candidate.refresh_from_db()
        self.assertEqual(self.other_candidate.profile.role, 'interviewer')

    def test_non_admin_cannot_update_user_roles(self):
        """
        Test that non-admin users cannot update roles.
        Scenario: Non-admin cannot update user roles
        """
        self.client.force_login(self.candidate_user)

        # Try to update another user's role
        response = self.client.patch(
            f'/api/admin/users/{self.other_candidate.id}/role/',
            data=json.dumps({'role': 'admin'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 403)

        # Verify role wasn't changed
        self.other_candidate.refresh_from_db()
        self.assertEqual(self.other_candidate.profile.role, 'candidate')

    def test_admin_can_access_user_list(self):
        """
        Test admin can access admin routes.
        Scenario: Admin can access admin routes
        """
        self.client.force_login(self.admin_user)

        response = self.client.get('/api/admin/users/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('users', data)
        self.assertGreater(len(data['users']), 0)

    def test_candidate_cannot_access_admin_routes(self):
        """
        Test candidate cannot access admin routes.
        Scenario: Candidate cannot access admin routes
        """
        self.client.force_login(self.candidate_user)

        response = self.client.get('/api/admin/users/')
        self.assertEqual(response.status_code, 403)

        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Forbidden', data['error'])

    def test_interviewer_cannot_access_admin_routes(self):
        """
        Test interviewer cannot access admin routes.
        Scenario: Interviewer cannot access admin routes
        """
        self.client.force_login(self.interviewer_user)

        response = self.client.get('/api/admin/users/')
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_access_admin_routes(self):
        """
        Test unauthenticated user cannot access admin routes.
        Scenario: Unauthenticated user cannot access admin routes
        """
        # Don't login
        response = self.client.get('/api/admin/users/')
        # Should redirect to login or return 302
        self.assertIn(response.status_code, [302, 401])


class CandidateProfileAccessTest(TestCase):
    """
    Test cases for candidate profile access control.
    Covers scenarios from @issue-72
    """

    def setUp(self):
        """Set up test users"""
        self.client = Client()

        # Create admin
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            email='admin@test.com'
        )
        self.admin.profile.role = UserProfile.ADMIN
        self.admin.profile.save()

        # Create interviewer
        self.interviewer = User.objects.create_user(
            username='interviewer',
            password='interviewpass123'
        )
        self.interviewer.profile.role = UserProfile.INTERVIEWER
        self.interviewer.profile.save()

        # Create candidate 1
        self.candidate1 = User.objects.create_user(
            username='candidate1',
            password='pass123',
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )

        # Create candidate 2
        self.candidate2 = User.objects.create_user(
            username='candidate2',
            password='pass123',
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com'
        )

    def test_candidate_can_access_own_profile(self):
        """
        Test candidate can access their own profile.
        Scenario: Candidate can access their own profile
        """
        self.client.force_login(self.candidate1)

        response = self.client.get(f'/api/candidates/{self.candidate1.id}/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['id'], self.candidate1.id)
        self.assertEqual(data['username'], 'candidate1')
        self.assertEqual(data['email'], 'john@example.com')

    def test_candidate_cannot_access_another_candidate_profile(self):
        """
        Test candidate cannot access another candidate's profile.
        Scenario: Candidate cannot access another candidate's profile
        """
        self.client.force_login(self.candidate1)

        response = self.client.get(f'/api/candidates/{self.candidate2.id}/')
        self.assertEqual(response.status_code, 403)

        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Forbidden', data['error'])

    def test_candidate_can_update_own_profile(self):
        """
        Test candidate can update their own profile.
        Scenario: Candidate can update their own profile
        """
        self.client.force_login(self.candidate1)

        response = self.client.patch(
            f'/api/candidates/{self.candidate1.id}/update/',
            data=json.dumps({
                'first_name': 'Updated Name',
                'email': 'newemail@example.com'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['first_name'], 'Updated Name')
        self.assertEqual(data['email'], 'newemail@example.com')

        # Verify in database
        self.candidate1.refresh_from_db()
        self.assertEqual(self.candidate1.first_name, 'Updated Name')
        self.assertEqual(self.candidate1.email, 'newemail@example.com')

    def test_candidate_cannot_update_another_candidate_profile(self):
        """
        Test candidate cannot update another candidate's profile.
        Scenario: Candidate cannot update another candidate's profile
        """
        self.client.force_login(self.candidate1)

        response = self.client.patch(
            f'/api/candidates/{self.candidate2.id}/update/',
            data=json.dumps({'first_name': 'Hacked Name'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 403)

        # Verify profile wasn't modified
        self.candidate2.refresh_from_db()
        self.assertEqual(self.candidate2.first_name, 'Jane')

    def test_admin_can_view_any_candidate_profile(self):
        """
        Test admin can view any candidate's profile.
        Scenario: Admin can access any candidate's profile
        """
        self.client.force_login(self.admin)

        response = self.client.get(f'/api/candidates/{self.candidate1.id}/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['username'], 'candidate1')

    def test_interviewer_can_view_any_candidate_profile(self):
        """
        Test interviewer can view any candidate's profile.
        Scenario: Interviewer can access any candidate's profile
        """
        self.client.force_login(self.interviewer)

        response = self.client.get(f'/api/candidates/{self.candidate1.id}/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['username'], 'candidate1')


class RBACDecoratorTest(TestCase):
    """Test RBAC decorator helper functions"""

    def setUp(self):
        """Set up test users"""
        self.admin = User.objects.create_user(
            username='admin', password='pass'
        )
        self.admin.profile.role = UserProfile.ADMIN
        self.admin.profile.save()

        self.interviewer = User.objects.create_user(
            username='interviewer', password='pass'
        )
        self.interviewer.profile.role = UserProfile.INTERVIEWER
        self.interviewer.profile.save()

        self.candidate = User.objects.create_user(
            username='candidate', password='pass'
        )

    def test_check_user_permission_admin_access(self):
        """Test admin can access with allow_admin=True"""
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.admin

        result = check_user_permission(
            request, 123,
            allow_admin=True,
            allow_interviewer=False,
            allow_self=False
        )
        self.assertTrue(result)

    def test_check_user_permission_interviewer_access(self):
        """Test interviewer access with allow_interviewer=True"""
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.interviewer

        result = check_user_permission(
            request, 123,
            allow_admin=False,
            allow_interviewer=True,
            allow_self=False
        )
        self.assertTrue(result)

    def test_check_user_permission_self_access(self):
        """Test user can access own data with allow_self=True"""
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.candidate

        result = check_user_permission(
            request, self.candidate.id,
            allow_admin=False,
            allow_interviewer=False,
            allow_self=True
        )
        self.assertTrue(result)

    def test_check_user_permission_denied(self):
        """Test permission denied when no flags match"""
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.candidate

        result = check_user_permission(
            request, 999,  # Different user ID
            allow_admin=False,
            allow_interviewer=False,
            allow_self=True
        )
        self.assertFalse(result)


class RBACEdgeCasesTest(TestCase):
    """Test edge cases and error handling for RBAC"""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123'
        )
        self.admin.profile.role = UserProfile.ADMIN
        self.admin.profile.save()

    def test_update_role_with_invalid_role(self):
        """Test updating user role with invalid role value"""
        self.client.force_login(self.admin)

        user = User.objects.create_user(username='testuser', password='pass')

        response = self.client.patch(
            f'/api/admin/users/{user.id}/role/',
            data=json.dumps({'role': 'invalid_role'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_update_role_nonexistent_user(self):
        """Test updating role for non-existent user"""
        self.client.force_login(self.admin)

        response = self.client.patch(
            '/api/admin/users/99999/role/',
            data=json.dumps({'role': 'admin'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)

    def test_update_role_with_invalid_json(self):
        """Test updating role with malformed JSON"""
        self.client.force_login(self.admin)

        user = User.objects.create_user(username='testuser', password='pass')

        response = self.client.patch(
            f'/api/admin/users/{user.id}/role/',
            data='invalid json',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_view_nonexistent_candidate_profile(self):
        """Test viewing non-existent candidate profile"""
        self.client.force_login(self.admin)

        response = self.client.get('/api/candidates/99999/')
        self.assertEqual(response.status_code, 404)

    def test_update_profile_with_invalid_method(self):
        """Test profile update with wrong HTTP method"""
        self.client.force_login(self.admin)

        response = self.client.get(f'/api/admin/users/{self.admin.id}/role/')
        self.assertEqual(response.status_code, 405)
