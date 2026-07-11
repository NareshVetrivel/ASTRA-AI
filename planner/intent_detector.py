"""
Intent Detection Module

This module identifies the user's intent
from the recognized speech text using
keyword and fuzzy matching.
"""

from rapidfuzz import process, fuzz


class IntentDetector:
    """
    Detects user intent based on keywords
    and fuzzy matching.
    """

    def __init__(self):

        self.intent_keywords = {

            # Launch Application
            "open": "launch_application",
            "start": "launch_application",
            "run": "launch_application",
            "launch": "launch_application",

            # Close Application
            "close": "close_application",
            "exit": "close_application",
            "stop": "close_application",
            "quit": "close_application",

            # Type Text
            "type": "type_text",
            "write": "type_text",

            # Clipboard Commands
            "copy": "copy",
            "paste": "paste",
            "cut": "cut",
            "undo": "undo",
            "redo": "redo"
        }

    def detect_intent(self, text):
        """
        Detect the user's intent.

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

        # -----------------------------
        # Exact Keyword Match
        # -----------------------------
        words = text.split()

        for word in words:

            if word in self.intent_keywords:

                return self.intent_keywords[word]

        # -----------------------------
        # Fuzzy Matching
        # -----------------------------
        best_match = process.extractOne(
            text,
            self.intent_keywords.keys(),
            scorer=fuzz.partial_ratio
        )

        if best_match:

            keyword, score, _ = best_match

            print(f"Intent Fuzzy Match : {keyword} ({score:.1f}%)")

            if score >= 75:

                return self.intent_keywords[keyword]

        # -----------------------------
        # No Intent Found
        # -----------------------------
        return None