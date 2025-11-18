/**
 * Connection Handler Module
 *
 * Manages offline/online connection state, message queueing, and automatic sync
 * for the Active Interview Service chat functionality.
 *
 * @module ConnectionHandler
 */

'use strict';

// ============================================================================
// Configuration Constants
// ============================================================================

const CONFIG = {
  // Time intervals (milliseconds)
  CACHE_SAVE_INTERVAL: 1000,        // Auto-save user input every 1 second
  HEARTBEAT_INTERVAL: 5000,         // Check connection every 5 seconds
  SYNC_CHECK_INTERVAL: 15000,       // Attempt to sync pending messages every 15 seconds
  AJAX_TIMEOUT: 30000,              // AJAX request timeout: 30 seconds
  SYNC_RETRY_DELAY: 1000,           // Delay between syncing multiple messages
  SUCCESS_INDICATOR_DURATION: 3000, // How long to show "Sync Successful" before fade

  // Status text
  STATUS_TEXT: {
    ONLINE: 'Saved by server',
    OFFLINE: 'Saved locally'
  },

  // CSS classes
  CSS_CLASSES: {
    CONNECTION_STATUS: 'connection-status',
    ONLINE: 'online',
    OFFLINE: 'offline',
    SYNC_PENDING: 'sync-pending-indicator',
    SYNC_SUCCESSFUL: 'sync-successful-indicator'
  },

  // Icon classes (Bootstrap Icons)
  ICONS: {
    WIFI: 'bi bi-wifi',
    WIFI_OFF: 'bi bi-wifi-off',
    ARROW_REPEAT: 'bi bi-arrow-repeat',
    CHECK_CIRCLE: 'bi bi-check-circle-fill'
  }
};

// ============================================================================
// Connection Handler Class
// ============================================================================

class ConnectionHandler {
  /**
   * Initialize the connection handler
   * @param {Object} options - Configuration options
   * @param {string} options.chatId - Unique identifier for this chat
   * @param {string} options.heartbeatUrl - URL to ping for connection checks
   * @param {Function} options.onConnectionChange - Callback when connection state changes
   */
  constructor(options) {
    this.chatId = options.chatId;
    this.heartbeatUrl = options.heartbeatUrl;
    this.onConnectionChange = options.onConnectionChange || function() {};

    // State
    this.isOnline = true;
    this.connectionDroppedTime = null;

    // Intervals
    this.heartbeatInterval = null;
    this.syncInterval = null;

    // LocalStorage keys
    this.storageKeys = {
      cache: `chat_input_cache_${this.chatId}`,
      pending: `chat_pending_message_${this.chatId}`,
      pendingSync: `chat_pending_sync_${this.chatId}`
    };

    this._initializeUI();
  }

  // --------------------------------------------------------------------------
  // Initialization
  // --------------------------------------------------------------------------

  /**
   * Initialize UI elements and event listeners
   * @private
   */
  _initializeUI() {
    this.elements = {
      status: document.getElementById('connection-status'),
      statusIcon: document.querySelector('.connection-status-icon'),
      statusText: document.querySelector('.connection-status-text'),
      notification: document.getElementById('connectionDroppedNotification'),
      dropTime: document.getElementById('connectionDropTime')
    };
  }

  /**
   * Start monitoring connection and syncing messages
   */
  start() {
    this.updateConnectionStatus(true);
    this.startHeartbeat();
    this.startSyncCheck();

    // Check for pending messages from previous session
    const pendingMessages = this.getPendingMessages();
    if (pendingMessages.length > 0) {
      console.log(`Found ${pendingMessages.length} pending message(s) from previous session`);
      this.syncPendingMessages();
    }
  }

  /**
   * Stop monitoring (cleanup)
   */
  stop() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  // --------------------------------------------------------------------------
  // Connection Status Management
  // --------------------------------------------------------------------------

