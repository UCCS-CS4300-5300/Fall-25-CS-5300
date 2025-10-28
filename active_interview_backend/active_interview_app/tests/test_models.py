"""
Comprehensive tests for all models in active_interview_app
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from active_interview_app.models import (
    UploadedResume,
    UploadedJobListing,
    Chat
)
from django.utils import timezone


class UploadedResumeModelTest(TestCase):
    """Test cases for UploadedResume model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_resume(self):
        """Test creating a resume with all fields"""
        resume = UploadedResume.objects.create(
            user=self.user,
            content="Test resume content",
            title="Software Engineer Resume",
            filesize=1024,
            original_filename="resume.pdf"
        )
        self.assertEqual(resume.user, self.user)
        self.assertEqual(resume.content, "Test resume content")
        self.assertEqual(resume.title, "Software Engineer Resume")
        self.assertEqual(resume.filesize, 1024)
        self.assertEqual(resume.original_filename, "resume.pdf")

    def test_resume_str_method(self):
        """Test the __str__ method returns title"""
        resume = UploadedResume.objects.create(
            user=self.user,
            content="Content",
            title="My Resume"
        )
        self.assertEqual(str(resume), "My Resume")

    def test_resume_uploaded_at_auto_now(self):
        """Test that uploaded_at is automatically set"""
        resume = UploadedResume.objects.create(
            user=self.user,
            content="Content",
            title="Resume"
        )
        self.assertIsNotNone(resume.uploaded_at)
        self.assertLessEqual(resume.uploaded_at, timezone.now())

    def test_resume_cascade_delete_on_user_deletion(self):
        """Test that resumes are deleted when user is deleted"""
        resume = UploadedResume.objects.create(
            user=self.user,
            content="Content",
            title="Resume"
        )
        resume_id = resume.id
        self.user.delete()
        self.assertFalse(UploadedResume.objects.filter(id=resume_id).exists())

    def test_resume_optional_fields(self):
        """Test creating resume with minimal required fields"""
        resume = UploadedResume.objects.create(
            user=self.user,
            content="Minimal content",
            title="Minimal Resume"
        )
        self.assertIsNone(resume.filesize)
        self.assertIsNone(resume.original_filename)


