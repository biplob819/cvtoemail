"""CV tailoring service -- uses OpenAI to generate job-specific tailored CVs."""

import json
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
import asyncio

from app.config import settings


TAILOR_SYSTEM_PROMPT = """You are an expert CV/resume writer specializing in ATS optimization and keyword matching.

Your task is to tailor a candidate's CV for a specific job posting while:
1. PRESERVING all factual information (dates, titles, company names, education details) EXACTLY as provided
2. Rephrasing achievements and responsibilities to highlight relevant experience for the target role
3. Optimizing the professional summary to align with the job requirements
4. Ensuring key terms and technologies from the job description appear naturally in the CV
5. Maintaining a professional, achievement-focused tone

CRITICAL RULES:
- Do NOT invent or fabricate any experience, skills, or achievements
- Do NOT change dates, titles, or company names
- Do NOT add skills the candidate doesn't have
- DO rephrase existing achievements to emphasize relevance to the target job
- DO prioritize and reorder experience to highlight most relevant roles
- DO optimize keywords naturally (no keyword stuffing)
- DO keep the CV concise and ATS-friendly

Return the tailored CV in the EXACT same JSON structure as the input CV."""


async def _extract_keywords_from_job(job_description: str, api_key: str) -> list[str]:
    """Extract key skills, technologies, and terms from job description."""
    client = AsyncOpenAI(api_key=api_key)
    
    prompt = """Extract the most important skills, technologies, qualifications, and key terms from this job description. 
Return as a JSON array of strings. Focus on:
- Required technical skills
- Preferred technologies/tools
- Key responsibilities
- Important qualifications
- Industry-specific terms

Return ONLY a JSON array, no markdown fences.

Job Description:
""" + job_description

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a job description analyzer. Extract key terms as a JSON array."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        
        content = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        
        keywords = json.loads(content)
        return keywords if isinstance(keywords, list) else []
    except Exception as e:
        # If keyword extraction fails, continue without it
        print(f"Keyword extraction failed: {e}")
        return []


async def tailor_cv_for_job(
    cv_data: Dict[str, Any],
    job_title: str,
    job_company: str,
    job_description: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a tailored CV for a specific job posting.
    
    Args:
        cv_data: Original CV data (structured JSON from CVProfile)
        job_title: Target job title
        job_company: Target company name
        job_description: Full job description text
        api_key: OpenAI API key (uses settings if not provided)
    
    Returns:
        Tailored CV data in the same structure as input
    
    Raises:
        ValueError: If OpenAI API key is not configured
        Exception: If OpenAI API call fails after retries
    """
    key = api_key or settings.openai_api_key
    if not key:
        raise ValueError("OpenAI API key is not configured. Please set it in Settings.")
    
    # Extract keywords from job description first
    keywords = await _extract_keywords_from_job(job_description, key)
    
    client = AsyncOpenAI(api_key=key)
    
    # Build the tailoring prompt
    user_prompt = f"""Tailor this CV for the following job:

JOB TITLE: {job_title}
COMPANY: {job_company}

JOB DESCRIPTION:
{job_description[:4000]}  

KEY TERMS TO INCORPORATE (naturally, if relevant): {", ".join(keywords[:15])}

ORIGINAL CV:
{json.dumps(cv_data, indent=2)}

Return the tailored CV in the EXACT same JSON structure. Remember:
- Keep ALL dates, titles, company names, and education details EXACTLY as provided
- Rephrase achievements to highlight relevance to this specific job
- Optimize the summary for this role
- Ensure key terms from the job description appear naturally where relevant
- Do NOT fabricate any information"""
    
    # Retry logic with exponential backoff
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",  # Use more powerful model for CV writing
                messages=[
                    {"role": "system", "content": TAILOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,  # Some creativity for rephrasing
                max_tokens=4000,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Strip markdown fences if present
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
            
            tailored_cv = json.loads(content)
            
            # Validate structure
            required_keys = ["personal_info", "summary", "work_experience", "education", "skills"]
            if not all(key in tailored_cv for key in required_keys):
                raise ValueError("Tailored CV is missing required fields")
            
            return tailored_cv
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise Exception(f"Failed to parse OpenAI response after {max_retries} attempts")

        except ValueError:
            raise  # validation errors (e.g. missing required fields) are not retried

        except Exception as e:
            print(f"OpenAI API error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise Exception(f"Failed to generate tailored CV after {max_retries} attempts: {str(e)}")
        
        # Wait before retry with exponential backoff
        await asyncio.sleep(retry_delay * (2 ** attempt))
    
    raise Exception("Failed to generate tailored CV")
