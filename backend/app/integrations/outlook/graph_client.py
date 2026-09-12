"""
Microsoft Graph API client for Outlook email.
Uses OAuth 2.0 — never username/password.
"""
from __future__ import annotations

import base64
import logging
import os
from typing import List, Optional

import httpx
import msal

from app.config import settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["Mail.Send", "User.Read"]


class OutlookClient:
    def __init__(self):
        self._token: Optional[str] = None
        self._app = None

    def get_auth_url(self) -> str:
        app = self._get_app()
        result = app.initiate_auth_code_flow(SCOPES, redirect_uri=settings.MICROSOFT_REDIRECT_URI)
        return result["auth_uri"]

    def handle_callback(self, code: str, state: str) -> dict:
        app = self._get_app()
        result = app.acquire_token_by_authorization_code(
            code,
            scopes=SCOPES,
            redirect_uri=settings.MICROSOFT_REDIRECT_URI,
        )
        if "error" in result:
            raise ValueError(f"OAuth error: {result.get('error_description', result.get('error'))}")
        self._token = result["access_token"]
        return result

    def is_connected(self) -> bool:
        return self._token is not None

    async def send_email(
        self,
        to: List[str],
        cc: List[str],
        subject: str,
        body: str,
        attachment_path: Optional[str] = None,
    ) -> bool:
        if not self._token:
            raise ValueError("Outlook not connected. Please authenticate first.")

        message = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body},
            "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
            "ccRecipients": [{"emailAddress": {"address": addr}} for addr in cc],
        }

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                content = base64.b64encode(f.read()).decode()
            message["attachments"] = [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": os.path.basename(attachment_path),
                    "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "contentBytes": content,
                }
            ]

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GRAPH_BASE}/me/sendMail",
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                },
                json={"message": message},
            )
            if resp.status_code == 202:
                logger.info("Email sent successfully via Graph API.")
                return True
            else:
                logger.error("Graph API error: %s — %s", resp.status_code, resp.text)
                raise ValueError(f"Outlook email could not be sent. Status: {resp.status_code}")

    def _get_app(self):
        if not all([settings.MICROSOFT_CLIENT_ID, settings.MICROSOFT_CLIENT_SECRET, settings.MICROSOFT_TENANT_ID]):
            raise ValueError("Microsoft credentials not configured.")
        if self._app is None:
            self._app = msal.ConfidentialClientApplication(
                settings.MICROSOFT_CLIENT_ID,
                authority=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}",
                client_credential=settings.MICROSOFT_CLIENT_SECRET,
            )
        return self._app


# Singleton instance
outlook_client = OutlookClient()
