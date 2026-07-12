"""
Intent Detection Module

This module identifies the user's intent
from the recognized speech text using
keyword and fuzzy matching.
"""

from rapidfuzz import process, fuzz


class IntentDetector:
    """
    Detects user intent using keyword
    and fuzzy matching.
    """

    def __init__(self):

        self.intent_keywords = {

            # ---------------------------------
            # Application Commands
            # ---------------------------------
            "open": "launch_application",
            "start": "launch_application",
            "run": "launch_application",
            "launch": "launch_application",

            "close": "close_application",
            "exit": "close_application",
            "stop": "close_application",
            "quit": "close_application",

            # ---------------------------------
            # Typing Commands
            # ---------------------------------
            "type": "type_text",
            "write": "type_text",

            # ---------------------------------
            # Clipboard Commands
            # ---------------------------------
            "copy": "copy",
            "paste": "paste",
            "cut": "cut",
            "undo": "undo",
            "redo": "redo",

            # ---------------------------------
            # Keyboard Commands
            # ---------------------------------
            "enter": "press_enter",
            "tab": "press_tab",

            # ---------------------------------
            # Mouse Commands
            # ---------------------------------
            "click": "left_click",
            "left": "left_click",
            "right": "right_click",
            "double": "double_click",

            # ---------------------------------
            # Shortcut Commands
            # ---------------------------------
            "select": "select_all",
            "save": "save_file",
            "print": "print_file"
        }

    def detect_intent(self, text):
        """
        Detect user intent.

        Parameters
        ----------
        text : str

        Returns
        -------
        str | None
        """

        if not text:
            return None

        text = text.lower()

        # ---------------------------------
        # Multi-word Commands (Highest Priority)
        # ---------------------------------

        if "select all" in text:
            return "select_all"

        if "press enter" in text:
            return "press_enter"

        if "press tab" in text:
            return "press_tab"

        if "save file" in text:
            return "save_file"

        if "print file" in text:
            return "print_file"

        if "right click" in text:
            return "right_click"

        if "double click" in text:
            return "double_click"

        if "left click" in text:
            return "left_click"

        if "scroll up" in text:
            return "scroll_up"

        if "scroll down" in text:
            return "scroll_down"

        # ---------------------------------
        # Exact Match
        # ---------------------------------

        words = text.split()

        for word in words:

            if word in self.intent_keywords:

                return self.intent_keywords[word]

        # ---------------------------------
        # Fuzzy Match
        # ---------------------------------

        best_match = process.extractOne(
            text,
            self.intent_keywords.keys(),
            scorer=fuzz.partial_ratio
        )

        if best_match:

            keyword, score, _ = best_match

            print(
                f"Intent Fuzzy Match : "
                f"{keyword} ({score:.1f}%)"
            )

            if score >= 75:

                return self.intent_keywords[keyword]

        # ---------------------------------
        # No Match
        # ---------------------------------

        return None