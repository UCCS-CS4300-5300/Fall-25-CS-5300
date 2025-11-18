from django import forms
from django.forms import ModelForm, ModelChoiceField, IntegerField
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Form field constants
TITLE_MAX_LENGTH_SHORT = 48
TITLE_MAX_LENGTH_JOB = 100
TITLE_MAX_LENGTH = 255
TEXTAREA_ROWS_DEFAULT = 15
TEXTAREA_ROWS_SMALL = 4
DIFFICULTY_INITIAL = 5
DIFFICULTY_MIN = 1
DIFFICULTY_MAX = 10
QUESTION_COUNT_INITIAL = 5
QUESTION_COUNT_MIN = 1
PERCENTAGE_MIN = 0
PERCENTAGE_MAX = 100
PERCENTAGE_DEFAULT_EASY = 30
PERCENTAGE_DEFAULT_MEDIUM = 50
PERCENTAGE_DEFAULT_HARD = 20


class CreateUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class DocumentEditForm(forms.ModelForm):
    class Meta:
        model = UploadedResume
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'maxlength': str(TITLE_MAX_LENGTH_SHORT)}),
            'content': forms.Textarea(attrs={'class': 'form-control',
                                             'rows': TEXTAREA_ROWS_DEFAULT}),
        }


class JobPostingEditForm(forms.ModelForm):
    title = forms.CharField(required=True, max_length=TITLE_MAX_LENGTH_JOB)
    content = forms.CharField(required=True, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': TEXTAREA_ROWS_DEFAULT}))

    class Meta:
        model = UploadedJobListing
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'maxlength': str(TITLE_MAX_LENGTH_JOB)}),
        }


class CreateChatForm(ModelForm):
    difficulty = IntegerField(initial=DIFFICULTY_INITIAL, min_value=DIFFICULTY_MIN, max_value=DIFFICULTY_MAX)
    title = forms.CharField(required=False, initial="Interview Chat")

    listing_choice = ModelChoiceField(
                            queryset=UploadedJobListing.objects.none())
    resume_choice = ModelChoiceField(queryset=UploadedResume.objects.none(),
                                     required=False)

    class Meta:
        model = Chat
        fields = ["title", "type"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)  # ensure parent object initialized

        if user is not None:
            self.fields['listing_choice'].queryset = \
                UploadedJobListing.objects.filter(user=user)
            self.fields['resume_choice'].queryset = \
                UploadedResume.objects.filter(user=user)

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            return "Interview Chat"
        return title


class EditChatForm(ModelForm):
    difficulty = IntegerField(min_value=DIFFICULTY_MIN, max_value=DIFFICULTY_MAX, required=False)
    title = forms.CharField(required=False)

    class Meta:
        model = Chat
        fields = ["title"]


