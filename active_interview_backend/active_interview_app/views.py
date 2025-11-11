import os
import filetype
import json
import pymupdf4llm
import tempfile
import textwrap
import re
from markdownify import markdownify as md
from docx import Document

from .models import (
    UploadedResume, UploadedJobListing, Chat,
    ExportableReport, UserProfile, RoleChangeRequest,
    InterviewTemplate
)
from .forms import (
    CreateUserForm,
    CreateChatForm,
    EditChatForm,
    UploadFileForm,
    DocumentEditForm,
    JobPostingEditForm,
    InterviewTemplateForm
)
from .serializers import (
    UploadedResumeSerializer,
    UploadedJobListingSerializer,
    ExportableReportSerializer
)
from .pdf_export import generate_pdf_report
from .resume_parser import parse_resume_with_ai


from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils import timezone
from django.views import View


from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


# Import OpenAI utilities (moved to separate module to prevent circular imports)
from .openai_utils import get_openai_client, _ai_available, MAX_TOKENS

# Import RBAC decorators (Issue #69)
from .decorators import (
    admin_required,
    admin_or_interviewer_required,
    check_user_permission
)


def _ai_unavailable_json():
    """Return a JSON response for when AI features are disabled."""
    return JsonResponse({'error': 'AI features are disabled on this server.'}, status=503)


# Create your views here.
def index(request):
    return render(request, 'index.html')


def aboutus(request):
    return render(request, 'about-us.html')


# def demo(request):
#     return render(request, os.path.join('demo', 'demo.html'))


def features(request):
    return render(request, 'features.html')


def results(request):
    return render(request, 'results.html')


# @login_required
# def chat_view(request):
#     if request.method == 'GET':
#         chat = Chat.objects.create(
#             owner=request.user,
#             title="New Chat",
#             messages=[
#                 {
#                   "role": "system",
#                   "content": "You are a helpful assistant."
#                 },
#             ]
#         )
#
#         owner_chats = Chat.objects.filter(owner=request.user) \
#               .order_by('-modified_date')
#
#         request.session['chat_id'] = chat.id
#
#         context = {}
#         context['chat'] = chat
#         context['owner_chats'] = owner_chats
#
#         return render(request, os.path.join('chat', 'chat-view.html'),
#                       context)
#
#     elif request.method == 'POST':
#         chat_id = request.session.get('chat_id')
#         chat = Chat.objects.get(id=chat_id)
#
#         user_message = request.POST.get('message', '')
#
#         new_messages = chat.messages
#         new_messages.append({"role": "user", "content": user_message})
#
#         response = get_openai_client().chat.completions.create(
#             model="gpt-4o",
#             messages=new_messages,
#             max_tokens=500
#         )
#         ai_message = response.choices[0].message.content
#         new_messages.append({"role": "assistant", "content": ai_message})
#
#         chat.messages = new_messages
#         chat.save()
#
#         return JsonResponse({'message': ai_message})


@login_required
def chat_list(request):
    owner_chats = Chat.objects.filter(owner=request.user)\
        .order_by('-modified_date')

    context = {}
    context['owner_chats'] = owner_chats

    return render(request, os.path.join('chat', 'chat-list.html'), context)


