from django.contrib import admin
from .models import (
    Chat, UploadedJobListing, UploadedResume,
    ExportableReport, UserProfile, RoleChangeRequest,
    DataExportRequest, DeletionRequest,
    Tag, QuestionBank, Question, InterviewTemplate, InvitedInterview
)
from .token_usage_models import TokenUsage
from .merge_stats_models import MergeTokenStats
from .observability_models import (
    RequestMetric, DailyMetricsSummary,
    ProviderCostDaily, ErrorLog
)
from .spending_tracker_models import (
    MonthlySpendingCap, MonthlySpending
)
from .api_key_rotation_models import (
    APIKeyPool, KeyRotationSchedule, KeyRotationLog
)

# Register your models here.
admin.site.register(Chat)
admin.site.register(UploadedJobListing)
admin.site.register(UploadedResume)
admin.site.register(ExportableReport)


# Invited Interview Admin - Issue #4, #134
@admin.register(InvitedInterview)
class InvitedInterviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'interviewer',
        'candidate_email',
        'template',
        'scheduled_time',
        'status',
        'interviewer_review_status',
        'created_at'
    )
    list_filter = ('status', 'interviewer_review_status', 'scheduled_time', 'created_at')
    search_fields = (
        'candidate_email',
        'interviewer__username',
        'template__name',
        'id'
    )
    readonly_fields = ('id', 'created_at', 'invitation_sent_at', 'completed_at', 'reviewed_at')

    fieldsets = (
        ('Invitation Details', {
            'fields': (
                'id',
                'interviewer',
                'candidate_email',
                'template'
            )
        }),
        ('Schedule', {
            'fields': (
                'scheduled_time',
                'duration_minutes'
            )
        }),
        ('Status', {
            'fields': (
                'status',
                'interviewer_review_status',
                'chat'
            )
        }),
        ('Review', {
            'fields': (
                'interviewer_feedback',
                'reviewed_at'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'invitation_sent_at',
                'completed_at'
            ),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        """Optimize query with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('interviewer', 'template', 'chat')


# RBAC Admin - Issue #69
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'auth_provider',
        'created_at',
        'updated_at'
    )
    list_filter = ('role', 'auth_provider', 'created_at')
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name'
    )
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Access Control', {
            'fields': ('role', 'auth_provider'),
            'description': (
                'Role determines application-level permissions. '
                'This is separate from Django admin permissions.'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    # Make role prominently editable
    list_editable = ('role',)

    def get_queryset(self, request):
        """Optimize query with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('user')


# Role Change Requests Admin - Issue #69
@admin.register(RoleChangeRequest)
class RoleChangeRequestAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'current_role',
        'requested_role',
        'status',
        'created_at',
        'reviewed_by'
    )
    list_filter = ('status', 'requested_role', 'created_at')
    search_fields = (
        'user__username',
        'user__email',
        'reason',
        'admin_notes'
    )
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Request Information', {
            'fields': (
                'user',
                'current_role',
                'requested_role',
                'reason'
            )
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        """Optimize query with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'reviewed_by')


# Question Bank Tagging Admin
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'question_count')
    search_fields = ('name',)
    readonly_fields = ('created_at',)

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ('text', 'difficulty', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'question_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [QuestionInline]

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'question_bank', 'difficulty', 'tag_list',
                   'owner', 'created_at')
    list_filter = ('difficulty', 'created_at', 'tags')
    search_fields = ('text', 'question_bank__name', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tags',)

    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Question'

    def tag_list(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    tag_list.short_description = 'Tags'


@admin.register(InterviewTemplate)
class InterviewTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'use_auto_assembly', 'question_count',
                   'tag_list', 'difficulty_distribution', 'status', 'created_at')
    list_filter = ('use_auto_assembly', 'created_at', 'updated_at')
    search_fields = ('name', 'user__username', 'description')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tags', 'question_banks')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'user', 'description')
        }),
        ('Template Sections', {
            'fields': ('sections',),
            'description': 'JSON structure for template sections'
        }),
        ('Auto-Assembly Configuration', {
            'fields': ('use_auto_assembly', 'question_banks', 'tags',
                      'question_count', 'easy_percentage', 'medium_percentage',
                      'hard_percentage'),
            'description': 'Settings for automatically assembling interviews from question banks'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def tag_list(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()][:5]) + \
               ('...' if obj.tags.count() > 5 else '')
    tag_list.short_description = 'Tags'

    def difficulty_distribution(self, obj):
        if obj.use_auto_assembly:
            return f"E:{obj.easy_percentage}% M:{obj.medium_percentage}% H:{obj.hard_percentage}%"
        return "N/A"
    difficulty_distribution.short_description = 'Difficulty'

    def status(self, obj):
        return obj.get_status_display()
    status.short_description = 'Status'

# Token Tracking Admin
@admin.register(TokenUsage)
class TokenUsageAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'git_branch', 'model_name', 'endpoint', 'total_tokens', 'estimated_cost')
    list_filter = ('git_branch', 'model_name', 'endpoint', 'created_at')
    search_fields = ('user__username', 'git_branch', 'endpoint')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    def estimated_cost(self, obj):
        prompt_cost = (obj.prompt_tokens / 1000.0) * 0.03
        completion_cost = (obj.completion_tokens / 1000.0) * 0.06
        return f"${prompt_cost + completion_cost:.4f}"
    estimated_cost.short_description = 'Est. Cost'


@admin.register(MergeTokenStats)
class MergeTokenStatsAdmin(admin.ModelAdmin):
    list_display = ('merge_date', 'source_branch', 'target_branch', 'total_tokens', 'estimated_cost', 'cumulative_total_tokens', 'cumulative_cost', 'pr_number')
    list_filter = ('target_branch', 'merge_date')
    search_fields = ('source_branch', 'target_branch', 'merged_by', 'merge_commit_sha')
    readonly_fields = ('merge_date', 'cumulative_total_tokens', 'cumulative_cost')
    date_hierarchy = 'merge_date'

    def estimated_cost(self, obj):
        return f"${obj.branch_cost:.4f}"
    estimated_cost.short_description = 'Est. Cost'

    fieldsets = (
        ('Merge Information', {
            'fields': ('source_branch', 'target_branch', 'merge_date', 'merge_commit_sha', 'merged_by', 'pr_number')
        }),
        ('Token Usage', {
            'fields': ('total_tokens', 'total_prompt_tokens', 'total_completion_tokens', 'request_count')
        }),
        ('Cumulative Totals', {
            'fields': ('cumulative_total_tokens', 'cumulative_cost'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )


# Data Export Request Admin - Issue #63, #64
@admin.register(DataExportRequest)
class DataExportRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'status',
        'requested_at',
        'completed_at',
        'expires_at',
        'file_size_display',
        'download_count'
    )
    list_filter = ('status', 'requested_at', 'completed_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = (
        'requested_at',
        'completed_at',
        'last_downloaded_at',
        'file_size_bytes'
    )
    date_hierarchy = 'requested_at'

    fieldsets = (
        ('User & Status', {
            'fields': ('user', 'status')
        }),
        ('Export File', {
            'fields': ('export_file', 'file_size_bytes', 'download_count')
        }),
        ('Timestamps', {
            'fields': (
                'requested_at',
                'completed_at',
                'expires_at',
                'last_downloaded_at'
            )
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )

    def file_size_display(self, obj):
        if obj.file_size_bytes:
            # Convert bytes to human-readable format
            size = obj.file_size_bytes
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        return "N/A"
    file_size_display.short_description = 'File Size'

    def get_queryset(self, request):
        """Optimize query with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('user')


# Deletion Request Admin - Issue #63, #65
@admin.register(DeletionRequest)
class DeletionRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'anonymized_user_id',
        'username',
        'status',
        'requested_at',
        'completed_at',
        'total_data_deleted'
    )
    list_filter = ('status', 'requested_at', 'completed_at')
    search_fields = ('anonymized_user_id', 'username', 'email')
    readonly_fields = ('requested_at', 'completed_at')
    date_hierarchy = 'requested_at'

    fieldsets = (
        ('User Information', {
            'fields': (
                'anonymized_user_id',
                'username',
                'email',
                'status'
            )
        }),
        ('Deletion Statistics', {
            'fields': (
                'total_interviews_deleted',
                'total_resumes_deleted',
                'total_job_listings_deleted'
            )
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'completed_at')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )

    def total_data_deleted(self, obj):
        total = (
            obj.total_interviews_deleted +
            obj.total_resumes_deleted +
            obj.total_job_listings_deleted
        )
        return f"{total} items"
    total_data_deleted.short_description = 'Total Deleted'


# Observability Metrics Admin - Issues #14, #15
@admin.register(RequestMetric)
class RequestMetricAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp',
        'endpoint',
        'method',
        'status_code',
        'response_time_ms',
        'user_id',
        'is_error'
    )
    list_filter = ('method', 'status_code', 'timestamp')
    search_fields = ('endpoint', 'user_id')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

    def is_error(self, obj):
        return obj.is_error
    is_error.boolean = True
    is_error.short_description = 'Error?'


@admin.register(DailyMetricsSummary)
class DailyMetricsSummaryAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'total_requests',
        'error_rate_display',
        'avg_response_time',
        'p50_response_time',
        'p95_response_time'
    )
    list_filter = ('date',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    ordering = ('-date',)

    fieldsets = (
        ('Summary Date', {
            'fields': ('date',)
        }),
        ('Request Statistics', {
            'fields': (
                'total_requests',
                'total_errors',
                'client_errors',
                'server_errors'
            )
        }),
        ('Latency Statistics', {
            'fields': (
                'avg_response_time',
                'p50_response_time',
                'p95_response_time',
                'max_response_time'
            )
        }),
        ('Endpoint Breakdown', {
            'fields': ('endpoint_stats',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def error_rate_display(self, obj):
        return f"{obj.error_rate:.1f}%"
    error_rate_display.short_description = 'Error Rate'


@admin.register(ProviderCostDaily)
class ProviderCostDailyAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'provider',
        'service',
        'total_requests',
        'cost_display',
        'total_tokens'
    )
    list_filter = ('provider', 'service', 'date')
    search_fields = ('provider', 'service')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    ordering = ('-date', 'provider')

    fieldsets = (
        ('Provider Information', {
            'fields': ('date', 'provider', 'service')
        }),
        ('Usage Statistics', {
            'fields': (
                'total_requests',
                'total_cost_usd',
                'total_tokens',
                'prompt_tokens',
                'completion_tokens'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def cost_display(self, obj):
        return f"${obj.total_cost_usd:.4f}"
    cost_display.short_description = 'Cost (USD)'


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp',
        'endpoint',
        'method',
        'status_code',
        'error_type',
        'error_message_preview',
        'user_id'
    )
    list_filter = ('status_code', 'error_type', 'timestamp')
    search_fields = ('endpoint', 'error_type', 'error_message')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

    fieldsets = (
        ('Request Information', {
            'fields': ('timestamp', 'endpoint', 'method', 'status_code', 'user_id')
        }),
        ('Error Details', {
            'fields': ('error_type', 'error_message', 'stack_trace')
        }),
        ('Request Context', {
            'fields': ('request_data',),
            'classes': ('collapse',)
        })
    )

    def error_message_preview(self, obj):
        return obj.error_message[:100] + '...' if len(obj.error_message) > 100 else obj.error_message
    error_message_preview.short_description = 'Error Message'


# Spending Tracker Admin - Issues #10, #11, #12
@admin.register(MonthlySpendingCap)
class MonthlySpendingCapAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cap_amount_usd',
        'is_active',
        'created_by',
        'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('created_by__username',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Cap Configuration', {
            'fields': ('cap_amount_usd', 'is_active')
        }),
        ('Created By', {
            'fields': ('created_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        """Optimize query with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('created_by')


@admin.register(MonthlySpending)
class MonthlySpendingAdmin(admin.ModelAdmin):
    list_display = (
        'year_month_display',
        'total_cost_display',
        'llm_cost_display',
        'tts_cost_display',
        'total_requests',
        'cap_percentage_display',
        'alert_status'
    )
    list_filter = ('year',)
    readonly_fields = (
        'created_at',
        'updated_at',
        'last_updated_from_token_usage'
    )
    ordering = ('-year', '-month')

    fieldsets = (
        ('Period', {
            'fields': ('year', 'month')
        }),
        ('Total Costs', {
            'fields': (
                'total_cost_usd',
                'llm_cost_usd',
                'tts_cost_usd',
                'other_cost_usd'
            )
        }),
        ('Request Counts', {
            'fields': (
                'total_requests',
                'llm_requests',
                'tts_requests'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
                'last_updated_from_token_usage'
            ),
            'classes': ('collapse',)
        })
    )

    def year_month_display(self, obj):
        return f"{obj.year}-{obj.month:02d}"
    year_month_display.short_description = 'Month'
    year_month_display.admin_order_field = 'year'

    def total_cost_display(self, obj):
        return f"${obj.total_cost_usd:.2f}"
    total_cost_display.short_description = 'Total Cost'

    def llm_cost_display(self, obj):
        return f"${obj.llm_cost_usd:.2f}"
    llm_cost_display.short_description = 'LLM Cost'

    def tts_cost_display(self, obj):
        return f"${obj.tts_cost_usd:.2f}"
    tts_cost_display.short_description = 'TTS Cost'

    def cap_percentage_display(self, obj):
        percentage = obj.get_percentage_of_cap()
        if percentage is None:
            return "No cap"
        return f"{percentage:.1f}%"
    cap_percentage_display.short_description = 'Cap Usage'

    def alert_status(self, obj):
        cap_status = obj.get_cap_status()
        if not cap_status['has_cap']:
            return "-"

        alert_level = cap_status['alert_level']
        if alert_level == 'danger' or cap_status['is_over_cap']:
            return "OVER CAP"
        elif alert_level == 'critical':
            return "CRITICAL"
        elif alert_level == 'warning':
            return "Warning"
        elif alert_level == 'caution':
            return "Caution"
        else:
            return "OK"
    alert_status.short_description = 'Status'


# API Key Rotation Admin - Issues #10, #13
@admin.register(APIKeyPool)
class APIKeyPoolAdmin(admin.ModelAdmin):
    list_display = (
        'key_name',
        'provider',
        'masked_key_display',
        'status',
        'usage_count',
        'last_used_at',
        'added_by'
    )
    list_filter = ('provider', 'status', 'added_at')
    search_fields = ('key_name', 'key_prefix', 'notes')
    readonly_fields = (
        'encrypted_key',
        'key_prefix',
        'usage_count',
        'last_used_at',
        'added_at',
        'updated_at',
        'activated_at',
        'deactivated_at'
    )
    ordering = ('-added_at',)

    fieldsets = (
        ('Key Information', {
            'fields': ('provider', 'key_name', 'status')
        }),
        ('Key Details', {
            'fields': ('key_prefix', 'encrypted_key'),
            'classes': ('collapse',)
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used_at')
        }),
        ('Rotation Tracking', {
            'fields': ('activated_at', 'deactivated_at')
        }),
        ('Metadata', {
            'fields': ('added_by', 'added_at', 'updated_at', 'notes')
        })
    )

    def masked_key_display(self, obj):
        return obj.get_masked_key()
    masked_key_display.short_description = 'Key'

    def get_queryset(self, request):
        """Optimize query with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('added_by')

    def save_model(self, request, obj, form, change):
        """Set added_by to current user if creating."""
        if not change:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(KeyRotationSchedule)
class KeyRotationScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'provider',
        'rotation_frequency',
        'is_enabled',
        'last_rotation_at',
        'next_rotation_at',
        'created_by'
    )
    list_filter = ('provider', 'is_enabled', 'rotation_frequency')
    readonly_fields = ('created_at', 'updated_at', 'last_rotation_at')
    ordering = ('provider',)

    fieldsets = (
        ('Provider', {
            'fields': ('provider',)
        }),
        ('Schedule Configuration', {
            'fields': ('is_enabled', 'rotation_frequency')
        }),
        ('Rotation Status', {
            'fields': ('last_rotation_at', 'next_rotation_at')
        }),
        ('Notifications', {
            'fields': ('notify_on_rotation', 'notification_email'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        """Set created_by and update next_rotation_at."""
        if not change:
            obj.created_by = request.user
        obj.update_next_rotation()
        super().save_model(request, obj, form, change)


@admin.register(KeyRotationLog)
class KeyRotationLogAdmin(admin.ModelAdmin):
    list_display = (
        'rotated_at',
        'provider',
        'old_key_masked',
        'new_key_masked',
        'status',
        'rotation_type',
        'rotated_by'
    )
    list_filter = ('provider', 'status', 'rotation_type', 'rotated_at')
    search_fields = ('old_key_masked', 'new_key_masked', 'notes', 'error_message')
    readonly_fields = (
        'provider',
        'old_key',
        'new_key',
        'old_key_masked',
        'new_key_masked',
        'status',
        'rotation_type',
        'rotated_at',
        'rotated_by',
        'error_message',
        'notes'
    )
    ordering = ('-rotated_at',)

    fieldsets = (
        ('Rotation Details', {
            'fields': ('provider', 'rotated_at', 'rotation_type', 'status')
        }),
        ('Keys', {
            'fields': ('old_key', 'old_key_masked', 'new_key', 'new_key_masked')
        }),
        ('User', {
            'fields': ('rotated_by',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'error_message'),
            'classes': ('collapse',)
        })
    )

    def has_add_permission(self, request):
        """Prevent manual creation of rotation logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of rotation logs (audit trail)."""
        return False

    def get_queryset(self, request):
        """Optimize query with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('old_key', 'new_key', 'rotated_by')
