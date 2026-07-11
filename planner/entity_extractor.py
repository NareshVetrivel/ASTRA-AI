"""
Entity Extraction Module

This module identifies application names
from the user's voice command using
fuzzy matching.
"""

from rapidfuzz import process, fuzz


class EntityExtractor:
    """
    Extracts application entities from
    user commands.
    """

    def __init__(self):

        # Supported Applications
        self.applications = {

            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",

            "notepad": "notepad.exe",
            "note pad": "notepad.exe",
            "node pad": "notepad.exe",
            "not to pad": "notepad.exe",
            "note card": "notepad.exe",

            "paint": "mspaint.exe",

            "calculator": "calc.exe",
            "calc": "calc.exe",

            "word": "winword.exe",
            "microsoft word": "winword.exe",

            "excel": "excel.exe",
            "microsoft excel": "excel.exe",

            "powerpoint": "powerpnt.exe",
            "power point": "powerpnt.exe",

            "vscode": "Code.exe",
            "vs code": "Code.exe",
            "visual studio code": "Code.exe",

            "spotify": "spotify.exe"
        }

    def extract_application(self, text):
        """
        Extract application name from text.

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

        # Exact phrase match
        for app in self.applications:

            if app in text:

                return self.applications[app]

        # Fuzzy Matching
        best_match = process.extractOne(
            text,
            self.applications.keys(),
            scorer=fuzz.partial_ratio
        )

        if best_match:

            app_name, score, _ = best_match

            print(f"Fuzzy Match : {app_name} ({score}%)")

            if score >= 75:

                return self.applications[app_name]

        return None