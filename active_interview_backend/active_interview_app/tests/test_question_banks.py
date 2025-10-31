"""
Tests for Question Bank Tagging feature (Issue #24)
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from active_interview_app.models import QuestionBank, Question, Tag, InterviewTemplate


class TagModelTest(TestCase):
    """Tests for Tag model (Issue #40)"""

    def test_tag_auto_normalization(self):
        """Test that tags are automatically normalized"""
        tag = Tag.objects.create(name="Python")
        self.assertEqual(tag.name, "#python")

    def test_tag_already_has_hash(self):
        """Test tag normalization when # is already present"""
        tag = Tag.objects.create(name="#SQL")
        self.assertEqual(tag.name, "#sql")

    def test_tag_unique_constraint(self):
        """Test that duplicate tags are prevented"""
        Tag.objects.create(name="#python")
        with self.assertRaises(Exception):
            Tag.objects.create(name="#python")


class QuestionBankModelTest(TestCase):
    """Tests for QuestionBank model (Issue #38)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_question_bank(self):
        """Test creating a question bank"""
        bank = QuestionBank.objects.create(
            name="Python Questions",
            description="Questions about Python programming",
            owner=self.user
        )
        self.assertEqual(bank.name, "Python Questions")
        self.assertEqual(bank.owner, self.user)

    def test_question_bank_str(self):
        """Test string representation"""
        bank = QuestionBank.objects.create(
            name="Test Bank",
            owner=self.user
        )
        self.assertEqual(str(bank), "Test Bank")


class QuestionModelTest(TestCase):
    """Tests for Question model (Issue #39)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.bank = QuestionBank.objects.create(
            name="Test Bank",
            owner=self.user
        )
        self.tag1 = Tag.objects.create(name="#python")
        self.tag2 = Tag.objects.create(name="#sql")

    def test_create_question(self):
        """Test creating a question"""
        question = Question.objects.create(
            question_bank=self.bank,
            text="What is a Python decorator?",
            difficulty="medium",
            owner=self.user
        )
        self.assertEqual(question.text, "What is a Python decorator?")
        self.assertEqual(question.difficulty, "medium")

    def test_add_tags_to_question(self):
        """Test adding tags to a question"""
        question = Question.objects.create(
            question_bank=self.bank,
            text="What is a JOIN in SQL?",
            difficulty="easy",
            owner=self.user
        )
        question.tags.add(self.tag1, self.tag2)
        self.assertEqual(question.tags.count(), 2)
        self.assertIn(self.tag1, question.tags.all())


class QuestionBankAPITest(APITestCase):
    """Tests for QuestionBank API endpoints (Issue #38)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_question_bank_via_api(self):
        """Test creating a question bank via API"""
        url = reverse('question-bank-list')
        data = {
            'name': 'API Test Bank',
            'description': 'Created via API'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QuestionBank.objects.count(), 1)
        self.assertEqual(QuestionBank.objects.get().name, 'API Test Bank')

    def test_list_question_banks(self):
        """Test listing question banks"""
        QuestionBank.objects.create(
            name="Bank 1",
            owner=self.user
        )
        QuestionBank.objects.create(
            name="Bank 2",
            owner=self.user
        )

        url = reverse('question-bank-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_update_question_bank(self):
        """Test updating a question bank"""
        bank = QuestionBank.objects.create(
            name="Original Name",
            owner=self.user
        )
        url = reverse('question-bank-detail', args=[bank.id])
        data = {'name': 'Updated Name', 'description': 'New description'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bank.refresh_from_db()
        self.assertEqual(bank.name, 'Updated Name')

    def test_delete_question_bank(self):
        """Test deleting a question bank"""
        bank = QuestionBank.objects.create(
            name="To Delete",
            owner=self.user
        )
        url = reverse('question-bank-detail', args=[bank.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(QuestionBank.objects.count(), 0)


class QuestionAPITest(APITestCase):
    """Tests for Question API endpoints (Issue #39)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.bank = QuestionBank.objects.create(
            name="Test Bank",
            owner=self.user
        )
        self.tag = Tag.objects.create(name="#python")

    def test_create_question_with_tags(self):
        """Test creating a question with tags"""
        url = reverse('question-list')
        data = {
            'question_bank': self.bank.id,
            'text': 'What is a list comprehension?',
            'difficulty': 'medium',
            'tag_ids': [self.tag.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        question = Question.objects.get()
        self.assertEqual(question.tags.count(), 1)

    def test_bulk_tag_questions(self):
        """Test bulk tagging multiple questions"""
        q1 = Question.objects.create(
            question_bank=self.bank,
            text="Question 1",
            owner=self.user
        )
        q2 = Question.objects.create(
            question_bank=self.bank,
            text="Question 2",
            owner=self.user
        )

        url = reverse('question-bulk-tag')
        data = {
            'question_ids': [q1.id, q2.id],
            'tag_ids': [self.tag.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(q1.tags.count(), 1)
        self.assertEqual(q2.tags.count(), 1)


class TagFilteringTest(APITestCase):
    """Tests for tag filtering (Issue #41)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.bank = QuestionBank.objects.create(
            name="Test Bank",
            owner=self.user
        )
        self.tag_python = Tag.objects.create(name="#python")
        self.tag_sql = Tag.objects.create(name="#sql")

        # Create questions with different tags
        self.q1 = Question.objects.create(
            question_bank=self.bank,
            text="Python question",
            owner=self.user
        )
        self.q1.tags.add(self.tag_python)

        self.q2 = Question.objects.create(
            question_bank=self.bank,
            text="SQL question",
            owner=self.user
        )
        self.q2.tags.add(self.tag_sql)

        self.q3 = Question.objects.create(
            question_bank=self.bank,
            text="Both tags",
            owner=self.user
        )
        self.q3.tags.add(self.tag_python, self.tag_sql)

    def test_filter_by_single_tag(self):
        """Test filtering questions by a single tag"""
        url = reverse('question-list')
        response = self.client.get(url, {'tags': [self.tag_python.id]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return q1 and q3
        self.assertEqual(len(response.data), 2)

    def test_filter_by_multiple_tags_and_logic(self):
        """Test filtering with AND logic"""
        url = reverse('question-list')
        response = self.client.get(url, {
            'tags': [self.tag_python.id, self.tag_sql.id],
            'filter_mode': 'AND'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return only q3
        self.assertEqual(len(response.data), 1)

    def test_filter_by_multiple_tags_or_logic(self):
        """Test filtering with OR logic"""
        url = reverse('question-list')
        response = self.client.get(url, {
            'tags': [self.tag_python.id, self.tag_sql.id],
            'filter_mode': 'OR'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return all 3 questions
        self.assertEqual(len(response.data), 3)


class AutoAssembleInterviewTest(APITestCase):
    """Tests for auto-interview assembly (Issue #42)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.bank = QuestionBank.objects.create(
            name="Test Bank",
            owner=self.user
        )
        self.tag = Tag.objects.create(name="#python")

        # Create questions with different difficulties
        for i in range(3):
            q = Question.objects.create(
                question_bank=self.bank,
                text=f"Easy question {i}",
                difficulty="easy",
                owner=self.user
            )
            q.tags.add(self.tag)

        for i in range(5):
            q = Question.objects.create(
                question_bank=self.bank,
                text=f"Medium question {i}",
                difficulty="medium",
                owner=self.user
            )
            q.tags.add(self.tag)

        for i in range(2):
            q = Question.objects.create(
                question_bank=self.bank,
                text=f"Hard question {i}",
                difficulty="hard",
                owner=self.user
            )
            q.tags.add(self.tag)

    def test_auto_assemble_interview(self):
        """Test auto-assembling an interview"""
        url = reverse('auto_assemble_interview')
        data = {
            'title': 'Test Interview',
            'tag_ids': [self.tag.id],
            'question_count': 10,
            'difficulty_distribution': {
                'easy': 30,
                'medium': 50,
                'hard': 20
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_questions'], 10)

    def test_insufficient_questions_warning(self):
        """Test warning when insufficient questions available"""
        url = reverse('auto_assemble_interview')
        data = {
            'tag_ids': [self.tag.id],
            'question_count': 20  # More than available
        }
        response = self.client.post(url, data, format='json')
        # Should return partial content with warning
        self.assertIn('available_count', response.data)


class TagManagementTest(APITestCase):
    """Tests for tag management (Issue #40)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_rename_tag(self):
        """Test renaming a tag globally"""
        tag = Tag.objects.create(name="#python")
        url = reverse('tag-rename', args=[tag.id])
        data = {'new_name': '#python3'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, '#python3')

    def test_merge_tags(self):
        """Test merging multiple tags"""
        tag1 = Tag.objects.create(name="#sql")
        tag2 = Tag.objects.create(name="#database")
        tag3 = Tag.objects.create(name="#rdbms")

        # Create questions with these tags
        bank = QuestionBank.objects.create(name="Test", owner=self.user)
        q1 = Question.objects.create(
            question_bank=bank,
            text="Q1",
            owner=self.user
        )
        q1.tags.add(tag2)

        url = reverse('tag-merge')
        data = {
            'tag_ids': [tag1.id, tag2.id],
            'primary_tag_id': tag1.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # tag2 should be deleted
        self.assertFalse(Tag.objects.filter(id=tag2.id).exists())
        # q1 should now have tag1
        self.assertIn(tag1, q1.tags.all())

    def test_tag_statistics(self):
        """Test getting tag usage statistics"""
        Tag.objects.create(name="#python")
        Tag.objects.create(name="#sql")

        url = reverse('tag-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_tags', response.data)
        self.assertEqual(response.data['total_tags'], 2)
