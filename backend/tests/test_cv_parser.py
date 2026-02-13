"""Unit tests for app.services.cv_parser -- text extraction and OpenAI parsing."""

import io
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.cv_parser import (
    extract_text,
    extract_text_from_pdf,
    extract_text_from_docx,
    parse_cv_with_openai,
)


# ---------------------------------------------------------------------------
# extract_text() -- routing by file extension
# ---------------------------------------------------------------------------

class TestExtractText:
    """Tests for the extract_text dispatcher function."""

    @pytest.mark.unit
    def test_unsupported_file_type_raises_error(self):
        """Reject files that are not PDF or DOCX."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text(b"some bytes", "resume.txt")

    @pytest.mark.unit
    def test_unsupported_file_type_xlsx(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text(b"some bytes", "data.xlsx")

    @pytest.mark.unit
    def test_pdf_extension_dispatches_to_pdf_extractor(self):
        """PDF files should go through the PDF extraction path."""
        with patch("app.services.cv_parser.extract_text_from_pdf", return_value="pdf text") as mock:
            result = extract_text(b"fake pdf", "Resume.PDF")
            mock.assert_called_once_with(b"fake pdf")
            assert result == "pdf text"

    @pytest.mark.unit
    def test_docx_extension_dispatches_to_docx_extractor(self):
        """DOCX files should go through the DOCX extraction path."""
        with patch("app.services.cv_parser.extract_text_from_docx", return_value="docx text") as mock:
            result = extract_text(b"fake docx", "resume.docx")
            mock.assert_called_once_with(b"fake docx")
            assert result == "docx text"

    @pytest.mark.unit
    def test_case_insensitive_extension(self):
        """File extension matching should be case-insensitive."""
        with patch("app.services.cv_parser.extract_text_from_pdf", return_value="text"):
            result = extract_text(b"data", "MY_CV.Pdf")
            assert result == "text"


# ---------------------------------------------------------------------------
# extract_text_from_pdf() -- PyPDF2 extraction
# ---------------------------------------------------------------------------

class TestExtractTextFromPdf:
    """Tests for PDF text extraction using PyPDF2."""

    @pytest.mark.unit
    def test_extracts_text_from_valid_pdf(self):
        """Given valid PDF bytes with text, should extract all page text."""
        with patch("app.services.cv_parser.PyPDF2.PdfReader") as MockReader:
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = "Page 1 text"
            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = "Page 2 text"
            MockReader.return_value.pages = [mock_page1, mock_page2]

            result = extract_text_from_pdf(b"fake pdf bytes")
            assert "Page 1 text" in result
            assert "Page 2 text" in result

    @pytest.mark.unit
    def test_empty_pdf_returns_empty_string(self):
        """A PDF with no extractable text should return an empty string."""
        with patch("app.services.cv_parser.PyPDF2.PdfReader") as MockReader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = None
            MockReader.return_value.pages = [mock_page]

            result = extract_text_from_pdf(b"fake pdf bytes")
            assert result == ""

    @pytest.mark.unit
    def test_multi_page_pdf_joins_with_newline(self):
        """Multiple pages should be joined with newlines."""
        with patch("app.services.cv_parser.PyPDF2.PdfReader") as MockReader:
            pages = []
            for text in ["Line A", "Line B", "Line C"]:
                p = MagicMock()
                p.extract_text.return_value = text
                pages.append(p)
            MockReader.return_value.pages = pages

            result = extract_text_from_pdf(b"data")
            assert result == "Line A\nLine B\nLine C"


# ---------------------------------------------------------------------------
# extract_text_from_docx() -- python-docx extraction
# ---------------------------------------------------------------------------

class TestExtractTextFromDocx:
    """Tests for DOCX text extraction using python-docx."""

    @pytest.mark.unit
    def test_extracts_text_from_docx(self):
        """Given valid DOCX bytes, should extract paragraph text."""
        with patch("app.services.cv_parser.Document") as MockDocument:
            mock_para1 = MagicMock()
            mock_para1.text = "Paragraph 1"
            mock_para2 = MagicMock()
            mock_para2.text = "Paragraph 2"
            mock_para3 = MagicMock()
            mock_para3.text = "   "  # whitespace-only -- should be skipped
            MockDocument.return_value.paragraphs = [mock_para1, mock_para2, mock_para3]

            result = extract_text_from_docx(b"fake docx bytes")
            assert "Paragraph 1" in result
            assert "Paragraph 2" in result
            assert result.count("\n") == 1  # only 2 paragraphs joined

    @pytest.mark.unit
    def test_empty_docx_returns_empty(self):
        """A DOCX with no text paragraphs should return empty string."""
        with patch("app.services.cv_parser.Document") as MockDocument:
            MockDocument.return_value.paragraphs = []
            result = extract_text_from_docx(b"empty")
            assert result == ""


# ---------------------------------------------------------------------------
# parse_cv_with_openai() -- OpenAI integration (mocked)
# ---------------------------------------------------------------------------

class TestParseCvWithOpenai:
    """Tests for OpenAI CV parsing (API calls are mocked)."""

    @pytest.mark.unit
    async def test_missing_api_key_raises_error(self):
        """Should raise ValueError when no API key is available."""
        with patch("app.services.cv_parser.settings") as mock_settings:
            mock_settings.openai_api_key = None
            with pytest.raises(ValueError, match="OpenAI API key is not configured"):
                await parse_cv_with_openai("some text")

    @pytest.mark.unit
    async def test_successful_parse_returns_dict(self):
        """Should return structured dict from OpenAI response."""
        expected = {
            "personal_info": {"name": "Jane Doe", "email": "jane@example.com"},
            "summary": "Experienced engineer",
            "work_experience": [],
            "education": [],
            "skills": ["Python"],
            "certifications": [],
        }

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(expected)

        with patch("app.services.cv_parser.AsyncOpenAI") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_instance

            result = await parse_cv_with_openai("raw text", api_key="test-key")
            assert result["personal_info"]["name"] == "Jane Doe"
            assert result["skills"] == ["Python"]

    @pytest.mark.unit
    async def test_strips_markdown_fences_from_response(self):
        """Should handle response wrapped in markdown code fences."""
        expected = {"personal_info": {"name": "Test"}, "summary": "", "work_experience": [],
                    "education": [], "skills": [], "certifications": []}
        content_with_fences = f"```json\n{json.dumps(expected)}\n```"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = content_with_fences

        with patch("app.services.cv_parser.AsyncOpenAI") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_instance

            result = await parse_cv_with_openai("text", api_key="test-key")
            assert result["personal_info"]["name"] == "Test"

    @pytest.mark.unit
    async def test_uses_provided_api_key_over_settings(self):
        """When an explicit api_key is passed, it should be used instead of settings."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"personal_info": {}, "summary": "", "work_experience": [], "education": [], "skills": [], "certifications": []}'

        with patch("app.services.cv_parser.AsyncOpenAI") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_instance

            await parse_cv_with_openai("text", api_key="my-custom-key")
            MockClient.assert_called_once_with(api_key="my-custom-key")
