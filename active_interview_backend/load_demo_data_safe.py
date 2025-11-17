#!/usr/bin/env python
"""
Production-safe demo data loader for Active Interview application.

This script safely loads demo data without conflicts with existing production data.
It uses unique prefixes for demo users and checks for existing objects before creating.

Usage:
    python load_demo_data_safe.py

Safe to run multiple times - won't duplicate data.
"""
import os
import sys
import json
from datetime import datetime, timezone

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'active_interview_project.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.core.management.color import color_style
from django.db import IntegrityError, transaction
from active_interview_app.models import (
    UserProfile, UploadedResume, UploadedJobListing, Chat,
    ExportableReport, Tag, QuestionBank, Question, InterviewTemplate
)

style = color_style()


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(style.SUCCESS(f"  {text}"))
    print("=" * 70)


def print_section(text):
    """Print a formatted section header."""
    print("\n" + style.HTTP_INFO(f">>> {text}"))


def print_success(text):
    """Print success message."""
    print(style.SUCCESS(f"  [OK] {text}"))


def print_info(text):
    """Print info message."""
    print(f"  - {text}")


def print_warning(text):
    """Print warning message."""
    print(style.WARNING(f"  [!] {text}"))


def create_demo_users():
    """Create demo users with unique usernames."""
    print_section("Creating Demo Users")

    users_data = [
        {
            'username': 'demo_admin',
            'email': 'demo.admin@example.com',
            'first_name': 'Demo',
            'last_name': 'Admin',
            'password': 'demo123',
            'role': 'admin',
            'is_superuser': False,  # Don't give superuser in production
        },
        {
            'username': 'demo_interviewer',
            'email': 'demo.interviewer@example.com',
            'first_name': 'Demo',
            'last_name': 'Interviewer',
            'password': 'demo123',
            'role': 'interviewer',
            'is_superuser': False,
        },
        {
            'username': 'demo_candidate',
            'email': 'demo.candidate@example.com',
            'first_name': 'Demo',
            'last_name': 'Candidate',
            'password': 'demo123',
            'role': 'candidate',
            'is_superuser': False,
        }
    ]

    created_users = {}

    for user_data in users_data:
        username = user_data['username']
        role = user_data.pop('role')
        password = user_data.pop('password')

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'is_superuser': user_data['is_superuser'],
                'is_staff': False,
                'is_active': True,
            }
        )

        if created:
            user.set_password(password)
            user.save()
            print_success(f"Created user: {username} (password: {password})")
        else:
            print_info(f"User already exists: {username}")

        # Create or update profile
        profile, profile_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': role,
                'auth_provider': 'local',
            }
        )

        if profile_created:
            print_success(f"Created profile for {username} with role: {role}")
        else:
            if profile.role != role:
                profile.role = role
                profile.save()
                print_info(f"Updated role for {username} to: {role}")
            else:
                print_info(f"Profile already exists for {username}")

        created_users[username] = user

    return created_users


def create_tags():
    """Create tags for questions."""
    print_section("Creating Tags")

    tag_names = ['Python', 'Django', 'JavaScript', 'React', 'Algorithms']
    created_tags = []

    for tag_name in tag_names:
        # Tag model normalizes to lowercase with # prefix
        normalized_name = f"#{tag_name.lower()}"

        try:
            # Try to get existing tag first
            tag = Tag.objects.filter(name=normalized_name).first()
            if tag:
                print_info(f"Tag already exists: {tag_name}")
                created_tags.append(tag)
            else:
                # Create new tag (will be normalized by model's save method)
                tag = Tag.objects.create(name=tag_name)
                print_success(f"Created tag: {tag_name}")
                created_tags.append(tag)
        except IntegrityError:
            # Tag was created between check and create (race condition)
            tag = Tag.objects.get(name=normalized_name)
            print_info(f"Tag already exists: {tag_name}")
            created_tags.append(tag)

    return created_tags


