"""CV management endpoints -- upload, parse, CRUD, and preview."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.cv import CVProfile
from app.services.cv_parser import extract_text, parse_cv_with_openai
from app.services.pdf_generator import generate_cv_pdf, generate_cv_html


def _format_dt(val) -> Optional[str]:
    """Safely format a datetime value to ISO string."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    return str(val)

router = APIRouter(prefix="/api/cv", tags=["CV"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


# --- Pydantic schemas ---

class PersonalInfo(BaseModel):
    name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    location: Optional[str] = ""
    linkedin: Optional[str] = None
    website: Optional[str] = None


class WorkExperience(BaseModel):
    title: str = ""
    company: str = ""
    duration: str = ""
    achievements: list[str] = []


class Education(BaseModel):
    degree: str = ""
    institution: str = ""
    year: str = ""
    details: Optional[str] = None


class Certification(BaseModel):
    name: str = ""
    issuer: Optional[str] = None
    year: Optional[str] = None


class CVData(BaseModel):
    personal_info: Optional[PersonalInfo] = None
    summary: Optional[str] = ""
    work_experience: Optional[list[WorkExperience]] = []
    education: Optional[list[Education]] = []
    skills: Optional[list[str]] = []
    certifications: Optional[list[Certification]] = []


class CVResponse(BaseModel):
    id: int
    personal_info: Optional[dict] = {}
    summary: Optional[str] = ""
    work_experience: Optional[list] = []
    education: Optional[list] = []
    skills: Optional[list] = []
    certifications: Optional[list] = []
    raw_text: Optional[str] = ""
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


# --- Helper ---

async def _get_or_create_cv(db: AsyncSession) -> CVProfile:
    """Get the singleton CV profile, or create one if it doesn't exist."""
    result = await db.execute(select(CVProfile).limit(1))
    cv = result.scalar_one_or_none()
    if cv is None:
        cv = CVProfile(
            personal_info={},
            summary="",
            work_experience=[],
            education=[],
            skills=[],
            certifications=[],
            raw_text="",
        )
        db.add(cv)
        await db.flush()
        await db.refresh(cv)
    return cv


# --- Endpoints ---

@router.get("", response_model=Optional[CVResponse])
async def get_cv(db: AsyncSession = Depends(get_db)):
    """Get the current CV profile."""
    result = await db.execute(select(CVProfile).limit(1))
    cv = result.scalar_one_or_none()
    if cv is None:
        return None
    return CVResponse(
        id=cv.id,
        personal_info=cv.personal_info or {},
        summary=cv.summary or "",
        work_experience=cv.work_experience or [],
        education=cv.education or [],
        skills=cv.skills or [],
        certifications=cv.certifications or [],
        raw_text=cv.raw_text or "",
        updated_at=_format_dt(cv.updated_at),
    )


@router.put("", response_model=CVResponse)
async def update_cv(data: CVData, db: AsyncSession = Depends(get_db)):
    """Update (save) the CV profile data."""
    cv = await _get_or_create_cv(db)

    if data.personal_info is not None:
        cv.personal_info = data.personal_info.model_dump()
    if data.summary is not None:
        cv.summary = data.summary
    if data.work_experience is not None:
        cv.work_experience = [e.model_dump() for e in data.work_experience]
    if data.education is not None:
        cv.education = [e.model_dump() for e in data.education]
    if data.skills is not None:
        cv.skills = data.skills
    if data.certifications is not None:
        cv.certifications = [c.model_dump() for c in data.certifications]

    await db.flush()
    await db.refresh(cv)

    return CVResponse(
        id=cv.id,
        personal_info=cv.personal_info or {},
        summary=cv.summary or "",
        work_experience=cv.work_experience or [],
        education=cv.education or [],
        skills=cv.skills or [],
        certifications=cv.certifications or [],
        raw_text=cv.raw_text or "",
        updated_at=_format_dt(cv.updated_at),
    )


@router.post("/upload", response_model=CVResponse)
async def upload_cv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Upload a CV file (PDF/DOCX), extract text, parse with OpenAI, and store."""
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    lower_name = file.filename.lower()
    if not (lower_name.endswith(".pdf") or lower_name.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    # Read and validate size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit.")

    # Extract text
    try:
        raw_text = extract_text(file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to extract text from file: {str(e)}")

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract any text from the file. The file may be scanned/image-based.")

    # Parse with OpenAI
    try:
        parsed = await parse_cv_with_openai(raw_text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI parsing failed: {str(e)}. You can enter your CV data manually.",
        )

    # Store
    cv = await _get_or_create_cv(db)
    cv.personal_info = parsed.get("personal_info", {})
    cv.summary = parsed.get("summary", "")
    cv.work_experience = parsed.get("work_experience", [])
    cv.education = parsed.get("education", [])
    cv.skills = parsed.get("skills", [])
    cv.certifications = parsed.get("certifications", [])
    cv.raw_text = raw_text

    await db.flush()
    await db.refresh(cv)

    return CVResponse(
        id=cv.id,
        personal_info=cv.personal_info or {},
        summary=cv.summary or "",
        work_experience=cv.work_experience or [],
        education=cv.education or [],
        skills=cv.skills or [],
        certifications=cv.certifications or [],
        raw_text=cv.raw_text or "",
        updated_at=_format_dt(cv.updated_at),
    )


@router.get("/preview")
async def preview_cv(db: AsyncSession = Depends(get_db)):
    """Generate and return ATS-friendly PDF of the current CV."""
    result = await db.execute(select(CVProfile).limit(1))
    cv = result.scalar_one_or_none()
    if cv is None:
        raise HTTPException(status_code=404, detail="No CV data found. Please upload or enter your CV first.")

    cv_data = {
        "personal_info": cv.personal_info or {},
        "summary": cv.summary or "",
        "work_experience": cv.work_experience or [],
        "education": cv.education or [],
        "skills": cv.skills or [],
        "certifications": cv.certifications or [],
    }

    try:
        pdf_bytes = generate_cv_pdf(cv_data)
        # Check if it's actually HTML (WeasyPrint not available)
        if pdf_bytes[:5] == b"<!DOC" or pdf_bytes[:5] == b"<html":
            return Response(content=pdf_bytes, media_type="text/html")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline; filename=cv_preview.pdf"},
        )
    except Exception as e:
        # Fallback to HTML preview
        try:
            html_content = generate_cv_html(cv_data)
            return Response(content=html_content, media_type="text/html")
        except Exception:
            raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@router.get("/preview/html")
async def preview_cv_html(db: AsyncSession = Depends(get_db)):
    """Return HTML preview of the current CV (for in-browser viewing)."""
    result = await db.execute(select(CVProfile).limit(1))
    cv = result.scalar_one_or_none()
    if cv is None:
        raise HTTPException(status_code=404, detail="No CV data found.")

    cv_data = {
        "personal_info": cv.personal_info or {},
        "summary": cv.summary or "",
        "work_experience": cv.work_experience or [],
        "education": cv.education or [],
        "skills": cv.skills or [],
        "certifications": cv.certifications or [],
    }

    html_string = generate_cv_html(cv_data)
    return Response(content=html_string, media_type="text/html")
