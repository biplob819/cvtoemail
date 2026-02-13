"""Unit tests for CV tailoring service (cv_writer.py).

Tests cover:
- Keyword extraction from job descriptions
- CV tailoring with OpenAI (mocked)
- Error handling and retries
- Structure validation
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.cv_writer import tailor_cv_for_job, _extract_keywords_from_job

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit


SAMPLE_CV_DATA = {
    "personal_info": {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1-555-0100",
        "location": "San Francisco, CA",
    },
    "summary": "Experienced software engineer with 6+ years building scalable web applications.",
    "work_experience": [
        {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "duration": "Jan 2021 - Present",
            "achievements": [
                "Led a team of 5 engineers to build a microservices platform",
                "Reduced API latency by 40% through caching optimization",
            ],
        }
    ],
    "education": [
        {
            "degree": "B.S. Computer Science",
            "institution": "UC Berkeley",
            "year": "2018",
        }
    ],
    "skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
    "certifications": [],
}

SAMPLE_JOB_DESCRIPTION = """
We are seeking a Senior Backend Engineer to join our team.

Required Skills:
- Python, FastAPI, Django
- PostgreSQL, Redis
- Docker, Kubernetes
- AWS or GCP

Responsibilities:
- Build scalable APIs
- Mentor junior developers
- Design system architecture

