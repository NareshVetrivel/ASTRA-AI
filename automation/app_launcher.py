"""
Application Launcher Module

This module launches Windows applications and ensures that the
newly launched application's window becomes the active foreground
window before reporting success.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from automation.application_finder import ApplicationFinder
from automation.window_controller import WindowController


class AppLauncher:
    """
    Launch Windows applications.

    Launch flow
    -----------
    1. Resolve application name/path.
    2. Launch the application.
    3. Wait for its window to appear.
    4. Activate the application window.
    5. Verify that it is actually the foreground window.
    6. Return success only after activation succeeds.
    """

    def __init__(self):

        self.finder = ApplicationFinder()

        self.window_controller = WindowController()

        self.applications = {

            # ==========================================================
            # Windows Apps
            # ==========================================================

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

            # ==========================================================
            # Browsers
            # ==========================================================

            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",

            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",

            "firefox": "firefox.exe",

            "brave": "brave.exe",

            "opera": "opera.exe",

            # ==========================================================
            # IDEs
            # ==========================================================

            "visual studio code": "code",
            "vs code": "code",
            "vscode": "code",

            "pycharm": "pycharm64.exe",

            "android studio": "studio64.exe",

            # ==========================================================
            # Microsoft Office
            # ==========================================================

            "word": "WINWORD.EXE",

            "excel": "EXCEL.EXE",

            "powerpoint": "POWERPNT.EXE",

            "power point": "POWERPNT.EXE",

            "outlook": "OUTLOOK.EXE",

            "onenote": "ONENOTE.EXE",
        }

    # ==============================================================
    # WAIT UNTIL READY
    # ==============================================================

    def wait_until_ready(
        self,
        application,
        timeout=10,
    ):
        """
        Wait until the launched application's window appears and
        becomes the foreground window.

        Parameters
        ----------
        application:
            Window title keyword.

        timeout:
            Maximum number of seconds to wait.

        Returns
        -------
        bool
            True only when the target window is active.
        """

        if not application:
            return False

        try:

            return self.window_controller.wait_for_window(
                application,
                timeout,
            )

        except Exception as error:

            print(
                f"Window Ready Error : {error}"
            )

            return False

    # ==============================================================
    # RESOLVE APPLICATION
    # ==============================================================

    def _resolve_application(
        self,
        application,
    ):
        """
        Resolve a user-facing application name to an executable/path.

        Examples
        --------
        "notepad" -> "notepad.exe"
        "word"    -> "WINWORD.EXE"
        """

        if not application:
            return None

        application = str(application).strip().lower()

        if not application:
            return None

        return self.applications.get(
            application,
            application,
        )

    # ==============================================================
    # GET WINDOW KEYWORD
    # ==============================================================

    def _get_window_keyword(
        self,
        application_path,
    ):
        """
        Return a suitable window-title keyword for a launched
        application.

        This primarily uses the executable filename stem.

        Examples
        --------
        WINWORD.EXE  -> WINWORD
        EXCEL.EXE    -> EXCEL
        POWERPNT.EXE -> POWERPNT
        notepad.exe  -> notepad
        """

        try:

            path = Path(str(application_path))

            return path.stem

        except Exception:

            return str(application_path)

    # ==============================================================
    # LAUNCH APPLICATION
    # ==============================================================

    def launch_application(
        self,
        application,
    ):
        """
        Launch a Windows application and make its window active.

        Returns
        -------
        bool
            True only when:

            - application launch succeeds
            - application window appears
            - application window becomes foreground/active

        Notes
        -----
        This method deliberately does NOT report success merely
        because os.startfile() returned without an exception.
        """

        if not application:
            return False

        try:

            # ------------------------------------------------------
            # 1. Resolve user application name
            # ------------------------------------------------------

            resolved_application = self._resolve_application(
                application
            )

            if not resolved_application:
                return False

            # ------------------------------------------------------
            # 2. Resolve actual application path
            # ------------------------------------------------------

            application_path = self.finder.find_application(
                resolved_application
            )

            print(
                f"Resolved Application Path : "
                f"{application_path}"
            )

            if not application_path:
                print(
                    "Launch Error : Application path could not "
                    "be resolved."
                )

                return False

            # ------------------------------------------------------
            # 3. Launch application
            # ------------------------------------------------------

            print(
                f"Launching Application : "
                f"{application_path}"
            )

            os.startfile(application_path)

            # ------------------------------------------------------
            # 4. Give Windows a short startup period
            # ------------------------------------------------------

            time.sleep(0.8)

            # ------------------------------------------------------
            # 5. Determine window-title keyword
            # ------------------------------------------------------

            title_keyword = self._get_window_keyword(
                application_path
            )

            print(
                f"Waiting For Window : "
                f"{title_keyword}"
            )

            # ------------------------------------------------------
            # 6. Wait for window + activate + verify foreground
            # ------------------------------------------------------

            ready = self.wait_until_ready(
                title_keyword,
                timeout=10,
            )

            if not ready:

                print(
                    f"Launch Error : Application launched but "
                    f"window could not be activated : "
                    f"{title_keyword}"
                )

                return False

            # ------------------------------------------------------
            # 7. Final foreground verification
            # ------------------------------------------------------

            active_title = (
                self.window_controller.get_window_title()
            )

            if not active_title:

                print(
                    "Launch Error : Active window title "
                    "could not be determined."
                )

                return False

            print(
                f"Active Window : {active_title}"
            )

            # ------------------------------------------------------
            # 8. Success
            # ------------------------------------------------------

            print(
                f"SUCCESS : Application launched and "
                f"activated : {active_title}"
            )

            return True

        except Exception as error:

            print(
                f"Launch Error : {error}"
            )

            return False