def create_question_bank(owner, tags):
    """Create demo question bank with questions."""
    print_section("Creating Question Bank")

    qb, created = QuestionBank.objects.get_or_create(
        name="Demo Technical Questions",
        owner=owner,
        defaults={
            'description': 'Sample technical interview questions for demonstrations'
        }
    )

    if created:
        print_success("Created question bank: Demo Technical Questions")
    else:
        print_info("Question bank already exists: Demo Technical Questions")

    # Questions data
    questions_data = [
        {
            'text': 'Explain the difference between select_related and prefetch_related in Django ORM.',
            'difficulty': 'medium',
            'tags': ['Python', 'Django']
        },
        {
            'text': 'What are the differences between PUT and PATCH HTTP methods in REST APIs?',
            'difficulty': 'easy',
            'tags': ['Django']
        },
        {
            'text': 'Describe how you would optimize a Django application with slow database queries.',
            'difficulty': 'hard',
            'tags': ['Python', 'Django']
        },
        {
            'text': 'Explain the concept of middleware in Django and give an example use case.',
            'difficulty': 'medium',
            'tags': ['Python', 'Django']
        },
        {
            'text': 'What is the difference between git merge and git rebase?',
            'difficulty': 'medium',
            'tags': ['Algorithms']
        },
        {
            'text': 'Explain the difference between let, const, and var in JavaScript.',
            'difficulty': 'easy',
            'tags': ['JavaScript']
        },
        {
            'text': 'What are React hooks and why are they useful?',
            'difficulty': 'medium',
            'tags': ['JavaScript', 'React']
        },
        {
            'text': 'Explain the time complexity of common sorting algorithms.',
            'difficulty': 'hard',
            'tags': ['Algorithms']
        }
    ]

    created_questions = []
    tags_dict = {tag.name: tag for tag in tags}

    for q_data in questions_data:
        # Check if question already exists (by text)
        existing = Question.objects.filter(
            text=q_data['text'],
            question_bank=qb
        ).first()

        if existing:
            print_info(f"Question already exists: {q_data['text'][:50]}...")
            created_questions.append(existing)
        else:
            question = Question.objects.create(
                text=q_data['text'],
                question_bank=qb,
                difficulty=q_data['difficulty'],
                owner=owner
            )
            # Add tags
            for tag_name in q_data['tags']:
                if tag_name in tags_dict:
                    question.tags.add(tags_dict[tag_name])
            print_success(f"Created question: {q_data['text'][:50]}...")
            created_questions.append(question)

    return qb, created_questions


def create_interview_template(owner):
    """Create demo interview template."""
    print_section("Creating Interview Template")

    template, created = InterviewTemplate.objects.get_or_create(
        name="Demo Full-Stack Developer Interview",
        user=owner,
        defaults={
            'description': 'Comprehensive technical interview for full-stack developer positions covering backend, frontend, and system design.',
            'sections': [
                {
                    "id": "section-1",
                    "title": "Introduction",
                    "content": "Welcome! This interview will assess your full-stack development skills. We'll cover Python/Django, databases, algorithms, and problem-solving abilities.",
                    "order": 0,
                    "weight": 10
                },
                {
                    "id": "section-2",
                    "title": "Backend Development (Django/Python)",
                    "content": "In this section, we'll discuss your experience with Python and Django. Be prepared to explain ORM concepts, database optimization, and REST API design.",
                    "order": 1,
                    "weight": 30
                },
                {
                    "id": "section-3",
                    "title": "Frontend Development",
                    "content": "We'll explore your knowledge of JavaScript, React, and modern frontend practices. Topics include state management, component design, and performance optimization.",
                    "order": 2,
                    "weight": 25
                },
                {
                    "id": "section-4",
                    "title": "Algorithms & Problem Solving",
                    "content": "This section tests your problem-solving abilities and understanding of data structures and algorithms.",
                    "order": 3,
                    "weight": 25
                },
                {
                    "id": "section-5",
                    "title": "Closing Questions",
                    "content": "Do you have any questions about the role, team, or company? This is your opportunity to learn more about us.",
                    "order": 4,
                    "weight": 10
                }
            ],
            'use_auto_assembly': False
        }
    )

    if created:
        print_success("Created interview template: Demo Full-Stack Developer Interview")
    else:
        print_info("Interview template already exists: Demo Full-Stack Developer Interview")

    return template


