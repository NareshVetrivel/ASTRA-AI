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

        self.application_open_keywords = {

            "chrome",
            "google chrome",
            "edge",
            "microsoft edge",
            "firefox",
            "notepad",
            "paint",
            "calculator",
            "calc",
            "cmd",
            "command prompt",
            "powershell",
            "explorer",
            "word",
            "excel",
            "powerpoint",
            "vscode",
            "visual studio code",
            "pycharm",
            "internet",
            "browser"
        }

        self.folder_open_keywords = {

            "desktop",

            "documents",

            "downloads",

            "pictures",

            "videos",

            "music",

            "this pc",

            "my computer",

            "computer",

            "recycle bin",

            "trash",

            "c drive",

            "d drive",

            "e drive"

        }

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
            "print": "print_file",

            # Folder

            "folder": "open_folder",

            # File

            "file": "open_file"
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
        # Smart Open Detection
        # ---------------------------------

        if (

            text.startswith("open")

            or

            text.startswith("launch")

            or

            text.startswith("start")

            or

            text.startswith("run")

        ):

            # ---------------------------------
            # Browser Website Detection
            # ---------------------------------

            if any(site in text for site in [

                "youtube",
                "google",
                "gmail",
                "github",
                "wikipedia",
                "amazon",
                "flipkart",
                "linkedin",
                "instagram",
                "facebook",
                "twitter",
                ".com",
                ".org",
                ".net"

            ]):

                return "open_website"

            # ---------------------------------
            # Google Search
            # ---------------------------------

            if (

                text.startswith("search")

                or

                "search google" in text

                or

                "google search" in text

            ):

                return "google_search"

            # Browser commands (check BEFORE folders)

            if text == "open history":

                return "browser_history"

            if text == "history":

                return "browser_history"

            if text == "open browser history":

                return "browser_history"

            if text == "open browser downloads":

                return "browser_downloads"

            # Applications

            for app in self.application_open_keywords:

                if app in text:

                    return "launch_application"

            # Special Folders

            for folder in self.folder_open_keywords:

                if folder in text:

                    return "open_folder"

            # Website

            if "www." in text:

                return "open_website"

            if "." in text:

                return "open_website"

            return "open_file"

        # ---------------------------------
        # Folder Commands
        # ---------------------------------

        if "create folder" in text:

            return "create_folder"

        if "rename folder" in text:

            return "rename_folder"

        if "delete folder" in text:

            return "delete_folder"

        if "move folder" in text:

            return "move_folder"

        if "copy folder" in text:

            return "copy_folder"

        if (

            "empty recycle bin" in text

            or

            "clear recycle bin" in text

        ):

            return "empty_recycle_bin"

        # ---------------------------------
        # File Commands
        # ---------------------------------

        if "create file" in text:

            return "create_file"

        if "delete file" in text:

            return "delete_file"

        if "rename file" in text:

            return "rename_file"

        if "move file" in text:

            return "move_file"

        if "copy file" in text:

            return "copy_file"

        if "zip file" in text:

            return "compress_file"

        if "extract zip" in text:

            return "extract_zip"

        if "search extension" in text:

            return "search_extension"

        if "search date" in text:

            return "search_date"

        if "search size" in text:

            return "search_size"

        # ---------------------------------
        # Browser Commands
        # ---------------------------------

        if "new tab" in text:

            return "new_tab"

        if "close tab" in text:

            return "close_tab"

        if "next tab" in text:

            return "next_tab"

        if "previous tab" in text:

            return "previous_tab"

        if "refresh" in text:

            return "refresh"

        if "reload" in text:

            return "refresh"

        if (

            "history" == text

            or

            "open history" == text

            or

            "browser history" in text

        ):

            return "browser_history"

        if (

            text == "downloads"

            or

            text == "open downloads"

            or

            "browser downloads" in text

        ):

            return "browser_downloads"

        if "bookmark page" in text:

            return "bookmark_page"

        if "bookmark" in text:

            return "browser_bookmarks"

        if "address bar" in text:

            return "address_bar"

        if "go back" in text:

            return "browser_back"

        if "go forward" in text:

            return "browser_forward"

        if (

            "private window" in text

            or

            "incognito" in text

            or

            "inprivate" in text

        ):

            return "private_window"

        if (

            "open website" in text

            or

            "visit" in text

        ):

            return "open_website"

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