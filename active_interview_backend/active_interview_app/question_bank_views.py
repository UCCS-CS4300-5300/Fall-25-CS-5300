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
from typing import Optional, List, Dict, Any
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count, QuerySet
from django.shortcuts import get_object_or_404, render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
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


class QuestionQueryBuilder:
    """
    Utility class for building Question querysets with common filters.
    Reduces code duplication across views that need question filtering.

    This class provides a fluent interface for building complex Question queries
    with multiple filters including owner, question bank, tags, difficulty, and search.
    """

    @staticmethod
    def build_base_queryset(user: User) -> QuerySet:
        """
        Create base queryset filtered by owner.

        Args:
            user: User who owns the questions

        Returns:
            QuerySet filtered by owner
        """
        return Question.objects.filter(owner=user)

    @staticmethod
    def apply_question_bank_filter(queryset: QuerySet,
                                     question_bank_id: Optional[int]) -> QuerySet:
        """
        Apply question bank filter if provided.

        Args:
            queryset: Base Question queryset
            question_bank_id: Optional question bank ID to filter by

        Returns:
            Filtered queryset
        """
        if question_bank_id:
            return queryset.filter(question_bank_id=question_bank_id)
        return queryset

    @staticmethod
    def apply_tag_filter(queryset: QuerySet,
                         tag_ids: Optional[List[int]],
                         filter_mode: str = 'OR') -> QuerySet:
        """
        Apply tag filtering with AND or OR logic.

        Args:
            queryset: Base Question queryset
            tag_ids: List of tag IDs to filter by
            filter_mode: 'AND' for questions with all tags, 'OR' for any tag (default: 'OR')

        Returns:
            Filtered queryset with tag filters applied
        """
        if not tag_ids:
            return queryset

        if filter_mode == 'OR':
            # OR logic: questions with any of the tags
            return queryset.filter(tags__id__in=tag_ids).distinct()
        else:
            # AND logic: questions with all of the tags
            for tag_id in tag_ids:
                queryset = queryset.filter(tags__id=tag_id)
            return queryset

    @staticmethod
    def apply_difficulty_filter(queryset: QuerySet,
                                 difficulty: Optional[str]) -> QuerySet:
        """
        Apply difficulty filter if provided.

        Args:
            queryset: Base Question queryset
            difficulty: Optional difficulty level ('easy', 'medium', or 'hard')

        Returns:
            Filtered queryset
        """
        if difficulty:
            return queryset.filter(difficulty=difficulty)
        return queryset

    @staticmethod
    def apply_search_filter(queryset: QuerySet,
                            search_term: Optional[str]) -> QuerySet:
        """
        Apply text search filter if provided.

        Args:
            queryset: Base Question queryset
            search_term: Optional search term to match in question text

        Returns:
            Filtered queryset with case-insensitive text search applied
        """
        if search_term:
            return queryset.filter(text__icontains=search_term)
        return queryset

    @staticmethod
    def exclude_untagged(queryset: QuerySet) -> QuerySet:
        """
        Exclude questions without any tags.

        Args:
            queryset: Base Question queryset

        Returns:
            Filtered queryset excluding untagged questions
        """
        return queryset.filter(tags__isnull=False)

    @classmethod
    def build_filtered_queryset(cls,
                                 user: User,
                                 question_bank_id: Optional[int] = None,
                                 tag_ids: Optional[List[int]] = None,
                                 filter_mode: str = 'OR',
                                 difficulty: Optional[str] = None,
                                 search: Optional[str] = None,
                                 exclude_untagged: bool = False) -> QuerySet:
        """
        Build a complete filtered queryset with all common filters.

        This method provides a convenient way to apply multiple filters in a single call,
        ensuring consistent query building across different views.

        Args:
            user: User to filter questions by (required)
            question_bank_id: Optional question bank ID to filter by
            tag_ids: Optional list of tag IDs to filter by
            filter_mode: 'AND' or 'OR' for tag filtering (default: 'OR')
            difficulty: Optional difficulty level ('easy', 'medium', or 'hard')
            search: Optional search term for question text
            exclude_untagged: Whether to exclude questions without tags (default: False)

        Returns:
            Filtered and distinct Question queryset

        Example:
            >>> queryset = QuestionQueryBuilder.build_filtered_queryset(
            ...     user=request.user,
            ...     tag_ids=[1, 2, 3],
            ...     filter_mode='OR',
            ...     difficulty='medium'
            ... )
        """
        queryset = cls.build_base_queryset(user)
        queryset = cls.apply_question_bank_filter(queryset, question_bank_id)
        queryset = cls.apply_tag_filter(queryset, tag_ids, filter_mode)
        queryset = cls.apply_difficulty_filter(queryset, difficulty)
        queryset = cls.apply_search_filter(queryset, search)

        if exclude_untagged:
            queryset = cls.exclude_untagged(queryset)

        return queryset.distinct()


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
        """Return questions owned by the current user with applied filters."""
        # Extract filter parameters
        question_bank_id = self.request.query_params.get('question_bank', None)
        tag_ids = self.request.query_params.getlist('tags', [])
        filter_mode = self.request.query_params.get('filter_mode', 'AND')
        difficulty = self.request.query_params.get('difficulty', None)
        search = self.request.query_params.get('search', None)

        # Use QuestionQueryBuilder to build filtered queryset
        return QuestionQueryBuilder.build_filtered_queryset(
            user=self.request.user,
            question_bank_id=question_bank_id,
            tag_ids=tag_ids,
            filter_mode=filter_mode,
            difficulty=difficulty,
            search=search,
            exclude_untagged=False
        )

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
        # Parse parameters from request
        params = self._parse_template_parameters(request)

        # Validate template data
        validation_response = self._validate_template_data(
            params['name'],
            params['easy_percentage'],
            params['medium_percentage'],
            params['hard_percentage']
        )
        if validation_response:
            return validation_response

        # Create sections from questions if provided
        sections = self._create_sections_from_questions(params['questions'])

        # Create the template instance
        template = self._create_template_instance(
            request.user,
            params['name'],
            params['description'],
            params['question_count'],
            params['easy_percentage'],
            params['medium_percentage'],
            params['hard_percentage'],
            sections
        )

        # Associate tags and question bank
        self._associate_tags_and_bank(
            template,
            params['tag_ids'],
            params['question_bank_id'],
            request.user
        )

        # Build and return response
        return self._build_template_response(template)

    def _parse_template_parameters(self, request: Request) -> Dict[str, Any]:
        """
        Extract and parse parameters from the request data.

        Args:
            request: DRF Request object containing template parameters

        Returns:
            Dictionary containing all parsed template parameters
        """
        return {
            'name': request.data.get('name'),
            'description': request.data.get('description', ''),
            'tag_ids': request.data.get('tag_ids', []),
            'question_count': request.data.get('question_count', 5),
            'easy_percentage': request.data.get('easy_percentage', 30),
            'medium_percentage': request.data.get('medium_percentage', 50),
            'hard_percentage': request.data.get('hard_percentage', 20),
            'question_bank_id': request.data.get('question_bank_id'),
            'questions': request.data.get('questions', [])
        }

    def _validate_template_data(self,
                                 name: Optional[str],
                                 easy_pct: int,
                                 medium_pct: int,
                                 hard_pct: int) -> Optional[Response]:
        """
        Validate template name and difficulty percentages.

        Args:
            name: Template name (required)
            easy_pct: Percentage of easy questions
            medium_pct: Percentage of medium questions
            hard_pct: Percentage of hard questions

        Returns:
            Error Response if validation fails, None if valid
        """
        if not name:
            return Response(
                {'error': 'Template name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        total = easy_pct + medium_pct + hard_pct
        if total != 100:
            return Response(
                {'error': f'Difficulty percentages must total 100% (currently {total}%)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return None

    def _create_sections_from_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create interview template sections from provided questions.

        Each question becomes its own section with evenly distributed weights.
        Handles weight distribution to ensure total equals 100%.

        Args:
            questions: List of question dictionaries

        Returns:
            List of section dictionaries with UUID, title, content, order, and weight
        """
        import uuid

        sections = []
        if not questions:
            return sections

        # Calculate weight per question (distributed evenly)
        weight_per_question = 100 // len(questions)
        remaining_weight = 100 - (weight_per_question * len(questions))

        for i, question in enumerate(questions):
            section = self._create_section_from_question(
                question,
                i,
                weight_per_question,
                remaining_weight if i == 0 else 0
            )
            sections.append(section)

        return sections

    def _create_section_from_question(self,
                                       question: Dict[str, Any],
                                       index: int,
                                       base_weight: int,
                                       extra_weight: int) -> Dict[str, Any]:
        """
        Create a single section from a question dict.

        Args:
            question: Question dictionary with text, difficulty, and tags
            index: Zero-based index for ordering
            base_weight: Base weight value for this question
            extra_weight: Additional weight (for first question to handle remainders)

        Returns:
            Section dictionary with id, title, content, order, and weight
        """
        import uuid

        # Format question content with metadata
        tags_str = ', '.join([tag['name'] for tag in question.get('tags', [])])
        question_content = (
            f"{question['text']}\n\n"
            f"Difficulty: {question['difficulty']}\n"
            f"Tags: {tags_str}"
        )

        # Truncate question text for title (max 50 chars)
        title = question['text'][:50] + '...' if len(question['text']) > 50 else question['text']

        return {
            'id': str(uuid.uuid4()),
            'title': f"Question {index + 1}: {title}",
            'content': question_content,
            'order': index,
            'weight': base_weight + extra_weight
        }

    def _create_template_instance(self,
                                   user: User,
                                   name: str,
                                   description: str,
                                   question_count: int,
                                   easy_pct: int,
                                   medium_pct: int,
                                   hard_pct: int,
                                   sections: List[Dict[str, Any]]) -> InterviewTemplate:
        """
        Create and return a new InterviewTemplate instance.

        Args:
            user: Template owner
            name: Template name
            description: Template description
            question_count: Number of questions for auto-assembly
            easy_pct: Percentage of easy questions
            medium_pct: Percentage of medium questions
            hard_pct: Percentage of hard questions
            sections: List of section dictionaries

        Returns:
            Newly created InterviewTemplate instance
        """
        return InterviewTemplate.objects.create(
            name=name,
            user=user,
            description=description,
            use_auto_assembly=True,
            question_count=question_count,
            easy_percentage=easy_pct,
            medium_percentage=medium_pct,
            hard_percentage=hard_pct,
            sections=sections
        )

    def _associate_tags_and_bank(self,
                                  template: InterviewTemplate,
                                  tag_ids: List[int],
                                  question_bank_id: Optional[int],
                                  user: User) -> None:
        """
        Associate tags and question bank with the template.

        Args:
            template: InterviewTemplate instance to update
            tag_ids: List of tag IDs to associate
            question_bank_id: Optional question bank ID to associate
            user: User for ownership validation of question bank
        """
        # Set tags if provided
        if tag_ids:
            template.tags.set(tag_ids)

        # Set question bank if provided
        if question_bank_id:
            try:
                question_bank = QuestionBank.objects.get(
                    id=question_bank_id,
                    owner=user
                )
                template.question_banks.add(question_bank)
            except QuestionBank.DoesNotExist:
                pass  # Skip if question bank not found

    def _build_template_response(self, template: InterviewTemplate) -> Response:
        """
        Build the success response for template creation.

        Args:
            template: Created InterviewTemplate instance

        Returns:
            Response with success message and serialized template data
        """
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
        # Parse and load parameters
        params = self._parse_request_parameters(request)

        # Load template settings if template_id provided
        template_response = self._load_template_settings(request, params)
        if template_response:
            return template_response

        # Build filtered question queryset
        questions_query = self._build_question_queryset(request.user, params)

        # Calculate difficulty distribution
        difficulty_counts = self._calculate_difficulty_counts(
            params['question_count'],
            params['difficulty_dist']
        )

        # Validate question availability
        validation_response = self._validate_question_availability(
            questions_query,
            params['question_count'],
            difficulty_counts
        )
        if validation_response:
            return validation_response

        # Select questions
        selected_questions = self._select_questions(
            questions_query,
            difficulty_counts,
            params['randomize']
        )

        # Build and return response
        return self._build_response(params['title'], selected_questions)

    def _parse_request_parameters(self, request):
        """Extract and return parameters from request."""
        return {
            'title': request.data.get('title', 'Auto-assembled Interview'),
            'tag_ids': request.data.get('tag_ids', []),
            'question_count': request.data.get('question_count', 5),
            'difficulty_dist': request.data.get('difficulty_distribution', {
                'easy': 30,
                'medium': 50,
                'hard': 20
            }),
            'question_bank_id': request.data.get('question_bank_id', None),
            'template_id': request.data.get('template_id', None),
            'randomize': request.data.get('randomize', True)
        }

    def _load_template_settings(self, request, params):
        """Load settings from template if template_id provided. Returns error Response or None."""
        if not params['template_id']:
            return None

        try:
            template = InterviewTemplate.objects.get(
                id=params['template_id'],
                user=request.user
            )

            if not template.use_auto_assembly:
                return Response(
                    {'error': 'Template does not have auto-assembly enabled'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update params with template settings
            params['tag_ids'] = list(template.tags.values_list('id', flat=True))
            params['question_count'] = template.question_count
            params['difficulty_dist'] = {
                'easy': template.easy_percentage,
                'medium': template.medium_percentage,
                'hard': template.hard_percentage
            }
            return None

        except InterviewTemplate.DoesNotExist:
            return Response(
                {'error': 'Template not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def _build_question_queryset(self, user, params):
        """Build and return filtered question queryset using QuestionQueryBuilder."""
        return QuestionQueryBuilder.build_filtered_queryset(
            user=user,
            question_bank_id=params['question_bank_id'],
            tag_ids=params['tag_ids'],
            filter_mode='OR',  # Auto-assembly uses OR logic for tags
            difficulty=None,  # Difficulty filtering done during selection
            search=None,
            exclude_untagged=True  # Only tagged questions for auto-assembly
        )

    def _calculate_difficulty_counts(self, question_count, difficulty_dist):
        """Calculate how many questions needed for each difficulty level."""
        easy_count = int(question_count * difficulty_dist.get('easy', 0) / 100)
        medium_count = int(question_count * difficulty_dist.get('medium', 0) / 100)
        hard_count = question_count - easy_count - medium_count

        return {
            'easy': easy_count,
            'medium': medium_count,
            'hard': hard_count
        }

    def _validate_question_availability(self, questions_query, question_count, difficulty_counts):
        """
        Validate sufficient questions are available.
        Returns error Response if validation fails, None if valid.
        """
        # Count available questions by difficulty
        available = {
            'easy': questions_query.filter(difficulty='easy').count(),
            'medium': questions_query.filter(difficulty='medium').count(),
            'hard': questions_query.filter(difficulty='hard').count()
        }
        total_available = sum(available.values())

        # Check total availability
        if total_available < question_count:
            return Response({
                'error': f'Not enough questions available. Requested: {question_count}, Available: {total_available}',
                'available_count': total_available,
                'requested_count': question_count,
                'breakdown': self._build_breakdown(difficulty_counts, available),
                'message': 'Please reduce the number of questions or adjust the difficulty distribution.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check per-difficulty availability
        if any(available[d] < difficulty_counts[d] for d in ['easy', 'medium', 'hard']):
            insufficient = [
                f"{d} (need {difficulty_counts[d]}, have {available[d]})"
                for d in ['easy', 'medium', 'hard']
                if available[d] < difficulty_counts[d]
            ]

            return Response({
                'error': f'Not enough questions for difficulty levels: {", ".join(insufficient)}',
                'breakdown': self._build_breakdown(difficulty_counts, available),
                'message': 'Please adjust the difficulty distribution or add more questions to your question bank.'
            }, status=status.HTTP_400_BAD_REQUEST)

        return None

    def _build_breakdown(self, requested, available):
        """Build difficulty breakdown for error responses."""
        return {
            difficulty: {
                'requested': requested[difficulty],
                'available': available[difficulty]
            }
            for difficulty in ['easy', 'medium', 'hard']
        }

    def _select_questions(self, questions_query, difficulty_counts, randomize):
        """Select questions based on difficulty distribution and randomization."""
        selected_questions = []

        for difficulty in ['easy', 'medium', 'hard']:
            count = difficulty_counts[difficulty]
            available = list(questions_query.filter(difficulty=difficulty))

            if randomize:
                selected_questions.extend(random.sample(available, count))
            else:
                selected_questions.extend(available[:count])

        return selected_questions

    def _select_questions_disregard_difficulty(self, questions_query, question_count, randomize):
        """
        Select questions without considering difficulty distribution.
        Used when disregard_difficulty flag is set to True.
        """
        available = list(questions_query)

        if randomize:
            return random.sample(available, question_count)
        else:
            return available[:question_count]

    def _build_response(self, title, selected_questions):
        """Build the final response with interview data."""
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
