from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
import uuid


# Create your models here.

# Seniority level constants (Issues #21, #51, #52, #53)
SENIORITY_ENTRY = 'entry'
SENIORITY_MID = 'mid'
SENIORITY_SENIOR = 'senior'
SENIORITY_LEAD = 'lead'
SENIORITY_EXECUTIVE = 'executive'

SENIORITY_CHOICES = [
    (SENIORITY_ENTRY, 'Entry Level'),
    (SENIORITY_MID, 'Mid Level'),
    (SENIORITY_SENIOR, 'Senior'),
    (SENIORITY_LEAD, 'Lead/Principal'),
    (SENIORITY_EXECUTIVE, 'Executive'),
]


class UserProfile(models.Model):
    """
    Extended user profile to track authentication provider and user role.
    Created automatically when a User is created via signal.

    Related to Issue #69 (RBAC) and OAuth implementation.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )

    # Authentication provider (for OAuth compatibility)
    auth_provider = models.CharField(
        max_length=50,
        default='local',
        help_text='Authentication provider (e.g., local, google)'
    )

    # Role-based access control (Issue #69)
    ADMIN = 'admin'
    INTERVIEWER = 'interviewer'
    CANDIDATE = 'candidate'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (INTERVIEWER, 'Interviewer'),
        (CANDIDATE, 'Candidate'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=CANDIDATE,
        help_text='User role for access control'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role} ({self.auth_provider})"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a new User is created."""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class UploadedResume(models.Model):  # Renamed from UploadedFile
    # Will be saved under media/uploads/
    file = models.FileField(upload_to='uploads/')
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filesize = models.IntegerField(null=True, blank=True)
    original_filename = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255)

    # NEW: Parsed data fields (Issues #48, #49, #50)
    skills = models.JSONField(default=list, blank=True)
    # Structure: ["Python", "Django", "React", ...]

    experience = models.JSONField(default=list, blank=True)
    # Structure: [{"company": "...", "title": "...", "duration": "...",
    # "description": "..."}, ...]

    education = models.JSONField(default=list, blank=True)
    # Structure: [{"institution": "...", "degree": "...", "field": "...",
    # "year": "..."}, ...]

    # NEW: Parsing metadata
    parsing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('success', 'Success'),
            ('error', 'Error'),
        ],
        default='pending'
    )
    parsing_error = models.TextField(blank=True, null=True)
    parsed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        # return f'{self.file.name} uploaded by {self.user}'
        return self.title


# need title for the job listing
class UploadedJobListing(models.Model):  # Renamed from PastedText
    file = models.FileField(upload_to='uploads/')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    filepath = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)

    # NEW: Parsed data fields (Issues #21, #51, #52, #53)
    required_skills = models.JSONField(
        default=list,
        blank=True,
        help_text='List of required skills extracted from job description'
    )
    # Structure: ["Python", "Django", "5+ years experience", "Team leadership"]

    seniority_level = models.CharField(
        max_length=50,
        blank=True,
        choices=SENIORITY_CHOICES,
        help_text='Inferred seniority level from job description'
    )

    requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text='Structured requirements extracted from job description'
    )
    # Structure: {
    #     "education": ["Bachelor's in CS", "..."],
    #     "years_experience": "5+",
    #     "certifications": ["AWS", "..."],
    #     "responsibilities": ["...", "..."]
    # }

    # NEW: Template association (Issue #53)
    recommended_template = models.ForeignKey(
        'InterviewTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_listings',
        help_text=(
            'Auto-recommended interview template based on job requirements'
        )
    )

    # NEW: Parsing metadata (same pattern as UploadedResume)
    parsing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('success', 'Success'),
            ('error', 'Error'),
        ],
        default='pending',
        help_text='Status of AI parsing for this job listing'
    )
    parsing_error = models.TextField(
        blank=True,
        null=True,
        help_text='Error message if parsing failed'
    )
    parsed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when job description was successfully parsed'
    )

    def __str__(self):
        # return self.filename
        return self.title


