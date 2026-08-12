"""
ASTRA-AI Command Normalizer

Normalizes speech-recognized commands before they reach
the intent detection and entity extraction layers.

Responsibilities
----------------
- Clean Whisper speech-recognition output.
- Normalize whitespace and punctuation.
- Correct common speech-to-text mistakes.
- Correct common application-name pronunciations.
- Correct common website-name pronunciations.
- Correct common command-word variations.
- Support common Tanglish command phrases.
- Preserve user-provided entities as much as possible.
- Avoid dangerous global replacements.

ASTRA-AI V1
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


class CommandNormalizer:
    """
    Normalize natural-language commands produced by
    Whisper / speech-recognition systems.

    The normalizer is intentionally local-first.

    It does NOT call Gemini for every command.

    Example
    -------
    Input:
        "sesearch sona college"

    Output:
        "search sona college"
    """

    # =========================================================
    # Common Whisper / STT command corrections
    # =========================================================

    COMMAND_CORRECTIONS: Dict[str, str] = {

        # Search
        "sesearch": "search",
        "seach": "search",
        "serach": "search",
        "serch": "search",
        "herch": "search",
        "arch": "search",
        "searchh": "search",
        "searches": "search",
        "searching": "search",

        # Open
        "openn": "open",
        "oppen": "open",
        "ope": "open",

        # Close
        "clsoe": "close",
        "clos": "close",
        "closs": "close",
        "closee": "close",

        # Play
        "plaay": "play",
        "playy": "play",
        "pley": "play",
        "plai": "play",

        # Click
        "clik": "click",
        "clic": "click",
        "clickk": "click",

        # Launch
        "lauch": "launch",
        "lanuch": "launch",
        "launh": "launch",
        "launchh": "launch",

        # Create
        "creat": "create",
        "creatе": "create",
        "createe": "create",

        # Delete
        "delet": "delete",
        "delte": "delete",
        "deletee": "delete",

        # Rename
        "renam": "rename",
        "renmae": "rename",
        "renamee": "rename",

        # Move
        "mve": "move",
        "mov": "move",
        "movee": "move",

        # Copy
        "cop": "copy",
        "coppy": "copy",
        "copyy": "copy",

        # Open / type
        "typ": "type",
        "typee": "type",
        "writ": "write",
        "writee": "write",
    }

    # =========================================================
    # Application name corrections
    # =========================================================

    APPLICATION_CORRECTIONS: Dict[str, str] = {

        # Chrome
        "kurom": "chrome",
        "krom": "chrome",
        "krome": "chrome",
        "kroom": "chrome",
        "kuroam": "chrome",
        "chromeu": "chrome",
        "chrom": "chrome",

        # Edge
        "edg": "edge",
        "edgee": "edge",

        # Firefox
        "fire fox": "firefox",
        "firefoks": "firefox",
        "fire fox browser": "firefox",

        # Notepad
        "note pad": "notepad",
        "not pad": "notepad",
        "notepadd": "notepad",

        # Calculator
        "calculater": "calculator",
        "calculatorr": "calculator",

        # File Explorer
        "file explorer": "file explorer",
        "fileexplorer": "file explorer",

        # WhatsApp
        "what's app": "whatsapp",
        "what app": "whatsapp",
        "whatapp": "whatsapp",
        "whats app": "whatsapp",
        "whatsappu": "whatsapp",

        # Gmail
        "g mail": "gmail",
        "gmailu": "gmail",
        "gemail": "gmail",

        # VS Code
        "vs codee": "vs code",
        "visual studio code": "vs code",
    }

    # =========================================================
    # Website corrections
    # =========================================================

    WEBSITE_CORRECTIONS: Dict[str, str] = {

        # YouTube
        "you tube": "youtube",
        "you-tube": "youtube",
        "youtubeu": "youtube",
        "you toob": "youtube",
        "you toub": "youtube",

        # Google
        "googel": "google",
        "gogle": "google",
        "googlee": "google",
        "googal": "google",

        # Gmail
        "g mail": "gmail",

        # GitHub
        "git hub": "github",
        "githhub": "github",

        # Instagram
        "insta gram": "instagram",
        "insta-gram": "instagram",

        # Facebook
        "face book": "facebook",
        "face-book": "facebook",

        # LinkedIn
        "linked in": "linkedin",
        "linkdin": "linkedin",
    }

    # =========================================================
    # Tanglish command phrase corrections
    # =========================================================

    TANGLISH_PHRASES: List[Tuple[str, str]] = [

        # -----------------------------------------------------
        # Search
        # -----------------------------------------------------

        ("search pannu", "search"),
        ("search pannunga", "search"),
        ("search pan", "search"),
        ("search pann", "search"),

        ("thedu", "search"),
        ("theda", "search"),
        ("thedu da", "search"),
        ("thedi", "search"),

        # -----------------------------------------------------
        # Open
        # -----------------------------------------------------

        ("thorakka", "open"),
        ("thoraku", "open"),
        ("thirakka", "open"),
        ("thiraku", "open"),
        ("open pannu", "open"),
        ("open pannunga", "open"),

        # -----------------------------------------------------
        # Close
        # -----------------------------------------------------

        ("moodu", "close"),
        ("moodu da", "close"),
        ("close pannu", "close"),
        ("close pannunga", "close"),

        # -----------------------------------------------------
        # Play
        # -----------------------------------------------------

        ("play pannu", "play"),
        ("play pannunga", "play"),
        ("podu", "play"),
        ("pottu", "play"),

        # -----------------------------------------------------
        # Click
        # -----------------------------------------------------

        ("click pannu", "click"),
        ("click pannunga", "click"),
        ("clicku", "click"),

        # -----------------------------------------------------
        # Launch
        # -----------------------------------------------------

        ("launch pannu", "launch"),
        ("launch pannunga", "launch"),

        # -----------------------------------------------------
        # Create
        # -----------------------------------------------------

        ("create pannu", "create"),
        ("create pannunga", "create"),
        ("uruvakku", "create"),

        # -----------------------------------------------------
        # Delete
        # -----------------------------------------------------

        ("delete pannu", "delete"),
        ("delete pannunga", "delete"),
        ("azhichidu", "delete"),
        ("azhichu", "delete"),

        # -----------------------------------------------------
        # Rename
        # -----------------------------------------------------

        ("rename pannu", "rename"),
        ("rename pannunga", "rename"),

        # -----------------------------------------------------
        # Move
        # -----------------------------------------------------

        ("move pannu", "move"),
        ("move pannunga", "move"),
        ("maathu", "move"),
        ("maathi", "move"),

        # -----------------------------------------------------
        # Copy
        # -----------------------------------------------------

        ("copy pannu", "copy"),
        ("copy pannunga", "copy"),
        ("nakal edu", "copy"),

        # -----------------------------------------------------
        # Type / Write
        # -----------------------------------------------------

        ("type pannu", "type"),
        ("type pannunga", "type"),
        ("write pannu", "write"),
        ("write pannunga", "write"),

        # -----------------------------------------------------
        # Enter
        # -----------------------------------------------------

        ("enter pannu", "enter"),
        ("enter pannunga", "enter"),

        # -----------------------------------------------------
        # Press
        # -----------------------------------------------------

        ("press pannu", "press"),
        ("press pannunga", "press"),

        # -----------------------------------------------------
        # First / second / third result
        # -----------------------------------------------------

        ("mudhal result", "first result"),
        ("first resultu", "first result"),

        ("rendu result", "second result"),
        ("second resultu", "second result"),

        ("moonu result", "third result"),
        ("third resultu", "third result"),
    ]

    # =========================================================
    # Phrase-level STT corrections
    # =========================================================

    PHRASE_CORRECTIONS: List[Tuple[str, str]] = [

        # Search phrases
        (
            "search google for",
            "search google for",
        ),

        (
            "search google",
            "search google",
        ),

        # YouTube
        (
            "youtube la",
            "youtube",
        ),

        (
            "youtube il",
            "youtube",
        ),

        (
            "youtube ku",
            "youtube",
        ),

        # Common spoken filler
        (
            "can you please",
            "",
        ),

        (
            "could you please",
            "",
        ),

        (
            "please",
            "",
        ),

        (
            "hey astra",
            "",
        ),

        (
            "okay astra",
            "",
        ),

        (
            "ok astra",
            "",
        ),
    ]

    # =========================================================
    # Words that should NEVER be blindly replaced
    # =========================================================

    PROTECTED_WORDS = {
        "study",
        "today",
        "tomorrow",
        "yesterday",
        "college",
        "school",
        "python",
        "java",
        "javascript",
        "email",
        "mail",
        "song",
        "music",
        "file",
        "folder",
        "document",
    }

    # =========================================================
    # Constructor
    # =========================================================

    def __init__(self) -> None:
        """
        Initialize the command normalizer.
        """

        # Keep corrections sorted by length so longer
        # phrases are processed before shorter phrases.

        self._command_corrections = (
            self._sort_mapping(
                self.COMMAND_CORRECTIONS
            )
        )

        self._application_corrections = (
            self._sort_mapping(
                self.APPLICATION_CORRECTIONS
            )
        )

        self._website_corrections = (
            self._sort_mapping(
                self.WEBSITE_CORRECTIONS
            )
        )

        self._tanglish_phrases = (
            self._sort_pairs(
                self.TANGLISH_PHRASES
            )
        )

        self._phrase_corrections = (
            self._sort_pairs(
                self.PHRASE_CORRECTIONS
            )
        )

    # =========================================================
    # Public API
    # =========================================================

    def normalize(
        self,
        command: str,
    ) -> str:
        """
        Normalize a speech-recognized command.

        Parameters
        ----------
        command:
            Raw command produced by Whisper or another
            speech-recognition system.

        Returns
        -------
        str
            Normalized command.

        Example
        -------
        >>> normalizer.normalize(
        ...     "sesearch Sona College"
        ... )
        'search sona college'
        """

        if command is None:

            return ""

        if not isinstance(command, str):

            command = str(command)

        text = command.strip()

        if not text:

            return ""

        # -----------------------------------------------------
        # Basic text cleanup
        # -----------------------------------------------------

        text = self._clean_text(text)

        # -----------------------------------------------------
        # Remove common conversational fillers
        # -----------------------------------------------------

        text = self._apply_phrase_corrections(
            text
        )

        # -----------------------------------------------------
        # Tanglish phrase normalization
        # -----------------------------------------------------

        text = self._apply_tanglish_phrases(
            text
        )

        # -----------------------------------------------------
        # Application names
        # -----------------------------------------------------

        text = self._apply_mapping(
            text,
            self._application_corrections,
        )

        # -----------------------------------------------------
        # Website names
        # -----------------------------------------------------

        text = self._apply_mapping(
            text,
            self._website_corrections,
        )

        # -----------------------------------------------------
        # Command words
        # -----------------------------------------------------

        text = self._apply_mapping(
            text,
            self._command_corrections,
        )

        # -----------------------------------------------------
        # Final cleanup
        # -----------------------------------------------------

        text = self._clean_text(text)

        return text

    # ---------------------------------------------------------

    def normalize_with_changes(
        self,
        command: str,
    ) -> Tuple[str, List[str]]:
        """
        Normalize a command and return a list of changes.

        Useful for debugging and future UI logging.

        Returns
        -------
        tuple[str, list[str]]

        Example
        -------
        (
            "search sona college",
            [
                "sesearch -> search"
            ]
        )
        """

        original = (
            ""
            if command is None
            else str(command)
        )

        normalized = self.normalize(
            original
        )

        changes: List[str] = []

        if original.strip() != normalized:

            changes.append(
                f"{original.strip()} -> {normalized}"
            )

        return normalized, changes

    # ---------------------------------------------------------

    def is_changed(
        self,
        command: str,
    ) -> bool:
        """
        Return True when normalization changes
        the supplied command.
        """

        original = (
            ""
            if command is None
            else str(command).strip()
        )

        normalized = self.normalize(
            original
        )

        return original != normalized

    # =========================================================
    # Text cleanup
    # =========================================================

    def _clean_text(
        self,
        text: str,
    ) -> str:
        """
        Perform safe basic text cleanup.

        This method intentionally does NOT remove punctuation
        aggressively because punctuation may belong to a
        filename, search query, URL, or typed text.
        """

        text = text.strip()

        # Normalize Unicode apostrophe variants.

        text = (
            text
            .replace("’", "'")
            .replace("‘", "'")
            .replace("“", '"')
            .replace("”", '"')
        )

        # Normalize repeated whitespace.

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # =========================================================
    # Phrase corrections
    # =========================================================

    def _apply_phrase_corrections(
        self,
        text: str,
    ) -> str:
        """
        Apply safe phrase-level corrections.
        """

        result = text

        for old, new in self._phrase_corrections:

            result = self._replace_phrase(
                result,
                old,
                new,
            )

        return self._clean_text(
            result
        )

    # =========================================================
    # Tanglish corrections
    # =========================================================

    def _apply_tanglish_phrases(
        self,
        text: str,
    ) -> str:
        """
        Apply Tanglish command phrase corrections.
        """

        result = text

        for old, new in self._tanglish_phrases:

            result = self._replace_phrase(
                result,
                old,
                new,
            )

        return self._clean_text(
            result
        )

    # =========================================================
    # Mapping corrections
    # =========================================================

    def _apply_mapping(
        self,
        text: str,
        mapping: List[Tuple[str, str]],
    ) -> str:
        """
        Apply word/phrase corrections using word boundaries.

        Word boundaries prevent accidental replacements inside
        unrelated user entities.

        Example:

            "study" will NOT become "today".
        """

        result = text

        for old, new in mapping:

            # Never normalize protected words.

            if old in self.PROTECTED_WORDS:

                continue

            pattern = (
                r"(?<!\w)"
                + re.escape(old)
                + r"(?!\w)"
            )

            result = re.sub(
                pattern,
                new,
                result,
                flags=re.IGNORECASE,
            )

        return self._clean_text(
            result
        )

    # =========================================================
    # Safe phrase replacement
    # =========================================================

    def _replace_phrase(
        self,
        text: str,
        old: str,
        new: str,
    ) -> str:
        """
        Replace a complete phrase safely.

        Phrase matching is case-insensitive and does not
        replace partial words.
        """

        if not old:

            return text

        pattern = (
            r"(?<!\w)"
            + re.escape(old)
            + r"(?!\w)"
        )

        return re.sub(
            pattern,
            new,
            text,
            flags=re.IGNORECASE,
        )

    # =========================================================
    # Sorting helpers
    # =========================================================

    @staticmethod
    def _sort_mapping(
        mapping: Dict[str, str],
    ) -> List[Tuple[str, str]]:
        """
        Convert a dictionary into a list sorted by key length.

        Longer phrases are processed first.
        """

        return sorted(
            mapping.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        )

    # ---------------------------------------------------------

    @staticmethod
    def _sort_pairs(
        pairs: List[Tuple[str, str]],
    ) -> List[Tuple[str, str]]:
        """
        Sort correction pairs by source phrase length.
        """

        return sorted(
            pairs,
            key=lambda item: len(item[0]),
            reverse=True,
        )

    # =========================================================
    # Debug helpers
    # =========================================================

    def explain(
        self,
        command: str,
    ) -> Dict[str, object]:
        """
        Return useful debugging information.

        This does NOT execute the command.
        """

        normalized = self.normalize(
            command
        )

        return {
            "original": command,
            "normalized": normalized,
            "changed": (
                command.strip()
                != normalized
                if isinstance(command, str)
                else True
            ),
        }


__all__ = [
    "CommandNormalizer",
]