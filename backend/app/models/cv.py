"""CVProfile model -- singleton table storing the user's CV data."""

from sqlalchemy import Column, Integer, JSON, Text, DateTime, func
from app.database import Base


class CVProfile(Base):
    __tablename__ = "cv_profiles"

    id = Column(Integer, primary_key=True, index=True)
    personal_info = Column(JSON, nullable=True, default=dict)
    summary = Column(Text, nullable=True, default="")
    work_experience = Column(JSON, nullable=True, default=list)
    education = Column(JSON, nullable=True, default=list)
    skills = Column(JSON, nullable=True, default=list)
    certifications = Column(JSON, nullable=True, default=list)
    raw_text = Column(Text, nullable=True, default="")
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