class CreateChat(LoginRequiredMixin, View):
    def get(self, request):
        owner_chats = Chat.objects.filter(owner=request.user)\
            .order_by('-modified_date')

        form = CreateChatForm(user=request.user)  # Pass user into chatform

        context = {}
        context['owner_chats'] = owner_chats
        context['form'] = form

        return render(request, os.path.join('chat', 'chat-create.html'),
                      context)

    def post(self, request):
        if 'create' in request.POST:
            form = CreateChatForm(request.POST, user=request.user)

            if form.is_valid():
                chat = form.save(commit=False)

                chat.job_listing = form.cleaned_data['listing_choice']
                chat.resume = form.cleaned_data['resume_choice']
                chat.difficulty = form.cleaned_data["difficulty"]
                chat.type = form.cleaned_data["type"]
                chat.owner = request.user

                # Prompts are edited by ChatGPT after being written by a human
                # developer
                # Default message. Should only show up if something went wrong.
                system_prompt = "An error has occurred.  Please notify the " \
                                "user about this."
                if chat.resume:  # if resume is present
                    system_prompt = textwrap.dedent("""\
                        You are a professional interviewer for a company
                        preparing for a candidate's interview. You will act as
                        the interviewer and engage in a roleplaying session
                        with the candidate.

                        Please review the job listing, resume and misc.
                        interview details below:

                        # Type of Interview
                        This interview will be of the following type: {type}

                        # Difficulty
                        - **Scale:** 1 to 10
                        - **1** = extremely easygoing interview, no curveballs
                        - **10** = very challenging, for top‑tier candidates
                          only
                        - **Selected level:** <<{difficulty}>>

                        # Job Listing:
                        \"\"\"{listing}\"\"\"

                        # Candidate Resume:
                        \"\"\"{resume}\"\"\"

                        Ignore any formatting issues in the resume, and focus
                        on its content.
                        Begin the session by greeting the candidate and asking
                        an introductory question about their background, then
                        move on to deeper, role-related questions based on the
                        job listing and resume.

                        Respond critically to any responses that are off-topic
                        or ignore the fact that the user is in an interview.
                        For example, the user may not ask questions that are
                        normally accpetable for AI like recipes or book
                        reviews.
                    """).format(listing=chat.job_listing.content,
                                resume=chat.resume.content,
                                difficulty=chat.difficulty,
                                type=chat.get_type_display())
                else:  # if no resume
                    system_prompt = textwrap.dedent("""\
                        You are a professional interviewer for a company
                        preparing for a candidate's interview. You will act as
                        the interviewer and engage in a roleplaying session
                        with the candidate.

                        Please review the job listing and misc. interview
                        details below:

                        # Type of Interview
                        This interview will be of the following type: {type}

                        # Difficulty
                        - **Scale:** 1 to 10
                        - **1** = extremely easygoing interview, no curveballs
                        - **10** = very challenging, for top‑tier candidates
                          only
                        - **Selected level:** <<{difficulty}>>

                        # Job Listing:
                        \"\"\"{listing}\"\"\"

                        Begin the session by greeting the candidate and asking
                        an introductory question about their background, then
                        move on to role-specific questions based on the job
                        listing.

                        Respond critically to any responses that are off-topic
                        or ignore the fact that the user is in an interview.
                        For example, the user may not ask questions that are
                        normally accpetable for AI like recipes or book
                        reviews.
                    """).format(listing=chat.job_listing.content,
                                difficulty=chat.difficulty,
                                type=chat.get_type_display())

                chat.messages = [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                ]

                # Make ai speak first
                if not _ai_available():
                    messages.error(request, "AI features are disabled on this server.")
                    ai_message = ""
                else:
                    response = get_openai_client().chat.completions.create(
                        model="gpt-4o",
                        messages=chat.messages,
                        max_tokens=MAX_TOKENS
                    )
                    ai_message = response.choices[0].message.content
                chat.messages.append(
                    {
                        "role": "assistant",
                        "content": ai_message
                    }
                )

                # ===== Get AI timed questions =====
                if chat.resume:  # if resume is present
                    system_prompt = textwrap.dedent("""\
                        You are a professional interviewer for a company
                        preparing for a candidate's interview. You will act as
                        the interviewer and engage in a roleplaying session
                        with the candidate.

                        Please review the job listing, resume and misc.
                        interview details below:

                        # Type of Interview
                        This interview will be of the following type: {type}

                        # Difficulty
                        - **Scale:** 1 to 10
                        - **1** = extremely easygoing interview, no curveballs
                        - **10** = very challenging, for top‑tier candidates
                          only
                        - **Selected level:** <<{difficulty}>>

                        # Job Listing:
                        \"\"\"{listing}\"\"\"

                        # Candidate Resume:
                        \"\"\"{resume}\"\"\"

                        Ignore any formatting issues in the resume, and focus
                        on its content.
                        Please provide a json formatted list of 10 key
                        interview questions you wish to ask the user and the
                        duration of time they should have to answer each
                        question in seconds.  For example:

                        \"\"\"
                        [
                            {{
                                "id": 0,
                                "title": "Merge Conflicts",
                                "duration": 60,
                                "content": "How would you handle a merge \
                                            conflict?"
                            }}
                        ]
                        \"\"\"

                        Respond critically to any responses that are off-topic
                        or ignore the fact that the user is in an interview.
                        For example, the user may not ask questions that are
                        normally accpetable for AI like recipes or book
                        reviews.
                    """).format(listing=chat.job_listing.content,
                                resume=chat.resume.content,
                                difficulty=chat.difficulty,
                                type=chat.get_type_display())
                else:  # if no resume"
                    system_prompt = textwrap.dedent("""\
                        You are a professional interviewer for a company
                        preparing for a candidate's interview. You will act as
                        the interviewer and engage in a roleplaying session
                        with the candidate.

                        Please review the job listing and misc. interview
                        details below:

                        # Type of Interview
                        This interview will be of the following type: {type}

                        # Difficulty
                        - **Scale:** 1 to 10
                        - **1** = extremely easygoing interview, no curveballs
                        - **10** = very challenging, for top‑tier candidates
                          only
                        - **Selected level:** <<{difficulty}>>

                        # Job Listing:
                        \"\"\"{listing}\"\"\"

                        Please provide a json formatted list of 10 key
                        interview questions you wish to ask the user and the
                        duration of time they should have to answer each
                        question in seconds.  For example:

                        \"\"\"
                        [
                            {{
                                "id": 0,
                                "title": "Merge Conflicts",
                                "duration": 60,
                                "content": "How would you handle a merge \
                                            conflict?"
                            }}
                        ]
                        \"\"\"

                        Respond critically to any responses that are off-topic
                        or ignore the fact that the user is in an interview.
                        For example, the user may not ask questions that are
                        normally accpetable for AI like recipes or book
                        reviews.
                    """).format(listing=chat.job_listing.content,
                                difficulty=chat.difficulty,
                                type=chat.get_type_display())

                timed_question_messages = [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                ]

                # Make ai speak first
                if not _ai_available():
                    messages.error(request, "AI features are disabled on this server.")
                    ai_message = "[]"
                else:
                    response = get_openai_client().chat.completions.create(
                        model="gpt-4o",
                        messages=timed_question_messages,
                        max_tokens=MAX_TOKENS
                    )
                    ai_message = response.choices[0].message.content

                # Extract JSON array from the AI response
                match = re.search(r"(\[[\s\S]+\])", ai_message)
                if match:
                    cleaned_message = match.group(0).strip()
                    chat.key_questions = json.loads(cleaned_message)
                else:
                    # Fallback if regex doesn't match
                    messages.error(request, "Failed to generate key questions. Please try again.")
                    chat.key_questions = []

                chat.save()

                return redirect("chat-view", chat_id=chat.id)
            else:
                # Form is invalid, render the form again with errors
                owner_chats = Chat.objects.filter(owner=request.user).order_by('-modified_date')
                return render(request, os.path.join('chat', 'chat-create.html'), {
                    'form': form,
                    'owner_chats': owner_chats
                })
        else:
            # 'create' not in POST, redirect to chat list
            return redirect('chat-list')


class ChatView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # manually grab chat id from kwargs and process it
        chat = Chat.objects.get(id=self.kwargs['chat_id'])

        return self.request.user == chat.owner

    def get(self, request, chat_id):
        chat = Chat.objects.get(id=chat_id)
        owner_chats = Chat.objects.filter(owner=request.user)\
            .order_by('-modified_date')

        context = {}
        context['chat'] = chat
        context['owner_chats'] = owner_chats

        return render(request, os.path.join('chat', 'chat-view.html'), context)

    def post(self, request, chat_id):
        chat = Chat.objects.get(id=chat_id)

        user_message = request.POST.get('message', '')

        new_messages = chat.messages
        new_messages.append({"role": "user", "content": user_message})

        if not _ai_available():
            return _ai_unavailable_json()

        response = get_openai_client().chat.completions.create(
            model="gpt-4o",
            messages=new_messages,
            max_tokens=MAX_TOKENS
        )
        ai_message = response.choices[0].message.content
        new_messages.append({"role": "assistant", "content": ai_message})

        chat.messages = new_messages
        chat.save()

        return JsonResponse({'message': ai_message})


