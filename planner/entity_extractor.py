"""
Entity Extraction Module

This module identifies entities
such as application names from
the user's command.
"""


class EntityExtractor:
    """
    Extracts entities from user commands.
    """

    def __init__(self):

        # Supported Applications
        self.applications = {

            "chrome": "chrome.exe",
            "notepad": "notepad.exe",
            "paint": "mspaint.exe",
            "calculator": "calc.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "vscode": "Code.exe",
            "spotify": "spotify.exe"
        }

    def extract_application(self, text):
        """
        Extract application entity.

        Parameters:
            text (str)

        Returns:
            str | None
        """

        if not text:
            return None

        # Normalize text
        text = text.lower()

        # Split sentence
        words = text.split()

        # Search application
        for word in words:

            if word in self.applications:

                return self.applications[word]

        return None