def create_resume(candidate):
    """Create demo resume for candidate."""
    print_section("Creating Demo Resume")

    resume, created = UploadedResume.objects.get_or_create(
        user=candidate,
        title="Demo Candidate - Software Engineer Resume",
        defaults={
            'file': 'uploads/demo_resume.pdf',
            'content': "Demo Candidate\\nSoftware Engineer\\n\\nEXPERIENCE\\nJunior Developer at TechCorp (2022-2024)\\n- Developed web applications using Django and React\\n- Implemented REST APIs and database optimizations\\n- Collaborated with cross-functional teams\\n\\nSKILLS\\nPython, Django, JavaScript, React, PostgreSQL, Git\\n\\nEDUCATION\\nB.S. Computer Science, State University, 2022",
            'filesize': 45678,
            'original_filename': 'demo_resume.pdf',
            'skills': ['Python', 'Django', 'JavaScript', 'React', 'PostgreSQL', 'Git'],
            'experience': [
                {
                    "company": "TechCorp",
                    "title": "Junior Developer",
                    "duration": "2022-2024",
                    "description": "Developed web applications using Django and React"
                }
            ],
            'education': [
                {
                    "institution": "State University",
                    "degree": "B.S.",
                    "field": "Computer Science",
                    "year": "2022"
                }
            ],
            'parsing_status': 'success',
            'parsed_at': datetime.now(timezone.utc)
        }
    )

    if created:
        print_success("Created demo resume")
    else:
        print_info("Demo resume already exists")

    return resume


def create_job_listing(candidate):
    """Create demo job listing for candidate."""
    print_section("Creating Demo Job Listing")

    job, created = UploadedJobListing.objects.get_or_create(
        user=candidate,
        title="Software Engineer - Web Development",
        defaults={
            'file': 'uploads/demo_job.txt',
            'filename': 'demo_job.txt',
            'filepath': 'uploads/demo_job.txt',
            'content': "Software Engineer Position\\n\\nWe are seeking a talented Software Engineer to join our growing team.\\n\\nResponsibilities:\\n- Design and develop web applications using modern frameworks\\n- Write clean, maintainable code\\n- Participate in code reviews\\n- Collaborate with product team\\n\\nRequirements:\\n- 2+ years experience with Python/Django\\n- Strong understanding of databases and SQL\\n- Experience with REST APIs\\n- Excellent problem-solving skills\\n\\nBonus:\\n- Experience with React or Vue.js\\n- Knowledge of AWS or cloud platforms\\n- Contributions to open source projects"
        }
    )

    if created:
        print_success("Created demo job listing")
    else:
        print_info("Demo job listing already exists")

    return job


