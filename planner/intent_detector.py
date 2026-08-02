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
            "ms edge",

            "firefox",

            "notepad",
            "note pad",
            "node pad",

            "paint",

            "calculator",
            "calc",

            "cmd",
            "command prompt",
            "powershell",

            "explorer",

            "word",
            "ms word",
            "m s word",

            "excel",
            "ms excel",
            "m s excel",

            "powerpoint",
            "power point",
            "ppt",
            "presentation",

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

        text = (
            text
            .lower()
            .strip()
            .rstrip(".,!?")
        )

        # ---------------------------------
        # Whisper Corrections
        # ---------------------------------

        text = (
            text
            .replace("bdf", "pdf")
            .replace("pdf", "pdf")
            .replace("estaday", "yesterday")
            .replace("study", "today")
        )

        # ---------------------------------
        # Smart Open Detection
        # ---------------------------------

        if (
            (
                text.startswith("open")
                or
                text.startswith("launch")
                or
                text.startswith("run")
            )
            and
            "find " not in text
            and
            "search " not in text
        ):

            # ---------------------------------
            # Browser Website Detection
            # ---------------------------------

            if any(site in text for site in [

                "youtube",

                "gmail",

                "github",

                "wikipedia",

                "amazon",

                "flipkart",

                "linkedin",

                "instagram",

                "facebook",

                "twitter",

                "chatgpt",

                "reddit",

                "stackoverflow"

            ]):

                return "open_website"

        # ---------------------------------
        # File Search Commands
        # ---------------------------------

        file_extensions = {

            "pdf",
            "doc",
            "docx",
            "txt",
            "ppt",
            "pptx",
            "xls",
            "xlsx",
            "csv",
            "jpg",
            "jpeg",
            "png",
            "mp3",
            "mp4",
            "zip"

        }

        # Don't treat ZIP commands as extension search

        if not any(

            keyword in text

            for keyword in (

                "compress",

                "extract",

                "unzip",

                "zip file",

                "create zip"

            )

        ):

            if any(
                extension in text
                for extension in file_extensions
            ) or any(
                word in text
                for word in (
                    "word",
                    "excel",
                    "powerpoint",
                    "ppt",
                    "text"
                )
            ):

                if any(
                    keyword in text
                    for keyword in (
                        "file",
                        "files",
                        "find",
                        "search",
                        "show",
                        "list"
                    )
                ):

                    return "search_extension"

        # ---------------------------------
        # Search By Size
        # ---------------------------------

        if any(
            keyword in text
            for keyword in (
                "larger than",
                "bigger than",
                "greater than",
                "above",
                "over",
                "under",
                "less than",
                "smaller than",
                "size"
            )
        ):

            return "search_size"

        # ---------------------------------
        # Search By Date
        # ---------------------------------

        if any(

            keyword in text

            for keyword in (

                "today",

                "yesterday",

                "last week",

                "last month",

                "recent",

                "modified",

                "created"

            )

        ):

            return "search_date"

        # ---------------------------------
        # Google Search
        # ---------------------------------

        if (

            text.startswith("google search")

            or

            text.startswith("search google")

            or

            (
                text.startswith("search")
                and
                "file" not in text
            )

            or

            (
                " search " in text
                and
                "file" not in text
            )

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

        # Chrome Profiles

        if (
            "profile" in text
            and
            (
                "open" in text
                or
                "launch" in text
                or
                "start" in text
            )
        ):
            return "open_chrome_profile"

        # Move/Copy commands should be checked
        # before folder detection

        if (
            "move file" in text
            or
            "move this file" in text
            or
            "move document" in text
            or
            "move pdf" in text
        ):

            return "move_file"

        if (
            "copy file" in text
            or
            "copy this file" in text
            or
            "copy document" in text
            or
            "copy pdf" in text
        ):

            return "copy_file"

        # Special Folders

        for folder in self.folder_open_keywords:

            if folder in text:

                return "open_folder"

        # Website

        if "www." in text:

            return "open_website"

        # ---------------------------------
        # Search Extension (Priority)
        # ---------------------------------

        if any(
            command in text
            for command in (

                "find pdf",
                "find word",
                "find excel",
                "find powerpoint",
                "find ppt",
                "find text",
                "find txt",
                "find csv",
                "find image",
                "find images",
                "find photo",
                "find photos",
                "find video",
                "find videos",
                "find music",
                "find audio",

                "search pdf",
                "search word",
                "search excel",
                "search powerpoint",
                "search ppt",
                "search txt",
                "search csv",

                "show pdf",
                "show word",
                "show excel",

                "list pdf",
                "list word",
                "list excel"

            )
        ):
            return "search_extension"

        # ---------------------------------
        # Application Open / Close
        # ---------------------------------

        # Don't launch applications for search commands
        if not any(
            keyword in text
            for keyword in (
                "find",
                "search",
                "show",
                "list",
                "locate"
            )
        ):

            for app in self.application_open_keywords:

                if app in text:

                    if any(

                        keyword in text

                        for keyword in (

                            "close",

                            "exit",

                            "quit",

                            "terminate",

                            "stop"

                        )

                    ):

                        return "close_application"

                    if any(

                        keyword in text

                        for keyword in (

                            "open",

                            "launch",

                            "run",

                            "start"

                        )

                    ):

                        return "launch_application"

                    return "launch_application"

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

        if (

            "copy file" in text

            or

            "copy this file" in text

            or

            "copy document" in text

            or

            "copy pdf" in text

        ):

            return "copy_file"

        if (

            "move file" in text

            or

            "move this file" in text

            or

            "move document" in text

            or

            "move pdf" in text

        ):

            return "move_file"

        # ---------------------------------
        # ZIP / Extract ZIP
        # ---------------------------------

        if (
            "extract zip" in text
            or
            "extract file" in text
            or
            "extract archive" in text
            or
            "extract" in text
            or
            "unzip" in text
            or
            "un zip" in text
            or
            "open zip" in text
        ):

            return "extract_zip"

        if (
            "compress file" in text
            or
            "compress" in text
            or
            "zip file" in text
            or
            "create zip" in text
            or
            "zip this file" in text
            or
            "make zip" in text
            or
            "archive file" in text
        ):

            return "compress_file"

        # ---------------------------------
        # MS Office Automation (Intent Only)
        # ---------------------------------

        if (
            "word" in text
            and
            (
                "new document" in text
                or
                "create document" in text
                or
                "blank document" in text
            )
        ):

            return "create_word_document"


        if (
            "excel" in text
            and
            (
                "new workbook" in text
                or
                "create workbook" in text
                or
                "blank workbook" in text
                or
                "new sheet" in text
            )
        ):

            return "create_excel_workbook"


        if (
            "powerpoint" in text
            or
            "power point" in text
            or
            "ppt" in text
        ):

            if (
                "new presentation" in text
                or
                "create presentation" in text
                or
                "create ppt" in text
                or
                "new ppt" in text
                or
                "blank presentation" in text
            ):

                return "create_powerpoint_presentation"

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

        if (

            "youtube" in text

            and

            "search" in text

        ):

            return "youtube_search"

        # YouTube

        if (

            text.startswith("play")

            or

            "play song" in text

            or

            "play music" in text

            or

            "play video" in text

            or

            " song" in text

            or

            " music" in text

        ):

            return "play_youtube"

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

        # Clipboard Commands

        if (

            "copy selected" in text

            or

            "copy the selected" in text

            or

            "copy selected text" in text

            or

            "copy text" in text

            or

            "copy the text" in text

            or

            text == "copy"

            or

            text == "copy it"

        ):

            return "copy"

        if (

            "paste text" in text

            or

            text == "paste"

            or

            text == "paste it"

        ):

            return "paste"

        if (

            "cut text" in text

            or

            text == "cut"

            or

            text == "cut it"

        ):

            return "cut"

        # ---------------------------------
        # Multi-word Commands (Highest Priority)
        # ---------------------------------

        if "select all" in text:
            return "select_all"

        # ---------------------------------
        # Press Commands (Highest Priority)
        # ---------------------------------

        if text.startswith("press"):

            if "enter" in text:
                return "press_enter"

            if "tab" in text:
                return "press_tab"

            if "space" in text:
                return "space"

            if "escape" in text or "esc" in text:
                return "escape"

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

        # Default Open Command

        if (
            text.startswith("open")
            or
            text.startswith("launch")
            or
            text.startswith("run")
        ):
            if "profile" not in text:

                if "file" in text:

                    return "open_file"

                return "launch_application"

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