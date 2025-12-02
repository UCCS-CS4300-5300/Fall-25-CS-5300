import os
import filetype
import json
import pymupdf4llm
import tempfile
import textwrap
import re
import csv
import io
from datetime import timedelta
from markdownify import markdownify as md
from docx import Document

from .models import (
    UploadedResume, UploadedJobListing, Chat,
    ExportableReport, UserProfile, RoleChangeRequest,
    InterviewTemplate, DataExportRequest, DeletionRequest,
    InvitedInterview
)
from .forms import (
    CreateUserForm,
    CreateChatForm,
    EditChatForm,
    UploadFileForm,
    DocumentEditForm,
    JobPostingEditForm,
    InterviewTemplateForm,
    InvitationCreationForm
)
from .serializers import (
    UploadedResumeSerializer,
    UploadedJobListingSerializer
)
from .pdf_export import generate_pdf_report, get_score_rating
from .resume_parser import parse_resume_with_ai
from .job_listing_parser import parse_job_listing_with_ai
from .user_data_utils import (
    process_export_request,
    delete_user_account,
    generate_anonymized_id
)
from .invitation_utils import send_invitation_email


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
# Updated for Issue #14: Multi-tier model selection with automatic fallback
from .openai_utils import get_openai_client, get_client_and_model, ai_available, MAX_TOKENS

# Import token tracking (Issue #15.10)
from .token_tracking import record_openai_usage

# Import RBAC decorators (Issue #69)
from .decorators import (
    admin_required,
    admin_or_interviewer_required
)


def _ai_unavailable_json():
    """Return a JSON response for when AI features are disabled."""
    return JsonResponse(
        {'error': 'AI features are disabled on this server.'}, status=503)


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
    owner_chats = Chat.objects.filter(
        owner=request.user
    ).order_by('-modified_date')

    context = {}
    context['owner_chats'] = owner_chats

    return render(request, os.path.join('chat', 'chat-list.html'), context)


class CreateChat(LoginRequiredMixin, View):
    def get(self, request):
        owner_chats = Chat.objects.filter(
            owner=request.user
        ).order_by('-modified_date')

        # Pre-populate form from URL parameters (Issue #53)
        job_id = request.GET.get('job_id')
        template_id = request.GET.get('template_id')

        initial_data = {}

        # Pre-select job listing if provided
        if job_id:
            try:
                job_listing = UploadedJobListing.objects.get(
                    id=job_id, user=request.user
                )
                initial_data['listing_choice'] = job_listing
            except UploadedJobListing.DoesNotExist:
                pass  # Ignore invalid job_id

        # Set suggested template in context (not in form, just for display)
        suggested_template = None
        if template_id:
            try:
                suggested_template = InterviewTemplate.objects.get(
                    id=template_id, user=request.user
                )
            except InterviewTemplate.DoesNotExist:
                pass  # Ignore invalid template_id

        form = CreateChatForm(user=request.user, initial=initial_data)

        context = {
            'owner_chats': owner_chats,
            'form': form,
            'suggested_template': suggested_template,  # Issue #53
            'from_job_analysis': bool(job_id)  # Flag for UI
        }

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
                system_prompt = (
                    "An error has occurred.  Please notify the user about "
                    "this."
                )
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
                if not ai_available():
                    messages.error(
                        request, "AI features are disabled on this server.")
                    ai_message = ""
                else:
                    # Auto-select model tier based on spending cap (Issue #14)
                    client, model, tier_info = get_client_and_model()
                    response = client.chat.completions.create(
                        model=model,
                        messages=chat.messages,
                        max_tokens=MAX_TOKENS
                    )
                    # Track token usage for spending cap (Issue #15.10)
                    record_openai_usage(request.user, 'create_chat', response)
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
                if not ai_available():
                    messages.error(
                        request, "AI features are disabled on this server.")
                    ai_message = "[]"
                else:
                    # Auto-select model tier based on spending cap (Issue #14)
                    client, model, tier_info = get_client_and_model()
                    response = client.chat.completions.create(
                        model=model,
                        messages=timed_question_messages,
                        max_tokens=MAX_TOKENS
                    )
                    # Track token usage for spending cap (Issue #15.10)
                    record_openai_usage(request.user, 'create_chat_timed_questions', response)
                    ai_message = response.choices[0].message.content

                # Extract JSON array from the AI response
                match = re.search(r"(\[[\s\S]+\])", ai_message)
                if match:
                    cleaned_message = match.group(0).strip()
                    chat.key_questions = json.loads(cleaned_message)
                else:
                    # Fallback if regex doesn't match
                    messages.error(
                        request, "Failed to generate key questions. Please try again.")
                    chat.key_questions = []

                chat.save()

                return redirect("chat-view", chat_id=chat.id)
            else:
                # Form is invalid, render the form again with errors
                owner_chats = Chat.objects.filter(
                    owner=request.user).order_by('-modified_date')
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
        owner_chats = Chat.objects.filter(
            owner=request.user
        ).order_by('-modified_date')

        # Check if invited interview time has expired (Issue #138)
        time_expired = False
        if chat.interview_type == Chat.INVITED:
            time_expired = chat.is_time_expired()
            if time_expired:
                # Mark invitation as completed if not already
                try:
                    invitation = InvitedInterview.objects.get(chat=chat)
                    if invitation.status != InvitedInterview.COMPLETED:
                        invitation.status = InvitedInterview.COMPLETED
                        invitation.completed_at = timezone.now()
                        invitation.save()

                        # Send completion notification to interviewer
                        from .invitation_utils import send_completion_notification_email
                        send_completion_notification_email(invitation)
                except InvitedInterview.DoesNotExist:
                    pass

        context = {}
        context['chat'] = chat
        context['owner_chats'] = owner_chats
        context['time_expired'] = time_expired
        context['time_remaining'] = chat.time_remaining()

        return render(request, os.path.join('chat', 'chat-view.html'), context)

    def post(self, request, chat_id):
        chat = Chat.objects.get(id=chat_id)

        # Check if invited interview time has expired (Issue #138)
        if chat.interview_type == Chat.INVITED and chat.is_time_expired():
            # Mark invitation as completed if not already
            try:
                invitation = InvitedInterview.objects.get(chat=chat)
                if invitation.status != InvitedInterview.COMPLETED:
                    invitation.status = InvitedInterview.COMPLETED
                    invitation.completed_at = timezone.now()
                    invitation.save()

                    # Send completion notification to interviewer
                    from .invitation_utils import send_completion_notification_email
                    send_completion_notification_email(invitation)
            except InvitedInterview.DoesNotExist:
                pass

            return JsonResponse({
                'error': 'Interview time has expired',
                'time_expired': True
            }, status=403)

        user_message = request.POST.get('message', '')

        new_messages = chat.messages
        new_messages.append({"role": "user", "content": user_message})

        if not ai_available():
            return _ai_unavailable_json()

        # Phase 6-7: For invited interviews, check if we should ask another question
        # No new questions after T-5 minutes (graceful ending)
        should_end_interview = False
        if chat.interview_type == Chat.INVITED:
            time_remaining = chat.time_remaining()
            if time_remaining and time_remaining.total_seconds() < 300:  # Less than 5 mins
                should_end_interview = True

        if should_end_interview:
            # Don't ask new questions - thank candidate and end
            import textwrap
            ai_message = textwrap.dedent("""\
                Thank you for your response.

                The interview time window is ending, so this concludes our interview.
                Your responses will be reviewed and you'll receive feedback soon.

                Thank you for your time!
            """)

            # Add final message
            new_messages.append({"role": "assistant", "content": ai_message})
            chat.messages = new_messages
            chat.last_question_at = timezone.now()
            chat.save()

            # Auto-finalize
            if not chat.is_finalized:
                from .report_utils import generate_and_save_report
                try:
                    report = generate_and_save_report(chat, include_rushed_qualifier=True)
                    chat.is_finalized = True
                    chat.finalized_at = timezone.now()
                    chat.save()

                    # Phase 7: Update invitation status
                    try:
                        invitation = InvitedInterview.objects.get(chat=chat)
                        if invitation.status != InvitedInterview.COMPLETED:
                            invitation.status = InvitedInterview.COMPLETED
                            invitation.completed_at = timezone.now()
                            invitation.save()

                            from .invitation_utils import send_completion_notification_email
                            send_completion_notification_email(invitation)
                    except InvitedInterview.DoesNotExist:
                        pass
                except Exception:
                    # If report generation fails, still mark as finalized
                    chat.is_finalized = True
                    chat.finalized_at = timezone.now()
                    chat.save()

            return JsonResponse({
                'role': 'assistant',
                'content': ai_message,
                'interview_ended': True,
                'time_expired': True
            })

        # Normal flow - get AI response
        try:
            # Auto-select model tier based on spending cap (Issue #14)
            client, model, tier_info = get_client_and_model()
            response = client.chat.completions.create(
                model=model,
                messages=new_messages,
                max_tokens=MAX_TOKENS
            )
            # Track token usage for spending cap (Issue #15.10)
            record_openai_usage(request.user, 'chat_view', response)
            ai_message = response.choices[0].message.content
            new_messages.append({"role": "assistant", "content": ai_message})

            # Update last question time for invited interviews
            if chat.interview_type == Chat.INVITED:
                chat.last_question_at = timezone.now()

            chat.messages = new_messages
            chat.save()

            # Phase 8: Check if all questions answered and auto-finalize
            # NOTE: Only applies to practice interviews with key_questions
            # Invited interviews use time-based finalization (T-5, hard cutoff, abandonment)
            if chat.interview_type == Chat.PRACTICE and chat.all_questions_answered() and not chat.is_finalized:
                # For practice interviews: just signal completion, let user finalize manually
                return JsonResponse({
                    'message': ai_message,
                    'all_questions_answered': True,
                    'show_completion_message': True
                })

            return JsonResponse({'message': ai_message})
        except Exception as e:
            # Handle AI service exceptions gracefully
            return JsonResponse({
                'error': 'AI service unavailable',
                'message': str(e)
            }, status=503)