class UploadedJobListingModelTest(TestCase):
    """Test cases for UploadedJobListing model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_job_listing(self):
        """Test creating a job listing with all fields"""
        job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content="Software Engineer position available",
            filename="job_listing.txt",
            title="Software Engineer",
            filepath="/path/to/file.txt"
        )
        self.assertEqual(job_listing.user, self.user)
        self.assertEqual(job_listing.content,
                         "Software Engineer position available")
        self.assertEqual(job_listing.filename, "job_listing.txt")
        self.assertEqual(job_listing.title, "Software Engineer")
        self.assertEqual(job_listing.filepath, "/path/to/file.txt")

    def test_job_listing_str_method(self):
        """Test the __str__ method returns title"""
        job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content="Content",
            filename="test.txt",
            title="Python Developer"
        )
        self.assertEqual(str(job_listing), "Python Developer")

    def test_job_listing_created_at_auto_now(self):
        """Test that created_at is automatically set"""
        job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content="Content",
            filename="test.txt"
        )
        self.assertIsNotNone(job_listing.created_at)
        self.assertLessEqual(job_listing.created_at, timezone.now())

    def test_job_listing_cascade_delete_on_user_deletion(self):
        """Test that job listings are deleted when user is deleted"""
        job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content="Content",
            filename="test.txt"
        )
        job_id = job_listing.id
        self.user.delete()
        self.assertFalse(UploadedJobListing.objects.filter(id=job_id).exists())

    def test_job_listing_optional_fields(self):
        """Test creating job listing with minimal fields"""
        job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content="Minimal content",
            filename="minimal.txt"
        )
        self.assertIsNone(job_listing.title)
        self.assertIsNone(job_listing.filepath)


class ChatModelTest(TestCase):
    """Test cases for Chat model"""

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

    def test_create_chat_with_all_fields(self):
        """Test creating a chat with all fields populated"""
        chat = Chat.objects.create(
            owner=self.user,
            title="Interview Chat",
            difficulty=7,
            messages=[{"role": "system", "content": "Test"}],
            key_questions={"question1": "What is Python?"},
            job_listing=self.job_listing,
            resume=self.resume,
            type=Chat.SKILLS
        )
        self.assertEqual(chat.owner, self.user)
        self.assertEqual(chat.title, "Interview Chat")
        self.assertEqual(chat.difficulty, 7)
        self.assertEqual(chat.type, Chat.SKILLS)
        self.assertEqual(chat.job_listing, self.job_listing)
        self.assertEqual(chat.resume, self.resume)

    def test_chat_str_method(self):
        """Test the __str__ method returns title"""
        chat = Chat.objects.create(
            owner=self.user,
            title="My Interview",
            messages=[]
        )
        self.assertEqual(str(chat), "My Interview")

    def test_chat_default_difficulty(self):
        """Test that difficulty defaults to 5"""
        chat = Chat.objects.create(
            owner=self.user,
            title="Test Chat",
            messages=[]
        )
        self.assertEqual(chat.difficulty, 5)

    def test_chat_difficulty_validation_min(self):
        """Test that difficulty cannot be less than 1"""
        chat = Chat(
            owner=self.user,
            title="Test Chat",
            difficulty=0,
            messages=[]
        )
        with self.assertRaises(ValidationError):
            chat.full_clean()

    def test_chat_difficulty_validation_max(self):
        """Test that difficulty cannot be more than 10"""
        chat = Chat(
            owner=self.user,
            title="Test Chat",
            difficulty=11,
            messages=[]
        )
        with self.assertRaises(ValidationError):
            chat.full_clean()

    def test_chat_difficulty_validation_valid(self):
        """Test that difficulty between 1-10 is valid"""
        for difficulty in range(1, 11):
            chat = Chat(
                owner=self.user,
                title=f"Test Chat {difficulty}",
                difficulty=difficulty,
                messages=[{"role": "system", "content": "Test"}],
                key_questions={},
                job_listing=self.job_listing
            )
            # Should not raise an exception
            chat.full_clean()
            chat.save()
            self.assertEqual(chat.difficulty, difficulty)

    def test_chat_interview_types(self):
        """Test all interview type choices"""
        types = [Chat.GENERAL, Chat.SKILLS, Chat.PERSONALITY,
                 Chat.FINAL_SCREENING]
        for interview_type in types:
            chat = Chat.objects.create(
                owner=self.user,
                title=f"Chat {interview_type}",
                messages=[],
                type=interview_type
            )
            self.assertEqual(chat.type, interview_type)

    def test_chat_default_type(self):
        """Test that type defaults to GENERAL"""
        chat = Chat.objects.create(
            owner=self.user,
            title="Test Chat",
            messages=[]
        )
        self.assertEqual(chat.type, Chat.GENERAL)

    def test_chat_get_type_display(self):
        """Test the get_type_display method for all types"""
        type_displays = {
            Chat.GENERAL: "General",
            Chat.SKILLS: "Industry Skills",
            Chat.PERSONALITY: "Personality/Preliminary",
            Chat.FINAL_SCREENING: "Final Screening"
        }
        for type_code, type_name in type_displays.items():
            chat = Chat.objects.create(
                owner=self.user,
                title=f"Chat {type_code}",
                messages=[],
                type=type_code
            )
            self.assertEqual(chat.get_type_display(), type_name)

    def test_chat_modified_date_auto_now(self):
        """Test that modified_date is automatically updated"""
        chat = Chat.objects.create(
            owner=self.user,
            title="Test Chat",
            messages=[]
        )
        original_modified_date = chat.modified_date

        # Modify and save
        chat.title = "Updated Chat"
        chat.save()

        self.assertGreaterEqual(chat.modified_date, original_modified_date)

    def test_chat_cascade_delete_on_user_deletion(self):
        """Test that chats are deleted when user is deleted"""
        chat = Chat.objects.create(
            owner=self.user,
            title="Test Chat",
            messages=[]
        )
        chat_id = chat.id
        self.user.delete()
        self.assertFalse(Chat.objects.filter(id=chat_id).exists())

    def test_chat_set_null_on_job_listing_deletion(self):
        """Test that job_listing is set to NULL when job listing is deleted"""
        chat = Chat.objects.create(
            owner=self.user,
            title="Test Chat",
            messages=[],
            job_listing=self.job_listing
        )
        self.job_listing.delete()
        chat.refresh_from_db()
        self.assertIsNone(chat.job_listing)

    def test_chat_set_null_on_resume_deletion(self):
        """Test that resume is set to NULL when resume is deleted"""
        chat = Chat.objects.create(
            owner=self.user,
            title="Test Chat",
            messages=[],
            resume=self.resume
        )
        self.resume.delete()
        chat.refresh_from_db()
        self.assertIsNone(chat.resume)

    def test_chat_without_resume(self):
        """Test creating chat without resume (optional field)"""
        chat = Chat.objects.create(
            owner=self.user,
            title="No Resume Chat",
            messages=[],
            job_listing=self.job_listing
        )
        self.assertIsNone(chat.resume)

    def test_chat_json_fields(self):
        """Test that JSON fields work correctly"""
        messages = [
            {"role": "system", "content": "You are an interviewer"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        key_questions = {
            "q1": {"question": "What is Python?", "duration": 60},
            "q2": {"question": "Explain OOP", "duration": 120}
        }
        chat = Chat.objects.create(
            owner=self.user,
            title="JSON Test",
            messages=messages,
            key_questions=key_questions
        )
        chat.refresh_from_db()
        self.assertEqual(chat.messages, messages)
        self.assertEqual(chat.key_questions, key_questions)

    def test_chat_default_key_questions(self):
        """Test that key_questions defaults to empty list"""
        chat = Chat.objects.create(
            owner=self.user,
            title="Test Chat",
            messages=[]
        )
        self.assertEqual(chat.key_questions, [])
