from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.


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
    Named interview templates created by interviewers.
    Allows interviewers to organize and structure their interviews.

    Templates can be empty initially and later populated with questions,
    criteria, and other interview structure.
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


# Import token tracking models (must be at end to avoid circular imports)
from .token_usage_models import TokenUsage  # noqa: E402, F401
from .merge_stats_models import MergeTokenStats  # noqa: E402, F401
