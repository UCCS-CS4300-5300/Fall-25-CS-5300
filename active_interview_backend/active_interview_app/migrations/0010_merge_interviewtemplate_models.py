# Custom migration to merge InterviewTemplate models from both branches
# Generated manually on 2025-11-10

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('active_interview_app', '0009_merge_20251110_2046'),
    ]

    operations = [
        # The main branch version (with user, description, sections) is what exists
        # The tags M2M relationship already exists from the question bank migration
        # Add remaining question bank integration fields
        migrations.AddField(
            model_name='interviewtemplate',
            name='question_count',
            field=models.IntegerField(default=5, help_text='Number of questions for auto-assembly', validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AddField(
            model_name='interviewtemplate',
            name='easy_percentage',
            field=models.IntegerField(default=30, help_text='Percentage of easy questions', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AddField(
            model_name='interviewtemplate',
            name='medium_percentage',
            field=models.IntegerField(default=50, help_text='Percentage of medium questions', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AddField(
            model_name='interviewtemplate',
            name='hard_percentage',
            field=models.IntegerField(default=20, help_text='Percentage of hard questions', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
        # Skip tags - already exists from 0008_tag_questionbank_question_interviewtemplate
        migrations.AddField(
            model_name='interviewtemplate',
            name='question_banks',
            field=models.ManyToManyField(blank=True, help_text='Question banks to use for auto-assembly', related_name='templates', to='active_interview_app.questionbank'),
        ),
        migrations.AddField(
            model_name='interviewtemplate',
            name='use_auto_assembly',
            field=models.BooleanField(default=False, help_text='Enable automatic interview assembly from question banks'),
        ),
    ]
