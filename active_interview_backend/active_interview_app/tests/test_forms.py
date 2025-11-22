"""
Comprehensive tests for all forms in active_interview_app
"""
from django.test import TestCase
from django.contrib.auth.models import User
from active_interview_app.forms import (
    CreateUserForm,
    CreateChatForm,
    EditChatForm,
    UploadFileForm,
    DocumentEditForm,
    JobPostingEditForm,
    InterviewTemplateForm
)
from active_interview_app.models import (
    UploadedResume,
    UploadedJobListing,
    Chat,
    QuestionBank,
    Tag,
    UserProfile
)
from django.core.files.uploadedfile import SimpleUploadedFile


class CreateUserFormTest(TestCase):
    """Test cases for CreateUserForm"""

    def test_valid_user_creation_form(self):
        """Test form with valid data"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        }
        form = CreateUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        """Test form fails when passwords don't match"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123!',
            'password2': 'differentpass!'
        }
        form = CreateUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_missing_username(self):
        """Test form fails when username is missing"""
        form_data = {
            'email': 'test@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        }
        form = CreateUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_missing_email(self):
        """Test form fails when email is missing"""
        form_data = {
            'username': 'testuser',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        }
        form = CreateUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_username(self):
        """Test form fails when username already exists"""
        User.objects.create_user(username='testuser', password='testpass123!')
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        }
        form = CreateUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)


class DocumentEditFormTest(TestCase):
    """Test cases for DocumentEditForm"""

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

    def test_valid_document_edit_form(self):
        """Test form with valid data"""
        form_data = {
            'title': 'Updated Title',
            'content': 'Updated content'
        }
        form = DocumentEditForm(data=form_data, instance=self.resume)
        self.assertTrue(form.is_valid())

    def test_missing_title(self):
        """Test form fails when title is missing"""
        form_data = {
            'content': 'Updated content'
        }
        form = DocumentEditForm(data=form_data, instance=self.resume)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_missing_content(self):
        """Test form fails when content is missing"""
        form_data = {
            'title': 'Updated Title'
        }
        form = DocumentEditForm(data=form_data, instance=self.resume)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)

    def test_form_fields(self):
        """Test that form has correct fields"""
        form = DocumentEditForm()
        self.assertIn('title', form.fields)
        self.assertIn('content', form.fields)
        self.assertEqual(len(form.fields), 2)


