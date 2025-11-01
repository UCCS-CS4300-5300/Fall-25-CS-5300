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



class UserProfileViewTest(TestCase):
    """
    Test cases for user profile view (HTML-based).
    Tests that admins and interviewers can view candidate profiles.
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

    def test_user_can_view_own_profile(self):
        """Test user can view their own profile via user profile view"""
        self.client.force_login(self.candidate1)

        response = self.client.get(f'/user/{self.candidate1.id}/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile_user', response.context)
        self.assertEqual(response.context['profile_user'].id, self.candidate1.id)
        self.assertTrue(response.context['is_own_profile'])

    def test_candidate_cannot_view_another_candidate_profile(self):
        """Test candidate cannot view another candidate's profile"""
        self.client.force_login(self.candidate1)

        response = self.client.get(f'/user/{self.candidate2.id}/profile/')
        self.assertEqual(response.status_code, 403)

    def test_admin_can_view_any_user_profile(self):
        """Test admin can view any user's profile"""
        self.client.force_login(self.admin)

        response = self.client.get(f'/user/{self.candidate1.id}/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile_user', response.context)
        self.assertEqual(response.context['profile_user'].username, 'candidate1')
        self.assertFalse(response.context['is_own_profile'])

    def test_interviewer_can_view_any_user_profile(self):
        """Test interviewer can view any user's profile"""
        self.client.force_login(self.interviewer)

        response = self.client.get(f'/user/{self.candidate1.id}/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile_user', response.context)
        self.assertEqual(response.context['profile_user'].username, 'candidate1')

    def test_view_nonexistent_user_returns_404(self):
        """Test viewing non-existent user profile returns 404"""
        self.client.force_login(self.admin)

        response = self.client.get('/user/99999/profile/')
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_cannot_view_profiles(self):
        """Test unauthenticated users cannot view profiles"""
        response = self.client.get(f'/user/{self.candidate1.id}/profile/')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


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



