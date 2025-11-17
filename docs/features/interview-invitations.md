# Interview Invitation Feature

Schedule and manage formal interview invitations with candidates, complete with time-gated access, email notifications, and interviewer review.

## Overview

The Interview Invitation feature allows interviewers to send formal interview invitations to candidates via email. Candidates receive a unique join link, can start the interview within a specified time window, and receive feedback from the interviewer after completion.

## User Roles

### Interviewer Workflow

Interviewers can create, manage, and review interview invitations.

#### 1. Create Invitation

From the invitation dashboard or template detail page:

1. Navigate to `/invitations/` or `/templates/<id>/`
2. Click **"Create Invitation"** or **"Invite Candidate"**
3. Fill out the invitation form:
   - **Candidate Email:** Email address of the candidate
   - **Template:** Select an interview template with questions
   - **Scheduled Date & Time:** When the interview should start (local timezone)
   - **Duration:** How long the candidate has to complete (in minutes)
4. Click **"Send Invitation"**
5. System sends email with join link and calendar attachment
6. Redirected to confirmation page with invitation details

#### 2. View Invitations Dashboard

From `/invitations/`:

1. View all sent invitations
2. Filter by status:
   - **Pending:** Not yet started
   - **In Progress:** Currently active
   - **Completed:** Finished, awaiting review
   - **Reviewed:** Feedback provided
3. See invitation details (candidate, template, scheduled time)
4. Access review page for completed interviews

#### 3. Review Interview

From the invitation dashboard:

1. Click **"Review"** on a completed invitation
2. View interview transcript (without system prompts)
3. See AI-generated feedback and scores
4. Provide interviewer feedback:
   - Write detailed feedback in textarea
   - Click **"Save Feedback"** to save without notifying
   - Click **"Mark as Reviewed & Notify Candidate"** to finalize
5. Email sent to candidate with notification

### Candidate Workflow

Candidates receive invitations and complete interviews within the time window.

#### 1. Receive Invitation Email

Email includes:
- Interview details (template name, scheduled time, duration)
- Interviewer information
- Unique join link
- Calendar attachment (.ics file) for scheduling
- Instructions for joining

#### 2. Join Interview

Click the join link or navigate to it:

1. If not logged in, redirected to registration/login
2. Email verification (must match invited email)
3. Redirected to interview detail page

#### 3. View Interview Details

From `/interview/invited/<invitation_id>/`:

**Before scheduled time:**
- Countdown timer showing time until interview starts
- Interview window information
- Instructions and preparation tips

**During valid window:**
- "Start Interview Now" button enabled
- Time remaining to start the interview
- Interview details and instructions

**After window expires:**
- Warning that the window has passed
- Contact information for interviewer

#### 4. Start Interview

Click **"Start Interview Now"**:

1. Chat session created with template questions
2. System prompt loaded from template
3. Interview timer starts (duration countdown)
4. Redirected to chat interface
5. Time remaining banner displayed at top

#### 5. Complete Interview

During the interview:
- Answer questions via chat interface
- Monitor time remaining
- Interview auto-completes when time expires
- Can view results after completion

#### 6. View Results

From `/chat/<chat_id>/results/`:

1. View AI feedback and scores (charts)
2. Check interviewer review status:
   - **Pending:** Waiting for interviewer feedback
   - **Completed:** View interviewer feedback and timestamp
3. Generate detailed report with section scores
4. Download PDF report

#### 7. My Invitations Page

Navigate to `/my-invitations/`:

1. View all received invitations
2. See status (pending, in-progress, completed)
3. Access active interviews or view results
4. Track invitation history

---

## Key Features

### Time-Gated Access

**Interview Window Logic:**

- **Start Time:** Earliest the interview can be started (scheduled_time)
- **Window Close:** Latest the interview can be started (scheduled_time + duration_minutes)
- **Duration:** Time to complete once started (duration_minutes)

**Example:**
- Scheduled: 2:00 PM
- Duration: 60 minutes
- Window: 2:00 PM - 3:00 PM (can start anytime)
- Once started at 2:30 PM: Must complete by 3:30 PM

