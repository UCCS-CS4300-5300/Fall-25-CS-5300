from django import forms
from django.forms import ModelForm, ModelChoiceField, IntegerField
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# Form field constants
TITLE_MAX_LENGTH_SHORT = 32
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
    title = forms.CharField(required=True, max_length=TITLE_MAX_LENGTH_SHORT)
    content = forms.CharField(required=True, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': TEXTAREA_ROWS_DEFAULT}))

    class Meta:
        model = UploadedJobListing
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'maxlength': str(TITLE_MAX_LENGTH_SHORT)}),
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
        max_length=TITLE_MAX_LENGTH,
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
