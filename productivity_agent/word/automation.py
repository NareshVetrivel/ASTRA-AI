"""
WordAutomation — Microsoft Word COM automation wrapper.

All COM-specific logic is isolated inside this module.
Primary automation mechanism: pywin32 / win32com.client.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import win32com.client
import pywintypes  # noqa: F401 — needed for pywintypes.com_error

logger = logging.getLogger(__name__)

# ── Word COM constants ────────────────────────────────────────────────

# File format enums (wdSaveFormat)
WD_FORMAT_DOCUMENT_DEFAULT = 16  # .docx
WD_FORMAT_PDF = 17               # .pdf

# Alignment enums (wdParagraphAlignment)
WD_ALIGN_LEFT = 0
WD_ALIGN_CENTER = 1
WD_ALIGN_RIGHT = 2
WD_ALIGN_JUSTIFY = 3

# Line-spacing rule enums (wdLineSpacingRule)
WD_LINE_SPACE_SINGLE = 0
WD_LINE_SPACE_1PT5 = 1
WD_LINE_SPACE_DOUBLE = 2
WD_LINE_SPACE_EXACTLY = 4
WD_LINE_SPACE_MULTIPLE = 5

# List gallery type enums
WD_LIST_BULLET = 0
WD_LIST_NUMBER = 1

# Selection type
WD_SELECTION_NORMAL = 1

# Header/Footer index
WD_HEADER_FOOTER_PRIMARY = 1

# Page-number alignment
WD_ALIGN_PAGE_NUMBER_CENTER = 1

# wdStory / wdMove
WD_STORY = 6
WD_MOVE = 0

# Section start types
WD_SECTION_NEW_PAGE = 2

# Find wrap enum
WD_FIND_CONTINUE = 1

# Find/Replace enums
WD_REPLACE_ONE = 1
WD_REPLACE_ALL = 2


class WordAutomationError(Exception):
    """Raised when a Word COM operation fails."""


class WordAutomation:
    """Reusable Microsoft Word COM automation class.

    Usage
    -----
    >>> wa = WordAutomation()
    >>> wa.start_word()
    >>> wa.create_document()
    >>> wa.type_text("Hello, ASTRA!")
    >>> wa.save_as_docx(r"C:\\temp\\hello.docx")
    >>> wa.close_document()
    >>> wa.close_word()
    """

    def __init__(self, visible: bool = False) -> None:
        self._visible = visible
        self._word: Any | None = None
        self._document: Any | None = None

    # ── helpers ───────────────────────────────────────────────────────

    @property
    def word(self) -> Any:
        """Return the live Word.Application COM object or raise."""
        if self._word is None:
            raise WordAutomationError(
                "Word application is not running. "
                "Call start_word() first."
            )
        return self._word

    @property
    def document(self) -> Any:
        """Return the active document COM object or raise."""
        if self._document is None:
            raise WordAutomationError(
                "No document is open. "
                "Call create_document() or open_document() first."
            )
        return self._document

    @property
    def selection(self) -> Any:
        """Shortcut to the Word Selection object."""
        return self.word.Selection

    def _validate_path(self, path: str | Path) -> Path:
        """Resolve and validate a filesystem path."""
        p = Path(path).resolve()
        return p

    def _ensure_parent_dir(self, path: Path) -> None:
        """Create parent directories if they don't exist."""
        path.parent.mkdir(parents=True, exist_ok=True)

    # ══════════════════════════════════════════════════════════════════
    # APPLICATION LIFECYCLE
    # ══════════════════════════════════════════════════════════════════

    def start_word(self) -> None:
        """Start a new Word COM instance."""
        try:
            self._word = win32com.client.Dispatch("Word.Application")
            self._word.Visible = self._visible

            logger.info(
                "Word application started (version %s).",
                self._word.Version,
            )

        except Exception as exc:
            raise WordAutomationError(
                f"Failed to start Word: {exc}"
            ) from exc

    def connect_to_word(self) -> None:
        """Connect to an already-running Word instance."""
        try:
            self._word = win32com.client.GetActiveObject(
                "Word.Application"
            )

            logger.info(
                "Connected to existing Word instance (version %s).",
                self._word.Version,
            )

        except Exception as exc:
            raise WordAutomationError(
                f"Failed to connect to running Word: {exc}"
            ) from exc

    def close_word(self) -> None:
        """Quit the Word application, closing all documents without saving."""

        if self._word is None:
            return

        try:
            # Close any remaining documents without saving.
            for doc in self._word.Documents:
                try:
                    doc.Close(SaveChanges=False)
                except Exception as doc_exc:
                    logger.warning(
                        "Error closing document during Word shutdown: %s",
                        doc_exc,
                    )

            self._word.Quit()

        except Exception as exc:
            logger.warning(
                "Error while closing Word: %s",
                exc,
            )

        finally:
            self._document = None
            self._word = None

            # Give COM/Windows time to tear down the process.
            time.sleep(0.5)

    # ══════════════════════════════════════════════════════════════════
    # DOCUMENT LIFECYCLE
    # ══════════════════════════════════════════════════════════════════

    def create_document(self) -> None:
        """Create a new blank document."""
        self._document = self.word.Documents.Add()

        logger.info(
            "New blank document created."
        )

    def open_document(self, path: str | Path) -> None:
        """Open an existing document by path."""

        p = self._validate_path(path)

        if not p.exists():
            raise WordAutomationError(
                f"File does not exist: {p}"
            )

        try:
            self._document = self.word.Documents.Open(str(p))

            logger.info(
                "Opened document: %s",
                p,
            )

        except Exception as exc:
            raise WordAutomationError(
                f"Failed to open document '{p}': {exc}"
            ) from exc

    def close_document(self, save: bool = False) -> None:
        """Close the current document."""

        if self._document is None:
            return

        try:
            self._document.Close(
                SaveChanges=save
            )

        except Exception as exc:
            logger.warning(
                "Error closing document: %s",
                exc,
            )

        finally:
            self._document = None

    def save_document(self) -> None:
        """Save the current document to its existing path."""

        self.document.Save()

        logger.info(
            "Document saved."
        )

    def save_as(self, path: str | Path) -> None:
        """Save the current document to *path*.

        Supported formats:
            .docx
            .pdf
        """

        p = self._validate_path(path)
        self._ensure_parent_dir(p)

        ext = p.suffix.lower()

        if ext == ".pdf":
            self.save_as_pdf(p)
            return

        if ext == ".docx":
            self.document.SaveAs2(
                str(p),
                FileFormat=WD_FORMAT_DOCUMENT_DEFAULT,
            )

            logger.info(
                "Document saved as: %s",
                p,
            )
            return

        raise WordAutomationError(
            f"Unsupported file extension '{ext}'. "
            "Only .docx and .pdf are accepted."
        )

    def save_as_docx(self, path: str | Path) -> None:
        """Save the current document as .docx."""

        p = self._validate_path(path)
        self._ensure_parent_dir(p)

        self.document.SaveAs2(
            str(p),
            FileFormat=WD_FORMAT_DOCUMENT_DEFAULT,
        )

        logger.info(
            "Document saved as DOCX: %s",
            p,
        )

    def save_as_pdf(self, path: str | Path) -> None:
        """Export the current document as PDF."""

        p = self._validate_path(path)
        self._ensure_parent_dir(p)

        self.document.ExportAsFixedFormat(
            OutputFileName=str(p),
            ExportFormat=WD_FORMAT_PDF,
        )

        logger.info(
            "Document exported as PDF: %s",
            p,
        )

    # ══════════════════════════════════════════════════════════════════
    # CONTENT
    # ══════════════════════════════════════════════════════════════════

    def type_text(self, text: str) -> None:
        """Type text at the current selection/cursor."""

        self.selection.TypeText(text)

    def add_text_at_cursor(self, text: str) -> None:
        """Insert text at the current cursor position."""

        self.type_text(text)

    def read_document(self) -> str:
        """Return the full text content of the active document."""

        text: str = self.document.Content.Text

        return text

    def clear_document(self) -> None:
        """Delete all content from the active document."""

        self.document.Content.Delete()

    def select_all(self) -> None:
        """Select the entire document content."""

        self.word.Selection.WholeStory()

    def copy(self) -> None:
        """Copy the current selection to the clipboard."""

        self.selection.Copy()

    def cut(self) -> None:
        """Cut the current selection to the clipboard."""

        self.selection.Cut()

    def paste(self) -> None:
        """Paste clipboard content at the cursor."""

        self.selection.Paste()

    def replace_content(self, text: str) -> None:
        """Replace the entire document content with *text*."""

        self.document.Content.Text = text

    # ══════════════════════════════════════════════════════════════════
    # FORMATTING
    # ══════════════════════════════════════════════════════════════════

    def set_bold(self, enabled: bool = True) -> None:
        self.selection.Font.Bold = enabled

    def set_italic(self, enabled: bool = True) -> None:
        self.selection.Font.Italic = enabled

    def set_underline(self, enabled: bool = True) -> None:
        self.selection.Font.Underline = (
            1 if enabled else 0
        )

    def set_strikethrough(self, enabled: bool = True) -> None:
        self.selection.Font.StrikeThrough = enabled

    def set_font(self, name: str) -> None:
        self.selection.Font.Name = name

    def set_font_size(self, size: float) -> None:
        self.selection.Font.Size = size

    def set_text_color(
        self,
        r: int,
        g: int,
        b: int,
    ) -> None:
        """Set text colour using RGB values (0-255)."""

        # Word uses BGR colour encoding:
        # R + G*256 + B*65536
        self.selection.Font.Color = (
            r + (g * 256) + (b * 65536)
        )

    def set_highlight(self, color_index: int = 7) -> None:
        """Set highlight colour."""

        self.selection.Range.HighlightColorIndex = color_index

    def align_left(self) -> None:
        self.selection.ParagraphFormat.Alignment = (
            WD_ALIGN_LEFT
        )

    def align_center(self) -> None:
        self.selection.ParagraphFormat.Alignment = (
            WD_ALIGN_CENTER
        )

    def align_right(self) -> None:
        self.selection.ParagraphFormat.Alignment = (
            WD_ALIGN_RIGHT
        )

    def justify(self) -> None:
        self.selection.ParagraphFormat.Alignment = (
            WD_ALIGN_JUSTIFY
        )

    # ══════════════════════════════════════════════════════════════════
    # PARAGRAPH
    # ══════════════════════════════════════════════════════════════════

    def set_line_spacing(self, value: float = 1.0) -> None:
        """Set line spacing as a multiple."""

        pf = self.selection.ParagraphFormat

        pf.LineSpacingRule = WD_LINE_SPACE_MULTIPLE
        pf.LineSpacing = value * 12

    def set_paragraph_spacing(
        self,
        before: float | None = None,
        after: float | None = None,
    ) -> None:
        """Set paragraph spacing in points."""

        pf = self.selection.ParagraphFormat

        if before is not None:
            pf.SpaceBefore = before

        if after is not None:
            pf.SpaceAfter = after

    def set_indentation(
        self,
        left: float | None = None,
        right: float | None = None,
        first_line: float | None = None,
    ) -> None:
        """Set indentation in points."""

        pf = self.selection.ParagraphFormat

        if left is not None:
            pf.LeftIndent = left

        if right is not None:
            pf.RightIndent = right

        if first_line is not None:
            pf.FirstLineIndent = first_line

    def apply_bullets(self) -> None:
        """Apply bullet list formatting to current selection."""

        template = self.word.ListGalleries(
            1
        ).ListTemplates(1)

        self.selection.Range.ListFormat.ApplyListTemplateWithLevel(
            template,
            ContinuePreviousList=False,
            ApplyTo=0,
            DefaultListBehavior=1,
        )

    def apply_numbering(self) -> None:
        """Apply numbered list formatting to current selection."""

        template = self.word.ListGalleries(
            2
        ).ListTemplates(1)

        self.selection.Range.ListFormat.ApplyListTemplateWithLevel(
            template,
            ContinuePreviousList=False,
            ApplyTo=0,
            DefaultListBehavior=1,
        )

    # ══════════════════════════════════════════════════════════════════
    # STYLES
    # ══════════════════════════════════════════════════════════════════

    def apply_title(self) -> None:
        self.selection.Style = self.document.Styles(
            "Title"
        )

    def apply_heading1(self) -> None:
        self.selection.Style = self.document.Styles(
            "Heading 1"
        )

    def apply_normal(self) -> None:
        self.selection.Style = self.document.Styles(
            "Normal"
        )

    def change_style(self, style_name: str) -> None:
        """Apply an arbitrary built-in or custom style."""

        self.selection.Style = self.document.Styles(
            style_name
        )

    # ══════════════════════════════════════════════════════════════════
    # TABLES
    # ══════════════════════════════════════════════════════════════════

    def create_table(
        self,
        rows: int,
        columns: int,
    ) -> Any:
        """Insert a table at the current cursor position."""

        if rows < 1 or columns < 1:
            raise WordAutomationError(
                "Table must have at least 1 row and 1 column."
            )

        rng = self.selection.Range

        table = self.document.Tables.Add(
            rng,
            rows,
            columns,
        )

        logger.info(
            "Table created: %d rows × %d columns.",
            rows,
            columns,
        )

        return table

    def read_table_data(
        self,
        table_index: int = 1,
    ) -> list[list[str]]:
        """Read cell text from a table.

        table_index is 1-based.
        """

        tables = self.document.Tables

        if table_index < 1:
            raise WordAutomationError(
                "Table index must be at least 1."
            )

        if tables.Count < table_index:
            raise WordAutomationError(
                f"Document has {tables.Count} table(s); "
                f"requested index {table_index}."
            )

        table = tables.Item(table_index)

        data: list[list[str]] = []

        for r in range(
            1,
            table.Rows.Count + 1,
        ):
            row_data: list[str] = []

            for c in range(
                1,
                table.Columns.Count + 1,
            ):
                cell_text = table.Cell(
                    r,
                    c,
                ).Range.Text

                # Word table cells normally end with \r\x07.
                row_data.append(
                    cell_text.rstrip(
                        "\r\x07"
                    ).strip()
                )

            data.append(row_data)

        return data

    # ══════════════════════════════════════════════════════════════════
    # FIND / REPLACE
    # ══════════════════════════════════════════════════════════════════

    def find_text(self, text: str) -> bool:
        """Find the first occurrence of *text*."""

        if not text:
            raise WordAutomationError(
                "Find text cannot be empty."
            )

        find = self.selection.Find

        find.ClearFormatting()
        find.Text = text
        find.Forward = True
        find.Wrap = WD_FIND_CONTINUE

        return bool(find.Execute())

    def replace_text(
        self,
        find_text: str,
        replace_with: str,
        replace_all: bool = True,
    ) -> int:
        """Find and replace text in the active document.

        This implementation performs replacement by directly modifying
        the matched Word Range instead of relying on Word's COM
        Replace argument.

        Parameters
        ----------
        find_text:
            Text to search for.

        replace_with:
            Text that should replace the matched text.

        replace_all:
            True  -> replace every occurrence.
            False -> replace only the first occurrence.

        Returns
        -------
        int
            Number of replacements performed.
        """

        if not find_text:
            raise WordAutomationError(
                "Find text cannot be empty."
            )

        if replace_with is None:
            raise WordAutomationError(
                "Replacement text cannot be None."
            )

        try:
            document = self.document

            # Create an independent Range covering the document.
            search_range = document.Content.Duplicate

            replacements = 0

            while True:
                find = search_range.Find

                # Reset previous Find settings.
                find.ClearFormatting()
                find.Replacement.ClearFormatting()

                find.Text = find_text
                find.Forward = True
                find.Wrap = 0  # wdFindStop
                find.Format = False
                find.MatchCase = False
                find.MatchWholeWord = False
                find.MatchWildcards = False

                found = bool(find.Execute())

                if not found:
                    break

                # Word's search range now represents the matched text.
                match_start = search_range.Start
                match_end = search_range.End

                logger.debug(
                    "Found text '%s' at range %d-%d.",
                    find_text,
                    match_start,
                    match_end,
                )

                # Directly replace the matched range.
                search_range.Text = replace_with

                replacements += 1

                logger.debug(
                    "Replacement %d completed: '%s' -> '%s'.",
                    replacements,
                    find_text,
                    replace_with,
                )

                # If only one replacement was requested, stop.
                if not replace_all:
                    break

                # Continue searching after the newly inserted text.
                next_position = match_start + len(replace_with)

                # Protect against invalid range positions.
                if next_position >= document.Content.End:
                    break

                search_range.SetRange(
                    Start=next_position,
                    End=document.Content.End,
                )

            logger.info(
                "Word find/replace completed: "
                "'%s' -> '%s' | replace_all=%s | replacements=%d",
                find_text,
                replace_with,
                replace_all,
                replacements,
            )

            return replacements

        except WordAutomationError:
            raise

        except Exception as exc:
            raise WordAutomationError(
                f"Failed to replace text "
                f"'{find_text}': {exc}"
            ) from exc

    # ══════════════════════════════════════════════════════════════════
    # INSERT
    # ══════════════════════════════════════════════════════════════════

    def insert_image(
        self,
        path: str | Path,
    ) -> None:
        """Insert an image at the current cursor position."""

        p = self._validate_path(path)

        if not p.exists():
            raise WordAutomationError(
                f"Image file does not exist: {p}"
            )

        self.selection.InlineShapes.AddPicture(
            str(p)
        )

        logger.info(
            "Image inserted: %s",
            p,
        )

    def insert_hyperlink(
        self,
        url: str,
        display_text: str | None = None,
    ) -> None:
        """Insert a hyperlink at the current selection."""

        text = display_text or url

        self.document.Hyperlinks.Add(
            Anchor=self.selection.Range,
            Address=url,
            TextToDisplay=text,
        )

        logger.info(
            "Hyperlink inserted: %s",
            url,
        )

    # ══════════════════════════════════════════════════════════════════
    # DOCUMENT STRUCTURE
    # ══════════════════════════════════════════════════════════════════

    def insert_page_break(self) -> None:
        """Insert a page break at the cursor."""

        self.selection.InsertBreak(
            Type=7
        )  # wdPageBreak = 7

    def set_header(
        self,
        text: str,
        section_index: int = 1,
    ) -> None:
        """Set the primary header text."""

        section = self.document.Sections(
            section_index
        )

        header = section.Headers(
            WD_HEADER_FOOTER_PRIMARY
        )

        header.Range.Text = text

        logger.info(
            "Header set for section %d.",
            section_index,
        )

    def set_footer(
        self,
        text: str,
        section_index: int = 1,
    ) -> None:
        """Set the primary footer text."""

        section = self.document.Sections(
            section_index
        )

        footer = section.Footers(
            WD_HEADER_FOOTER_PRIMARY
        )

        footer.Range.Text = text

        logger.info(
            "Footer set for section %d.",
            section_index,
        )

    def add_page_number(
        self,
        alignment: int = WD_ALIGN_PAGE_NUMBER_CENTER,
    ) -> None:
        """Add page numbers to the footer."""

        section = self.document.Sections(1)

        footer = section.Footers(
            WD_HEADER_FOOTER_PRIMARY
        )

        footer.PageNumbers.Add(
            PageNumberAlignment=alignment
        )

        logger.info(
            "Page numbers added."
        )

    def set_margins(
        self,
        top: float | None = None,
        bottom: float | None = None,
        left: float | None = None,
        right: float | None = None,
    ) -> None:
        """Set page margins in points.

        72 points = 1 inch.
        """

        ps = self.document.PageSetup

        if top is not None:
            ps.TopMargin = top

        if bottom is not None:
            ps.BottomMargin = bottom

        if left is not None:
            ps.LeftMargin = left

        if right is not None:
            ps.RightMargin = right

        logger.info(
            "Margins updated."
        )

    # ══════════════════════════════════════════════════════════════════
    # CONTEXT MANAGER
    # ══════════════════════════════════════════════════════════════════

    def __enter__(self) -> "WordAutomation":
        self.start_word()
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
    ) -> None:
        try:
            self.close_document()
        except Exception:
            pass

        self.close_word()