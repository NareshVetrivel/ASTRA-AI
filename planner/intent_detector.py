"""
Intent Detection Module

This module identifies the user's intent
from the recognized speech text.
"""


class IntentDetector:
    """
    Detects user intent based on keywords.
    """

    def __init__(self):

        self.intent_keywords = {

            # Launch Application
            "open": "launch_application",
            "start": "launch_application",
            "run": "launch_application",

            # Close Application
            "close": "close_application",
            "exit": "close_application",
            "stop": "close_application"
        }

    def detect_intent(self, text):
        """
        Detect the user's intent.

        Parameters:
            text (str)

        Returns:
            str | None
        """

        # Empty text
        if not text:
            return None

        # Convert to lowercase
        text = text.lower()

        # Split sentence into words
        words = text.split()

        # Check every word
        for word in words:

            if word in self.intent_keywords:

                return self.intent_keywords[word]

        # No intent found
        return None