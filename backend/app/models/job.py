"""Job model -- stores individual job listings discovered by the scraper."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("job_sources.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=True, default="")
    location = Column(String, nullable=True, default="")
    description = Column(Text, nullable=True, default="")
    url = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default="New")  # New / Viewed / CV Generated / CV Sent / Skipped
    is_new = Column(Boolean, nullable=False, default=True)
    discovered_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    # CV tailoring fields
    tailored_cv = Column(JSON, nullable=True, default=None)  # Structured CV data tailored for this job
    cv_pdf_path = Column(String, nullable=True, default=None)  # Path to generated PDF file
    cv_generated_at = Column(DateTime(timezone=True), nullable=True, default=None)
    
    # Relationships
    applications = relationship("Application", back_populates="job")
