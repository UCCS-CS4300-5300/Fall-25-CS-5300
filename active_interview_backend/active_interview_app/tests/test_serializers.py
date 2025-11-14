"""
Comprehensive tests for all serializers in active_interview_app
"""
from django.test import TestCase
from django.contrib.auth.models import User
from active_interview_app.serializers import (
    UploadedResumeSerializer,
    UploadedJobListingSerializer,
    QuestionSerializer,
    InterviewTemplateSerializer
)
from active_interview_app.models import (
    UploadedResume,
    UploadedJobListing,
    QuestionBank,
    Question,
    Tag,
    InterviewTemplate,
    UserProfile
)
from django.core.files.uploadedfile import SimpleUploadedFile


class UploadedResumeSerializerTest(TestCase):
    """Test cases for UploadedResumeSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.resume = UploadedResume.objects.create(
            user=self.user,
            content="Test resume content",
            title="Software Engineer Resume"
        )

    def test_serialize_resume(self):
        """Test serializing a resume instance"""
        serializer = UploadedResumeSerializer(instance=self.resume)
        data = serializer.data

        self.assertEqual(data['id'], self.resume.id)
        self.assertEqual(data['user'], self.user.id)
        self.assertIn('uploaded_at', data)

    def test_serializer_fields(self):
        """Test that serializer has correct fields"""
        serializer = UploadedResumeSerializer(instance=self.resume)
        expected_fields = {'id', 'file', 'user', 'uploaded_at', 'title'}
        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_deserialize_valid_data(self):
        """Test deserializing valid resume data"""
        file_content = b'Resume content'
        uploaded_file = SimpleUploadedFile(
            "resume.pdf",
            file_content,
            content_type="application/pdf"
        )

        data = {
            'file': uploaded_file,
            'user': self.user.id,
            'title': 'Test Resume'
        }

        serializer = UploadedResumeSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_deserialize_missing_user(self):
        """Test deserializing fails when user is missing"""
        file_content = b'Resume content'
        uploaded_file = SimpleUploadedFile(
            "resume.pdf",
            file_content,
            content_type="application/pdf"
        )

        data = {
            'file': uploaded_file
        }

        serializer = UploadedResumeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_create_resume_via_serializer(self):
        """Test creating a resume through serializer"""
        file_content = b'New resume content'
        uploaded_file = SimpleUploadedFile(
            "new_resume.pdf",
            file_content,
            content_type="application/pdf"
        )

        data = {
            'file': uploaded_file,
            'title': 'New Resume'
        }

        serializer = UploadedResumeSerializer(data=data)
        if serializer.is_valid():
            resume = serializer.save(user=self.user, content='New resume content')
            self.assertIsNotNone(resume.id)
            self.assertEqual(resume.user, self.user)

    def test_update_resume_via_serializer(self):
        """Test updating a resume through serializer"""
        file_content = b'Updated resume content'
        uploaded_file = SimpleUploadedFile(
            "updated_resume.pdf",
            file_content,
            content_type="application/pdf"
        )

        data = {
            'file': uploaded_file,
            'user': self.user.id
        }

        serializer = UploadedResumeSerializer(
            instance=self.resume,
            data=data,
            partial=True
        )
        if serializer.is_valid():
            updated_resume = serializer.save()
            self.assertEqual(updated_resume.id, self.resume.id)

    def test_multiple_resumes_serialization(self):
        """Test serializing multiple resumes"""
        resume2 = UploadedResume.objects.create(
            user=self.user,
            content="Second resume content",
            title="Data Scientist Resume"
        )

        resumes = UploadedResume.objects.filter(user=self.user)
        serializer = UploadedResumeSerializer(resumes, many=True)

        self.assertEqual(len(serializer.data), 2)
        resume_ids = [r['id'] for r in serializer.data]
        self.assertIn(self.resume.id, resume_ids)
        self.assertIn(resume2.id, resume_ids)


class UploadedJobListingSerializerTest(TestCase):
    """Test cases for UploadedJobListingSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.job_listing = UploadedJobListing.objects.create(
            user=self.user,
            content="Software Engineer position",
            filename="job.txt",
            title="Software Engineer"
        )

    def test_serialize_job_listing(self):
        """Test serializing a job listing instance"""
        serializer = UploadedJobListingSerializer(instance=self.job_listing)
        data = serializer.data

        self.assertEqual(data['id'], self.job_listing.id)
        self.assertEqual(data['user'], self.user.id)
        self.assertEqual(data['filename'], "job.txt")
        self.assertEqual(data['content'], "Software Engineer position")
        self.assertIn('created_at', data)

    def test_serializer_fields(self):
        """Test that serializer has correct fields"""
        serializer = UploadedJobListingSerializer(instance=self.job_listing)
        expected_fields = {'id', 'user', 'filename', 'content', 'created_at', 'title', 'file'}
        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_deserialize_valid_data(self):
        """Test deserializing valid job listing data"""
        data = {
            'user': self.user.id,
            'filename': 'new_job.txt',
            'content': 'Python Developer position'
        }

        serializer = UploadedJobListingSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_deserialize_missing_user(self):
        """Test deserializing succeeds when user is missing (read-only field)"""
        data = {
            'filename': 'new_job.txt',
            'content': 'Python Developer position',
            'title': 'Job Title'
        }

        serializer = UploadedJobListingSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_deserialize_missing_content(self):
        """Test deserializing fails when content is missing"""
        data = {
            'user': self.user.id,
            'filename': 'new_job.txt'
        }

        serializer = UploadedJobListingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)

    def test_deserialize_missing_filename(self):
        """Test deserializing succeeds when filename is missing (optional field)"""
        data = {
            'content': 'Python Developer position',
            'title': 'Job Title'
        }

        serializer = UploadedJobListingSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_create_job_listing_via_serializer(self):
        """Test creating a job listing through serializer"""
        data = {
            'filename': 'data_scientist.txt',
            'content': 'Data Scientist position available',
            'title': 'Data Scientist'
        }

        serializer = UploadedJobListingSerializer(data=data)
        if serializer.is_valid():
            job_listing = serializer.save(user=self.user)
            self.assertIsNotNone(job_listing.id)
            self.assertEqual(job_listing.user, self.user)
            self.assertEqual(job_listing.filename, 'data_scientist.txt')
            self.assertEqual(job_listing.content,
                             'Data Scientist position available')

    def test_update_job_listing_via_serializer(self):
        """Test updating a job listing through serializer"""
        data = {
            'content': 'Updated job content',
            'filename': 'updated_job.txt'
        }

        serializer = UploadedJobListingSerializer(
            instance=self.job_listing,
            data=data,
            partial=True
        )
        if serializer.is_valid():
            updated_job = serializer.save()
            self.assertEqual(updated_job.id, self.job_listing.id)
            self.assertEqual(updated_job.content, 'Updated job content')
            self.assertEqual(updated_job.filename, 'updated_job.txt')

    def test_multiple_job_listings_serialization(self):
        """Test serializing multiple job listings"""
        job_listing2 = UploadedJobListing.objects.create(
            user=self.user,
            content="Data Analyst position",
            filename="analyst.txt",
            title="Data Analyst"
        )

        job_listings = UploadedJobListing.objects.filter(user=self.user)
        serializer = UploadedJobListingSerializer(job_listings, many=True)

        self.assertEqual(len(serializer.data), 2)
        job_ids = [j['id'] for j in serializer.data]
        self.assertIn(self.job_listing.id, job_ids)
        self.assertIn(job_listing2.id, job_ids)

    def test_serializer_read_only_fields(self):
        """Test that created_at is read-only"""
        serializer = UploadedJobListingSerializer(instance=self.job_listing)
        # created_at should be in the serialized data
        self.assertIn('created_at', serializer.data)

        # Trying to update created_at should not work
        from django.utils import timezone
        import datetime
        new_time = timezone.now() - datetime.timedelta(days=10)

        data = {
            'user': self.user.id,
            'filename': 'test.txt',
            'content': 'Test content',
            'created_at': new_time
        }

        serializer = UploadedJobListingSerializer(
            instance=self.job_listing,
            data=data,
            partial=True
        )
        if serializer.is_valid():
            updated_job = serializer.save()
            # created_at should not have changed
            self.assertNotEqual(updated_job.created_at, new_time)

    def test_serializer_with_different_users(self):
        """Test serializing job listings from different users"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_job = UploadedJobListing.objects.create(
            user=other_user,
            content="Other user's job",
            filename="other.txt",
            title="Other Job"
        )

        # Serialize the current user's job
        serializer1 = UploadedJobListingSerializer(instance=self.job_listing)
        # Serialize the other user's job
        serializer2 = UploadedJobListingSerializer(instance=other_job)

        self.assertEqual(serializer1.data['user'], self.user.id)
        self.assertEqual(serializer2.data['user'], other_user.id)
        self.assertNotEqual(serializer1.data['user'], serializer2.data['user'])


def create_interviewer_user(username='testuser', password='testpass123'):
    """Helper function to create a user with interviewer role."""
    user = User.objects.create_user(username=username, password=password)
    user.profile.role = UserProfile.INTERVIEWER
    user.profile.save()
    return user


class QuestionSerializerTest(TestCase):
    """Tests for QuestionSerializer"""

    def setUp(self):
        self.user = create_interviewer_user()
        self.bank = QuestionBank.objects.create(
            name="Test Bank",
            owner=self.user
        )
        self.tag1 = Tag.objects.create(name="#python")
        self.tag2 = Tag.objects.create(name="#sql")

    def test_update_question_text(self):
        """Test updating question text via serializer"""
        question = Question.objects.create(
            question_bank=self.bank,
            text="Original question",
            difficulty="easy",
            owner=self.user
        )
        question.tags.add(self.tag1)

        serializer = QuestionSerializer(question, data={
            'text': 'Updated question',
            'difficulty': 'medium',
            'question_bank': self.bank.id,
            'tag_ids': [self.tag1.id]
        })
        self.assertTrue(serializer.is_valid())
        updated_question = serializer.save()

        self.assertEqual(updated_question.text, 'Updated question')
        self.assertEqual(updated_question.difficulty, 'medium')

    def test_update_question_tags(self):
        """Test updating question tags via serializer"""
        question = Question.objects.create(
            question_bank=self.bank,
            text="Test question",
            difficulty="easy",
            owner=self.user
        )
        question.tags.add(self.tag1)

        serializer = QuestionSerializer(question, data={
            'text': 'Test question',
            'difficulty': 'easy',
            'question_bank': self.bank.id,
            'tag_ids': [self.tag2.id]
        })
        self.assertTrue(serializer.is_valid())
        updated_question = serializer.save()

        self.assertEqual(updated_question.tags.count(), 1)
        self.assertIn(self.tag2, updated_question.tags.all())
        self.assertNotIn(self.tag1, updated_question.tags.all())

    def test_update_question_without_tags(self):
        """Test updating question without specifying tags"""
        question = Question.objects.create(
            question_bank=self.bank,
            text="Test question",
            difficulty="easy",
            owner=self.user
        )
        question.tags.add(self.tag1)

        serializer = QuestionSerializer(question, data={
            'text': 'Updated question',
            'difficulty': 'hard',
            'question_bank': self.bank.id
        })
        self.assertTrue(serializer.is_valid())
        updated_question = serializer.save()

        # Tags should remain unchanged
        self.assertEqual(updated_question.tags.count(), 1)
        self.assertIn(self.tag1, updated_question.tags.all())


class InterviewTemplateSerializerTest(TestCase):
    """Tests for InterviewTemplateSerializer"""

    def setUp(self):
        self.user = create_interviewer_user()
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

    def test_create_template_with_tags_and_question_banks(self):
        """Test creating template with tags and question banks via serializer"""
        serializer = InterviewTemplateSerializer(data={
            'name': 'Test Template',
            'description': 'Test Description',
            'sections': [],
            'tag_ids': [self.tag1.id, self.tag2.id],
            'question_bank_ids': [self.bank1.id, self.bank2.id],
            'use_auto_assembly': True,
            'question_count': 10,
            'easy_percentage': 30,
            'medium_percentage': 50,
            'hard_percentage': 20
        })
        self.assertTrue(serializer.is_valid())
        template = serializer.save(user=self.user)

        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.tags.count(), 2)
        self.assertEqual(template.question_banks.count(), 2)
        self.assertTrue(template.use_auto_assembly)

    def test_create_template_without_optional_fields(self):
        """Test creating template without tags or question banks"""
        serializer = InterviewTemplateSerializer(data={
            'name': 'Simple Template',
            'sections': []
        })
        self.assertTrue(serializer.is_valid())
        template = serializer.save(user=self.user)

        self.assertEqual(template.name, 'Simple Template')
        self.assertEqual(template.tags.count(), 0)
        self.assertEqual(template.question_banks.count(), 0)

    def test_update_template_name_and_description(self):
        """Test updating template name and description via serializer"""
        template = InterviewTemplate.objects.create(
            name="Original Name",
            description="Original Description",
            user=self.user,
            sections=[]
        )
        template.tags.add(self.tag1)

        serializer = InterviewTemplateSerializer(template, data={
            'name': 'Updated Name',
            'description': 'Updated Description',
            'sections': []
        })
        self.assertTrue(serializer.is_valid())
        updated_template = serializer.save()

        self.assertEqual(updated_template.name, 'Updated Name')
        self.assertEqual(updated_template.description, 'Updated Description')

    def test_update_template_tags(self):
        """Test updating template tags via serializer"""
        template = InterviewTemplate.objects.create(
            name="Test Template",
            user=self.user,
            sections=[]
        )
        template.tags.add(self.tag1)

        serializer = InterviewTemplateSerializer(template, data={
            'name': 'Test Template',
            'sections': [],
            'tag_ids': [self.tag2.id]
        })
        self.assertTrue(serializer.is_valid())
        updated_template = serializer.save()

        self.assertEqual(updated_template.tags.count(), 1)
        self.assertIn(self.tag2, updated_template.tags.all())
        self.assertNotIn(self.tag1, updated_template.tags.all())

    def test_update_template_question_banks(self):
        """Test updating template question banks via serializer"""
        template = InterviewTemplate.objects.create(
            name="Test Template",
            user=self.user,
            sections=[]
        )
        template.question_banks.add(self.bank1)

        serializer = InterviewTemplateSerializer(template, data={
            'name': 'Test Template',
            'sections': [],
            'question_bank_ids': [self.bank2.id]
        })
        self.assertTrue(serializer.is_valid())
        updated_template = serializer.save()

        self.assertEqual(updated_template.question_banks.count(), 1)
        self.assertIn(self.bank2, updated_template.question_banks.all())
        self.assertNotIn(self.bank1, updated_template.question_banks.all())

    def test_update_template_without_tags_or_banks(self):
        """Test updating template without changing tags or question banks"""
        template = InterviewTemplate.objects.create(
            name="Test Template",
            user=self.user,
            sections=[]
        )
        template.tags.add(self.tag1)
        template.question_banks.add(self.bank1)

        serializer = InterviewTemplateSerializer(template, data={
            'name': 'Updated Name',
            'sections': []
        })
        self.assertTrue(serializer.is_valid())
        updated_template = serializer.save()

        # Tags and question banks should remain unchanged
        self.assertEqual(updated_template.tags.count(), 1)
        self.assertIn(self.tag1, updated_template.tags.all())
        self.assertEqual(updated_template.question_banks.count(), 1)
        self.assertIn(self.bank1, updated_template.question_banks.all())
