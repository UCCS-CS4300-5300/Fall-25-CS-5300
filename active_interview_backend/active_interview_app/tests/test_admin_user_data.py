"""
Tests for Admin interfaces related to User Data Export & Deletion.
Tests admin display methods and queryset optimizations.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from django.utils import timezone
from datetime import timedelta

from active_interview_app.models import DataExportRequest, DeletionRequest
from active_interview_app.admin import (
    DataExportRequestAdmin,
    DeletionRequestAdmin
)


class MockRequest:
    """Mock request object for admin tests"""
    pass


class DataExportRequestAdminTest(TestCase):
    """Test DataExportRequestAdmin display methods"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = DataExportRequestAdmin(DataExportRequest, self.site)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = RequestFactory()
        self.request = MockRequest()

    def test_file_size_display_bytes(self):
        """Test file size display for bytes"""
        export = DataExportRequest.objects.create(
            user=self.user,
            file_size_bytes=500
        )
        result = self.admin.file_size_display(export)
        self.assertEqual(result, "500.0 B")

    def test_file_size_display_kilobytes(self):
        """Test file size display for kilobytes"""
        export = DataExportRequest.objects.create(
            user=self.user,
            file_size_bytes=2048  # 2 KB
        )
        result = self.admin.file_size_display(export)
        self.assertEqual(result, "2.0 KB")

    def test_file_size_display_megabytes(self):
        """Test file size display for megabytes"""
        export = DataExportRequest.objects.create(
            user=self.user,
            file_size_bytes=5242880  # 5 MB
        )
        result = self.admin.file_size_display(export)
        self.assertEqual(result, "5.0 MB")

    def test_file_size_display_gigabytes(self):
        """Test file size display for gigabytes"""
        export = DataExportRequest.objects.create(
            user=self.user,
            file_size_bytes=3221225472  # 3 GB
        )
        result = self.admin.file_size_display(export)
        self.assertEqual(result, "3.0 GB")

    def test_file_size_display_terabytes(self):
        """Test file size display for terabytes"""
        export = DataExportRequest.objects.create(
            user=self.user,
            file_size_bytes=1099511627776  # 1 TB
        )
        result = self.admin.file_size_display(export)
        self.assertEqual(result, "1.0 TB")

    def test_file_size_display_none(self):
        """Test file size display when size is None"""
        export = DataExportRequest.objects.create(
            user=self.user,
            file_size_bytes=None
        )
        result = self.admin.file_size_display(export)
        self.assertEqual(result, "N/A")

    def test_file_size_display_zero(self):
        """Test file size display for zero bytes"""
        export = DataExportRequest.objects.create(
            user=self.user,
            file_size_bytes=0
        )
        result = self.admin.file_size_display(export)
        # Zero is falsy in Python, so it returns N/A
        self.assertEqual(result, "N/A")

    def test_get_queryset_optimization(self):
        """Test that get_queryset uses select_related"""
        # Create multiple export requests
        for i in range(3):
            DataExportRequest.objects.create(user=self.user)

        queryset = self.admin.get_queryset(self.request)

        # Verify queryset is optimized with select_related
        self.assertIn('user', queryset.query.select_related)

    def test_file_size_display_edge_case_1024(self):
        """Test file size display at exactly 1024 bytes (1 KB)"""
        export = DataExportRequest.objects.create(
            user=self.user,
            file_size_bytes=1024
        )
        result = self.admin.file_size_display(export)
        self.assertEqual(result, "1.0 KB")


class DeletionRequestAdminTest(TestCase):
    """Test DeletionRequestAdmin display methods"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = DeletionRequestAdmin(DeletionRequest, self.site)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_total_data_deleted_all_zeros(self):
        """Test total data deleted when all counts are zero"""
        deletion = DeletionRequest.objects.create(
            anonymized_user_id='abc123',
            username='testuser',
            email='test@example.com',
            total_interviews_deleted=0,
            total_resumes_deleted=0,
            total_job_listings_deleted=0
        )
        result = self.admin.total_data_deleted(deletion)
        self.assertEqual(result, "0 items")

    def test_total_data_deleted_with_data(self):
        """Test total data deleted with various counts"""
        deletion = DeletionRequest.objects.create(
            anonymized_user_id='abc123',
            username='testuser',
            email='test@example.com',
            total_interviews_deleted=5,
            total_resumes_deleted=3,
            total_job_listings_deleted=2
        )
        result = self.admin.total_data_deleted(deletion)
        self.assertEqual(result, "10 items")

    def test_total_data_deleted_only_interviews(self):
        """Test total data deleted with only interviews"""
        deletion = DeletionRequest.objects.create(
            anonymized_user_id='abc123',
            username='testuser',
            email='test@example.com',
            total_interviews_deleted=7,
            total_resumes_deleted=0,
            total_job_listings_deleted=0
        )
        result = self.admin.total_data_deleted(deletion)
        self.assertEqual(result, "7 items")

    def test_total_data_deleted_large_numbers(self):
        """Test total data deleted with large counts"""
        deletion = DeletionRequest.objects.create(
            anonymized_user_id='abc123',
            username='testuser',
            email='test@example.com',
            total_interviews_deleted=1000,
            total_resumes_deleted=500,
            total_job_listings_deleted=250
        )
        result = self.admin.total_data_deleted(deletion)
        self.assertEqual(result, "1750 items")

    def test_admin_list_display_configuration(self):
        """Test that admin list_display is properly configured"""
        expected_fields = (
            'id',
            'anonymized_user_id',
            'username',
            'status',
            'requested_at',
            'completed_at',
            'total_data_deleted'
        )
        self.assertEqual(self.admin.list_display, expected_fields)

    def test_admin_search_fields_configuration(self):
        """Test that admin search_fields is properly configured"""
        expected_fields = ('anonymized_user_id', 'username', 'email')
        self.assertEqual(self.admin.search_fields, expected_fields)


class AdminIntegrationTest(TestCase):
    """Integration tests for admin interfaces"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

    def test_data_export_request_admin_registered(self):
        """Test that DataExportRequestAdmin is registered"""
        from django.contrib import admin
        self.assertIn(DataExportRequest, admin.site._registry)

    def test_deletion_request_admin_registered(self):
        """Test that DeletionRequestAdmin is registered"""
        from django.contrib import admin
        self.assertIn(DeletionRequest, admin.site._registry)

    def test_data_export_admin_display_methods_callable(self):
        """Test that admin display methods are callable"""
        site = AdminSite()
        admin_instance = DataExportRequestAdmin(DataExportRequest, site)

        export = DataExportRequest.objects.create(
            user=self.user,
            file_size_bytes=1024
        )

        # Should not raise exception
        result = admin_instance.file_size_display(export)
        self.assertIsInstance(result, str)

    def test_deletion_admin_display_methods_callable(self):
        """Test that deletion admin display methods are callable"""
        site = AdminSite()
        admin_instance = DeletionRequestAdmin(DeletionRequest, site)

        deletion = DeletionRequest.objects.create(
            anonymized_user_id='test123',
            username='testuser',
            total_interviews_deleted=5,
            total_resumes_deleted=3,
            total_job_listings_deleted=2
        )

        # Should not raise exception
        result = admin_instance.total_data_deleted(deletion)
        self.assertIsInstance(result, str)
        self.assertEqual(result, "10 items")