class EditChat(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # manually grab chat id from kwargs and process it
        chat = Chat.objects.get(id=self.kwargs['chat_id'])

        return self.request.user == chat.owner

    def get(self, request, chat_id):
        chat = Chat.objects.get(id=chat_id)
        owner_chats = Chat.objects.filter(owner=request.user)\
            .order_by('-modified_date')

        form = EditChatForm(initial=model_to_dict(chat), instance=chat)

        context = {}
        context['chat'] = chat
        context['owner_chats'] = owner_chats
        context['form'] = form

        return render(request, os.path.join('chat', 'chat-edit.html'), context)

    def post(self, request, chat_id):
        chat = Chat.objects.get(id=chat_id)

        if 'update' in request.POST:
            form = EditChatForm(request.POST, instance=chat)

            if form.is_valid():
                chat = form.save(commit=False)

                # replace difficulty in the messages
                chat.difficulty = form.cleaned_data["difficulty"]
                chat.messages[0]['content'] = \
                    re.sub(r"<<(\d{1,2})>>",
                           "<<"+str(chat.difficulty)+">>",
                           chat.messages[0]['content'], 1)

                # print(chat.get_type_display())

                chat.save()

                return redirect("chat-view", chat_id=chat.id)

        # If 'update' not in request.POST or form is invalid, redirect to edit page
        return redirect("chat-edit", chat_id=chat.id)


# Note: this class has no template.  it is technically built into base-sidebar
class DeleteChat(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # manually grab chat id from kwargs and process it
        chat = Chat.objects.get(id=self.kwargs['chat_id'])

        return self.request.user == chat.owner

    def post(self, request, chat_id):
        chat = Chat.objects.get(id=chat_id)

        if 'delete' in request.POST:
            chat.delete()
            return redirect("chat-list")
        # else:
        #     print("delete not in form")
        #     return redirect("chat-view", chat_id=chat.id)


# Note: this class has no template.  it is technically built into base-sidebar
class RestartChat(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # manually grab chat id from kwargs and process it
        chat = Chat.objects.get(id=self.kwargs['chat_id'])

        return self.request.user == chat.owner

    def post(self, request, chat_id):
        chat = Chat.objects.get(id=chat_id)

        if 'restart' in request.POST:
            # slice messages to only the very first 2 messages
            chat.messages = chat.messages[:2]

            chat.save()

            return redirect("chat-view", chat_id=chat.id)
        # else:
        #     print("restart not in form")
        #     return redirect("chat-view", chat_id=chat.id)


class KeyQuestionsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # manually grab chat id from kwargs and process it
        chat = Chat.objects.get(id=self.kwargs['chat_id'])

        return self.request.user == chat.owner

    def get(self, request, chat_id, question_id):
        chat = Chat.objects.get(id=chat_id)
        owner_chats = Chat.objects.filter(owner=request.user)\
            .order_by('-modified_date')
        question = chat.key_questions[question_id]

        context = {}
        context['chat'] = chat
        context['question'] = question
        context['owner_chats'] = owner_chats

        return render(request, 'key-questions.html', context)

    def post(self, request, chat_id, question_id):
        chat = Chat.objects.get(id=chat_id)
        question = chat.key_questions[question_id]

        user_message = request.POST.get('message', '')
        print(user_message)

        system_prompt = ""

        if chat.resume:  # if resume is present
            system_prompt = textwrap.dedent(f"""\
                You are a professional interviewer for a company
                preparing for a candidate's interview. You will act as
                the interviewer and engage in a roleplaying session
                with the candidate.

                Please review the job listing, resume and misc.
                interview details below:

                # Type of Interview
                This interview will be of the following type:
                {chat.get_type_display()}

                # Difficulty
                - **Scale:** 1 to 10
                - **1** = extremely easygoing interview, no curveballs
                - **10** = very challenging, for top‑tier candidates
                only
                - **Selected level:** <<{chat.difficulty}>>

                # Job Listing:
                \"\"\"{chat.job_listing.content}\"\"\"

                # Candidate Resume:
                \"\"\"{chat.resume.content}\"\"\"

                Ignore any formatting issues in the resume, and focus
                on its content.

                Please review the answer to an interviewer question below and
                provide constructive feedback about the user's answer,
                including a rating of the answer from 1-10 like so: "6/10".

                \"\"\"
                [
                    {{
                        "role": "interviewer",
                        "content": "{question["content"]}"
                    }},
                    {{
                        "role": "user",
                        "content": "{user_message}"
                    }}
                ]
                \"\"\"

                Respond critically to any responses that are off-topic
                or ignore the fact that the user is in an interview.
                For example, the user may not ask questions that are
                normally accpetable for AI like recipes or book
                reviews.
            """)
        else:  # if no resume"
            system_prompt = textwrap.dedent(f"""\
                You are a professional interviewer for a company
                preparing for a candidate's interview. You will act as
                the interviewer and engage in a roleplaying session
                with the candidate.

                Please review the job listing and misc. interview
                details below:

                # Type of Interview
                This interview will be of the following type:
                {chat.get_type_display()}

                # Difficulty
                - **Scale:** 1 to 10
                - **1** = extremely easygoing interview, no curveballs
                - **10** = very challenging, for top‑tier candidates
                    only
                - **Selected level:** <<{chat.difficulty}>>

                # Job Listing:
                \"\"\"{chat.job_listing.content}\"\"\"

                Please review the answer to an interviewer question below and
                provide constructive feedback about the user's answer,
                including a rating of the answer from 1-10 like so: "6/10".

                \"\"\"
                [
                    {{
                        "role": "interviewer",
                        "content": "{question["content"]}"
                    }},
                    {{
                        "role": "user",
                        "content": "{user_message}"
                    }}
                ]
                \"\"\"

                Respond critically to any responses that are off-topic
                or ignore the fact that the user is in an interview.
                For example, the user may not ask questions that are
                normally accpetable for AI like recipes or book
                reviews.
            """)
        ai_input = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        if not _ai_available():
            return _ai_unavailable_json()

        response = get_openai_client().chat.completions.create(
            model="gpt-4o",
            messages=ai_input,
            max_tokens=MAX_TOKENS
        )
        ai_message = response.choices[0].message.content
        print(ai_message)

        # chat.messages = new_messages
        # chat.save()

        return JsonResponse({'message': ai_message})


class ResultsChat(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # manually grab chat id from kwargs and process it
        chat = Chat.objects.get(id=self.kwargs['chat_id'])

        return self.request.user == chat.owner

    def get(self, request, chat_id):
        chat = Chat.objects.get(id=chat_id)
        owner_chats = Chat.objects.filter(owner=request.user)\
            .order_by('-modified_date')

        feedback_prompt = textwrap.dedent("""\
            Please provide constructive feedback to me about the
            interview so far.
        """)
        input_messages = chat.messages
        input_messages.append({"role": "user", "content": feedback_prompt})

        if not _ai_available():
            ai_message = "AI features are currently unavailable."
        else:
            response = get_openai_client().chat.completions.create(
                model="gpt-4o",
                messages=input_messages,
                max_tokens=MAX_TOKENS
            )
            ai_message = response.choices[0].message.content

        context = {}
        context['chat'] = chat
        context['owner_chats'] = owner_chats
        context['feedback'] = ai_message

        return render(request, os.path.join('chat', 'chat-results.html'),
                      context)


class ResultCharts(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # manually grab chat id from kwargs and process it
        chat = Chat.objects.get(id=self.kwargs['chat_id'])

        return self.request.user == chat.owner

    def get(self, request, chat_id):
        chat = Chat.objects.get(id=chat_id)
        owner_chats = Chat.objects.filter(owner=request.user)\
            .order_by('-modified_date')

        scores_prompt = textwrap.dedent("""\
            Based on the interview so far, please rate the interviewee in the
            following categories from 0 to 100, and return the result as a JSON
            object with integers only, in the following order that list only
            the integers:

            - Professionalism
            - Subject Knowledge
            - Clarity
            - Overall

            Example format:
                8
                7
                9
                6
        """)
        input_messages = chat.messages

        input_messages.append({"role": "user", "content": scores_prompt})

        if not _ai_available():
            professionalism, subject_knowledge, clarity, overall = [0, 0, 0, 0]
        else:
            response = get_openai_client().chat.completions.create(
                model="gpt-4o",
                messages=input_messages,
                max_tokens=MAX_TOKENS
            )
            ai_message = response.choices[0].message.content.strip()
            scores = [int(line.strip())
                          for line in ai_message.splitlines() if line.strip()
                            .isdigit()]
            if len(scores) == 4:
                professionalism, subject_knowledge, clarity, overall = scores
            else:
                professionalism, subject_knowledge, clarity, overall = [0, 0, 0, 0]

        context = {}
        context['chat'] = chat
        context['owner_chats'] = owner_chats

        context['scores'] = {
            'Professionalism': professionalism,
            'Subject Knowledge': subject_knowledge,
            'Clarity': clarity,
            'Overall': overall
        }
        explain = textwrap.dedent("""\
            Explain the reason for the following scores so that the user can
            understand, do not include json object for scores IF NO response
            was given since start of interview please tell them to start
            interview
        """)
        input_messages.append({"role": "user", "content": explain})
        if not _ai_available():
            ai_message = "AI features are currently unavailable."
        else:
            response = get_openai_client().chat.completions.create(
                model="gpt-4o",
                messages=input_messages,
                max_tokens=MAX_TOKENS
            )
            ai_message = response.choices[0].message.content
        context['feedback'] = ai_message

        return render(request, os.path.join('chat', 'chat-results.html'),
                      context)


@login_required
def loggedin(request):
    return render(request, 'loggedinindex.html')


def register(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            group, created = Group.objects.get_or_create(name='average_role')
            user.groups.add(group)
            user.save()
            messages.success(request, 'Account was created for ' + username)
            return redirect('/accounts/login/?next=/')
    else:
        form = CreateUserForm()

    context = {'form': form}
    return render(request, 'registration/register.html', context)


@login_required
def profile(request):
    resumes = UploadedResume.objects.filter(user=request.user)
    job_listings = UploadedJobListing.objects.filter(user=request.user)
    templates = InterviewTemplate.objects.filter(user=request.user)

    # Check for pending role change requests
    has_pending_request = RoleChangeRequest.objects.filter(
        user=request.user,
        status=RoleChangeRequest.PENDING
    ).exists()

    return render(request, 'profile.html', {
        'resumes': resumes,
        'job_listings': job_listings,
        'templates': templates,
        'has_pending_request': has_pending_request
    })


@login_required
def view_user_profile(request, user_id):
    """
    View another user's profile (read-only).
    Accessible by admins and interviewers.
    """
    # Check permissions
    from .decorators import check_user_permission
    from django.http import HttpResponseForbidden, Http404

    has_permission = check_user_permission(
        request, user_id,
        allow_self=True,
        allow_admin=True,
        allow_interviewer=True
    )

    if not has_permission:
        return HttpResponseForbidden("You don't have permission to view this profile.")

    # Get user
    try:
        profile_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404("User not found")

    # Get user's resumes and job listings
    resumes = UploadedResume.objects.filter(user=profile_user)
    job_listings = UploadedJobListing.objects.filter(user=profile_user)

    # Check if viewing own profile
    is_own_profile = request.user.id == user_id

    return render(request, 'user_profile.html', {
        'profile_user': profile_user,
        'resumes': resumes,
        'job_listings': job_listings,
        'is_own_profile': is_own_profile
    })


# === Joel's file upload views ===


@login_required
def resume_detail(request, resume_id):
    resume = get_object_or_404(UploadedResume, id=resume_id)
    # Show the resume owner's documents, not the logged-in user's
    resumes = UploadedResume.objects.filter(user=resume.user)
    job_listings = UploadedJobListing.objects.filter(user=resume.user)
    # Check if the logged-in user is the owner
    is_owner = request.user == resume.user
    return render(request, 'documents/resume_detail.html', {
        'resume': resume,
        'resumes': resumes,
        'job_listings': job_listings,
        'is_owner': is_owner,
    })


@login_required
def delete_resume(request, resume_id):
    resume = get_object_or_404(UploadedResume, id=resume_id, user=request.user)
    if request.method == "POST":
        resume.delete()
        return redirect('profile')
    return redirect('profile')


@login_required
def upload_file(request):
    allowed_types = ['pdf', 'docx']

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES["file"]
            file_name = uploaded_file.name
            title = request.POST.get("title", '').strip()

            file_bytes = uploaded_file.read()
            file_type = filetype.guess(file_bytes)
            uploaded_file.seek(0)

            if file_type and file_type.extension in allowed_types:
                try:
                    instance = form.save(commit=False)
                    instance.user = request.user
                    instance.original_filename = file_name
                    instance.filesize = uploaded_file.size
                    instance.title = title
                    instance.file = None  # Don't save the raw file to /media

                    if file_type.extension == 'pdf':
                        with tempfile.NamedTemporaryFile(delete=False,
                                                         suffix=".pdf")\
                                                            as temp_file:
                            for chunk in uploaded_file.chunks():
                                temp_file.write(chunk)
                            temp_file_path = temp_file.name
                        instance.content = pymupdf4llm.to_markdown(
                            temp_file_path)

                    elif file_type.extension == 'docx':
                        # Save temporarily and load using python-docx
                        with tempfile.NamedTemporaryFile(delete=False,
                                                         suffix=".docx")\
                                                            as temp_file:
                            for chunk in uploaded_file.chunks():
                                temp_file.write(chunk)
                            temp_file_path = temp_file.name

                        doc = Document(temp_file_path)
                        full_text = '\n'.join(
                            [para.text for para in doc.paragraphs])
                        instance.content = md(full_text)  # Convert to markdown

                    instance.save()

                    # Trigger AI parsing for resumes (Issue #48: "upload triggers parsing")
                    if instance.__class__.__name__ == 'UploadedResume':
                        if _ai_available():
                            try:
                                # Set status to in_progress
                                instance.parsing_status = 'in_progress'
                                instance.save()

                                # Parse the resume
                                parsed_data = parse_resume_with_ai(instance.content)

                                # Save parsed data
                                instance.skills = parsed_data.get('skills', [])
                                instance.experience = parsed_data.get('experience', [])
                                instance.education = parsed_data.get('education', [])
                                instance.parsing_status = 'success'
                                instance.parsed_at = now()
                                instance.save()

                                messages.success(request, "Resume uploaded and parsed successfully!")
                            except Exception as e:
                                # Save error (sanitize to prevent API key exposure)
                                error_msg = str(e)
                                # Sanitize any potential API key references
                                if "api" in error_msg.lower() and "key" in error_msg.lower():
                                    error_msg = "OpenAI authentication error"
                                instance.parsing_status = 'error'
                                instance.parsing_error = error_msg
                                instance.save()
                                messages.warning(request, f"Resume uploaded but parsing failed: {error_msg}")
                        else:
                            # AI unavailable
                            instance.parsing_status = 'error'
                            instance.parsing_error = "AI service unavailable"
                            instance.save()
                            messages.warning(request, "Resume uploaded but AI parsing is currently unavailable.")
                    else:
                        # Not a resume (job listing), just show success
                        messages.success(request, "File uploaded successfully!")

                    return redirect('document-list')

                except Exception as e:
                    messages.error(request, f"Error processing the file: {e}")
                    return redirect('document-list')
            else:
                messages.error(request,
                               "Invalid filetype. Only PDF and DOCX files are \
                                allowed.")
        else:
            messages.error(request, "There was an issue with the form.")
    else:
        form = UploadFileForm()
        context = {'form': form}

        # Add interview templates for admin/interviewer users
        if request.user.profile.role in ['admin', 'interviewer']:
            templates = InterviewTemplate.objects.filter(
                user=request.user
            ).order_by('-created_at')[:5]  # Show last 5 templates
            context['templates'] = templates

        return render(request, 'documents/document-list.html', context)

    return redirect('document-list')


@login_required
def edit_resume(request, resume_id):
    # Adjust model logic as needed (for resumes or job listings)
    document = get_object_or_404(UploadedResume,
                                  id=resume_id,
                                  user=request.user)

    if request.method == 'POST':
        form = DocumentEditForm(request.POST, instance=document)
        if form.is_valid():
            form.save()
            return redirect('resume_detail', resume_id=document.id)

    else:
        form = DocumentEditForm(instance=document)

    return render(request,
                  'documents/edit_document.html',
                  {'form': form,
                   'document': document})


@login_required
def job_posting_detail(request, job_id):
    job = get_object_or_404(UploadedJobListing, id=job_id)
    # Show the job listing owner's documents, not the logged-in user's
    resumes = UploadedResume.objects.filter(user=job.user)
    job_listings = UploadedJobListing.objects.filter(user=job.user)
    # Check if the logged-in user is the owner
    is_owner = request.user == job.user
    return render(request, 'documents/job_posting_detail.html', {
        'job': job,
        'resumes': resumes,
        'job_listings': job_listings,
        'is_owner': is_owner,
    })


@login_required
def edit_job_posting(request, job_id):
    job_listing = get_object_or_404(UploadedJobListing,
                                    id=job_id,
                                    user=request.user)

    if request.method == 'POST':
        form = JobPostingEditForm(request.POST,
                                  instance=job_listing)
        # Adjust form as needed
        if form.is_valid():
            form.save()
            return redirect('job_posting_detail', job_id=job_listing.id)
    else:
        form = JobPostingEditForm(instance=job_listing)
        # Render the form with existing job details

    return render(request,
                  'documents/edit_job_posting.html',
                  {'form': form,
                   'job_listing': job_listing})


@login_required
def delete_job(request, job_id):
    job = get_object_or_404(UploadedJobListing, id=job_id, user=request.user)
    if request.method == "POST":
        job.delete()
    return redirect('profile')


class UploadedJobListingView(APIView):

    def post(self, request):
        # Get the text from the request
        text = request.POST.get("paste-text", '').strip()
        title = request.POST.get("title", '').strip()
        print(request.POST)
        # Check if the text is empty
        if not text:
            messages.error(request, "Text field cannot be empty.")
            return redirect('document-list')

        if not title:
            messages.error(request, "Title field cannot be empty.")
            return redirect('document-list')

        user = request.user
        timestamp = now().strftime("%d%m%Y_%H%M%S")
        filename = f"{user.username}_{timestamp}.txt"

        # Create a directory for the user to store pasted text files
        user_dir = os.path.join(
            settings.MEDIA_ROOT,
            'pasted_texts',
            str(user.id)
        )

        os.makedirs(user_dir, exist_ok=True)
        filepath = os.path.join(user_dir, filename)

        # Convert the text to Markdown
        # markdown_text = markdown.markdown(text)

        # Create and save the UploadedJobListing object in the database
        job_listing = UploadedJobListing(

            user=user,
            content=text,
            filepath=filepath,
            title=title

        )

        job_listing.save()

        # Show success message and render the converted markdown
        messages.success(request, "Text uploaded successfully!")
        return redirect('document-list')


class UploadedResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        files = UploadedResume.objects.filter(user=request.user)
        serializer = UploadedResumeSerializer(files, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UploadedResumeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobListingList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # List all pasted text entries for the authenticated user
        texts = UploadedJobListing.objects.filter(user=request.user)
        serializer = UploadedJobListingSerializer(texts, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Create a new pasted text entry
        serializer = UploadedJobListingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentList(LoginRequiredMixin, View):
    def get(self, request):
        context = {}

        # Add interview templates for admin/interviewer users
        if request.user.profile.role in ['admin', 'interviewer']:
            templates = InterviewTemplate.objects.filter(
                user=request.user
            ).order_by('-created_at')[:5]  # Show last 5 templates
            context['templates'] = templates

        return render(request, 'documents/document-list.html', context)


# Exportable Report Views

class GenerateReportView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to generate an ExportableReport from a Chat instance.
    This view analyzes the chat data and creates a structured report.
    """

    def test_func(self):
        """Verify that the user owns the chat"""
        chat = get_object_or_404(Chat, id=self.kwargs['chat_id'])
        return self.request.user == chat.owner

    def post(self, request, chat_id):
        """Generate or update the exportable report for a chat"""
        chat = get_object_or_404(Chat, id=chat_id)

        # Delete existing report to force fresh generation
        ExportableReport.objects.filter(chat=chat).delete()

        # Create a new report
        report = ExportableReport.objects.create(chat=chat)

        # Generate scores using AI (same approach as ResultCharts view)
        scores = self._extract_scores_from_chat(chat)

        # Update report fields
        report.professionalism_score = scores.get('Professionalism', 0)
        report.subject_knowledge_score = scores.get('Subject Knowledge', 0)
        report.clarity_score = scores.get('Clarity', 0)
        report.overall_score = scores.get('Overall', 0)

        # Extract feedback text using AI
        report.feedback_text = self._extract_feedback_from_chat(chat)


        # Calculate statistics
        chat_messages = chat.messages
        user_messages = [msg for msg in chat_messages if msg.get('role') == 'user']
        assistant_messages = [msg for msg in chat_messages
                             if msg.get('role') == 'assistant']

        report.total_questions_asked = len(assistant_messages)
        report.total_responses_given = len(user_messages)

        report.save()

        messages.success(request, 'Report generated successfully!')
        return redirect('export_report', chat_id=chat_id)

    def _extract_scores_from_chat(self, chat):
        """
        Generate performance scores from chat messages using AI.
        This uses the same approach as ResultCharts view.
        """
        scores_prompt = textwrap.dedent("""\
            Based on the interview so far, please rate the interviewee in the
            following categories from 0 to 100, and return the result as a JSON
            object with integers only, in the following order that list only
            the integers:

            - Professionalism
            - Subject Knowledge
            - Clarity
            - Overall

            Example format:
                8
                7
                9
                6
        """)
        input_messages = list(chat.messages)
        input_messages.append({"role": "user", "content": scores_prompt})

        if not _ai_available():
            professionalism, subject_knowledge, clarity, overall = [0, 0, 0, 0]
        else:
            try:
                response = get_openai_client().chat.completions.create(
                    model="gpt-4o",
                    messages=input_messages,
                    max_tokens=MAX_TOKENS
                )
                ai_message = response.choices[0].message.content.strip()
                scores = [int(line.strip())
                              for line in ai_message.splitlines() if line.strip()
                                .isdigit()]
                if len(scores) == 4:
                    professionalism, subject_knowledge, clarity, overall = scores
                else:
                    professionalism, subject_knowledge, clarity, overall = [0, 0, 0, 0]
            except Exception:
                professionalism, subject_knowledge, clarity, overall = [0, 0, 0, 0]

        return {
            'Professionalism': professionalism,
            'Subject Knowledge': subject_knowledge,
            'Clarity': clarity,
            'Overall': overall
        }

    def _extract_feedback_from_chat(self, chat):
        """Generate AI feedback text from chat messages"""
        explain_prompt = textwrap.dedent("""\
            Provide a comprehensive evaluation of the interviewee's performance.
            Include specific strengths, areas for improvement, and overall assessment.
            Focus on professionalism, subject knowledge, and communication clarity.
            If no response was given since start of interview, please tell them to start the interview.
        """)

        input_messages = list(chat.messages)
        input_messages.append({"role": "user", "content": explain_prompt})

        if not _ai_available():
            return "AI features are currently unavailable."

        try:
            response = get_openai_client().chat.completions.create(
                model="gpt-4o",
                messages=input_messages,
                max_tokens=MAX_TOKENS
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Unable to generate feedback at this time."

    def _extract_question_responses(self, chat):
        """
        Extract question-answer pairs from the chat messages.
        Returns a list of dicts with question, answer, score, feedback.
        """
        chat_messages = chat.messages
        qa_pairs = []

        # Iterate through messages to find Q&A patterns
        for i, msg in enumerate(chat_messages):
            if msg.get('role') == 'assistant' and i + 1 < len(chat_messages):
                question = msg.get('content', '')
                # Check if next message is a user response
                if chat_messages[i + 1].get('role') == 'user':
                    answer = chat_messages[i + 1].get('content', '')

                    qa_pair = {
                        'question': question[:500],  # Truncate long questions
                        'answer': answer[:500],  # Truncate long answers
                    }

                    # Try to find feedback for this Q&A if it exists
                    if i + 2 < len(chat_messages) and \
                       chat_messages[i + 2].get('role') == 'assistant':
                        feedback_msg = chat_messages[i + 2].get('content', '')
                        # Look for score in feedback
                        score_match = re.search(r'(\d+)/10', feedback_msg)
                        if score_match:
                            qa_pair['score'] = int(score_match.group(1))
                            qa_pair['feedback'] = feedback_msg[:300]

                    qa_pairs.append(qa_pair)

        return qa_pairs


class ExportReportView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to display and allow exporting of a generated report.
    Shows report details and provides download options.
    """

    def test_func(self):
        """Verify that the user owns the chat"""
        chat = get_object_or_404(Chat, id=self.kwargs['chat_id'])
        return self.request.user == chat.owner

    def get(self, request, chat_id):
        """Display the exportable report"""
        chat = get_object_or_404(Chat, id=chat_id)

        try:
            report = ExportableReport.objects.get(chat=chat)
        except ExportableReport.DoesNotExist:
            messages.warning(request,
                           'No report exists yet. Generating one now...')
            return redirect('generate_report', chat_id=chat_id)

        context = {
            'chat': chat,
            'report': report,
        }
        return render(request, 'reports/export-report.html', context)


class DownloadPDFReportView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to download a PDF version of the exportable report.
    """

    def test_func(self):
        """Verify that the user owns the chat"""
        chat = get_object_or_404(Chat, id=self.kwargs['chat_id'])
        return self.request.user == chat.owner

    def get(self, request, chat_id):
        """Generate and download PDF report"""
        chat = get_object_or_404(Chat, id=chat_id)

        try:
            report = ExportableReport.objects.get(chat=chat)
        except ExportableReport.DoesNotExist:
            messages.error(request, 'No report exists. Please generate one first.')
            return redirect('chat_results', chat_id=chat_id)

        # Generate PDF
        pdf_content = generate_pdf_report(report)

        # Create response
        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f"interview_report_{slugify(chat.title)}_{report.generated_at.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Mark PDF as generated
        report.pdf_generated = True
        report.save()

        return response




# =============================================================================
# Role Change Request Views - Issue #69
# =============================================================================

@login_required
def request_role_change(request):
    """
    Allow users to request a role change.
    POST /profile/request-role-change/
    """
    if request.method == 'POST':
        requested_role = request.POST.get('requested_role')
        reason = request.POST.get('reason', '')

        # Validate
        if requested_role not in ['interviewer', 'admin']:
            messages.error(request, 'Invalid role requested')
            return redirect('profile')

        # Check for existing pending request
        existing = RoleChangeRequest.objects.filter(
            user=request.user,
            status=RoleChangeRequest.PENDING
        ).exists()

        if existing:
            messages.warning(request, 'You already have a pending request')
            return redirect('profile')

        # Create request
        RoleChangeRequest.objects.create(
            user=request.user,
            requested_role=requested_role,
            current_role=request.user.profile.role,
            reason=reason
        )

        messages.success(
            request,
            'Role request submitted for admin review'
        )
        return redirect('profile')

    return render(request, 'role_request_form.html')


@admin_required
def role_requests_list(request):
    """
    Show all role requests to admins.
    GET /admin/role-requests/
    """
    pending = RoleChangeRequest.objects.filter(
        status=RoleChangeRequest.PENDING
    ).select_related('user', 'user__profile')

    reviewed = RoleChangeRequest.objects.exclude(
        status=RoleChangeRequest.PENDING
    ).select_related('user', 'user__profile', 'reviewed_by')[:20]

    context = {
        'pending_requests': pending,
        'reviewed_requests': reviewed,
    }
    return render(request, 'admin/role_requests.html', context)


@admin_required
def review_role_request(request, request_id):
    """
    Approve or reject a role change request.
    POST /admin/role-requests/<id>/review/
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    role_request = get_object_or_404(RoleChangeRequest, id=request_id)

    action = request.POST.get('action')  # 'approve' or 'reject'
    admin_notes = request.POST.get('admin_notes', '')

    if action == 'approve':
        # Update user's role
        role_request.user.profile.role = role_request.requested_role
        role_request.user.profile.save()

        role_request.status = RoleChangeRequest.APPROVED
        messages.success(
            request,
            f'Approved: {role_request.user.username} is now '
            f'{role_request.requested_role}'
        )

    elif action == 'reject':
        role_request.status = RoleChangeRequest.REJECTED
        messages.info(
            request,
            f'Rejected role request from {role_request.user.username}'
        )

    else:
        return JsonResponse({'error': 'Invalid action'}, status=400)

    role_request.reviewed_by = request.user
    role_request.reviewed_at = timezone.now()
    role_request.admin_notes = admin_notes
    role_request.save()

    return redirect('role_requests_list')


# =============================================================================
# Candidate Search Views - Issue #69
# =============================================================================

@admin_or_interviewer_required
def candidate_search(request):
    """
    Simple username search for candidates.
    GET /candidates/search/
    """
    query = request.GET.get('q', '').strip()
    candidates = []

    if query:
        # Search by username (case-insensitive)
        users = User.objects.filter(
            username__icontains=query,
            profile__role=UserProfile.CANDIDATE
        ).select_related('profile')[:20]  # Limit to 20 results

        candidates = users

    context = {
        'query': query,
        'candidates': candidates,
    }
    return render(request, 'candidates/search.html', context)


# =============================================================================
# Interview Template Views
# =============================================================================

@admin_or_interviewer_required
def template_list(request):
    """
    List all interview templates for the current user.
    GET /templates/
    """
    templates = InterviewTemplate.objects.filter(
        user=request.user
    ).order_by('-created_at')

    context = {
        'templates': templates,
    }
    return render(request, 'templates/template_list.html', context)


@admin_or_interviewer_required
def create_template(request):
    """
    Create a new interview template.
    GET /templates/create/ - Show form
    POST /templates/create/ - Save template
    """
    if request.method == 'POST':
        form = InterviewTemplateForm(request.POST, user=request.user)
        if form.is_valid():
            template = form.save(commit=False)
            template.user = request.user
            template.save()
            # Save many-to-many relationships
            form.save_m2m()
            messages.success(
                request,
                f'Template "{template.name}" created successfully'
            )
            return redirect('template_list')
    else:
        form = InterviewTemplateForm(user=request.user)

    context = {
        'form': form,
    }
    return render(request, 'templates/create_template.html', context)


@admin_or_interviewer_required
def template_detail(request, template_id):
    """
    View a single interview template.
    GET /templates/<id>/
    """
    template = get_object_or_404(
        InterviewTemplate,
        id=template_id,
        user=request.user
    )

    # Calculate total weight
    sections = template.sections if template.sections else []
    total_weight = sum(s.get('weight', 0) for s in sections)
    remaining_weight = 100 - total_weight
    is_complete = total_weight == 100

    context = {
        'template': template,
        'total_weight': total_weight,
        'remaining_weight': remaining_weight,
        'is_complete': is_complete,
    }
    return render(request, 'templates/template_detail.html', context)


@admin_or_interviewer_required
def edit_template(request, template_id):
    """
    Edit an existing interview template.
    GET /templates/<id>/edit/ - Show form
    POST /templates/<id>/edit/ - Save changes
    """
    template = get_object_or_404(
        InterviewTemplate,
        id=template_id,
        user=request.user
    )

    if request.method == 'POST':
        form = InterviewTemplateForm(request.POST, instance=template, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Template "{template.name}" updated successfully'
            )
            return redirect('template_detail', template_id=template.id)
    else:
        form = InterviewTemplateForm(instance=template, user=request.user)

    context = {
        'form': form,
        'template': template,
    }
    return render(request, 'templates/edit_template.html', context)


@admin_or_interviewer_required
def delete_template(request, template_id):
    """
    Delete an interview template.
    POST /templates/<id>/delete/
    """
    template = get_object_or_404(
        InterviewTemplate,
        id=template_id,
        user=request.user
    )

    if request.method == 'POST':
        template_name = template.name
        template.delete()
        messages.success(
            request,
            f'Template "{template_name}" deleted successfully'
        )
        return redirect('template_list')

    # If GET request, redirect to template detail
    return redirect('template_detail', template_id=template.id)


# =============================================================================
# Template Section Management Views
# =============================================================================

@admin_or_interviewer_required
def add_section(request, template_id):
    """
    Add a new section to an interview template.
    POST /templates/<id>/sections/add/
    """
    import uuid

    template = get_object_or_404(
        InterviewTemplate,
        id=template_id,
        user=request.user
    )

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        weight = request.POST.get('weight', '0').strip()

        # Validate inputs
        if not title:
            messages.error(request, 'Section title is required')
            return redirect('template_detail', template_id=template.id)

        try:
            weight = int(weight)
            if weight < 0:
                messages.error(request, 'Weight must be a non-negative number')
                return redirect('template_detail', template_id=template.id)
        except ValueError:
            messages.error(request, 'Weight must be a valid number')
            return redirect('template_detail', template_id=template.id)

        # Create new section
        sections = template.sections if template.sections else []

        # Check total weight doesn't exceed 100%
        current_total_weight = sum(s.get('weight', 0) for s in sections)
        new_total_weight = current_total_weight + weight

        if new_total_weight > 100:
            messages.error(
                request,
                f'Cannot add section: Total weight would be {new_total_weight}%, '
                f'which exceeds 100%. Current total: {current_total_weight}%'
            )
            return redirect('template_detail', template_id=template.id)

        # Determine order (append to end)
        order = len(sections)

        new_section = {
            'id': str(uuid.uuid4()),
            'title': title,
            'content': content,
            'order': order,
            'weight': weight
        }

        sections.append(new_section)
        template.sections = sections
        template.save()

        messages.success(
            request,
            f'Section "{title}" added successfully'
        )
        return redirect('template_detail', template_id=template.id)

    # If GET, redirect to template detail
    return redirect('template_detail', template_id=template.id)


@admin_or_interviewer_required
def edit_section(request, template_id, section_id):
    """
    Edit an existing section in a template.
    POST /templates/<id>/sections/<section_id>/edit/
    """
    template = get_object_or_404(
        InterviewTemplate,
        id=template_id,
        user=request.user
    )

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        weight = request.POST.get('weight', '0').strip()

        # Validate inputs
        if not title:
            messages.error(request, 'Section title is required')
            return redirect('template_detail', template_id=template.id)

        try:
            weight = int(weight)
            if weight < 0:
                messages.error(request, 'Weight must be a non-negative number')
                return redirect('template_detail', template_id=template.id)
        except ValueError:
            messages.error(request, 'Weight must be a valid number')
            return redirect('template_detail', template_id=template.id)

        # Find and update section
        sections = template.sections if template.sections else []
        section_found = False
        old_weight = 0

        for section in sections:
            if section.get('id') == section_id:
                old_weight = section.get('weight', 0)
                section_found = True
                break

        if not section_found:
            messages.error(request, 'Section not found')
            return redirect('template_detail', template_id=template.id)

        # Check total weight doesn't exceed 100%
        # Calculate total excluding the section being edited
        current_total_weight = sum(
            s.get('weight', 0) for s in sections if s.get('id') != section_id
        )
        new_total_weight = current_total_weight + weight

        if new_total_weight > 100:
            messages.error(
                request,
                f'Cannot update section: Total weight would be {new_total_weight}%, '
                f'which exceeds 100%. Current total (excluding this section): {current_total_weight}%'
            )
            return redirect('template_detail', template_id=template.id)

        # Update the section
        for section in sections:
            if section.get('id') == section_id:
                section['title'] = title
                section['content'] = content
                section['weight'] = weight
                break

        template.sections = sections
        template.save()

        messages.success(
            request,
            f'Section "{title}" updated successfully'
        )
        return redirect('template_detail', template_id=template.id)

    # If GET, redirect to template detail
    return redirect('template_detail', template_id=template.id)


@admin_or_interviewer_required
def delete_section(request, template_id, section_id):
    """
    Delete a section from a template.
    POST /templates/<id>/sections/<section_id>/delete/
    """
    template = get_object_or_404(
        InterviewTemplate,
        id=template_id,
        user=request.user
    )

    if request.method == 'POST':
        # Find and remove section
        sections = template.sections if template.sections else []
        original_length = len(sections)

        sections = [s for s in sections if s.get('id') != section_id]

        if len(sections) == original_length:
            messages.error(request, 'Section not found')
            return redirect('template_detail', template_id=template.id)

        # Reorder remaining sections
        for i, section in enumerate(sections):
            section['order'] = i

        template.sections = sections
        template.save()

        messages.success(request, 'Section deleted successfully')
        return redirect('template_detail', template_id=template.id)

    # If GET, redirect to template detail
    return redirect('template_detail', template_id=template.id)
