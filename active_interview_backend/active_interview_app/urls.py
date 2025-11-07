from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import routers
from allauth.account import views as allauth_views

from . import views


# Create router and register views
router = routers.DefaultRouter()


urlpatterns = [
    # Misc. urls
    path('', views.index, name='index'),
    path('about-us/', views.aboutus, name='about-us'),
    path('aboutus/', views.aboutus, name='aboutus'),  # Alias for tests
    path('features/', views.features, name='features'),

    # Auth urls - using custom paths that work with allauth
    path('register/', views.register, name='register_page'),
    path('testlogged/', views.loggedin, name='loggedin'),
    path('profile/', views.profile, name='profile'),
    path('results/', views.results, name='results'),

    # Include django.contrib.auth.urls for password reset, etc.
    path('accounts/', include('django.contrib.auth.urls')),

    # Chat url
    path('chat/', views.chat_list, name='chat-list'),
    path('chat/create/', views.CreateChat.as_view(), name='chat-create'),
    path('chat/<int:chat_id>/', views.ChatView.as_view(), name='chat-view'),
    path('chat/<int:chat_id>/edit/', views.EditChat.as_view(),
         name='chat-edit'),
    path('chat/<int:chat_id>/delete/', views.DeleteChat.as_view(),
         name='chat-delete'),
    path('chat/<int:chat_id>/restart/', views.RestartChat.as_view(),
         name='chat-restart'),
    path('chat/<int:chat_id>/results/', views.ResultCharts.as_view(),
         name='chat-results'),
    path('chat/<int:chat_id>/result-charts/', views.ResultCharts.as_view(),
         name='result-charts'),  # Alias for tests
    path('chat/<int:chat_id>/key-questions/<int:question_id>/',
         views.KeyQuestionsView.as_view(), name='key-questions'),

    # Demo urls
    # path('demo/', views.demo, name='demo'),
    # path('chat-test/', views.test_chat_view, name='chat-test'),

    # api urls
    path('api/', include(router.urls)),

    # Joel's file upload urls
    path('document/', views.DocumentList.as_view(), name='document-list'),
    path('upload-file/', views.upload_file, name='upload_file'),
    path('api/paste-text/', views.UploadedJobListingView.as_view(),
         name='save_pasted_text'),
    path('paste-text/<int:pk>/', views.UploadedJobListingView.as_view(),
         name='pasted_text_detail'),
    # List files and uploads.
    path('api/files/', views.UploadedResumeView.as_view(), name='file_list'),
    path('api/files-list/', views.UploadedResumeView.as_view(), name='files_list'),
    # path('api/files/<int:pk>/', views.UploadedResumeDetail.as_view(),
    #      name='file_detail'), #Making changes to files.
    # For the text box input.
    path('pasted-text/', views.UploadedJobListingView.as_view(),
         name='save_pasted_text'),
    path('api/job-listings/', views.JobListingList.as_view(), name='pasted_text_list'),
    path('resume/<int:resume_id>/', views.resume_detail, name='resume_detail'),
    path('job-posting/<int:job_id>/',
         views.job_posting_detail, name='job_posting_detail'),
    path('resume/delete/<int:resume_id>/',
         views.delete_resume, name='delete_resume'),
    path('delete_job/<int:job_id>/', views.delete_job, name='delete_job'),
    path('resume/edit/<int:resume_id>/', views.edit_resume,
         name='edit_resume'),
    path('job-posting/edit/<int:job_id>/',
         views.edit_job_posting, name='edit_job_posting'),

    # Exportable Report urls
    path('chat/<int:chat_id>/generate-report/',
         views.GenerateReportView.as_view(), name='generate_report'),
    path('chat/<int:chat_id>/export-report/',
         views.ExportReportView.as_view(), name='export_report'),
    path('chat/<int:chat_id>/download-pdf/',
         views.DownloadPDFReportView.as_view(), name='download_pdf_report'),
    path('chat/<int:chat_id>/download-csv/',
         views.DownloadCSVReportView.as_view(), name='download_csv_report'),

    # User Profile View (Issue #69)
    path('user/<int:user_id>/profile/', views.view_user_profile,
         name='view_user_profile'),

    # Role Request urls (Issue #69)
    path('profile/request-role-change/', views.request_role_change,
         name='request_role_change'),
    path('role-requests/', views.role_requests_list,
         name='role_requests_list'),
    path('role-requests/<int:request_id>/review/',
         views.review_role_request, name='review_role_request'),

    # Candidate Search urls (Issue #69)
    path('candidates/search/', views.candidate_search,
         name='candidate_search'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.PROD:
#     # add these urls for production environments only
#     # urlpatterns.append(path('api/', include(router.urls)))
#     pass
# else:
#     # add these urls for non-production environments only
#     # urlpatterns.append(path('api/', include(router.urls)))
#     pass
