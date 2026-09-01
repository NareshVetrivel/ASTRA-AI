"""
WordAgent — Orchestration layer for ASTRA-AI Word automation.

Architecture:

    Command / Intent / Entities
            |
        WordAgent
            |
     WordAutomation          (COM operations)
            |
      WordVerifier           (state verification)
            |
       AgentResult           (structured response)

WordAgent contains NO direct win32com / COM code.
All Word operations are delegated to WordAutomation.
All verification is delegated to WordVerifier.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from productivity_agent.word.automation import WordAutomation, WordAutomationError
from productivity_agent.word.verifier import WordVerifier
from productivity_agent.word import commands as cmd

logger = logging.getLogger(__name__)


# ======================================================================
# Result models  (mirrors ff_agent.models pattern)
# ======================================================================

class WordAgentStatus(str, Enum):
    """Current state of the Word Agent."""

    READY = "ready"
    CLARIFICATION_REQUIRED = "clarification_required"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


@dataclass
class WordAgentResult:
    """
    Structured result returned by every WordAgent operation.

    Designed to be convertible to the existing ASTRA response format
    by CommandDispatcher or UI layers when integration happens.
    """

    success: bool
    status: WordAgentStatus

    action: str | None = None
    message: str = ""

    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    requires_clarification: bool = False
    missing_parameters: list[str] = field(default_factory=list)


# ======================================================================
# Parameter helpers
# ======================================================================

def _require(params: dict[str, Any], *keys: str) -> list[str]:
    """Return a list of missing required parameter names."""
    return [k for k in keys if k not in params or params[k] is None or params[k] == ""]


def _clarification(action: str, missing: list[str]) -> WordAgentResult:
    """Build a clarification-required result for missing parameters."""
    return WordAgentResult(
        success=False,
        status=WordAgentStatus.CLARIFICATION_REQUIRED,
        action=action,
        message=f"Missing required parameter(s): {', '.join(missing)}.",
        requires_clarification=True,
        missing_parameters=missing,
    )


def _success(action: str, message: str, **data: Any) -> WordAgentResult:
    return WordAgentResult(
        success=True,
        status=WordAgentStatus.COMPLETED,
        action=action,
        message=message,
        data=dict(data) if data else {},
    )


def _failure(action: str, message: str, error: str | None = None) -> WordAgentResult:
    return WordAgentResult(
        success=False,
        status=WordAgentStatus.FAILED,
        action=action,
        message=message,
        error=error,
    )


def _unsupported(action: str) -> WordAgentResult:
    return WordAgentResult(
        success=False,
        status=WordAgentStatus.UNSUPPORTED,
        action=action,
        message=f"Unsupported Word operation: '{action}'.",
    )


# ======================================================================
# Operations that require a running Word application
# ======================================================================

_APP_REQUIRED_ACTIONS: set[str] = set(cmd.ALL_COMMANDS) - {cmd.OPEN_WORD}

# Operations that require an open document
_DOC_REQUIRED_ACTIONS: set[str] = (
    set(cmd.ALL_COMMANDS)
    - {
        cmd.OPEN_WORD,
        cmd.CLOSE_WORD,
        cmd.CREATE_BLANK_DOCUMENT,
        cmd.OPEN_EXISTING_DOCUMENT,
        cmd.OPEN_DOCX,
    }
)


# ======================================================================
# WordAgent
# ======================================================================

class WordAgent:
    """
    Smart orchestration layer between ASTRA's dispatcher and WordAutomation.

    Usage
    -----
    >>> agent = WordAgent()
    >>> result = agent.execute("open_word")
    >>> result = agent.execute("create_blank_document")
    >>> result = agent.execute("type_text", {"text": "Hello!"})
    >>> result = agent.execute("save_docx", {"path": "C:/tmp/hello.docx"})
    >>> result = agent.execute("close_word")
    """

    def __init__(
        self,
        automation: WordAutomation | None = None,
        verifier: WordVerifier | None = None,
        visible: bool = False,
    ) -> None:
        self._automation = automation or WordAutomation(visible=visible)
        self._verifier = verifier or WordVerifier()
        self._visible = visible

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(
        self,
        action: str,
        parameters: dict[str, Any] | None = None,
        command: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> WordAgentResult:
        """
        Execute a Word operation identified by *action*.

        Parameters
        ----------
        action : str
            Operation name from ``productivity_agent.word.commands``.
        parameters : dict, optional
            Named parameters for the operation (e.g. ``{"text": "Hello"}``).
        command : str, optional
            The raw user command text (reserved for future dispatcher use).
        context : dict, optional
            Optional context from a conversational session.

        Returns
        -------
        WordAgentResult
        """
        action = (action or "").strip().lower()
        params = dict(parameters or {})

        # ── Unsupported action (fast exit) ───────────────────────────
        handler = self._DISPATCH.get(action)
        if handler is None:
            return _unsupported(action)

        # ── Required-parameter pre-check ─────────────────────────────
        # Run this before lifecycle checks so users get actionable
        # "missing parameter" errors even when Word/document is closed.
        required = self._REQUIRED_PARAMS.get(action)
        if required:
            missing = _require(params, *required)
            if missing:
                return _clarification(action, missing)

        # ── Auto-start Word if needed ────────────────────────────────
        if action in _APP_REQUIRED_ACTIONS and self._automation._word is None:
            try:
                self._automation.start_word()
                logger.info("Word auto-started for action '%s'.", action)
            except WordAutomationError as exc:
                return _failure(action, "Could not start Word.", error=str(exc))

        # ── Auto-check document requirement ──────────────────────────
        if action in _DOC_REQUIRED_ACTIONS and self._automation._document is None:
            return _failure(
                action,
                "No document is open. Create or open a document first.",
            )

        # ── Dispatch ─────────────────────────────────────────────────
        try:
            return handler(self, params)
        except WordAutomationError as exc:
            return _failure(action, f"Word operation failed: {exc}", error=str(exc))
        except Exception as exc:
            logger.exception("Unexpected error in WordAgent.execute('%s').", action)
            return _failure(action, f"Unexpected error: {exc}", error=str(exc))

    # ------------------------------------------------------------------
    # Application lifecycle handlers
    # ------------------------------------------------------------------

    def _handle_open_word(self, params: dict[str, Any]) -> WordAgentResult:
        if self._automation._word is not None:
            return _success(cmd.OPEN_WORD, "Word is already running.")
        self._automation.start_word()
        return _success(cmd.OPEN_WORD, "Microsoft Word started.")

    def _handle_close_word(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.close_word()
        return _success(cmd.CLOSE_WORD, "Microsoft Word closed.")

    def _handle_create_blank_document(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.create_document()
        return _success(cmd.CREATE_BLANK_DOCUMENT, "Blank document created.")

    def _handle_open_existing_document(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "path")
        if missing:
            return _clarification(cmd.OPEN_EXISTING_DOCUMENT, missing)
        path = Path(params["path"])
        if not path.exists():
            return _failure(cmd.OPEN_EXISTING_DOCUMENT, f"File not found: {path}")
        self._automation.open_document(path)
        active = self._verifier.get_active_document_path(self._automation._word)
        return _success(cmd.OPEN_EXISTING_DOCUMENT, f"Opened: {path}", path=str(active or path))

    def _handle_save(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.save_document()
        return _success(cmd.SAVE, "Document saved.")

    def _handle_save_as(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "path")
        if missing:
            return _clarification(cmd.SAVE_AS, missing)
        self._automation.save_as(params["path"])
        return _success(cmd.SAVE_AS, f"Document saved as: {params['path']}")

    def _handle_close_current_document(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.close_document()
        return _success(cmd.CLOSE_CURRENT_DOCUMENT, "Document closed.")

    # ------------------------------------------------------------------
    # Content handlers
    # ------------------------------------------------------------------

    def _handle_type_text(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "text")
        if missing:
            return _clarification(cmd.TYPE_TEXT, missing)
        self._automation.type_text(params["text"])
        return _success(cmd.TYPE_TEXT, "Text typed.")

    def _handle_add_text_at_cursor(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "text")
        if missing:
            return _clarification(cmd.ADD_TEXT_AT_CURSOR, missing)
        self._automation.add_text_at_cursor(params["text"])
        return _success(cmd.ADD_TEXT_AT_CURSOR, "Text added at cursor.")

    def _handle_replace_content(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "text")
        if missing:
            return _clarification(cmd.REPLACE_CONTENT, missing)
        self._automation.replace_content(params["text"])
        return _success(cmd.REPLACE_CONTENT, "Document content replaced.")

    def _handle_read_document(self, params: dict[str, Any]) -> WordAgentResult:
        text = self._automation.read_document()
        return _success(cmd.READ_DOCUMENT, "Document content read.", text=text)

    def _handle_clear_document(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.clear_document()
        return _success(cmd.CLEAR_DOCUMENT, "Document cleared.")

    def _handle_select_all(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.select_all()
        return _success(cmd.SELECT_ALL, "All content selected.")

    def _handle_copy(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.copy()
        return _success(cmd.COPY, "Selection copied.")

    def _handle_cut(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.cut()
        return _success(cmd.CUT, "Selection cut.")

    def _handle_paste(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.paste()
        return _success(cmd.PASTE, "Content pasted.")

    # ------------------------------------------------------------------
    # Formatting handlers
    # ------------------------------------------------------------------

    def _handle_bold(self, params: dict[str, Any]) -> WordAgentResult:
        enabled = params.get("enabled", True)
        self._automation.set_bold(enabled)
        state = "enabled" if enabled else "disabled"
        return _success(cmd.BOLD, f"Bold {state}.")

    def _handle_italic(self, params: dict[str, Any]) -> WordAgentResult:
        enabled = params.get("enabled", True)
        self._automation.set_italic(enabled)
        state = "enabled" if enabled else "disabled"
        return _success(cmd.ITALIC, f"Italic {state}.")

    def _handle_underline(self, params: dict[str, Any]) -> WordAgentResult:
        enabled = params.get("enabled", True)
        self._automation.set_underline(enabled)
        state = "enabled" if enabled else "disabled"
        return _success(cmd.UNDERLINE, f"Underline {state}.")

    def _handle_strikethrough(self, params: dict[str, Any]) -> WordAgentResult:
        enabled = params.get("enabled", True)
        self._automation.set_strikethrough(enabled)
        state = "enabled" if enabled else "disabled"
        return _success(cmd.STRIKETHROUGH, f"Strikethrough {state}.")

    def _handle_font(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "name")
        if missing:
            return _clarification(cmd.FONT, missing)
        self._automation.set_font(params["name"])
        return _success(cmd.FONT, f"Font set to '{params['name']}'.")

    def _handle_font_size(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "size")
        if missing:
            return _clarification(cmd.FONT_SIZE, missing)
        try:
            size = float(params["size"])
        except (TypeError, ValueError):
            return _failure(cmd.FONT_SIZE, f"Invalid font size: '{params['size']}'. Must be a number.")
        if size <= 0 or size > 1638:
            return _failure(cmd.FONT_SIZE, f"Font size {size} out of valid range (0-1638).")
        self._automation.set_font_size(size)
        return _success(cmd.FONT_SIZE, f"Font size set to {size}pt.")

    def _handle_text_color(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "r", "g", "b")
        if missing:
            return _clarification(cmd.TEXT_COLOR, missing)
        self._automation.set_text_color(int(params["r"]), int(params["g"]), int(params["b"]))
        return _success(cmd.TEXT_COLOR, "Text color set.")

    def _handle_highlight(self, params: dict[str, Any]) -> WordAgentResult:
        color_index = params.get("color_index", 7)
        self._automation.set_highlight(int(color_index))
        return _success(cmd.HIGHLIGHT, "Highlight applied.")

    def _handle_align_left(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.align_left()
        return _success(cmd.ALIGN_LEFT, "Aligned left.")

    def _handle_align_center(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.align_center()
        return _success(cmd.ALIGN_CENTER, "Aligned center.")

    def _handle_align_right(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.align_right()
        return _success(cmd.ALIGN_RIGHT, "Aligned right.")

    def _handle_justify(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.justify()
        return _success(cmd.JUSTIFY, "Justified.")

    # ------------------------------------------------------------------
    # Paragraph handlers
    # ------------------------------------------------------------------

    def _handle_line_spacing(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "value")
        if missing:
            return _clarification(cmd.LINE_SPACING, missing)
        self._automation.set_line_spacing(float(params["value"]))
        return _success(cmd.LINE_SPACING, f"Line spacing set to {params['value']}.")

    def _handle_paragraph_spacing(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.set_paragraph_spacing(
            before=params.get("before"),
            after=params.get("after"),
        )
        return _success(cmd.PARAGRAPH_SPACING, "Paragraph spacing updated.")

    def _handle_indentation(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.set_indentation(
            left=params.get("left"),
            right=params.get("right"),
            first_line=params.get("first_line"),
        )
        return _success(cmd.INDENTATION, "Indentation updated.")

    def _handle_bullets(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.apply_bullets()
        return _success(cmd.BULLETS, "Bullet list applied.")

    def _handle_numbering(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.apply_numbering()
        return _success(cmd.NUMBERING, "Numbered list applied.")

    # ------------------------------------------------------------------
    # Style handlers
    # ------------------------------------------------------------------

    def _handle_title(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.apply_title()
        return _success(cmd.TITLE, "Title style applied.")

    def _handle_heading_1(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.apply_heading1()
        return _success(cmd.HEADING_1, "Heading 1 style applied.")

    def _handle_normal(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.apply_normal()
        return _success(cmd.NORMAL, "Normal style applied.")

    def _handle_document_style(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "style_name")
        if missing:
            return _clarification(cmd.DOCUMENT_STYLE, missing)
        self._automation.change_style(params["style_name"])
        return _success(cmd.DOCUMENT_STYLE, f"Style '{params['style_name']}' applied.")

    # ------------------------------------------------------------------
    # Table handlers
    # ------------------------------------------------------------------

    def _handle_create_table(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "rows", "columns")
        if missing:
            return _clarification(cmd.CREATE_TABLE, missing)
        try:
            rows = int(params["rows"])
            columns = int(params["columns"])
        except (TypeError, ValueError):
            return _failure(cmd.CREATE_TABLE, "Rows and columns must be integers.")
        if rows < 1 or columns < 1:
            return _failure(cmd.CREATE_TABLE, "Table must have at least 1 row and 1 column.")
        self._automation.create_table(rows, columns)
        return _success(cmd.CREATE_TABLE, f"Table created ({rows}x{columns}).", rows=rows, columns=columns)

    def _handle_read_table_data(self, params: dict[str, Any]) -> WordAgentResult:
        table_index = int(params.get("table_index", 1))
        data = self._automation.read_table_data(table_index)
        return _success(cmd.READ_TABLE_DATA, "Table data read.", table_data=data)

    # ------------------------------------------------------------------
    # Find / Replace handlers
    # ------------------------------------------------------------------

    def _handle_find(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "text")
        if missing:
            return _clarification(cmd.FIND, missing)
        found = self._automation.find_text(params["text"])
        if found:
            return _success(cmd.FIND, f"Found: '{params['text']}'.", found=True)
        return _success(cmd.FIND, f"'{params['text']}' not found.", found=False)

    def _handle_replace(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "find_text", "replace_text")
        if missing:
            return _clarification(cmd.REPLACE, missing)
        count = self._automation.replace_text(params["find_text"], params["replace_text"])
        if count:
            return _success(cmd.REPLACE, "Replacement made.", replaced=True)
        return _success(cmd.REPLACE, "No match found to replace.", replaced=False)

    # ------------------------------------------------------------------
    # Insert handlers
    # ------------------------------------------------------------------

    def _handle_image(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "path")
        if missing:
            return _clarification(cmd.IMAGE, missing)
        path = Path(params["path"])
        if not path.exists():
            return _failure(cmd.IMAGE, f"Image file not found: {path}")
        self._automation.insert_image(path)
        return _success(cmd.IMAGE, f"Image inserted: {path}")

    def _handle_hyperlink(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "url")
        if missing:
            return _clarification(cmd.HYPERLINK, missing)
        display_text = params.get("text", params.get("display_text"))
        self._automation.insert_hyperlink(params["url"], display_text)
        return _success(cmd.HYPERLINK, f"Hyperlink inserted: {params['url']}")

    # ------------------------------------------------------------------
    # Document structure handlers
    # ------------------------------------------------------------------

    def _handle_page_break(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.insert_page_break()
        return _success(cmd.PAGE_BREAK, "Page break inserted.")

    def _handle_new_page(self, params: dict[str, Any]) -> WordAgentResult:
        # new_page is semantically identical to page_break
        self._automation.insert_page_break()
        return _success(cmd.NEW_PAGE, "New page inserted.")

    def _handle_header(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "text")
        if missing:
            return _clarification(cmd.HEADER, missing)
        self._automation.set_header(params["text"])
        return _success(cmd.HEADER, "Header set.")

    def _handle_footer(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "text")
        if missing:
            return _clarification(cmd.FOOTER, missing)
        self._automation.set_footer(params["text"])
        return _success(cmd.FOOTER, "Footer set.")

    def _handle_page_number(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.add_page_number()
        return _success(cmd.PAGE_NUMBER, "Page numbers added.")

    def _handle_margins(self, params: dict[str, Any]) -> WordAgentResult:
        self._automation.set_margins(
            top=params.get("top"),
            bottom=params.get("bottom"),
            left=params.get("left"),
            right=params.get("right"),
        )
        return _success(cmd.MARGINS, "Margins updated.")

    # ------------------------------------------------------------------
    # File handlers (with verification)
    # ------------------------------------------------------------------

    def _handle_save_docx(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "path")
        if missing:
            return _clarification(cmd.SAVE_DOCX, missing)
        path = params["path"]
        self._automation.save_as_docx(path)
        if not self._verifier.docx_exists(path):
            return _failure(cmd.SAVE_DOCX, f"Save appeared to succeed but file not found: {path}")
        return _success(cmd.SAVE_DOCX, f"Document saved as DOCX: {path}", path=str(path))

    def _handle_save_pdf(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "path")
        if missing:
            return _clarification(cmd.SAVE_PDF, missing)
        path = params["path"]
        self._automation.save_as_pdf(path)
        if not self._verifier.pdf_exists(path):
            return _failure(cmd.SAVE_PDF, f"Export appeared to succeed but file not found: {path}")
        return _success(cmd.SAVE_PDF, f"Document exported as PDF: {path}", path=str(path))

    def _handle_open_docx(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "path")
        if missing:
            return _clarification(cmd.OPEN_DOCX, missing)
        path = Path(params["path"])
        if not path.exists():
            return _failure(cmd.OPEN_DOCX, f"File not found: {path}")
        self._automation.open_document(path)
        active = self._verifier.get_active_document_path(self._automation._word)
        return _success(cmd.OPEN_DOCX, f"Opened: {path}", path=str(active or path))

    def _handle_create_specified_filename(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "path")
        if missing:
            return _clarification(cmd.CREATE_SPECIFIED_FILENAME, missing)
        self._automation.create_document()
        self._automation.save_as_docx(params["path"])
        if not self._verifier.docx_exists(params["path"]):
            return _failure(cmd.CREATE_SPECIFIED_FILENAME, "Document created but save verification failed.")
        return _success(cmd.CREATE_SPECIFIED_FILENAME, f"Document created: {params['path']}", path=str(params["path"]))

    def _handle_read_existing_document(self, params: dict[str, Any]) -> WordAgentResult:
        missing = _require(params, "path")
        if missing:
            return _clarification(cmd.READ_EXISTING_DOCUMENT, missing)
        path = Path(params["path"])
        if not path.exists():
            return _failure(cmd.READ_EXISTING_DOCUMENT, f"File not found: {path}")
        self._automation.open_document(path)
        text = self._automation.read_document()
        return _success(cmd.READ_EXISTING_DOCUMENT, "Document read.", text=text, path=str(path))

    # ------------------------------------------------------------------
    # Dispatch table
    # ------------------------------------------------------------------

    _DISPATCH: dict[str, Any] = {
        # Application
        cmd.OPEN_WORD: _handle_open_word,
        cmd.CLOSE_WORD: _handle_close_word,
        cmd.CREATE_BLANK_DOCUMENT: _handle_create_blank_document,
        cmd.OPEN_EXISTING_DOCUMENT: _handle_open_existing_document,
        cmd.SAVE: _handle_save,
        cmd.SAVE_AS: _handle_save_as,
        cmd.CLOSE_CURRENT_DOCUMENT: _handle_close_current_document,

        # Content
        cmd.TYPE_TEXT: _handle_type_text,
        cmd.ADD_TEXT_AT_CURSOR: _handle_add_text_at_cursor,
        cmd.REPLACE_CONTENT: _handle_replace_content,
        cmd.READ_DOCUMENT: _handle_read_document,
        cmd.CLEAR_DOCUMENT: _handle_clear_document,
        cmd.SELECT_ALL: _handle_select_all,
        cmd.COPY: _handle_copy,
        cmd.CUT: _handle_cut,
        cmd.PASTE: _handle_paste,

        # Formatting
        cmd.BOLD: _handle_bold,
        cmd.ITALIC: _handle_italic,
        cmd.UNDERLINE: _handle_underline,
        cmd.STRIKETHROUGH: _handle_strikethrough,
        cmd.FONT: _handle_font,
        cmd.FONT_SIZE: _handle_font_size,
        cmd.TEXT_COLOR: _handle_text_color,
        cmd.HIGHLIGHT: _handle_highlight,
        cmd.ALIGN_LEFT: _handle_align_left,
        cmd.ALIGN_CENTER: _handle_align_center,
        cmd.ALIGN_RIGHT: _handle_align_right,
        cmd.JUSTIFY: _handle_justify,

        # Paragraph
        cmd.LINE_SPACING: _handle_line_spacing,
        cmd.PARAGRAPH_SPACING: _handle_paragraph_spacing,
        cmd.INDENTATION: _handle_indentation,
        cmd.BULLETS: _handle_bullets,
        cmd.NUMBERING: _handle_numbering,

        # Styles
        cmd.TITLE: _handle_title,
        cmd.HEADING_1: _handle_heading_1,
        cmd.NORMAL: _handle_normal,
        cmd.DOCUMENT_STYLE: _handle_document_style,

        # Tables
        cmd.CREATE_TABLE: _handle_create_table,
        cmd.READ_TABLE_DATA: _handle_read_table_data,

        # Find / Replace
        cmd.FIND: _handle_find,
        cmd.REPLACE: _handle_replace,

        # Insert
        cmd.IMAGE: _handle_image,
        cmd.HYPERLINK: _handle_hyperlink,

        # Document structure
        cmd.NEW_PAGE: _handle_new_page,
        cmd.PAGE_BREAK: _handle_page_break,
        cmd.HEADER: _handle_header,
        cmd.FOOTER: _handle_footer,
        cmd.PAGE_NUMBER: _handle_page_number,
        cmd.MARGINS: _handle_margins,

        # Files
        cmd.SAVE_DOCX: _handle_save_docx,
        cmd.SAVE_PDF: _handle_save_pdf,
        cmd.OPEN_DOCX: _handle_open_docx,
        cmd.CREATE_SPECIFIED_FILENAME: _handle_create_specified_filename,
        cmd.READ_EXISTING_DOCUMENT: _handle_read_existing_document,
    }

    # Required parameters per action (used by pre-dispatch validation)
    _REQUIRED_PARAMS: dict[str, tuple[str, ...]] = {
        cmd.TYPE_TEXT: ("text",),
        cmd.ADD_TEXT_AT_CURSOR: ("text",),
        cmd.REPLACE_CONTENT: ("text",),
        cmd.OPEN_EXISTING_DOCUMENT: ("path",),
        cmd.SAVE_AS: ("path",),
        cmd.FONT: ("name",),
        cmd.FONT_SIZE: ("size",),
        cmd.TEXT_COLOR: ("r", "g", "b"),
        cmd.LINE_SPACING: ("value",),
        cmd.DOCUMENT_STYLE: ("style_name",),
        cmd.CREATE_TABLE: ("rows", "columns"),
        cmd.FIND: ("text",),
        cmd.REPLACE: ("find_text", "replace_text"),
        cmd.IMAGE: ("path",),
        cmd.HYPERLINK: ("url",),
        cmd.HEADER: ("text",),
        cmd.FOOTER: ("text",),
        cmd.SAVE_DOCX: ("path",),
        cmd.SAVE_PDF: ("path",),
        cmd.OPEN_DOCX: ("path",),
        cmd.CREATE_SPECIFIED_FILENAME: ("path",),
        cmd.READ_EXISTING_DOCUMENT: ("path",),
    }
