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

            # -------------------------
            # Windows Apps
            # -------------------------

            "notepad": "notepad",
            "note pad": "notepad",
            "node pad": "notepad",
            "not to pad": "notepad",
            "note card": "notepad",

            "paint": "paint",
            "mspaint": "paint",

            "calculator": "calculator",
            "calc": "calculator",

            "command prompt": "command prompt",
            "cmd": "command prompt",

            "powershell": "powershell",

            "explorer": "file explorer",
            "file explorer": "file explorer",

            "this pc": "this pc",
            "my computer": "this pc",

            "task manager": "task manager",

            "settings": "settings",

            "control panel": "control panel",

            "registry editor": "registry editor",

            "services": "services",

            "device manager": "device manager",

            # -------------------------
            # Browsers
            # -------------------------

            "chrome": "chrome",
            "google chrome": "chrome",

            "edge": "edge",
            "microsoft edge": "edge",

            "firefox": "firefox",

            "brave": "brave",

            "opera": "opera",

            # -------------------------
            # IDEs
            # -------------------------

            "vs code": "vs code",
            "vscode": "vs code",
            "visual studio code": "vs code",

            "pycharm": "pycharm",

            "android studio": "android studio",

            # -------------------------
            # Office
            # -------------------------

            "word": "word",
            "microsoft word": "word",

            "excel": "excel",
            "microsoft excel": "excel",

            "powerpoint": "powerpoint",
            "power point": "powerpoint",

            "outlook": "outlook",

            "onenote": "onenote",

            # -------------------------
            # Others
            # -------------------------

            "spotify": "spotify"
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
        text = text.strip()

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

            if score >= 70:

                return self.applications[app_name]

        return None