class Chat(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    difficulty = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    # Json of the messages object
    messages = models.JSONField(blank=True, default=list)
    # Json of the key questions
    key_questions = models.JSONField(blank=True, default=list)
    job_listing = models.ForeignKey(
        UploadedJobListing, null=True, blank=True, on_delete=models.SET_NULL
    )
    resume = models.ForeignKey(UploadedResume, null=True, blank=True,
                               on_delete=models.SET_NULL)

    # interview type
    GENERAL = "GEN"
    SKILLS = "ISK"
    PERSONALITY = "PER"
    FINAL_SCREENING = "FSC"
    INTERVIEW_TYPES = [
        (GENERAL, "General"),
        (SKILLS, "Industry Skills"),
        (PERSONALITY, "Personality/Preliminary"),
        (FINAL_SCREENING, "Final Screening"),
    ]
    type = models.CharField(max_length=3, choices=INTERVIEW_TYPES,
                            default=GENERAL)

    # Interview category: practice (self-initiated) or invited (from
    # interviewer). Related to Issue #137 (Interview Categorization)
    PRACTICE = 'PRACTICE'
    INVITED = 'INVITED'
    INTERVIEW_CATEGORY_CHOICES = [
        (PRACTICE, 'Practice Interview'),
        (INVITED, 'Invited Interview'),
    ]
    interview_type = models.CharField(
        max_length=10,
        choices=INTERVIEW_CATEGORY_CHOICES,
        default=PRACTICE,
        help_text='Whether this is a practice or invited interview'
    )

    # Time tracking for invited interviews (Issue #138)
    # For invited interviews, track when the interview session started
    # and when it should end based on duration limits
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Time when the interview session started'
    )
    scheduled_end_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Scheduled time when interview should end'
    )

    # Finalization tracking (Report Generation Refactor)
    is_finalized = models.BooleanField(
        default=False,
        help_text='Whether the interview has been finalized and report generated'
    )
    finalized_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the interview was finalized'
    )

    # Graceful ending tracking for invited interviews
    last_question_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the last question was asked (for graceful ending calculation)'
    )

    # create object itself, not the field
    # all templates for documents in /documents/
    # thing that returns all user files is at views

    modified_date = models.DateTimeField(auto_now=True)  # date last modified

    def is_time_expired(self):
        """
        Check if the interview time has expired.
        Only applicable for invited interviews with scheduled end times.
        """
        if self.interview_type == self.INVITED and self.scheduled_end_at:
            return timezone.now() > self.scheduled_end_at
        return False

    def time_remaining(self):
        """
        Get the time remaining for this interview.
        Returns None if not applicable or already expired.
        """
        if self.interview_type == self.INVITED and self.scheduled_end_at:
            now = timezone.now()
            if now < self.scheduled_end_at:
                return self.scheduled_end_at - now
        return None

    def all_questions_answered(self):
        """
        Check if all key questions have been answered by the candidate.

        Logic:
        - Count user messages in self.messages (excluding first system message)
        - Compare to len(self.key_questions)
        - Return True if user has answered all questions

        Related to Phase 8: Auto-finalize on Last Question Answered
        """
        if not self.key_questions:
            # No key questions generated yet
            return False

        # Count user messages (role == "user")
        user_message_count = sum(1 for msg in self.messages if msg.get('role') == 'user')

        # User should have answered all key questions
        return user_message_count >= len(self.key_questions)

    def __str__(self):
        return self.title


