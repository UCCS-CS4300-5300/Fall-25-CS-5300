"""
Resume Parsing Service

This module provides AI-powered resume parsing functionality using OpenAI GPT-4o.
Extracts structured data (skills, experience, education) from resume text.

Issues: #48, #49, #50
"""

import json
import textwrap
from typing import Dict, List, Any

# Import the OpenAI client lazy loader from openai_utils
# This ensures consistent error handling and configuration
from .openai_utils import get_openai_client, _ai_available, MAX_TOKENS


def parse_resume_with_ai(resume_content: str) -> Dict[str, Any]:
    """
    Parse resume content using OpenAI to extract structured data.

    This function uses the OpenAI GPT-4o model to analyze resume text
    and extract:
    - Skills: List of technical and soft skills
    - Experience: Work history with company, title, duration, description
    - Education: Educational background with institution, degree, field, year

    Args:
        resume_content (str): The resume text in markdown format

    Returns:
        dict: Structured data with keys:
            - skills (list): List of skill strings
            - experience (list): List of experience dicts
            - education (list): List of education dicts

    Raises:
        ValueError: If AI is unavailable, parsing fails, or response is invalid

    Example:
        >>> content = "John Doe\\nPython Developer\\nSkills: Python, Django"
        >>> result = parse_resume_with_ai(content)
        >>> print(result['skills'])
        ['Python', 'Django']
    """
    # Check if OpenAI is available (same pattern as views.py)
    if not _ai_available():
        raise ValueError(
            "OpenAI service is unavailable. Please ensure OPENAI_API_KEY "
            "is configured and valid."
        )

    # Truncate extremely long resumes to prevent token limit issues
    # Keep first 10,000 characters (roughly 2,500 tokens)
    if len(resume_content) > 10000:
        resume_content = resume_content[:10000] + "\n... (truncated)"

    # System prompt for structured extraction
    system_prompt = textwrap.dedent("""
        You are a professional resume parser. Your task is to extract
        structured information from resumes and return it as valid JSON.

        Extract the following information:
        1. Skills: Technical skills, programming languages, tools, frameworks,
           soft skills, certifications
        2. Experience: Work history with company name, job title, duration,
           and brief description
        3. Education: Educational background with institution, degree, field
           of study, and graduation year

        Return ONLY a valid JSON object with this exact structure (no markdown,
        no code blocks, just pure JSON):
        {
            "skills": ["skill1", "skill2", "skill3"],
            "experience": [
                {
                    "company": "Company Name",
                    "title": "Job Title",
                    "duration": "Jan 2020 - Dec 2022",
                    "description": "Brief summary of responsibilities and achievements"
                }
            ],
            "education": [
                {
                    "institution": "University Name",
                    "degree": "Bachelor of Science",
                    "field": "Computer Science",
                    "year": "2019"
                }
            ]
        }

        Important guidelines:
        - If a section is not found, return an empty array [] for that field
        - Keep descriptions concise (1-2 sentences max)
        - Extract ALL skills mentioned (technical and soft skills)
        - For duration, use any format found in resume (e.g., "2020-2022",
          "Jan 2020 - Present")
        - For year in education, extract graduation year or expected year
        - Return pure JSON only - no markdown formatting, no ```json blocks
    """).strip()

    # User prompt with the resume content
    user_prompt = textwrap.dedent(f"""
        Please parse the following resume and extract skills, experience,
        and education information.

        Resume content:
        \"\"\"
        {resume_content}
        \"\"\"

        Return the structured data as JSON following the specified format.
    """).strip()

    try:
        # Call OpenAI API (same pattern as views.py)
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.3,  # Lower temperature for more consistent parsing
            response_format={"type": "json_object"}  # Force JSON response
        )

        # Extract the response content
        response_content = response.choices[0].message.content.strip()

        # Parse the JSON response
        try:
            parsed_data = json.loads(response_content)
        except json.JSONDecodeError as e:
            # Try to clean common JSON formatting issues
            # Remove markdown code blocks if present
            cleaned_content = response_content.replace('```json', '').replace('```', '').strip()
            try:
                parsed_data = json.loads(cleaned_content)
            except json.JSONDecodeError:
                raise ValueError(
                    f"Failed to parse OpenAI response as JSON: {e}. "
                    f"Response: {response_content[:200]}"
                )

        # Validate the response structure
        if not isinstance(parsed_data, dict):
            raise ValueError(
                f"Expected dict from OpenAI, got {type(parsed_data).__name__}"
            )

        # Ensure required keys exist with proper types
        result = {
            'skills': parsed_data.get('skills', []),
            'experience': parsed_data.get('experience', []),
            'education': parsed_data.get('education', [])
        }

        # Validate types
        if not isinstance(result['skills'], list):
            result['skills'] = []
        if not isinstance(result['experience'], list):
            result['experience'] = []
        if not isinstance(result['education'], list):
            result['education'] = []

        # Validate experience structure
        for exp in result['experience']:
            if not isinstance(exp, dict):
                continue
            # Ensure required fields exist (with defaults)
            exp.setdefault('company', 'Unknown')
            exp.setdefault('title', 'Unknown')
            exp.setdefault('duration', 'Unknown')
            exp.setdefault('description', '')

        # Validate education structure
        for edu in result['education']:
            if not isinstance(edu, dict):
                continue
            # Ensure required fields exist (with defaults)
            edu.setdefault('institution', 'Unknown')
            edu.setdefault('degree', 'Unknown')
            edu.setdefault('field', 'Unknown')
            edu.setdefault('year', 'Unknown')

        return result

    except Exception as e:
        # Re-raise with more context
        raise ValueError(f"Resume parsing failed: {str(e)}")


def validate_parsed_data(data: Dict[str, Any]) -> bool:
    """
    Validate that parsed resume data has the correct structure.

    Args:
        data (dict): Parsed data to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False

    required_keys = ['skills', 'experience', 'education']
    if not all(key in data for key in required_keys):
        return False

    if not isinstance(data['skills'], list):
        return False
    if not isinstance(data['experience'], list):
        return False
    if not isinstance(data['education'], list):
        return False

    return True