class RoleChangeRequestTest(TestCase):
    """
    Test cases for role change request functionality.
    Tests candidate-to-interviewer role change requests and admin approval.
    """

    def setUp(self):
        """Set up test users and client"""
        self.client = Client()

        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123'
        )
        self.admin.profile.role = UserProfile.ADMIN
        self.admin.profile.save()

        # Create candidate user
        self.candidate = User.objects.create_user(
            username='candidate',
            password='candidatepass123'
        )
        self.candidate.profile.role = UserProfile.CANDIDATE
        self.candidate.profile.save()

        # Create interviewer user
        self.interviewer = User.objects.create_user(
            username='interviewer',
            password='interviewerpass123'
        )
        self.interviewer.profile.role = UserProfile.INTERVIEWER
        self.interviewer.profile.save()

    def test_candidate_can_submit_role_request(self):
        """Test that a candidate can submit a role change request"""
        self.client.force_login(self.candidate)

        response = self.client.post('/profile/request-role-change/', {
            'requested_role': 'interviewer',
            'reason': 'I have 5 years of experience conducting interviews.'
        })

        # Should redirect on success
        self.assertEqual(response.status_code, 302)

        # Verify request was created
        from active_interview_app.models import RoleChangeRequest
        request = RoleChangeRequest.objects.filter(
            user=self.candidate
        ).first()
        self.assertIsNotNone(request)
        self.assertEqual(request.requested_role, 'interviewer')
        self.assertEqual(request.status, 'pending')

    def test_candidate_cannot_submit_duplicate_pending_request(self):
        """
        Test that a candidate cannot submit another request
        if they already have a pending one
        """
        from active_interview_app.models import RoleChangeRequest

        # Create pending request
        RoleChangeRequest.objects.create(
            user=self.candidate,
            requested_role='interviewer',
            current_role='candidate',
            status=RoleChangeRequest.PENDING
        )

        self.client.force_login(self.candidate)

        response = self.client.post('/profile/request-role-change/', {
            'requested_role': 'interviewer',
            'reason': 'Another reason'
        })

        # Should redirect back with error message
        self.assertEqual(response.status_code, 302)

        # Should still only have one request
        count = RoleChangeRequest.objects.filter(
            user=self.candidate,
            status=RoleChangeRequest.PENDING
        ).count()
        self.assertEqual(count, 1)

    def test_unauthenticated_cannot_submit_request(self):
        """Test that unauthenticated users cannot submit requests"""
        response = self.client.post('/profile/request-role-change/', {
            'requested_role': 'interviewer',
            'reason': 'I want to be an interviewer'
        })

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_admin_can_view_role_requests(self):
        """Test that admins can view the role requests list"""
        from active_interview_app.models import RoleChangeRequest

        # Create some requests
        RoleChangeRequest.objects.create(
            user=self.candidate,
            requested_role='interviewer',
            current_role='candidate',
            status=RoleChangeRequest.PENDING
        )

        self.client.force_login(self.admin)
        response = self.client.get('/role-requests/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('pending_requests', response.context)
        self.assertEqual(response.context['pending_requests'].count(), 1)

    def test_non_admin_cannot_view_role_requests(self):
        """Test that non-admins cannot access role requests list"""
        self.client.force_login(self.candidate)
        response = self.client.get('/role-requests/')

        self.assertEqual(response.status_code, 403)

    def test_admin_can_approve_role_request(self):
        """Test that admins can approve role change requests"""
        from active_interview_app.models import RoleChangeRequest

        # Create pending request
        request_obj = RoleChangeRequest.objects.create(
            user=self.candidate,
            requested_role='interviewer',
            current_role='candidate',
            status=RoleChangeRequest.PENDING
        )

        self.client.force_login(self.admin)
        response = self.client.post(
            f'/role-requests/{request_obj.id}/review/',
            {'action': 'approve'}
        )

        # Should redirect on success
        self.assertEqual(response.status_code, 302)

        # Verify request was approved
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'approved')
        self.assertEqual(request_obj.reviewed_by, self.admin)
        self.assertIsNotNone(request_obj.reviewed_at)

        # Verify user's role was updated
        self.candidate.profile.refresh_from_db()
        self.assertEqual(self.candidate.profile.role, 'interviewer')

    def test_admin_can_reject_role_request(self):
        """Test that admins can reject role change requests"""
        from active_interview_app.models import RoleChangeRequest

        # Create pending request
        request_obj = RoleChangeRequest.objects.create(
            user=self.candidate,
            requested_role='interviewer',
            current_role='candidate',
            status=RoleChangeRequest.PENDING
        )

        self.client.force_login(self.admin)
        response = self.client.post(
            f'/role-requests/{request_obj.id}/review/',
            {
                'action': 'reject',
                'admin_notes': 'Need more experience'
            }
        )

        # Should redirect on success
        self.assertEqual(response.status_code, 302)

        # Verify request was rejected
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'rejected')
        self.assertEqual(request_obj.reviewed_by, self.admin)
        self.assertEqual(request_obj.admin_notes, 'Need more experience')

        # Verify user's role was NOT updated
        self.candidate.profile.refresh_from_db()
        self.assertEqual(self.candidate.profile.role, 'candidate')

    def test_non_admin_cannot_review_requests(self):
        """Test that non-admins cannot approve or reject requests"""
        from active_interview_app.models import RoleChangeRequest

        request_obj = RoleChangeRequest.objects.create(
            user=self.candidate,
            requested_role='interviewer',
            current_role='candidate',
            status=RoleChangeRequest.PENDING
        )

        self.client.force_login(self.interviewer)
        response = self.client.post(
            f'/role-requests/{request_obj.id}/review/',
            {'action': 'approve'}
        )

        self.assertEqual(response.status_code, 403)

        # Verify request was not approved
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'pending')

    def test_profile_shows_pending_request_status(self):
        """Test that profile page shows pending request status"""
        from active_interview_app.models import RoleChangeRequest

        RoleChangeRequest.objects.create(
            user=self.candidate,
            requested_role='interviewer',
            current_role='candidate',
            status=RoleChangeRequest.PENDING
        )

        self.client.force_login(self.candidate)
        response = self.client.get('/profile/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['has_pending_request'])


class CandidateSearchTest(TestCase):
    """
    Test cases for candidate search functionality.
    Tests that admins and interviewers can search for candidates.
    """

    def setUp(self):
        """Set up test users and client"""
        self.client = Client()

        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123',
            email='admin@example.com'
        )
        self.admin.profile.role = UserProfile.ADMIN
        self.admin.profile.save()

        # Create interviewer user
        self.interviewer = User.objects.create_user(
            username='interviewer',
            password='interviewerpass123',
            email='interviewer@example.com'
        )
        self.interviewer.profile.role = UserProfile.INTERVIEWER
        self.interviewer.profile.save()

        # Create candidate users
        self.candidate1 = User.objects.create_user(
            username='john_doe',
            password='pass123',
            email='john@example.com',
            first_name='John',
            last_name='Doe'
        )
        self.candidate1.profile.role = UserProfile.CANDIDATE
        self.candidate1.profile.save()

        self.candidate2 = User.objects.create_user(
            username='jane_smith',
            password='pass123',
            email='jane@example.com',
            first_name='Jane',
            last_name='Smith'
        )
        self.candidate2.profile.role = UserProfile.CANDIDATE
        self.candidate2.profile.save()

        self.candidate3 = User.objects.create_user(
            username='bob_johnson',
            password='pass123',
            email='bob@example.com'
        )
        self.candidate3.profile.role = UserProfile.CANDIDATE
        self.candidate3.profile.save()

    def test_admin_can_access_search(self):
        """Test that admins can access the search page"""
        self.client.force_login(self.admin)
        response = self.client.get('/candidates/search/')

        self.assertEqual(response.status_code, 200)

    def test_interviewer_can_access_search(self):
        """Test that interviewers can access the search page"""
        self.client.force_login(self.interviewer)
        response = self.client.get('/candidates/search/')

        self.assertEqual(response.status_code, 200)

    def test_candidate_cannot_access_search(self):
        """Test that candidates cannot access the search page"""
        self.client.force_login(self.candidate1)
        response = self.client.get('/candidates/search/')

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_access_search(self):
        """Test that unauthenticated users cannot access search"""
        response = self.client.get('/candidates/search/')

        # Decorator returns 401 for unauthenticated users
        self.assertEqual(response.status_code, 401)

    def test_search_by_username_returns_matches(self):
        """Test that searching by username returns matching candidates"""
        self.client.force_login(self.admin)
        response = self.client.get('/candidates/search/?q=john')

        self.assertEqual(response.status_code, 200)
        self.assertIn('candidates', response.context)
        candidates = response.context['candidates']
        self.assertEqual(candidates.count(), 2)  # john_doe and bob_johnson

    def test_search_exact_username_match(self):
        """Test exact username search"""
        self.client.force_login(self.admin)
        response = self.client.get('/candidates/search/?q=jane_smith')

        self.assertEqual(response.status_code, 200)
        candidates = response.context['candidates']
        self.assertEqual(candidates.count(), 1)
        self.assertEqual(candidates[0].username, 'jane_smith')

    def test_search_case_insensitive(self):
        """Test that search is case-insensitive"""
        self.client.force_login(self.admin)
        response = self.client.get('/candidates/search/?q=JOHN')

        self.assertEqual(response.status_code, 200)
        candidates = response.context['candidates']
        self.assertGreater(candidates.count(), 0)

    def test_search_no_query_shows_message(self):
        """Test that empty search shows appropriate message"""
        self.client.force_login(self.admin)
        response = self.client.get('/candidates/search/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query'], '')

    def test_search_no_results(self):
        """Test search with no matching results"""
        self.client.force_login(self.admin)
        response = self.client.get('/candidates/search/?q=nonexistent_user')

        self.assertEqual(response.status_code, 200)
        candidates = response.context['candidates']
        self.assertEqual(candidates.count(), 0)

    def test_search_only_returns_candidates(self):
        """
        Test that search only returns users with candidate role,
        not admins or interviewers
        """
        # Create an admin with 'john' in username
        User.objects.create_user(
            username='john_admin',
            password='pass123'
        ).profile.role = UserProfile.ADMIN

        self.client.force_login(self.admin)
        response = self.client.get('/candidates/search/?q=john')

        candidates = response.context['candidates']
        # Should only find john_doe and bob_johnson, not john_admin
        for candidate in candidates:
            self.assertEqual(candidate.profile.role, UserProfile.CANDIDATE)
