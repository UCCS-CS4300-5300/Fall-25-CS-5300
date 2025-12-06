"""
Management command to seed the BiasTermLibrary with initial bias terms.

Usage:
    python manage.py seed_bias_terms
    python manage.py seed_bias_terms --clear  # Clear existing terms first
    python manage.py seed_bias_terms --update  # Update existing terms

Related to Issues #18, #57, #58, #59 (Bias Guardrails).
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from active_interview_app.models import BiasTermLibrary


class Command(BaseCommand):
    help = 'Seed the BiasTermLibrary with initial bias terms for feedback detection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing bias terms before seeding',
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing terms if they already exist',
        )

    def handle(self, *args, **options):
        clear = options['clear']
        update = options['update']

        if clear:
            self.stdout.write(self.style.WARNING('Clearing existing bias terms...'))
            deleted_count = BiasTermLibrary.objects.all().delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {deleted_count} existing terms')
            )

        self.stdout.write('Seeding bias term library...')

        # Define initial bias terms
        bias_terms = self._get_initial_bias_terms()

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for term_data in bias_terms:
                term_exists = BiasTermLibrary.objects.filter(
                    term=term_data['term']
                ).exists()

                if term_exists and not update:
                    skipped_count += 1
                    continue

                if term_exists and update:
                    BiasTermLibrary.objects.filter(
                        term=term_data['term']
                    ).update(**term_data)
                    updated_count += 1
                else:
                    BiasTermLibrary.objects.create(**term_data)
                    created_count += 1

        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSeeding complete!'
                f'\n  Created: {created_count}'
                f'\n  Updated: {updated_count}'
                f'\n  Skipped: {skipped_count}'
                f'\n  Total in library: {BiasTermLibrary.objects.count()}'
            )
        )

    def _get_initial_bias_terms(self):
        """Return list of initial bias terms with full configuration."""
        return [
            # AGE-RELATED BIAS
            {
                'term': 'too old',
                'category': BiasTermLibrary.AGE,
                'pattern': r'\b(too old|very old|quite old|rather old)\b',
                'explanation': (
                    'Age-related language that may constitute age discrimination. '
                    'Focus on skills and experience rather than age.'
                ),
                'neutral_alternatives': [
                    'requires additional training in new technologies',
                    'may benefit from upskilling in modern tools',
                    'brings extensive experience to the role'
                ],
                'severity': BiasTermLibrary.BLOCKING,
                'is_active': True
            },
            {
                'term': 'too young',
                'category': BiasTermLibrary.AGE,
                'pattern': r'\b(too young|very young|quite young|immature)\b',
                'explanation': (
                    'Age-related language suggesting lack of capability due to youth. '
                    'Focus on experience level rather than age.'
                ),
                'neutral_alternatives': [
                    'requires more experience in X',
                    'early in career development',
                    'would benefit from mentorship in Y'
                ],
                'severity': BiasTermLibrary.BLOCKING,
                'is_active': True
            },
            {
                'term': 'young and energetic',
                'category': BiasTermLibrary.AGE,
                'pattern': r'\b(young and energetic|youthful energy)\b',
                'explanation': (
                    'Implies energy is correlated with youth, which is age-biased. '
                    'Use objective descriptors of work style.'
                ),
                'neutral_alternatives': [
                    'demonstrated high energy and enthusiasm',
                    'showed proactive approach',
                    'displayed strong initiative'
                ],
                'severity': BiasTermLibrary.WARNING,
                'is_active': True
            },
            {
                'term': 'overqualified',
                'category': BiasTermLibrary.AGE,
                'pattern': r'\b(overqualified|over-qualified)\b',
                'explanation': (
                    'Often used as a proxy for age discrimination. '
                    'Be specific about role fit and career goals instead.'
                ),
                'neutral_alternatives': [
                    'experience level exceeds current role requirements',
                    'may seek more senior responsibilities',
                    'career goals may not align with role scope'
                ],
                'severity': BiasTermLibrary.WARNING,
                'is_active': True
            },

            # CULTURAL/OTHER BIAS
            {
                'term': 'cultural fit',
                'category': BiasTermLibrary.OTHER,
                'pattern': r'\b(cultural fit|culture fit|good fit|poor fit|bad fit)\b',
                'explanation': (
                    'Vague and subjective term often used to mask bias based on '
                    'race, age, gender, or background. Use specific, objective criteria.'
                ),
                'neutral_alternatives': [
                    'alignment with company values',
                    'team collaboration skills',
                    'working style compatibility',
                    'communication style matches team needs'
                ],
                'severity': BiasTermLibrary.WARNING,
                'is_active': True
            },
            {
                'term': 'culture add',
                'category': BiasTermLibrary.OTHER,
                'pattern': r'\b(culture add)\b',
                'explanation': (
                    'While intended as positive, can still be subjective. '
                    'Be specific about what skills or perspectives they bring.'
                ),
                'neutral_alternatives': [
                    'brings unique perspective in X',
                    'adds expertise in Y area',
                    'contributes diverse experience in Z'
                ],
                'severity': BiasTermLibrary.WARNING,
                'is_active': True
            },

            # GENDER-RELATED BIAS
            {
                'term': 'aggressive',
                'category': BiasTermLibrary.GENDER,
                'pattern': r'\b(aggressive|abrasive|pushy|bossy)\b',
                'explanation': (
                    'These terms are often applied more harshly to women than men '
                    'for the same behavior. Use objective descriptions of actions.'
                ),
                'neutral_alternatives': [
                    'assertive in communication',
                    'direct communication style',
                    'takes initiative proactively',
                    'confident in expressing opinions'
                ],
                'severity': BiasTermLibrary.WARNING,
                'is_active': True
            },
            {
                'term': 'emotional',
                'category': BiasTermLibrary.GENDER,
                'pattern': r'\b(emotional|too emotional|overly emotional)\b',
                'explanation': (
                    'Often used as gender-biased criticism. '
                    'Describe specific behaviors objectively instead.'
                ),
                'neutral_alternatives': [
                    'expresses strong opinions',
                    'passionate about their work',
                    'demonstrated engagement with topic'
                ],
                'severity': BiasTermLibrary.WARNING,
                'is_active': True
            },

            # FAMILY STATUS BIAS
            {
                'term': 'pregnant',
                'category': BiasTermLibrary.FAMILY,
                'pattern': r'\b(pregnant|pregnancy|expecting)\b',
                'explanation': (
                    'Pregnancy status is protected and should never appear in '
                    'professional feedback. This constitutes illegal discrimination.'
                ),
                'neutral_alternatives': [
                    '[This information should not be included in feedback]'
                ],
                'severity': BiasTermLibrary.BLOCKING,
                'is_active': True
            },
            {
                'term': 'family commitments',
                'category': BiasTermLibrary.FAMILY,
                'pattern': r'\b(family (commitments|obligations|responsibilities))\b',
                'explanation': (
                    'Family status should not factor into hiring or evaluation decisions. '
                    'Focus on job performance and availability only.'
                ),
                'neutral_alternatives': [
                    'schedule availability aligns with role needs',
                    'demonstrated flexibility with work hours'
                ],
                'severity': BiasTermLibrary.BLOCKING,
                'is_active': True
            },
            {
                'term': 'single',
                'category': BiasTermLibrary.FAMILY,
                'pattern': r'\b(single|married|divorced)\b',
                'explanation': (
                    'Marital status is protected and irrelevant to job performance. '
                    'Never include in feedback.'
                ),
                'neutral_alternatives': [
                    '[This information should not be included in feedback]'
                ],
                'severity': BiasTermLibrary.BLOCKING,
                'is_active': True
            },

            # APPEARANCE BIAS
            {
                'term': 'overweight',
                'category': BiasTermLibrary.APPEARANCE,
                'pattern': r'\b(overweight|obese|fat|heavy-set|large)\b',
                'explanation': (
                    'Physical appearance comments constitute discrimination. '
                    'Focus solely on job-related qualifications.'
                ),
                'neutral_alternatives': [
                    '[Physical appearance should not be included in feedback]'
                ],
                'severity': BiasTermLibrary.BLOCKING,
                'is_active': True
            },
            {
                'term': 'attractive',
                'category': BiasTermLibrary.APPEARANCE,
                'pattern': r'\b(attractive|unattractive|good-looking|handsome|pretty)\b',
                'explanation': (
                    'Physical appearance is irrelevant to job performance and '
                    'including it constitutes bias.'
                ),
                'neutral_alternatives': [
                    '[Physical appearance should not be included in feedback]'
                ],
                'severity': BiasTermLibrary.BLOCKING,
                'is_active': True
            },
            {
                'term': 'unprofessional appearance',
                'category': BiasTermLibrary.APPEARANCE,
                'pattern': r'\b(unprofessional appearance|dressed inappropriately)\b',
                'explanation': (
                    'Appearance standards can be biased and subjective. '
                    'If attire is truly an issue, cite specific dress code policy.'
                ),
                'neutral_alternatives': [
                    'attire did not meet stated dress code policy',
                    'presentation style may not match client-facing role expectations'
                ],
                'severity': BiasTermLibrary.WARNING,
                'is_active': True
            },

            # DISABILITY BIAS
            {
                'term': 'disabled',
                'category': BiasTermLibrary.DISABILITY,
                'pattern': r'\b(disabled|handicapped|crippled)\b',
                'explanation': (
                    'Disability status is protected. Focus on ability to perform '
                    'job functions with or without accommodation.'
                ),
                'neutral_alternatives': [
                    'may require accommodation for X task',
                    'demonstrated ability to perform core functions'
                ],
                'severity': BiasTermLibrary.BLOCKING,
                'is_active': True
            },

            # RACE/ETHNICITY BIAS
            {
                'term': 'accent',
                'category': BiasTermLibrary.RACE,
                'pattern': r'\b(heavy accent|thick accent|strong accent|foreign accent)\b',
                'explanation': (
                    'Accent-based criticism can be a proxy for national origin or '
                    'race discrimination. Focus on communication effectiveness.'
                ),
                'neutral_alternatives': [
                    'communication was clear and effective',
                    'may benefit from additional clarity in technical explanations',
                    'pronunciation did not impede understanding'
                ],
                'severity': BiasTermLibrary.WARNING,
                'is_active': True
            },
            {
                'term': 'articulate',
                'category': BiasTermLibrary.RACE,
                'pattern': r'\b(articulate|well-spoken|surprisingly articulate)\b',
                'explanation': (
                    'When used for candidates of color, "articulate" can carry '
                    'bias by expressing surprise at competence. Use objectively.'
                ),
                'neutral_alternatives': [
                    'communicated ideas clearly',
                    'explained concepts effectively',
                    'strong verbal communication skills'
                ],
                'severity': BiasTermLibrary.WARNING,
                'is_active': True
            },
            {
                'term': 'diversity hire',
                'category': BiasTermLibrary.RACE,
                'pattern': r'\b(diversity hire|diversity candidate)\b',
                'explanation': (
                    'Implies candidate was hired for diversity rather than merit, '
                    'which is discriminatory and undermines their qualifications.'
                ),
                'neutral_alternatives': [
                    '[This characterization should not be used in feedback]'
                ],
                'severity': BiasTermLibrary.BLOCKING,
                'is_active': True
            },

            # ADDITIONAL GENDERED LANGUAGE
            {
                'term': 'guys',
                'category': BiasTermLibrary.GENDER,
                'pattern': r'\b(you guys|the guys|hey guys)\b',
                'explanation': (
                    'Using "guys" to refer to mixed-gender groups reinforces '
                    'male as default. Use gender-neutral alternatives.'
                ),
                'neutral_alternatives': [
                    'the team',
                    'everyone',
                    'folks',
                    'colleagues'
                ],
                'severity': BiasTermLibrary.WARNING,
                'is_active': True
            },

            # EXPERIENCE-RELATED (POTENTIAL AGE PROXY)
            {
                'term': 'fresh perspective',
                'category': BiasTermLibrary.AGE,
                'pattern': r'\b(fresh perspective|fresh ideas|new blood)\b',
                'explanation': (
                    'Can be code for preferring younger candidates. '
                    'Be specific about innovative thinking if that\'s what you mean.'
                ),
                'neutral_alternatives': [
                    'demonstrated innovative thinking',
                    'proposed creative solutions',
                    'showed novel approach to problem-solving'
                ],
                'severity': BiasTermLibrary.WARNING,
                'is_active': True
            }
        ]