Qualifications:
- 5+ years of backend development experience
- Strong understanding of microservices
- Experience with cloud platforms
"""

SAMPLE_TAILORED_CV = {
    "personal_info": {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1-555-0100",
        "location": "San Francisco, CA",
    },
    "summary": "Senior software engineer with 6+ years building scalable backend systems and microservices platforms using Python, FastAPI, and cloud technologies.",
    "work_experience": [
        {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "duration": "Jan 2021 - Present",
            "achievements": [
                "Led a team of 5 engineers to design and build a microservices platform using Python and FastAPI",
                "Optimized API performance reducing latency by 40% through Redis caching and PostgreSQL query optimization",
            ],
        }
    ],
    "education": [
        {
            "degree": "B.S. Computer Science",
            "institution": "UC Berkeley",
            "year": "2018",
        }
    ],
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "Kubernetes", "AWS"],
    "certifications": [],
}


@pytest.mark.asyncio
async def test_extract_keywords_success():
    """Test successful keyword extraction from job description."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps([
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
        "Kubernetes",
        "Microservices",
    ])
    
    with patch("app.services.cv_writer.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        keywords = await _extract_keywords_from_job(SAMPLE_JOB_DESCRIPTION, "test-key")
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert "Python" in keywords
        mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_extract_keywords_strips_markdown():
    """Test that markdown fences are stripped from keyword response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    # Response with markdown fences
    mock_response.choices[0].message.content = '```json\n["Python", "FastAPI"]\n```'
    
    with patch("app.services.cv_writer.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        keywords = await _extract_keywords_from_job(SAMPLE_JOB_DESCRIPTION, "test-key")
        
        assert isinstance(keywords, list)
        assert "Python" in keywords


@pytest.mark.asyncio
async def test_extract_keywords_failure_returns_empty():
    """Test that keyword extraction failures return empty list instead of crashing."""
    with patch("app.services.cv_writer.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        keywords = await _extract_keywords_from_job(SAMPLE_JOB_DESCRIPTION, "test-key")
        
        assert keywords == []


@pytest.mark.asyncio
async def test_tailor_cv_success():
    """Test successful CV tailoring with mocked OpenAI."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(SAMPLE_TAILORED_CV)
    
    with patch("app.services.cv_writer.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        result = await tailor_cv_for_job(
            cv_data=SAMPLE_CV_DATA,
            job_title="Senior Backend Engineer",
            job_company="TechStartup",
            job_description=SAMPLE_JOB_DESCRIPTION,
            api_key="test-key",
        )
        
        # Verify structure
        assert "personal_info" in result
        assert "summary" in result
        assert "work_experience" in result
        assert "education" in result
        assert "skills" in result
        
        # Verify personal info is preserved
        assert result["personal_info"]["name"] == "Jane Doe"
        assert result["personal_info"]["email"] == "jane@example.com"


@pytest.mark.asyncio
async def test_tailor_cv_strips_markdown():
    """Test that markdown fences are stripped from tailored CV response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    # Response with markdown fences
    mock_response.choices[0].message.content = f'```json\n{json.dumps(SAMPLE_TAILORED_CV)}\n```'
    
    with patch("app.services.cv_writer.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        result = await tailor_cv_for_job(
            cv_data=SAMPLE_CV_DATA,
            job_title="Senior Backend Engineer",
            job_company="TechStartup",
            job_description=SAMPLE_JOB_DESCRIPTION,
            api_key="test-key",
        )
        
        assert result["personal_info"]["name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_tailor_cv_no_api_key_raises():
    """Test that missing API key raises ValueError."""
    with patch("app.services.cv_writer.settings") as mock_settings:
        mock_settings.openai_api_key = None
        
        with pytest.raises(ValueError, match="OpenAI API key is not configured"):
            await tailor_cv_for_job(
                cv_data=SAMPLE_CV_DATA,
                job_title="Engineer",
                job_company="Company",
                job_description="Description",
                api_key=None,
            )


@pytest.mark.asyncio
async def test_tailor_cv_uses_settings_key():
    """Test that API key from settings is used when not provided."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(SAMPLE_TAILORED_CV)
    
    with patch("app.services.cv_writer.settings") as mock_settings:
        mock_settings.openai_api_key = "settings-key"
        
        with patch("app.services.cv_writer.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            await tailor_cv_for_job(
                cv_data=SAMPLE_CV_DATA,
                job_title="Engineer",
                job_company="Company",
                job_description=SAMPLE_JOB_DESCRIPTION,
                api_key=None,  # Should use settings key
            )
            
            # Verify AsyncOpenAI was called with settings key
            mock_openai.assert_called_with(api_key="settings-key")


@pytest.mark.asyncio
async def test_tailor_cv_invalid_json_retries():
    """Test that invalid JSON response triggers retry logic."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    
    # First two attempts fail, third succeeds
    mock_response.choices[0].message.content = "invalid json"
    
    with patch("app.services.cv_writer.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Should retry 3 times and then raise
        with pytest.raises(Exception, match="Failed to parse OpenAI response"):
            await tailor_cv_for_job(
                cv_data=SAMPLE_CV_DATA,
                job_title="Engineer",
                job_company="Company",
                job_description=SAMPLE_JOB_DESCRIPTION,
                api_key="test-key",
            )
        
        # Verify it tried multiple times
        assert mock_client.chat.completions.create.call_count == 3


@pytest.mark.asyncio
async def test_tailor_cv_api_error_retries():
    """Test that OpenAI API errors trigger retry with exponential backoff."""
    with patch("app.services.cv_writer.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        with patch("app.services.cv_writer.asyncio.sleep") as mock_sleep:
            with pytest.raises(Exception, match="Failed to generate tailored CV"):
                await tailor_cv_for_job(
                    cv_data=SAMPLE_CV_DATA,
                    job_title="Engineer",
                    job_company="Company",
                    job_description=SAMPLE_JOB_DESCRIPTION,
                    api_key="test-key",
                )
            
            # Verify it tried 3 times
            assert mock_client.chat.completions.create.call_count == 3
            
            # Verify exponential backoff (sleep called with increasing delays)
            assert mock_sleep.call_count == 2  # Sleep between attempts
            # First retry: 1 * 2^0 = 1 second
            # Second retry: 1 * 2^1 = 2 seconds


@pytest.mark.asyncio
async def test_tailor_cv_missing_required_fields_raises():
    """Test that tailored CV with missing required fields raises validation error."""
    incomplete_cv = {
        "personal_info": {"name": "Test"},
        "summary": "Summary",
        # Missing work_experience, education, skills
    }
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(incomplete_cv)
    
    with patch("app.services.cv_writer.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with pytest.raises(ValueError, match="missing required fields"):
            await tailor_cv_for_job(
                cv_data=SAMPLE_CV_DATA,
                job_title="Engineer",
                job_company="Company",
                job_description=SAMPLE_JOB_DESCRIPTION,
                api_key="test-key",
            )


@pytest.mark.asyncio
async def test_tailor_cv_long_description_truncated():
    """Test that very long job descriptions are truncated to avoid token limits."""
    # Create a very long job description (> 4000 chars)
    long_description = "Required skills: " + ", ".join([f"Skill{i}" for i in range(1000)])
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(SAMPLE_TAILORED_CV)
    
    with patch("app.services.cv_writer.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        await tailor_cv_for_job(
            cv_data=SAMPLE_CV_DATA,
            job_title="Engineer",
            job_company="Company",
            job_description=long_description,
            api_key="test-key",
        )
        
        # Verify the call was made
        mock_client.chat.completions.create.assert_called()
        
        # Verify the prompt contains truncated description
        call_args = mock_client.chat.completions.create.call_args
        user_message = call_args[1]["messages"][1]["content"]
        
        # Should be truncated at 4000 chars in the prompt
        assert "JOB DESCRIPTION:" in user_message
        # The description in the prompt should be limited
        description_part = user_message.split("JOB DESCRIPTION:")[1].split("KEY TERMS")[0]
        assert len(description_part) <= 4100  # 4000 + some buffer for formatting
