"""
Intent Detection Module

This module identifies the user's intent
from the recognized speech text using
keyword and fuzzy matching.
"""

from rapidfuzz import process, fuzz


class IntentDetector:
    """
    Detects user intent using keyword
    and fuzzy matching.
    """

    def __init__(self):

        self.intent_keywords = {

            # ---------------------------------
            # Application Commands
            # ---------------------------------
            "open": "launch_application",
            "start": "launch_application",
            "run": "launch_application",
            "launch": "launch_application",
            "execute": "launch_application",

            "close": "close_application",
            "exit": "close_application",
            "stop": "close_application",
            "quit": "close_application",
            "terminate": "close_application",

            # ---------------------------------
            # Typing Commands
            # ---------------------------------
            "type": "type_text",
            "write": "type_text",

            # ---------------------------------
            # Clipboard Commands
            # ---------------------------------
            "copy": "copy",
            "paste": "paste",
            "cut": "cut",
            "undo": "undo",
            "redo": "redo",

            # ---------------------------------
            # Keyboard Commands
            # ---------------------------------
            "enter": "press_enter",
            "tab": "press_tab",

            "backspace": "backspace",
            "delete": "delete",

            "escape": "escape",
            "esc": "escape",

            "space": "space",

            "up": "arrow_up",
            "down": "arrow_down",
            "left": "arrow_left",
            "right": "arrow_right",

            "home": "home",
            "end": "end",

            "page": "page_down",

            # ---------------------------------
            # Mouse Commands
            # ---------------------------------
            "click": "left_click",
            "left": "left_click",
            "right": "right_click",
            "double": "double_click",
            "scroll": "scroll_down",

            # ---------------------------------
            # Window Commands
            # ---------------------------------
            "minimize": "minimize_window",
            "maximize": "maximize_window",
            "restore": "restore_window",
            "minimise": "minimize_window",
            "maximise": "maximize_window",

            # ---------------------------------
            # System Commands
            # ---------------------------------
            "mute": "mute",
            "screenshot": "take_screenshot",
            "task": "open_task_manager",
            "explorer": "open_file_explorer",
            "lock": "lock_screen",

            # ---------------------------------
            # Shortcut Commands
            # ---------------------------------
            "select": "select_all",
            "save": "save_file",
            "print": "print_file"
        }

    def detect_intent(self, text):
        """
        Detect user intent.

        Parameters
        ----------
        text : str

        Returns
        -------
        str | None
        """

        if not text:
            return None

        text = text.lower()
        text = text.strip()

        # ---------------------------------
        # Multi-word Commands (Highest Priority)
        # ---------------------------------

        if "select all" in text:
            return "select_all"

        if "press enter" in text:
            return "press_enter"

        if "press tab" in text:
            return "press_tab"

        if "backspace" in text:
            return "backspace"

        if "delete" in text:
            return "delete"

        if "save file" in text:
            return "save_file"

        if "print file" in text:
            return "print_file"

        if "right click" in text:
            return "right_click"

        if "double click" in text:
            return "double_click"

        if "left click" in text:
            return "left_click"

        if "scroll up" in text:
            return "scroll_up"

        if "scroll down" in text:
            return "scroll_down"

        if "window" in text and "minimize" in text:
            return "minimize_window"

        if "window" in text and "maximize" in text:
            return "maximize_window"

        if "window" in text and "restore" in text:
            return "restore_window"

        if "window" in text and "close" in text:
            return "close_window"

        if "current window" in text:
            return "close_window"

        # ---------------------------------
        # System Commands
        # ---------------------------------

        # Volume

        if (
            "volume up" in text
            or "increase volume" in text
            or "raise volume" in text
        ):
            return "volume_up"

        if (
            "volume down" in text
            or "decrease volume" in text
            or "lower volume" in text
        ):
            return "volume_down"

        # Mute

        if (
            "mute" in text
            or "mute audio" in text
            or "turn off sound" in text
        ):
            return "mute"

        # Lock

        if (
            "lock screen" in text
            or "lock computer" in text
            or "lock my pc" in text
            or "lock system" in text
        ):
            return "lock_screen"

        # Screenshot

        if (
            "take screenshot" in text
            or "screen shot" in text
            or "capture screen" in text
            or "take screen shot" in text
        ):
            return "take_screenshot"

        # Task Manager

        if "task manager" in text:
            return "open_task_manager"

        # Explorer

        if (
            "file explorer" in text
            or "this pc" in text
            or "my computer" in text
        ):
            return "open_file_explorer"

        # ---------------------------------
        # Exact Match
        # ---------------------------------

        words = text.split()

        for word in words:

            if word in self.intent_keywords:

                return self.intent_keywords[word]

        # ---------------------------------
        # Fuzzy Match
        # ---------------------------------

        best_match = process.extractOne(
            text,
            self.intent_keywords.keys(),
            scorer=fuzz.partial_ratio
        )

        if best_match:

            keyword, score, _ = best_match

            print(
                f"Intent Fuzzy Match : "
                f"{keyword} ({score:.1f}%)"
            )

            if score >= 70:

                return self.intent_keywords[keyword]

        # ---------------------------------
        # No Match
        # ---------------------------------

        return None