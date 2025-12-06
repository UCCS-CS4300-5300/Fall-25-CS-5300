"""
Shared utilities for generating interview reports.
Centralizes AI-based report generation logic to avoid duplication.

This module provides functions to:
- Generate performance scores from interview chats
- Extract AI feedback and rationales
- Create and save ExportableReport instances

Related to: Report Generation Refactor (Phase 2)
"""

import textwrap
from .models import ExportableReport
from .openai_utils import get_openai_client, ai_available, MAX_TOKENS


def generate_and_save_report(chat, include_rushed_qualifier=False):
    """
    Generate an ExportableReport for a chat.
    Makes AI calls to extract scores, feedback, and rationales.

    This is the main entry point for report generation. It orchestrates
    all the AI calls needed to create a complete report.

    Args:
        chat: Chat instance to generate report for
        include_rushed_qualifier: If True, add note about rushed final responses
                                 (for invited interviews with time pressure)

    Returns:
        ExportableReport instance (newly created or existing)

    Raises:
        None - All exceptions are caught and handled gracefully
    """
    # Check if report already exists (avoid regeneration)
    existing = ExportableReport.objects.filter(chat=chat).first()
    if existing:
        return existing

    # Create new report
    report = ExportableReport.objects.create(chat=chat)

    # Extract scores from chat (AI call 1)
    scores = _extract_scores_from_chat(chat)
    report.professionalism_score = scores['Professionalism']
    report.subject_knowledge_score = scores['Subject Knowledge']
    report.clarity_score = scores['Clarity']
    report.overall_score = scores['Overall']

    # Extract feedback text (AI call 2)
    report.feedback_text = _extract_feedback_from_chat(chat, include_rushed_qualifier)

    # Extract rationales for each score (AI call 3)
    rationales = _extract_rationales_from_chat(chat, scores)
    report.professionalism_rationale = rationales['professionalism']
    report.subject_knowledge_rationale = rationales['subject_knowledge']
    report.clarity_rationale = rationales['clarity']
    report.overall_rationale = rationales['overall']

    # Calculate interview statistics (no AI needed)
    user_messages = [m for m in chat.messages if m.get('role') == 'user']
    assistant_messages = [m for m in chat.messages if m.get('role') == 'assistant']
    report.total_questions_asked = len(assistant_messages)
    report.total_responses_given = len(user_messages)

    # Calculate duration if timestamps available
    if chat.started_at and chat.finalized_at:
        duration = chat.finalized_at - chat.started_at
        report.interview_duration_minutes = int(duration.total_seconds() / 60)

    # Save and return
    report.save()
    return report


def _extract_scores_from_chat(chat):
    """
    Generate performance scores from chat messages using AI.

    Asks the AI to rate the interviewee in 4 categories on a 0-100 scale:
    - Professionalism
    - Subject Knowledge
    - Clarity
    - Overall

    Args:
        chat: Chat instance with messages to analyze

    Returns:
        dict: {
            'Professionalism': int (0-100),
            'Subject Knowledge': int (0-100),
            'Clarity': int (0-100),
            'Overall': int (0-100)
        }

    Note:
        Returns all zeros if AI is unavailable or parsing fails.
    """
    scores_prompt = textwrap.dedent("""\
        Based on the interview so far, please rate the interviewee in the
        following categories from 0 to 100, and return the result as integers
        only, in the following order:

        - Professionalism
        - Subject Knowledge
        - Clarity
        - Overall

        Example format:
            85
            78
            92
            81
    """)

    input_messages = list(chat.messages)
    input_messages.append({"role": "user", "content": scores_prompt})

    if not ai_available():
        return {
            'Professionalism': 0,
            'Subject Knowledge': 0,
            'Clarity': 0,
            'Overall': 0
        }

    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-4o",
            messages=input_messages,
            max_tokens=MAX_TOKENS
        )
        ai_message = response.choices[0].message.content.strip()

        # Parse scores from response (looking for lines with just digits)
        scores = [int(line.strip()) for line in ai_message.splitlines()
                  if line.strip().isdigit()]

        if len(scores) == 4:
            professionalism, subject_knowledge, clarity, overall = scores
        else:
            # Fallback if we didn't get exactly 4 scores
            professionalism, subject_knowledge, clarity, overall = [0, 0, 0, 0]

    except Exception:
        # Catch any errors (API failures, parsing issues, etc.)
        professionalism, subject_knowledge, clarity, overall = [0, 0, 0, 0]

    return {
        'Professionalism': professionalism,
        'Subject Knowledge': subject_knowledge,
        'Clarity': clarity,
        'Overall': overall
    }