class ExportableReport(models.Model):
    """
    Data structure to store exportable report information for an interview.
    This model captures all the necessary data for generating PDF or other
    format exports of interview results.
    """
    chat = models.OneToOneField(Chat, on_delete=models.CASCADE,
                                related_name='exportable_report')

    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    # Interview Scores (0-100)
    professionalism_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    subject_knowledge_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    clarity_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    overall_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # AI-generated feedback
    feedback_text = models.TextField(blank=True)

    # Scoring rationales (explanations for each score component)
    professionalism_rationale = models.TextField(blank=True)
    subject_knowledge_rationale = models.TextField(blank=True)
    clarity_rationale = models.TextField(blank=True)
    overall_rationale = models.TextField(blank=True)

    # Score weights (percentages that sum to 100)
    professionalism_weight = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    subject_knowledge_weight = models.IntegerField(
        default=40,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    clarity_weight = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Question-by-question analysis
    question_responses = models.JSONField(default=list)
    # Structure: [{"question": str, "answer": str, "score": int,
    # "feedback": str}, ...]

    # Summary statistics
    total_questions_asked = models.IntegerField(default=0)
    total_responses_given = models.IntegerField(default=0)
    interview_duration_minutes = models.IntegerField(null=True, blank=True)

    # Export tracking
    pdf_generated = models.BooleanField(default=False)
    pdf_file = models.FileField(
        upload_to='exports/pdfs/', null=True, blank=True
    )

    def __str__(self):
        return (
            f"Report for {self.chat.title} - "
            f"{self.generated_at.strftime('%Y-%m-%d')}"
        )

    class Meta:
        ordering = ['-generated_at']


class InterviewTemplate(models.Model):
    """
    Comprehensive interview templates created by interviewers.
    Combines structured sections with question bank integration.

    Templates can include:
    - Manual sections with custom content and weighting
    - Auto-assembly configuration for question banks
    - Tag-based question selection
    - Difficulty distribution settings
    """
    name = models.CharField(
        max_length=255,
        help_text=(
            'Name of the interview template (e.g., "Technical Interview")'
        )
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='interview_templates',
        help_text='User who created this template'
    )
    description = models.TextField(
        blank=True,
        help_text='Optional description of the template purpose'
    )

    # Template sections - allows owners to add/delete sections
    sections = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            'List of sections in the template. Each section has: title, '
            'content, order, weight'
        )
    )
    # Structure: [{"id": "uuid", "title": "...", "content": "...",
    # "order": 0, "weight": 0}, ...]

    # Question Bank Integration fields
    question_banks = models.ManyToManyField(
        'QuestionBank',
        blank=True,
        related_name='templates',
        help_text='Question banks to use for auto-assembly'
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        related_name='templates',
        help_text='Tags to filter questions for auto-assembly'
    )

    # Auto-assembly configuration
    use_auto_assembly = models.BooleanField(
        default=False,
        help_text='Enable automatic interview assembly from question banks'
    )
    question_count = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        help_text='Number of questions for auto-assembly'
    )

    # Difficulty distribution (percentages should sum to 100)
    easy_percentage = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percentage of easy questions'
    )
    medium_percentage = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percentage of medium questions'
    )
    hard_percentage = models.IntegerField(
        default=20,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percentage of hard questions'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = 'Interview Template'
        verbose_name_plural = 'Interview Templates'

    def __str__(self):
        return f"{self.name} (by {self.user.username})"

    def get_total_weight(self):
        """Calculate the total weight of all sections in the template."""
        sections = self.sections if self.sections else []
        return sum(s.get('weight', 0) for s in sections)

    def is_complete(self):
        """Check if the template weight totals 100%."""
        return self.get_total_weight() == 100

    def get_status_display(self):
        """Return 'WIP' if not complete, otherwise return 'Complete'."""
        return "Complete" if self.is_complete() else "WIP"

    def get_difficulty_distribution(self):
        """Return the difficulty distribution as a dict."""
        return {
            'easy': self.easy_percentage,
            'medium': self.medium_percentage,
            'hard': self.hard_percentage
        }

    def validate_difficulty_distribution(self):
        """Check if difficulty percentages sum to 100."""
        total = (
            self.easy_percentage + self.medium_percentage +
            self.hard_percentage
        )
        return total == 100


class InvitedInterview(models.Model):
    """
    Represents an interview invitation sent from an interviewer to a candidate.

    When an interviewer creates an invitation, they select a template,
    specify a candidate email, and set a scheduled time and duration window.
    The candidate receives an email with a unique join link.

    Related to Issues #4, #5, #6, #8, #134-141 (Interview Invitation Workflow).
    """

    # Status choices
    PENDING = 'pending'
    COMPLETED = 'completed'
    REVIEWED = 'reviewed'
    EXPIRED = 'expired'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (REVIEWED, 'Reviewed'),
        (EXPIRED, 'Expired'),
    ]

    # Interviewer review status
    REVIEW_PENDING = 'pending'
    REVIEW_COMPLETED = 'completed'

    REVIEW_STATUS_CHOICES = [
        (REVIEW_PENDING, 'Pending Review'),
        (REVIEW_COMPLETED, 'Review Complete'),
    ]

    # Core fields
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for secure join links'
    )

    interviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        help_text='Interviewer who sent this invitation'
    )

    candidate_email = models.EmailField(
        help_text='Email address of the candidate'
    )

    template = models.ForeignKey(
        InterviewTemplate,
        on_delete=models.CASCADE,
        related_name='invitations',
        help_text='Interview template structure for this invitation'
    )

    # Scheduling fields
    scheduled_time = models.DateTimeField(
        help_text='When the interview can start'
    )

    duration_minutes = models.IntegerField(
        default=60,
        validators=[MinValueValidator(15), MaxValueValidator(240)],
        help_text=(
            'Duration window for completing the interview (15-240 minutes)'
        )
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        help_text='Current status of the invitation'
    )

    interviewer_review_status = models.CharField(
        max_length=20,
        choices=REVIEW_STATUS_CHOICES,
        default=REVIEW_PENDING,
        help_text='Whether interviewer has reviewed the completed interview'
    )

    # Interview session (created when candidate starts interview)
    chat = models.OneToOneField(
        Chat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invitation',
        help_text='The actual interview session (Chat)'
    )

    # Interviewer feedback
    interviewer_feedback = models.TextField(
        blank=True,
        help_text='Feedback provided by the interviewer after review'
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the interviewer marked this as reviewed'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    invitation_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the invitation email was sent'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the candidate completed the interview'
    )
    last_activity_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time candidate interacted with interview (for abandonment detection)'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['interviewer', '-created_at']),
            models.Index(fields=['candidate_email']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_time']),
        ]
        verbose_name = 'Invited Interview'
        verbose_name_plural = 'Invited Interviews'

    def __str__(self):
        return f"{self.template.name} → {self.candidate_email} ({self.status})"

    def get_join_url(self):
        """Generate the full join URL for this invitation."""
        return f"{settings.SITE_URL}/interview/invite/{self.id}/"

    def get_window_end(self):
        """Calculate when the interview window closes."""
        from datetime import timedelta
        return self.scheduled_time + timedelta(minutes=self.duration_minutes)

    def is_accessible(self):
        """
        Check if the interview is currently accessible to the candidate.
        Returns True if current time is within the valid window.
        """
        now = timezone.now()
        window_end = self.get_window_end()

        # If interview already started (has chat), check if it's completed
        if self.chat:
            return self.status != self.COMPLETED

        # Otherwise, check if we're within the time window
        return self.scheduled_time <= now <= window_end

    def is_expired(self):
        """
        Check if the interview window has expired without being started.
        """
        if self.chat:  # Interview was started
            return False

        now = timezone.now()
        window_end = self.get_window_end()
        return now > window_end

    def can_start(self):
        """
        Check if the candidate can start the interview now.
        """
        if self.chat:  # Already started
            return False

        if self.is_expired():
            return False

        now = timezone.now()
        return now >= self.scheduled_time