class JobPostingEditFormTest(TestCase):
    """Test cases for JobPostingEditForm"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content="Original job content",
            filename="job.txt",
            title="Original Job Title"
        )

    def test_valid_job_posting_edit_form(self):
        """Test form with valid data"""
        form_data = {
            'title': 'Updated Job Title',
            'content': 'Updated job content'
        }
        form = JobPostingEditForm(data=form_data, instance=self.job_listing)
        self.assertTrue(form.is_valid())

    def test_missing_title(self):
        """Test form fails when title is missing"""
        form_data = {
            'content': 'Updated job content'
        }
        form = JobPostingEditForm(data=form_data, instance=self.job_listing)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_missing_content(self):
        """Test form fails when content is missing"""
        form_data = {
            'title': 'Updated Job Title'
        }
        form = JobPostingEditForm(data=form_data, instance=self.job_listing)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)

    def test_form_fields(self):
        """Test that form has correct fields"""
        form = JobPostingEditForm()
        self.assertIn('title', form.fields)
        self.assertIn('content', form.fields)
        self.assertEqual(len(form.fields), 2)


class CreateChatFormTest(TestCase):
    """Test cases for CreateChatForm"""

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
        self.resume = UploadedResume.objects.create(
            user=self.user,
            content="Resume content",
            title="Test Resume"
        )

    def test_valid_create_chat_form_with_resume(self):
        """Test form with valid data including resume"""
        form_data = {
            'title': 'Test Chat',
            'type': Chat.GENERAL,
            'difficulty': 5,
            'listing_choice': self.job_listing.id,
            'resume_choice': self.resume.id
        }
        form = CreateChatForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_valid_create_chat_form_without_resume(self):
        """Test form with valid data without resume (optional)"""
        form_data = {
            'title': 'Test Chat',
            'type': Chat.GENERAL,
            'difficulty': 5,
            'listing_choice': self.job_listing.id
        }
        form = CreateChatForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_difficulty_min_value(self):
        """Test form with difficulty at minimum (1)"""
        form_data = {
            'title': 'Test Chat',
            'type': Chat.GENERAL,
            'difficulty': 1,
            'listing_choice': self.job_listing.id
        }
        form = CreateChatForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_difficulty_max_value(self):
        """Test form with difficulty at maximum (10)"""
        form_data = {
            'title': 'Test Chat',
            'type': Chat.GENERAL,
            'difficulty': 10,
            'listing_choice': self.job_listing.id
        }
        form = CreateChatForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_difficulty_below_min(self):
        """Test form fails with difficulty below 1"""
        form_data = {
            'title': 'Test Chat',
            'type': Chat.GENERAL,
            'difficulty': 0,
            'listing_choice': self.job_listing.id
        }
        form = CreateChatForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_difficulty_above_max(self):
        """Test form fails with difficulty above 10"""
        form_data = {
            'title': 'Test Chat',
            'type': Chat.GENERAL,
            'difficulty': 11,
            'listing_choice': self.job_listing.id
        }
        form = CreateChatForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_form_filters_job_listings_by_user(self):
        """Test that form only shows user's job listings"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_job = UploadedJobListing.objects.create(
            user=other_user,
            content="Other job content",
            filename="other.txt",
            title="Other Job"
        )

        form = CreateChatForm(user=self.user)
        queryset = form.fields['listing_choice'].queryset
        self.assertIn(self.job_listing, queryset)
        self.assertNotIn(other_job, queryset)

    def test_form_filters_resumes_by_user(self):
        """Test that form only shows user's resumes"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_resume = UploadedResume.objects.create(
            user=other_user,
            content="Other resume content",
            title="Other Resume"
        )

        form = CreateChatForm(user=self.user)
        queryset = form.fields['resume_choice'].queryset
        self.assertIn(self.resume, queryset)
        self.assertNotIn(other_resume, queryset)

    def test_missing_title(self):
        """Test form uses default title when title is missing"""
        form_data = {
            'type': Chat.GENERAL,
            'difficulty': 5,
            'listing_choice': self.job_listing.id
        }
        form = CreateChatForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        # Check that default title is used
        self.assertEqual(form.cleaned_data.get('title'), 'Interview Chat')

    def test_missing_listing_choice(self):
        """Test form fails when listing_choice is missing"""
        form_data = {
            'title': 'Test Chat',
            'type': Chat.GENERAL,
            'difficulty': 5
        }
        form = CreateChatForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('listing_choice', form.errors)

    def test_all_interview_types(self):
        """Test form accepts all valid interview types"""
        types = [Chat.GENERAL, Chat.SKILLS, Chat.PERSONALITY,
                 Chat.FINAL_SCREENING]
        for interview_type in types:
            form_data = {
                'title': f'Test Chat {interview_type}',
                'type': interview_type,
                'difficulty': 5,
                'listing_choice': self.job_listing.id
            }
            form = CreateChatForm(data=form_data, user=self.user)
            self.assertTrue(form.is_valid(),
                            f"Form should be valid for type {interview_type}")


class EditChatFormTest(TestCase):
    """Test cases for EditChatForm"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.chat = Chat.objects.create(
            owner=self.user,
            title="Original Title",
            difficulty=5,
            messages=[]
        )

    def test_valid_edit_chat_form(self):
        """Test form with valid data"""
        form_data = {
            'title': 'Updated Title',
            'difficulty': 7
        }
        form = EditChatForm(data=form_data, instance=self.chat)
        self.assertTrue(form.is_valid())

    def test_missing_title(self):
        """Test form is valid when title is missing (optional field)"""
        form_data = {
            'difficulty': 7
        }
        form = EditChatForm(data=form_data, instance=self.chat)
        self.assertTrue(form.is_valid())

    def test_difficulty_validation_min(self):
        """Test form accepts minimum difficulty (1)"""
        form_data = {
            'title': 'Updated Title',
            'difficulty': 1
        }
        form = EditChatForm(data=form_data, instance=self.chat)
        self.assertTrue(form.is_valid())

    def test_difficulty_validation_max(self):
        """Test form accepts maximum difficulty (10)"""
        form_data = {
            'title': 'Updated Title',
            'difficulty': 10
        }
        form = EditChatForm(data=form_data, instance=self.chat)
        self.assertTrue(form.is_valid())

    def test_difficulty_validation_below_min(self):
        """Test form fails with difficulty below 1"""
        form_data = {
            'title': 'Updated Title',
            'difficulty': 0
        }
        form = EditChatForm(data=form_data, instance=self.chat)
        self.assertFalse(form.is_valid())

    def test_difficulty_validation_above_max(self):
        """Test form fails with difficulty above 10"""
        form_data = {
            'title': 'Updated Title',
            'difficulty': 11
        }
        form = EditChatForm(data=form_data, instance=self.chat)
        self.assertFalse(form.is_valid())

    def test_form_fields(self):
        """Test that form has correct fields"""
        form = EditChatForm()
        self.assertIn('title', form.fields)
        self.assertIn('difficulty', form.fields)


