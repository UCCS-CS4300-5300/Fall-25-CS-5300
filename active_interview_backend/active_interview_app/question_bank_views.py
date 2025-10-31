"""
Views for Question Bank Tagging feature (Issue #24)
Includes:
- QuestionBank CRUD (Issue #38)
- Question Tagging (Issue #39)
- Tag Management (Issue #40)
- Tag Filtering (Issue #41)
- Auto-Interview Assembly (Issue #42)
"""

import random
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import QuestionBank, Question, Tag, InterviewTemplate, Chat
from .serializers import (
    QuestionBankSerializer,
    QuestionBankListSerializer,
    QuestionSerializer,
    TagSerializer,
    InterviewTemplateSerializer
)


# Template views
@login_required
def question_banks_view(request):
    """Render the question banks management page"""
    return render(request, 'question_banks.html')


class QuestionBankViewSet(viewsets.ModelViewSet):
    """
    ViewSet for QuestionBank CRUD operations.
    Implements Issue #38: Question Bank Creation
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionBankSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return QuestionBankListSerializer
        return QuestionBankSerializer

    def get_queryset(self):
        """Return question banks owned by the current user"""
        return QuestionBank.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """Set the owner to the current user"""
        serializer.save(owner=self.request.user)


class QuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Question CRUD operations and tagging.
    Implements Issue #39: Basic Question Tagging
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionSerializer

    def get_queryset(self):
        """Return questions owned by the current user"""
        queryset = Question.objects.filter(owner=self.request.user)

        # Filter by question bank
        question_bank_id = self.request.query_params.get('question_bank', None)
        if question_bank_id:
            queryset = queryset.filter(question_bank_id=question_bank_id)

        # Filter by tags (Issue #41: Tag Filtering)
        tag_ids = self.request.query_params.getlist('tags', [])
        filter_mode = self.request.query_params.get('filter_mode', 'AND')

        if tag_ids:
            if filter_mode == 'OR':
                # OR logic: questions with any of the tags
                queryset = queryset.filter(tags__id__in=tag_ids).distinct()
            else:
                # AND logic: questions with all of the tags
                for tag_id in tag_ids:
                    queryset = queryset.filter(tags__id=tag_id)

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty', None)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        # Search in question text
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(text__icontains=search)

        return queryset.distinct()

    def perform_create(self, serializer):
        """Set the owner to the current user"""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def add_tags(self, request, pk=None):
        """Add tags to a question"""
        question = self.get_object()
        tag_ids = request.data.get('tag_ids', [])

        if not tag_ids:
            return Response(
                {'error': 'tag_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        question.tags.add(*tag_ids)
        serializer = self.get_serializer(question)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def remove_tags(self, request, pk=None):
        """Remove tags from a question"""
        question = self.get_object()
        tag_ids = request.data.get('tag_ids', [])

        if not tag_ids:
            return Response(
                {'error': 'tag_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        question.tags.remove(*tag_ids)
        serializer = self.get_serializer(question)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_tag(self, request):
        """Add tags to multiple questions at once"""
        question_ids = request.data.get('question_ids', [])
        tag_ids = request.data.get('tag_ids', [])

        if not question_ids or not tag_ids:
            return Response(
                {'error': 'question_ids and tag_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        questions = Question.objects.filter(
            id__in=question_ids,
            owner=request.user
        )

        count = 0
        for question in questions:
            question.tags.add(*tag_ids)
            count += 1

        return Response({
            'message': f'Tags applied to {count} questions',
            'count': count
        })


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tag management.
    Implements Issue #40: Tag Management
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()

    def get_queryset(self):
        """Return all tags, with optional search"""
        queryset = Tag.objects.all()

        # Search tags
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)

        # Annotate with question count for statistics
        queryset = queryset.annotate(
            questions_count=Count('questions')
        )

        return queryset

    @action(detail=True, methods=['post'])
    def rename(self, request, pk=None):
        """Rename a tag globally"""
        tag = self.get_object()
        new_name = request.data.get('new_name', '')

        if not new_name:
            return Response(
                {'error': 'new_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if tag with new name already exists
        if Tag.objects.filter(name=new_name).exclude(id=tag.id).exists():
            return Response(
                {'error': 'Tag with this name already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tag.name = new_name
        tag.save()

        serializer = self.get_serializer(tag)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def merge(self, request):
        """Merge multiple tags into one"""
        tag_ids = request.data.get('tag_ids', [])
        primary_tag_id = request.data.get('primary_tag_id', None)

        if not tag_ids or not primary_tag_id:
            return Response(
                {'error': 'tag_ids and primary_tag_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if primary_tag_id not in tag_ids:
            return Response(
                {'error': 'primary_tag_id must be in tag_ids'},
                status=status.HTTP_400_BAD_REQUEST
            )

        primary_tag = get_object_or_404(Tag, id=primary_tag_id)
        tags_to_merge = Tag.objects.filter(id__in=tag_ids).exclude(id=primary_tag_id)

        # Move all questions from merged tags to primary tag
        for tag in tags_to_merge:
            for question in tag.questions.all():
                question.tags.add(primary_tag)
                question.tags.remove(tag)
            tag.delete()

        return Response({
            'message': f'Tags merged into {primary_tag.name}',
            'primary_tag': TagSerializer(primary_tag).data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get tag usage statistics"""
        tags = Tag.objects.annotate(
            question_count=Count('questions')
        ).order_by('-question_count')

        stats = {
            'total_tags': tags.count(),
            'most_used': TagSerializer(tags[:5], many=True).data,
            'unused': TagSerializer(
                tags.filter(question_count=0), many=True
            ).data,
        }

        return Response(stats)


class InterviewTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Interview Template management.
    Allows saving and reusing interview assembly configurations.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InterviewTemplateSerializer

    def get_queryset(self):
        """Return templates owned by the current user"""
        return InterviewTemplate.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """Set the owner to the current user"""
        serializer.save(owner=self.request.user)


class AutoAssembleInterviewView(APIView):
    """
    Auto-assemble an interview based on tags and configuration.
    Implements Issue #42: Auto-Interview Assembly
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Assemble an interview based on provided criteria.

        Request body:
        {
            "title": "Interview title",
            "tag_ids": [1, 2, 3],  # Tags to filter by
            "question_count": 10,  # Total questions needed
            "difficulty_distribution": {
                "easy": 30,   # percentage
                "medium": 50,
                "hard": 20
            },
            "question_bank_id": 1,  # Optional: specific question bank
            "template_id": 1,  # Optional: use saved template
            "randomize": true  # Default: true
        }
        """
        # Get parameters from request
        title = request.data.get('title', 'Auto-assembled Interview')
        tag_ids = request.data.get('tag_ids', [])
        question_count = request.data.get('question_count', 5)
        difficulty_dist = request.data.get('difficulty_distribution', {
            'easy': 30,
            'medium': 50,
            'hard': 20
        })
        question_bank_id = request.data.get('question_bank_id', None)
        template_id = request.data.get('template_id', None)
        randomize = request.data.get('randomize', True)

        # If template_id is provided, use template settings
        if template_id:
            try:
                template = InterviewTemplate.objects.get(
                    id=template_id,
                    owner=request.user
                )
                tag_ids = list(template.tags.values_list('id', flat=True))
                question_count = template.question_count
                difficulty_dist = {
                    'easy': template.easy_percentage,
                    'medium': template.medium_percentage,
                    'hard': template.hard_percentage
                }
            except InterviewTemplate.DoesNotExist:
                return Response(
                    {'error': 'Template not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Build question queryset
        questions_query = Question.objects.filter(owner=request.user)

        # Filter by question bank if specified
        if question_bank_id:
            questions_query = questions_query.filter(
                question_bank_id=question_bank_id
            )

        # Filter by tags (must have at least one of the specified tags)
        if tag_ids:
            questions_query = questions_query.filter(
                tags__id__in=tag_ids
            ).distinct()

        # Exclude untagged questions
        questions_query = questions_query.filter(tags__isnull=False).distinct()

        # Calculate how many questions of each difficulty
        easy_count = int(question_count * difficulty_dist.get('easy', 0) / 100)
        medium_count = int(question_count * difficulty_dist.get('medium', 0) / 100)
        hard_count = question_count - easy_count - medium_count

        # Get questions for each difficulty level
        selected_questions = []

        for difficulty, count in [('easy', easy_count), ('medium', medium_count), ('hard', hard_count)]:
            available = list(questions_query.filter(difficulty=difficulty))

            if len(available) < count:
                # Not enough questions of this difficulty
                selected_questions.extend(available)
            else:
                if randomize:
                    selected_questions.extend(random.sample(available, count))
                else:
                    selected_questions.extend(available[:count])

        # Check if we have enough questions
        if len(selected_questions) < question_count:
            return Response({
                'warning': f'Only {len(selected_questions)} questions available with selected tags',
                'available_count': len(selected_questions),
                'requested_count': question_count,
                'questions': QuestionSerializer(selected_questions, many=True).data
            }, status=status.HTTP_206_PARTIAL_CONTENT)

        # Return the assembled interview preview
        return Response({
            'title': title,
            'questions': QuestionSerializer(selected_questions, many=True).data,
            'total_questions': len(selected_questions),
            'difficulty_breakdown': {
                'easy': len([q for q in selected_questions if q.difficulty == 'easy']),
                'medium': len([q for q in selected_questions if q.difficulty == 'medium']),
                'hard': len([q for q in selected_questions if q.difficulty == 'hard']),
            },
            'tag_breakdown': self._get_tag_breakdown(selected_questions)
        })

    def _get_tag_breakdown(self, questions):
        """Calculate tag distribution in selected questions"""
        tag_counts = {}
        for question in questions:
            for tag in question.tags.all():
                tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1
        return tag_counts
