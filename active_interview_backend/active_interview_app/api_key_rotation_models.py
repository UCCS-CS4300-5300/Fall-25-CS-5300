"""
API Key Rotation models for automatic key management.

Related to Issue #10 (Cost Caps & API Key Rotation) and Issue #13 (Automatic API Key Rotation).

This module provides functionality for:
- Storing multiple API keys in a pool
- Automatic rotation on a schedule
- Audit logging of rotation events
- Security best practices (encryption, masking)
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from cryptography.fernet import Fernet
from datetime import timedelta


# Encryption key for API keys (should be stored in environment variable)
def get_encryption_key():
    """
    Get or create encryption key for API keys.

    In production, this should be stored in environment variable.
    For development, we'll generate and store it in settings.
    """
    key = getattr(settings, 'API_KEY_ENCRYPTION_KEY', None)
    if not key:
        # Generate new key (only for development)
        key = Fernet.generate_key()
        settings.API_KEY_ENCRYPTION_KEY = key
    return key


class APIKeyPool(models.Model):
    """
    Pool of API keys for rotation.

    Stores multiple OpenAI API keys that can be rotated automatically.
    Keys are encrypted at rest for security.

    Related to Issue #13 (Automatic API Key Rotation).
    """
    # Key status choices
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    PENDING = 'pending'
    REVOKED = 'revoked'

    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
        (PENDING, 'Pending'),
        (REVOKED, 'Revoked'),
    ]

    # Provider choices (extensible for future providers)
    OPENAI = 'openai'
    ANTHROPIC = 'anthropic'

    PROVIDER_CHOICES = [
        (OPENAI, 'OpenAI'),
        (ANTHROPIC, 'Anthropic'),
    ]

    # Model tier choices for cost control and fallback
    PREMIUM = 'premium'
    STANDARD = 'standard'
    FALLBACK = 'fallback'

    TIER_CHOICES = [
        (PREMIUM, 'Premium (GPT-4o, Claude Opus)'),
        (STANDARD, 'Standard (GPT-4-turbo, Claude Sonnet)'),
        (FALLBACK, 'Fallback (GPT-3.5-turbo, Budget models)'),
    ]

    provider = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        default=OPENAI,
        help_text='API provider (e.g., OpenAI, Anthropic)'
    )

    model_tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default=PREMIUM,
        help_text='Model tier for cost control (premium/standard/fallback)'
    )

    key_name = models.CharField(
        max_length=255,
        help_text='Friendly name for this key (e.g., "Production Key 1")'
    )

    encrypted_key = models.BinaryField(
        help_text='Encrypted API key value'
    )

    key_prefix = models.CharField(
        max_length=20,
        help_text='First few characters of key for identification (e.g., "sk-proj-abc...")'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        help_text='Current status of this key'
    )

    # Usage tracking
    usage_count = models.IntegerField(
        default=0,
        help_text='Number of times this key has been used'
    )

    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time this key was used for an API call'
    )

    # Metadata
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_api_keys',
        help_text='Admin who added this key'
    )

    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Rotation tracking
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this key was activated'
    )

    deactivated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this key was deactivated'
    )

    notes = models.TextField(
        blank=True,
        help_text='Optional notes about this key'
    )

    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Key Pool'
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['provider', 'model_tier', 'status']),
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['status', '-added_at']),
        ]

    def __str__(self):
        masked_key = self.get_masked_key()
        return f"{self.key_name} ({masked_key}) - {self.status}"

    def set_key(self, api_key):
        """
        Encrypt and store the API key.

        Args:
            api_key (str): The plaintext API key
        """
        # Store key prefix for identification
        self.key_prefix = api_key[:20] if len(api_key) >= 20 else api_key

        # Encrypt the key
        f = Fernet(get_encryption_key())
        self.encrypted_key = f.encrypt(api_key.encode())

    def get_key(self):
        """
        Decrypt and return the API key.

        Returns:
            str: The plaintext API key

        Raises:
            ValueError: If decryption fails
        """
        try:
            f = Fernet(get_encryption_key())
            return f.decrypt(self.encrypted_key).decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {e}")

    def get_masked_key(self):
        """
        Get a masked version of the key for display.

        Returns:
            str: Masked key (e.g., "sk-proj-abc...xyz")
        """
        if len(self.key_prefix) > 10:
            return f"{self.key_prefix[:10]}...{self.key_prefix[-4:]}"
        return self.key_prefix

    def activate(self):
        """
        Activate this key and deactivate all others for the same provider and tier.
        """
        # Deactivate all other active keys for this provider AND tier
        APIKeyPool.objects.filter(
            provider=self.provider,
            model_tier=self.model_tier,
            status=self.ACTIVE
        ).exclude(pk=self.pk).update(
            status=self.INACTIVE,
            deactivated_at=timezone.now()
        )

        # Activate this key
        self.status = self.ACTIVE
        self.activated_at = timezone.now()
        self.save()

    def deactivate(self):
        """Deactivate this key."""
        self.status = self.INACTIVE
        self.deactivated_at = timezone.now()
        self.save()

    def revoke(self):
        """
        Revoke this key (cannot be reactivated).
        Use this when a key is compromised or no longer valid.
        """
        self.status = self.REVOKED
        self.deactivated_at = timezone.now()
        self.save()

    def increment_usage(self):
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['usage_count', 'last_used_at'])

    @classmethod
    def get_active_key(cls, provider=OPENAI, model_tier=PREMIUM):
        """
        Get the currently active key for a provider and tier.

        Args:
            provider (str): Provider name (default: 'openai')
            model_tier (str): Model tier (default: 'premium')

        Returns:
            APIKeyPool: Active key or None
        """
        try:
            return cls.objects.get(
                provider=provider,
                model_tier=model_tier,
                status=cls.ACTIVE
            )
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            # Should not happen due to activate() logic, but handle gracefully
            return cls.objects.filter(
                provider=provider,
                model_tier=model_tier,
                status=cls.ACTIVE
            ).first()

    @classmethod
    def get_next_key_for_rotation(cls, provider=OPENAI, model_tier=PREMIUM):
        """
        Get the next key to rotate to for a provider and tier.

        Uses round-robin strategy based on last activated time.

        Args:
            provider (str): Provider name (default: 'openai')
            model_tier (str): Model tier (default: 'premium')

        Returns:
            APIKeyPool: Next key to use or None
        """
        # Get all inactive/pending keys for this provider and tier
        available_keys = cls.objects.filter(
            provider=provider,
            model_tier=model_tier,
            status__in=[cls.INACTIVE, cls.PENDING]
        ).order_by('activated_at', 'added_at')

        return available_keys.first()


class KeyRotationSchedule(models.Model):
    """
    Configuration for automatic key rotation schedule.

    Defines when and how API keys should be rotated.

    Related to Issue #13 (Automatic API Key Rotation).
    """
    # Rotation frequency choices
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'

    FREQUENCY_CHOICES = [
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
        (QUARTERLY, 'Quarterly'),
    ]

    provider = models.CharField(
        max_length=50,
        choices=APIKeyPool.PROVIDER_CHOICES,
        default=APIKeyPool.OPENAI,
        help_text='API provider this schedule applies to'
    )

    model_tier = models.CharField(
        max_length=20,
        choices=APIKeyPool.TIER_CHOICES,
        default=APIKeyPool.PREMIUM,
        help_text='Model tier for this rotation schedule'
    )

    is_enabled = models.BooleanField(
        default=False,
        help_text='Whether automatic rotation is enabled'
    )

    rotation_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default=WEEKLY,
        help_text='How often to rotate keys'
    )

    last_rotation_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the last rotation occurred'
    )

    next_rotation_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the next rotation is scheduled'
    )

    # Notification settings
    notify_on_rotation = models.BooleanField(
        default=True,
        help_text='Send notification when rotation occurs'
    )

    notification_email = models.EmailField(
        blank=True,
        help_text='Email address for rotation notifications'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Admin who configured this schedule'
    )

    class Meta:
        verbose_name = 'Key Rotation Schedule'
        verbose_name_plural = 'Key Rotation Schedules'
        ordering = ['provider', 'model_tier']
        unique_together = ['provider', 'model_tier']

    def __str__(self):
        status = "Enabled" if self.is_enabled else "Disabled"
        return f"{self.get_provider_display()} {self.get_model_tier_display()} - {self.get_rotation_frequency_display()} ({status})"

    def calculate_next_rotation(self):
        """
        Calculate when the next rotation should occur based on frequency.

        Returns:
            datetime: Next rotation time
        """
        base_time = self.last_rotation_at or timezone.now()

        if self.rotation_frequency == self.DAILY:
            delta = timedelta(days=1)
        elif self.rotation_frequency == self.WEEKLY:
            delta = timedelta(weeks=1)
        elif self.rotation_frequency == self.MONTHLY:
            delta = timedelta(days=30)
        elif self.rotation_frequency == self.QUARTERLY:
            delta = timedelta(days=90)
        else:
            delta = timedelta(weeks=1)  # Default to weekly

        return base_time + delta

    def update_next_rotation(self):
        """Update the next_rotation_at field based on current settings."""
        self.next_rotation_at = self.calculate_next_rotation()
        self.save(update_fields=['next_rotation_at'])

    def is_rotation_due(self):
        """
        Check if rotation is due based on schedule.

        Returns:
            bool: True if rotation should occur now
        """
        if not self.is_enabled:
            return False

        if not self.next_rotation_at:
            return True  # Never rotated, do it now

        return timezone.now() >= self.next_rotation_at

    @classmethod
    def get_or_create_for_provider(cls, provider=APIKeyPool.OPENAI, model_tier=APIKeyPool.PREMIUM):
        """
        Get or create rotation schedule for a provider and tier.

        Args:
            provider (str): Provider name
            model_tier (str): Model tier (default: 'premium')

        Returns:
            tuple: (KeyRotationSchedule, created)
        """
        return cls.objects.get_or_create(
            provider=provider,
            model_tier=model_tier,
            defaults={
                'is_enabled': False,
                'rotation_frequency': cls.WEEKLY
            }
        )


class KeyRotationLog(models.Model):
    """
    Audit log for API key rotation events.

    Tracks all rotation events for security and compliance.

    Related to Issue #13 (Automatic API Key Rotation).
    """
    # Rotation status choices
    SUCCESS = 'success'
    FAILED = 'failed'
    SKIPPED = 'skipped'

    STATUS_CHOICES = [
        (SUCCESS, 'Success'),
        (FAILED, 'Failed'),
        (SKIPPED, 'Skipped'),
    ]

    provider = models.CharField(
        max_length=50,
        choices=APIKeyPool.PROVIDER_CHOICES,
        help_text='API provider'
    )

    old_key = models.ForeignKey(
        APIKeyPool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rotation_logs_as_old_key',
        help_text='Key that was deactivated'
    )

    new_key = models.ForeignKey(
        APIKeyPool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rotation_logs_as_new_key',
        help_text='Key that was activated'
    )

    old_key_masked = models.CharField(
        max_length=50,
        help_text='Masked old key (for audit even if key is deleted)'
    )

    new_key_masked = models.CharField(
        max_length=50,
        help_text='Masked new key (for audit even if key is deleted)'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text='Result of rotation attempt'
    )

    rotation_type = models.CharField(
        max_length=20,
        default='scheduled',
        help_text='Type of rotation (scheduled, manual, forced)'
    )

    rotated_at = models.DateTimeField(auto_now_add=True)

    rotated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Admin who initiated rotation (null for automatic)'
    )

    error_message = models.TextField(
        blank=True,
        help_text='Error details if rotation failed'
    )

    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this rotation'
    )

    class Meta:
        verbose_name = 'Key Rotation Log'
        verbose_name_plural = 'Key Rotation Logs'
        ordering = ['-rotated_at']
        indexes = [
            models.Index(fields=['provider', '-rotated_at']),
            models.Index(fields=['status', '-rotated_at']),
        ]

    def __str__(self):
        return (
            f"{self.get_provider_display()} rotation "
            f"({self.old_key_masked} → {self.new_key_masked}) - "
            f"{self.status} at {self.rotated_at.strftime('%Y-%m-%d %H:%M')}"
        )

    @classmethod
    def log_rotation(cls, provider, old_key, new_key, status,
                     rotation_type='scheduled',
                     rotated_by=None, error_message='', notes=''):
        """
        Create a rotation log entry.

        Args:
            provider (str): Provider name
            old_key (APIKeyPool): Previous active key (can be None)
            new_key (APIKeyPool): Newly activated key (can be None)
            status (str): Rotation status
            rotation_type (str): Type of rotation
            rotated_by (User): User who initiated (None for automatic)
            error_message (str): Error details if failed
            notes (str): Additional notes

        Returns:
            KeyRotationLog: Created log entry
        """
        return cls.objects.create(
            provider=provider,
            old_key=old_key,
            new_key=new_key,
            old_key_masked=old_key.get_masked_key() if old_key else 'None',
            new_key_masked=new_key.get_masked_key() if new_key else 'None',
            status=status,
            rotation_type=rotation_type,
            rotated_by=rotated_by,
            error_message=error_message,
            notes=notes
        )

    @classmethod
    def get_recent_rotations(cls, provider=None, limit=10):
        """
        Get recent rotation logs.

        Args:
            provider (str): Filter by provider (None for all)
            limit (int): Number of logs to return

        Returns:
            QuerySet: Recent rotation logs
        """
        queryset = cls.objects.all()
        if provider:
            queryset = queryset.filter(provider=provider)
        return queryset[:limit]
