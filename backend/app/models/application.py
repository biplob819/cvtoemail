"""Application model -- logs each job application (email sent)."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    cv_path = Column(String, nullable=True)  # path to the tailored CV PDF
    email_sent_to = Column(String, nullable=False)
    status = Column(String, nullable=False, default="sent")  # sent, failed
    error_message = Column(String, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    job = relationship("Job", back_populates="applications")