class RoleChangeRequest(models.Model):
    """
    Track requests from users to change their role.
    Primarily used for candidates requesting interviewer role.

    Related to Issue #69 (RBAC).
    """
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='role_requests'
    )
    requested_role = models.CharField(
        max_length=20,
        help_text='Role being requested (typically "interviewer")'
    )
    current_role = models.CharField(
        max_length=20,
        help_text='Role at time of request'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    reason = models.TextField(
        blank=True,
        help_text='User explanation for role request'
    )

    # Admin review tracking
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_role_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(
        blank=True,
        help_text='Admin notes on approval/rejection'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return (
            f"{self.user.username}: {self.current_role} → "
            f"{self.requested_role} ({self.status})"
        )


class DataExportRequest(models.Model):
    """
    Track user data export requests for GDPR/CCPA compliance.
    Stores the export file and metadata about the request.

    Related to Issue #63, #64 (GDPR/CCPA Data Export).
    """
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    EXPIRED = 'expired'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (EXPIRED, 'Expired'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='data_export_requests',
        help_text='User requesting data export'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        help_text='Current status of the export request'
    )

    # Export file storage
    export_file = models.FileField(
        upload_to='exports/user_data/',
        null=True,
        blank=True,
        help_text='ZIP file containing exported user data'
    )

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Export download link expires after 7 days'
    )

    # Error tracking
    error_message = models.TextField(
        blank=True,
        help_text='Error details if export failed'
    )

    # Export metadata
    file_size_bytes = models.BigIntegerField(
        null=True,
        blank=True,
        help_text='Size of the export file in bytes'
    )

    download_count = models.IntegerField(
        default=0,
        help_text='Number of times the export has been downloaded'
    )

    last_downloaded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last download timestamp'
    )

    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['user', '-requested_at']),
            models.Index(fields=['status', '-requested_at']),
        ]
        verbose_name = 'Data Export Request'
        verbose_name_plural = 'Data Export Requests'

    def __str__(self):
        return (
            f"Export request by {self.user.username} - {self.status} "
            f"({self.requested_at.strftime('%Y-%m-%d %H:%M')})"
        )

    def is_expired(self):
        """Check if the export download link has expired."""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def mark_downloaded(self):
        """Increment download count and update last download timestamp."""
        from django.utils import timezone
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save()


