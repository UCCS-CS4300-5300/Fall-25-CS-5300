"""
Additional comprehensive tests for views to increase coverage
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from active_interview_app.models import (
    UploadedResume,
    UploadedJobListing
)
from unittest.mock import patch
from .test_credentials import TEST_PASSWORD


class IndexViewTest(TestCase):
    """Test cases for index view"""

    def test_index_view_get(self):
        """Test GET request to index view"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')


class AboutUsViewTest(TestCase):
    """Test cases for about us view"""

    def test_aboutus_view_get(self):
        """Test GET request to about us view"""
        response = self.client.get(reverse('about-us'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about-us.html')


class ResultsViewTest(TestCase):
    """Test cases for results view"""

    def test_results_view_get(self):
        """Test GET request to results view"""
        response = self.client.get(reverse('results'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'results.html')


class LoggedInViewTest(TestCase):
    """Test cases for loggedin view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client = Client()

    def test_loggedin_view_requires_login(self):
        """Test loggedin view requires authentication"""
        response = self.client.get(reverse('loggedin'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_loggedin_view_authenticated(self):
        """Test loggedin view when authenticated"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        response = self.client.get(reverse('loggedin'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'loggedinindex.html')


class ProfileViewTest(TestCase):
    """Test cases for profile view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client = Client()

    def test_profile_view_requires_login(self):
        """Test profile view requires authentication"""
        response = self.client.get(reverse('profile'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_profile_view_authenticated(self):
        """Test profile view when authenticated"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')

    def test_profile_view_shows_user_resumes(self):
        """Test profile view shows user's resumes"""
        self.client.login(username='testuser', password=TEST_PASSWORD)

        resume = UploadedResume.objects.create(
            user=self.user,
            content="Test content",
            title="Test Resume"
        )

        response = self.client.get(reverse('profile'))
        self.assertIn('resumes', response.context)
        self.assertIn(resume, response.context['resumes'])

    def test_profile_view_shows_user_job_listings(self):
        """Test profile view shows user's job listings"""
        self.client.login(username='testuser', password=TEST_PASSWORD)

        job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content="Job content",
            filename="job.txt",
            title="Test Job"
        )

        response = self.client.get(reverse('profile'))
        self.assertIn('job_listings', response.context)
        self.assertIn(job_listing, response.context['job_listings'])

    def test_profile_view_shows_spending_data(self):
        """Test profile view shows monthly spending data (Issue #15.10)"""
        from decimal import Decimal
        from active_interview_app.spending_tracker_models import (
            MonthlySpending, MonthlySpendingCap
        )

        self.client.login(username='testuser', password=TEST_PASSWORD)

        # Create spending cap
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )

        # Create spending record
        spending = MonthlySpending.get_current_month()
        spending.llm_cost_usd = Decimal('50.00')
        spending.total_cost_usd = Decimal('50.00')
        spending.llm_requests = 10
        spending.total_requests = 10
        spending.save()

        response = self.client.get(reverse('profile'))

        # Check spending_data is in context
        self.assertIn('spending_data', response.context)
        spending_data = response.context['spending_data']

        # Verify spending data content
        self.assertIsNotNone(spending_data)
        self.assertEqual(spending_data['total_cost'], Decimal('50.00'))
        self.assertEqual(spending_data['llm_requests'], 10)
        self.assertTrue(spending_data['cap_status']['has_cap'])
        self.assertEqual(spending_data['cap_status']['cap_amount'], 200.00)

        # Check that spending data is displayed in the response
        self.assertContains(response, 'Monthly API Spending')
        self.assertContains(response, '$50.00')
        self.assertContains(response, '$200.00')

    def test_spending_resets_monthly(self):
        """Test that spending resets automatically when a new month starts (Issue #15.10)"""
        from decimal import Decimal
        from active_interview_app.spending_tracker_models import MonthlySpending
        from datetime import datetime
        from unittest.mock import patch

        self.client.login(username='testuser', password=TEST_PASSWORD)

        # Create spending for November 2025
        MonthlySpending.objects.create(
            year=2025,
            month=11,
            total_cost_usd=Decimal('150.00'),
            llm_cost_usd=Decimal('150.00'),
            llm_requests=100,
            total_requests=100,
            premium_cost_usd=Decimal('150.00'),
            premium_requests=100
        )

        # Mock current date to be November 2025
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime(2025, 11, 15, 12, 0, 0)

            # Get current month spending (should be November with $150)
            current = MonthlySpending.get_current_month()
            self.assertEqual(current.year, 2025)
            self.assertEqual(current.month, 11)
            self.assertEqual(current.total_cost_usd, Decimal('150.00'))
            self.assertEqual(current.total_requests, 100)

        # Mock current date to be December 2025 (new month)
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime(2025, 12, 1, 0, 0, 0)

            # Get current month spending (should be December with $0)
            current = MonthlySpending.get_current_month()
            self.assertEqual(current.year, 2025)
            self.assertEqual(current.month, 12)
            # New month should start at zero
            self.assertEqual(current.total_cost_usd, Decimal('0.0000'))
            self.assertEqual(current.total_requests, 0)
            self.assertEqual(current.premium_requests, 0)

        # Verify November data is still preserved
        nov_data = MonthlySpending.objects.get(year=2025, month=11)
        self.assertEqual(nov_data.total_cost_usd, Decimal('150.00'))
        self.assertEqual(nov_data.total_requests, 100)

        # Verify we now have 2 separate month records
        self.assertEqual(MonthlySpending.objects.count(), 2)


class ResumeDetailViewTest(TestCase):
    """Test cases for resume detail view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.resume = UploadedResume.objects.create(
            user=self.user,
            content="Test content",
            title="Test Resume"
        )
        self.client = Client()

    def test_resume_detail_requires_login(self):
        """Test resume detail view requires authentication"""
        response = self.client.get(
            reverse('resume_detail', args=[self.resume.id])
        )
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_resume_detail_authenticated(self):
        """Test resume detail view when authenticated"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        response = self.client.get(
            reverse('resume_detail', args=[self.resume.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/resume_detail.html')
        self.assertEqual(response.context['resume'], self.resume)

    def test_resume_detail_nonexistent_resume(self):
        """Test resume detail view with nonexistent resume"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        response = self.client.get(reverse('resume_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)


class DeleteResumeViewTest(TestCase):
    """Test cases for delete resume view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.resume = UploadedResume.objects.create(
            user=self.user,
            content="Test content",
            title="Test Resume"
        )
        self.client = Client()

    def test_delete_resume_requires_login(self):
        """Test delete resume requires authentication"""
        response = self.client.post(
            reverse('delete_resume', args=[self.resume.id])
        )
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        # Resume should still exist
        self.assertTrue(UploadedResume.objects.filter(
            id=self.resume.id).exists())

    def test_delete_resume_post(self):
        """Test deleting resume with POST request"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        resume_id = self.resume.id

        response = self.client.post(reverse('delete_resume', args=[resume_id]))

        # Should redirect to profile
        self.assertRedirects(response, reverse('profile'))
        # Resume should be deleted
        self.assertFalse(UploadedResume.objects.filter(id=resume_id).exists())

    def test_delete_resume_get(self):
        """Test GET request to delete resume redirects"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        resume_id = self.resume.id

        response = self.client.get(reverse('delete_resume', args=[resume_id]))

        # Should redirect to profile
        self.assertRedirects(response, reverse('profile'))
        # Resume should still exist
        self.assertTrue(UploadedResume.objects.filter(id=resume_id).exists())

    def test_delete_resume_different_user(self):
        """Test user cannot delete another user's resume"""
        User.objects.create_user(
            username='otheruser',
            password=TEST_PASSWORD
        )
        self.client.login(username='otheruser', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('delete_resume', args=[self.resume.id])
        )

        # Should return 404
        self.assertEqual(response.status_code, 404)
        # Resume should still exist
        self.assertTrue(UploadedResume.objects.filter(
            id=self.resume.id).exists())


class JobPostingDetailViewTest(TestCase):
    """Test cases for job posting detail view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content="Job content",
            filename="job.txt",
            title="Test Job"
        )
        self.client = Client()

    def test_job_posting_detail_requires_login(self):
        """Test job posting detail view requires authentication"""
        response = self.client.get(
            reverse('job_posting_detail', args=[self.job_listing.id])
        )
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_job_posting_detail_authenticated(self):
        """Test job posting detail view when authenticated"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        response = self.client.get(
            reverse('job_posting_detail', args=[self.job_listing.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/job_posting_detail.html')
        self.assertEqual(response.context['job'], self.job_listing)

    def test_job_posting_detail_nonexistent_job(self):
        """Test job posting detail view with nonexistent job"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        response = self.client.get(
            reverse('job_posting_detail', args=[99999])
        )
        self.assertEqual(response.status_code, 404)


class DeleteJobViewTest(TestCase):
    """Test cases for delete job view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content="Job content",
            filename="job.txt",
            title="Test Job"
        )
        self.client = Client()

    def test_delete_job_requires_login(self):
        """Test delete job requires authentication"""
        response = self.client.post(
            reverse('delete_job', args=[self.job_listing.id])
        )
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        # Job should still exist
        self.assertTrue(
            UploadedJobListing.objects.filter(id=self.job_listing.id).exists()
        )

    def test_delete_job_post(self):
        """Test deleting job with POST request"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        job_id = self.job_listing.id

        response = self.client.post(reverse('delete_job', args=[job_id]))

        # Should redirect to profile
        self.assertRedirects(response, reverse('profile'))
        # Job should be deleted
        self.assertFalse(UploadedJobListing.objects.filter(id=job_id).exists())

    def test_delete_job_different_user(self):
        """Test user cannot delete another user's job"""
        User.objects.create_user(
            username='otheruser',
            password=TEST_PASSWORD
        )
        self.client.login(username='otheruser', password=TEST_PASSWORD)

        response = self.client.post(
            reverse('delete_job', args=[self.job_listing.id])
        )

        # Should return 404
        self.assertEqual(response.status_code, 404)
        # Job should still exist
        self.assertTrue(
            UploadedJobListing.objects.filter(id=self.job_listing.id).exists()
        )


class EditResumeViewTest(TestCase):
    """Test cases for edit resume view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.resume = UploadedResume.objects.create(
            user=self.user,
            content="Original content",
            title="Original Title"
        )
        self.client = Client()

    def test_edit_resume_get(self):
        """Test GET request to edit resume view"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        response = self.client.get(
            reverse('edit_resume', args=[self.resume.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/edit_document.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['document'], self.resume)

    def test_edit_resume_post_valid(self):
        """Test POST request to edit resume with valid data"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        data = {
            'title': 'Updated Title',
            'content': 'Updated content'
        }
        response = self.client.post(
            reverse('edit_resume', args=[self.resume.id]),
            data
        )

        # Should redirect to resume detail
        self.assertRedirects(
            response,
            reverse('resume_detail', args=[self.resume.id])
        )

        # Check that resume was updated
        self.resume.refresh_from_db()
        self.assertEqual(self.resume.title, 'Updated Title')
        self.assertEqual(self.resume.content, 'Updated content')

    def test_edit_resume_nonexistent(self):
        """Test editing nonexistent resume returns 404"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        response = self.client.get(reverse('edit_resume', args=[99999]))
        self.assertEqual(response.status_code, 404)


class EditJobPostingViewTest(TestCase):
    """Test cases for edit job posting view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content="Original content",
            filename="job.txt",
            title="Original Job"
        )
        self.client = Client()

    def test_edit_job_posting_requires_login(self):
        """Test edit job posting requires authentication"""
        response = self.client.get(
            reverse('edit_job_posting', args=[self.job_listing.id])
        )
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_edit_job_posting_get(self):
        """Test GET request to edit job posting view"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        response = self.client.get(
            reverse('edit_job_posting', args=[self.job_listing.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/edit_job_posting.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['job_listing'], self.job_listing)

    def test_edit_job_posting_post_valid(self):
        """Test POST request to edit job posting with valid data"""
        self.client.login(username='testuser', password=TEST_PASSWORD)
        data = {
            'title': 'Updated Job',
            'content': 'Updated job content'
        }
        response = self.client.post(
            reverse('edit_job_posting', args=[self.job_listing.id]),
            data
        )

        # Should redirect to job posting detail
        self.assertRedirects(
            response,
            reverse('job_posting_detail', args=[self.job_listing.id])
        )

        # Check that job posting was updated
        self.job_listing.refresh_from_db()
        self.assertEqual(self.job_listing.title, 'Updated Job')
        self.assertEqual(self.job_listing.content, 'Updated job content')

    def test_edit_job_posting_different_user(self):
        """Test user cannot edit another user's job posting"""
        User.objects.create_user(
            username='otheruser',
            password=TEST_PASSWORD
        )
        self.client.login(username='otheruser', password=TEST_PASSWORD)

        response = self.client.get(
            reverse('edit_job_posting', args=[self.job_listing.id])
        )

        # Should return 404
        self.assertEqual(response.status_code, 404)


class DocumentListViewTest(TestCase):
    """Test cases for document list view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client = Client()

    def test_document_list_view_get(self):
        """Test GET request to document list view"""
        # Document list requires login
        self.client.login(username='testuser', password=TEST_PASSWORD)
        response = self.client.get(reverse('document-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/document-list.html')


class OpenAIClientTest(TestCase):
    """Test cases for OpenAI client utility functions"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.client = Client()

    @patch('active_interview_app.openai_utils.settings')
    def testai_available_without_api_key(self, mock_settings):
        """Test ai_available returns False when API key is not set"""
        from active_interview_app.openai_utils import ai_available
        import active_interview_app.openai_utils as openai_utils

        # Reset the global client
        openai_utils._openai_client = None

        mock_settings.OPENAI_API_KEY = None

        result = ai_available()
        self.assertFalse(result)

    @patch('active_interview_app.openai_utils.settings')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_get_openai_client_raises_error_without_key(self,
                                                        mock_openai,
                                                        mock_settings):
        """Test get_openai_client raises error when API key is not set"""
        from active_interview_app.openai_utils import get_openai_client
        import active_interview_app.openai_utils as openai_utils

        # Reset the global client
        openai_utils._openai_client = None

        mock_settings.OPENAI_API_KEY = None

        with self.assertRaises(ValueError) as context:
            get_openai_client()

        self.assertIn("No OpenAI API key available", str(context.exception))

    def test_ai_unavailable_json(self):
        """Test _ai_unavailable_json returns proper JSON response"""
        from active_interview_app.views import _ai_unavailable_json

        response = _ai_unavailable_json()

        self.assertEqual(response.status_code, 503)
        import json
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'],
                         'AI features are disabled on this server.')