class UploadFileFormTest(TestCase):
    """Test cases for UploadFileForm"""

    def test_valid_upload_file_form(self):
        """Test form with valid file upload"""
        file_content = b'Test file content'
        uploaded_file = SimpleUploadedFile(
            "test.pdf",
            file_content,
            content_type="application/pdf"
        )
        form_data = {'title': 'Test Upload'}
        form = UploadFileForm(data=form_data,
                              files={'file': uploaded_file})
        self.assertTrue(form.is_valid())

    def test_missing_file(self):
        """Test form fails when file is missing"""
        form_data = {'title': 'Test Upload'}
        form = UploadFileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_missing_title(self):
        """Test form fails when title is missing"""
        file_content = b'Test file content'
        uploaded_file = SimpleUploadedFile(
            "test.pdf",
            file_content,
            content_type="application/pdf"
        )
        form = UploadFileForm(files={'file': uploaded_file})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_clean_file_method(self):
        """Test that clean_file method returns uploaded file"""
        file_content = b'Test file content'
        uploaded_file = SimpleUploadedFile(
            "test.pdf",
            file_content,
            content_type="application/pdf"
        )
        form_data = {'title': 'Test Upload'}
        form = UploadFileForm(data=form_data,
                              files={'file': uploaded_file})
        if form.is_valid():
            cleaned_file = form.cleaned_data.get('file')
            self.assertIsNotNone(cleaned_file)
            self.assertEqual(cleaned_file.name, 'test.pdf')

    def test_form_fields(self):
        """Test that form has correct fields"""
        form = UploadFileForm()
        self.assertIn('file', form.fields)
        self.assertIn('title', form.fields)
        self.assertEqual(len(form.fields), 2)


class InterviewTemplateFormTest(TestCase):
    """Test cases for InterviewTemplateForm"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.profile.role = UserProfile.INTERVIEWER
        self.user.profile.save()

        self.bank1 = QuestionBank.objects.create(
            name="Test Bank 1",
            owner=self.user
        )
        self.bank2 = QuestionBank.objects.create(
            name="Test Bank 2",
            owner=self.user
        )
        self.tag1 = Tag.objects.create(name="#python")
        self.tag2 = Tag.objects.create(name="#sql")

    def test_form_init_filters_question_banks_by_user(self):
        """Test that form filters question banks by user"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_bank = QuestionBank.objects.create(
            name="Other Bank",
            owner=other_user
        )

        form = InterviewTemplateForm(user=self.user)
        queryset = form.fields['question_banks'].queryset

        self.assertIn(self.bank1, queryset)
        self.assertIn(self.bank2, queryset)
        self.assertNotIn(other_bank, queryset)

    def test_form_init_without_user(self):
        """Test form initialization without user argument"""
        form = InterviewTemplateForm()
        # Should not crash and should have empty queryset
        self.assertEqual(form.fields['question_banks'].queryset.count(), 0)

    def test_clean_valid_percentages(self):
        """Test clean method with valid difficulty percentages"""
        form_data = {
            'name': 'Test Template',
            'use_auto_assembly': True,
            'question_count': 10,
            'easy_percentage': 30,
            'medium_percentage': 50,
            'hard_percentage': 20
        }
        form = InterviewTemplateForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_clean_invalid_percentages(self):
        """Test clean method with percentages not summing to 100"""
        form_data = {
            'name': 'Test Template',
            'use_auto_assembly': True,
            'question_count': 10,
            'easy_percentage': 30,
            'medium_percentage': 50,
            'hard_percentage': 30  # Total is 110%
        }
        form = InterviewTemplateForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Difficulty percentages must sum to 100%',
                      str(form.errors))

    def test_clean_without_auto_assembly(self):
        """Test clean method when auto_assembly is disabled"""
        form_data = {
            'name': 'Test Template',
            'use_auto_assembly': False,
            'easy_percentage': 30,
            'medium_percentage': 50,
            'hard_percentage': 30  # Total is 110%, but should be ignored
        }
        form = InterviewTemplateForm(data=form_data, user=self.user)
        # Should be valid because auto_assembly is not enabled
        self.assertTrue(form.is_valid())

    def test_clean_with_none_percentages(self):
        """Test clean method with None percentages (treated as 0)"""
        form_data = {
            'name': 'Test Template',
            'use_auto_assembly': True,
            'question_count': 10,
            'easy_percentage': None,
            'medium_percentage': 50,
            'hard_percentage': 50
        }
        form = InterviewTemplateForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_form_fields(self):
        """Test that form has correct fields"""
        form = InterviewTemplateForm()
        self.assertIn('name', form.fields)
        self.assertIn('description', form.fields)
        self.assertIn('use_auto_assembly', form.fields)
        self.assertIn('question_banks', form.fields)
        self.assertIn('tags', form.fields)
        self.assertIn('question_count', form.fields)
        self.assertIn('easy_percentage', form.fields)
        self.assertIn('medium_percentage', form.fields)
        self.assertIn('hard_percentage', form.fields)