class DeletionRequest(models.Model):
    """
    Audit trail for account deletion requests.
    Stores anonymized user identifier and deletion timestamp for legal
    compliance.

    Related to Issue #63, #65 (GDPR/CCPA Data Deletion).
    """
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]

    # Anonymized user identifier (stored before deletion)
    anonymized_user_id = models.CharField(
        max_length=255,
        help_text='Anonymized identifier for audit purposes'
    )

    username = models.CharField(
        max_length=150,
        help_text='Username at time of deletion (for audit trail)'
    )

    email = models.EmailField(
        blank=True,
        help_text='Email at time of deletion (for audit trail)'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Deletion metadata
    error_message = models.TextField(
        blank=True,
        help_text='Error details if deletion failed'
    )

    # Statistics (anonymized counts for analytics)
    total_interviews_deleted = models.IntegerField(
        default=0,
        help_text='Number of interviews anonymized'
    )
    total_resumes_deleted = models.IntegerField(
        default=0,
        help_text='Number of resumes deleted'
    )
    total_job_listings_deleted = models.IntegerField(
        default=0,
        help_text='Number of job listings deleted'
    )

    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['status', '-requested_at']),
            models.Index(fields=['requested_at']),
        ]
        verbose_name = 'Deletion Request'
        verbose_name_plural = 'Deletion Requests'

    def __str__(self):
        return (
            f"Deletion: {self.anonymized_user_id} - {self.status} "
            f"({self.requested_at.strftime('%Y-%m-%d %H:%M')})"
        )


