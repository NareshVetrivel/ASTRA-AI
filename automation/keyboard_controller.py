"""
Keyboard Automation Module

This module performs keyboard automation
using PyAutoGUI and PyWinAuto.

Focus handling is intentionally performed before
keyboard input so that newly launched applications
receive the typing command instead of ASTRA's UI.
"""

from __future__ import annotations

import time

import pyautogui
import win32con
import win32gui

from pywinauto import Application
from pywinauto.keyboard import send_keys


BROWSER_DELAY = 1.5

# Small delay values used for focus stabilization.
FOCUS_WAIT = 0.25
TYPE_DELAY = 0.02


class KeyboardController:
    """
    Perform keyboard automation tasks.

    The controller sends keyboard input to the current
    foreground application. Before typing, it verifies
    and re-activates the foreground window so that focus
    is not accidentally left on ASTRA-AI.
    """

    def __init__(self):
        """
        Initialize keyboard controller.
        """

        # Small delay between PyAutoGUI actions.
        pyautogui.PAUSE = 0.1

    # --------------------------------------------------
    # Active Window Helpers
    # --------------------------------------------------

    def _get_foreground_hwnd(self):
        """
        Return the current foreground window handle.

        Returns
        -------
        int | None
            HWND of the foreground window.
        """

        try:
            hwnd = win32gui.GetForegroundWindow()

            if hwnd == 0:
                return None

            return hwnd

        except Exception:
            return None

    def _get_foreground_title(self):
        """
        Return the title of the current foreground window.

        Returns
        -------
        str | None
        """

        try:
            hwnd = self._get_foreground_hwnd()

            if not hwnd:
                return None

            title = win32gui.GetWindowText(hwnd)

            return title or None

        except Exception:
            return None

    def _activate_foreground_window(self):
        """
        Re-activate the current foreground window.

        This is useful immediately before typing because
        ASTRA's UI/TTS activity may temporarily steal focus.

        Returns
        -------
        bool
            True when a valid foreground window exists
            and activation was attempted successfully.
        """

        try:
            hwnd = self._get_foreground_hwnd()

            if not hwnd:
                return False

            # Restore minimized windows.
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(
                    hwnd,
                    win32con.SW_RESTORE
                )

            # Bring the target window to the front.
            win32gui.BringWindowToTop(hwnd)

            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass

            try:
                win32gui.SetActiveWindow(hwnd)
            except Exception:
                pass

            # PyWinAuto can provide an additional focus attempt.
            try:
                app = Application(
                    backend="uia"
                ).connect(
                    handle=hwnd
                )

                window = app.window(
                    handle=hwnd
                )

                try:
                    window.set_focus()
                except Exception:
                    pass

            except Exception:
                # Some windows cannot be connected through UIA.
                # Win32 foreground activation is still enough.
                pass

            time.sleep(FOCUS_WAIT)

            # Final verification.
            return (
                self._get_foreground_hwnd() == hwnd
            )

        except Exception:
            return False

    def _focus_current_window(self):
        """
        Stabilize focus on the current foreground window.

        Important:
        This method does NOT click the screen.

        Clicking at the current mouse position is unsafe because
        the mouse may be positioned over ASTRA or another control.
        """

        try:
            hwnd = self._get_foreground_hwnd()

            if not hwnd:
                return False

            title = self._get_foreground_title()

            print(
                f"Keyboard Target Window : {title or 'Unknown'}"
            )

            if self._activate_foreground_window():

                active_title = self._get_foreground_title()

                print(
                    f"Keyboard Active Window : "
                    f"{active_title or 'Unknown'}"
                )

                return True

            return False

        except Exception as error:

            print(
                f"Keyboard Focus Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Type Text
    # --------------------------------------------------

    def type_text(self, text):
        """
        Type the given text into the currently active window.

        Parameters
        ----------
        text : str
            Text to type.

        Returns
        -------
        bool
            True when typing was attempted successfully.
        """

        if not text:
            return False

        try:

            # Give a newly launched application a moment to
            # finish creating its main input surface.
            time.sleep(0.8)

            # Re-acquire and stabilize the foreground window
            # immediately before typing.
            if not self._focus_current_window():

                print(
                    "Keyboard Target Error : "
                    "Could not stabilize foreground window."
                )

                return False

            # Small final delay after focus activation.
            time.sleep(FOCUS_WAIT)

            print(
                f"Typing Text : {text}"
            )

            pyautogui.write(
                str(text),
                interval=TYPE_DELAY
            )

            return True

        except Exception as error:

            print(
                f"Typing Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Press Key
    # --------------------------------------------------

    def press_key(self, key):
        """
        Press a single keyboard key.

        Parameters:
            key (str)

        Returns:
            bool
        """

        if not key:
            return False

        time.sleep(0.3)

        key = key.lower()

        key_map = {

            # Basic Keys
            "enter": "{ENTER}",
            "tab": "{TAB}",
            "space": " ",
            "esc": "{ESC}",
            "escape": "{ESC}",
            "backspace": "{BACKSPACE}",
            "delete": "{DELETE}",

            # Arrow Keys
            "up": "{UP}",
            "down": "{DOWN}",
            "left": "{LEFT}",
            "right": "{RIGHT}",

            # Navigation Keys
            "home": "{HOME}",
            "end": "{END}",
            "pageup": "{PGUP}",
            "pagedown": "{PGDN}",
            "insert": "{INSERT}",

            # Function Keys
            "f1": "{F1}",
            "f2": "{F2}",
            "f3": "{F3}",
            "f4": "{F4}",
            "f5": "{F5}",
            "f6": "{F6}",
            "f7": "{F7}",
            "f8": "{F8}",
            "f9": "{F9}",
            "f10": "{F10}",
            "f11": "{F11}",
            "f12": "{F12}"
        }

        if key in key_map:

            try:

                # Make sure the currently active application
                # remains the keyboard target.
                self._focus_current_window()

                send_keys(
                    key_map[key]
                )

                return True

            except Exception:

                return False

        # Letters
        if len(key) == 1 and key.isalpha():

            try:

                self._focus_current_window()

                send_keys(key)

                return True

            except Exception:

                return False

        # Numbers
        if len(key) == 1 and key.isdigit():

            try:

                self._focus_current_window()

                send_keys(key)

                return True

            except Exception:

                return False

        return False

    # --------------------------------------------------
    # Hotkey
    # --------------------------------------------------

    def hotkey(self, *keys):
        """
        Press multiple keys together.

        Examples:
            Ctrl + A
            Ctrl + S
            Ctrl + C

        Returns:
            bool
        """

        if not keys:
            return False

        time.sleep(0.5)

        shortcut = "+".join(
            key.lower() for key in keys
        )

        shortcut_map = {

            "ctrl+a": "^a",
            "ctrl+c": "^c",
            "ctrl+v": "^v",
            "ctrl+x": "^x",
            "ctrl+s": "^s",
            "ctrl+z": "^z",
            "ctrl+y": "^y",
            "ctrl+p": "^p",
            "ctrl+n": "^n",
            "ctrl+o": "^o",
            "ctrl+t": "^t",
            "ctrl+w": "^w",
            "ctrl+tab": "^{TAB}",
            "ctrl+shift+tab": "^+{TAB}",
            "ctrl+r": "^r",
            "ctrl+d": "^d",
            "ctrl+h": "^h",
            "ctrl+j": "^j",
            "ctrl+shift+b": "^+b",
            "ctrl+l": "^l",
            "alt+left": "%{LEFT}",
            "alt+right": "%{RIGHT}",
            "ctrl+shift+n": "^+n"
        }

        try:

            # Stabilize current target before sending shortcut.
            self._focus_current_window()

            if shortcut in shortcut_map:

                send_keys(
                    shortcut_map[shortcut]
                )

                return True

            # Generic fallback using PyAutoGUI.
            pyautogui.hotkey(
                *[
                    key.lower()
                    for key in keys
                ]
            )

            return True

        except Exception:

            return False

    # --------------------------------------------------
    # Clipboard
    # --------------------------------------------------

    def copy(self):
        """
        Copy selected text.
        """

        return self.hotkey(
            "ctrl",
            "c"
        )

    def paste(self):
        """
        Paste copied text.
        """

        return self.hotkey(
            "ctrl",
            "v"
        )

    def cut(self):
        """
        Cut selected text.
        """

        return self.hotkey(
            "ctrl",
            "x"
        )

    def undo(self):
        """
        Undo previous action.
        """

        return self.hotkey(
            "ctrl",
            "z"
        )

    def redo(self):
        """
        Redo previous action.
        """

        return self.hotkey(
            "ctrl",
            "y"
        )

    # --------------------------------------------------
    # Browser Shortcuts
    # --------------------------------------------------

    def new_tab(self):
        """
        Open a new browser tab.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "ctrl",
            "t"
        )

    def close_tab(self):
        """
        Close browser tab.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "ctrl",
            "w"
        )

    def next_tab(self):
        """
        Go to next browser tab.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "ctrl",
            "tab"
        )

    def previous_tab(self):
        """
        Go to previous browser tab.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "ctrl",
            "shift",
            "tab"
        )

    def refresh(self):
        """
        Refresh browser tab.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "ctrl",
            "r"
        )

    def bookmarks(self):
        """
        Show bookmark bar.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "ctrl",
            "shift",
            "b"
        )

    def downloads(self):
        """
        Open Downloads browser tab.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "ctrl",
            "j"
        )

    def history(self):
        """
        Open history browser tab.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "ctrl",
            "h"
        )

    def address_bar(self):
        """
        Focus browser address bar.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "ctrl",
            "l"
        )

    def bookmark_page(self):
        """
        Bookmark current browser tab.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "ctrl",
            "d"
        )

    def private_window(self):
        """
        Open a new private browser window/tab.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "ctrl",
            "shift",
            "n"
        )

    def back(self):
        """
        Go back in browser.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "alt",
            "left"
        )

    def forward(self):
        """
        Go forward in browser.
        """

        time.sleep(BROWSER_DELAY)

        return self.hotkey(
            "alt",
            "right"
        )

    # --------------------------------------------------
    # Navigation Helpers
    # --------------------------------------------------

    def backspace(self):
        """
        Press Backspace key.
        """

        return self.press_key(
            "backspace"
        )

    def delete(self):
        """
        Press Delete key.
        """

        return self.press_key(
            "delete"
        )

    def arrow_up(self):
        """
        Press Up arrow key.
        """

        return self.press_key(
            "up"
        )

    def arrow_down(self):
        """
        Press Down arrow key.
        """

        return self.press_key(
            "down"
        )

    def arrow_left(self):
        """
        Press Left arrow key.
        """

        return self.press_key(
            "left"
        )

    def arrow_right(self):
        """
        Press Right arrow key.
        """

        return self.press_key(
            "right"
        )

    def home(self):
        """
        Press Home key.
        """

        return self.press_key(
            "home"
        )

    def end(self):
        """
        Press End key.
        """

        return self.press_key(
            "end"
        )

    def page_up(self):
        """
        Press Page Up key.
        """

        return self.press_key(
            "pageup"
        )

    def page_down(self):
        """
        Press Page Down key.
        """

        return self.press_key(
            "pagedown"
        )

    def escape(self):
        """
        Press Escape key.
        """

        return self.press_key(
            "escape"
        )

    def space(self):
        """
        Press Space key.
        """

        return self.press_key(
            "space"
        )

    def press_character(self, character):
        """
        Press a single letter or number.
        """

        return self.press_key(
            character
        )

    def press_enter_after_typing(self):
        """
        Press Enter after typing.
        """

        time.sleep(0.5)

        return self.press_key(
            "enter"
        )

    # --------------------------------------------------
    # Activate Window
    # --------------------------------------------------

    def activate_window(
        self,
        seconds=1.5
    ):
        """
        Wait until the current/newly opened window
        becomes active and bring focus to it.

        This method intentionally avoids clicking the
        current mouse position because that can steal
        focus or interact with an unrelated UI element.
        """

        time.sleep(seconds)

        try:

            hwnd = self._get_foreground_hwnd()

            if not hwnd:
                return False

            if win32gui.IsIconic(hwnd):

                win32gui.ShowWindow(
                    hwnd,
                    win32con.SW_RESTORE
                )

            win32gui.BringWindowToTop(
                hwnd
            )

            try:

                win32gui.SetForegroundWindow(
                    hwnd
                )

            except Exception:
                pass

            try:

                win32gui.SetActiveWindow(
                    hwnd
                )

            except Exception:
                pass

            time.sleep(
                FOCUS_WAIT
            )

            return (
                self._get_foreground_hwnd()
                == hwnd
            )

        except Exception:

            return False