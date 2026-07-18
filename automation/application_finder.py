"""
Application Finder Module

This module locates installed Windows
applications and returns the executable
path for launching.
"""

import os
import shutil

from database.database_manager import DatabaseManager

class ApplicationFinder:
    """
    Find installed application executable paths.
    """

    def __init__(self):

        self.database = DatabaseManager()

        self.aliases = {

            # Browsers
            "chrome": "chrome",
            "chrome.exe": "chrome",

            "edge": "edge",
            "msedge": "edge",
            "msedge.exe": "edge",

            "firefox": "firefox",
            "firefox.exe": "firefox",

            "brave": "brave",
            "brave.exe": "brave",

            "opera": "opera",
            "opera.exe": "opera",

            # VS Code
            "code": "vscode",
            "code.exe": "vscode",
            "vscode": "vscode",

            # Office
            "winword": "word",
            "winword.exe": "word",
            "word": "word",

            "excel": "excel",
            "excel.exe": "excel",

            "powerpoint": "powerpoint",
            "powerpnt": "powerpoint",
            "powerpnt.exe": "powerpoint",

            "outlook": "outlook",
            "outlook.exe": "outlook"
        }

        self.known_paths = {

            "chrome": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ],

            "edge": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ],

            "firefox": [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
            ],

            "brave": [
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            ],

            "opera": [
                r"C:\Users\{}\AppData\Local\Programs\Opera\opera.exe".format(
                    os.getlogin()
                ),
            ],

            "vscode": [
                r"C:\\Users\\{}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe".format(
                    os.getlogin()
                ),
            ],

            "pycharm": [
                r"C:\Program Files\JetBrains\PyCharm Community Edition\bin\pycharm64.exe",
            ],

            "android studio": [
                r"C:\Program Files\Android\Android Studio\bin\studio64.exe",
            ],

            "word": [
                r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            ],

            "excel": [
                r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            ],

            "powerpoint": [
                r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
            ],

            "outlook": [
                r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
            ],
        }

    def find_application(self, application):
        """
        Find executable path.

        Parameters
        ----------
        application : str

        Returns
        -------
        str | None
        """

        if not application:
            return None

        application = application.lower()

        application = self.aliases.get(
            application,
            application
        )

        application = application.replace(".exe", "")

        path = self.search_database(
            application
        )

        if path:
            return path

        # -----------------------------------
        # Search Known Locations
        # -----------------------------------

        path = self.search_known_locations(application)

        if path:
            return path

        # -----------------------------------
        # Search Environment PATH
        # -----------------------------------

        path = self.search_environment(application)

        if path:
            return path

        # -----------------------------------
        # Return executable name
        # (Windows apps like notepad.exe)
        # -----------------------------------

        return application + ".exe"

    def search_known_locations(self, application):
        """
        Search predefined installation paths.
        """

        if application not in self.known_paths:
            return None

        for path in self.known_paths[application]:

            if os.path.exists(path):

                return path

        return None

    def search_environment(self, application):
        """
        Search Windows PATH variable.
        """

        executable = shutil.which(application)

        if executable:
            return executable

        executable = shutil.which(application + ".exe")

        if executable:
            return executable

        return None
    
    def search_database(self, application):
        """
        Search application from SQLite database.
        """

        result = self.database.get_application(
            application
        )

        if result:
            return result[2]

        return None