class InterviewTemplateForm(ModelForm):
    """
    Form for creating and editing interview templates.
    Supports both section-based templates and question bank integration.
    """
    name = forms.CharField(
        required=True,
        max_length=TITLE_MAX_LENGTH_SHORT,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Technical Interview, Behavioral Interview'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': TEXTAREA_ROWS_SMALL,
            'placeholder': 'Optional: Describe the purpose of this template'
        })
    )

    # Question bank integration fields
    use_auto_assembly = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Enable Auto-Assembly',
        help_text='Automatically generate interview questions from question banks'
    )

    question_banks = forms.ModelMultipleChoiceField(
        queryset=QuestionBank.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': '5'
        }),
        help_text='Select question banks to use for auto-assembly'
    )

    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': '5'
        }),
        help_text='Select tags to filter questions'
    )

    question_count = forms.IntegerField(
        required=False,
        initial=QUESTION_COUNT_INITIAL,
        min_value=QUESTION_COUNT_MIN,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': str(QUESTION_COUNT_MIN)
        }),
        help_text='Number of questions for auto-assembly'
    )

    easy_percentage = forms.IntegerField(
        required=False,
        initial=PERCENTAGE_DEFAULT_EASY,
        min_value=PERCENTAGE_MIN,
        max_value=PERCENTAGE_MAX,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': str(PERCENTAGE_MIN),
            'max': str(PERCENTAGE_MAX)
        }),
        help_text='Percentage of easy questions (0-100)'
    )

    medium_percentage = forms.IntegerField(
        required=False,
        initial=PERCENTAGE_DEFAULT_MEDIUM,
        min_value=PERCENTAGE_MIN,
        max_value=PERCENTAGE_MAX,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': str(PERCENTAGE_MIN),
            'max': str(PERCENTAGE_MAX)
        }),
        help_text='Percentage of medium questions (0-100)'
    )

    hard_percentage = forms.IntegerField(
        required=False,
        initial=PERCENTAGE_DEFAULT_HARD,
        min_value=PERCENTAGE_MIN,
        max_value=PERCENTAGE_MAX,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': str(PERCENTAGE_MIN),
            'max': str(PERCENTAGE_MAX)
        }),
        help_text='Percentage of hard questions (0-100)'
    )

    class Meta:
        model = InterviewTemplate
        fields = [
            'name', 'description', 'use_auto_assembly',
            'question_banks', 'tags', 'question_count',
            'easy_percentage', 'medium_percentage', 'hard_percentage'
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user is not None:
            # Filter question banks to show only those owned by the user
            self.fields['question_banks'].queryset = QuestionBank.objects.filter(owner=user)

    def clean(self):
        cleaned_data = super().clean()
        use_auto_assembly = cleaned_data.get('use_auto_assembly')

        # Validate difficulty percentages sum to 100 if auto-assembly is enabled
        if use_auto_assembly:
            easy = cleaned_data.get('easy_percentage', 0) or 0
            medium = cleaned_data.get('medium_percentage', 0) or 0
            hard = cleaned_data.get('hard_percentage', 0) or 0

            if easy + medium + hard != 100:
                raise forms.ValidationError(
                    'Difficulty percentages must sum to 100% when auto-assembly is enabled'
                )

        return cleaned_data


# Defines a Django form for handling file uploads.
class UploadFileForm(ModelForm):

    class Meta:
        model = UploadedResume
        fields = ["file", "title"]
        widgets = {
            'title': forms.TextInput(attrs={'maxlength': str(TITLE_MAX_LENGTH_SHORT)}),
        }

    def clean_file(self):
        # allowed_types = ['txt', 'pdf', 'jpg', 'png']
        uploaded_file = self.cleaned_data.get("file")
        return uploaded_file


class InvitationCreationForm(ModelForm):
    """
    Form for creating interview invitations.
    Allows interviewers to invite candidates to take interviews based on templates.

    Related to Issue #5 (Create Interview Invitation).
    """

    template = ModelChoiceField(
        queryset=InterviewTemplate.objects.none(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text='Select the interview template for this invitation'
    )

    candidate_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'candidate@example.com'
        }),
        help_text='Email address of the candidate'
    )

    scheduled_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Date when the interview can be taken (in your local timezone)'
    )

    scheduled_time = forms.TimeField(
        required=True,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        help_text='Time when the interview can be taken (in your local timezone)'
    )

    # Hidden field to capture user's timezone offset
    timezone_offset = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'id_timezone_offset'
        })
    )

    duration_minutes = forms.IntegerField(
        initial=60,
        min_value=15,
        max_value=240,
        widget=forms.Select(
            choices=[
                (30, '30 minutes'),
                (60, '1 hour'),
                (90, '1.5 hours'),
                (120, '2 hours'),
                (180, '3 hours'),
                (240, '4 hours'),
            ],
            attrs={'class': 'form-control'}
        ),
        help_text='Duration window for completing the interview'
    )

    class Meta:
        model = InvitedInterview
        # Note: scheduled_date and scheduled_time are form-only fields, not model fields
        # The model has 'scheduled_time' as a DateTimeField, which the view sets manually
        fields = ['template', 'candidate_email', 'duration_minutes']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        template_id = kwargs.pop('template_id', None)
        super().__init__(*args, **kwargs)

        # Filter templates to only show user's complete templates
        if user is not None:
            # Get all templates for this user
            all_templates = InterviewTemplate.objects.filter(user=user)
            # Filter to only complete templates (weight = 100%)
            complete_templates = [t for t in all_templates if t.is_complete()]
            # Set queryset to only complete templates
            self.fields['template'].queryset = \
                InterviewTemplate.objects.filter(
                    id__in=[t.id for t in complete_templates]
                )

        # Pre-select template if template_id provided (from template detail page)
        if template_id is not None:
            try:
                template = InterviewTemplate.objects.get(id=template_id, user=user)
                # Only set initial if template is complete
                if template.is_complete():
                    self.fields['template'].initial = template
            except InterviewTemplate.DoesNotExist:
                pass

    def clean_scheduled_date(self):
        """Validate that scheduled date is not in the past."""
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date:
            today = timezone.now().date()
            if scheduled_date < today:
                raise forms.ValidationError(
                    'Scheduled date cannot be in the past.'
                )
        return scheduled_date

    def clean(self):
        """Validate that scheduled datetime is in the future."""
        cleaned_data = super().clean()
        scheduled_date = cleaned_data.get('scheduled_date')
        scheduled_time = cleaned_data.get('scheduled_time')
        timezone_offset = cleaned_data.get('timezone_offset')

        if scheduled_date and scheduled_time:
            # Combine date and time
            from datetime import datetime

            # Create naive datetime from user input
            naive_datetime = datetime.combine(scheduled_date, scheduled_time)

            # If we have timezone offset from JavaScript, use it to convert to UTC
            if timezone_offset is not None:
                # timezone_offset from getTimezoneOffset() is in minutes
                # IMPORTANT: getTimezoneOffset() returns POSITIVE for timezones
                # behind UTC (e.g., EST returns +300, not -300)
                # It represents "minutes to ADD to local time to get UTC"
                # So we ADD the offset to convert local time to UTC
                utc_datetime = naive_datetime + timedelta(minutes=timezone_offset)
                scheduled_datetime = timezone.make_aware(utc_datetime)
            else:
                # Fallback: treat as UTC if no timezone info provided
                scheduled_datetime = timezone.make_aware(naive_datetime)

            # Check if in the future with a small buffer
            # Require at least 2 minutes in the future
            now = timezone.now()
            min_time = now + timedelta(minutes=2)

            if scheduled_datetime < min_time:
                # Calculate how far in the past/future for helpful message
                diff_minutes = (scheduled_datetime - now).total_seconds() / 60
                if diff_minutes < 0:
                    raise forms.ValidationError(
                        f'Scheduled time is in the past ({abs(int(diff_minutes))} '
                        f'minutes ago). Please select a future time.'
                    )
                else:
                    raise forms.ValidationError(
                        f'Scheduled time must be at least 2 minutes in the future. '
                        f'Selected time is only {int(diff_minutes)} minute(s) away.'
                    )

            # Store combined datetime for easy access
            cleaned_data['scheduled_datetime'] = scheduled_datetime

        # Validate that template is complete
        template = cleaned_data.get('template')
        if template and not template.is_complete():
            raise forms.ValidationError(
                'Cannot create invitation with incomplete template. '
                'Template must have sections totaling 100% weight.'
            )

        return cleaned_data

    def clean_candidate_email(self):
        """Validate email format."""
        email = self.cleaned_data.get('candidate_email')
        if email:
            email = email.lower().strip()
        return email
