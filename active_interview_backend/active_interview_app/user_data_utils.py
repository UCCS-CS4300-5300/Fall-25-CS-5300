"""
Utility functions for user data export and deletion.
Implements GDPR/CCPA compliance features.

Related to Issues #63, #64, #65 (User Data Export & Deletion).
"""

import csv
import hashlib
import io
import json
import logging
import os
import zipfile
from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from .constants import (
    EXPORT_EXPIRATION_DAYS,
    EXPORT_FILE_PREFIX,
    EMAIL_FAIL_SILENTLY
)
from .models import (
    Chat,
    DataExportRequest,
    DeletionRequest,
    InterviewTemplate,
    RoleChangeRequest,
    UploadedJobListing,
    UploadedResume
)

# Configure logger
logger = logging.getLogger(__name__)


def generate_anonymized_id(user):
    """
    Generate an anonymized identifier for a user.
    Uses hash of user ID + salt for privacy.

    Args:
        user: Django User instance

    Returns:
        str: Anonymized identifier
    """
    salt = settings.SECRET_KEY
    data = f"{user.id}:{user.username}:{user.date_joined}:{salt}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def export_user_data_to_dict(user):
    """
    Export all user data to a Python dictionary.

    Args:
        user: Django User instance

    Returns:
        dict: Complete user data structured for export
    """
    # User profile information
    profile = getattr(user, 'profile', None)
    user_info = {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_joined': user.date_joined.isoformat(),
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'is_active': user.is_active,
    }

    if profile:
        user_info['role'] = profile.role
        user_info['auth_provider'] = profile.auth_provider
        user_info['profile_created_at'] = profile.created_at.isoformat()

    # Resumes
    resumes = []
    for resume in UploadedResume.objects.filter(user=user):
        resumes.append({
            'id': resume.id,
            'title': resume.title,
            'original_filename': resume.original_filename,
            'content': resume.content,
            'skills': resume.skills,
            'experience': resume.experience,
            'education': resume.education,
            'parsing_status': resume.parsing_status,
            'uploaded_at': resume.uploaded_at.isoformat(),
            'filesize': resume.filesize,
        })

    # Job listings
    job_listings = []
    for job in UploadedJobListing.objects.filter(user=user):
        job_listings.append({
            'id': job.id,
            'title': job.title,
            'filename': job.filename,
            'content': job.content,
            'created_at': job.created_at.isoformat(),
        })

    # Interview chats
    interviews = []
    for chat in Chat.objects.filter(owner=user):
        interview_data = {
            'id': chat.id,
            'title': chat.title,
            'type': chat.get_type_display(),
            'difficulty': chat.difficulty,
            'messages': chat.messages,
            'key_questions': chat.key_questions,
            'modified_date': chat.modified_date.isoformat(),
            'resume_title': chat.resume.title if chat.resume else None,
            'job_listing_title': chat.job_listing.title if chat.job_listing else None,
        }

        # Include exportable report if exists
        if hasattr(chat, 'exportable_report'):
            report = chat.exportable_report
            interview_data['report'] = {
                'professionalism_score': report.professionalism_score,
                'subject_knowledge_score': report.subject_knowledge_score,
                'clarity_score': report.clarity_score,
                'overall_score': report.overall_score,
                'feedback_text': report.feedback_text,
                'question_responses': report.question_responses,
                'total_questions_asked': report.total_questions_asked,
                'total_responses_given': report.total_responses_given,
                'generated_at': report.generated_at.isoformat(),
            }

        interviews.append(interview_data)

    # Interview templates
    templates = []
    for template in InterviewTemplate.objects.filter(user=user):
        templates.append({
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'sections': template.sections,
            'created_at': template.created_at.isoformat(),
            'updated_at': template.updated_at.isoformat(),
        })

    # Role change requests
    role_requests = []
    for request in RoleChangeRequest.objects.filter(user=user):
        role_requests.append({
            'id': request.id,
            'requested_role': request.requested_role,
            'current_role': request.current_role,
            'status': request.status,
            'reason': request.reason,
            'created_at': request.created_at.isoformat(),
            'reviewed_at': request.reviewed_at.isoformat() if request.reviewed_at else None,
        })

    return {
        'export_date': timezone.now().isoformat(),
        'user_info': user_info,
        'resumes': resumes,
        'job_listings': job_listings,
        'interviews': interviews,
        'interview_templates': templates,
        'role_change_requests': role_requests,
    }


