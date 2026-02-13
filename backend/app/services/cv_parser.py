"""CV parsing service -- extract text from PDF/DOCX and parse with OpenAI."""

import json
import io
from typing import Optional

import PyPDF2
from docx import Document
from openai import AsyncOpenAI

from app.config import settings

PARSE_SYSTEM_PROMPT = """You are a CV/resume parser. Given raw text from a CV document, extract structured data in the following JSON format. Return ONLY valid JSON, no markdown fences.

{
  "personal_info": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "location": "string",
    "linkedin": "string or null",
    "website": "string or null"
  },
  "summary": "string (professional summary/objective, or empty string if not present)",
  "work_experience": [
    {
      "title": "string",
      "company": "string",
      "duration": "string (e.g. Jan 2020 - Present)",
      "achievements": ["string (bullet point)"]
    }
  ],
  "education": [
    {
      "degree": "string",
      "institution": "string",
      "year": "string",
      "details": "string or null"
    }
  ],
  "skills": ["string"],
  "certifications": [
    {
      "name": "string",
      "issuer": "string or null",
      "year": "string or null"
    }
  ]
}

Be thorough. If a section is not present in the CV, return an empty array or empty string. Preserve exact dates, titles, and company names."""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes."""
    doc = Document(io.BytesIO(file_bytes))
    text_parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)
    return "\n".join(text_parts)


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from a CV file based on its extension."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}. Only PDF and DOCX are supported.")


async def parse_cv_with_openai(raw_text: str, api_key: Optional[str] = None) -> dict:
    """Send raw CV text to OpenAI and get structured data back."""
    key = api_key or settings.openai_api_key
    if not key:
        raise ValueError("OpenAI API key is not configured. Please set it in Settings.")

    client = AsyncOpenAI(api_key=key)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PARSE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Parse this CV:\n\n{raw_text}"},
        ],
        temperature=0.1,
        max_tokens=4000,
    )

    content = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    return json.loads(content)
