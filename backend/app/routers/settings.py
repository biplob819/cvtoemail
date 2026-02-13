"""Settings API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import time
import logging

from app.database import get_db
from app.models.settings import AppSettings
from app.utils.crypto import encrypt_string, decrypt_string
from app.services.email_sender import create_email_sender, EmailSendError
import openai

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


# Schemas
class SettingsResponse(BaseModel):
    id: int
    notification_email: Optional[str] = None
    smtp_host: Optional[str] = "smtp.gmail.com"
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password_set: bool = False  # Don't expose actual password
    openai_api_key_set: bool = False  # Don't expose actual key
    openai_model: Optional[str] = "gpt-4o-mini"
    scan_frequency: Optional[int] = 5
    scan_window_start: Optional[str] = None
    scan_window_end: Optional[str] = None

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    notification_email: Optional[EmailStr] = None
    smtp_host: Optional[str] = Field(default="smtp.gmail.com", min_length=1)
    smtp_port: Optional[int] = Field(default=587, ge=1, le=65535)
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None  # If empty string, clear it
    openai_api_key: Optional[str] = None  # If empty string, clear it
    openai_model: Optional[str] = Field(default="gpt-4o-mini", min_length=1)
    scan_frequency: Optional[int] = Field(default=5, ge=1, le=24)
    scan_window_start: Optional[str] = None  # HH:MM format
    scan_window_end: Optional[str] = None  # HH:MM format


class TestEmailRequest(BaseModel):
    test_email: EmailStr


class TestEmailResponse(BaseModel):
    success: bool
    message: str


@router.get("", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Get application settings (singleton)."""
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings if they don't exist
        settings = AppSettings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    # Convert time to string format
    response = SettingsResponse(
        id=settings.id,
        notification_email=settings.notification_email,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password_set=bool(settings.smtp_password),
        openai_api_key_set=bool(settings.openai_api_key),
        openai_model=settings.openai_model,
        scan_frequency=settings.scan_frequency,
        scan_window_start=settings.scan_window_start.strftime("%H:%M") if settings.scan_window_start else None,
        scan_window_end=settings.scan_window_end.strftime("%H:%M") if settings.scan_window_end else None,
    )
    return response


@router.put("", response_model=SettingsResponse)
async def update_settings(
    update: SettingsUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update application settings."""
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        settings = AppSettings(id=1)
        db.add(settings)

    # Update fields
    if update.notification_email is not None:
        settings.notification_email = update.notification_email
    if update.smtp_host is not None:
        settings.smtp_host = update.smtp_host
    if update.smtp_port is not None:
        settings.smtp_port = update.smtp_port
    if update.smtp_user is not None:
        settings.smtp_user = update.smtp_user
    
    # Handle password - encrypt if provided, clear if empty string
    if update.smtp_password is not None:
        if update.smtp_password == "":
            settings.smtp_password = None
        else:
            settings.smtp_password = encrypt_string(update.smtp_password)
    
    # Handle OpenAI key - encrypt if provided, clear if empty string
    if update.openai_api_key is not None:
        if update.openai_api_key == "":
            settings.openai_api_key = None
        else:
            # Validate OpenAI key
            try:
                test_client = openai.OpenAI(api_key=update.openai_api_key)
                # Make a minimal test call
                test_client.models.list()
                settings.openai_api_key = encrypt_string(update.openai_api_key)
            except openai.AuthenticationError:
                raise HTTPException(status_code=400, detail="Invalid OpenAI API key")
            except Exception as e:
                logger.warning(f"Could not validate OpenAI key: {e}")
                # Still save it even if validation fails (might be network issue)
                settings.openai_api_key = encrypt_string(update.openai_api_key)
    
    if update.openai_model is not None:
        settings.openai_model = update.openai_model
    if update.scan_frequency is not None:
        settings.scan_frequency = update.scan_frequency
    
    # Parse time strings
    if update.scan_window_start is not None:
        if update.scan_window_start == "":
            settings.scan_window_start = None
        else:
            try:
                hour, minute = map(int, update.scan_window_start.split(":"))
                settings.scan_window_start = time(hour, minute)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
    
    if update.scan_window_end is not None:
        if update.scan_window_end == "":
            settings.scan_window_end = None
        else:
            try:
                hour, minute = map(int, update.scan_window_end.split(":"))
                settings.scan_window_end = time(hour, minute)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

    await db.commit()
    await db.refresh(settings)

    # Return response
    response = SettingsResponse(
        id=settings.id,
        notification_email=settings.notification_email,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password_set=bool(settings.smtp_password),
        openai_api_key_set=bool(settings.openai_api_key),
        openai_model=settings.openai_model,
        scan_frequency=settings.scan_frequency,
        scan_window_start=settings.scan_window_start.strftime("%H:%M") if settings.scan_window_start else None,
        scan_window_end=settings.scan_window_end.strftime("%H:%M") if settings.scan_window_end else None,
    )
    return response


@router.post("/test-email", response_model=TestEmailResponse)
async def send_test_email(
    request: TestEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send a test email to verify SMTP configuration."""
    # Get settings
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(status_code=400, detail="Settings not configured")

    # Validate required fields
    if not all([settings.smtp_host, settings.smtp_port, settings.smtp_user, settings.smtp_password]):
        raise HTTPException(
            status_code=400,
            detail="SMTP configuration incomplete. Please configure all SMTP settings first."
        )

    # Decrypt password
    smtp_password = decrypt_string(settings.smtp_password)
    if not smtp_password:
        raise HTTPException(status_code=400, detail="SMTP password not set")

    # Create email sender and send test email
    try:
        email_sender = create_email_sender(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_password=smtp_password,
            from_email=settings.smtp_user,
        )
        email_sender.send_test_email(to_email=request.test_email)
        return TestEmailResponse(
            success=True,
            message=f"Test email sent successfully to {request.test_email}"
        )
    except EmailSendError as e:
        logger.error(f"Test email failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error sending test email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")
