import os
import aiosmtplib
from email.message import EmailMessage


async def send_magic_link(to_email: str, token: str) -> None:
    base_url = os.getenv("MAGIC_LINK_BASE_URL", "http://localhost:8080")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")

    link = f"{base_url}/auth/verify?token={token}"

    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = "Your login link"
    msg.set_content(f"Click the link below to log in (expires in 15 minutes):\n\n{link}")

    await aiosmtplib.send(
        msg,
        hostname=smtp_host,
        port=smtp_port,
        username=smtp_user,
        password=smtp_password,
        start_tls=True,
    )
