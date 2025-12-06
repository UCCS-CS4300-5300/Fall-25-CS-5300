"""
Management command to automatically update invitation statuses.

This command should be run periodically (e.g., every 10 minutes via cron)
to maintain accurate invitation statuses based on time and activity.

Related to Issues #7, #138, #139, #141 (Invitation Workflow).

Usage:
    python manage.py update_invitation_statuses
    python manage.py update_invitation_statuses --dry-run
    python manage.py update_invitation_statuses --verbose
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from active_interview_app.models import InvitedInterview


class Command(BaseCommand):
    help = 'Update invitation statuses based on time and activity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each invitation processed'
        )
        parser.add_argument(
            '--inactivity-minutes',
            type=int,
            default=30,
            help='Minutes of inactivity before considering an interview abandoned (default: 30)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        inactivity_threshold = options['inactivity_minutes']

        now = timezone.now()
        inactivity_cutoff = now - timedelta(minutes=inactivity_threshold)

        self.stdout.write(
            self.style.WARNING(
                f"\n{'[DRY RUN] ' if dry_run else ''}"
                f"Updating invitation statuses as of {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
        )

        # Counters for summary
        expired_count = 0
        abandoned_count = 0
        total_checked = 0

        # ==================================================================
        # 1. Mark PENDING -> EXPIRED for unstarted interviews past their window
        # ==================================================================

        pending_invitations = InvitedInterview.objects.filter(
            status=InvitedInterview.PENDING
        ).select_related('chat')

        for invitation in pending_invitations:
            total_checked += 1

            # Check if invitation window has ended
            if invitation.scheduled_time and invitation.duration_minutes:
                window_end = invitation.scheduled_time + timedelta(minutes=invitation.duration_minutes)

                if now > window_end:
                    # Interview window has ended and never started
                    expired_count += 1

                    if verbose:
                        self.stdout.write(
                            f"  - Invitation #{invitation.id} ({invitation.candidate_email}): "
                            f"PENDING -> EXPIRED (window ended {window_end})"
                        )

                    if not dry_run:
                        invitation.status = InvitedInterview.EXPIRED
                        invitation.save(update_fields=['status'])

        # ==================================================================
        # 2. Auto-finalize abandoned in-progress interviews
        # ==================================================================

        # Find invitations that are COMPLETED but chat is not finalized
        # AND have been inactive for the threshold period
        completed_invitations = InvitedInterview.objects.filter(
            status=InvitedInterview.COMPLETED
        ).select_related('chat')

        for invitation in completed_invitations:
            total_checked += 1

            # Skip if chat is already finalized
            if invitation.chat and invitation.chat.is_finalized:
                continue

            # Check if there's been activity
            if not invitation.last_activity_at:
                # No activity recorded - check if scheduled time has passed
                if invitation.scheduled_time:
                    window_end = invitation.scheduled_time + timedelta(minutes=invitation.duration_minutes or 60)

                    if now > window_end:
                        # Window ended, no activity, not finalized -> abandoned
                        abandoned_count += 1

                        if verbose:
                            self.stdout.write(
                                f"  - Invitation #{invitation.id} ({invitation.candidate_email}): "
                                f"Abandoned (no activity, window ended)"
                            )

                        if not dry_run:
                            # Auto-finalize the interview
                            self._auto_finalize_interview(invitation)
            else:
                # Check if inactive for threshold period
                if invitation.last_activity_at < inactivity_cutoff:
                    abandoned_count += 1

                    if verbose:
                        self.stdout.write(
                            f"  - Invitation #{invitation.id} ({invitation.candidate_email}): "
                            f"Abandoned (inactive since {invitation.last_activity_at})"
                        )

                    if not dry_run:
                        # Auto-finalize the interview
                        self._auto_finalize_interview(invitation)

        # ==================================================================
        # Summary
        # ==================================================================

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'[DRY RUN] ' if dry_run else ''}Summary:"
            )
        )
        self.stdout.write(f"  Total invitations checked: {total_checked}")
        self.stdout.write(
            self.style.WARNING(f"  PENDING -> EXPIRED: {expired_count}")
        )
        self.stdout.write(
            self.style.WARNING(f"  Abandoned & auto-finalized: {abandoned_count}")
        )

        if dry_run:
            self.stdout.write(
                self.style.NOTICE(
                    "\n[DRY RUN] No changes were made. "
                    "Run without --dry-run to apply changes.\n"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully updated {expired_count + abandoned_count} invitations.\n"
                )
            )

    def _auto_finalize_interview(self, invitation):
        """
        Auto-finalize an abandoned interview.

        Generates report and marks chat as finalized.
        """
        chat = invitation.chat

        if not chat or chat.is_finalized:
            return

        try:
            # Generate report with rushed qualifier
            from active_interview_app.report_utils import generate_and_save_report
            generate_and_save_report(chat, include_rushed_qualifier=True)

            # Mark chat as finalized
            chat.is_finalized = True
            chat.finalized_at = timezone.now()
            chat.save(update_fields=['is_finalized', 'finalized_at'])

            # Send completion notification to interviewer
            from active_interview_app.invitation_utils import send_completion_notification_email
            send_completion_notification_email(invitation)

            self.stdout.write(
                self.style.SUCCESS(
                    f"    -> Auto-finalized chat #{chat.id} and sent notification"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"    -> Error auto-finalizing chat #{chat.id}: {str(e)}"
                )
            )
            # Mark as finalized anyway to prevent repeated attempts
            if chat:
                chat.is_finalized = True
                chat.finalized_at = timezone.now()
                chat.save(update_fields=['is_finalized', 'finalized_at'])