**Enforcement:**
- Cannot start before scheduled time
- Cannot start after window closes
- Auto-completes when duration expires
- Chat view disabled after time expires

### Email Notifications

**Invitation Sent Email:**
- Sent when invitation is created
- Includes join link, interview details, calendar attachment
- Template: `templates/emails/invitation_sent.html`

**Interview Completed Email:**
- Sent to interviewer when candidate completes
- Includes link to review page
- Template: `templates/emails/interview_completed.html`

**Review Notification Email:**
- Sent to candidate when interviewer marks as reviewed
- Includes link to view feedback
- Template: `templates/emails/interview_reviewed.html`

### Calendar Integration

**ICS Attachment:**
- Automatically generated calendar file
- Includes interview details and join link
- Works with Google Calendar, Outlook, Apple Calendar
- Generated by `invitation_utils.py:create_calendar_event()`

### Timezone Handling

**Server-side (UTC):**
- All datetimes stored in UTC in database
- Conversions handled by Django's timezone utilities

**Form Submission:**
- User selects date/time in their local timezone
- Form combines into datetime and converts to UTC
- Custom field: `InvitationCreationForm.scheduled_datetime`

**Display:**
- UTC times shown in templates with `data-utc-time` attribute
- JavaScript converts to user's local timezone on page load
- Format: "Jan 15, 2025, 2:30 PM PST"

### Template Requirements

**Valid Templates:**
- Must have `status = 'COMPLETE'`
- Must have at least one question (in sections)
- Templates without questions show warning
- Enforced in `InvitationCreationForm.clean_template()`

**System Prompt:**
- Loaded from template's first section
- Concatenated from all section prompts if multiple
- Initialized when interview starts
- Used to guide AI interviewer behavior

---

## Data Models

### InvitedInterview Model

**Fields:**
- `id` (UUID): Unique identifier for invitation
- `interviewer` (ForeignKey): User who created invitation
- `candidate_email` (EmailField): Invited candidate's email
- `template` (ForeignKey): InterviewTemplate to use
- `scheduled_time` (DateTimeField): When interview should start (UTC)
- `duration_minutes` (IntegerField): Time limit for interview
- `status` (CharField): PENDING, IN_PROGRESS, COMPLETED
- `interviewer_review_status` (CharField): PENDING, REVIEW_COMPLETE
- `chat` (OneToOneField): Associated Chat session (if started)
- `interviewer_feedback` (TextField): Feedback from interviewer
- `invitation_sent_at` (DateTimeField): When email was sent
- `completed_at` (DateTimeField): When interview finished
- `reviewed_at` (DateTimeField): When interviewer marked as reviewed

**Methods:**
- `get_join_url()`: Returns full URL for candidate to join
- `can_start()`: Checks if current time is within window
- `is_expired()`: Checks if window has passed
- `get_window_end()`: Calculates when window closes

**See:** `active_interview_app/models.py`

### Chat Model Extensions

**New Fields:**
- `interview_type` (CharField): PRACTICE or INVITED
- `scheduled_end_at` (DateTimeField): For invited interviews

**Purpose:**
- Distinguish invited interviews from practice
- Enable time-based auto-completion
- Link back to invitation via OneToOne

---

## Technical Implementation

### Forms

**InvitationCreationForm:**
- File: `active_interview_app/forms.py`
- Fields: `candidate_email`, `template`, `scheduled_date`, `scheduled_time`, `duration_minutes`
- Custom field: `scheduled_datetime` (combines date + time)
- Validation:
  - Template must be complete with questions
  - Scheduled time must be in future
  - Duration between 15-300 minutes
- Timezone conversion: Local → UTC

### Views

**Key Views:**

1. `invitation_create` - Create and send invitation
   - URL: `/invitations/create/` or `/invitations/create/<template_id>/`
   - Permission: `@admin_or_interviewer_required`
   - Sends email with calendar attachment

2. `invitation_dashboard` - List all invitations
   - URL: `/invitations/`
   - Permission: `@admin_or_interviewer_required`
   - Filter by status, search by email

3. `invitation_review` - Review completed interview
   - URL: `/invitations/<invitation_id>/review/`
   - Permission: Must be invitation creator
   - View transcript and provide feedback

