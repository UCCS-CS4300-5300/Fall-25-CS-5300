# Generated migration for adding rationale and weight fields to ExportableReport

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('active_interview_app', '0007_alter_chat_type_userprofile_rolechangerequest'),
    ]

    operations = [
        # Add rationale fields
        migrations.AddField(
            model_name='exportablereport',
            name='professionalism_rationale',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='exportablereport',
            name='subject_knowledge_rationale',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='exportablereport',
            name='clarity_rationale',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='exportablereport',
            name='overall_rationale',
            field=models.TextField(blank=True),
        ),
        # Add weight fields
        migrations.AddField(
            model_name='exportablereport',
            name='professionalism_weight',
            field=models.IntegerField(
                default=30,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100)
                ]
            ),
        ),
        migrations.AddField(
            model_name='exportablereport',
            name='subject_knowledge_weight',
            field=models.IntegerField(
                default=40,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100)
                ]
            ),
        ),
        migrations.AddField(
            model_name='exportablereport',
            name='clarity_weight',
            field=models.IntegerField(
                default=30,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100)
                ]
            ),
        ),
    ]