  /**
   * Update connection status UI
   * @param {boolean} isOnline - Whether the connection is online
   */
  updateConnectionStatus(isOnline) {
    this.isOnline = isOnline;

    const { statusIcon, statusText } = this.elements;
    const { CSS_CLASSES, ICONS, STATUS_TEXT } = CONFIG;

    if (isOnline) {
      this.elements.status.classList.remove(CSS_CLASSES.OFFLINE);
      this.elements.status.classList.add(CSS_CLASSES.ONLINE);
      statusIcon.className = `${ICONS.WIFI} connection-status-icon`;
      statusText.textContent = STATUS_TEXT.ONLINE;
    } else {
      this.elements.status.classList.remove(CSS_CLASSES.ONLINE);
      this.elements.status.classList.add(CSS_CLASSES.OFFLINE);
      statusIcon.className = `${ICONS.WIFI_OFF} connection-status-icon`;
      statusText.textContent = STATUS_TEXT.OFFLINE;
    }

    this.onConnectionChange(isOnline);
  }

  /**
   * Show connection dropped notification
   */
  showConnectionDroppedNotification() {
    if (this.isOnline) {
      this.isOnline = false;
      this.connectionDroppedTime = new Date();

      const formattedTime = this.connectionDroppedTime.toLocaleString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });

