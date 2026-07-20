"""
Keyboard Automation Module

This module performs keyboard automation
using PyAutoGUI and PyWinAuto.
"""

import time
import pyautogui

from pywinauto.keyboard import send_keys


BROWSER_DELAY = 1.5
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
            send_keys(key_map[key])
            return True

        # Letters

        if len(key) == 1 and key.isalpha():

            send_keys(key)

            return True


        # Numbers

        if len(key) == 1 and key.isdigit():

            send_keys(key)

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

        if shortcut in shortcut_map:
            send_keys(shortcut_map[shortcut])
            return True

        # Generic fallback using PyAutoGUI
        try:
            pyautogui.hotkey(*[key.lower() for key in keys])
            return True
        except Exception:
            return False

    def copy(self):
        """
        Copy selected text.
        """

        return self.hotkey("ctrl", "c")

    def paste(self):
        """
        Paste copied text.
        """

        return self.hotkey("ctrl", "v")

    def cut(self):
        """
        Cut selected text.
        """

        return self.hotkey("ctrl", "x")

    def undo(self):
        """
        Undo previous action.
        """

        return self.hotkey("ctrl", "z")

    def redo(self):
        """
        Redo previous action.
        """

        return self.hotkey("ctrl", "y")
    

    # --------------------------------------------------
    # Browser Shortcuts
    # --------------------------------------------------
    def new_tab(self):
        """
        Open a new browser tab.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("ctrl", "t")


    def close_tab(self):
        """
        Close browser tab.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("ctrl", "w")


    def next_tab(self):
        """
        Go to next browser tab.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("ctrl", "tab")


    def previous_tab(self):
        """
        Go to Previous browser tab.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("ctrl", "shift", "tab")


    def refresh(self):
        """
        Refresh browser tab.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("ctrl", "r")


    def bookmarks(self):
        """
        Show bookmark bar.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("ctrl", "shift", "b")


    def downloads(self):
        """
        Open a Downloads browser tab.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("ctrl", "j")


    def history(self):
        """
        Open a history browser tab.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("ctrl", "h")


    def address_bar(self):
        """
        Focus browser address bar.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("ctrl", "l")


    def bookmark_page(self):
        """
        bookmark browser tab.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("ctrl", "d")


    def private_window(self):
        """
        Open a new private browser tab.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("ctrl", "shift", "n")


    def back(self):
        """
        Go to back browser tab.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("alt", "left")


    def forward(self):
        """
        Go forward.
        """
        time.sleep(BROWSER_DELAY)
        return self.hotkey("alt", "right")
    
    def backspace(self):
        """
        Press Backspace key.
        """

        return self.press_key("backspace")

    def delete(self):
        """
        Press Delete key.
        """

        return self.press_key("delete")
    
    def arrow_up(self):
        """
        Press Up arrow key.
        """

        return self.press_key("up")


    def arrow_down(self):
        """
        Press Down arrow key.
        """

        return self.press_key("down")


    def arrow_left(self):
        """
        Press Left arrow key.
        """

        return self.press_key("left")


    def arrow_right(self):
        """
        Press Right arrow key.
        """

        return self.press_key("right")
    
    def home(self):
        """
        Press Home key.
        """

        return self.press_key("home")


    def end(self):
        """
        Press End key.
        """

        return self.press_key("end")


    def page_up(self):
        """
        Press Page Up key.
        """

        return self.press_key("pageup")


    def page_down(self):
        """
        Press Page Down key.
        """

        return self.press_key("pagedown")


    def escape(self):
        """
        Press Escape key.
        """

        return self.press_key("escape")


    def space(self):
        """
        Press Space key.
        """

        return self.press_key("space")
    
    def press_character(self, character):

        """
        Press a single letter or number.
        """

        return self.press_key(character)
    
    