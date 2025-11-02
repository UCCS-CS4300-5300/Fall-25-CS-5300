from django.contrib import admin
from .models import (
    Chat, UploadedJobListing, UploadedResume,
    ExportableReport, UserProfile, RoleChangeRequest,
    Tag, QuestionBank, Question, InterviewTemplate
)
from .token_usage_models import TokenUsage
from .merge_stats_models import MergeTokenStats

# Register your models here.
admin.site.register(Chat)
admin.site.register(UploadedJobListing)
admin.site.register(UploadedResume)
admin.site.register(ExportableReport)


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
    list_display = ('name', 'owner', 'question_count', 'tag_list',
                   'difficulty_distribution', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tags',)

    def tag_list(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    tag_list.short_description = 'Tags'

    def difficulty_distribution(self, obj):
        return f"E:{obj.easy_percentage}% M:{obj.medium_percentage}% H:{obj.hard_percentage}%"
    difficulty_distribution.short_description = 'Difficulty'

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
