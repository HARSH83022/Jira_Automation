from __future__ import annotations

import mimetypes
import os
import smtplib
from email.message import EmailMessage
from typing import Iterable, Optional

from app.config import settings
from app.integrations.email.provider import EmailProvider


class GmailEmailProvider(EmailProvider):
    host = "smtp.gmail.com"
    port = 587

    def __init__(self, user: Optional[str] = None, app_password: Optional[str] = None):
        self.user = user if user is not None else settings.GMAIL_USER
        self.app_password = (
            app_password if app_password is not None else settings.GMAIL_APP_PASSWORD
        )

    def validate_configuration(self) -> None:
        if not self.user or not self.app_password:
            raise ValueError(
                "Gmail is not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD in backend/.env."
            )

    def send(
        self,
        *,
        to: Iterable[str],
        cc: Iterable[str],
        subject: str,
        body: str,
        attachment_path: Optional[str] = None,
        attachment_filename: Optional[str] = None,
    ) -> None:
        self.validate_configuration()
        recipients = [*to, *cc]
        if not recipients:
            raise ValueError("At least one recipient is required.")
        message = EmailMessage()
        message["From"] = self.user
        message["To"] = ", ".join(to)
        if cc:
            message["Cc"] = ", ".join(cc)
        message["Subject"] = subject
        message.set_content(body)

        if attachment_path:
            if not os.path.isfile(attachment_path):
                raise FileNotFoundError("Email attachment does not exist.")
            content_type, _ = mimetypes.guess_type(attachment_path)
            maintype, subtype = (content_type or "application/octet-stream").split("/", 1)
            with open(attachment_path, "rb") as handle:
                message.add_attachment(
                    handle.read(),
                    maintype=maintype,
                    subtype=subtype,
                    filename=attachment_filename or os.path.basename(attachment_path),
                )

        with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(self.user, self.app_password)
            smtp.send_message(message, from_addr=self.user, to_addrs=recipients)

    def test_connection(self) -> None:
        self.validate_configuration()
        with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(self.user, self.app_password)
