# Generated merge migration to resolve parallel branches

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('active_interview_app', '0004_alter_chat_type'),
        ('active_interview_app', '0005_alter_chat_type'),
    ]

    operations = [
        # No operations needed - this just merges the two branches
    ]
