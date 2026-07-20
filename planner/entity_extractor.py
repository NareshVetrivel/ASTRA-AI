"""
Entity Extraction Module

This module identifies application names
from the SQLite database using
RapidFuzz matching.

It also extracts file search queries
for File Finder.

ASTRA-AI V1
"""

from rapidfuzz import process, fuzz

from database.database_manager import DatabaseManager


class EntityExtractor:
    """
    Extract application names
    and file names.
    """

    def __init__(self):

        self.database = DatabaseManager()

        # ---------------------------------
        # Special Folders
        # ---------------------------------

        self.special_folders = {

            "desktop",

            "documents",

            "downloads",

            "pictures",

            "videos",

            "music",

            "this pc",

            "my computer",

            "computer",

            "recycle bin",

            "trash",

            "c drive",

            "d drive",

            "e drive"

        }

        # ---------------------------------
        # Common Websites
        # ---------------------------------

        self.websites = {

            "google": "google.com",

            "youtube": "youtube.com",

            "gmail": "gmail.com",

            "github": "github.com",

            "stackoverflow": "stackoverflow.com",

            "chatgpt": "chat.openai.com",

            "wikipedia": "wikipedia.org",

            "amazon": "amazon.in",

            "flipkart": "flipkart.com",

            "linkedin": "linkedin.com",

            "instagram": "instagram.com",

            "facebook": "facebook.com",

            "twitter": "x.com"

        }

        # ---------------------------------
        # Chrome Profiles
        # ---------------------------------

        self.chrome_profiles = {

            "naresh": "Default",

            "naresh s": "Default",

            "naresh senthil": "Profile 1",

            "college": "Profile 1",

            "ragxii": "Profile 12"

        }

    # --------------------------------------------------
    # Load Applications
    # --------------------------------------------------

    def load_applications(self):
        """
        Load all stored applications.
        """

        applications = {}

        rows = self.database.get_all_applications()

        for name, exe_name, _ in rows:

            applications[name] = exe_name

        return applications

    # --------------------------------------------------
    # Extract Application
    # --------------------------------------------------

    def extract_application(
        self,
        text
    ):
        """
        Extract application name.
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

            alias = self.database.get_alias(
                word
            )

            if alias:

                application = (
                    self.database.get_application(
                        alias[0]
                    )
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

    # --------------------------------------------------
    # Extract Folder
    # --------------------------------------------------

    def extract_folder(
        self,
        text
    ):
        """
        Extract folder name from
        voice command.
        """

        if not text:

            return None

        text = text.lower().strip()

        # -------------------------
        # Exact Match
        # -------------------------

        for folder in self.special_folders:

            if folder in text:

                return folder

        # -------------------------
        # Fuzzy Match
        # -------------------------

        best_match = process.extractOne(

            text,

            self.special_folders,

            scorer=fuzz.partial_ratio

        )

        if best_match:

            folder, score, _ = best_match

            print(

                f"Folder Match : "

                f"{folder} ({score:.1f}%)"

            )

            if score >= 75:

                return folder

        return None

    # --------------------------------------------------
    # Extract Website
    # --------------------------------------------------

    def extract_website(
        self,
        text
    ):
        """
        Extract website from command.
        """

        if not text:

            return None

        text = text.lower().strip()

        # Exact Match

        for name, url in self.websites.items():

            if name in text:

                return url

        # URL Detection

        words = text.split()

        for word in words:

            if "." in word:

                return word

        # Fuzzy Match

        best_match = process.extractOne(

            text,

            self.websites.keys(),

            scorer=fuzz.partial_ratio

        )

        if best_match:

            name, score, _ = best_match

            print(

                f"Website Match : {name} ({score:.1f}%)"

            )

            if score >= 80:

                return self.websites[name]

        return None

    # --------------------------------------------------
    # Extract Google Search Query
    # --------------------------------------------------

    def extract_search_query(
        self,
        text
    ):
        """
        Extract Google search query.
        """

        if not text:

            return None

        text = text.lower()

        remove_words = {

            "search",

            "google",

            "for",

            "on",

            "please"

        }

        words = [

            word

            for word in text.split()

            if word not in remove_words

        ]

        query = " ".join(words).strip()

        return query if query else None

    # --------------------------------------------------
    # Extract Browser
    # --------------------------------------------------

    def extract_browser(
        self,
        text
    ):
        """
        Detect browser name.
        """

        if not text:

            return "chrome"

        text = text.lower()

        if "edge" in text:

            return "edge"

        if "chrome" in text:

            return "chrome"

        return "chrome"

    # --------------------------------------------------
    # Extract Chrome Profile
    # --------------------------------------------------

    def extract_profile(
        self,
        text
    ):
        """
        Detect Chrome profile name.
        """

        if not text:

            return None

        text = text.lower()

        # Exact Match

        for profile in self.chrome_profiles:

            if profile in text:

                return profile

        # Fuzzy Match

        best_match = process.extractOne(

            text,

            self.chrome_profiles.keys(),

            scorer=fuzz.partial_ratio

        )

        if best_match:

            profile, score, _ = best_match

            print(

                f"Profile Match : {profile} ({score:.1f}%)"

            )

            if score >= 80:

                return profile

        return None

    # --------------------------------------------------
    # Extract File Query
    # --------------------------------------------------

    def extract_file_query(
        self,
        text
    ):
        """
        Extract filename from
        voice command.
        """

        if not text:

            return None

        text = text.lower().strip()

        remove_words = {

            "open",

            "file",

            "document",

            "folder",

            "create",

            "rename",

            "delete",

            "move",

            "copy",

            "please",

            "my",

            "the",

            "named",

            "called",

            "to",

            "into",

            "in"

        }

        words = [

            word

            for word in text.split()

            if word not in remove_words

        ]

        query = " ".join(words).strip()

        if not query:

            return None

        return query

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close(self):
        """
        Close database connection.
        """

        self.database.close()