4. `invitation_join` - Candidate join flow
   - URL: `/interview/invite/<invitation_id>/`
   - Verifies email, redirects to detail or registration

5. `invited_interview_detail` - Interview detail page
   - URL: `/interview/invited/<invitation_id>/`
   - Permission: Must be invited candidate
   - Shows status, countdown, start button

6. `start_invited_interview` - Start the interview
   - URL: `/interview/invited/<invitation_id>/start/`
   - Permission: Must be invited candidate
   - Creates Chat with system prompt
   - Sets scheduled_end_at for auto-completion

7. `candidate_invitations` - My invitations page
   - URL: `/my-invitations/`
   - Permission: `@login_required`
   - Lists all invitations for logged-in user

**See:** `active_interview_app/views.py`

### Email Utilities

**File:** `active_interview_app/invitation_utils.py`

**Functions:**

- `send_invitation_email(invitation)`: Sends invitation with calendar
- `create_calendar_event(invitation)`: Generates .ics file
- `send_interview_completed_email(invitation)`: Notifies interviewer
- `send_review_notification_email(invitation)`: Notifies candidate

**Email Backend:**
- Production: SMTP (Gmail configured)
- Development: Console backend (prints to terminal)
- Configuration: `settings.py`

### Templates

**Invitation Management:**
- `invitations/invitation_create.html` - Create invitation form
- `invitations/invitation_dashboard.html` - List invitations
- `invitations/invitation_confirmation.html` - Confirmation page
- `invitations/invitation_review.html` - Review interview

**Candidate Flow:**
- `invitations/invited_interview_detail.html` - Interview detail
- `invitations/candidate_invitations.html` - My invitations

**Email Templates:**
- `emails/invitation_sent.html` - Invitation email
- `emails/interview_completed.html` - Completion notification
- `emails/interview_reviewed.html` - Review notification

### JavaScript Features

**Countdown Timers:**
- Live countdown until scheduled time
- Live countdown for time remaining to start
- Auto-refresh when timers expire

**Timezone Conversion:**
- Converts UTC to user's local timezone
- Uses JavaScript `Date.toLocaleString()`
- Updates `[data-utc-time]` elements on page load

**Time Enforcement:**
- Disables input when time expires
- Shows expiration warning
- Reloads page to show completion status

**See:** `invitations/invited_interview_detail.html`, `chat/chat-view.html`

---

## URL Patterns

### Interviewer URLs

```
GET  /invitations/                                    - invitation_dashboard
GET  /invitations/create/                            - invitation_create
POST /invitations/create/                            - invitation_create
GET  /invitations/create/<template_id>/              - invitation_create_from_template
POST /invitations/create/<template_id>/              - invitation_create_from_template
GET  /invitations/<invitation_id>/confirmation/      - invitation_confirmation
GET  /invitations/<invitation_id>/review/            - invitation_review
POST /invitations/<invitation_id>/review/            - invitation_review
```

### Candidate URLs

```
GET  /interview/invite/<invitation_id>/              - invitation_join
GET  /interview/invited/<invitation_id>/             - invited_interview_detail
POST /interview/invited/<invitation_id>/start/       - start_invited_interview
GET  /my-invitations/                                - candidate_invitations
```

### Chat URLs (Time-Gated)

```
GET  /chat/<chat_id>/                                - chat-view (with time banner)
POST /chat/<chat_id>/                                - chat-view (403 if expired)
GET  /chat/<chat_id>/results/                        - chat-results (with feedback)
```

---

## Permissions & Access Control

### Role-Based Access

**Interviewers (role='interviewer' or 'admin'):**
- Create invitations
- View invitation dashboard
- Review completed interviews
- See all invitations they created

**Candidates (any authenticated user):**
- Join invited interviews via link
- View their invitation details
- Start interviews within window
- View results and feedback
- See all invitations sent to their email

### Email Verification

**Join Flow:**
- Must log in or register
- Logged-in user's email must match invited email (case-insensitive)
- If mismatch: Error message, cannot access
- If match: Redirected to interview detail

### Ownership Checks

**Invitation Review:**
- Only invitation creator can review
- Enforced by checking `invitation.interviewer == request.user`