def create_demo_interview(candidate, resume, job_listing):
    """Create demo completed interview with chat and results."""
    print_section("Creating Demo Interview")

    chat, created = Chat.objects.get_or_create(
        owner=candidate,
        title="Demo Practice Interview - Software Engineer Position",
        defaults={
            'difficulty': 6,
            'type': 'ISK',
            'interview_type': 'PRACTICE',
            'job_listing': job_listing,
            'resume': resume,
            'messages': [
                {
                    "role": "system",
                    "content": "You are an experienced technical interviewer conducting a software engineering interview."
                },
                {
                    "role": "assistant",
                    "content": "Hello! Welcome to your practice interview for the Software Engineer position. I've reviewed your resume and the job listing. Let's start with some questions about your experience. Can you tell me about a challenging technical problem you solved at TechCorp?"
                },
                {
                    "role": "user",
                    "content": "Sure! One of the biggest challenges I faced was optimizing our database queries. We had a dashboard that was taking 8-10 seconds to load because of multiple N+1 query issues. I used Django's select_related and prefetch_related to reduce the query count from over 100 to just 5 queries, bringing the load time down to under 1 second."
                },
                {
                    "role": "assistant",
                    "content": "Excellent work on identifying and solving that performance issue! That's a common problem in Django applications. Can you explain the difference between select_related and prefetch_related, and when you would use each?"
                },
                {
                    "role": "user",
                    "content": "select_related is used for foreign key and one-to-one relationships. It creates a SQL join and retrieves related objects in a single query. prefetch_related is for many-to-many and reverse foreign key relationships. It does a separate query for each relationship and joins them in Python. I used select_related for our User foreign keys and prefetch_related for the many-to-many tags relationship."
                },
                {
                    "role": "assistant",
                    "content": "Perfect explanation! Now let's talk about your experience with REST APIs. Can you describe the difference between PUT and PATCH HTTP methods?"
                },
                {
                    "role": "user",
                    "content": "PUT is used to replace an entire resource - you send all the fields even if you're only updating one. PATCH is for partial updates where you only send the fields you want to change. At TechCorp, we used PATCH for most updates since it's more efficient and user-friendly."
                },
                {
                    "role": "assistant",
                    "content": "Great! Let me ask you about testing. How do you approach writing tests for Django applications?"
                },
                {
                    "role": "user",
                    "content": "I follow the arrange-act-assert pattern. I typically write unit tests for models and utility functions, integration tests for views and APIs, and use Django's TestCase or pytest. I aim for at least 80% code coverage and make sure to test both success and failure cases, especially edge cases and validation errors."
                },
                {
                    "role": "assistant",
                    "content": "Excellent testing practices! One final question: You mentioned Git in your skills. Can you explain the difference between git merge and git rebase, and when you would use each?"
                },
                {
                    "role": "user",
                    "content": "git merge creates a merge commit that combines two branches, preserving the complete history. git rebase moves your commits to the tip of another branch, creating a linear history. I use merge for integrating feature branches into main to preserve the feature context, and rebase when updating my feature branch with the latest main changes to keep the history clean before merging."
                },
                {
                    "role": "assistant",
                    "content": "Outstanding answers throughout the interview! You've demonstrated strong technical knowledge and practical experience. That concludes our interview. Good luck with your job search!"
                }
            ],
            'key_questions': [
                "Tell me about a challenging technical problem you solved",
                "Explain select_related vs prefetch_related in Django",
                "What's the difference between PUT and PATCH?",
                "How do you approach testing Django applications?",
                "Explain git merge vs git rebase"
            ]
        }
    )

    if created:
        print_success("Created demo interview chat")
    else:
        print_info("Demo interview chat already exists")

    # Create exportable report
    if created:
        report, report_created = ExportableReport.objects.get_or_create(
            chat=chat,
            defaults={
                'professionalism_score': 92,
                'subject_knowledge_score': 88,
                'clarity_score': 90,
                'overall_score': 89,
                'feedback_text': "Demo candidate demonstrated excellent technical knowledge and communication skills throughout the interview. Answers were clear, detailed, and showed practical experience. Successfully explained complex concepts like Django ORM optimization and version control strategies. Problem-solving approach is methodical and shows awareness of best practices including testing and code quality.",
                'professionalism_rationale': "Candidate maintained professional demeanor, provided structured responses, and demonstrated good communication skills. Responses were respectful and well-articulated.",
                'subject_knowledge_rationale': "Strong understanding of Django, Python, databases, and software engineering practices. Successfully explained N+1 query optimization, ORM methods, REST API concepts, testing strategies, and version control. Minor room for improvement in discussing advanced architectural patterns.",
                'clarity_rationale': "Explanations were clear and concise with good use of concrete examples from real experience. Technical concepts were broken down effectively for understanding.",
                'overall_rationale': "Overall excellent performance demonstrating both theoretical knowledge and practical application. Candidate would be a strong fit for mid-level software engineering positions.",
                'professionalism_weight': 30,
                'subject_knowledge_weight': 40,
                'clarity_weight': 30,
                'question_responses': [
                    {
                        "question": "Tell me about a challenging technical problem you solved",
                        "answer": "Optimized database queries from 100+ to 5 queries, reducing load time from 8-10s to under 1s",
                        "score": 95,
                        "feedback": "Excellent real-world example with specific metrics showing impact"
                    },
                    {
                        "question": "Explain select_related vs prefetch_related in Django",
                        "answer": "select_related for FK/O2O with SQL joins, prefetch_related for M2M with separate queries",
                        "score": 90,
                        "feedback": "Accurate technical explanation with practical application context"
                    },
                    {
                        "question": "What's the difference between PUT and PATCH?",
                        "answer": "PUT replaces entire resource, PATCH does partial updates",
                        "score": 85,
                        "feedback": "Correct understanding with practical usage example"
                    },
                    {
                        "question": "How do you approach testing Django applications?",
                        "answer": "Arrange-act-assert pattern, unit and integration tests, 80% coverage target, test success and failure cases",
                        "score": 90,
                        "feedback": "Comprehensive testing strategy showing best practices awareness"
                    },
                    {
                        "question": "Explain git merge vs git rebase",
                        "answer": "merge preserves history with merge commit, rebase creates linear history",
                        "score": 85,
                        "feedback": "Good explanation with appropriate use cases for each"
                    }
                ],
                'total_questions_asked': 5,
                'total_responses_given': 5,
                'interview_duration_minutes': 25,
                'pdf_generated': False
            }
        )

        if report_created:
            print_success("Created demo interview results/report")
        else:
            print_info("Demo interview report already exists")

    return chat


