"""
Window Controller Module

Provides reliable Windows window automation using
PyWinAuto + Win32 API.

Responsibilities
----------------
- Detect the current foreground window
- Read active window title
- Find and activate application windows
- Restore minimized windows
- Verify foreground activation
- Wait for newly launched application windows
- Minimize / maximize / restore / close active windows
"""

from __future__ import annotations

import time

import win32con
import win32gui

from pywinauto import Application


class WindowController:
    """
    Controls Windows desktop windows.

    The controller uses Win32 APIs for reliable foreground-window
    management and PyWinAuto for high-level window operations.
    """

    def __init__(self) -> None:
        pass

    # ==============================================================
    # ACTIVE WINDOW
    # ==============================================================

    def _get_active_window(self):
        """
        Return the currently active foreground window.

        Returns
        -------
        pywinauto.WindowSpecification | None
            Active window wrapper, or None if unavailable.
        """

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

    # ==============================================================
    # ACTIVE WINDOW HANDLE
    # ==============================================================

    def _get_active_hwnd(self) -> int | None:
        """
        Return the HWND of the current foreground window.
        """

        try:
            hwnd = win32gui.GetForegroundWindow()

            if hwnd == 0:
                return None

            return hwnd

        except Exception as error:
            print(f"HWND Error : {error}")
            return None

    # ==============================================================
    # ACTIVE WINDOW TITLE
    # ==============================================================

    def get_window_title(self):
        """
        Return the title of the current foreground window.
        """

        try:
            hwnd = win32gui.GetForegroundWindow()

            if hwnd == 0:
                return None

            return win32gui.GetWindowText(hwnd)

        except Exception as error:
            print(f"Title Error : {error}")
            return None

    # ==============================================================
    # WINDOW TITLE MATCHING
    # ==============================================================

    def _title_matches(
        self,
        title: str,
        title_keyword: str,
    ) -> bool:
        """
        Check whether a window title matches a keyword.

        Matching is case-insensitive and supports partial matches.

        Example
        -------
        title:
            "Document1 - Microsoft Word"

        keyword:
            "word"

        Result:
            True
        """

        if not title or not title_keyword:
            return False

        return title_keyword.strip().lower() in title.lower()

    # ==============================================================
    # VERIFY FOREGROUND WINDOW
    # ==============================================================

    def _is_foreground_window(
        self,
        hwnd: int,
    ) -> bool:
        """
        Verify that the supplied HWND is currently the foreground
        window.

        This is important because calling SetForegroundWindow()
        does not guarantee that Windows actually granted foreground
        focus.
        """

        try:
            active_hwnd = win32gui.GetForegroundWindow()

            return active_hwnd == hwnd

        except Exception as error:
            print(
                f"Foreground Verification Error : {error}"
            )

            return False

    # ==============================================================
    # FORCE FOREGROUND WINDOW
    # ==============================================================

    def _bring_to_foreground(
        self,
        hwnd: int,
        retries: int = 5,
    ) -> bool:
        """
        Attempt to bring a window to the foreground and verify it.

        Parameters
        ----------
        hwnd:
            Target window handle.

        retries:
            Number of activation attempts.

        Returns
        -------
        bool
            True only when the target window is actually the
            foreground window.
        """

        if hwnd == 0:
            return False

        for attempt in range(retries):

            try:

                # --------------------------------------------------
                # Restore minimized window
                # --------------------------------------------------

                if win32gui.IsIconic(hwnd):

                    win32gui.ShowWindow(
                        hwnd,
                        win32con.SW_RESTORE,
                    )

                else:

                    win32gui.ShowWindow(
                        hwnd,
                        win32con.SW_SHOW,
                    )

                # --------------------------------------------------
                # Bring window to top
                # --------------------------------------------------

                try:
                    win32gui.BringWindowToTop(hwnd)
                except Exception:
                    pass

                # --------------------------------------------------
                # Set foreground window
                # --------------------------------------------------

                try:
                    win32gui.SetForegroundWindow(hwnd)
                except Exception:
                    pass

                # --------------------------------------------------
                # Set active window
                # --------------------------------------------------

                try:
                    win32gui.SetActiveWindow(hwnd)
                except Exception:
                    pass

                # --------------------------------------------------
                # Set focus
                # --------------------------------------------------

                try:
                    win32gui.SetFocus(hwnd)
                except Exception:
                    pass

                # --------------------------------------------------
                # Give Windows time to process activation
                # --------------------------------------------------

                time.sleep(0.15)

                # --------------------------------------------------
                # Verify actual foreground window
                # --------------------------------------------------

                if self._is_foreground_window(hwnd):

                    return True

            except Exception as error:

                print(
                    f"Foreground Activation Attempt "
                    f"{attempt + 1} Error : {error}"
                )

            time.sleep(0.15)

        return False

    # ==============================================================
    # ACTIVATE WINDOW
    # ==============================================================

    def activate_window(
        self,
        title_keyword,
    ):
        """
        Find and activate a visible window whose title contains
        the supplied keyword.

        The method returns True ONLY when the target window is
        actually confirmed as the foreground window.

        Parameters
        ----------
        title_keyword:
            Window-title keyword.

        Returns
        -------
        bool
            True if the target window became active.
        """

        if not title_keyword:
            return False

        target_keyword = str(title_keyword).strip()

        if not target_keyword:
            return False

        found_hwnd = None

        def callback(hwnd, _):

            nonlocal found_hwnd

            if found_hwnd is not None:
                return

            # ------------------------------------------------------
            # Ignore invisible windows
            # ------------------------------------------------------

            if not win32gui.IsWindowVisible(hwnd):
                return

            # ------------------------------------------------------
            # Get title
            # ------------------------------------------------------

            try:
                title = win32gui.GetWindowText(hwnd)
            except Exception:
                return

            if not title:
                return

            # ------------------------------------------------------
            # Match title
            # ------------------------------------------------------

            if not self._title_matches(
                title,
                target_keyword,
            ):
                return

            found_hwnd = hwnd

        # ----------------------------------------------------------
        # Enumerate all top-level windows
        # ----------------------------------------------------------

        try:

            win32gui.EnumWindows(
                callback,
                None,
            )

        except Exception as error:

            print(
                f"Window Enumeration Error : {error}"
            )

            return False

        if found_hwnd is None:
            return False

        # ----------------------------------------------------------
        # Activate target window
        # ----------------------------------------------------------

        title = win32gui.GetWindowText(found_hwnd)

        activated = self._bring_to_foreground(
            found_hwnd
        )

        if activated:

            print(
                f"Window Activated : {title}"
            )

            return True

        print(
            f"Window Found But Activation Failed : {title}"
        )

        return False

    # ==============================================================
    # ACTIVATE WINDOW BY HWND
    # ==============================================================

    def activate_window_by_handle(
        self,
        hwnd: int,
    ) -> bool:
        """
        Activate a specific window using its HWND.

        This is useful when an application launcher already knows
        the exact window handle of a newly launched application.
        """

        if not hwnd:
            return False

        if not win32gui.IsWindow(hwnd):
            return False

        title = win32gui.GetWindowText(hwnd)

        activated = self._bring_to_foreground(
            hwnd
        )

        if activated:

            print(
                f"Window Activated : {title}"
            )

            return True

        print(
            f"Window Activation Failed : {title}"
        )

        return False

    # ==============================================================
    # WAIT FOR WINDOW
    # ==============================================================

    def wait_for_window(
        self,
        title_keyword,
        timeout=10,
    ):
        """
        Wait until a matching window appears and becomes active.

        Parameters
        ----------
        title_keyword:
            Window-title keyword.

        timeout:
            Maximum number of seconds to wait.

        Returns
        -------
        bool
            True only after the matching window has been confirmed
            as the foreground window.
        """

        if not title_keyword:
            return False

        start = time.time()

        while time.time() - start < timeout:

            if self.activate_window(
                title_keyword
            ):

                # --------------------------------------------------
                # Extra verification after activation
                # --------------------------------------------------

                time.sleep(0.2)

                active_title = self.get_window_title()

                if active_title and self._title_matches(
                    active_title,
                    title_keyword,
                ):

                    return True

            time.sleep(0.3)

        return False

    # ==============================================================
    # MINIMIZE
    # ==============================================================

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

    # ==============================================================
    # MAXIMIZE
    # ==============================================================

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

    # ==============================================================
    # RESTORE
    # ==============================================================

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

    # ==============================================================
    # CLOSE
    # ==============================================================

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