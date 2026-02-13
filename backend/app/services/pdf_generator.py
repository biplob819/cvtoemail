"""PDF generation service -- renders CV data to ATS-friendly PDF using WeasyPrint."""

import os
from pathlib import Path
from typing import Optional

from app.config import settings

# ATS-friendly CV template (single column, no tables, no graphics, standard fonts)
# Optimized for maximum ATS compatibility with semantic HTML and minimal styling
CV_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resume</title>
<style>
  /* Use web-safe fonts that ATS systems can parse easily */
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #000000;
    padding: 0.5in 0.75in;
    max-width: 8.5in;
  }

  h1 {
    font-size: 18pt;
    font-weight: 700;
    margin-bottom: 8px;
    color: #000000;
  }

  .contact-info {
    font-size: 10pt;
    color: #333333;
    margin-bottom: 20px;
    line-height: 1.4;
  }

  .contact-info span {
    display: inline-block;
    margin-right: 12px;
  }

  h2 {
    font-size: 12pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 2px solid #000000;
    padding-bottom: 4px;
    margin-top: 18px;
    margin-bottom: 12px;
    color: #000000;
  }

  .summary {
    margin-bottom: 10px;
    font-size: 10.5pt;
    line-height: 1.6;
  }

  .entry {
    margin-bottom: 14px;
    page-break-inside: avoid;
  }

  .entry-header {
    margin-bottom: 4px;
  }

  .entry-title {
    font-weight: 700;
    font-size: 11pt;
    color: #000000;
  }

  .entry-subtitle {
    font-size: 10.5pt;
    color: #333333;
    font-style: italic;
  }

  .entry-duration {
    font-size: 10pt;
    color: #666666;
    margin-top: 2px;
  }

  ul {
    margin-left: 20px;
    margin-top: 6px;
    list-style-type: disc;
  }

  li {
    font-size: 10.5pt;
    margin-bottom: 4px;
    line-height: 1.5;
  }

  .skills-list {
    font-size: 10.5pt;
    line-height: 1.8;
  }

  .cert-entry {
    margin-bottom: 6px;
    font-size: 10.5pt;
  }

  /* Ensure page breaks don't split sections awkwardly */
  h2 {
    page-break-after: avoid;
  }

  .entry {
    page-break-inside: avoid;
  }
</style>
</head>
<body>
  {content}
</body>
</html>"""


def _build_cv_html(cv_data: dict) -> str:
    """Build the inner HTML content from structured CV data with ATS-optimized formatting."""
    parts = []

    # Personal info / header - Use semantic structure for ATS parsing
    pi = cv_data.get("personal_info", {})
    name = pi.get("name", "Your Name")
    parts.append(f"<h1>{name}</h1>")

    contact_items = []
    for key in ["email", "phone", "location", "linkedin", "website"]:
        val = pi.get(key)
        if val:
            contact_items.append(f"<span>{val}</span>")
    if contact_items:
        parts.append(f'<div class="contact-info">{"".join(contact_items)}</div>')

    # Summary - Professional summary is important for ATS keyword matching
    summary = cv_data.get("summary", "")
    if summary:
        parts.append("<h2>Professional Summary</h2>")
        parts.append(f'<p class="summary">{summary}</p>')

    # Work Experience - Most critical section for ATS
    experience = cv_data.get("work_experience", [])
    if experience:
        parts.append("<h2>Work Experience</h2>")
        for entry in experience:
            parts.append('<div class="entry">')
            parts.append('<div class="entry-header">')
            # Job title and company on separate lines for better ATS parsing
            parts.append(f'<div class="entry-title">{entry.get("title", "")}</div>')
            parts.append(f'<div class="entry-subtitle">{entry.get("company", "")}</div>')
            parts.append(f'<div class="entry-duration">{entry.get("duration", "")}</div>')
            parts.append('</div>')
            achievements = entry.get("achievements", [])
            if achievements:
                parts.append("<ul>")
                for ach in achievements:
                    parts.append(f"<li>{ach}</li>")
                parts.append("</ul>")
            parts.append('</div>')

    # Education
    education = cv_data.get("education", [])
    if education:
        parts.append("<h2>Education</h2>")
        for entry in education:
            parts.append('<div class="entry">')
            parts.append('<div class="entry-header">')
            parts.append(f'<div class="entry-title">{entry.get("degree", "")}</div>')
            parts.append(f'<div class="entry-subtitle">{entry.get("institution", "")}</div>')
            parts.append(f'<div class="entry-duration">{entry.get("year", "")}</div>')
            parts.append('</div>')
            details = entry.get("details")
            if details:
                parts.append(f'<div style="font-size:10.5pt;margin-top:4px;">{details}</div>')
            parts.append('</div>')

    # Skills - Very important for ATS keyword matching
    skills = cv_data.get("skills", [])
    if skills:
        parts.append("<h2>Skills</h2>")
        # Use comma separation for better ATS parsing
        parts.append(f'<div class="skills-list">{", ".join(skills)}</div>')

    # Certifications
    certs = cv_data.get("certifications", [])
    if certs:
        parts.append("<h2>Certifications</h2>")
        for cert in certs:
            line = cert.get("name", "")
            issuer = cert.get("issuer")
            year = cert.get("year")
            if issuer:
                line += f" - {issuer}"
            if year:
                line += f" ({year})"
            parts.append(f'<div class="cert-entry">{line}</div>')

    return "\n".join(parts)


def generate_cv_html(cv_data: dict) -> str:
    """Generate full HTML document for a CV."""
    content = _build_cv_html(cv_data)
    return CV_TEMPLATE.replace("{content}", content)


def generate_cv_pdf(cv_data: dict, output_path: Optional[str] = None) -> bytes:
    """Generate ATS-friendly PDF from CV data. Returns PDF bytes.
    Falls back to HTML if WeasyPrint is not available."""
    try:
        from weasyprint import HTML

        html_string = generate_cv_html(cv_data)
        html = HTML(string=html_string)

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            html.write_pdf(output_path)
            with open(output_path, "rb") as f:
                return f.read()
        else:
            return html.write_pdf()
    except ImportError:
        # WeasyPrint not available -- return HTML as bytes for preview
        html_string = generate_cv_html(cv_data)
        return html_string.encode("utf-8")
