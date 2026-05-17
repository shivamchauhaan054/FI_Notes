import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.core.config import settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(
        settings.smtp_host
        and settings.smtp_from
        and settings.smtp_user
        and settings.smtp_password
    )


def send_otp_email(to_email: str, otp: str, purpose: str = "verify your account") -> bool:
    """
    Send an OTP email. Returns True if sent successfully, False if the
    network is unreachable (e.g. Railway blocks outbound SMTP). Raises
    on credential/auth errors so misconfiguration is visible in logs.
    """
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
            "SMTP not configured. OTP for %s: %s (set SMTP_* env vars to send real emails)",
            to_email,
            otp,
        )
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = formataddr(("FI Notes", settings.smtp_from))
    message["To"] = to_email
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    port = settings.smtp_port
    logger.info("Connecting to SMTP server %s:%s...", settings.smtp_host, port)

    try:
        # Port 465 -> implicit TLS (SMTP_SSL); port 587 -> STARTTLS
        if port == 465:
            ssl_context = ssl.create_default_context()
            with smtplib.SMTP_SSL(settings.smtp_host, port, timeout=15, context=ssl_context) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from, [to_email], message.as_string())
        else:
            with smtplib.SMTP(settings.smtp_host, port, timeout=15) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from, [to_email], message.as_string())

        logger.info("OTP email successfully sent to %s", to_email)
        return True

    except OSError as exc:
        # Covers [Errno 101] Network is unreachable, [Errno 111] Connection refused, etc.
        # These are infrastructure-level blocks (e.g. Railway firewall) - not code bugs.
        logger.warning(
            "SMTP network unreachable for %s (port %s blocked by host): %s "
            "- OTP will be shown on screen.",
            to_email, port, exc,
        )
        return False

    except smtplib.SMTPAuthenticationError as exc:
        # Wrong credentials - this IS a config bug, so raise it.
        logger.error("SMTP authentication failed for user %s: %s", settings.smtp_user, exc)
        raise

    except smtplib.SMTPResponseException as exc:
        logger.error("SMTP error %s: %s", exc.smtp_code, exc.smtp_error)
        raise

    except Exception as exc:
        logger.error("Unexpected SMTP error sending to %s: %s", to_email, exc)
        return False
