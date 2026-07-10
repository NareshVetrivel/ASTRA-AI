"""
Keyboard Automation Module

This module performs keyboard automation
using PyAutoGUI and PyWinAuto.
"""

import time
import pyautogui

from pywinauto.keyboard import send_keys


class KeyboardController:
    """
    Perform keyboard automation tasks.
    """

    def __init__(self):
        """
        Initialize keyboard controller.
        """

        # Small delay between PyAutoGUI actions
        pyautogui.PAUSE = 0.1

    def type_text(self, text):
        """
        Type the given text.

        Parameters:
            text (str)

        Returns:
            bool
        """

        if not text:
            return False

        # Wait for the target window
        time.sleep(2)

        # Type text
        pyautogui.write(
            text,
            interval=0.03
        )

        return True

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

        time.sleep(2)

        key = key.lower()

        key_map = {
            "enter": "{ENTER}",
            "tab": "{TAB}",
            "space": " ",
            "esc": "{ESC}",
            "escape": "{ESC}",
            "backspace": "{BACKSPACE}",
            "delete": "{DELETE}",
            "up": "{UP}",
            "down": "{DOWN}",
            "left": "{LEFT}",
            "right": "{RIGHT}"
        }

        if key in key_map:
            send_keys(key_map[key])
            return True

        return False

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

        time.sleep(2)

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
            "ctrl+o": "^o"
        }

        if shortcut in shortcut_map:
            send_keys(shortcut_map[shortcut])
            return True

        return False