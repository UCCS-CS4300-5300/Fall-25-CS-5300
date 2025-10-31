from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User


# Create your models here.


class UploadedResume(models.Model):  # Renamed from UploadedFile
    # Will be saved under media/uploads/
    file = models.FileField(upload_to='uploads/')
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filesize = models.IntegerField(null=True, blank=True)
    original_filename = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255)
    

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
    INTERVIEW_TYPES = {
        (GENERAL, "General"),
        (SKILLS, "Industry Skills"),
        (PERSONALITY, "Personality/Preliminary"),
        (FINAL_SCREENING, "Final Screening"),
    }
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


class InterviewTemplate(models.Model):
    """
    Saved configuration for auto-assembling interviews.
    Stores tag preferences, question counts, and difficulty distribution.
    """
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                            related_name='interview_templates')
    tags = models.ManyToManyField(Tag, related_name='templates')
    question_count = models.IntegerField(default=5,
                                        validators=[MinValueValidator(1)])

    # Difficulty distribution (percentages should sum to 100)
    easy_percentage = models.IntegerField(default=30,
                                         validators=[MinValueValidator(0),
                                                   MaxValueValidator(100)])
    medium_percentage = models.IntegerField(default=50,
                                           validators=[MinValueValidator(0),
                                                     MaxValueValidator(100)])
    hard_percentage = models.IntegerField(default=20,
                                         validators=[MinValueValidator(0),
                                                   MaxValueValidator(100)])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-updated_at']


# Import token tracking models (must be at end to avoid circular imports)
from .token_usage_models import TokenUsage  # noqa: E402, F401
from .merge_stats_models import MergeTokenStats  # noqa: E402, F401
