"""
Application Scanner Module

Scans installed Windows applications
and stores them in the SQLite database.
"""

import os
import shutil

from database.database_manager import DatabaseManager


class ApplicationScanner:
    """
    Scan installed applications.
    """

    def __init__(self):

        self.database = DatabaseManager()

        self.common_applications = {

            # Browsers
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "firefox": "firefox.exe",
            "brave": "brave.exe",
            "opera": "opera.exe",

            # Windows
            "notepad": "notepad.exe",
            "paint": "mspaint.exe",
            "calculator": "calc.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "explorer": "explorer.exe",

            # IDEs
            "vscode": "Code.exe",
            "pycharm": "pycharm64.exe",
            "android studio": "studio64.exe",

            # Office
            "word": "WINWORD.EXE",
            "excel": "EXCEL.EXE",
            "powerpoint": "POWERPNT.EXE",
            "outlook": "OUTLOOK.EXE",
        }

    # -------------------------------------

    def scan_environment(self):

        print("\nScanning Windows PATH...\n")

        for app_name, executable in self.common_applications.items():

            path = shutil.which(executable)

            if not path:
                continue

            print(f"Found : {app_name}")

            self.database.insert_application(

                name=app_name,

                exe_name=executable,

                full_path=path,

                source="PATH"

            )

            self.database.insert_alias(
                app_name,
                app_name
            )

    # -------------------------------------

    def scan_common_locations(self):
        """
        Scan common Program Files folders.
        """

        print("\nScanning Common Locations...\n")

        folders = [

            r"C:\Program Files",

            r"C:\Program Files (x86)",

            os.path.expandvars(
                r"%LOCALAPPDATA%\Programs"
            ),

            rf"C:\Users\{os.getlogin()}\myproject"
        ]

        executable_names = {

            exe.lower()

            for exe in self.common_applications.values()

        }

        found_apps = set()

        for folder in folders:

            if not os.path.exists(folder):

                continue

            for root, _, files in os.walk(folder):

                for file in files:

                    if file.lower() in executable_names:

                        full_path = os.path.join(root, file)

                        # Ignore unwanted Microsoft executables
                        if (
                            "Copilot" in full_path
                            or "EdgeCore" in full_path
                            or "EdgeWebView" in full_path
                        ):
                            continue

                        full_path = os.path.join(
                            root,
                            file
                        )

                        app_name = None

                        for name, exe in self.common_applications.items():

                            if exe.lower() == file.lower():

                                app_name = name

                                break

                        if app_name not in found_apps:

                            found_apps.add(app_name)

                            print(f"Found : {app_name}")

                            self.database.insert_application(

                                name=app_name,

                                exe_name=file,

                                full_path=full_path,

                                source="PROGRAM_FILES"

                            )

                            self.database.insert_alias(
                                app_name,
                                app_name
                            )

    # -------------------------------------

    def scan(self):
        """
        Perform complete application scan.
        """

        print("\n==============================")
        print("ASTRA-AI Application Scanner")
        print("==============================")

        # Already scanned?
        if self.database.application_count() > 0:

            print("\nApplications already exist in database.")
            print("Skipping scan...")

            self.database.close()

            return

        print("\nScanning system...")

        self.scan_environment()

        self.scan_common_locations()

        self.insert_default_aliases()

        applications = self.database.get_all_applications()

        print(
            f"\nTotal Applications Found : {len(applications)}"
        )

        print("\nApplications Stored :")

        for app in applications:

            print(
                f"{app[0]} -> {app[2]}"
            )

        print("\nScan Completed.")

        self.database.close()

    def insert_default_aliases(self):
        """
        Store common aliases.
        """

        aliases = {

            "google chrome": "chrome",

            "microsoft edge": "edge",

            "visual studio code": "vscode",

            "vs code": "vscode",

            "v s code": "vscode",

            "code": "vscode",

            "note pad": "notepad",

            "my computer": "explorer",

            "this pc": "explorer",

            "command prompt": "cmd",

            "terminal": "cmd",

            "calc": "calculator",

            "power point": "powerpoint",

            "microsoft word": "word",

            "microsoft excel": "excel"

        }

        for alias, application in aliases.items():

            self.database.insert_alias(
                alias,
                application
            )

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close(self):
        """
        Close database connection.
        """

        self.database.close()