      this.elements.dropTime.textContent = formattedTime;
      this.updateConnectionStatus(false);
      this.elements.notification.style.display = 'block';
    }
  }

  /**
   * Dismiss connection notification
   */
  dismissNotification() {
    this.elements.notification.style.display = 'none';
  }

  /**
   * Manually retry connection
   */
  retryConnection() {
    return fetch(this.heartbeatUrl, {
      method: 'GET',
      signal: AbortSignal.timeout(CONFIG.HEARTBEAT_INTERVAL)
    })
    .then(() => {
      this._handleConnectionRestored();
      return true;
    })
    .catch(() => {
      this.updateConnectionStatus(false);
      return false;
    });
  }

  /**
   * Handle connection restored
   * @private
   */
  _handleConnectionRestored() {
    this.isOnline = true;
    this.connectionDroppedTime = null;
    this.updateConnectionStatus(true);
    this.dismissNotification();
    console.log('Connection restored successfully');
    this.syncPendingMessages();
  }

  // --------------------------------------------------------------------------
  // Heartbeat Monitoring
  // --------------------------------------------------------------------------

  /**
   * Start periodic heartbeat to check connection
   */
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      fetch(this.heartbeatUrl, {
        method: 'GET',
        signal: AbortSignal.timeout(CONFIG.HEARTBEAT_INTERVAL)
      })
      .then(() => {
        if (!this.isOnline) {
          this._handleConnectionRestored();
        }
      })
      .catch((error) => {
        // Only show notification for network errors
        if (error.name === 'TypeError' || error.name === 'TimeoutError') {
          this.showConnectionDroppedNotification();
        }
      });
    }, CONFIG.HEARTBEAT_INTERVAL);
  }

  /**
   * Start periodic sync check
   */
  startSyncCheck() {
    this.syncInterval = setInterval(() => {
      if (this.isOnline) {
        this.syncPendingMessages();
      }
    }, CONFIG.SYNC_CHECK_INTERVAL);
  }

  // --------------------------------------------------------------------------
  // Message Queue Management (LocalStorage)
  // --------------------------------------------------------------------------

  /**
   * Get pending messages from localStorage
   * @returns {Array} Array of pending message objects
   */
  getPendingMessages() {
    const data = localStorage.getItem(this.storageKeys.pendingSync);
    return data ? JSON.parse(data) : [];
  }

  /**
   * Save pending messages to localStorage
   * @param {Array} messages - Array of message objects
   */
  savePendingMessages(messages) {
    if (messages.length > 0) {
      localStorage.setItem(this.storageKeys.pendingSync, JSON.stringify(messages));
    } else {
      localStorage.removeItem(this.storageKeys.pendingSync);
    }
  }

  /**
   * Add message to pending sync queue
   * @param {string} messageText - The message content
   * @param {string} elementId - DOM element ID for the message
   */
  addToPendingSync(messageText, elementId) {
    const pendingMessages = this.getPendingMessages();
    pendingMessages.push({
      message: messageText,
      timestamp: Date.now(),
      elementId: elementId
    });
    this.savePendingMessages(pendingMessages);
  }

  /**
   * Add sync pending indicator to a message element
   * @param {string} elementId - DOM element ID
   */
  addSyncPendingIndicator(elementId) {
    const messageElement = document.getElementById(elementId);
    if (messageElement) {
      const indicator = document.createElement('div');
      indicator.className = CONFIG.CSS_CLASSES.SYNC_PENDING;
      indicator.innerHTML = `
        <small class="text-warning">
          <i class="${CONFIG.ICONS.ARROW_REPEAT}"></i> Sync Pending
        </small>
      `;
      messageElement.appendChild(indicator);
    }
  }

  /**
   * Replace sync pending with sync successful indicator
   * @param {string} elementId - DOM element ID
   */
  showSyncSuccessful(elementId) {
    const messageElement = document.getElementById(elementId);
    if (!messageElement) return;

    // Remove pending indicator
    const pendingIndicator = messageElement.querySelector(`.${CONFIG.CSS_CLASSES.SYNC_PENDING}`);
    if (pendingIndicator) {
      pendingIndicator.remove();
    }

    // Add success indicator
    const successIndicator = document.createElement('div');
    successIndicator.className = CONFIG.CSS_CLASSES.SYNC_SUCCESSFUL;
    successIndicator.innerHTML = `
      <small>
        <i class="${CONFIG.ICONS.CHECK_CIRCLE}"></i> Sync Successful
      </small>
    `;
    messageElement.appendChild(successIndicator);

    // Remove after configured duration
    setTimeout(() => {
      if (successIndicator.parentElement) {
        successIndicator.remove();
      }
    }, CONFIG.SUCCESS_INDICATOR_DURATION);
  }

  // --------------------------------------------------------------------------
  // Message Syncing
  // --------------------------------------------------------------------------

  /**
   * Sync pending messages with server
   * @param {Function} sendMessageCallback - Function to call for each message
   * @returns {Promise} Promise that resolves when sync is complete
   */
  async syncPendingMessages(sendMessageCallback) {
    const pendingMessages = this.getPendingMessages();
    if (pendingMessages.length === 0) {
      return Promise.resolve();
    }

    console.log(`Attempting to sync ${pendingMessages.length} pending message(s)...`);

    // Process messages one at a time
    const message = pendingMessages[0];

    try {
      const response = await sendMessageCallback(message.message);

      // Sync successful
      this.showSyncSuccessful(message.elementId);

      // Remove from queue
      pendingMessages.shift();
      this.savePendingMessages(pendingMessages);

      console.log('Message synced successfully');
      this.updateConnectionStatus(true);

      // If more messages, sync them with delay
      if (pendingMessages.length > 0) {
        setTimeout(() => {
          this.syncPendingMessages(sendMessageCallback);
        }, CONFIG.SYNC_RETRY_DELAY);
      }

      return response;
    } catch (error) {
      console.log('Sync failed, will retry later');
      this.updateConnectionStatus(false);
      throw error;
    }
  }

  // --------------------------------------------------------------------------
  // Input Caching
  // --------------------------------------------------------------------------

  /**
   * Save user input to localStorage
   * @param {string} inputText - The input text to cache
   */
  saveCachedInput(inputText) {
    if (inputText.trim() !== '') {
      localStorage.setItem(this.storageKeys.cache, inputText);
    } else {
      localStorage.removeItem(this.storageKeys.cache);
    }
  }

  /**
   * Restore cached input
   * @returns {string|null} The cached input or null
   */
  restoreCachedInput() {
    // First check for pending message (message being sent when connection dropped)
    const pendingMessage = localStorage.getItem(this.storageKeys.pending);
    if (pendingMessage) {
      console.log('Restored message that failed to send');
      return pendingMessage;
    }

    // Otherwise restore regular cached input
    const cachedInput = localStorage.getItem(this.storageKeys.cache);
    if (cachedInput) {
      console.log('Restored unsent message from cache');
      return cachedInput;
    }

    return null;
  }

  /**
   * Clear all caches
   */
  clearAllCaches() {
    localStorage.removeItem(this.storageKeys.cache);
    localStorage.removeItem(this.storageKeys.pending);
  }

  /**
   * Save message to pending cache (called just before sending)
   * @param {string} messageText - The message to save
   */
  savePendingMessage(messageText) {
    localStorage.setItem(this.storageKeys.pending, messageText);
  }

  /**
   * Clear pending message cache
   */
  clearPendingMessage() {
    localStorage.removeItem(this.storageKeys.pending);
  }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ConnectionHandler, CONFIG };
}
