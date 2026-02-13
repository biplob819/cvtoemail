"""Email service for sending job notifications with CV attachments."""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """Raised when email sending fails."""
    pass


class EmailSender:
    """Handles sending emails via SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email

    def send_job_notification(
        self,
        to_email: str,
        job_title: str,
        company: str,
        location: Optional[str],
        job_url: str,
        job_description: Optional[str],
        cv_pdf_path: Optional[Path] = None,
    ) -> bool:
        """
        Send job notification email with tailored CV attachment.

        Args:
            to_email: Recipient email address
            job_title: Job title
            company: Company name
            location: Job location (optional)
            job_url: URL to the job posting
            job_description: Job description text (optional)
            cv_pdf_path: Path to the tailored CV PDF (optional)

        Returns:
            bool: True if sent successfully, False otherwise

        Raises:
            EmailSendError: If email sending fails
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = f"New Job Match: {job_title} at {company}"

            # Build email body
            body = self._build_email_body(
                job_title=job_title,
                company=company,
                location=location,
                job_url=job_url,
                job_description=job_description,
            )
            msg.attach(MIMEText(body, "html"))

            # Attach CV PDF if provided
            if cv_pdf_path and cv_pdf_path.exists():
                with open(cv_pdf_path, "rb") as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
                    pdf_attachment.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=f"CV_{company.replace(' ', '_')}_{job_title.replace(' ', '_')}.pdf",
                    )
                    msg.attach(pdf_attachment)
                    logger.info(f"Attached CV PDF: {cv_pdf_path}")

            # Send email
            self._send_email(msg)
            logger.info(f"Email sent successfully to {to_email} for job: {job_title} at {company}")
            return True

        except Exception as e:
            error_msg = f"Failed to send email for job '{job_title}' at '{company}': {str(e)}"
            logger.error(error_msg)
            raise EmailSendError(error_msg) from e

    def send_test_email(self, to_email: str) -> bool:
        """
        Send a test email to verify SMTP configuration.

        Args:
            to_email: Recipient email address

        Returns:
            bool: True if sent successfully

        Raises:
            EmailSendError: If email sending fails
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = "Auto Job Apply - Test Email"

            body = """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #2563EB;">Email Configuration Test</h2>
                <p>This is a test email from <strong>Auto Job Apply</strong>.</p>
                <p>If you're receiving this, your email configuration is working correctly! ✓</p>
                <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 20px 0;">
                <p style="color: #6B7280; font-size: 14px;">
                    Sent at: {timestamp}
                </p>
            </body>
            </html>
            """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            msg.attach(MIMEText(body, "html"))
            self._send_email(msg)
            logger.info(f"Test email sent successfully to {to_email}")
            return True

        except Exception as e:
            error_msg = f"Failed to send test email: {str(e)}"
            logger.error(error_msg)
            raise EmailSendError(error_msg) from e

    def _send_email(self, msg: MIMEMultipart):
        """Internal method to send email via SMTP."""
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
        except smtplib.SMTPAuthenticationError as e:
            raise EmailSendError(f"SMTP authentication failed. Check your email and password.") from e
        except smtplib.SMTPConnectError as e:
            raise EmailSendError(f"Failed to connect to SMTP server {self.smtp_host}:{self.smtp_port}") from e
        except smtplib.SMTPException as e:
            raise EmailSendError(f"SMTP error occurred: {str(e)}") from e
        except Exception as e:
            raise EmailSendError(f"Unexpected error sending email: {str(e)}") from e

    def _build_email_body(
        self,
        job_title: str,
        company: str,
        location: Optional[str],
        job_url: str,
        job_description: Optional[str],
    ) -> str:
        """Build HTML email body."""
        location_html = f"<p><strong>Location:</strong> {location}</p>" if location else ""
        
        # Truncate description if too long
        description_preview = ""
        if job_description:
            max_length = 500
            if len(job_description) > max_length:
                description_preview = job_description[:max_length] + "..."
            else:
                description_preview = job_description
            description_html = f"""
            <div style="background-color: #F9FAFB; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #111827;">Job Description</h3>
                <p style="color: #6B7280; margin-bottom: 0;">{description_preview}</p>
            </div>
            """
        else:
            description_html = ""

        return f"""
        <html>
        <body style="font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #111827; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #2563EB; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">New Job Match Found!</h1>
            </div>
            
            <div style="padding: 30px; background-color: #FFFFFF;">
                <h2 style="color: #2563EB; margin-top: 0;">{job_title}</h2>
                <p><strong>Company:</strong> {company}</p>
                {location_html}
                
                {description_html}
                
                <div style="margin: 30px 0;">
                    <a href="{job_url}" 
                       style="display: inline-block; background-color: #2563EB; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 6px; font-weight: 600;">
                        View Job Posting →
                    </a>
                </div>
                
                <div style="background-color: #FEF3C7; border-left: 4px solid #D97706; padding: 15px; margin-top: 20px;">
                    <p style="margin: 0; color: #92400E;">
                        <strong>📎 Tailored CV Attached</strong><br>
                        A customized CV has been generated for this position and is attached to this email.
                    </p>
                </div>
            </div>
            
            <div style="padding: 20px; background-color: #F9FAFB; border-radius: 0 0 8px 8px; text-align: center;">
                <p style="color: #6B7280; font-size: 14px; margin: 0;">
                    Sent by <strong>Auto Job Apply</strong> | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                </p>
            </div>
        </body>
        </html>
        """


def create_email_sender(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    from_email: str,
) -> EmailSender:
    """Factory function to create EmailSender instance."""
    return EmailSender(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        from_email=from_email,
    )
