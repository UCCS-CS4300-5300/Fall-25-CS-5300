from django.contrib import admin
from .models import *
from .token_usage_models import TokenUsage
from .merge_stats_models import MergeTokenStats

# Register your models here.
admin.site.register(Chat)
admin.site.register(UploadedJobListing)
admin.site.register(UploadedResume)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'auth_provider', 'created_at', 'updated_at')
    list_filter = ('auth_provider', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


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