class AuditLog(models.Model):
    """
    Immutable audit log for security and compliance tracking.
    Records user and admin actions with full context (who/what/when/where).

    Related to Issues #66, #67, #68 (Audit Logging).
    """

    # Action type constants (initial set for Phase 1)
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    LOGIN_FAILED = 'LOGIN_FAILED'
    ADMIN_CREATE = 'ADMIN_CREATE'
    ADMIN_UPDATE = 'ADMIN_UPDATE'
    ADMIN_DELETE = 'ADMIN_DELETE'

    # Extended action types (Phase 3)
    INTERVIEW_FINALIZED = 'INTERVIEW_FINALIZED'
    REPORT_EXPORTED = 'REPORT_EXPORTED'
    RESUME_DELETED = 'RESUME_DELETED'
    ROLE_CHANGED = 'ROLE_CHANGED'
    RATE_LIMIT_VIOLATION = 'RATE_LIMIT_VIOLATION'

    ACTION_TYPES = [
        # Authentication events
        (LOGIN, 'User Login'),
        (LOGOUT, 'User Logout'),
        (LOGIN_FAILED, 'Failed Login Attempt'),

        # Admin actions
        (ADMIN_CREATE, 'Admin Created Object'),
        (ADMIN_UPDATE, 'Admin Updated Object'),
        (ADMIN_DELETE, 'Admin Deleted Object'),

        # Interview events
        (INTERVIEW_FINALIZED, 'Interview Finalized'),

        # Report events
        (REPORT_EXPORTED, 'Report Exported'),

        # Resume events
        (RESUME_DELETED, 'Resume Deleted'),

        # User management events
        (ROLE_CHANGED, 'User Role Changed'),

        # Security events
        (RATE_LIMIT_VIOLATION, 'Rate Limit Violation'),
    ]

    # Core fields
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='When the action occurred'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='User who performed the action (null for anonymous)'
    )

    # Action details
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        db_index=True,
        help_text='Type of action performed'
    )
    resource_type = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text='Type of resource affected (e.g., "User", "Chat")'
    )
    resource_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='ID of the affected resource'
    )
    description = models.TextField(
        help_text='Human-readable description of the action'
    )

    # Request context
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        db_index=True,
        help_text='IP address of the request'
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text='Browser/client user agent string'
    )

    # Additional metadata
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional action-specific metadata'
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'user']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return (
            f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{user_str}: {self.get_action_type_display()}"
        )

    def save(self, *args, **kwargs):
        """
        Enforce immutability: only allow creation, not updates.
        """
        if self.pk is not None:
            raise ValueError(
                "AuditLog entries are immutable and cannot be updated"
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Prevent deletion of audit logs for compliance.
        Only superusers should be able to delete via admin if absolutely
        necessary.
        """
        raise ValueError(
            "AuditLog entries cannot be deleted for compliance reasons"
        )


class Tag(models.Model):
    """
    Tags for categorizing questions (e.g., #python, #sql, #behavioral).
    Tag names are automatically normalized to lowercase with # prefix.
    """
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Normalize tag: lowercase and ensure # prefix
        if self.name and not self.name.startswith('#'):
            self.name = f"#{self.name.lower()}"
        else:
            self.name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class QuestionBank(models.Model):
    """
    A collection of questions that can be tagged and used for interview
    assembly.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='question_banks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-updated_at']


class Question(models.Model):
    """
    Individual question within a question bank.
    Questions can be tagged for categorization and filtering.
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    question_bank = models.ForeignKey(
        QuestionBank, on_delete=models.CASCADE, related_name='questions'
    )
    text = models.TextField()
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default='medium'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='questions')
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='questions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text[:100]

    class Meta:
        ordering = ['-created_at']


class BiasTermLibrary(models.Model):
    """
    Library of bias terms for detecting discriminatory language in feedback.

    Each entry represents a potentially biased term or phrase with:
    - Pattern matching rules (regex)
    - Category classification
    - Explanation of why it's problematic
    - Neutral alternative suggestions
    - Severity level (warning vs. blocking)

    Related to Issues #18, #57, #58, #59 (Bias Guardrails).
    """

    # Bias categories
    AGE = 'age'
    GENDER = 'gender'
    RACE = 'race'
    DISABILITY = 'disability'
    APPEARANCE = 'appearance'
    FAMILY = 'family'
    OTHER = 'other'

    CATEGORY_CHOICES = [
        (AGE, 'Age-related'),
        (GENDER, 'Gender-related'),
        (RACE, 'Race/Ethnicity'),
        (DISABILITY, 'Disability'),
        (APPEARANCE, 'Physical Appearance'),
        (FAMILY, 'Family Status'),
        (OTHER, 'Other Bias'),
    ]

    # Severity levels
    WARNING = 1  # Shows warning but allows saving
    BLOCKING = 2  # Prevents saving until resolved

    SEVERITY_CHOICES = [
        (WARNING, 'Warning'),
        (BLOCKING, 'Blocking'),
    ]

    # Core fields
    term = models.CharField(
        max_length=100,
        help_text='The biased term or phrase (e.g., "cultural fit")'
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text='Category of bias this term represents'
    )

    pattern = models.CharField(
        max_length=500,
        help_text=(
            'Regex pattern for detecting this term and its variations. '
            'Example: \\b(cultural fit|culture fit)\\b'
        )
    )

    explanation = models.TextField(
        help_text=(
            'Explanation of why this term is problematic. '
            'Shown in tooltip to educate users.'
        )
    )

    neutral_alternatives = models.JSONField(
        default=list,
        help_text=(
            'List of neutral alternative phrasings. '
            'Example: ["team collaboration skills", "alignment with company values"]'
        )
    )

    severity = models.IntegerField(
        choices=SEVERITY_CHOICES,
        default=WARNING,
        help_text=(
            'Severity level: WARNING (1) shows warning but allows save, '
            'BLOCKING (2) prevents save until resolved'
        )
    )

    is_active = models.BooleanField(
        default=True,
        help_text='Whether this term is actively checked during bias detection'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_bias_terms',
        help_text='Admin who added this term'
    )

    # Usage statistics
    detection_count = models.IntegerField(
        default=0,
        help_text='Number of times this term has been detected in feedback'
    )

    def __str__(self):
        return f"{self.term} ({self.get_category_display()})"

    class Meta:
        verbose_name = 'Bias Term'
        verbose_name_plural = 'Bias Term Library'
        ordering = ['category', 'term']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', 'severity']),
        ]


class BiasAnalysisResult(models.Model):
    """
    Stores the result of bias detection analysis for a specific feedback text.

    This model captures:
    - Which bias terms were detected
    - Overall bias score/severity
    - Detailed analysis results
    - Whether the feedback was saved with warnings

    Related to Issues #18, #57, #58, #59 (Bias Guardrails).
    """

    # Link to feedback source (polymorphic - can be InvitedInterview or ExportableReport)
    # We'll use GenericForeignKey for flexibility
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text='Type of model this analysis is for (InvitedInterview or ExportableReport)'
    )
    object_id = models.CharField(
        max_length=255,
        help_text='ID of the specific object (supports both integer IDs and UUIDs)'
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    # Analysis results
    flagged_terms = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            'List of detected bias terms with details. '
            'Structure: [{"term": str, "category": str, "severity": int, '
            '"positions": [int], "suggestions": [str]}, ...]'
        )
    )

    bias_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text='Overall bias probability score (0.0 = clean, 1.0 = highly biased)'
    )

    severity_level = models.CharField(
        max_length=10,
        choices=[
            ('CLEAN', 'Clean'),
            ('LOW', 'Low'),
            ('MEDIUM', 'Medium'),
            ('HIGH', 'High'),
        ],
        default='CLEAN',
        help_text='Overall severity assessment'
    )

    total_flags = models.IntegerField(
        default=0,
        help_text='Total number of bias flags detected'
    )

    blocking_flags = models.IntegerField(
        default=0,
        help_text='Number of blocking-severity flags (prevent save)'
    )

    warning_flags = models.IntegerField(
        default=0,
        help_text='Number of warning-severity flags (allow save with acknowledgment)'
    )

    # User interaction
    saved_with_warnings = models.BooleanField(
        default=False,
        help_text='Whether the user chose to save despite warnings'
    )

    user_acknowledged = models.BooleanField(
        default=False,
        help_text='Whether the user acknowledged the bias warnings'
    )

    # Metadata
    analyzed_at = models.DateTimeField(auto_now_add=True)
    feedback_text_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text='Hash of analyzed text (for detecting re-analysis of same content)'
    )

    def __str__(self):
        return (
            f"Bias Analysis: {self.severity_level} "
            f"({self.total_flags} flags) - {self.analyzed_at}"
        )

    class Meta:
        verbose_name = 'Bias Analysis Result'
        verbose_name_plural = 'Bias Analysis Results'
        ordering = ['-analyzed_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['severity_level', 'analyzed_at']),
        ]


# Import token tracking models (must be at end to avoid circular imports)
from .token_usage_models import TokenUsage  # noqa: E402, F401
from .merge_stats_models import MergeTokenStats  # noqa: E402, F401

# Import observability models (Issues #14, #15)
from .observability_models import (  # noqa: E402, F401
    RequestMetric,
    DailyMetricsSummary,
    ProviderCostDaily,
    ErrorLog
)

# Import spending tracker models (Issues #10, #11, #12)
from .spending_tracker_models import (  # noqa: E402, F401
    MonthlySpendingCap,
    MonthlySpending
)


class RateLimitViolation(models.Model):
    """
    Model to log rate limit violations for monitoring and abuse detection.

    Tracks all instances where users exceed rate limits, including:
    - Timestamp of violation
    - User (if authenticated) or IP address
    - Endpoint that was accessed
    - Rate limit that was exceeded

    Used for admin monitoring, abuse detection, and analytics.
    """

    # Violation details
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='When the violation occurred'
    )

    # User information (nullable for anonymous users)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rate_limit_violations',
        help_text='User who violated rate limit (null for anonymous)'
    )

    # IP address (always recorded)
    ip_address = models.GenericIPAddressField(
        db_index=True,
        help_text='IP address of the request'
    )

    # Request details
    endpoint = models.CharField(
        max_length=255,
        db_index=True,
        help_text='URL path that was accessed'
    )

    method = models.CharField(
        max_length=10,
        help_text='HTTP method (GET, POST, etc.)'
    )

    # Rate limit details
    rate_limit_type = models.CharField(
        max_length=20,
        choices=[
            ('default', 'Default'),
            ('strict', 'Strict'),
            ('lenient', 'Lenient'),
        ],
        help_text='Type of rate limit that was exceeded'
    )

    limit_value = models.IntegerField(
        help_text='Rate limit value (requests per minute)'
    )

    # User agent for device tracking
    user_agent = models.TextField(
        blank=True,
        help_text='User agent string from request'
    )

    # Geographic information (optional, can be populated by GeoIP)
    country_code = models.CharField(
        max_length=2,
        blank=True,
        help_text='Country code from IP (if available)'
    )

    # Alert tracking
    alert_sent = models.BooleanField(
        default=False,
        help_text='Whether an alert was sent for this violation'
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'user']),
            models.Index(fields=['-timestamp', 'ip_address']),
            models.Index(fields=['endpoint', '-timestamp']),
        ]
        verbose_name = 'Rate Limit Violation'
        verbose_name_plural = 'Rate Limit Violations'

    def __str__(self):
        user_str = f"User {self.user.username}" if self.user else f"IP {self.ip_address}"
        return f"{user_str} - {self.endpoint} at {self.timestamp}"

    @property
    def is_authenticated_user(self):
        """Check if violation was by an authenticated user."""
        return self.user is not None

    @classmethod
    def get_recent_violations(cls, minutes=5):
        """Get violations from the last N minutes."""
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(minutes=minutes)
        return cls.objects.filter(timestamp__gte=cutoff)

    @classmethod
    def get_top_violators(cls, limit=10, days=7):
        """
        Get top violators in the last N days.

        Returns list of tuples: (identifier, count)
        where identifier is username or IP address.
        """
        from datetime import timedelta
        from django.db.models import Count

        cutoff = timezone.now() - timedelta(days=days)
        violations = cls.objects.filter(timestamp__gte=cutoff)

        # Group by user
        user_violations = violations.filter(user__isnull=False).values(
            'user__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:limit]

        # Group by IP for anonymous
        ip_violations = violations.filter(user__isnull=True).values(
            'ip_address'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:limit]

        # Combine and sort
        results = []
        for v in user_violations:
            results.append((v['user__username'], v['count'], 'user'))
        for v in ip_violations:
            results.append((v['ip_address'], v['count'], 'ip'))

        return sorted(results, key=lambda x: x[1], reverse=True)[:limit]

    @classmethod
    def check_threshold_exceeded(cls, minutes=5, threshold=10):
        """
        Check if violation threshold has been exceeded.

        Args:
            minutes: Time window to check
            threshold: Number of violations to trigger alert

        Returns:
            tuple: (exceeded, count, violators)
        """
        recent = cls.get_recent_violations(minutes)
        count = recent.count()
        exceeded = count >= threshold

        if exceeded:
            # Get unique violators
            violators = set()
            for v in recent:
                if v.user:
                    violators.add(f"User: {v.user.username}")
                else:
                    violators.add(f"IP: {v.ip_address}")

        return (exceeded, count, list(violators) if exceeded else [])


# Import API key rotation models (Issues #10, #13)
from .api_key_rotation_models import (  # noqa: E402, F401
    APIKeyPool,
    KeyRotationSchedule,
    KeyRotationLog
)
