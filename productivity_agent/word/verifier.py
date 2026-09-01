"""
WordVerifier — Verification helpers for Word automation.

All methods inspect actual state (filesystem, COM objects) rather than
blindly trusting return values from automation calls.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class WordVerifier:
    """Verification helpers that check real-world state after Word operations."""

    # ── Application ───────────────────────────────────────────────────

    @staticmethod
    def is_word_available() -> bool:
        """Return True if Word COM automation is reachable."""
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            word.Quit()
            return True
        except Exception:
            return False

    @staticmethod
    def is_word_running() -> bool:
        """Return True if there is an active Word.Application instance."""
        try:
            import win32com.client
            win32com.client.GetActiveObject("Word.Application")
            return True
        except Exception:
            return False

    # ── Document existence ────────────────────────────────────────────

    @staticmethod
    def document_exists(path: str | Path) -> bool:
        """Return True if a file exists at *path*."""
        return Path(path).resolve().exists()

    @staticmethod
    def docx_exists(path: str | Path) -> bool:
        """Return True if a .docx file exists at *path*."""
        p = Path(path).resolve()
        return p.exists() and p.suffix.lower() == ".docx"

    @staticmethod
    def pdf_exists(path: str | Path) -> bool:
        """Return True if a .pdf file exists at *path*."""
        p = Path(path).resolve()
        return p.exists() and p.suffix.lower() == ".pdf"

    # ── Opened document ───────────────────────────────────────────────

    @staticmethod
    def get_active_document_path(word_app: Any) -> str | None:
        """Return the full path of the currently active document, or None."""
        try:
            doc = word_app.ActiveDocument
            return doc.FullName
        except Exception:
            return None

    @staticmethod
    def verify_document_has_content(word_app: Any) -> bool:
        """Return True if the active document contains non-whitespace text."""
        try:
            text: str = word_app.ActiveDocument.Content.Text
            return bool(text.strip())
        except Exception:
            return False

    @staticmethod
    def verify_file_not_empty(path: str | Path) -> bool:
        """Return True if *path* exists and has a non-zero file size."""
        p = Path(path).resolve()
        return p.exists() and p.stat().st_size > 0
