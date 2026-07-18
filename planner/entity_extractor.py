"""
Entity Extraction Module

This module identifies application names
from the SQLite database using
RapidFuzz matching.
"""

from rapidfuzz import process, fuzz

from database.database_manager import DatabaseManager


class EntityExtractor:
    """
    Extract application names from
    user commands.
    """

    def __init__(self):

        self.database = DatabaseManager()

    def load_applications(self):
        """
        Load all applications stored
        inside SQLite.
        """

        applications = {}

        rows = self.database.get_all_applications()

        for name, exe_name, _ in rows:

            applications[name] = exe_name

        return applications

    def extract_application(self, text):
        """
        Extract application name.

        Parameters
        ----------
        text : str

        Returns
        -------
        str | None
        """

        if not text:
            return None

        text = text.lower().strip()

        applications = self.load_applications()

        if not applications:
            return None

        # -------------------------
        # Exact Match
        # -------------------------

        for app_name in applications:

            if app_name in text:

                return applications[app_name]

        # -------------------------
        # Alias Match
        # -------------------------

        words = text.split()

        for word in words:

            alias = self.database.get_alias(word)

            if alias:

                application = self.database.get_application(
                    alias[0]
                )

                if application:

                    return application[1]

        # -------------------------
        # Fuzzy Match
        # -------------------------

        best_match = process.extractOne(
            text,
            applications.keys(),
            scorer=fuzz.partial_ratio
        )

        if best_match:

            app_name, score, _ = best_match

            print(
                f"Fuzzy Match : "
                f"{app_name} ({score:.1f}%)"
            )

            if score >= 70:

                return applications[app_name]

        return None