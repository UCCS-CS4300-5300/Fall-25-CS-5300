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
from .test_credentials import TEST_PASSWORD
from .test_utils import create_mock_openai_response


# === Helper Functions ===
def generateConnectionTestUser():
    """Create a test user for connection handling tests."""
    user = User.objects.create_user(
        username="connectiontestuser",
        password=TEST_PASSWORD
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

    def test_get_chat_view_has_connection_features(self):
        """Test that GET requests to chat view include connection handling features."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Connection Test Chat')
        self.assertContains(response, 'connection-status')
        self.assertContains(response, 'Saved by server')
        self.assertTemplateUsed(response, 'base-sidebar.html')

    @patch('active_interview_app.views.get_client_and_model')
    def test_post_chat_view_success(self, mock_get_client_and_model):
        """Test successful message post to chat view."""
        # Mock the OpenAI client and API response
        mock_client = MagicMock()
        mock_response = create_mock_openai_response("Test AI response")
        mock_client.chat.completions.create.return_value = mock_response
        # get_client_and_model returns (client, model, tier_info)
        mock_get_client_and_model.return_value = (mock_client, "gpt-4o", {"tier": "premium"})

        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.post(url, {'message': 'Test message'})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Test AI response')

    @patch('active_interview_app.views.get_client_and_model')
    def test_post_chat_view_ai_unavailable(self, mock_get_client_and_model):
        """Test chat view when AI service raises an exception."""
        # Mock get_client_and_model to raise an exception
        mock_get_client_and_model.side_effect = Exception("AI service unavailable")

        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.post(url, {'message': 'Test message'})

        # The view should handle the exception gracefully
        # Response code may vary based on implementation
        self.assertIn(response.status_code, [200, 500, 503])

    def test_chat_view_unauthorized_access(self):
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

    def test_connection_dropped_notification_present(self):
        """Test that connection dropped inline notification is present in chat view."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'connectionDroppedNotification')
        self.assertContains(response, 'Connection Lost')
        self.assertContains(response, 'Retry')
        self.assertContains(response, 'Disconnected at')

    def test_notification_is_dismissible(self):
        """Test that inline notification has dismiss functionality."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'dismissConnectionNotification')
        self.assertContains(response, 'btn-close')

    def test_caching_keys_present(self):
        """Test that connection handler module and chat ID configuration are present."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check for connection-handler.js module inclusion
        self.assertContains(response, 'connection-handler.js')
        # Check for ConnectionHandler initialization with chatId
        self.assertContains(response, 'ConnectionHandler')
        self.assertContains(response, 'chatId')
        self.assertContains(response, f'{self.chat.id}')

    def test_connection_status_functions_present(self):
        """Test that connection handler methods and wrapper functions are present."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check for ConnectionHandler instance and usage
        self.assertContains(response, 'connectionHandler')
        self.assertContains(response, 'connectionHandler.start()')

        # Check for wrapper functions for backwards compatibility
        self.assertContains(response, 'function retryConnection()')
        self.assertContains(response, 'function dismissConnectionNotification()')

        # Check for connectionHandler method calls
        self.assertContains(response, 'connectionHandler.updateConnectionStatus')
        self.assertContains(response, 'connectionHandler.saveCachedInput')
        self.assertContains(response, 'connectionHandler.restoreCachedInput')
        self.assertContains(response, 'connectionHandler.savePendingMessage')
        self.assertContains(response, 'connectionHandler.addToPendingSync')
        self.assertContains(response, 'connectionHandler.syncPendingMessages')


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
        """Test that connection handler module is present for key questions."""
        url = reverse('key-questions', args=[self.chat.id, 0])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check for connection-handler.js module inclusion
        self.assertContains(response, 'connection-handler.js')
        # Check for ConnectionHandler initialization with chatId and question ID
        self.assertContains(response, 'ConnectionHandler')
        self.assertContains(response, 'chatId')
        self.assertContains(response, f'{self.chat.id}')

    @patch('active_interview_app.views.get_client_and_model')
    def testPOSTKeyQuestionsSuccess(self, mock_get_client_and_model):
        """Test successful answer submission to key question."""
        # Mock the OpenAI client and API response
        mock_client = MagicMock()
        mock_response = create_mock_openai_response("Excellent answer!")
        mock_client.chat.completions.create.return_value = mock_response
        # get_client_and_model returns (client, model, tier_info)
        mock_get_client_and_model.return_value = (mock_client, "gpt-4o", {"tier": "premium"})

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
        """Test that connection handler starts heartbeat monitoring."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check that connectionHandler.start() is called, which starts heartbeat
        self.assertContains(response, 'connectionHandler.start()')
        # Check for CONFIG constants from connection-handler.js
        self.assertContains(response, 'CONFIG')

    def testSyncCheckIntervalPresent(self):
        """Test that sync check is started via connection handler."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # The connectionHandler.start() includes starting sync check
        self.assertContains(response, 'connectionHandler.start()')
        # Check for CONFIG object which contains SYNC_CHECK_INTERVAL
        self.assertContains(response, 'CONFIG')

    def testAjaxErrorHandlingPresent(self):
        """Test that AJAX error handling uses CONFIG timeout."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'error: function')
        self.assertContains(response, 'timeout:')
        # Check for CONFIG.AJAX_TIMEOUT usage
        self.assertContains(response, 'CONFIG.AJAX_TIMEOUT')

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
        self.assertContains(response, 'var(--text-secondary')
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
        """Test that auto-save is configured via connection handler."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check for setupAutoSave function (still in template)
        self.assertContains(response, 'setupAutoSave')
        # Check for CONFIG usage (from connection-handler.js)
        self.assertContains(response, 'CONFIG')
        self.assertContains(response, 'connectionHandler.saveCachedInput')

    def testLocalStorageOperationsPresent(self):
        """Test that localStorage operations are available via connection handler."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # LocalStorage operations are now in connection-handler.js module
        # Check that the module is included and connectionHandler is used
        self.assertContains(response, 'connection-handler.js')
        self.assertContains(response, 'connectionHandler')
        # Some localStorage operations still exist in template (e.g., for cache removal)
        self.assertContains(response, 'localStorage.removeItem')

    def testPendingMessageProtection(self):
        """Test that pending message protection is configured via connection handler."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # These methods are now part of connectionHandler
        self.assertContains(response, 'connectionHandler.savePendingMessage')
        self.assertContains(response, 'connectionHandler.clearPendingMessage')
        # Check that connectionHandler has storage keys
        self.assertContains(response, 'connectionHandler')

    def testMessageRestorationOnError(self):
        """Test that messages are restored on send error."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check that error messages mention restoration
        self.assertContains(response, 'restored to the input field')
        # Check that there's error handling in sendMessage
        self.assertContains(response, 'error: function')


class TestSyncStatusIndicators(TestCase):
    """Test sync status indicators (Sync Pending and Sync Successful)."""

    def setUp(self):
        """Set up test user and chat."""
        self.user = generateConnectionTestUser()
        self.chat = generateConnectionTestChat(self.user)
        self.client.force_login(self.user)

    def testSyncPendingIndicatorCSSPresent(self):
        """Test that Sync Pending indicator CSS and logic are present."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # CSS is still in the template
        self.assertContains(response, '.sync-pending-indicator')
        # Logic is now in connection-handler.js via connectionHandler methods
        self.assertContains(response, 'connectionHandler.addSyncPendingIndicator')
        self.assertContains(response, 'bi-arrow-repeat')

    def testSyncSuccessfulIndicatorCSSPresent(self):
        """Test that Sync Successful indicator CSS and logic are present."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # CSS is still in the template
        self.assertContains(response, '.sync-successful-indicator')
        # Logic is now in connection-handler.js via connectionHandler methods
        self.assertContains(response, 'connectionHandler.showSyncSuccessful')
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
        # Check that the custom sync override uses connectionHandler methods
        self.assertContains(response, 'connectionHandler.showSyncSuccessful')
        self.assertContains(response, '.sync-successful-indicator')
        # The timeout logic is now in connection-handler.js
        # Check that we're calling the method from our custom sync function
        self.assertContains(response, 'connectionHandler.syncPendingMessages')

    def testSyncPendingAddedOnNetworkError(self):
        """Test that Sync Pending is added when network error occurs."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check that error handler adds sync pending indicator via connectionHandler
        self.assertContains(response, 'connectionHandler.addToPendingSync')
        self.assertContains(response, 'connectionHandler.addSyncPendingIndicator')
        self.assertContains(response, 'text-warning')

    def testSyncIndicatorPositioning(self):
        """Test that sync indicators are positioned correctly below messages."""
        url = reverse('chat-view', args=[self.chat.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check CSS positioning
        self.assertContains(response, 'margin-top: 0.25rem')
        self.assertContains(response, 'text-align: left')
