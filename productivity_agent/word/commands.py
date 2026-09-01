"""
Word V1 Operation Names / Constants

Centralized registry of all Word operation identifiers.
No COM execution logic belongs here — this module is purely declarative.
"""


# ── Application Lifecycle ─────────────────────────────────────────────
OPEN_WORD = "open_word"
CLOSE_WORD = "close_word"
CREATE_BLANK_DOCUMENT = "create_blank_document"
OPEN_EXISTING_DOCUMENT = "open_existing_document"
SAVE = "save"
SAVE_AS = "save_as"
CLOSE_CURRENT_DOCUMENT = "close_current_document"

# ── Content ───────────────────────────────────────────────────────────
TYPE_TEXT = "type_text"
ADD_TEXT_AT_CURSOR = "add_text_at_cursor"
REPLACE_CONTENT = "replace_content"
READ_DOCUMENT = "read_document"
CLEAR_DOCUMENT = "clear_document"
SELECT_ALL = "select_all"
COPY = "copy"
CUT = "cut"
PASTE = "paste"

# ── Formatting ────────────────────────────────────────────────────────
BOLD = "bold"
ITALIC = "italic"
UNDERLINE = "underline"
STRIKETHROUGH = "strikethrough"
FONT = "font"
FONT_SIZE = "font_size"
TEXT_COLOR = "text_color"
HIGHLIGHT = "highlight"
ALIGN_LEFT = "align_left"
ALIGN_CENTER = "align_center"
ALIGN_RIGHT = "align_right"
JUSTIFY = "justify"

# ── Paragraph ─────────────────────────────────────────────────────────
LINE_SPACING = "line_spacing"
PARAGRAPH_SPACING = "paragraph_spacing"
INDENTATION = "indentation"
BULLETS = "bullets"
NUMBERING = "numbering"

# ── Styles ────────────────────────────────────────────────────────────
TITLE = "title"
HEADING_1 = "heading_1"
NORMAL = "normal"
DOCUMENT_STYLE = "document_style"

# ── Tables ────────────────────────────────────────────────────────────
CREATE_TABLE = "create_table"
ROWS = "rows"
COLUMNS = "columns"
READ_TABLE_DATA = "read_table_data"

# ── Find / Replace ───────────────────────────────────────────────────
FIND = "find"
REPLACE = "replace"

# ── Insert ────────────────────────────────────────────────────────────
IMAGE = "image"
HYPERLINK = "hyperlink"

# ── Document Structure ───────────────────────────────────────────────
NEW_PAGE = "new_page"
PAGE_BREAK = "page_break"
HEADER = "header"
FOOTER = "footer"
PAGE_NUMBER = "page_number"
MARGINS = "margins"

# ── Files ─────────────────────────────────────────────────────────────
SAVE_DOCX = "save_docx"
SAVE_PDF = "save_pdf"
OPEN_DOCX = "open_docx"
CREATE_SPECIFIED_FILENAME = "create_specified_filename"
READ_EXISTING_DOCUMENT = "read_existing_document"


# ── Convenience collection ────────────────────────────────────────────

ALL_COMMANDS: list[str] = [
    # Application
    OPEN_WORD, CLOSE_WORD, CREATE_BLANK_DOCUMENT, OPEN_EXISTING_DOCUMENT,
    SAVE, SAVE_AS, CLOSE_CURRENT_DOCUMENT,
    # Content
    TYPE_TEXT, ADD_TEXT_AT_CURSOR, REPLACE_CONTENT, READ_DOCUMENT,
    CLEAR_DOCUMENT, SELECT_ALL, COPY, CUT, PASTE,
    # Formatting
    BOLD, ITALIC, UNDERLINE, STRIKETHROUGH, FONT, FONT_SIZE,
    TEXT_COLOR, HIGHLIGHT, ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT, JUSTIFY,
    # Paragraph
    LINE_SPACING, PARAGRAPH_SPACING, INDENTATION, BULLETS, NUMBERING,
    # Styles
    TITLE, HEADING_1, NORMAL, DOCUMENT_STYLE,
    # Tables
    CREATE_TABLE, ROWS, COLUMNS, READ_TABLE_DATA,
    # Find / Replace
    FIND, REPLACE,
    # Insert
    IMAGE, HYPERLINK,
    # Document Structure
    NEW_PAGE, PAGE_BREAK, HEADER, FOOTER, PAGE_NUMBER, MARGINS,
    # Files
    SAVE_DOCX, SAVE_PDF, OPEN_DOCX, CREATE_SPECIFIED_FILENAME,
    READ_EXISTING_DOCUMENT,
]
