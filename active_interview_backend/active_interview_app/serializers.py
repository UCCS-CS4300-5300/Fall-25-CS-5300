from rest_framework import serializers
from .models import *


class UploadedResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedResume
        fields = ['id', 'file', 'user', 'uploaded_at', 'title']
        read_only_fields = ['id', 'uploaded_at', 'user']


class UploadedJobListingSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(required=False, allow_blank=True, default='')
    file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = UploadedJobListing
        fields = ['id', 'user', 'filename', 'content', 'created_at', 'title', 'file']
        read_only_fields = ['id', 'created_at', 'user']


class ExportableReportSerializer(serializers.ModelSerializer):
    chat_title = serializers.CharField(source='chat.title', read_only=True)
    chat_type = serializers.CharField(source='chat.get_type_display',
                                      read_only=True)
    chat_difficulty = serializers.IntegerField(source='chat.difficulty',
                                                read_only=True)

    class Meta:
        model = ExportableReport
        fields = [
            'id',
            'chat',
            'chat_title',
            'chat_type',
            'chat_difficulty',
            'generated_at',
            'last_updated',
            'professionalism_score',
            'subject_knowledge_score',
            'clarity_score',
            'overall_score',
            'feedback_text',
            'question_responses',
            'total_questions_asked',
            'total_responses_given',
            'interview_duration_minutes',
            'pdf_generated',
            'pdf_file',
        ]
        read_only_fields = ['generated_at', 'last_updated']
