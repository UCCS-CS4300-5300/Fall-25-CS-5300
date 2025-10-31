from rest_framework import serializers
from .models import *


class UploadedResumeSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, allow_null=True)

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


# Question Bank Tagging Serializers
class TagSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'created_at', 'question_count']
        read_only_fields = ['id', 'created_at']

    def get_question_count(self, obj):
        return obj.questions.count()


class QuestionSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), write_only=True, required=False
    )
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'question_bank', 'text', 'difficulty', 'tags', 'tag_ids',
                 'owner', 'owner_username', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        question = Question.objects.create(**validated_data)
        question.tags.set(tag_ids)
        return question

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        return instance


class QuestionBankSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = QuestionBank
        fields = ['id', 'name', 'description', 'owner', 'owner_username',
                 'questions', 'question_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_question_count(self, obj):
        return obj.questions.count()


class QuestionBankListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views without nested questions"""
    question_count = serializers.SerializerMethodField()
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = QuestionBank
        fields = ['id', 'name', 'description', 'owner', 'owner_username',
                 'question_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_question_count(self, obj):
        return obj.questions.count()


class InterviewTemplateSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), write_only=True, required=False
    )
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = InterviewTemplate
        fields = ['id', 'name', 'owner', 'owner_username', 'tags', 'tag_ids',
                 'question_count', 'easy_percentage', 'medium_percentage',
                 'hard_percentage', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        template = InterviewTemplate.objects.create(**validated_data)
        template.tags.set(tag_ids)
        return template

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        return instance
