"""JobSource model -- stores user-defined URLs to monitor for job listings."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
from app.database import Base


class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    portal_name = Column(String, nullable=False)
    filters_description = Column(Text, nullable=True, default="")
    is_active = Column(Boolean, nullable=False, default=True)
    last_checked = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
