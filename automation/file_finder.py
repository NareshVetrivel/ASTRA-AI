"""
File Finder Module

Search indexed files from
SQLite database.

ASTRA-AI V1
"""

import os
import subprocess
import time

import pyautogui

from rapidfuzz import process, fuzz

from database.database_manager import DatabaseManager


class FileFinder:
    """
    Search indexed files from
    SQLite database.
    """

    def __init__(self):

        self.database = DatabaseManager()

    # --------------------------------------------------
    # Find File
    # --------------------------------------------------

    def find_file(
        self,
        filename
    ):
        """
        Search file using multiple
        search strategies.

        Parameters
        ----------
        filename : str

        Returns
        -------
        str | None
        """

        if not filename:

            return None

        filename = filename.strip().lower()

        # Remove extension if user speaks it

        filename = filename.replace(".pdf", "")
        filename = filename.replace(".docx", "")
        filename = filename.replace(".doc", "")
        filename = filename.replace(".pptx", "")
        filename = filename.replace(".ppt", "")
        filename = filename.replace(".xlsx", "")
        filename = filename.replace(".xls", "")
        filename = filename.replace(".txt", "")

        # -----------------------------
        # Exact Search
        # -----------------------------

        path = self.search_exact(
            filename
        )

        if path:

            return path

        # -----------------------------
        # Partial Search
        # -----------------------------

        path = self.search_partial(
            filename
        )

        if path:

            return path

        # -----------------------------
        # Fuzzy Search
        # -----------------------------

        path = self.search_fuzzy(
            filename
        )

        if path:

            return path

        return None

    # --------------------------------------------------
    # Exact Search
    # --------------------------------------------------

    def search_exact(
        self,
        filename
    ):
        """
        Search exact filename.
        """

        result = self.database.get_file(
            filename
        )

        if not result:

            return None

        print(
            f"\nExact Match : {result[0]}"
        )

        return result[2]

    # --------------------------------------------------
    # Partial Search
    # --------------------------------------------------

    def search_partial(
        self,
        filename
    ):
        """
        Search partial filename.
        """

        results = self.database.search_files(
            filename
        )

        if not results:

            return None

        print(
            f"\nPartial Match : {results[0][0]}"
        )

        return results[0][2]

    # --------------------------------------------------
    # Fuzzy Search
    # --------------------------------------------------

    def search_fuzzy(
        self,
        filename
    ):
        """
        Search filename using
        RapidFuzz.
        """

        files = self.database.get_all_files()

        if not files:

            return None

        file_names = [

            file[0].lower()

            for file in files

        ]

        match = process.extractOne(

            filename,

            file_names,

            scorer=fuzz.WRatio

        )

        if not match:

            return None

        matched_name, score, _ = match

        print(
            f"\nFuzzy Match : "
            f"{matched_name} ({score:.1f}%)"
        )

        # Prevent wrong file selection

        if score < 85:

            return None

        for file in files:

            if file[0].lower() == matched_name:

                return file[2]

        return None

    # --------------------------------------------------
    # Search By Extension
    # --------------------------------------------------

    def search_by_extension(
        self,
        extension
    ):
        """
        Search using Windows File Explorer.
        """

        try:

            print(
                f"\nOpening Explorer Search : *.{extension}"
            )

            subprocess.Popen("explorer")

            time.sleep(2.5)

            # Wake Explorer window

            pyautogui.press("alt")

            time.sleep(0.2)

            # Focus search box

            pyautogui.hotkey(
                "ctrl",
                "e"
            )

            time.sleep(0.8)

            # Click once to ensure focus

            pyautogui.click()

            time.sleep(0.2)

            pyautogui.write(
                f"*.{extension}",
                interval=0.02
            )

            time.sleep(0.3)

            pyautogui.press("enter")

            return True

        except Exception as error:

            print(
                f"\nExplorer Search Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Open File
    # --------------------------------------------------

    def open_file(
        self,
        filename
    ):
        """
        Search and open a file.
        """

        path = self.find_file(
            filename
        )

        if not path:

            print(
                "\nFile not found."
            )

            return False

        if not os.path.exists(path):

            print(
                "\nFile does not exist."
            )

            return False

        try:

            print(
                f"\nOpening File :\n{path}"
            )

            os.startfile(path)

            return True

        except Exception as error:

            print(
                f"\nOpen File Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Search By Size
    # --------------------------------------------------

    def search_by_size(
        self,
        minimum_size_mb
    ):
        """
        Search files larger than
        the given size.
        """

        results = self.database.search_by_size(
            minimum_size_mb
        )

        if not results:

            print(
                "\nNo matching files found."
            )

            return False

        print("\nMatching Files:\n")

        for file in results:

            print(file[2])

        return True

    # --------------------------------------------------
    # Search By Date
    # --------------------------------------------------

    def search_by_date(
        self,
        days
    ):
        """
        Search recently modified files
        using File Explorer.
        """

        try:

            if days == 0:

                query = "datemodified:today"

            elif days == 1:

                query = "datemodified:yesterday"

            elif days <= 7:

                query = "datemodified:this week"

            elif days <= 31:

                query = "datemodified:this month"

            else:

                query = "datemodified:this year"

            print(
                f"\nExplorer Search : {query}"
            )

            subprocess.Popen("explorer")

            time.sleep(2.5)

            pyautogui.press("alt")

            time.sleep(0.2)

            pyautogui.hotkey(
                "ctrl",
                "e"
            )

            time.sleep(0.8)

            pyautogui.click()

            time.sleep(0.2)

            pyautogui.write(
                query,
                interval=0.02
            )

            time.sleep(0.3)

            pyautogui.press("enter")

            return True

        except Exception as error:

            print(
                f"\nExplorer Search Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close(self):
        """
        Close database connection.
        """

        self.database.close()