def display_summary(users):
    """Display summary of created demo data."""
    print_header("Demo Data Loaded Successfully!")

    print("\n" + style.HTTP_INFO("Demo Users Created:"))
    for username, user in users.items():
        role = user.profile.role if hasattr(user, 'profile') else 'unknown'
        print(f"  - {username} ({role})")
        print(f"    Email: {user.email}")
        print(f"    Password: demo123")

    print("\n" + style.HTTP_INFO("Tags:"))
    tags = Tag.objects.all()
    print(f"  {', '.join(tag.name for tag in tags)}")

    print("\n" + style.HTTP_INFO("Question Banks:"))
    for qb in QuestionBank.objects.filter(name__startswith="Demo"):
        question_count = qb.questions.count()
        print(f"  - {qb.name} ({question_count} questions)")

    print("\n" + style.HTTP_INFO("Interview Templates:"))
    for template in InterviewTemplate.objects.filter(name__startswith="Demo"):
        section_count = len(template.sections) if template.sections else 0
        print(f"  - {template.name} ({section_count} sections)")

    print("\n" + style.HTTP_INFO("Demo Interviews:"))
    demo_candidate = users.get('demo_candidate')
    if demo_candidate:
        for chat in Chat.objects.filter(owner=demo_candidate):
            print(f"  - {chat.title} ({chat.type})")
            has_report = hasattr(chat, 'exportablereport')
            if has_report:
                print(f"    - Results available (Overall Score: {chat.exportablereport.overall_score})")

    print("\n" + style.WARNING("Next Steps:"))
    print("  1. Demo users are ready to use in presentations")
    print("  2. Login with any demo user:")
    print("     - demo_admin (admin)")
    print("     - demo_interviewer (interviewer)")
    print("     - demo_candidate (candidate)")
    print("  3. All use password: demo123")
    print("  4. Demo candidate has a completed interview with results")
    print("\n" + "=" * 70 + "\n")


def main():
    """Main execution function."""
    print_header("Active Interview - Production-Safe Demo Data Loader")

    print_info("This script will create demo data for presentations")
    print_info("It will NOT delete or modify existing production data")
    print_info("Safe to run multiple times - won't create duplicates\n")

    # Create demo users
    users = create_demo_users()

    # Create tags
    tags = create_tags()

    # Create question bank
    demo_interviewer = users['demo_interviewer']
    qb, questions = create_question_bank(demo_interviewer, tags)

    # Create interview template
    template = create_interview_template(demo_interviewer)

    # Create resume and job listing for demo candidate
    demo_candidate = users['demo_candidate']
    resume = create_resume(demo_candidate)
    job_listing = create_job_listing(demo_candidate)

    # Create demo interview
    chat = create_demo_interview(demo_candidate, resume, job_listing)

    # Display summary
    display_summary(users)


if __name__ == '__main__':
    main()
