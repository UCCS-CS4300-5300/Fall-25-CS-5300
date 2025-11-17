"""
Tests for connection drop detection and message caching functionality.

This module tests the backend behavior when connections drop or timeout,
ensuring proper error handling and response formats that work with the
frontend connection monitoring system.
"""

import json
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from ..models import Chat, UploadedJobListing, UploadedResume


# === Helper Functions ===
def generateConnectionTestUser():
    """Create a test user for connection handling tests."""
    user = User.objects.create_user(
        username="connectiontestuser",
        password="testpass123"
    )
    return user


def generateConnectionTestChat(owner):
    """Create a test chat for connection handling tests."""
    chat = Chat.objects.create(
        title="Connection Test Chat",
        owner=owner,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
        ],
        key_questions=[]
    )
    return chat


def generateConnectionTestChatWithQuestions(owner):
    """Create a test chat with key questions for testing."""
    # Create job listing for the chat
    job_listing = UploadedJobListing.objects.create(
        user=owner,
        title='Test Job',
        content='Software Engineer position',
        filename='job.txt'
    )

    # Create resume for the chat
    resume = UploadedResume.objects.create(
        user=owner,
        content='Test resume content',
        title='Test Resume',
        original_filename='resume.txt'
    )

    chat = Chat.objects.create(
        title="Interview Test Chat",
        owner=owner,
        job_listing=job_listing,
        resume=resume,
        messages=[{"role": "system", "content": "You are an interviewer."}],
        key_questions=[
            {
                "id": 0,
                "title": "Test Question",
                "duration": 120,
                "content": "What is your experience with Python?"
            },
            {
                "id": 1,
                "title": "Second Question",
                "duration": 90,
                "content": "Describe a challenging project."
            }
        ]
    )
    return chat


# === View Tests ===
class TestConnectionHandlingChatView(TestCase):
    """Test connection handling features in chat view."""

    def setUp(self):
        """Set up test user and chat for connection handling tests."""
        self.user = generateConnectionTestUser()
        self.chat = generateConnectionTestChat(self.user)
        self.client.force_login(self.user)

    def testGETChatViewHasConnectionFeatures(self):
        """Test that GET requests to chat view include connection handling features."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Connection Test Chat')
        self.assertContains(response, 'connection-status')
        self.assertContains(response, 'Saved by server')
        self.assertTemplateUsed(response, 'base-sidebar.html')

    @patch('active_interview_app.views.get_openai_client')
    def testPOSTChatViewSuccess(self, mock_get_client):
        """Test successful message post to chat view."""
        # Mock the OpenAI client and API response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test AI response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.post(url, {'message': 'Test message'})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Test AI response')

    @patch('active_interview_app.views._ai_available')
    def testPOSTChatViewAIUnavailable(self, mock_ai_available):
        """Test chat view when AI service is unavailable."""
        mock_ai_available.return_value = False

        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.post(url, {'message': 'Test message'})

        self.assertEqual(response.status_code, 503)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def testChatViewUnauthorizedAccess(self):
        """Test that unauthorized users cannot access another user's chat."""
        other_user = User.objects.create_user(
            username="otheruserconnection",
            password="otherpass123"
        )
        other_chat = Chat.objects.create(
            title="Other User Chat",
            owner=other_user,
            messages=[{"role": "system", "content": "System"}]
        )

        url = reverse('chat-view', args=[other_chat.id])
        response = self.client.get(url)

        # Should redirect or return forbidden
        self.assertIn(response.status_code, [302, 403, 404])

    def testConnectionDroppedNotificationPresent(self):
        """Test that connection dropped inline notification is present in chat view."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'connectionDroppedNotification')
        self.assertContains(response, 'Connection Lost')
        self.assertContains(response, 'Retry')
        self.assertContains(response, 'Disconnected at')

    def testNotificationIsDismissible(self):
        """Test that inline notification has dismiss functionality."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'dismissConnectionNotification')
        self.assertContains(response, 'btn-close')

    def testCachingKeysPresent(self):
        """Test that caching configuration is present in JavaScript."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CACHE_KEY')
        self.assertContains(response, 'PENDING_KEY')
        self.assertContains(response, 'PENDING_SYNC_KEY')
        self.assertContains(response, f'chat_input_cache_{self.chat.id}')
        self.assertContains(response, f'chat_pending_message_{self.chat.id}')
        self.assertContains(response, f'chat_pending_sync_{self.chat.id}')

    def testConnectionStatusFunctionsPresent(self):
        """Test that connection status management functions are present."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'updateConnectionStatus')
        self.assertContains(response, 'showConnectionDroppedModal')
        self.assertContains(response, 'retryConnection')
        self.assertContains(response, 'saveCachedInput')
        self.assertContains(response, 'restoreCachedInput')
        self.assertContains(response, 'savePendingMessage')
        self.assertContains(response, 'restorePendingMessage')
        self.assertContains(response, 'getPendingMessages')
        self.assertContains(response, 'savePendingMessages')
        self.assertContains(response, 'addToPendingSync')
        self.assertContains(response, 'syncPendingMessages')
        self.assertContains(response, 'startSyncCheck')


