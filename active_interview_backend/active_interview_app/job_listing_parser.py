"""
Job Listing Parsing Service

This module provides AI-powered job description parsing functionality
using OpenAI GPT-4o. Extracts structured data (required skills,
seniority level, requirements) from job descriptions.

Issues: #21, #51, #52, #53
"""

import json
import textwrap
from typing import Dict, Any

# Import the OpenAI client utilities from openai_utils
# This ensures consistent error handling and configuration
# Updated for Issue #14: Multi-tier model selection with automatic fallback
from .openai_utils import get_openai_client, get_client_and_model, ai_available, MAX_TOKENS

# Import seniority constants from models
from .models import (
    SENIORITY_ENTRY,
    SENIORITY_MID,
    SENIORITY_SENIOR,
    SENIORITY_LEAD,
    SENIORITY_EXECUTIVE
)

# Maximum characters for job description content before truncation
# Keep first 15,000 characters (roughly 3,750 tokens)
# to prevent token limit issues
JOB_DESCRIPTION_LIMIT = 15000


def parse_job_listing_with_ai(job_description: str) -> Dict[str, Any]:
    """
    Parse job description using OpenAI to extract structured data.

    This function uses the OpenAI GPT-4o model to analyze
    job descriptions and extract:
    - Required Skills: Technical skills, tools, frameworks, soft skills
    - Seniority Level: Entry, Mid, Senior, Lead, Executive
    - Requirements: Education, experience, certifications

    Args:
        job_description (str): The job description text

    Returns:
        dict: Structured data with keys:
            - required_skills (list): List of skill strings
            - seniority_level (str): entry/mid/senior/lead/executive
            - requirements (dict): Structured requirements with keys:
                - education (list)
                - years_experience (str)
                - certifications (list)
                - responsibilities (list)

    Raises:
        ValueError: If AI unavailable, parsing fails, or invalid response

    Example:
        >>> content = "Senior Python Developer\\n5+ years\\nPython"
        >>> result = parse_job_listing_with_ai(content)
        >>> print(result['seniority_level'])
        'senior'
        >>> print(result['required_skills'])
        ['Python', 'Django']
    """
    # Check if OpenAI is available (same pattern as resume_parser.py)
    if not ai_available():
        raise ValueError(
            "OpenAI service is unavailable. Please ensure "
            "OPENAI_API_KEY is configured and valid."
        )

    # Truncate extremely long job descriptions
    # to prevent token limit issues
    if len(job_description) > JOB_DESCRIPTION_LIMIT:
        truncated = job_description[:JOB_DESCRIPTION_LIMIT]
        job_description = truncated + "\n... (truncated)"

    # System prompt for structured extraction
    system_prompt = textwrap.dedent("""
        You are a professional job description parser.
        Your task is to extract structured information from job postings
        and return it as valid JSON.

        Extract the following information:

        1. Required Skills: Extract ALL skills mentioned including:
           - Technical skills (programming languages, frameworks, tools)
           - Soft skills (leadership, communication, teamwork)
           - Domain knowledge (industry-specific expertise)
           - Years of experience requirements (e.g., "5+ years Python")

        2. Seniority Level: Infer the seniority level based on:
           - Job title (Junior, Senior, Lead, Principal, Director, etc.)
           - Years of experience required
           - Level of responsibility described
           - Team leadership expectations

           Return ONE of these exact values:
           - "entry" - Entry level, junior positions, 0-2 years
           - "mid" - Mid-level, 2-5 years experience
           - "senior" - Senior positions, 5+ years, technical expertise
           - "lead" - Lead/Principal, 7+ years, team leadership
           - "executive" - Executive, Director, VP, C-level positions

        3. Requirements: Extract structured requirements:
           - Education: Degree requirements (if mentioned)
           - Years of experience: Extract as string (e.g., "5+", "3-5")
           - Certifications: Professional certifications (if mentioned)
           - Responsibilities: Key job responsibilities and duties

        Return ONLY a valid JSON object with this exact structure
        (no markdown, no code blocks, just pure JSON):
        {
            "required_skills": ["skill1", "skill2", "skill3"],
            "seniority_level": "senior",
            "requirements": {
                "education": ["Bachelor's in CS", "Master's pref"],
                "years_experience": "5+",
                "certifications": ["AWS Certified", "PMP"],
                "responsibilities": [
                    "Lead engineering team",
                    "Design scalable systems",
                    "Mentor junior developers"
                ]
            }
        }

        Important guidelines:
        - If section not found, return empty array [] or empty string ""
        - For seniority_level, MUST return: entry/mid/senior/lead/exec
        - Extract ALL skills (combine technical and soft skills)
        - For years_experience, extract number or use "" if not specified
        - Keep responsibilities concise (1-2 sentences max per item)
        - Return pure JSON only - no markdown, no ```json blocks
    """).strip()

    # User prompt with the job description content
    user_prompt = textwrap.dedent(f"""
        Please parse the following job description and extract
        required skills, seniority level, and requirements.

        Job Description:
        \"\"\"
        {job_description}
        \"\"\"

        Return the structured data as JSON following specified format.
    """).strip()

    try:
        # Call OpenAI API with automatic tier selection (Issue #14)
        client, model, tier_info = get_client_and_model()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.3,  # Lower temp for consistent parsing
            response_format={"type": "json_object"}  # Force JSON
        )

        # Extract the response content
        response_content = response.choices[0].message.content.strip()

        # Parse the JSON response
        try:
            parsed_data = json.loads(response_content)
        except json.JSONDecodeError as e:
            # Try to clean common JSON formatting issues
            # Remove markdown code blocks if present
            cleaned = response_content.replace('```json', '')
            cleaned = cleaned.replace('```', '').strip()
            try:
                parsed_data = json.loads(cleaned)
            except json.JSONDecodeError:
                raise ValueError(
                    f"Failed to parse OpenAI response as JSON: {e}. "
                    f"Response: {response_content[:200]}"
                )

        # Validate the response structure
        if not isinstance(parsed_data, dict):
            ptype = type(parsed_data).__name__
            raise ValueError(f"Expected dict from OpenAI, got {ptype}")

        # Ensure required keys exist with proper types
        result = {
            'required_skills': parsed_data.get('required_skills', []),
            'seniority_level': parsed_data.get('seniority_level', ''),
            'requirements': parsed_data.get('requirements', {})
        }

        # Validate types
        if not isinstance(result['required_skills'], list):
            result['required_skills'] = []

        if not isinstance(result['seniority_level'], str):
            result['seniority_level'] = ''

        # Validate seniority level is one of the allowed values
        allowed = [
            SENIORITY_ENTRY,
            SENIORITY_MID,
            SENIORITY_SENIOR,
            SENIORITY_LEAD,
            SENIORITY_EXECUTIVE
        ]
        if result['seniority_level'] and \
                result['seniority_level'] not in allowed:
            # Try to map common variations
            seniority_lower = result['seniority_level'].lower()
            if 'junior' in seniority_lower or 'entry' in seniority_lower:
                result['seniority_level'] = SENIORITY_ENTRY
            elif 'mid' in seniority_lower or \
                    'intermediate' in seniority_lower:
                result['seniority_level'] = SENIORITY_MID
            elif 'senior' in seniority_lower:
                result['seniority_level'] = SENIORITY_SENIOR
            elif 'lead' in seniority_lower or \
                    'principal' in seniority_lower:
                result['seniority_level'] = SENIORITY_LEAD
            elif 'executive' in seniority_lower or \
                    'director' in seniority_lower or \
                    'vp' in seniority_lower:
                result['seniority_level'] = SENIORITY_EXECUTIVE
            else:
                result['seniority_level'] = ''  # Unknown, default empty

        if not isinstance(result['requirements'], dict):
            result['requirements'] = {}

        # Validate requirements structure
        requirements = result['requirements']
        requirements.setdefault('education', [])
        requirements.setdefault('years_experience', '')
        requirements.setdefault('certifications', [])
        requirements.setdefault('responsibilities', [])

        # Ensure lists are actually lists
        if not isinstance(requirements['education'], list):
            requirements['education'] = []
        if not isinstance(requirements['certifications'], list):
            requirements['certifications'] = []
        if not isinstance(requirements['responsibilities'], list):
            requirements['responsibilities'] = []

        # Ensure years_experience is a string
        if not isinstance(requirements['years_experience'], str):
            requirements['years_experience'] = str(
                requirements['years_experience']
            )

        return result

    except Exception as e:
        # Re-raise with sanitized error message (no API keys)
        error_msg = str(e)
        # Sanitize potential API key exposure in error messages
        if "api" in error_msg.lower() and "key" in error_msg.lower():
            error_msg = "OpenAI API authentication error"
        raise ValueError(f"Job listing parsing failed: {error_msg}")


def validate_parsed_data(data: Dict[str, Any]) -> bool:
    """
    Validate parsed job listing data has correct structure.

    Args:
        data (dict): Parsed data to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False

    required_keys = ['required_skills', 'seniority_level', 'requirements']
    if not all(key in data for key in required_keys):
        return False

    if not isinstance(data['required_skills'], list):
        return False

    if not isinstance(data['seniority_level'], str):
        return False

    if not isinstance(data['requirements'], dict):
        return False

    # Validate requirements has expected keys
    requirements = data['requirements']
    expected_req_keys = [
        'education', 'years_experience',
        'certifications', 'responsibilities'
    ]
    if not all(key in requirements for key in expected_req_keys):
        return False

    return True
