"""AppSettings model -- singleton table for user-configurable settings."""

from sqlalchemy import Column, Integer, String, Time
from app.database import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, default=1)
    notification_email = Column(String, nullable=True)
    smtp_host = Column(String, nullable=True, default="smtp.gmail.com")
    smtp_port = Column(Integer, nullable=True, default=587)
    smtp_user = Column(String, nullable=True)
    smtp_password = Column(String, nullable=True)  # encrypted at rest
    openai_api_key = Column(String, nullable=True)  # encrypted at rest
    openai_model = Column(String, nullable=True, default="gpt-4o-mini")
    scan_frequency = Column(Integer, nullable=True, default=5)  # times per day
    scan_window_start = Column(Time, nullable=True)
    scan_window_end = Column(Time, nullable=True)