**Interview Access:**
- Only invited candidate can access
- Enforced by checking `invitation.candidate_email == request.user.email`

**Chat Access:**
- Only chat owner can access
- Existing permission system applies

---

## Status Flow Diagram

```
INVITATION CREATED
        ↓
    [PENDING]
        ↓
Candidate Clicks Link → Email Verified → Detail Page
        ↓
Within Window? → Start Interview
        ↓
  [IN_PROGRESS]
        ↓
Time Expires or Candidate Finishes
        ↓
   [COMPLETED]
        ↓
Interviewer Reviews → Provides Feedback
        ↓
Review Status: [REVIEW_COMPLETE]
        ↓
Email Sent to Candidate
```

**Status Transitions:**
1. `PENDING` → `IN_PROGRESS`: When candidate starts interview
2. `IN_PROGRESS` → `COMPLETED`: When time expires or interview ends
3. Review status `PENDING` → `REVIEW_COMPLETE`: When interviewer marks as reviewed

---

## Testing

### Test Files

**Invitation Creation & Management:**
- `test_invitations.py`: Core invitation CRUD operations, form validation, status tracking

**Candidate Join Flow:**
- `test_candidate_join_flow.py`: Join links, email verification, detail page, starting interviews

**Duration Enforcement:**
- `test_duration_enforcement.py`: Time window checks, auto-completion, time expiration

**Email Notifications:**
- `test_invitation_emails.py`: Email sending, calendar attachments, notification triggers

**Interviewer Review:**
- `test_interviewer_review.py`: Review access, feedback submission, status updates, email notifications

**Navigation & UI:**
- `test_phase6_navigation_ui.py`: UI elements, navigation links, invitation dashboard

**PDF with Feedback:**
- `test_invited_interview_pdf.py`: PDF generation with interviewer feedback section

**Test Sequences (Research/logs/):**
- `test_sequence_20251114_210117_invitation_workflow.md`
- `test_sequence_20251115_140045_phase3_email_calendar.md`
- `test_sequence_20251115_140939_phase4_candidate_join_flow.md`
- `test_sequence_20251115_141855_phase5_duration_enforcement.md`
- `test_sequence_20251115_phase6_navigation_ui.md`
- `test_sequence_20251115_phase7_interviewer_review.md`
- `test_sequence_20251115_phase8_pdf_interviewer_feedback.md`

### Coverage

**Test Count:** 100+ tests across all phases

**Coverage Areas:**
- Model creation and validation
- Form validation and timezone handling
- View permissions and access control
- Email sending and calendar generation
- Time window enforcement
- Status transitions
- UI rendering and navigation
- Edge cases and error handling

### Running Tests

```bash
# All invitation tests
pytest active_interview_backend/active_interview_app/tests/test_invitations.py

# Specific test file
pytest active_interview_backend/active_interview_app/tests/test_candidate_join_flow.py

# All tests
pytest active_interview_backend/active_interview_app/tests/
```

---

## Seed Data

For testing and development, seed data is available:

**File:** `active_interview_backend/active_interview_app/fixtures/seed_data.json`

**Includes:**
- Sample users (interviewers and candidates)
- Interview templates with questions
- Pending, in-progress, and completed invitations
- Sample chat sessions

**Load Seed Data:**

```bash
python active_interview_backend/load_seed_data.py
```

**See:** `active_interview_backend/SEED_DATA_QUICKSTART.md`

---

## Use Cases

### For Interviewers

- **Structured Assessments:** Send formal interview invitations with templates
- **Time Management:** Control when candidates can start and how long they have
- **Centralized Tracking:** View all invitations in one dashboard
- **Candidate Review:** Provide detailed feedback on completed interviews
- **Email Notifications:** Automatically notified when candidates complete

### For Candidates

- **Professional Experience:** Receive formal invitations with calendar integration
- **Flexible Scheduling:** Start within a time window at their convenience
- **Clear Expectations:** Know exactly how long they have to complete
- **Feedback Loop:** Receive interviewer feedback after completion
- **Interview History:** Track all invitations in My Invitations page

### For Organizations

