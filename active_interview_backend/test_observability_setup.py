"""
Diagnostic script to test observability dashboard setup.
Run with: python test_observability_setup.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'active_interview_backend.settings')

# Add parent directory to path for proper imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

django.setup()

print("=" * 60)
print("OBSERVABILITY DASHBOARD DIAGNOSTIC")
print("=" * 60)

# Test 1: Check if observability_views can be imported
print("\n1. Testing observability_views import...")
try:
    from active_interview_app import observability_views
    print("   ✓ observability_views imported successfully")
except ImportError as e:
    print(f"   ✗ FAILED to import observability_views: {e}")
    sys.exit(1)

# Test 2: Check if view functions exist
print("\n2. Checking view functions...")
view_functions = [
    'observability_dashboard',
    'api_metrics_rps',
    'api_metrics_latency',
    'api_metrics_errors',
    'api_metrics_costs',
    'api_export_metrics'
]
for func_name in view_functions:
    if hasattr(observability_views, func_name):
        print(f"   ✓ {func_name} exists")
    else:
        print(f"   ✗ {func_name} MISSING")

# Test 3: Check if models can be imported
print("\n3. Testing observability models import...")
try:
    from active_interview_app.observability_models import (
        RequestMetric,
        DailyMetricsSummary,
        ProviderCostDaily,
        ErrorLog
    )
    print("   ✓ All observability models imported successfully")
except ImportError as e:
    print(f"   ✗ FAILED to import models: {e}")
    sys.exit(1)

# Test 4: Check if database tables exist
print("\n4. Checking database tables...")
from django.db import connection
tables = connection.introspection.table_names()
required_tables = [
    'active_interview_app_requestmetric',
    'active_interview_app_dailymetricssummary',
    'active_interview_app_providercostdaily',
    'active_interview_app_errorlog'
]
for table in required_tables:
    if table in tables:
        print(f"   ✓ {table} exists")
    else:
        print(f"   ✗ {table} MISSING")

# Test 5: Check URL patterns
print("\n5. Checking URL registration...")
from django.urls import reverse, NoReverseMatch
url_names = [
    'observability_dashboard',
    'api_metrics_rps',
    'api_metrics_latency',
    'api_metrics_errors',
    'api_metrics_costs',
    'api_export_metrics'
]
for url_name in url_names:
    try:
        url = reverse(url_name)
        print(f"   ✓ {url_name} -> {url}")
    except NoReverseMatch:
        print(f"   ✗ {url_name} NOT FOUND")

# Test 6: Check if template exists
print("\n6. Checking template...")
import os
template_path = os.path.join(
    os.path.dirname(__file__),
    'active_interview_app',
    'templates',
    'admin',
    'observability_dashboard.html'
)
if os.path.exists(template_path):
    print(f"   ✓ Template exists at {template_path}")
else:
    print(f"   ✗ Template MISSING at {template_path}")

# Test 7: Try to create a test request
print("\n7. Testing RequestMetric creation...")
try:
    from django.utils import timezone
    metric = RequestMetric.objects.create(
        endpoint='/test/',
        method='GET',
        status_code=200,
        response_time_ms=100.0,
        timestamp=timezone.now()
    )
    print(f"   ✓ Created RequestMetric: {metric.id}")
    metric.delete()
    print(f"   ✓ Deleted test metric")
except Exception as e:
    print(f"   ✗ FAILED to create RequestMetric: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
