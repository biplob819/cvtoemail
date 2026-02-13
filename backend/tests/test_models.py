"""Unit tests for database models -- CVProfile and AppSettings."""

import pytest
from sqlalchemy import select

from app.models.cv import CVProfile
from app.models.settings import AppSettings


class TestCVProfileModel:
    """Tests for the CVProfile database model."""

    @pytest.mark.integration
    async def test_create_cv_profile(self, db_session):
        """Should create a CVProfile with all fields."""
        cv = CVProfile(
            personal_info={"name": "Test User", "email": "test@example.com"},
            summary="A test summary.",
            work_experience=[{"title": "Dev", "company": "Corp"}],
            education=[{"degree": "BS", "institution": "Uni", "year": "2020"}],
            skills=["Python", "SQL"],
            certifications=[{"name": "Cert1"}],
            raw_text="Raw text content",
        )
        db_session.add(cv)
        await db_session.flush()

        assert cv.id is not None
        assert cv.personal_info["name"] == "Test User"
        assert cv.skills == ["Python", "SQL"]

    @pytest.mark.integration
    async def test_cv_profile_defaults(self, db_session):
        """CVProfile with no data should have sensible defaults."""
        cv = CVProfile()
        db_session.add(cv)
        await db_session.flush()

        assert cv.id is not None

    @pytest.mark.integration
    async def test_cv_profile_json_fields(self, db_session):
        """JSON fields should store and retrieve complex data structures."""
        work = [
            {"title": "Senior Dev", "company": "BigCo", "duration": "2020-2023",
             "achievements": ["Led team", "Built system"]},
            {"title": "Junior Dev", "company": "SmallCo", "duration": "2018-2020",
             "achievements": ["Learned stuff"]},
        ]
        cv = CVProfile(work_experience=work)
        db_session.add(cv)
        await db_session.flush()

        result = await db_session.execute(select(CVProfile).where(CVProfile.id == cv.id))
        loaded = result.scalar_one()
        assert len(loaded.work_experience) == 2
        assert loaded.work_experience[0]["achievements"][0] == "Led team"

    @pytest.mark.integration
    async def test_cv_profile_update(self, db_session):
        """Should be able to update CV profile fields."""
        cv = CVProfile(summary="Old summary", skills=["Python"])
        db_session.add(cv)
        await db_session.flush()

        cv.summary = "New summary"
        cv.skills = ["Python", "Go"]
        await db_session.flush()

        result = await db_session.execute(select(CVProfile).where(CVProfile.id == cv.id))
        loaded = result.scalar_one()
        assert loaded.summary == "New summary"
        assert "Go" in loaded.skills


class TestAppSettingsModel:
    """Tests for the AppSettings database model."""

    @pytest.mark.integration
    async def test_create_app_settings(self, db_session):
        """Should create AppSettings with all fields."""
        settings = AppSettings(
            id=1,
            notification_email="user@example.com",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="pass",
            openai_api_key="sk-test",
            openai_model="gpt-4o-mini",
            scan_frequency=5,
        )
        db_session.add(settings)
        await db_session.flush()

        assert settings.id == 1
        assert settings.notification_email == "user@example.com"
        assert settings.openai_model == "gpt-4o-mini"

    @pytest.mark.integration
    async def test_app_settings_defaults(self, db_session):
        """AppSettings should have sensible defaults."""
        settings = AppSettings()
        db_session.add(settings)
        await db_session.flush()

        assert settings.id is not None

    @pytest.mark.integration
    async def test_app_settings_singleton_pattern(self, db_session):
        """AppSettings is designed as a singleton (id=1)."""
        settings = AppSettings(id=1, notification_email="test@test.com")
        db_session.add(settings)
        await db_session.flush()

        result = await db_session.execute(select(AppSettings).where(AppSettings.id == 1))
        loaded = result.scalar_one()
        assert loaded.notification_email == "test@test.com"
