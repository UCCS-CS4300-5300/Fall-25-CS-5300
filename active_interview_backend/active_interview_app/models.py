from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    # Structure: [{"company": "...", "title": "...", "duration": "...", "description": "..."}, ...]

    education = models.JSONField(default=list, blank=True)
    # Structure: [{"institution": "...", "degree": "...", "field": "...", "year": "..."}, ...]

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
        help_text='Auto-recommended interview template based on job requirements'
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
    difficulty = models.IntegerField(default=5,
                                     validators=[MinValueValidator(1),
                                                 MaxValueValidator(10)])
    messages = models.JSONField(blank=True, default=list)  # Json of the messages object
    key_questions = models.JSONField(blank=True, default=list)  # Json of the key questions
    job_listing = models.ForeignKey(UploadedJobListing, null=True, blank=True,
                                    on_delete=models.SET_NULL)
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

    # create object itself, not the field
    # all templates for documents in /documents/
    # thing that returns all user files is at views

    modified_date = models.DateTimeField(auto_now=True)  # date last modified

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
    # Structure: [{"question": str, "answer": str, "score": int, "feedback": str}, ...]

    # Summary statistics
    total_questions_asked = models.IntegerField(default=0)
    total_responses_given = models.IntegerField(default=0)
    interview_duration_minutes = models.IntegerField(null=True, blank=True)

    # Export tracking
    pdf_generated = models.BooleanField(default=False)
    pdf_file = models.FileField(upload_to='exports/pdfs/', null=True, blank=True)

    def __str__(self):
        return f"Report for {self.chat.title} - {self.generated_at.strftime('%Y-%m-%d')}"

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
        help_text='Name of the interview template (e.g., "Technical Interview")'
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
        help_text='List of sections in the template. Each section has: title, content, order, weight'
    )
    # Structure: [{"id": "uuid", "title": "...", "content": "...", "order": 0, "weight": 0}, ...]

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
        total = self.easy_percentage + self.medium_percentage + self.hard_percentage
        return total == 100


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
            f"Export request by {self.user.username} - "
            f"{self.status} ({self.requested_at.strftime('%Y-%m-%d %H:%M')})"
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
    Stores anonymized user identifier and deletion timestamp for legal compliance.

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
            f"Deletion: {self.anonymized_user_id} - "
            f"{self.status} ({self.requested_at.strftime('%Y-%m-%d %H:%M')})"
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
    A collection of questions that can be tagged and used for interview assembly.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_banks')
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

    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE,
                                     related_name='questions')
    text = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES,
                                 default='medium')
    tags = models.ManyToManyField(Tag, blank=True, related_name='questions')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text[:100]

    class Meta:
        ordering = ['-created_at']


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
