from rest_framework import serializers
from .models import *


class UploadedResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedResume
        fields = ['id', 'file', 'user', 'uploaded_at']


class UploadedJobListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedJobListing
        fields = ['id', 'user', 'filename', 'content', 'created_at']


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
