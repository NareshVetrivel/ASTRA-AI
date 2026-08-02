"""
Window Controller Module

Provides window automation using
PyWinAuto + Win32 API.
"""

import time

import win32gui
import win32con

from pywinauto import Application


class WindowController:
    """
    Controls Windows desktop windows.
    """

    def __init__(self):
        pass

    # --------------------------------------------------
    # Active Window
    # --------------------------------------------------

    def _get_active_window(self):

        try:

            hwnd = win32gui.GetForegroundWindow()

            if hwnd == 0:
                return None

            app = Application(
                backend="uia"
            ).connect(handle=hwnd)

            return app.window(handle=hwnd)

        except Exception as error:

            print(f"Window Error : {error}")

            return None

    # --------------------------------------------------
    # Active Window Title
    # --------------------------------------------------

    def get_window_title(self):

        try:

            hwnd = win32gui.GetForegroundWindow()

            if hwnd == 0:
                return None

            return win32gui.GetWindowText(hwnd)

        except Exception as error:

            print(f"Title Error : {error}")

            return None

    # --------------------------------------------------
    # Activate Window
    # --------------------------------------------------

    def activate_window(
        self,
        title_keyword
    ):
        """
        Bring matching window
        to foreground.
        """

        found = False

        def callback(hwnd, _):

            nonlocal found

            if found:
                return

            if not win32gui.IsWindowVisible(hwnd):
                return

            title = win32gui.GetWindowText(hwnd)

            if not title:
                return

            if title_keyword.lower() not in title.lower():
                return

            try:

                if win32gui.IsIconic(hwnd):

                    win32gui.ShowWindow(
                        hwnd,
                        win32con.SW_RESTORE
                    )

                else:

                    win32gui.ShowWindow(
                        hwnd,
                        win32con.SW_SHOW
                    )

                win32gui.BringWindowToTop(hwnd)

                try:
                    win32gui.SetForegroundWindow(hwnd)
                except Exception:
                    pass

                try:
                    win32gui.SetActiveWindow(hwnd)
                except Exception:
                    pass

                try:
                    win32gui.SetFocus(hwnd)
                except Exception:
                    pass

                found = True

            except Exception as error:

                print(
                    f"Activate Error : {error}"
                )

        win32gui.EnumWindows(callback, None)

        return found

    # --------------------------------------------------
    # Wait For Window
    # --------------------------------------------------

    def wait_for_window(
        self,
        title_keyword,
        timeout=10
    ):
        """
        Wait until window appears.
        """

        start = time.time()

        while time.time() - start < timeout:

            if self.activate_window(
                title_keyword
            ):

                time.sleep(0.8)

                return True

            time.sleep(0.3)

        return False

    # --------------------------------------------------
    # Minimize
    # --------------------------------------------------

    def minimize_window(self):

        try:

            window = self._get_active_window()

            if window:

                window.minimize()

                return True

            return False

        except Exception as error:

            print(
                f"Minimize Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Maximize
    # --------------------------------------------------

    def maximize_window(self):

        try:

            window = self._get_active_window()

            if window:

                window.maximize()

                return True

            return False

        except Exception as error:

            print(
                f"Maximize Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Restore
    # --------------------------------------------------

    def restore_window(self):

        try:

            window = self._get_active_window()

            if window:

                window.restore()

                return True

            return False

        except Exception as error:

            print(
                f"Restore Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close_window(self):

        try:

            window = self._get_active_window()

            if window:

                window.close()

                return True

            return False

        except Exception as error:

            print(
                f"Close Error : {error}"
            )

            return False