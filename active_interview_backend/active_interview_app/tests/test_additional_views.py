"""
Additional comprehensive tests for views to increase coverage
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from active_interview_app.models import (
    UploadedResume,
    UploadedJobListing,
    Chat
)
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock


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
        response = self.client.get(reverse('aboutus'))
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
            password='testpass123'
        )
        self.client = Client()

    def test_loggedin_view_requires_login(self):
        """Test loggedin view requires authentication"""
        response = self.client.get(reverse('loggedin'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_loggedin_view_authenticated(self):
        """Test loggedin view when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('loggedin'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'loggedinindex.html')


class ProfileViewTest(TestCase):
    """Test cases for profile view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

    def test_profile_view_requires_login(self):
        """Test profile view requires authentication"""
        response = self.client.get(reverse('profile'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_profile_view_authenticated(self):
        """Test profile view when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')

    def test_profile_view_shows_user_resumes(self):
        """Test profile view shows user's resumes"""
        self.client.login(username='testuser', password='testpass123')

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
        self.client.login(username='testuser', password='testpass123')

        job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content="Job content",
            filename="job.txt",
            title="Test Job"
        )

        response = self.client.get(reverse('profile'))
        self.assertIn('job_listings', response.context)
        self.assertIn(job_listing, response.context['job_listings'])


class ResumeDetailViewTest(TestCase):
    """Test cases for resume detail view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
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
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('resume_detail', args=[self.resume.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/resume_detail.html')
        self.assertEqual(response.context['resume'], self.resume)

    def test_resume_detail_nonexistent_resume(self):
        """Test resume detail view with nonexistent resume"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('resume_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)


class DeleteResumeViewTest(TestCase):
    """Test cases for delete resume view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
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
        self.assertTrue(UploadedResume.objects.filter(id=self.resume.id).exists())

    def test_delete_resume_post(self):
        """Test deleting resume with POST request"""
        self.client.login(username='testuser', password='testpass123')
        resume_id = self.resume.id

        response = self.client.post(reverse('delete_resume', args=[resume_id]))

        # Should redirect to profile
        self.assertRedirects(response, reverse('profile'))
        # Resume should be deleted
        self.assertFalse(UploadedResume.objects.filter(id=resume_id).exists())

    def test_delete_resume_get(self):
        """Test GET request to delete resume redirects"""
        self.client.login(username='testuser', password='testpass123')
        resume_id = self.resume.id

        response = self.client.get(reverse('delete_resume', args=[resume_id]))

        # Should redirect to profile
        self.assertRedirects(response, reverse('profile'))
        # Resume should still exist
        self.assertTrue(UploadedResume.objects.filter(id=resume_id).exists())

    def test_delete_resume_different_user(self):
        """Test user cannot delete another user's resume"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.client.login(username='otheruser', password='testpass123')

        response = self.client.post(
            reverse('delete_resume', args=[self.resume.id])
        )

        # Should return 404
        self.assertEqual(response.status_code, 404)
        # Resume should still exist
        self.assertTrue(UploadedResume.objects.filter(id=self.resume.id).exists())


class JobPostingDetailViewTest(TestCase):
    """Test cases for job posting detail view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
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
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('job_posting_detail', args=[self.job_listing.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/job_posting_detail.html')
        self.assertEqual(response.context['job'], self.job_listing)

    def test_job_posting_detail_nonexistent_job(self):
        """Test job posting detail view with nonexistent job"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('job_posting_detail', args=[99999])
        )
        self.assertEqual(response.status_code, 404)


class DeleteJobViewTest(TestCase):
    """Test cases for delete job view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
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
        self.client.login(username='testuser', password='testpass123')
        job_id = self.job_listing.id

        response = self.client.post(reverse('delete_job', args=[job_id]))

        # Should redirect to profile
        self.assertRedirects(response, reverse('profile'))
        # Job should be deleted
        self.assertFalse(UploadedJobListing.objects.filter(id=job_id).exists())

    def test_delete_job_different_user(self):
        """Test user cannot delete another user's job"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.client.login(username='otheruser', password='testpass123')

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
            password='testpass123'
        )
        self.resume = UploadedResume.objects.create(
            user=self.user,
            content="Original content",
            title="Original Title"
        )
        self.client = Client()

    def test_edit_resume_get(self):
        """Test GET request to edit resume view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('edit_resume', args=[self.resume.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/edit_document.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['document'], self.resume)

    def test_edit_resume_post_valid(self):
        """Test POST request to edit resume with valid data"""
        self.client.login(username='testuser', password='testpass123')
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
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('edit_resume', args=[99999]))
        self.assertEqual(response.status_code, 404)


class EditJobPostingViewTest(TestCase):
    """Test cases for edit job posting view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
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
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('edit_job_posting', args=[self.job_listing.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/edit_job_posting.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['job_listing'], self.job_listing)

    def test_edit_job_posting_post_valid(self):
        """Test POST request to edit job posting with valid data"""
        self.client.login(username='testuser', password='testpass123')
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
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.client.login(username='otheruser', password='testpass123')

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
            password='testpass123'
        )
        self.client = Client()

    def test_document_list_view_get(self):
        """Test GET request to document list view"""
        response = self.client.get(reverse('document-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/document-list.html')


class OpenAIClientTest(TestCase):
    """Test cases for OpenAI client utility functions"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

    @patch('active_interview_app.views.settings')
    def test_ai_available_without_api_key(self, mock_settings):
        """Test _ai_available returns False when API key is not set"""
        from active_interview_app.views import _ai_available, _openai_client
        import active_interview_app.views as views

        # Reset the global client
        views._openai_client = None

        mock_settings.OPENAI_API_KEY = None

        result = _ai_available()
        self.assertFalse(result)

    @patch('active_interview_app.views.settings')
    @patch('active_interview_app.views.OpenAI')
    def test_get_openai_client_raises_error_without_key(self,
                                                         mock_openai,
                                                         mock_settings):
        """Test get_openai_client raises error when API key is not set"""
        from active_interview_app.views import get_openai_client
        import active_interview_app.views as views

        # Reset the global client
        views._openai_client = None

        mock_settings.OPENAI_API_KEY = None

        with self.assertRaises(ValueError) as context:
            get_openai_client()

        self.assertIn("OPENAI_API_KEY is not set", str(context.exception))

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
