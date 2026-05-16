import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(
        settings.smtp_host
        and settings.smtp_from
        and settings.smtp_user
        and settings.smtp_password
    )


def send_otp_email(to_email: str, otp: str, purpose: str = "verify your account") -> None:
    subject = f"Your FI Notes verification code: {otp}"
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1a2332;">
        <div style="max-width: 480px; margin: 0 auto; padding: 24px;">
          <h2 style="color: #6366f1;">FI Notes</h2>
          <p>Use this code to {purpose}:</p>
          <p style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #6366f1;">{otp}</p>
          <p>This code expires in {settings.otp_expire_minutes} minutes.</p>
          <p style="color: #8b9cb3; font-size: 13px;">If you did not request this, you can ignore this email.</p>
        </div>
      </body>
    </html>
    """
    text = (
        f"Your FI Notes verification code is: {otp}\n"
        f"It expires in {settings.otp_expire_minutes} minutes.\n"
        f"If you did not request this, ignore this email."
    )

    if not smtp_configured():
        logger.warning(
            "SMTP not configured. OTP for %s: %s (set SMTP_* in .env to send real emails)",
            to_email,
            otp,
        )
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, [to_email], message.as_string())
        logger.info("OTP email sent to %s", to_email)
    except smtplib.SMTPException as exc:
        logger.error("Failed to send OTP email to %s: %s", to_email, exc)
        raise
