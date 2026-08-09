"""
Application Closer Module

Provides robust Windows application/window closing.

Features
--------
- Check whether an application is running
- Resolve application names to process names
- Close application gracefully
- Force terminate if required
- Verify that application is closed
- Support CMD
- Support PowerShell
- Support Windows Camera
- Support common executable names
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path


class AppCloser:
    """
    Close running Windows applications safely and forcefully.
    """

    # ==================================================
    # Application Aliases
    # ==================================================

    APPLICATION_ALIASES = {

        # Browsers
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",

        "edge": "msedge.exe",
        "microsoft edge": "msedge.exe",

        "firefox": "firefox.exe",
        "mozilla firefox": "firefox.exe",

        "brave": "brave.exe",
        "brave browser": "brave.exe",

        # Windows Terminal / Consoles
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "command prompt window": "cmd.exe",

        "powershell": "powershell.exe",
        "windows powershell": "powershell.exe",

        # Windows applications
        "task manager": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",

        "file explorer": "explorer.exe",
        "explorer": "explorer.exe",

        "control panel": "control.exe",

        # Camera
        "camera": "WindowsCamera.exe",
        "camera app": "WindowsCamera.exe",
        "windows camera": "WindowsCamera.exe",

        # Common editors
        "notepad": "notepad.exe",
        "notepad++": "notepad++.exe",

        # VS Code
        "visual studio code": "Code.exe",
        "vs code": "Code.exe",
        "code": "Code.exe",

        # Python
        "python": "python.exe",
        "python launcher": "py.exe",

    }

    # ==================================================
    # Initialization
    # ==================================================

    def __init__(self):

        self.force_kill = True

        self.verify_delay = 0.5

        self.verify_attempts = 3

    # ==================================================
    # Resolve Application
    # ==================================================

    def resolve_application(
        self,
        application: str
    ) -> str | None:
        """
        Resolve a user/application name to an executable.

        Parameters
        ----------
        application : str

        Returns
        -------
        str | None
        """

        if not application:

            return None

        application = application.strip()

        normalized = (
            application
            .lower()
            .strip()
        )

        # ---------------------------------
        # Alias
        # ---------------------------------

        if normalized in self.APPLICATION_ALIASES:

            return self.APPLICATION_ALIASES[
                normalized
            ]

        # ---------------------------------
        # Full Path
        # ---------------------------------

        if "\\" in application:

            return Path(
                application
            ).name

        # ---------------------------------
        # Executable
        # ---------------------------------

        if normalized.endswith(".exe"):

            return application

        # ---------------------------------
        # Assume executable
        # ---------------------------------

        return (
            application
            + ".exe"
        )

    # ==================================================
    # Check Running
    # ==================================================

    def is_running(
        self,
        application: str
    ) -> bool:
        """
        Check whether an application process is running.

        Returns
        -------
        bool
        """

        executable = (
            self.resolve_application(
                application
            )
        )

        if not executable:

            return False

        try:

            result = subprocess.run(

                [
                    "tasklist",
                    "/FI",
                    f"IMAGENAME eq {executable}"
                ],

                capture_output=True,

                text=True,

                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if hasattr(
                        subprocess,
                        "CREATE_NO_WINDOW"
                    )
                    else 0
                )

            )

            output = (
                result.stdout
                .lower()
            )

            return (
                executable.lower()
                in output
            )

        except Exception as error:

            print(
                f"Process Check Error : {error}"
            )

            return False

    # ==================================================
    # Get Process List
    # ==================================================

    def get_running_processes(
        self
    ) -> list[str]:
        """
        Get currently running process names.

        Returns
        -------
        list[str]
        """

        try:

            result = subprocess.run(

                [
                    "tasklist",
                    "/FO",
                    "CSV",
                    "/NH"
                ],

                capture_output=True,

                text=True,

                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if hasattr(
                        subprocess,
                        "CREATE_NO_WINDOW"
                    )
                    else 0
                )

            )

            processes = []

            for line in (
                result.stdout
                .splitlines()
            ):

                line = line.strip()

                if not line:

                    continue

                parts = (
                    line
                    .strip('"')
                    .split('","')
                )

                if parts:

                    processes.append(
                        parts[0]
                    )

            return processes

        except Exception as error:

            print(
                f"Process List Error : {error}"
            )

            return []

    # ==================================================
    # Graceful Close
    # ==================================================

    def graceful_close(
        self,
        application: str
    ) -> bool:
        """
        Attempt graceful process termination.

        Uses taskkill without /F first.
        """

        executable = (
            self.resolve_application(
                application
            )
        )

        if not executable:

            return False

        try:

            result = subprocess.run(

                [
                    "taskkill",
                    "/IM",
                    executable
                ],

                capture_output=True,

                text=True,

                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if hasattr(
                        subprocess,
                        "CREATE_NO_WINDOW"
                    )
                    else 0
                )

            )

            if result.returncode == 0:

                return True

            return False

        except Exception as error:

            print(
                f"Graceful Close Error : {error}"
            )

            return False

    # ==================================================
    # Force Close
    # ==================================================

    def force_close(
        self,
        application: str
    ) -> bool:
        """
        Force terminate an application.
        """

        executable = (
            self.resolve_application(
                application
            )
        )

        if not executable:

            return False

        try:

            result = subprocess.run(

                [
                    "taskkill",
                    "/IM",
                    executable,
                    "/F",
                    "/T"
                ],

                capture_output=True,

                text=True,

                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if hasattr(
                        subprocess,
                        "CREATE_NO_WINDOW"
                    )
                    else 0
                )

            )

            if result.returncode == 0:

                return True

            return False

        except Exception as error:

            print(
                f"Force Close Error : {error}"
            )

            return False

    # ==================================================
    # Verify Closed
    # ==================================================

    def verify_closed(
        self,
        application: str
    ) -> bool:
        """
        Verify that application is no longer running.
        """

        for _ in range(
            self.verify_attempts
        ):

            if not self.is_running(
                application
            ):

                return True

            time.sleep(
                self.verify_delay
            )

        return False

    # ==================================================
    # Main Close Method
    # ==================================================

    def close_application(
        self,
        application: str
    ) -> bool:
        """
        Close an application.

        Workflow
        --------
        1. Resolve application.
        2. Check whether it is running.
        3. Try graceful close.
        4. Verify.
        5. Force kill if still running.
        6. Verify again.

        Returns
        -------
        bool
        """

        if not application:

            print(
                "Close Error : "
                "Application name is empty."
            )

            return False

        executable = (
            self.resolve_application(
                application
            )
        )

        if not executable:

            print(
                "Close Error : "
                "Unable to resolve application."
            )

            return False

        print(
            f"Checking : {executable}"
        )

        # ---------------------------------
        # Check Running
        # ---------------------------------

        if not self.is_running(
            executable
        ):

            print(
                f"{executable} is not running."
            )

            return False

        print(
            f"{executable} is running."
        )

        # ---------------------------------
        # Graceful Close
        # ---------------------------------

        print(
            f"Attempting graceful close : "
            f"{executable}"
        )

        self.graceful_close(
            executable
        )

        # ---------------------------------
        # Verify
        # ---------------------------------

        if self.verify_closed(
            executable
        ):

            print(
                f"{executable} closed successfully."
            )

            return True

        # ---------------------------------
        # Force Kill
        # ---------------------------------

        if self.force_kill:

            print(
                f"Graceful close failed."
            )

            print(
                f"Force closing : {executable}"
            )

            self.force_close(
                executable
            )

        # ---------------------------------
        # Final Verification
        # ---------------------------------

        if self.verify_closed(
            executable
        ):

            print(
                f"{executable} force closed successfully."
            )

            return True

        print(
            f"Unable to close : {executable}"
        )

        return False

    # ==================================================
    # Close By Executable
    # ==================================================

    def close_process(
        self,
        executable: str
    ) -> bool:
        """
        Directly close a known executable.
        """

        return self.close_application(
            executable
        )