def create_csv_from_list(data_list, fieldnames):
    """
    Convert a list of dictionaries to CSV format.

    Args:
        data_list: List of dictionaries
        fieldnames: List of field names for CSV header

    Returns:
        str: CSV formatted string
    """
    output = io.StringIO()
    writer = csv.DictWriter(
        output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(data_list)
    return output.getvalue()


def create_export_zip(user):
    """
    Create a ZIP file containing all user data in JSON and CSV formats.

    Args:
        user: Django User instance

    Returns:
        bytes: ZIP file content
    """
    # Get user data
    user_data = export_user_data_to_dict(user)

    # Create in-memory ZIP file
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add complete data as JSON
        zip_file.writestr(
            'complete_data.json',
            json.dumps(user_data, indent=2, ensure_ascii=False)
        )

        # Add user info as JSON
        zip_file.writestr(
            'user_info.json',
            json.dumps(user_data['user_info'], indent=2)
        )

        # Add resumes as CSV
        if user_data['resumes']:
            resume_fieldnames = [
                'id',
                'title',
                'original_filename',
                'uploaded_at',
                'filesize',
                'parsing_status']
            resumes_csv = create_csv_from_list(
                user_data['resumes'], resume_fieldnames)
            zip_file.writestr('resumes.csv', resumes_csv)

            # Add individual resume contents
            for idx, resume in enumerate(user_data['resumes'], 1):
                zip_file.writestr(
                    f'resumes/resume_{idx}_{resume["title"]}.txt',
                    resume['content']
                )

        # Add job listings as CSV
        if user_data['job_listings']:
            job_fieldnames = ['id', 'title', 'filename', 'created_at']
            jobs_csv = create_csv_from_list(
                user_data['job_listings'], job_fieldnames)
            zip_file.writestr('job_listings.csv', jobs_csv)

            # Add individual job listing contents
            for idx, job in enumerate(user_data['job_listings'], 1):
                zip_file.writestr(
                    f'job_listings/job_{idx}_{job["title"]}.txt',
                    job['content']
                )

        # Add interviews as CSV
        if user_data['interviews']:
            interview_fieldnames = [
                'id',
                'title',
                'type',
                'difficulty',
                'modified_date',
                'resume_title',
                'job_listing_title']
            interviews_csv = create_csv_from_list(
                user_data['interviews'], interview_fieldnames)
            zip_file.writestr('interviews.csv', interviews_csv)

            # Add detailed interview transcripts
            for idx, interview in enumerate(user_data['interviews'], 1):
                transcript_file = f'interviews/interview_{idx}_{interview["title"]}.json'
                zip_file.writestr(
                    transcript_file,
                    json.dumps(interview, indent=2)
                )

        # Add interview templates as JSON
        if user_data['interview_templates']:
            zip_file.writestr(
                'interview_templates.json',
                json.dumps(user_data['interview_templates'], indent=2)
            )

        # Add README
        readme_content = f"""USER DATA EXPORT
=================

Export Date: {user_data['export_date']}
Username: {user_data['user_info']['username']}

This archive contains all your personal data from the Active Interview Service.

Contents:
- complete_data.json: All data in a single JSON file
- user_info.json: Your profile information
- resumes.csv: Summary of uploaded resumes
- resumes/: Individual resume text files
- job_listings.csv: Summary of job listings
- job_listings/: Individual job listing text files
- interviews.csv: Summary of interviews
- interviews/: Detailed interview transcripts with messages
- interview_templates.json: Your custom interview templates

This export complies with GDPR/CCPA data portability requirements.
"""
        zip_file.writestr('README.txt', readme_content)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def process_export_request(export_request):
    """
    Process a data export request asynchronously.
    Creates ZIP file and updates the request status.

    Args:
        export_request: DataExportRequest instance

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Update status to processing
        export_request.status = DataExportRequest.PROCESSING
        export_request.save()

        # Generate export ZIP
        zip_content = create_export_zip(export_request.user)

        # Save to file field
        filename = f"{EXPORT_FILE_PREFIX}_{export_request.user.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.zip"
        export_request.export_file.save(
            filename,
            ContentFile(zip_content),
            save=False
        )

        # Update metadata
        export_request.status = DataExportRequest.COMPLETED
        export_request.completed_at = timezone.now()
        export_request.expires_at = timezone.now() + timedelta(days=EXPORT_EXPIRATION_DAYS)
        export_request.file_size_bytes = len(zip_content)
        export_request.save()

        # Send notification email
        send_export_ready_email(export_request)

        return True

    except Exception as e:
        logger.error(
            f"Failed to process export request {export_request.id} for user {export_request.user.username}: {e}",
            exc_info=True)
        export_request.status = DataExportRequest.FAILED
        export_request.error_message = str(e)
        export_request.save()
        return False


def send_export_ready_email(export_request):
    """
    Send email notification when data export is ready.

    Args:
        export_request: DataExportRequest instance
    """
    try:
        user = export_request.user
        download_url = f"{settings.SITE_URL}/profile/data-export/{export_request.id}/download/"

        subject = 'Your Data Export is Ready'

        html_message = render_to_string('emails/data_export_ready.html', {
            'user': user,
            'download_url': download_url,
            'expires_at': export_request.expires_at,
        })

        plain_message = strip_tags(html_message)

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=EMAIL_FAIL_SILENTLY,
        )
        logger.info(
            f"Export notification email sent to {user.email} for request {export_request.id}")
    except Exception as e:
        # Log error but don't fail the export process
        logger.warning(
            f"Failed to send export notification email to {user.email} for request {export_request.id}: {e}",
            exc_info=True)


def anonymize_user_interviews(user):
    """
    Anonymize user's interview data for analytics retention.
    Removes PII but keeps scores and anonymized statistics.

    Args:
        user: Django User instance

    Returns:
        int: Number of interviews anonymized
    """
    _anonymized_id = generate_anonymized_id(user)  # noqa: F841
    count = 0

    for chat in Chat.objects.filter(owner=user):
        # Clear personally identifiable message content
        if chat.messages:
            chat.messages = []

        # Clear key questions (may contain PII)
        if chat.key_questions:
            chat.key_questions = []

        # Update title to be anonymous
        chat.title = f"Anonymized Interview {chat.id}"

        # Remove relationships to user documents
        chat.resume = None
        chat.job_listing = None

        # Keep owner reference but will be deleted cascade
        chat.save()
        count += 1

        # Anonymize report feedback text (keep scores)
        if hasattr(chat, 'exportable_report'):
            report = chat.exportable_report
            report.feedback_text = "[Anonymized]"

            # Clear detailed question responses (may contain PII)
            if report.question_responses:
                # Keep structure but clear content
                report.question_responses = []

            report.save()

    return count


def delete_user_account(user, deletion_request=None):
    """
    Delete user account and associated data with anonymization.
    Implements hard deletion for PII and soft deletion for analytics.

    Args:
        user: Django User instance
        deletion_request: Optional DeletionRequest instance for tracking

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        # Count items for audit trail
        resume_count = UploadedResume.objects.filter(user=user).count()
        job_listing_count = UploadedJobListing.objects.filter(
            user=user).count()

        # Anonymize interviews (soft delete - keep scores for analytics)
        interview_count = anonymize_user_interviews(user)

        # Hard delete: Resumes and associated files
        for resume in UploadedResume.objects.filter(user=user):
            if resume.file:
                # Delete physical file
                if os.path.isfile(resume.file.path):
                    os.remove(resume.file.path)
            resume.delete()

        # Hard delete: Job listings and associated files
        for job in UploadedJobListing.objects.filter(user=user):
            if job.file:
                # Delete physical file
                if os.path.isfile(job.file.path):
                    os.remove(job.file.path)
            job.delete()

        # Hard delete: Export files
        for export_req in DataExportRequest.objects.filter(user=user):
            if export_req.export_file:
                if os.path.isfile(export_req.export_file.path):
                    os.remove(export_req.export_file.path)
            export_req.delete()

        # Update deletion request if provided
        if deletion_request:
            deletion_request.status = DeletionRequest.COMPLETED
            deletion_request.completed_at = timezone.now()
            deletion_request.total_interviews_deleted = interview_count
            deletion_request.total_resumes_deleted = resume_count
            deletion_request.total_job_listings_deleted = job_listing_count
            deletion_request.save()

        # Final step: Delete user (cascades to remaining objects)
        username = user.username
        email = user.email
        user.delete()

        # Send confirmation email before user is fully deleted
        send_deletion_confirmation_email(username, email)

        return True, None

    except Exception as e:
        logger.error(
            f"Failed to delete account for user {user.username}: {e}",
            exc_info=True
        )
        if deletion_request:
            deletion_request.status = DeletionRequest.FAILED
            deletion_request.error_message = str(e)
            deletion_request.save()

        return False, str(e)


def send_deletion_confirmation_email(username, email):
    """
    Send email confirmation after account deletion.

    Args:
        username: User's username (for reference)
        email: User's email address
    """
    subject = 'Your Account Has Been Deleted'

    message = f"""
Dear {username},

Your account and personal data have been successfully deleted from the Active Interview Service.

What was deleted:
- Your profile information
- All resumes and documents
- Interview recordings and transcripts
- All personally identifiable information

What was retained:
- Anonymized interview statistics (scores only, no personal information)
- Anonymized user identifier for legal compliance
- Deletion timestamp for audit purposes

This action is permanent and cannot be undone. If you wish to use our service again in the future, you will need to create a new account.

Thank you for using Active Interview Service.

Best regards,
The AIS Team
"""

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=EMAIL_FAIL_SILENTLY,
        )
        logger.info(
            f"Deletion confirmation email sent to {email} for user {username}")
    except Exception as e:
        logger.warning(
            f"Failed to send deletion confirmation email to {email} for user {username}: {e}",
            exc_info=True)
