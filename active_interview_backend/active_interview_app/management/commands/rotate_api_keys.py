"""
Management command to rotate API keys with multi-tier support.

Related to Issue #13 (Automatic API Key Rotation) and Issue #14 (Fallback Tier Switching).

This command can be run manually or scheduled via cron to automatically
rotate API keys based on the configured schedule.

Usage:
    # Rotate keys if due based on schedule for all tiers
    python manage.py rotate_api_keys

    # Rotate specific tier
    python manage.py rotate_api_keys --tier premium
    python manage.py rotate_api_keys --tier fallback

    # Rotate all tiers
    python manage.py rotate_api_keys --all

    # Force rotation immediately
    python manage.py rotate_api_keys --force --tier premium

    # Rotate for specific provider
    python manage.py rotate_api_keys --provider openai --tier premium

    # Dry run (don't actually rotate)
    python manage.py rotate_api_keys --dry-run --tier premium
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from active_interview_app.api_key_rotation_models import (
    APIKeyPool,
    KeyRotationSchedule,
    KeyRotationLog
)


class Command(BaseCommand):
    help = 'Rotate API keys based on schedule or force rotation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider',
            type=str,
            default='openai',
            choices=['openai', 'anthropic'],
            help='Provider to rotate keys for (default: openai)'
        )
        parser.add_argument(
            '--tier',
            type=str,
            choices=['premium', 'standard', 'fallback'],
            help='Model tier to rotate (use --all to rotate all tiers)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Rotate all tiers for the provider'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force rotation even if not due'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be rotated without actually rotating'
        )

    def handle(self, *args, **options):
        provider = options['provider']
        tier = options.get('tier')
        rotate_all = options.get('all', False)
        force = options.get('force', False)
        dry_run = options.get('dry-run', False)

        # Determine which tiers to rotate
        if rotate_all:
            tiers_to_rotate = ['premium', 'standard', 'fallback']
        elif tier:
            tiers_to_rotate = [tier]
        else:
            # If neither specified, rotate all tiers that are due
            tiers_to_rotate = ['premium', 'standard', 'fallback']

        self.stdout.write(
            self.style.HTTP_INFO(f'API Key Rotation for {provider}')
        )
        self.stdout.write('=' * 60)

        total_rotated = 0
        total_skipped = 0

        for current_tier in tiers_to_rotate:
            self.stdout.write(f'\n--- Tier: {current_tier.upper()} ---')

            try:
                rotated = self.rotate_tier(
                    provider=provider,
                    tier=current_tier,
                    force=force,
                    dry_run=dry_run
                )

                if rotated:
                    total_rotated += 1
                else:
                    total_skipped += 1

            except CommandError as e:
                self.stdout.write(self.style.ERROR(str(e)))
                total_skipped += 1

        # Print summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            f'Summary: {total_rotated} tier(s) rotated, {total_skipped} tier(s) skipped'
        )

    def rotate_tier(self, provider, tier, force=False, dry_run=False):
        """
        Rotate keys for a specific provider and tier.

        Returns:
            bool: True if rotation occurred, False if skipped
        """
        # Get rotation schedule
        schedule, created = KeyRotationSchedule.get_or_create_for_provider(
            provider=provider,
            model_tier=tier
        )

        if created:
            self.stdout.write(
                self.style.WARNING(
                    f'Created new rotation schedule for {provider} {tier} (disabled by default)'
                )
            )

        # Check if rotation should occur
        if not force and not schedule.is_rotation_due():
            self.stdout.write(
                self.style.WARNING('Rotation not due yet')
            )
            if schedule.next_rotation_at:
                self.stdout.write(
                    f'Next rotation scheduled for: {schedule.next_rotation_at}'
                )
            return False

        if not schedule.is_enabled and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Automatic rotation is disabled. Use --force to rotate anyway.'
                )
            )
            return False

        # Get current active key
        current_key = APIKeyPool.get_active_key(provider=provider, model_tier=tier)
        if current_key:
            self.stdout.write(
                f'Current active key: {current_key.key_name} ({current_key.get_masked_key()})'
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'No active key currently set for {tier} tier')
            )

        # Get next key to rotate to
        next_key = APIKeyPool.get_next_key_for_rotation(provider=provider, model_tier=tier)

        if not next_key:
            error_msg = f'No keys available for rotation in {provider} {tier} pool'
            self.stdout.write(self.style.ERROR(error_msg))

            # Log failed rotation
            if not dry_run:
                KeyRotationLog.log_rotation(
                    provider=provider,
                    old_key=current_key,
                    new_key=None,
                    status=KeyRotationLog.FAILED,
                    rotation_type='manual' if force else 'scheduled',
                    error_message=error_msg,
                    notes=f'No available keys in {tier} tier pool'
                )

            return False  # Skip this tier instead of raising error

        self.stdout.write(
            f'Next key to activate: {next_key.key_name} ({next_key.get_masked_key()})'
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'\n[DRY RUN] Would rotate {tier} tier to this key, but not actually doing it')
            )
            return False

        # Perform rotation
        try:
            self.stdout.write('\nPerforming rotation...')

            # Activate new key (this also deactivates old ones)
            next_key.activate()

            # Update schedule
            schedule.last_rotation_at = timezone.now()
            schedule.update_next_rotation()

            # Log successful rotation
            KeyRotationLog.log_rotation(
                provider=provider,
                old_key=current_key,
                new_key=next_key,
                status=KeyRotationLog.SUCCESS,
                rotation_type='manual' if force else 'scheduled',
                notes=f'{tier} tier rotation {"forced" if force else "scheduled"}'
            )

            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Successfully rotated {tier} tier to {next_key.key_name}')
            )
            self.stdout.write(f'Old key deactivated: {current_key.key_name if current_key else "None"}')
            self.stdout.write(f'New key activated: {next_key.key_name}')
            self.stdout.write(f'Next rotation scheduled for: {schedule.next_rotation_at}')

            # Show key pool status for this tier
            self.stdout.write(f'\nKey Pool Status ({tier} tier):')
            self.stdout.write('-' * 60)
            all_keys = APIKeyPool.objects.filter(
                provider=provider,
                model_tier=tier
            ).order_by('-status', 'added_at')

            for key in all_keys:
                status_color = self.get_status_color(key.status)
                self.stdout.write(
                    f'  {status_color(key.status.upper().ljust(10))} '
                    f'{key.key_name.ljust(25)} {key.get_masked_key().ljust(20)} '
                    f'Used: {key.usage_count} times'
                )

            return True

        except Exception as e:
            error_msg = f'{tier} tier rotation failed: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))

            # Log failed rotation
            KeyRotationLog.log_rotation(
                provider=provider,
                old_key=current_key,
                new_key=next_key,
                status=KeyRotationLog.FAILED,
                rotation_type='manual' if force else 'scheduled',
                error_message=str(e),
                notes=f'{tier} tier rotation error'
            )

            return False

    def get_status_color(self, status):
        """Get style function for status."""
        if status == APIKeyPool.ACTIVE:
            return self.style.SUCCESS
        elif status == APIKeyPool.INACTIVE:
            return self.style.WARNING
        elif status == APIKeyPool.REVOKED:
            return self.style.ERROR
        else:
            return self.style.HTTP_INFO
