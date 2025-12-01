from django.apps import AppConfig


class ActiveInterviewAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'active_interview_app'

    def ready(self):
        # import the signals module so that the receiver gets registered
        import active_interview_app.signals  # noqa
        # import spending signals for automatic tracking and rotation (Issue #11, #15.10)
        import active_interview_app.spending_signals  # noqa
