"""
Application Launcher Module

This module launches Windows applications.
"""

import subprocess

from automation.application_finder import ApplicationFinder
class AppLauncher:

    def __init__(self):

        self.finder = ApplicationFinder()

        self.applications = {
            # Windows Apps
            "notepad": "notepad.exe",
            "note pad": "notepad.exe",

            "paint": "mspaint.exe",
            "mspaint": "mspaint.exe",

            "calculator": "calc.exe",
            "calc": "calc.exe",

            "command prompt": "cmd.exe",
            "cmd": "cmd.exe",

            "powershell": "powershell.exe",

            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "this pc": "explorer.exe",
            "my computer": "explorer.exe",

            "task manager": "taskmgr.exe",

            "settings": "ms-settings:",

            "control panel": "control",

            "registry editor": "regedit.exe",

            "services": "services.msc",

            "device manager": "devmgmt.msc",

            # Browsers
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",

            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",

            "firefox": "firefox.exe",

            "brave": "brave.exe",

            "opera": "opera.exe",

            # IDEs
            "visual studio code": "code",
            "vs code": "code",
            "vscode": "code",

            "pycharm": "pycharm64.exe",

            "android studio": "studio64.exe",

            # Microsoft Office
            "word": "WINWORD.EXE",

            "excel": "EXCEL.EXE",

            "powerpoint": "POWERPNT.EXE",

            "power point": "POWERPNT.EXE",

            "outlook": "OUTLOOK.EXE",

            "onenote": "ONENOTE.EXE"
        }

    def launch_application(self, application):

        """
        Launch the given application.

        Parameters:
            application (str)

        Returns:
            bool
        """

        if not application:
            return False

        try:

            application = application.lower()

            application = self.applications.get(
                application,
                application
            )

            application = self.finder.find_application(
                application
            )

            print(f"Resolved Application Path : {application}")

            # Windows special URI
            if application.startswith("ms-"):

                import os
                os.startfile(application)

            # Normal executable
            else:

                import os
                os.startfile(application)

            return True

        except Exception as error:

            print(f"Error : {error}")

            return False