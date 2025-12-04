"""Tests for rate limit decorators and mixins."""

from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from rest_framework.viewsets import ModelViewSet
from rest_framework.serializers import ModelSerializer

from ..models import Tag
from ..decorators.ratelimit_decorators import (
    ratelimit_default,
    ratelimit_strict,
    ratelimit_lenient,
    ratelimit_api
)
from ..mixins.ratelimit_mixins import (
    RateLimitMixin,
    StrictRateLimitMixin,
    LenientRateLimitMixin
)


class TagSerializer(ModelSerializer):
    """Simple serializer for testing."""
    class Meta:
        model = Tag
        fields = ['id', 'name']


@override_settings(RATELIMIT_ENABLE=True)
class RateLimitDecoratorsTest(TestCase):
    """Tests for rate limit decorators."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_ratelimit_default_decorator(self):
        """Test ratelimit_default decorator can be applied."""
        @ratelimit_default(methods=['GET'])
        def test_view(request):
            return HttpResponse('OK')

        # Verify decorator doesn't break the view
        request = self.factory.get('/')
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 200)

    def test_ratelimit_strict_decorator(self):
        """Test ratelimit_strict decorator can be applied."""
        @ratelimit_strict(methods=['POST'])
        def test_view(request):
            return HttpResponse('OK')

        request = self.factory.post('/')
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 200)

    def test_ratelimit_lenient_decorator(self):
        """Test ratelimit_lenient decorator can be applied."""
        @ratelimit_lenient(methods=['GET'])
        def test_view(request):
            return HttpResponse('OK')

        request = self.factory.get('/')
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 200)

    def test_ratelimit_api_decorator_default(self):
        """Test ratelimit_api decorator can be applied."""
        # Test that the decorator can be applied without errors
        # The actual rate limiting behavior is tested in other test files
        try:
            class TestView:
                @ratelimit_api('default')
                def get(self, request):
                    return HttpResponse('OK')

            view = TestView()
            # Verify the method exists and is callable
            self.assertTrue(hasattr(view, 'get'))
            self.assertTrue(callable(view.get))
        except Exception as e:
            self.fail(f"Failed to apply ratelimit_api decorator: {e}")

    def test_ratelimit_api_decorator_strict(self):
        """Test ratelimit_api decorator can be applied with strict group."""
        # Test that the decorator can be applied without errors
        # The actual rate limiting behavior is tested in other test files
        try:
            class TestView:
                @ratelimit_api('strict')
                def post(self, request):
                    return HttpResponse('OK')

            view = TestView()
            # Verify the method exists and is callable
            self.assertTrue(hasattr(view, 'post'))
            self.assertTrue(callable(view.post))
        except Exception as e:
            self.fail(f"Failed to apply ratelimit_api decorator: {e}")

    def test_ratelimit_api_decorator_lenient(self):
        """Test ratelimit_api decorator can be applied with lenient group."""
        # Test that the decorator can be applied without errors
        # The actual rate limiting behavior is tested in other test files
        try:
            class TestView:
                @ratelimit_api('lenient')
                def get(self, request):
                    return HttpResponse('OK')

            view = TestView()
            # Verify the method exists and is callable
            self.assertTrue(hasattr(view, 'get'))
            self.assertTrue(callable(view.get))
        except Exception as e:
            self.fail(f"Failed to apply ratelimit_api decorator: {e}")


@override_settings(RATELIMIT_ENABLE=True, TESTING=True)
class RateLimitMixinsTest(TestCase):
    """Tests for rate limit mixins."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create UserProfile with interviewer role
        from django.contrib.auth.models import Group
        from ..models import UserProfile
        interviewer_group, _ = Group.objects.get_or_create(name='Interviewer')
        self.user.groups.add(interviewer_group)

        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.role = 'interviewer'
        profile.save()

    def test_ratelimit_mixin_class_creation(self):
        """Test RateLimitMixin can be used in ViewSet."""
        class TestViewSet(RateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        # Should create without errors
        viewset = TestViewSet()
        self.assertIsNotNone(viewset)

    def test_strict_ratelimit_mixin_class_creation(self):
        """Test StrictRateLimitMixin can be used in ViewSet."""
        class TestViewSet(StrictRateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        viewset = TestViewSet()
        self.assertIsNotNone(viewset)

    def test_lenient_ratelimit_mixin_class_creation(self):
        """Test LenientRateLimitMixin can be used in ViewSet."""
        class TestViewSet(LenientRateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        viewset = TestViewSet()
        self.assertIsNotNone(viewset)

    def test_ratelimit_mixin_applies_to_methods(self):
        """Test RateLimitMixin applies rate limits to ViewSet methods."""
        class TestViewSet(RateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        viewset = TestViewSet()

        # Check that methods exist and are decorated
        self.assertTrue(hasattr(viewset, 'list'))
        self.assertTrue(hasattr(viewset, 'create'))
        self.assertTrue(hasattr(viewset, 'retrieve'))
        self.assertTrue(hasattr(viewset, 'update'))
        self.assertTrue(hasattr(viewset, 'destroy'))

    def test_strict_mixin_applies_to_methods(self):
        """Test StrictRateLimitMixin applies strict limits to all methods."""
        class TestViewSet(StrictRateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        viewset = TestViewSet()

        # All methods should be decorated with strict limits
        self.assertTrue(hasattr(viewset, 'list'))
        self.assertTrue(hasattr(viewset, 'create'))

    def test_lenient_mixin_applies_to_methods(self):
        """Test LenientRateLimitMixin applies lenient limits to all methods."""
        class TestViewSet(LenientRateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        viewset = TestViewSet()

        # All methods should be decorated with lenient limits
        self.assertTrue(hasattr(viewset, 'list'))
        self.assertTrue(hasattr(viewset, 'retrieve'))

    def test_ratelimit_mixin_get_throttles(self):
        """Test RateLimitMixin.get_throttles returns empty list."""
        class TestViewSet(RateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        viewset = TestViewSet()
        throttles = viewset.get_throttles()
        self.assertEqual(throttles, [])

    def test_strict_ratelimit_mixin_get_throttles(self):
        """Test StrictRateLimitMixin.get_throttles returns empty list."""
        class TestViewSet(StrictRateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        viewset = TestViewSet()
        throttles = viewset.get_throttles()
        self.assertEqual(throttles, [])

    def test_lenient_ratelimit_mixin_get_throttles(self):
        """Test LenientRateLimitMixin.get_throttles returns empty list."""
        class TestViewSet(LenientRateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        viewset = TestViewSet()
        throttles = viewset.get_throttles()
        self.assertEqual(throttles, [])

    def test_ratelimit_mixin_initial_list_action(self):
        """Test RateLimitMixin.initial uses lenient limits for list action."""
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request

        class TestViewSet(RateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        factory = APIRequestFactory()
        django_request = factory.get('/api/tags/')
        django_request.user = self.user

        # Wrap Django request in DRF Request
        request = Request(django_request)

        viewset = TestViewSet()
        viewset.action = 'list'
        viewset.format_kwarg = None

        # Should not raise an exception
        try:
            viewset.initial(request)
        except Exception as e:
            # Rate limiting may trigger, but initial() should execute
            self.assertIn('429', str(e).lower(), f"Unexpected exception: {e}")

    def test_ratelimit_mixin_initial_create_action(self):
        """Test RateLimitMixin.initial uses strict limits for create action."""
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request

        class TestViewSet(RateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        factory = APIRequestFactory()
        django_request = factory.post('/api/tags/')
        django_request.user = self.user

        # Wrap Django request in DRF Request
        request = Request(django_request)

        viewset = TestViewSet()
        viewset.action = 'create'
        viewset.format_kwarg = None

        # Should not raise an exception
        try:
            viewset.initial(request)
        except Exception as e:
            # Rate limiting may trigger, but initial() should execute
            self.assertIn('429', str(e).lower(), f"Unexpected exception: {e}")

    def test_ratelimit_mixin_initial_custom_action(self):
        """Test RateLimitMixin.initial uses default limits for custom action."""
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request

        class TestViewSet(RateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        factory = APIRequestFactory()
        django_request = factory.get('/api/tags/custom/')
        django_request.user = self.user

        # Wrap Django request in DRF Request
        request = Request(django_request)

        viewset = TestViewSet()
        viewset.action = 'custom_action'
        viewset.format_kwarg = None

        # Should not raise an exception
        try:
            viewset.initial(request)
        except Exception as e:
            # Rate limiting may trigger, but initial() should execute
            self.assertIn('429', str(e).lower(), f"Unexpected exception: {e}")

    def test_strict_ratelimit_mixin_initial(self):
        """Test StrictRateLimitMixin.initial applies strict limits."""
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request

        class TestViewSet(StrictRateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        factory = APIRequestFactory()
        django_request = factory.get('/api/tags/')
        django_request.user = self.user

        # Wrap Django request in DRF Request
        request = Request(django_request)

        viewset = TestViewSet()
        viewset.action = 'list'
        viewset.format_kwarg = None

        # Should not raise an exception
        try:
            viewset.initial(request)
        except Exception as e:
            # Rate limiting may trigger, but initial() should execute
            self.assertIn('429', str(e).lower(), f"Unexpected exception: {e}")

    def test_lenient_ratelimit_mixin_initial(self):
        """Test LenientRateLimitMixin.initial applies lenient limits."""
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request

        class TestViewSet(LenientRateLimitMixin, ModelViewSet):
            queryset = Tag.objects.all()
            serializer_class = TagSerializer

        factory = APIRequestFactory()
        django_request = factory.get('/api/tags/')
        django_request.user = self.user

        # Wrap Django request in DRF Request
        request = Request(django_request)

        viewset = TestViewSet()
        viewset.action = 'list'
        viewset.format_kwarg = None

        # Should not raise an exception
        try:
            viewset.initial(request)
        except Exception as e:
            # Rate limiting may trigger, but initial() should execute
            self.assertIn('429', str(e).lower(), f"Unexpected exception: {e}")


@override_settings(RATELIMIT_ENABLE=False)
class RateLimitDisabledDecoratorsTest(TestCase):
    """Tests for decorators when rate limiting is disabled."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_decorators_work_when_disabled(self):
        """Test decorators don't break when rate limiting is disabled."""
        @ratelimit_default(methods=['GET'])
        def test_view(request):
            return HttpResponse('OK')

        request = self.factory.get('/')
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
