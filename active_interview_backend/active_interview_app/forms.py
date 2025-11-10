from django import forms
from django.forms import ModelForm, ModelChoiceField, IntegerField
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


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
            'title': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '32'}),
            'content': forms.Textarea(attrs={'class': 'form-control',
                                             'rows': 15}),
        }


class JobPostingEditForm(forms.ModelForm):
    title = forms.CharField(required=True, max_length=32)
    content = forms.CharField(required=True, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 15}))

    class Meta:
        model = UploadedJobListing
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '32'}),
        }


class CreateChatForm(ModelForm):
    difficulty = IntegerField(initial=5, min_value=1, max_value=10)
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
    difficulty = IntegerField(min_value=1, max_value=10, required=False)
    title = forms.CharField(required=False)

    class Meta:
        model = Chat
        fields = ["title"]


class InterviewTemplateForm(ModelForm):
    """
    Form for creating and editing interview templates.
    """
    name = forms.CharField(
        required=True,
        max_length=32,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Technical Interview, Behavioral Interview'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Optional: Describe the purpose of this template'
        })
    )

    class Meta:
        model = InterviewTemplate
        fields = ['name', 'description']


# Defines a Django form for handling file uploads.
class UploadFileForm(ModelForm):

    class Meta:
        model = UploadedResume
        fields = ["file", "title"]
        widgets = {
            'title': forms.TextInput(attrs={'maxlength': '32'}),
        }

    def clean_file(self):
        # allowed_types = ['txt', 'pdf', 'jpg', 'png']
        uploaded_file = self.cleaned_data.get("file")
        return uploaded_file