class TestConnectionHandlingKeyQuestions(TestCase):
    """Test connection handling for key questions functionality."""

    def setUp(self):
        """Set up test user and chat with key questions."""
        self.user = generateConnectionTestUser()
        self.chat = generateConnectionTestChatWithQuestions(self.user)
        self.client.force_login(self.user)

    def testGETKeyQuestionsHasConnectionStatus(self):
        """Test that connection status indicator is present in key questions."""
        url = reverse('key-questions', args=[self.chat.id, 0])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'connection-status')
        self.assertContains(response, 'Saved by server')
        self.assertTemplateUsed(response, 'base-sidebar.html')

    def testKeyQuestionsNotificationPresent(self):
        """Test that connection dropped inline notification is present in key questions."""
        url = reverse('key-questions', args=[self.chat.id, 0])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'connectionDroppedNotification')
        self.assertContains(response, 'Connection Lost')
        self.assertContains(response, 'Retry')
        self.assertContains(response, 'Disconnected at')

    def testKeyQuestionsCachingKeysPresent(self):
        """Test that caching configuration is present for key questions."""
        url = reverse('key-questions', args=[self.chat.id, 0])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'key_question_cache')
        self.assertContains(response, 'key_question_pending')
        self.assertContains(response, f'{self.chat.id}')

    @patch('active_interview_app.views.get_openai_client')
    def testPOSTKeyQuestionsSuccess(self, mock_get_client):
        """Test successful answer submission to key question."""
        # Mock the OpenAI client and API response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Excellent answer!"
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        url = reverse('key-questions', args=[self.chat.id, 0])
        response = self.client.post(url, {'message': 'My detailed answer'})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Excellent answer!')