class EditChat(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # manually grab chat id from kwargs and process it
        chat = Chat.objects.get(id=self.kwargs['chat_id'])

        return self.request.user == chat.owner

    def get(self, request, chat_id):
        chat = Chat.objects.get(id=chat_id)
        owner_chats = Chat.objects.filter(
            owner=request.user
        ).order_by('-modified_date')

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
                chat.messages[0]['content'] = re.sub(
                    r"<<(\d{1,2})>>",
                    "<<" + str(chat.difficulty) + ">>",
                    chat.messages[0]['content'],
                    1
                )

                # print(chat.get_type_display())

                chat.save()

                return redirect("chat-view", chat_id=chat.id)

        # If 'update' not in request.POST or form is invalid, redirect to edit
        # page
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
        owner_chats = Chat.objects.filter(
            owner=request.user
        ).order_by('-modified_date')
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

        if not ai_available():
            return _ai_unavailable_json()

        # Auto-select model tier based on spending cap (Issue #14)
        client, model, tier_info = get_client_and_model()
        response = client.chat.completions.create(
            model=model,
            messages=ai_input,
            max_tokens=MAX_TOKENS
        )
        # Track token usage for spending cap (Issue #15.10)
        record_openai_usage(request.user, 'single_question', response)
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
        owner_chats = Chat.objects.filter(
            owner=request.user
        ).order_by('-modified_date')

        feedback_prompt = textwrap.dedent("""\
            Please provide constructive feedback to me about the
            interview so far.
        """)
        input_messages = chat.messages
        input_messages.append({"role": "user", "content": feedback_prompt})

        if not ai_available():
            ai_message = "AI features are currently unavailable."
        else:
            # Auto-select model tier based on spending cap (Issue #14)
            client, model, tier_info = get_client_and_model()
            response = client.chat.completions.create(
                model=model,
                messages=input_messages,
                max_tokens=MAX_TOKENS
            )
            # Track token usage for spending cap (Issue #15.10)
            record_openai_usage(request.user, 'results_chat', response)
            ai_message = response.choices[0].message.content

        # Check if this is an invited interview and get invitation details
        invitation = None
        if chat.interview_type == Chat.INVITED:
            try:
                invitation = InvitedInterview.objects.get(chat=chat)
            except InvitedInterview.DoesNotExist:
                pass

        context = {}
        context['chat'] = chat
        context['owner_chats'] = owner_chats
        context['feedback'] = ai_message
        context['invitation'] = invitation

        return render(request, os.path.join('chat', 'chat-results.html'),
                      context)


class ResultCharts(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # manually grab chat id from kwargs and process it
        chat = Chat.objects.get(id=self.kwargs['chat_id'])

        return self.request.user == chat.owner

    def get(self, request, chat_id):
        chat = Chat.objects.get(id=chat_id)
        owner_chats = Chat.objects.filter(
            owner=request.user
        ).order_by('-modified_date')

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

        if not ai_available():
            professionalism, subject_knowledge, clarity, overall = [0, 0, 0, 0]
        else:
            # Auto-select model tier based on spending cap (Issue #14)
            client, model, tier_info = get_client_and_model()
            response = client.chat.completions.create(
                model=model,
                messages=input_messages,
                max_tokens=MAX_TOKENS
            )
            # Track token usage for spending cap (Issue #15.10)
            record_openai_usage(request.user, 'result_charts_scores', response)
            ai_message = response.choices[0].message.content.strip()
            scores = [int(line.strip())
                      for line in ai_message.splitlines() if line.strip()
                      .isdigit()]
            if len(scores) == 4:
                professionalism, subject_knowledge, clarity, overall = scores
            else:
                professionalism, subject_knowledge, clarity, overall = [
                    0, 0, 0, 0]

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
        if not ai_available():
            ai_message = "AI features are currently unavailable."
        else:
            # Auto-select model tier based on spending cap (Issue #14)
            client, model, tier_info = get_client_and_model()
            response = client.chat.completions.create(
                model=model,
                messages=input_messages,
                max_tokens=MAX_TOKENS
            )
            # Track token usage for spending cap (Issue #15.10)
            record_openai_usage(request.user, 'result_charts_feedback', response)
            ai_message = response.choices[0].message.content
        context['feedback'] = ai_message

        # Check if this is an invited interview and get invitation details
        invitation = None
        if chat.interview_type == Chat.INVITED:
            try:
                invitation = InvitedInterview.objects.get(chat=chat)
            except InvitedInterview.DoesNotExist:
                pass
        context['invitation'] = invitation

        return render(request, os.path.join('chat', 'chat-results.html'),
                      context)


@login_required
def loggedin(request):
    return render(request, 'loggedinindex.html')


def register(request):
    # Preserve invitation context if coming from invitation link
    next_url = request.GET.get('next', '/')

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            group, created = Group.objects.get_or_create(name='average_role')
            user.groups.add(group)
            user.save()
            messages.success(request, 'Account was created for ' + username)

            # Redirect to next URL (invitation link) or login
            return redirect(f'/accounts/login/?next={next_url}')
    else:
        form = CreateUserForm()

    context = {
        'form': form,
        'next': next_url
    }
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

    # Get spending information (Issue #15.10)
    spending_data = None
    try:
        from .spending_tracker_models import MonthlySpending
        from .model_tier_manager import get_active_tier, TIER_TO_MODEL

        current_month = MonthlySpending.get_current_month()
        cap_status = current_month.get_cap_status()

        # Get currently active tier based on spending
        active_tier = get_active_tier()

        spending_data = {
            'total_cost': current_month.total_cost_usd,
            'llm_cost': current_month.llm_cost_usd,
            'tts_cost': current_month.tts_cost_usd,
            'total_requests': current_month.total_requests,
            'llm_requests': current_month.llm_requests,
            'cap_status': cap_status,
            'year': current_month.year,
            'month': current_month.month,
            # Tier breakdown
            'premium_cost': current_month.premium_cost_usd,
            'standard_cost': current_month.standard_cost_usd,
            'fallback_cost': current_month.fallback_cost_usd,
            'premium_requests': current_month.premium_requests,
            'standard_requests': current_month.standard_requests,
            'fallback_requests': current_month.fallback_requests,
            # Active tier and available models
            'active_tier': active_tier,
            'available_models': TIER_TO_MODEL,
        }
    except Exception:
        # Spending tracker not configured or error occurred
        spending_data = None

    return render(request, 'profile.html', {
        'resumes': resumes,
        'job_listings': job_listings,
        'templates': templates,
        'has_pending_request': has_pending_request,
        'spending_data': spending_data
    })


@login_required
def view_user_profile(request, user_id):
    """
    View another user's profile (read-only).
    Accessible by admins and interviewers.
    """
    from .decorators import check_user_permission
    from django.http import HttpResponseForbidden, Http404

    # Get user first (to return 404 if user doesn't exist)
    try:
        profile_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404("User not found")

    # Check permissions after confirming user exists
    has_permission = check_user_permission(
        request, user_id,
        allow_self=True,
        allow_admin=True,
        allow_interviewer=True
    )

    if not has_permission:
        return HttpResponseForbidden(
            "You don't have permission to view this profile.")

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
                        with tempfile.NamedTemporaryFile(
                            delete=False,
                            suffix=".pdf"
                        ) as temp_file:
                            for chunk in uploaded_file.chunks():
                                temp_file.write(chunk)
                            temp_file_path = temp_file.name
                        instance.content = pymupdf4llm.to_markdown(
                            temp_file_path)

                    elif file_type.extension == 'docx':
                        # Save temporarily and load using python-docx
                        with tempfile.NamedTemporaryFile(
                            delete=False,
                            suffix=".docx"
                        ) as temp_file:
                            for chunk in uploaded_file.chunks():
                                temp_file.write(chunk)
                            temp_file_path = temp_file.name

                        doc = Document(temp_file_path)
                        full_text = '\n'.join(
                            [para.text for para in doc.paragraphs])
                        instance.content = md(full_text)  # Convert to markdown

                    instance.save()

                    # Trigger AI parsing for resumes (Issue #48: "upload
                    # triggers parsing")
                    if instance.__class__.__name__ == 'UploadedResume':
                        if ai_available():
                            try:
                                # Set status to in_progress
                                instance.parsing_status = 'in_progress'
                                instance.save()

                                # Parse the resume
                                parsed_data = parse_resume_with_ai(
                                    instance.content)

                                # Save parsed data
                                instance.skills = parsed_data.get('skills', [])
                                instance.experience = parsed_data.get(
                                    'experience', [])
                                instance.education = parsed_data.get(
                                    'education', [])
                                instance.parsing_status = 'success'
                                instance.parsed_at = now()
                                instance.save()

                                messages.success(
                                    request, "Resume uploaded and parsed successfully!")
                            except Exception as e:
                                # Save error (sanitize to prevent API key
                                # exposure)
                                error_msg = str(e)
                                # Sanitize any potential API key references
                                if "api" in error_msg.lower() and "key" in error_msg.lower():
                                    error_msg = "OpenAI authentication error"
                                instance.parsing_status = 'error'
                                instance.parsing_error = error_msg
                                instance.save()
                                messages.warning(
                                    request, f"Resume uploaded but parsing failed: {error_msg}")
                        else:
                            # AI unavailable
                            instance.parsing_status = 'error'
                            instance.parsing_error = "AI service unavailable"
                            instance.save()
                            messages.warning(
                                request, "Resume uploaded but AI parsing is currently unavailable.")
                    else:
                        # Not a resume (job listing), just show success
                        messages.success(
                            request, "File uploaded successfully!")

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


def recommend_template_for_job(job_listing):
    """
    Recommend an interview template for a job listing based on:
    - Tags (match required skills to template tags)
    - Seniority level (match difficulty distribution)
    - User's existing templates

    Args:
        job_listing (UploadedJobListing): Job listing with parsed data

    Returns:
        InterviewTemplate or None: Best matching template, or None if no good match

    Issues: #21, #53
    """
    # Get user's templates with prefetched tags to avoid N+1 queries
    templates = InterviewTemplate.objects.filter(
        user=job_listing.user
    ).prefetch_related('tags')

    if not templates.exists():
        return None

    best_match = None
    best_score = 0

    for template in templates:
        score = 0

        # Match tags (skills) - worth up to 50 points
        template_tags = set(tag.name.lower().replace('#', '')
                            for tag in template.tags.all())
        if template_tags:
            job_skills = set(skill.lower()
                             for skill in job_listing.required_skills)
            matching_tags = template_tags & job_skills
            score += len(matching_tags) * 10  # 10 points per matching skill

        # Match difficulty distribution to seniority - worth up to 30 points
        if job_listing.seniority_level:
            if job_listing.seniority_level == 'entry' and template.easy_percentage > 40:
                score += 20
            elif job_listing.seniority_level == 'mid' and template.medium_percentage > 40:
                score += 20
            elif job_listing.seniority_level == 'senior' and template.hard_percentage > 30:
                score += 20
            elif job_listing.seniority_level == 'lead' and template.hard_percentage > 40:
                score += 25
            elif job_listing.seniority_level == 'executive' and template.hard_percentage > 50:
                score += 30

        # Bonus points for complete templates - worth up to 20 points
        if template.is_complete():
            score += 20

        if score > best_score:
            best_score = score
            best_match = template

    # Only return a match if the score is meaningful (at least 20 points)
    # This prevents recommending completely unrelated templates
    if best_score >= 20:
        return best_match

    return None


class JobListingAnalyzeView(APIView):
    """
    API endpoint to analyze job description and extract structured data.

    POST /api/job-listing/analyze/
    {
        "title": "Senior Python Developer",
        "description": "Job description text..."
    }

    Returns:
    {
        "id": 123,
        "title": "Senior Python Developer",
        "required_skills": ["Python", "Django", ...],
        "seniority_level": "senior",
        "requirements": {...},
        "recommended_template": {...},
        "parsing_status": "success"
    }

    Issues: #21, #51, #52, #53
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Validate input
        title = request.data.get('title', '').strip()
        description = request.data.get('description', '').strip()

        if not title or not description:
            return Response(
                {'error': 'Both title and description are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create UploadedJobListing with pending status
        job_listing = UploadedJobListing.objects.create(
            user=request.user,
            title=title,
            content=description,
            filename=f"{slugify(title)}.txt",
            parsing_status='in_progress'
        )

        try:
            # Call AI parser
            parsed_data = parse_job_listing_with_ai(description)

            # Update job listing with parsed data
            job_listing.required_skills = parsed_data['required_skills']
            job_listing.seniority_level = parsed_data['seniority_level']
            job_listing.requirements = parsed_data['requirements']
            job_listing.parsing_status = 'success'
            job_listing.parsed_at = timezone.now()

            # Recommend template
            recommended_template = recommend_template_for_job(job_listing)
            if recommended_template:
                job_listing.recommended_template = recommended_template

            job_listing.save()

            # Serialize and return
            serializer = UploadedJobListingSerializer(job_listing)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            # Parsing failed
            job_listing.parsing_status = 'error'
            job_listing.parsing_error = str(e)
            job_listing.save()

            return Response(
                {
                    'error': 'Failed to parse job description',
                    'detail': str(e),
                    'job_listing_id': job_listing.id
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            # Unexpected error
            job_listing.parsing_status = 'error'
            job_listing.parsing_error = f'Unexpected error: {str(e)}'
            job_listing.save()

            return Response(
                {
                    'error': 'An unexpected error occurred',
                    'detail': str(e),
                    'job_listing_id': job_listing.id
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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

        # Extract rationales for each score component
        rationales = self._extract_rationales_from_chat(chat, scores)
        report.professionalism_rationale = rationales.get(
            'professionalism', '')
        report.subject_knowledge_rationale = rationales.get(
            'subject_knowledge', '')
        report.clarity_rationale = rationales.get('clarity', '')
        report.overall_rationale = rationales.get('overall', '')

        # Calculate statistics
        chat_messages = chat.messages
        user_messages = [
            msg for msg in chat_messages if msg.get('role') == 'user']
        assistant_messages = [msg for msg in chat_messages
                              if msg.get('role') == 'assistant']

        report.total_questions_asked = len(assistant_messages)
        report.total_responses_given = len(user_messages)

        report.save()

        # Mark chat as finalized
        chat.is_finalized = True
        chat.finalized_at = timezone.now()
        chat.save()

        # For invited interviews: Update invitation status and send notification
        if chat.interview_type == Chat.INVITED:
            try:
                invitation = InvitedInterview.objects.get(chat=chat)
                if invitation.status != InvitedInterview.COMPLETED:
                    invitation.status = InvitedInterview.COMPLETED
                    invitation.completed_at = timezone.now()
                    invitation.save()

                    # Send completion notification to interviewer
                    from .invitation_utils import send_completion_notification_email
                    send_completion_notification_email(invitation)
            except InvitedInterview.DoesNotExist:
                pass

        messages.success(request, 'Interview finalized and report generated successfully!')
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

        if not ai_available():
            professionalism, subject_knowledge, clarity, overall = [0, 0, 0, 0]
        else:
            try:
                # Auto-select model tier based on spending cap (Issue #14)
                client, model, tier_info = get_client_and_model()
                response = client.chat.completions.create(
                    model=model,
                    messages=input_messages,
                    max_tokens=MAX_TOKENS
                )
                # Track token usage for spending cap (Issue #15.10)
                record_openai_usage(chat.owner, 'generate_report_scores', response)
                ai_message = response.choices[0].message.content.strip()
                scores = [int(line.strip())
                          for line in ai_message.splitlines() if line.strip()
                          .isdigit()]
                if len(scores) == 4:
                    professionalism, subject_knowledge, clarity, overall = scores
                else:
                    professionalism, subject_knowledge, clarity, overall = [
                        0, 0, 0, 0]
            except Exception:
                professionalism, subject_knowledge, clarity, overall = [
                    0, 0, 0, 0]

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

        if not ai_available():
            return "AI features are currently unavailable."

        try:
            # Auto-select model tier based on spending cap (Issue #14)
            client, model, tier_info = get_client_and_model()
            response = client.chat.completions.create(
                model=model,
                messages=input_messages,
                max_tokens=MAX_TOKENS
            )
            # Track token usage for spending cap (Issue #15.10)
            record_openai_usage(chat.owner, 'generate_report_feedback', response)
            return response.choices[0].message.content.strip()
        except Exception:
            return "Unable to generate feedback at this time."

    def _extract_rationales_from_chat(self, chat, scores):
        """
        Generate rationales for each score component using AI.
        Returns a dict with keys: professionalism, subject_knowledge, clarity, overall
        """
        rationale_prompt = textwrap.dedent(f"""\
            Based on the interview, please provide a brief rationale for each of the following scores.
            Format your response exactly as shown below:

            Professionalism: [Your explanation for the professionalism score of {scores.get('Professionalism', 0)}]

            Subject Knowledge: [Your explanation for the subject knowledge score of {scores.get('Subject Knowledge', 0)}]

            Clarity: [Your explanation for the clarity score of {scores.get('Clarity', 0)}]

            Overall: [Your explanation for the overall score of {scores.get('Overall', 0)}]
        """)

        input_messages = list(chat.messages)
        input_messages.append({"role": "user", "content": rationale_prompt})

        if not ai_available():
            return {
                'professionalism': 'AI features are currently unavailable.',
                'subject_knowledge': 'AI features are currently unavailable.',
                'clarity': 'AI features are currently unavailable.',
                'overall': 'AI features are currently unavailable.'
            }

        try:
            # Auto-select model tier based on spending cap (Issue #14)
            client, model, tier_info = get_client_and_model()
            response = client.chat.completions.create(
                model=model,
                messages=input_messages,
                max_tokens=MAX_TOKENS
            )
            # Track token usage for spending cap (Issue #15.10)
            record_openai_usage(chat.owner, 'generate_report_rationales', response)
            rationale_text = response.choices[0].message.content.strip()

            # Parse the rationale text to extract each component
            rationales = {
                'professionalism': '',
                'subject_knowledge': '',
                'clarity': '',
                'overall': ''
            }

            # Split by the section headers and extract content
            current_section = None
            current_text = []

            for line in rationale_text.split('\n'):
                line = line.strip()
                if not line:
                    continue

                if line.startswith('Professionalism:'):
                    if current_section and current_text:
                        rationales[current_section] = ' '.join(
                            current_text).strip()
                    current_section = 'professionalism'
                    current_text = [line.split(':', 1)[1].strip()]
                elif line.startswith('Subject Knowledge:'):
                    if current_section and current_text:
                        rationales[current_section] = ' '.join(
                            current_text).strip()
                    current_section = 'subject_knowledge'
                    current_text = [line.split(':', 1)[1].strip()]
                elif line.startswith('Clarity:'):
                    if current_section and current_text:
                        rationales[current_section] = ' '.join(
                            current_text).strip()
                    current_section = 'clarity'
                    current_text = [line.split(':', 1)[1].strip()]
                elif line.startswith('Overall:'):
                    if current_section and current_text:
                        rationales[current_section] = ' '.join(
                            current_text).strip()
                    current_section = 'overall'
                    current_text = [line.split(':', 1)[1].strip()]
                elif current_section:
                    # This is a continuation of the current section
                    current_text.append(line)

            # Don't forget the last section
            if current_section and current_text:
                rationales[current_section] = ' '.join(current_text).strip()

            return rationales

        except Exception:
            # If rationale generation fails, provide fallback text
            return {
                'professionalism': 'Unable to generate rationale at this time.',
                'subject_knowledge': 'Unable to generate rationale at this time.',
                'clarity': 'Unable to generate rationale at this time.',
                'overall': 'Unable to generate rationale at this time.'}

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
                    if (i + 2 < len(chat_messages) and
                            chat_messages[i + 2].get('role') == 'assistant'):
                        feedback_msg = chat_messages[i + 2].get('content', '')
                        # Look for score in feedback
                        score_match = re.search(r'(\d+)/10', feedback_msg)
                        if score_match:
                            qa_pair['score'] = int(score_match.group(1))
                            qa_pair['feedback'] = feedback_msg[:300]

                    qa_pairs.append(qa_pair)

        return qa_pairs


class FinalizeInterviewView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to finalize an interview and generate its ExportableReport.

    This view is called when a user is ready to finalize their interview.
    Once finalized:
    - An ExportableReport is generated using AI analysis (ONCE)
    - The chat is marked as finalized (is_finalized=True)
    - For invited interviews, the invitation status is updated to COMPLETED
    - The report cannot be regenerated (immutable)

    Related to: Report Generation Refactor (Phase 3)
    """

    def test_func(self):
        """Verify that the user owns the chat"""
        chat = get_object_or_404(Chat, id=self.kwargs['chat_id'])
        return self.request.user == chat.owner

    def post(self, request, chat_id):
        """Finalize the interview and generate the report"""
        chat = get_object_or_404(Chat, id=chat_id)

        # Check if already finalized
        if chat.is_finalized:
            messages.info(request, 'This interview has already been finalized.')
            return redirect('export_report', chat_id=chat_id)

        # Check if report already exists (defensive - shouldn't happen)
        existing_report = ExportableReport.objects.filter(chat=chat).first()
        if existing_report:
            messages.info(request, 'A report already exists for this interview.')
            return redirect('export_report', chat_id=chat_id)

        # Generate report using shared utility (makes 4 AI calls)
        from .report_utils import generate_and_save_report
        report = generate_and_save_report(chat)

        # Mark chat as finalized
        chat.is_finalized = True
        chat.finalized_at = timezone.now()
        chat.save()

        # For invited interviews: Update invitation status and send notification
        if chat.interview_type == Chat.INVITED:
            try:
                invitation = InvitedInterview.objects.get(chat=chat)
                if invitation.status != InvitedInterview.COMPLETED:
                    invitation.status = InvitedInterview.COMPLETED
                    invitation.completed_at = timezone.now()
                    invitation.save()

                    # Send completion notification to interviewer
                    from .invitation_utils import send_completion_notification_email
                    send_completion_notification_email(invitation)
            except InvitedInterview.DoesNotExist:
                pass

        messages.success(request, 'Interview finalized and report generated successfully!')
        return redirect('export_report', chat_id=chat_id)


class ExportReportView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to display and allow exporting of a generated report.
    Shows report details and provides download options.
    """

    def test_func(self):
        """Verify that the user owns the chat or is the interviewer"""
        chat = get_object_or_404(Chat, id=self.kwargs['chat_id'])

        # Allow chat owner (candidate)
        if self.request.user == chat.owner:
            return True

        # Allow interviewer for invited interviews
        if chat.interview_type == Chat.INVITED:
            try:
                invitation = InvitedInterview.objects.get(chat=chat)
                return self.request.user == invitation.interviewer
            except InvitedInterview.DoesNotExist:
                pass

        return False

    def get(self, request, chat_id):
        """Display the exportable report"""
        chat = get_object_or_404(Chat, id=chat_id)

        try:
            report = ExportableReport.objects.get(chat=chat)
        except ExportableReport.DoesNotExist:
            messages.warning(request,
                             'No report exists yet. Generating one now...')
            return redirect('generate_report', chat_id=chat_id)

        # Get invitation if this is an invited interview
        invitation = None
        if chat.interview_type == Chat.INVITED:
            try:
                invitation = InvitedInterview.objects.get(chat=chat)
            except InvitedInterview.DoesNotExist:
                pass

        context = {
            'chat': chat,
            'report': report,
            'invitation': invitation,
        }
        return render(request, 'reports/export-report.html', context)


class DownloadPDFReportView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to download a PDF version of the exportable report.
    """

    def test_func(self):
        """Verify that the user owns the chat or is the interviewer"""
        chat = get_object_or_404(Chat, id=self.kwargs['chat_id'])

        # Allow chat owner (candidate)
        if self.request.user == chat.owner:
            return True

        # Allow interviewer for invited interviews
        if chat.interview_type == Chat.INVITED:
            try:
                invitation = InvitedInterview.objects.get(chat=chat)
                return self.request.user == invitation.interviewer
            except InvitedInterview.DoesNotExist:
                pass

        return False

    def get(self, request, chat_id):
        """Generate and download PDF report"""
        chat = get_object_or_404(Chat, id=chat_id)

        try:
            report = ExportableReport.objects.get(chat=chat)
        except ExportableReport.DoesNotExist:
            messages.error(
                request, 'No report exists. Please generate one first.')
            return redirect('chat-results', chat_id=chat_id)

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


class DownloadCSVReportView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to download a CSV version of the exportable report.
    """

    def test_func(self):
        """Verify that the user owns the chat or is the interviewer"""
        chat = get_object_or_404(Chat, id=self.kwargs['chat_id'])

        # Allow chat owner (candidate)
        if self.request.user == chat.owner:
            return True

        # Allow interviewer for invited interviews
        if chat.interview_type == Chat.INVITED:
            try:
                invitation = InvitedInterview.objects.get(chat=chat)
                return self.request.user == invitation.interviewer
            except InvitedInterview.DoesNotExist:
                pass

        return False

    def get(self, request, chat_id):
        """Generate and download CSV report"""
        chat = get_object_or_404(Chat, id=chat_id)

        try:
            report = ExportableReport.objects.get(chat=chat)
        except ExportableReport.DoesNotExist:
            messages.error(
                request, 'No report exists. Please generate one first.')
            return redirect('chat-results', chat_id=chat_id)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['Interview Report'])
        writer.writerow([''])

        # Write Interview Details section
        writer.writerow(['Interview Details'])
        writer.writerow(['Title', chat.title])
        writer.writerow(['Generated At',
                         report.generated_at.strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Difficulty', f'{chat.difficulty}/10'])

        # Add job listing and resume if present
        if chat.job_listing:
            writer.writerow(['Job Listing', chat.job_listing.title])
        if chat.resume:
            writer.writerow(['Resume', chat.resume.title])

        # Add interview duration if present
        if report.interview_duration_minutes:
            writer.writerow(
                ['Duration', f'{report.interview_duration_minutes} minutes'])

        writer.writerow([''])

        # Write scores with ratings and weights
        writer.writerow(['Scores'])
        writer.writerow(['Category', 'Score', 'Rating', 'Weight'])

        if report.professionalism_score is not None:
            writer.writerow([
                'Professionalism',
                f'{report.professionalism_score}/100',
                get_score_rating(report.professionalism_score),
                f'{report.professionalism_weight}%'
            ])

        if report.subject_knowledge_score is not None:
            writer.writerow([
                'Subject Knowledge',
                f'{report.subject_knowledge_score}/100',
                get_score_rating(report.subject_knowledge_score),
                f'{report.subject_knowledge_weight}%'
            ])

        if report.clarity_score is not None:
            writer.writerow([
                'Clarity',
                f'{report.clarity_score}/100',
                get_score_rating(report.clarity_score),
                f'{report.clarity_weight}%'
            ])

        if report.overall_score is not None:
            writer.writerow([
                'Overall Score',
                f'{report.overall_score}/100',
                get_score_rating(report.overall_score),
                ''
            ])

        writer.writerow([''])

        # Write Score Breakdown & Rationales section
        writer.writerow(['Score Breakdown & Rationales'])
        writer.writerow([''])

        if report.professionalism_rationale:
            writer.writerow(['Professionalism Rationale'])
            writer.writerow([report.professionalism_rationale])
            writer.writerow([''])

        if report.subject_knowledge_rationale:
            writer.writerow(['Subject Knowledge Rationale'])
            writer.writerow([report.subject_knowledge_rationale])
            writer.writerow([''])

        if report.clarity_rationale:
            writer.writerow(['Clarity Rationale'])
            writer.writerow([report.clarity_rationale])
            writer.writerow([''])

        if report.overall_rationale:
            writer.writerow(['Overall Rationale'])
            writer.writerow([report.overall_rationale])
            writer.writerow([''])

        # Write feedback
        writer.writerow(['Feedback'])
        writer.writerow([report.feedback_text])
        writer.writerow([''])

        # Write statistics
        writer.writerow(['Statistics'])
        writer.writerow(
            ['Total Questions Asked', report.total_questions_asked])
        writer.writerow(
            ['Total Responses Given', report.total_responses_given])

        # Create response
        csv_content = output.getvalue()
        response = HttpResponse(csv_content, content_type='text/csv')
        filename = f"interview_report_{slugify(chat.title)}_{report.generated_at.strftime('%Y%m%d')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

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
        form = InterviewTemplateForm(
            request.POST, instance=template, user=request.user)
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
                request, f'Cannot add section: Total weight would be {new_total_weight}%, '
                f'which exceeds 100%. Current total: {current_total_weight}%')
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

        for section in sections:
            if section.get('id') == section_id:
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
                request, f'Cannot update section: Total weight would be {new_total_weight}%, '
                f'which exceeds 100%. Current total (excluding this section): {current_total_weight}%')
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


# ============================================================================
# USER DATA EXPORT & DELETION VIEWS (Issues #63, #64, #65)
# ============================================================================

@login_required
def request_data_export(request):
    """
    Request a data export (GDPR/CCPA compliance).
    Creates a DataExportRequest and processes it asynchronously.

    GET: Show confirmation page
    POST: Create export request and redirect to status page

    Related to Issue #64 (Data Export Functionality).
    """
    if request.method == 'POST':
        # Check for existing pending/processing requests
        existing = DataExportRequest.objects.filter(
            user=request.user,
            status__in=[DataExportRequest.PENDING,
                        DataExportRequest.PROCESSING]
        ).first()

        if existing:
            messages.info(
                request,
                'You already have a pending data export request. '
                'Please wait for it to complete.'
            )
            return redirect('data_export_status', request_id=existing.id)

        # Create new export request
        export_request = DataExportRequest.objects.create(user=request.user)

        # Process the request (in production, this would be async with Celery)
        # For now, process synchronously
        process_export_request(export_request)

        messages.success(
            request,
            'Your data export request has been submitted. '
            'You will receive an email when it is ready.'
        )

        return redirect('data_export_status', request_id=export_request.id)

    # GET request - show confirmation page
    context = {
        'recent_exports': DataExportRequest.objects.filter(
            user=request.user
        ).order_by('-requested_at')[:5]
    }

    return render(request, 'user_data/request_export.html', context)


@login_required
def data_export_status(request, request_id):
    """
    View status of a data export request.

    Args:
        request_id: DataExportRequest ID

    Related to Issue #64 (Data Export Functionality).
    """
    export_request = get_object_or_404(
        DataExportRequest,
        id=request_id,
        user=request.user
    )

    # Check if expired
    is_expired = export_request.is_expired()
    if is_expired and export_request.status == DataExportRequest.COMPLETED:
        export_request.status = DataExportRequest.EXPIRED
        export_request.save()

    context = {
        'export_request': export_request,
        'is_expired': is_expired,
    }

    return render(request, 'user_data/export_status.html', context)


@login_required
def download_data_export(request, request_id):
    """
    Download a completed data export file.

    Args:
        request_id: DataExportRequest ID

    Returns:
        FileResponse with ZIP file

    Related to Issue #64 (Data Export Functionality).
    """
    export_request = get_object_or_404(
        DataExportRequest,
        id=request_id,
        user=request.user
    )

    # Check if export is completed
    if export_request.status != DataExportRequest.COMPLETED:
        messages.error(request, 'Export is not ready yet.')
        return redirect('data_export_status', request_id=request_id)

    # Check if expired
    if export_request.is_expired():
        export_request.status = DataExportRequest.EXPIRED
        export_request.save()
        messages.error(
            request,
            'This export link has expired. Please request a new export.'
        )
        return redirect('data_export_status', request_id=request_id)

    # Check if file exists
    if not export_request.export_file:
        messages.error(request, 'Export file not found.')
        return redirect('data_export_status', request_id=request_id)

    # Mark as downloaded
    export_request.mark_downloaded()

    # Serve file
    response = FileResponse(
        export_request.export_file.open('rb'),
        as_attachment=True,
        filename=os.path.basename(export_request.export_file.name)
    )

    return response


@login_required
def request_account_deletion(request):
    """
    Request account deletion (GDPR/CCPA Right to be Forgotten).

    GET: Show confirmation page with warnings
    POST: Show password confirmation

    Related to Issue #65 (Data Deletion & Anonymization).
    """
    if request.method == 'POST':
        # This just shows the confirmation dialog
        # Actual deletion happens in confirm_account_deletion
        return render(request, 'user_data/confirm_deletion.html', {
            'user': request.user,
        })

    # GET request - show information page
    context = {
        'user': request.user,
        'resume_count': UploadedResume.objects.filter(user=request.user).count(),
        'job_count': UploadedJobListing.objects.filter(user=request.user).count(),
        'interview_count': Chat.objects.filter(owner=request.user).count(),
    }

    return render(request, 'user_data/request_deletion.html', context)


@login_required
def confirm_account_deletion(request):
    """
    Confirm and execute account deletion.
    Requires password verification for security.

    POST only: Verify password and delete account

    Related to Issue #65 (Data Deletion & Anonymization).
    """
    if request.method != 'POST':
        return redirect('request_account_deletion')

    # Verify password
    password = request.POST.get('password', '')
    if not request.user.check_password(password):
        messages.error(
            request, 'Incorrect password. Account deletion cancelled.')
        return redirect('request_account_deletion')

    # Create deletion audit record
    anonymized_id = generate_anonymized_id(request.user)
    deletion_request = DeletionRequest.objects.create(
        anonymized_user_id=anonymized_id,
        username=request.user.username,
        email=request.user.email,
        status=DeletionRequest.PENDING,
    )

    # Perform deletion
    success, error = delete_user_account(request.user, deletion_request)

    if success:
        # User is deleted, so we can't redirect to a logged-in page
        # Render a static success page
        return render(request, 'user_data/deletion_complete.html', {
            'username': deletion_request.username,
        })
    else:
        messages.error(
            request,
            f'An error occurred during account deletion: {error}. '
            'Please contact support.'
        )
        return redirect('profile')


@login_required
def user_data_settings(request):
    """
    Main page for user data management settings.
    Shows options for data export and account deletion.

    Related to Issue #63 (GDPR/CCPA Data Export & Delete).
    """
    context = {
        'user': request.user,
        'recent_exports': DataExportRequest.objects.filter(
            user=request.user
        ).order_by('-requested_at')[:3],
        'has_pending_export': DataExportRequest.objects.filter(
            user=request.user,
            status__in=[DataExportRequest.PENDING,
                        DataExportRequest.PROCESSING]
        ).exists(),
    }

    return render(request, 'user_data/settings.html', context)


# ============================================================================
# INVITATION VIEWS (Issue #4: Interview Invitation Workflow)
# ============================================================================

@login_required
@admin_or_interviewer_required
def invitation_create(request, template_id=None):
    """
    Create a new interview invitation.
    Can be accessed from template detail page (with template_id) or
    from the invitation dashboard (without template_id).

    Related to Issue #5 (Create Interview Invitation).
    """
    # Permission already checked by @admin_or_interviewer_required decorator

    if request.method == 'POST':
        form = InvitationCreationForm(
            request.POST,
            user=request.user,
            template_id=template_id
        )

        if form.is_valid():
            # Create invitation but don't save yet
            invitation = form.save(commit=False)
            invitation.interviewer = request.user

            # Get combined datetime from form's clean method
            scheduled_datetime = form.cleaned_data.get('scheduled_datetime')
            invitation.scheduled_time = scheduled_datetime

            # Save invitation
            invitation.save()

            # Send invitation email with calendar attachment
            email_sent = send_invitation_email(invitation)

            # Mark invitation as sent
            if email_sent:
                invitation.invitation_sent_at = timezone.now()
                invitation.save()
                messages.success(
                    request,
                    f'Invitation sent to {invitation.candidate_email}'
                )
            else:
                messages.warning(
                    request,
                    f'Invitation created but email failed to send. Join link: {invitation.get_join_url()}'
                )

            # Redirect to confirmation page
            return redirect(
                'invitation_confirmation',
                invitation_id=invitation.id)
    else:
        # GET request - show form
        form = InvitationCreationForm(
            user=request.user,
            template_id=template_id
        )

    # Get template if template_id provided (for context)
    template = None
    if template_id:
        template = get_object_or_404(
            InterviewTemplate,
            id=template_id,
            user=request.user
        )

    context = {
        'form': form,
        'template': template,
    }

    return render(request, 'invitations/invitation_create.html', context)


@login_required
@admin_or_interviewer_required
def invitation_confirmation(request, invitation_id):
    """
    Show confirmation page after successfully creating an invitation.

    Related to Issue #9 (Interview Confirmation Page).
    """
    # Get invitation and verify ownership
    invitation = get_object_or_404(
        InvitedInterview,
        id=invitation_id,
        interviewer=request.user
    )

    context = {
        'invitation': invitation,
        'join_url': invitation.get_join_url(),
        'window_end': invitation.get_window_end(),
    }

    return render(request, 'invitations/invitation_confirmation.html', context)


@login_required
@admin_or_interviewer_required
def invitation_dashboard(request):
    """
    Dashboard for managing all interview invitations sent by the user.
    Supports filtering by status.

    Related to Issue #134 (Invitation Management Dashboard).
    """
    # Get filter parameter from query string
    status_filter = request.GET.get('status', 'all')

    # Get all invitations for this user
    invitations = InvitedInterview.objects.filter(
        interviewer=request.user
    ).select_related('template', 'chat').order_by('-created_at')

    # Apply status filter
    if status_filter and status_filter != 'all':
        invitations = invitations.filter(status=status_filter)

    # Get counts for each status (for filter badges)
    all_invitations = InvitedInterview.objects.filter(interviewer=request.user)
    status_counts = {
        'all': all_invitations.count(),
        'pending': all_invitations.filter(status=InvitedInterview.PENDING).count(),
        'completed': all_invitations.filter(status=InvitedInterview.COMPLETED).count(),
        'reviewed': all_invitations.filter(status=InvitedInterview.REVIEWED).count(),
        'expired': all_invitations.filter(status=InvitedInterview.EXPIRED).count(),
    }

    context = {
        'invitations': invitations,
        'status_filter': status_filter,
        'status_counts': status_counts,
    }

    return render(request, 'invitations/invitation_dashboard.html', context)


@login_required
@admin_or_interviewer_required
def invitation_review(request, invitation_id):
    """
    Interviewer review page for a completed invited interview.

    Shows:
    - Interview metadata
    - Candidate responses (from Chat messages)
    - AI feedback and scores
    - Form for interviewer to add feedback
    - Button to mark as reviewed

    Only accessible by the interviewer who created the invitation.

    Related to Issue #138 (Interviewer Review & Feedback).
    """
    # Get invitation and verify ownership
    invitation = get_object_or_404(
        InvitedInterview,
        id=invitation_id,
        interviewer=request.user
    )

    # Check if interview has been completed
    if not invitation.chat:
        messages.error(request, 'This interview has not been started yet.')
        return redirect('invitation_dashboard')

    # Get the chat/interview session
    chat = invitation.chat

    # Handle POST request (submitting feedback)
    if request.method == 'POST':
        feedback = request.POST.get('interviewer_feedback', '').strip()
        mark_reviewed = request.POST.get('mark_reviewed') == 'true'

        # Save feedback
        if feedback:
            invitation.interviewer_feedback = feedback

        # Mark as reviewed if requested
        if mark_reviewed:
            invitation.interviewer_review_status = InvitedInterview.REVIEW_COMPLETED
            invitation.status = InvitedInterview.REVIEWED
            invitation.reviewed_at = timezone.now()

            # Send notification email to candidate
            from .invitation_utils import send_review_notification_email
            send_review_notification_email(invitation)

            messages.success(
                request, 'Review completed! Notification sent to candidate.')
        else:
            messages.success(request, 'Feedback saved.')

        invitation.save()
        return redirect('invitation_dashboard')

    # GET request - show review page
    context = {
        'invitation': invitation,
        'chat': chat,
    }

    return render(request, 'invitations/invitation_review.html', context)


# ============================================================================
# CANDIDATE INVITATION VIEWS (Issue #4: Candidate Experience)
# ============================================================================

def invitation_join(request, invitation_id):
    """
    Handle candidate clicking on invitation join link.

    - If not authenticated: redirect to registration with next parameter
    - If authenticated but not matching email: show error
    - If authenticated and matching email: show interview detail page

    Related to Issue #135 (Registration Redirect Flow).
    """
    # Get invitation or 404
    invitation = get_object_or_404(InvitedInterview, id=invitation_id)

    # If user not authenticated, redirect to registration
    if not request.user.is_authenticated:
        # Build the join URL to redirect back to after registration/login
        join_url = f'/interview/invite/{invitation_id}/'
        messages.info(
            request,
            'Please register or log in to access your interview invitation.'
        )
        return redirect(f'/register/?next={join_url}')

    # User is authenticated - verify they're the invited candidate
    # Check if user's email matches invitation email
    if request.user.email.lower() != invitation.candidate_email.lower():
        messages.error(
            request,
            'This invitation was sent to a different email address. '
            'Please log in with the correct account.'
        )
        return redirect('index')

    # User is authenticated and email matches - redirect to interview detail
    return redirect('invited_interview_detail', invitation_id=invitation.id)


@login_required
def invited_interview_detail(request, invitation_id):
    """
    Show interview detail page with time-gated access.

    Candidates can view details but cannot start until scheduled time.
    Shows different states based on current time and invitation status.

    Related to Issues #136 (Time-Gated Access), #140 (Duration Enforcement).
    """
    # Get invitation and verify user
    invitation = get_object_or_404(InvitedInterview, id=invitation_id)

    # Verify user is the invited candidate
    if request.user.email.lower() != invitation.candidate_email.lower():
        messages.error(
            request, 'You do not have permission to access this interview.')
        return redirect('index')

    # Calculate time-related info
    now = timezone.now()
    window_end = invitation.get_window_end()
    can_start = invitation.can_start()
    is_expired = invitation.is_expired()
    is_accessible = invitation.is_accessible()

    # Calculate time until start (if not started yet)
    time_until_start = None
    if now < invitation.scheduled_time:
        time_until_start = invitation.scheduled_time - now

    # Calculate time remaining (if in window)
    time_remaining = None
    if invitation.scheduled_time <= now <= window_end and not invitation.chat:
        time_remaining = window_end - now

    context = {
        'invitation': invitation,
        'window_end': window_end,
        'can_start': can_start,
        'is_expired': is_expired,
        'is_accessible': is_accessible,
        'time_until_start': time_until_start,
        'time_remaining': time_remaining,
        'now': now,
    }

    return render(
        request,
        'invitations/invited_interview_detail.html',
        context)


@login_required
def candidate_invitations(request):
    """
    Show all invitations for the current user (as candidate).

    Displays invitations sent to the user's email address with status filtering.

    Sorting order (when status_filter='all'):
    1. Pending (sorted by soonest scheduled_time)
    2. Completed (sorted by most recent completed_at)
    3. Reviewed (sorted by most recent completed_at)
    4. Expired (sorted by most recent scheduled_time)

    When filtering by specific status, applies appropriate sorting for that status.
    """
    # Get filter parameter from query string
    status_filter = request.GET.get('status', 'all')

    # Get all invitations for this user's email
    invitations = InvitedInterview.objects.filter(
        candidate_email__iexact=request.user.email
    ).select_related('template', 'chat', 'interviewer')

    # Apply status filter
    if status_filter and status_filter != 'all':
        invitations = invitations.filter(status=status_filter)

    # Apply custom sorting
    invitations_list = list(invitations)

    if status_filter == 'all':
        # Custom sorting for 'all' view:
        # Group by status with specific order, then sort within each group
        def sort_key(invitation):
            # Status priority order: pending=1, completed=2, reviewed=3,
            # expired=4
            status_priority = {
                InvitedInterview.PENDING: 1,
                InvitedInterview.COMPLETED: 2,
                InvitedInterview.REVIEWED: 3,
                InvitedInterview.EXPIRED: 4,
            }

            priority = status_priority.get(invitation.status, 5)

            # Within-status sorting
            if invitation.status == InvitedInterview.PENDING:
                # Sort by soonest scheduled_time (ascending)
                return (priority, invitation.scheduled_time)
            elif invitation.status in [InvitedInterview.COMPLETED, InvitedInterview.REVIEWED]:
                # Sort by most recent completed_at (descending)
                # Use negative timestamp for descending order
                completed_time = invitation.completed_at or invitation.created_at
                return (priority, -completed_time.timestamp())
            elif invitation.status == InvitedInterview.EXPIRED:
                # Sort by most recent scheduled_time (descending)
                return (priority, -invitation.scheduled_time.timestamp())
            else:
                # Fallback
                return (priority, -invitation.created_at.timestamp())

        invitations_list.sort(key=sort_key)

    elif status_filter == 'pending':
        # Sort pending by soonest scheduled_time
        invitations_list.sort(key=lambda inv: inv.scheduled_time)

    elif status_filter in ['completed', 'reviewed']:
        # Sort completed/reviewed by most recent completed_at
        invitations_list.sort(
            key=lambda inv: inv.completed_at or inv.created_at,
            reverse=True
        )

    elif status_filter == 'expired':
        # Sort expired by most recent scheduled_time
        invitations_list.sort(key=lambda inv: inv.scheduled_time, reverse=True)

    # Get counts for each status (for filter badges)
    all_invitations = InvitedInterview.objects.filter(
        candidate_email__iexact=request.user.email
    )
    status_counts = {
        'all': all_invitations.count(),
        'pending': all_invitations.filter(status=InvitedInterview.PENDING).count(),
        'completed': all_invitations.filter(
            status=InvitedInterview.COMPLETED
        ).count(),
        'reviewed': all_invitations.filter(status=InvitedInterview.REVIEWED).count(),
        'expired': all_invitations.filter(status=InvitedInterview.EXPIRED).count(),
    }

    context = {
        'invitations': invitations_list,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'is_candidate_view': True,  # Flag to differentiate from interviewer view
    }

    return render(request, 'invitations/candidate_invitations.html', context)


@login_required
def start_invited_interview(request, invitation_id):
    """
    Start an invited interview by creating a Chat session.

    Verifies time window and user permissions before creating the chat.

    Related to Issue #136 (Time-Gated Access).
    """
    # Get invitation and verify user
    invitation = get_object_or_404(InvitedInterview, id=invitation_id)

    # Verify user is the invited candidate
    if request.user.email.lower() != invitation.candidate_email.lower():
        messages.error(
            request, 'You do not have permission to start this interview.')
        return redirect('index')

    # Check if already started
    if invitation.chat:
        messages.info(request, 'This interview has already been started.')
        return redirect('chat-view', chat_id=invitation.chat.id)

    # Check if can start (time window validation)
    if not invitation.can_start():
        if invitation.is_expired():
            messages.error(
                request,
                'This interview time has passed and you can no longer take it.'
            )
        else:
            messages.error(
                request,
                f'This interview cannot be started until {invitation.scheduled_time.strftime("%B %d, %Y at %I:%M %p")}.'
            )
        return redirect(
            'invited_interview_detail',
            invitation_id=invitation.id)

    # Create Chat session with time tracking (Issue #138)
    now = timezone.now()
    scheduled_end = now + timedelta(minutes=invitation.duration_minutes)

    chat = Chat.objects.create(
        owner=request.user,
        title=f"{invitation.template.name} - Invited Interview",
        interview_type=Chat.INVITED,
        type=Chat.GENERAL,  # Or inherit from template if available
        started_at=now,
        scheduled_end_at=scheduled_end,
    )

    # Initialize interview with system prompt based on template sections
    template = invitation.template
    sections = template.sections if template.sections else []

    # Build system prompt from template sections
    sections_content = ""
    if sections:
        # Sort sections by order
        sorted_sections = sorted(sections, key=lambda s: s.get('order', 0))
        for section in sorted_sections:
            title = section.get('title', 'Untitled Section')
            content = section.get('content', '')
            weight = section.get('weight', 0)
            sections_content += f"\n## {title} (Weight: {weight}%)\n{content}\n"

    system_prompt = textwrap.dedent("""\
        You are a professional interviewer conducting a structured interview.

        # Interview Template: {template_name}
        {template_description}

        # Interview Duration
        This interview has a time limit of {duration} minutes.

        # Interview Structure
        The interview is organized into the following sections:
        {sections_content}

        # CRITICAL INSTRUCTIONS - READ CAREFULLY
        - ONLY greet the candidate briefly and ask ONE question at a time
        - DO NOT list all the sections or questions upfront
        - DO NOT provide an agenda or overview of the interview
        - Start with a brief greeting, then immediately ask your first question from the first section
        - Wait for the candidate's response before asking the next question
        - Ask questions one at a time, conversationally
        - Progress through sections naturally based on their order and weight
        - Keep your responses concise - this is an interview, not a lecture
        - Be professional and encouraging in your tone
        - At the very end (after all sections), thank the candidate briefly

        IMPORTANT: This is a conversational interview. Ask questions one by one,
        listen to responses, and follow up naturally. Do NOT dump all questions
        at once or provide a roadmap of the interview.

        Respond critically to any responses that are off-topic or ignore
        the fact that the user is in an interview. The candidate should
        focus on answering interview questions, not asking for general
        AI assistance.
    """).format(
        template_name=template.name,
        template_description=f"\n{template.description}" if template.description else "",
        duration=invitation.duration_minutes,
        sections_content=sections_content if sections_content else "\n(No specific sections defined)"
    )

    chat.messages = [
        {
            "role": "system",
            "content": system_prompt
        },
    ]

    # Get AI's initial greeting
    if not ai_available():
        messages.error(request, "AI features are disabled on this server.")
        ai_message = (
            "Hello! I'm your interviewer today. Unfortunately, AI "
            "features are currently disabled. Please contact support."
        )
    else:
        # Auto-select model tier based on spending cap (Issue #14)
        client, model, tier_info = get_client_and_model()
        response = client.chat.completions.create(
            model=model,
            messages=chat.messages,
            max_tokens=MAX_TOKENS
        )
        # Track token usage for spending cap (Issue #15.10)
        record_openai_usage(request.user, 'start_invited_interview', response)
        ai_message = response.choices[0].message.content

    chat.messages.append(
        {
            "role": "assistant",
            "content": ai_message
        }
    )

    chat.save()

    # Link chat to invitation
    invitation.chat = chat
    invitation.save()

    messages.success(request, 'Interview started! Good luck!')
    return redirect('chat-view', chat_id=chat.id)
