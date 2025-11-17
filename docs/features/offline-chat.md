# Offline Chat & Message Sync

## Overview

The Active Interview Service supports offline functionality for the interview chat interface, ensuring users can continue their interview sessions even when internet connectivity is spotty or temporarily unavailable. Messages are saved locally and automatically synced when connection is restored.

## Features

### Connection Status Monitoring

- **Real-time status indicator** showing whether messages are "Saved by server" (online) or "Saved locally" (offline)
- **Visual feedback** using color-coded icons:
  - Green wifi icon when online
  - Orange pulsing wifi-off icon when offline
- **Heartbeat monitoring** checks connection every 5 seconds
- **Automatic detection** of connection drops

### Message Queueing

When internet connection is lost:

1. **Local Storage**: Messages are saved to browser localStorage immediately
2. **Sync Pending Indicator**: Messages display a "Sync Pending" status below them with a rotating arrow icon
3. **Queue Management**: All pending messages are stored in a queue for later sync
4. **Persistence**: Messages persist across page reloads until successfully synced

### Connection Recovery

When internet connection is restored:

1. **Automatic Detection**: Heartbeat detects connection recovery
2. **Auto-Sync**: Pending messages are automatically sent to the server
3. **Sync Successful Indicator**: Successfully synced messages display a green checkmark with "Sync Successful" text
4. **Auto-Removal**: The "Sync Successful" indicator fades out after 3 seconds
5. **Sequential Processing**: Messages are synced one at a time to maintain conversation order

### User Notifications

- **Connection Dropped Notification**: Inline alert appears when connection is lost
  - Shows timestamp of when connection was dropped
  - Provides manual "Retry" button
  - Can be dismissed by user
- **Status Text**: Clear text indicators like "Saved by server" and "Saved locally"

## Technical Implementation

### Frontend (JavaScript)

**Location**: `active_interview_app/templates/chat/chat-view.html`

#### Key Functions:

- `updateConnectionStatus(isOnline)` - Updates UI based on connection state
- `showConnectionDroppedModal()` - Displays connection loss notification
- `retryConnection()` - Manual retry for connection
- `startHeartbeat()` - Monitors connection every 5 seconds
- `getPendingMessages()` / `savePendingMessages()` - LocalStorage management
- `addToPendingSync(message, elementId)` - Adds message to sync queue
- `syncPendingMessages()` - Syncs queued messages with server
- `startSyncCheck()` - Periodic sync check every 15 seconds

#### LocalStorage Keys:

```javascript
CACHE_KEY = 'chat_input_cache_<chat_id>'           // Auto-save user input
PENDING_KEY = 'chat_pending_message_<chat_id>'     // Message being sent
PENDING_SYNC_KEY = 'chat_pending_sync_<chat_id>'   // Queue of messages to sync
```

#### Configuration:

```javascript
CACHE_INTERVAL = 1000        // Auto-save input every 1 second
SYNC_CHECK_INTERVAL = 15000  // Check for sync every 15 seconds
HEARTBEAT_INTERVAL = 5000    // Check connection every 5 seconds
```

### Styling (CSS)

**Location**: Same template file (inline styles)

#### CSS Classes:

- `.connection-status` - Main status indicator container
- `.connection-status.online` - Online state styles (green)
- `.connection-status.offline` - Offline state styles (orange, pulsing)
- `.connection-notification` - Inline notification for connection drops
- `.sync-pending-indicator` - "Sync Pending" status below messages
- `.sync-successful-indicator` - "Sync Successful" status with fade-out animation

#### Theme Integration:

All styles use CSS variables for theme compatibility:
- `var(--success)` - Green for online/success states
- `var(--warning)` - Orange for offline/pending states
- `var(--surface)` - Background colors
- `var(--text-primary)` - Text colors
- `var(--shadow-md)` - Shadows and depth

### Backend (Django)

**No special backend changes required** - The offline functionality is primarily client-side. The existing chat view endpoints handle message submission normally when connection is available.

## User Experience Flow

### Normal Operation (Online)

1. User types message
2. Clicks send
3. Message appears in chat with user bubble
4. Loading animation shows
5. AI response appears
6. Status shows "Saved by server" in green

### Connection Loss Scenario

1. User types message
2. Connection drops
3. Status immediately changes to "Saved locally" (orange)
4. Connection notification appears
5. User clicks send
6. Message appears in chat with user bubble
7. "Sync Pending" indicator appears below message (rotating arrow)
8. Message stored in localStorage

### Connection Restored

1. Heartbeat detects connection (or user clicks Retry)
2. Connection notification disappears
3. Status changes to "Saved by server" (green)
4. Messages in queue sync automatically
5. "Sync Pending" replaced with "Sync Successful" (green checkmark)
6. "Sync Successful" fades out after 3 seconds
7. AI responses appear for synced messages

## Testing

**Test File**: `active_interview_app/tests/test_connection_handling.py`

### Test Coverage:

- Connection status UI components present
- Notification system functionality
- LocalStorage operations
- Caching configuration
- Heartbeat monitoring
- Sync check intervals
- AJAX error handling
- Theme-aware styling
- Sync status indicators (Pending and Successful)
- Fade-out animation for Sync Successful

### Running Tests:

```bash
cd active_interview_backend
python manage.py test active_interview_app.tests.test_connection_handling
```

## Browser Compatibility

### Requirements:

- **LocalStorage**: Supported by all modern browsers
- **Fetch API**: For connection detection
- **ES6 JavaScript**: Arrow functions, const/let, template literals

### Tested Browsers:

- Chrome/Edge (Chromium)
- Firefox
- Safari (macOS/iOS)

## Limitations

1. **LocalStorage Quotas**: Browsers typically limit localStorage to 5-10MB
   - Sufficient for hundreds of messages
   - Old entries cleared after successful sync

2. **Cross-Device Sync**: Pending messages are device-specific
   - Messages queued on one device won't appear on another
   - Server only receives messages once synced

3. **Message Order**: Messages sync sequentially to maintain conversation order
   - Multiple pending messages sync one at a time
   - 1-second delay between syncs to avoid overwhelming server

4. **Time Limits**: For invited interviews, time continues counting even when offline
   - Connection restoration doesn't pause the timer
   - Time-expired interviews cannot sync new messages

## Future Enhancements

Potential improvements:

1. **Service Worker**: For true offline PWA capability
2. **IndexedDB**: For larger message queues
3. **Optimistic UI**: Show AI response placeholder while syncing
4. **Retry Strategy**: Exponential backoff for failed syncs
5. **Conflict Resolution**: Handle edge cases with concurrent sessions

## Related Files

- Template: `active_interview_app/templates/chat/chat-view.html`
- Tests: `active_interview_app/tests/test_connection_handling.py`
- Views: `active_interview_app/views.py` (chat_view function)
- CSS Variables: `active_interview_app/static/css/main.css`
- Theme JS: `active_interview_app/static/js/theme.js`

## References

- [LocalStorage API](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)
- [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [Online and offline events](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/onLine)
