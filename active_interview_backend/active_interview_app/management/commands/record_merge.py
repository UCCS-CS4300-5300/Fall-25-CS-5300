"""
Management command to record token usage statistics when a branch is merged.
This is called by the GitHub Actions workflow after a PR is merged.
"""
import sys
import json
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from active_interview_app.merge_stats_models import MergeTokenStats
from active_interview_app.token_usage_models import TokenUsage


class Command(BaseCommand):
    help = 'Record token usage statistics for a merged branch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-branch',
            type=str,
            required=True,
            help='Name of the branch that was merged'
        )
        parser.add_argument(
            '--target-branch',
            type=str,
            default='main',
            help='Name of the branch that received the merge (default: main)'
        )
        parser.add_argument(
            '--commit-sha',
            type=str,
            required=True,
            help='Git commit SHA of the merge'
        )
        parser.add_argument(
            '--merged-by',
            type=str,
            help='Username of the person who merged (optional)'
        )
        parser.add_argument(
            '--pr-number',
            type=int,
            help='Pull request number (optional)'
        )
        parser.add_argument(
            '--output-json',
            action='store_true',
            help='Output results as JSON for GitHub Actions'
        )

    def handle(self, *args, **options):
        source_branch = options['source_branch']
        target_branch = options['target_branch']
        commit_sha = options['commit_sha']
        merged_by_username = options.get('merged_by')
        pr_number = options.get('pr_number')
        output_json = options.get('output_json', False)

        # Get the user if username provided
        merged_by = None
        if merged_by_username:
            try:
                merged_by = User.objects.get(username=merged_by_username)
            except User.DoesNotExist:
                if not output_json:
                    self.stdout.write(
                        self.style.WARNING(
                            f'User "{merged_by_username}" not found. '
                            'Recording merge without user attribution.'
                        )
                    )

        # Check if this merge has already been recorded
        if MergeTokenStats.objects.filter(
                merge_commit_sha=commit_sha).exists():
            if output_json:
                existing = MergeTokenStats.objects.get(
                    merge_commit_sha=commit_sha
                )
                print(json.dumps(existing.get_breakdown_summary(), indent=2))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Merge {commit_sha} has already been recorded. '
                        'Skipping.'
                    )
                )
            return

        # Get token usage summary for this branch
        branch_summary = TokenUsage.get_branch_summary(source_branch)

        if branch_summary['total_requests'] == 0:
            if output_json:
                result = {
                    'branch': source_branch,
                    'status': 'no_usage',
                    'message': 'No token usage found for this branch'
                }
                print(json.dumps(result, indent=2))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'No token usage found for branch "{source_branch}"'
                    )
                )
            return

        # Create the merge statistics record
        try:
            merge_stat = MergeTokenStats.create_from_branch(
                branch_name=source_branch,
                commit_sha=commit_sha,
                merged_by=merged_by,
                pr_number=pr_number
            )
            merge_stat.target_branch = target_branch
            merge_stat.save()

            # Output results
            if output_json:
                # Output as JSON for GitHub Actions to consume
                result = merge_stat.get_breakdown_summary()
                print(json.dumps(result, indent=2))
            else:
                # Human-readable output
                self.stdout.write(self.style.SUCCESS('=' * 70))
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully recorded merge statistics for '
                        f'branch: {source_branch}'
                    )
                )
                self.stdout.write(self.style.SUCCESS('=' * 70))
                self.stdout.write('')

                # Claude tokens
                self.stdout.write(self.style.SUCCESS('Claude Tokens:'))
                self.stdout.write(
                    f'  Prompt tokens:     '
                    f'{merge_stat.claude_prompt_tokens:,}'
                )
                self.stdout.write(
                    f'  Completion tokens: '
                    f'{merge_stat.claude_completion_tokens:,}'
                )
                self.stdout.write(
                    f'  Total tokens:      '
                    f'{merge_stat.claude_total_tokens:,}'
                )
                self.stdout.write(
                    f'  API requests:      '
                    f'{merge_stat.claude_request_count:,}'
                )
                self.stdout.write('')

                # ChatGPT tokens
                self.stdout.write(self.style.SUCCESS('ChatGPT Tokens:'))
                self.stdout.write(
                    f'  Prompt tokens:     '
                    f'{merge_stat.chatgpt_prompt_tokens:,}'
                )
                self.stdout.write(
                    f'  Completion tokens: '
                    f'{merge_stat.chatgpt_completion_tokens:,}'
                )
                self.stdout.write(
                    f'  Total tokens:      '
                    f'{merge_stat.chatgpt_total_tokens:,}'
                )
                self.stdout.write(
                    f'  API requests:      '
                    f'{merge_stat.chatgpt_request_count:,}'
                )
                self.stdout.write('')

                # Combined totals
                self.stdout.write(self.style.SUCCESS('Combined Totals:'))
                self.stdout.write(
                    f'  Total prompt tokens:     '
                    f'{merge_stat.total_prompt_tokens:,}'
                )
                self.stdout.write(
                    f'  Total completion tokens: '
                    f'{merge_stat.total_completion_tokens:,}'
                )
                self.stdout.write(
                    f'  Total tokens:            '
                    f'{merge_stat.total_tokens:,}'
                )
                self.stdout.write(
                    f'  Total API requests:      '
                    f'{merge_stat.request_count:,}'
                )
                self.stdout.write(
                    f'  Branch cost:             '
                    f'${merge_stat.branch_cost:.2f}'
                )
                self.stdout.write('')

                # Cumulative totals
                self.stdout.write(
                    self.style.SUCCESS('Cumulative Totals (All Merges):')
                )
                self.stdout.write(
                    f'  Claude tokens:   '
                    f'{merge_stat.cumulative_claude_tokens:,}'
                )
                self.stdout.write(
                    f'  ChatGPT tokens:  '
                    f'{merge_stat.cumulative_chatgpt_tokens:,}'
                )
                self.stdout.write(
                    f'  Total tokens:    '
                    f'{merge_stat.cumulative_total_tokens:,}'
                )
                self.stdout.write(
                    f'  Total cost:      ${merge_stat.cumulative_cost:.2f}'
                )
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('=' * 70))

        except Exception as e:
            if output_json:
                error_result = {
                    'branch': source_branch,
                    'status': 'error',
                    'message': str(e)
                }
                print(json.dumps(error_result, indent=2))
                sys.exit(1)
            else:
                raise CommandError(f'Failed to record merge statistics: {e}')
