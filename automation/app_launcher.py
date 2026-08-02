"""
Application Launcher Module

This module launches Windows applications.
"""

import os
import time
from pathlib import Path

from automation.application_finder import ApplicationFinder
from automation.window_controller import WindowController


class AppLauncher:
    """
    Launch Windows applications.
    """

    def __init__(self):

        self.finder = ApplicationFinder()

        self.window_controller = WindowController()

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

    # --------------------------------------------------
    # Wait Until Ready
    # --------------------------------------------------

    def wait_until_ready(
        self,
        application,
        timeout=10
    ):
        """
        Wait until launched application
        becomes active.
        """

        return self.window_controller.wait_for_window(
            application,
            timeout
        )

    # --------------------------------------------------
    # Launch Application
    # --------------------------------------------------

    def launch_application(
        self,
        application
    ):
        """
        Launch application.

        Returns
        -------
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

            print(
                f"Resolved Application Path : {application}"
            )

            os.startfile(application)

            time.sleep(1.5)

            title = Path(application).stem

            self.wait_until_ready(title)

            return True

        except Exception as error:

            print(
                f"Launch Error : {error}"
            )

            return False