- **Standardized Process:** Consistent interview experience across candidates
- **Scalability:** Send multiple invitations efficiently
- **Quality Control:** Interviewers review before candidates see feedback
- **Documentation:** Full audit trail of invitations and completions
- **Integration:** Calendar invites work with existing scheduling tools

---

## Configuration

### Email Settings

**Environment Variables (.env):**

```env
# Email configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@activeinterviewservice.me

# Site URL (for email links)
SITE_URL=https://app.activeinterviewservice.me  # Production
SITE_URL=http://localhost:8000  # Development
```

**Settings (settings.py):**

- Production: Uses SMTP backend with Gmail
- Development: Uses console backend (prints to terminal)
- Configuration auto-switches based on `PROD` environment variable

### Time Window Defaults

**Default Duration:** 60 minutes

**Allowed Range:**
- Minimum: 15 minutes
- Maximum: 300 minutes (5 hours)

**Customization:**
- Set in `InvitationCreationForm.duration_minutes` field
- Can be changed per-invitation

---

## Limitations

### Current Limitations

1. **Email-Only Invitations:** No in-app notification system
2. **Single Window:** Cannot reschedule after creation
3. **No Extensions:** Cannot extend time if candidate needs more
4. **One Attempt:** Cannot restart once started
5. **Email Dependency:** Requires working email configuration
6. **Template Lock:** Cannot change template after invitation sent
7. **No Bulk Actions:** Must review interviews individually

### Future Enhancements

**Planned:**
- Invitation editing/rescheduling
- Bulk invitation creation (CSV upload)
- In-app notifications
- SMS notifications option
- Time extension requests
- Interview reattempts
- Automated reminders (24h before, 1h before)
- Interview analytics dashboard
- Candidate performance comparison
- Export invitation data (CSV, Excel)
- Custom email templates
- Webhook integration for external systems

---

## Troubleshooting

### Common Issues

**Email Not Sending:**
- Check `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env`
- Verify Gmail app password (not regular password)
- Check spam folder
- Review console output for errors
- In development: Emails print to console

**Timezone Issues:**
- Ensure browser timezone detection is enabled
- Check `TIME_ZONE = 'UTC'` in settings.py
- Verify JavaScript is enabled for timezone conversion
- Times display in user's local timezone via JavaScript

**Cannot Start Interview:**
- Check if current time is within window
- Verify invitation status is PENDING
- Ensure logged-in email matches invited email
- Check if window has expired

**Template Not Available:**
- Ensure template status is 'COMPLETE'
- Verify template has at least one question
- Check template hasn't been deleted

**Calendar Attachment Not Working:**
- Verify `.ics` file is being generated
- Check email client supports calendar attachments
- Try importing file manually

---

## Related Documentation

- **[Models Documentation](../architecture/models.md)** - InvitedInterview model details
- **[Question Banks](question-banks.md)** - Creating interview templates
- **[Exportable Reports](exportable-reports.md)** - Generating PDF reports
- **[RBAC](rbac.md)** - Role-based access control
- **[Testing Guide](../setup/testing.md)** - How to test this feature
- **[Architecture Overview](../architecture/overview.md)** - System integration

---

## Support

For issues or questions about the Interview Invitation feature:

1. Check this documentation
2. Review the [Troubleshooting Guide](../setup/troubleshooting.md)
3. Check test sequence logs in `Research/logs/`
4. Create a GitHub issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs or screenshots
   - Environment (local/production)

---

## Feature Metrics

**Implementation Stats:**
- **Models:** 1 new model (InvitedInterview), 2 extended models (Chat)
- **Views:** 7 new views
- **Templates:** 7 new templates
- **Tests:** 100+ tests across 7 test files
- **Email Templates:** 3 email notification types
- **Lines of Code:** ~2,000+ across all components
- **Development Time:** 8 implementation phases
- **Issues Addressed:** #4, #5, #8, #9, #134, #135, #136, #138, #139

**Related Issues:**
- #4: Interview Invitation Workflow
- #5: Create Interview Invitation
- #8: Email Notifications
- #9: Calendar Integration
- #134: Invitation Dashboard
- #135: Candidate Join Flow
- #136: Time-Gated Access
- #138: Duration Enforcement
- #139: Interviewer Review
