from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional


class EmailProvider(ABC):
    @abstractmethod
    def validate_configuration(self) -> None:
        """Raise a clear error when provider configuration is incomplete."""

    @abstractmethod
    def test_connection(self) -> None:
        """Open and authenticate a provider connection without sending mail."""

    @abstractmethod
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
        """Send one email."""
