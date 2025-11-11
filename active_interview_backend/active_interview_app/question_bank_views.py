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
from .permissions import IsAdminOrInterviewer
from .decorators import admin_or_interviewer_required


# Template views
@login_required
@admin_or_interviewer_required
def question_banks_view(request):
    """Render the question banks management page (Interviewers and Admins only)"""
    return render(request, 'question_banks.html')


class QuestionBankViewSet(viewsets.ModelViewSet):
    """
    ViewSet for QuestionBank CRUD operations.
    Implements Issue #38: Question Bank Creation
    Restricted to Interviewers and Admins only.
    """
    permission_classes = [IsAdminOrInterviewer]
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
    Restricted to Interviewers and Admins only.
    """
    permission_classes = [IsAdminOrInterviewer]
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
    Restricted to Interviewers and Admins only.
    """
    permission_classes = [IsAdminOrInterviewer]
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
    Restricted to Interviewers and Admins only.
    """
    permission_classes = [IsAdminOrInterviewer]
    serializer_class = InterviewTemplateSerializer

    def get_queryset(self):
        """Return templates owned by the current user"""
        return InterviewTemplate.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the user to the current user"""
        serializer.save(user=self.request.user)


class SaveAsTemplateView(APIView):
    """
    Save an auto-assembled interview configuration as an InterviewTemplate.
    Restricted to Interviewers and Admins only.
    """
    permission_classes = [IsAdminOrInterviewer]

    def post(self, request):
        """
        Save interview assembly configuration as a template.

        Request body:
        {
            "name": "Template name",
            "description": "Optional description",
            "tag_ids": [1, 2, 3],
            "question_count": 10,
            "easy_percentage": 30,
            "medium_percentage": 50,
            "hard_percentage": 20,
            "question_bank_id": 1,  # Optional
            "questions": [...]  # Optional: assembled questions to save as section
        }
        """
        import uuid

        name = request.data.get('name')
        description = request.data.get('description', '')
        tag_ids = request.data.get('tag_ids', [])
        question_count = request.data.get('question_count', 5)
        easy_percentage = request.data.get('easy_percentage', 30)
        medium_percentage = request.data.get('medium_percentage', 50)
        hard_percentage = request.data.get('hard_percentage', 20)
        question_bank_id = request.data.get('question_bank_id')
        questions = request.data.get('questions', [])

        # Validation
        if not name:
            return Response(
                {'error': 'Template name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        total = easy_percentage + medium_percentage + hard_percentage
        if total != 100:
            return Response(
                {'error': f'Difficulty percentages must total 100% (currently {total}%)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create section from questions if provided
        # Each question gets its own section
        sections = []
        if questions:
            # Calculate weight per question (distributed evenly)
            weight_per_question = 100 // len(questions) if questions else 0
            remaining_weight = 100 - (weight_per_question * len(questions))

            for i, q in enumerate(questions):
                # Format individual question as section content
                question_content = f"{q['text']}\n\nDifficulty: {q['difficulty']}\nTags: {', '.join([tag['name'] for tag in q.get('tags', [])])}"

                # Truncate question text for title (max 50 chars)
                title = q['text'][:50] + '...' if len(q['text']) > 50 else q['text']

                # Add extra weight to first section if there's a remainder
                weight = weight_per_question + (remaining_weight if i == 0 else 0)

                sections.append({
                    'id': str(uuid.uuid4()),
                    'title': f"Question {i+1}: {title}",
                    'content': question_content,
                    'order': i,
                    'weight': weight
                })

        # Create the template
        template = InterviewTemplate.objects.create(
            name=name,
            user=request.user,
            description=description,
            use_auto_assembly=True,
            question_count=question_count,
            easy_percentage=easy_percentage,
            medium_percentage=medium_percentage,
            hard_percentage=hard_percentage,
            sections=sections
        )

        # Set tags
        if tag_ids:
            template.tags.set(tag_ids)

        # Set question bank if provided
        if question_bank_id:
            try:
                question_bank = QuestionBank.objects.get(
                    id=question_bank_id,
                    owner=request.user
                )
                template.question_banks.add(question_bank)
            except QuestionBank.DoesNotExist:
                pass  # Skip if question bank not found

        return Response({
            'message': 'Template saved successfully',
            'template': InterviewTemplateSerializer(template).data
        }, status=status.HTTP_201_CREATED)


class AutoAssembleInterviewView(APIView):
    """
    Auto-assemble an interview based on tags and configuration.
    Implements Issue #42: Auto-Interview Assembly
    Restricted to Interviewers and Admins only.
    """
    permission_classes = [IsAdminOrInterviewer]

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
                    user=request.user
                )
                # Only use auto-assembly settings if enabled
                if template.use_auto_assembly:
                    tag_ids = list(template.tags.values_list('id', flat=True))
                    question_count = template.question_count
                    difficulty_dist = {
                        'easy': template.easy_percentage,
                        'medium': template.medium_percentage,
                        'hard': template.hard_percentage
                    }
                else:
                    return Response(
                        {'error': 'Template does not have auto-assembly enabled'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
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

        # Early validation: Check if enough questions are available
        # Count available questions for each difficulty level
        available_easy = questions_query.filter(difficulty='easy').count()
        available_medium = questions_query.filter(difficulty='medium').count()
        available_hard = questions_query.filter(difficulty='hard').count()
        total_available = available_easy + available_medium + available_hard

        # Check if total available is less than requested
        if total_available < question_count:
            return Response({
                'error': f'Not enough questions available. Requested: {question_count}, Available: {total_available}',
                'available_count': total_available,
                'requested_count': question_count,
                'breakdown': {
                    'easy': {
                        'requested': easy_count,
                        'available': available_easy
                    },
                    'medium': {
                        'requested': medium_count,
                        'available': available_medium
                    },
                    'hard': {
                        'requested': hard_count,
                        'available': available_hard
                    }
                },
                'message': 'Please reduce the number of questions or adjust the difficulty distribution.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if enough questions available for each difficulty level
        if available_easy < easy_count or available_medium < medium_count or available_hard < hard_count:
            insufficient_difficulties = []
            if available_easy < easy_count:
                insufficient_difficulties.append(f'easy (need {easy_count}, have {available_easy})')
            if available_medium < medium_count:
                insufficient_difficulties.append(f'medium (need {medium_count}, have {available_medium})')
            if available_hard < hard_count:
                insufficient_difficulties.append(f'hard (need {hard_count}, have {available_hard})')

            return Response({
                'error': f'Not enough questions for difficulty levels: {", ".join(insufficient_difficulties)}',
                'breakdown': {
                    'easy': {
                        'requested': easy_count,
                        'available': available_easy
                    },
                    'medium': {
                        'requested': medium_count,
                        'available': available_medium
                    },
                    'hard': {
                        'requested': hard_count,
                        'available': available_hard
                    }
                },
                'message': 'Please adjust the difficulty distribution or add more questions to your question bank.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get questions for each difficulty level
        selected_questions = []

        for difficulty, count in [('easy', easy_count), ('medium', medium_count), ('hard', hard_count)]:
            available = list(questions_query.filter(difficulty=difficulty))

            if randomize:
                selected_questions.extend(random.sample(available, count))
            else:
                selected_questions.extend(available[:count])

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