def _extract_feedback_from_chat(chat, include_rushed_qualifier=False):
    """
    Generate AI feedback text from chat messages.

    Asks the AI to provide a comprehensive evaluation of the interviewee's
    performance, including strengths, areas for improvement, and overall assessment.

    Args:
        chat: Chat instance with messages to analyze
        include_rushed_qualifier: If True, adds a note about rushed final responses
                                 (useful for time-limited invited interviews)

    Returns:
        str: AI-generated feedback text

    Note:
        Returns fallback message if AI is unavailable.
    """
    # Optional note about rushed responses (for invited interviews)
    rushed_note = ""
    if include_rushed_qualifier:
        rushed_note = textwrap.dedent("""\

            NOTE: The candidate's final response(s) may have been submitted during
            the last 5 minutes of the interview window and could be rushed or incomplete.
            Please take this into consideration when evaluating those responses.
        """)

    explain_prompt = textwrap.dedent(f"""\
        Provide a comprehensive evaluation of the interviewee's performance.
        Include specific strengths, areas for improvement, and overall assessment.
        Focus on professionalism, subject knowledge, and communication clarity.
        If no response was given since start of interview, please tell them to start.
        {rushed_note}
    """)

    input_messages = list(chat.messages)
    input_messages.append({"role": "user", "content": explain_prompt})

    if not ai_available():
        return "AI features are currently unavailable."

    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-4o",
            messages=input_messages,
            max_tokens=MAX_TOKENS
        )
        return response.choices[0].message.content.strip()

    except Exception:
        return "Unable to generate feedback at this time."


def _extract_rationales_from_chat(chat, scores):
    """
    Generate rationales (explanations) for each score component using AI.

    Asks the AI to explain why each score was given, providing context
    for the numerical ratings.

    Args:
        chat: Chat instance with messages to analyze
        scores: dict with score values (from _extract_scores_from_chat)

    Returns:
        dict: {
            'professionalism': str (explanation),
            'subject_knowledge': str (explanation),
            'clarity': str (explanation),
            'overall': str (explanation)
        }

    Note:
        Returns fallback messages if AI is unavailable or parsing fails.
    """
    rationale_prompt = textwrap.dedent(f"""\
        Based on the interview, provide a brief rationale for each score.
        Format your response exactly as shown:

        Professionalism: [Explanation for score of {scores.get('Professionalism', 0)}]

        Subject Knowledge: [Explanation for score of {scores.get('Subject Knowledge', 0)}]

        Clarity: [Explanation for score of {scores.get('Clarity', 0)}]

        Overall: [Explanation for score of {scores.get('Overall', 0)}]
    """)

    input_messages = list(chat.messages)
    input_messages.append({"role": "user", "content": rationale_prompt})

    # Default rationales if AI unavailable
    default_rationales = {
        'professionalism': 'AI features are currently unavailable.',
        'subject_knowledge': 'AI features are currently unavailable.',
        'clarity': 'AI features are currently unavailable.',
        'overall': 'AI features are currently unavailable.'
    }

    if not ai_available():
        return default_rationales

    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-4o",
            messages=input_messages,
            max_tokens=MAX_TOKENS
        )
        rationale_text = response.choices[0].message.content.strip()

        # Parse the structured response
        rationales = {
            'professionalism': '',
            'subject_knowledge': '',
            'clarity': '',
            'overall': ''
        }

        current_section = None
        current_text = []

        # Process line by line to extract each section
        for line in rationale_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Detect section headers
            if line.startswith('Professionalism:'):
                if current_section and current_text:
                    rationales[current_section] = ' '.join(current_text).strip()
                current_section = 'professionalism'
                current_text = [line.split(':', 1)[1].strip()]

            elif line.startswith('Subject Knowledge:'):
                if current_section and current_text:
                    rationales[current_section] = ' '.join(current_text).strip()
                current_section = 'subject_knowledge'
                current_text = [line.split(':', 1)[1].strip()]

            elif line.startswith('Clarity:'):
                if current_section and current_text:
                    rationales[current_section] = ' '.join(current_text).strip()
                current_section = 'clarity'
                current_text = [line.split(':', 1)[1].strip()]

            elif line.startswith('Overall:'):
                if current_section and current_text:
                    rationales[current_section] = ' '.join(current_text).strip()
                current_section = 'overall'
                current_text = [line.split(':', 1)[1].strip()]

            elif current_section:
                # Continuation of current section
                current_text.append(line)

        # Save the last section
        if current_section and current_text:
            rationales[current_section] = ' '.join(current_text).strip()

        return rationales

    except Exception:
        # If anything fails, return default messages
        return {
            'professionalism': 'Unable to generate rationale at this time.',
            'subject_knowledge': 'Unable to generate rationale at this time.',
            'clarity': 'Unable to generate rationale at this time.',
            'overall': 'Unable to generate rationale at this time.'
        }
