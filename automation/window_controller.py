"""
Window Controller Module

Provides window automation using
PyWinAuto + Win32 API.
"""

import win32gui

from pywinauto import Application


class WindowController:
    """
    Controls the currently active window.
    """

    def __init__(self):
        """
        Initialize Window Controller.
        """

        pass

    def _get_active_window(self):
        """
        Return the active window.

        Returns
        -------
        WindowSpecification | None
        """

        try:

            hwnd = win32gui.GetForegroundWindow()

            if hwnd == 0:
                return None

            app = Application(
                backend="uia"
            ).connect(handle=hwnd)

            window = app.window(handle=hwnd)

            return window

        except Exception as error:

            print(f"Window Error : {error}")

            return None

    def get_window_title(self):
        """
        Return active window title.

        Returns
        -------
        str | None
        """

        try:

            hwnd = win32gui.GetForegroundWindow()

            if hwnd == 0:
                return None

            return win32gui.GetWindowText(hwnd)

        except Exception as error:

            print(f"Title Error : {error}")

            return None

    def minimize_window(self):
        """
        Minimize active window.

        Returns
        -------
        bool
        """

        try:

            window = self._get_active_window()

            if window:

                window.minimize()

                return True

            return False

        except Exception as error:

            print(f"Minimize Error : {error}")

            return False

    def maximize_window(self):
        """
        Maximize active window.

        Returns
        -------
        bool
        """

        try:

            window = self._get_active_window()

            if window:

                window.maximize()

                return True

            return False

        except Exception as error:

            print(f"Maximize Error : {error}")

            return False

    def restore_window(self):
        """
        Restore active window.

        Returns
        -------
        bool
        """

        try:

            window = self._get_active_window()

            if window:

                window.restore()

                return True

            return False

        except Exception as error:

            print(f"Restore Error : {error}")

            return False

    def close_window(self):
        """
        Close active window.

        Returns
        -------
        bool
        """

        try:

            window = self._get_active_window()

            if window:

                window.close()

                return True

            return False

        except Exception as error:

            print(f"Close Error : {error}")

            return False