class TestConnectionMonitoringJavaScript(TestCase):
    """Test that JavaScript connection monitoring is properly configured."""

    def setUp(self):
        """Set up test user and chat."""
        self.user = generateConnectionTestUser()
        self.chat = generateConnectionTestChat(self.user)
        self.client.force_login(self.user)

    def testHeartbeatFunctionPresent(self):
        """Test that heartbeat monitoring function is present."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'startHeartbeat')
        self.assertContains(response, 'heartbeatInterval')
        self.assertContains(response, '5000')  # 5 second interval

    def testSyncCheckIntervalPresent(self):
        """Test that sync check interval is configured."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SYNC_CHECK_INTERVAL')
        self.assertContains(response, '15000')  # 15 second interval
        self.assertContains(response, 'syncInterval')

    def testAjaxErrorHandlingPresent(self):
        """Test that AJAX error handling is configured."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'error: function')
        self.assertContains(response, 'timeout:')
        self.assertContains(response, '30000')  # 30 second timeout

    def testConnectionStatusStylingPresent(self):
        """Test that connection status CSS styling is present."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '.connection-status')
        self.assertContains(response, '.connection-status.online')
        self.assertContains(response, '.connection-status.offline')
        self.assertContains(response, 'animation: pulse')

    def testDarkModeCompatibleStyles(self):
        """Test that connection modal uses theme-aware colors."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'var(--surface')
        self.assertContains(response, 'var(--text-primary')
        self.assertContains(response, 'var(--error')
        self.assertContains(response, 'var(--success')
        self.assertContains(response, 'var(--warning')


class TestMessageCaching(TestCase):
    """Test message caching and recovery functionality."""

    def setUp(self):
        """Set up test user and chat."""
        self.user = generateConnectionTestUser()
        self.chat = generateConnectionTestChat(self.user)
        self.client.force_login(self.user)

    def testAutoSaveConfiguration(self):
        """Test that auto-save is configured."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'setupAutoSave')
        self.assertContains(response, 'CACHE_INTERVAL')
        self.assertContains(response, '1000')  # 1 second interval

    def testLocalStorageOperationsPresent(self):
        """Test that localStorage operations are configured."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'localStorage.setItem')
        self.assertContains(response, 'localStorage.getItem')
        self.assertContains(response, 'localStorage.removeItem')

    def testPendingMessageProtection(self):
        """Test that pending message protection is configured."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'savePendingMessage')
        self.assertContains(response, 'restorePendingMessage')
        self.assertContains(response, 'PENDING_KEY')

    def testMessageRestorationOnError(self):
        """Test that messages are restored on send error."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check that error handler restores the message
        self.assertContains(response, 'restorePendingMessage()')
        self.assertContains(response, 'restored to the input field')


class TestSyncStatusIndicators(TestCase):
    """Test sync status indicators (Sync Pending and Sync Successful)."""

    def setUp(self):
        """Set up test user and chat."""
        self.user = generateConnectionTestUser()
        self.chat = generateConnectionTestChat(self.user)
        self.client.force_login(self.user)

    def testSyncPendingIndicatorCSSPresent(self):
        """Test that Sync Pending indicator CSS is present."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '.sync-pending-indicator')
        self.assertContains(response, 'Sync Pending')
        self.assertContains(response, 'bi-arrow-repeat')

    def testSyncSuccessfulIndicatorCSSPresent(self):
        """Test that Sync Successful indicator CSS is present."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '.sync-successful-indicator')
        self.assertContains(response, 'Sync Successful')
        self.assertContains(response, 'bi-check-circle-fill')

    def testSyncSuccessfulFadeOutAnimation(self):
        """Test that Sync Successful indicator has fade out animation."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '@keyframes fadeOut')
        self.assertContains(response, 'animation: fadeOut 3s ease-out forwards')

    def testSyncSuccessfulUsesThemeColors(self):
        """Test that Sync Successful indicator uses theme-aware colors."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'var(--success)')

    def testSyncSuccessfulReplacementLogic(self):
        """Test that sync logic replaces pending indicator with successful indicator."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check that the sync function replaces the pending indicator
        self.assertContains(response, '.sync-pending-indicator').remove()')
        self.assertContains(response, '.sync-successful-indicator')
        # Check that successful indicator is removed after 3 seconds
        self.assertContains(response, 'setTimeout')
        self.assertContains(response, '3000')

    def testSyncPendingAddedOnNetworkError(self):
        """Test that Sync Pending is added when network error occurs."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check that error handler adds sync pending indicator
        self.assertContains(response, 'addToPendingSync')
        self.assertContains(response, 'text-warning')

    def testSyncIndicatorPositioning(self):
        """Test that sync indicators are positioned correctly below messages."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check CSS positioning
        self.assertContains(response, 'margin-top: 0.25rem')
        self.assertContains(response, 'text-align: left')
