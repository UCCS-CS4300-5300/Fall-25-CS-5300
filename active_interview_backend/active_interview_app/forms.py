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
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control',
                                             'rows': 15}),
        }


class JobPostingEditForm(forms.ModelForm):
    title = forms.CharField(required=True)
    content = forms.CharField(required=True, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 15}))

    class Meta:
        model = UploadedJobListing
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
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


# Defines a Django form for handling file uploads.
class UploadFileForm(ModelForm):

    class Meta:
        model = UploadedResume
        fields = ["file", "title"]

    def clean_file(self):
        # allowed_types = ['txt', 'pdf', 'jpg', 'png']
        uploaded_file = self.cleaned_data.get("file")
        return uploaded_file
