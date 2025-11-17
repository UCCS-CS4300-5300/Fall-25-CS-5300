"""
Unit Tests for Job Listing Parser

Tests the AI-powered job description parsing functionality.

Issues: #21, #51, #52, #53
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
from active_interview_app.job_listing_parser import (
    parse_job_listing_with_ai,
    validate_parsed_data
)


class JobListingParserTests(TestCase):
    """Test suite for job_listing_parser module"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_job_description = """
        Senior Python Developer

        We are seeking a talented Senior Python Developer to join our team.

        Requirements:
        - 5+ years of professional Python development experience
        - Strong experience with Django and Flask frameworks
        - Experience with PostgreSQL and Redis
        - Bachelor's degree in Computer Science or related field
        - AWS certification preferred

        Responsibilities:
        - Lead backend development team
        - Design and implement scalable microservices
        - Mentor junior developers
        - Code review and architectural decisions

        Skills:
        - Python, Django, Flask
        - PostgreSQL, Redis, MongoDB
        - AWS, Docker, Kubernetes
        - Git, CI/CD, Agile methodologies
        """

        self.expected_structure = {
            'required_skills': list,
            'seniority_level': str,
            'requirements': dict
        }

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_valid(self, mockai_available, mock_get_client):
        """Test successful parsing of a valid job description"""
        # Arrange
        mockai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "required_skills": ["Python", "Django", "Flask", "PostgreSQL", "AWS", "Docker"],
            "seniority_level": "senior",
            "requirements": {
                "education": ["Bachelor's in Computer Science"],
                "years_experience": "5+",
                "certifications": ["AWS"],
                "responsibilities": [
                    "Lead backend development team",
                    "Design and implement scalable microservices",
                    "Mentor junior developers"
                ]
            }
        }
        '''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai(self.sample_job_description)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertIn('required_skills', result)
        self.assertIn('seniority_level', result)
        self.assertIn('requirements', result)

        self.assertIsInstance(result['required_skills'], list)
        self.assertGreater(len(result['required_skills']), 0)

        self.assertEqual(result['seniority_level'], 'senior')

        self.assertIsInstance(result['requirements'], dict)
        self.assertIn('education', result['requirements'])
        self.assertIn('years_experience', result['requirements'])
        self.assertIn('certifications', result['requirements'])
        self.assertIn('responsibilities', result['requirements'])

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_entry_level(
            self, mockai_available, mock_get_client):
        """Test parsing of entry-level job description"""
        # Arrange
        mockai_available.return_value = True

        entry_job = """
        Junior Software Developer

        We're looking for a motivated Junior Software Developer.

        Requirements:
        - 0-2 years of programming experience
        - Bachelor's degree in Computer Science
        - Knowledge of Python or Java
        """

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "required_skills": ["Python", "Java"],
            "seniority_level": "entry",
            "requirements": {
                "education": ["Bachelor's in Computer Science"],
                "years_experience": "0-2",
                "certifications": [],
                "responsibilities": ["Write clean code", "Learn from senior developers"]
            }
        }
        '''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai(entry_job)

        # Assert
        self.assertEqual(result['seniority_level'], 'entry')
        self.assertIsInstance(result['required_skills'], list)

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_lead_level(
            self, mockai_available, mock_get_client):
        """Test parsing of lead/principal level job description"""
        # Arrange
        mockai_available.return_value = True

        lead_job = """
        Principal Engineer - Platform Architecture

        We need an experienced Principal Engineer to lead our platform team.

        Requirements:
        - 10+ years of software engineering experience
        - 5+ years in technical leadership roles
        - Master's degree preferred
        """

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "required_skills": ["Software Architecture", "Technical Leadership", "Platform Engineering"],
            "seniority_level": "lead",
            "requirements": {
                "education": ["Master's degree preferred"],
                "years_experience": "10+",
                "certifications": [],
                "responsibilities": ["Lead platform architecture", "Mentor engineering teams"]
            }
        }
        '''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai(lead_job)

        # Assert
        self.assertEqual(result['seniority_level'], 'lead')

    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_ai_unavailable(self, mockai_available):
        """Test error handling when OpenAI is unavailable"""
        # Arrange
        mockai_available.return_value = False

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            parse_job_listing_with_ai(self.sample_job_description)

        self.assertIn("OpenAI service is unavailable", str(context.exception))

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_with_truncation(
            self, mockai_available, mock_get_client):
        """Test parsing of extremely long job descriptions (truncation)"""
        # Arrange
        mockai_available.return_value = True

        # Create a job description longer than JOB_DESCRIPTION_LIMIT (15000
        # chars)
        long_job = "Senior Developer\n" + ("Long description. " * 1000)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "required_skills": ["Python"],
            "seniority_level": "senior",
            "requirements": {
                "education": [],
                "years_experience": "",
                "certifications": [],
                "responsibilities": []
            }
        }
        '''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai(long_job)

        # Assert
        self.assertIsInstance(result, dict)
        # Verify the API was called (truncation happened internally)
        mock_client.chat.completions.create.assert_called_once()

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_invalid_json_recovery(
            self, mockai_available, mock_get_client):
        """Test recovery from markdown-wrapped JSON response"""
        # Arrange
        mockai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # OpenAI sometimes wraps JSON in markdown code blocks despite
        # json_object format
        mock_response.choices[0].message.content = '''```json
        {
            "required_skills": ["Python"],
            "seniority_level": "senior",
            "requirements": {
                "education": [],
                "years_experience": "5+",
                "certifications": [],
                "responsibilities": []
            }
        }
        ```'''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai(self.sample_job_description)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(result['seniority_level'], 'senior')

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_seniority_mapping(
            self, mockai_available, mock_get_client):
        """Test seniority level mapping from variations"""
        # Arrange
        mockai_available.return_value = True

        # Test case where OpenAI returns "Junior" instead of "entry"
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "required_skills": ["Python"],
            "seniority_level": "Junior Developer",
            "requirements": {
                "education": [],
                "years_experience": "0-2",
                "certifications": [],
                "responsibilities": []
            }
        }
        '''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai("Junior Developer")

        # Assert
        # Should map "Junior Developer" to "entry"
        self.assertEqual(result['seniority_level'], 'entry')

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_empty_fields(
            self, mockai_available, mock_get_client):
        """Test parsing with minimal job description (empty fields)"""
        # Arrange
        mockai_available.return_value = True

        minimal_job = "Looking for a developer."

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "required_skills": [],
            "seniority_level": "",
            "requirements": {
                "education": [],
                "years_experience": "",
                "certifications": [],
                "responsibilities": []
            }
        }
        '''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai(minimal_job)

        # Assert
        self.assertIsInstance(result['required_skills'], list)
        self.assertEqual(len(result['required_skills']), 0)
        self.assertEqual(result['seniority_level'], '')

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_api_error(
            self, mockai_available, mock_get_client):
        """Test error handling when OpenAI API call fails"""
        # Arrange
        mockai_available.return_value = True

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "API rate limit exceeded")
        mock_get_client.return_value = mock_client

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            parse_job_listing_with_ai(self.sample_job_description)

        self.assertIn("Job listing parsing failed", str(context.exception))

    def test_validate_parsed_data_valid(self):
        """Test validation of correctly structured parsed data"""
        # Arrange
        valid_data = {
            'required_skills': ['Python', 'Django'],
            'seniority_level': 'senior',
            'requirements': {
                'education': ['Bachelor\'s'],
                'years_experience': '5+',
                'certifications': ['AWS'],
                'responsibilities': ['Lead team']
            }
        }

        # Act
        result = validate_parsed_data(valid_data)

        # Assert
        self.assertTrue(result)

    def test_validate_parsed_data_missing_keys(self):
        """Test validation fails with missing required keys"""
        # Arrange
        invalid_data = {
            'required_skills': ['Python'],
            # Missing seniority_level and requirements
        }

        # Act
        result = validate_parsed_data(invalid_data)

        # Assert
        self.assertFalse(result)

    def test_validate_parsed_data_wrong_types(self):
        """Test validation fails with incorrect types"""
        # Arrange
        invalid_data = {
            'required_skills': 'Python',  # Should be list, not string
            'seniority_level': 'senior',
            'requirements': {}
        }

        # Act
        result = validate_parsed_data(invalid_data)

        # Assert
        self.assertFalse(result)

    def test_validate_parsed_data_not_dict(self):
        """Test validation fails when data is not a dict"""
        # Arrange
        invalid_data = ['Python', 'Django']

        # Act
        result = validate_parsed_data(invalid_data)

        # Assert
        self.assertFalse(result)

    def test_validate_parsed_data_missing_requirement_keys(self):
        """Test validation fails when requirements dict is missing keys"""
        # Arrange
        invalid_data = {
            'required_skills': ['Python'],
            'seniority_level': 'senior',
            'requirements': {
                'education': [],
                # Missing years_experience, certifications, responsibilities
            }
        }

        # Act
        result = validate_parsed_data(invalid_data)

        # Assert
        self.assertFalse(result)

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_completely_invalid_json(
            self, mockai_available, mock_get_client):
        """Test error when JSON is completely invalid even after cleaning"""
        # Arrange
        mockai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Return completely invalid JSON that can't be parsed
        mock_response.choices[0].message.content = \
            'This is not JSON at all, just plain text'

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            parse_job_listing_with_ai("Test job")

        self.assertIn("Failed to parse OpenAI response as JSON",
                      str(context.exception))

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_returns_non_dict(
            self, mockai_available, mock_get_client):
        """Test error when OpenAI returns valid JSON but not a dict"""
        # Arrange
        mockai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Return a JSON array instead of object
        mock_response.choices[0].message.content = '["item1", "item2"]'

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            parse_job_listing_with_ai("Test job")

        self.assertIn("Expected dict from OpenAI, got list",
                      str(context.exception))

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_wrong_field_types(
            self, mockai_available, mock_get_client):
        """Test type correction when OpenAI returns wrong types"""
        # Arrange
        mockai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Return wrong types: skills as string, seniority as int,
        # requirements as string
        mock_response.choices[0].message.content = '''{
            "required_skills": "Python, Django",
            "seniority_level": 123,
            "requirements": "some requirements"
        }'''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai("Test job")

        # Assert - should auto-correct to proper types
        self.assertIsInstance(result['required_skills'], list)
        self.assertEqual(result['required_skills'], [])  # Corrected to empty
        self.assertIsInstance(result['seniority_level'], str)
        self.assertEqual(result['seniority_level'], '')  # Corrected to empty
        self.assertIsInstance(result['requirements'], dict)

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_seniority_mid_level(
            self, mockai_available, mock_get_client):
        """Test seniority mapping for 'mid' or 'intermediate'"""
        # Arrange
        mockai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # AI returns "Intermediate Level" instead of "mid"
        mock_response.choices[0].message.content = '''{
            "required_skills": ["Python"],
            "seniority_level": "Intermediate Level",
            "requirements": {
                "education": [],
                "years_experience": "2-5",
                "certifications": [],
                "responsibilities": []
            }
        }'''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai("Mid-level Developer")

        # Assert - should map "Intermediate Level" to "mid"
        self.assertEqual(result['seniority_level'], 'mid')

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_seniority_lead_principal(
            self, mockai_available, mock_get_client):
        """Test seniority mapping for 'principal' positions"""
        # Arrange
        mockai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # AI returns "Principal Engineer"
        mock_response.choices[0].message.content = '''{
            "required_skills": ["System Design"],
            "seniority_level": "Principal Engineer",
            "requirements": {
                "education": [],
                "years_experience": "10+",
                "certifications": [],
                "responsibilities": []
            }
        }'''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai("Principal Engineer")

        # Assert - should map "Principal Engineer" to "lead"
        self.assertEqual(result['seniority_level'], 'lead')

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_seniority_executive_variants(
            self, mockai_available, mock_get_client):
        """Test seniority mapping for 'director', 'vp', 'executive'"""
        # Arrange
        mockai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # AI returns "VP of Engineering"
        mock_response.choices[0].message.content = '''{
            "required_skills": ["Leadership", "Strategy"],
            "seniority_level": "VP of Engineering",
            "requirements": {
                "education": [],
                "years_experience": "15+",
                "certifications": [],
                "responsibilities": []
            }
        }'''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai("VP Engineering")

        # Assert - should map "VP of Engineering" to "executive"
        self.assertEqual(result['seniority_level'], 'executive')

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_seniority_unknown(
            self, mockai_available, mock_get_client):
        """Test seniority mapping for completely unknown level"""
        # Arrange
        mockai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # AI returns unrecognizable seniority
        mock_response.choices[0].message.content = '''{
            "required_skills": ["Python"],
            "seniority_level": "Astronaut Level 5",
            "requirements": {
                "education": [],
                "years_experience": "",
                "certifications": [],
                "responsibilities": []
            }
        }'''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai("Strange job")

        # Assert - should default to empty string for unknown
        self.assertEqual(result['seniority_level'], '')

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_wrong_requirements_types(
            self, mockai_available, mock_get_client):
        """Test type correction for requirements fields"""
        # Arrange
        mockai_available.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Return requirements with wrong types
        mock_response.choices[0].message.content = '''{
            "required_skills": ["Python"],
            "seniority_level": "senior",
            "requirements": {
                "education": "Bachelor's degree",
                "years_experience": 5,
                "certifications": "AWS",
                "responsibilities": "Lead team"
            }
        }'''

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Act
        result = parse_job_listing_with_ai("Test job")

        # Assert - should auto-correct types
        self.assertIsInstance(result['requirements']['education'], list)
        self.assertEqual(result['requirements']['education'], [])
        self.assertIsInstance(result['requirements']['years_experience'], str)
        self.assertEqual(result['requirements']['years_experience'], '5')
        self.assertIsInstance(result['requirements']['certifications'], list)
        self.assertEqual(result['requirements']['certifications'], [])
        self.assertIsInstance(
            result['requirements']['responsibilities'], list)
        self.assertEqual(result['requirements']['responsibilities'], [])

    @patch('active_interview_app.job_listing_parser.get_openai_client')
    @patch('active_interview_app.job_listing_parser.ai_available')
    def test_parse_job_listing_api_key_sanitization(
            self, mockai_available, mock_get_client):
        """Test that API key errors are sanitized in error messages"""
        # Arrange
        mockai_available.return_value = True

        mock_client = MagicMock()
        # Simulate error with API key in message
        mock_client.chat.completions.create.side_effect = Exception(
            "Invalid API Key: sk-abc123xyz"
        )
        mock_get_client.return_value = mock_client

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            parse_job_listing_with_ai("Test job")

        # Should sanitize the API key from error message
        error_message = str(context.exception)
        self.assertIn("OpenAI API authentication error", error_message)
        self.assertNotIn("sk-abc123xyz", error_message)

    def test_validate_parsed_data_wrong_seniority_type(self):
        """Test validation fails when seniority_level is not a string"""
        # Arrange
        invalid_data = {
            'required_skills': ['Python'],
            'seniority_level': 123,  # Should be string
            'requirements': {
                'education': [],
                'years_experience': '',
                'certifications': [],
                'responsibilities': []
            }
        }

        # Act
        result = validate_parsed_data(invalid_data)

        # Assert
        self.assertFalse(result)

    def test_validate_parsed_data_wrong_requirements_type(self):
        """Test validation fails when requirements is not a dict"""
        # Arrange
        invalid_data = {
            'required_skills': ['Python'],
            'seniority_level': 'senior',
            'requirements': ['education', 'experience']  # Should be dict
        }

        # Act
        result = validate_parsed_data(invalid_data)

        # Assert
        self.assertFalse(result)
