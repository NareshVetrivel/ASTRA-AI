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

        # ---------------------------------
        # AI Conversation Keywords
        # ---------------------------------

        self.ai_keywords = {

            # Question words
            "what",
            "who",
            "why",
            "when",
            "where",
            "which",
            "whose",
            "whom",
            "how",

            # AI Requests
            "explain",
            "describe",
            "define",
            "compare",
            "difference",
            "meaning",
            "guide",
            "teach",
            "learn",
            "study",
            "example",
            "examples",
            "summary",
            "summarize",

            # Natural Conversation
            "tell me",
            "tell",
            "about",
            "say",
            "chat",
            "talk",
            "conversation",
            "question",
            "help",

            # Knowledge
            "information",
            "details",
            "history",
            "advantages",
            "disadvantages",
            "benefits",
            "uses",
            "purpose",

            # Programming
            "python",
            "java",
            "c++",
            "c#",
            "javascript",
            "html",
            "css",
            "sql",

            # AI
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "neural network",

            # Tanglish
            "pathi",

            "pati",

            "enna",

            "enna da",

            "epdi",

            "eppadi",

            "yen",

            "ethuku",

            "etharku",

            "sollu",

            "solunga",

            "sollunga",

            "puriyala",

            "puriya",

            "purinjikanum",

            "vilakkam",

            "explain",

            "explain pannu",

            "explain pannunga",

            "detail ah",

            "full detail",

            "full explain",

            "meaning",

            "artham",

            "history",

            "future",

            "use",

            "uses"

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

            # Audio

            "mute": "mute",

            "volume": "volume_up",

            "volumeup": "volume_up",

            "volumedown": "volume_down",

            # Display

            "brightness": "set_brightness",

            # Power

            "shutdown": "shutdown",

            "restart": "restart",

            "reboot": "restart",

            "sleep": "sleep",

            "logout": "sign_out",

            "signout": "sign_out",

            # Windows Utilities

            "settings": "open_settings",

            "task": "open_task_manager",

            "explorer": "open_file_explorer",

            "cmd": "open_cmd",

            "powershell": "open_powershell",

            "control": "open_control_panel",

            # Camera

            "camera": "open_camera",

            "photo": "capture_photo",

            "screenshot": "take_screenshot",

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

            "file": "open_file",

            # Screen Recording

            "record": "start_screen_recording",

            "recording": "start_screen_recording",
        }

        self.tanglish_command_map = {

            "thorakka": "open",
            "thorak": "open",
            "open pannu": "open",

            "moodu": "close",
            "close pannu": "close",

            "theda": "search",
            "thedu": "search",
            "thedi": "search",

            "kaatu": "show",

            "podu": "play",

            "uruvakku": "create",

            "azhichidu": "delete",

            "maathu": "rename",

            "nagarthu": "move",

            "copy pannu": "copy",

            "start pannu": "start",

            "stop pannu": "stop",
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

        # Ignore very short accidental speech

        if len(text.strip()) <= 1:

            return None

        text = (
            text
            .lower()
            .strip()
            .rstrip(".,!?")
        )

        # Remove duplicate filler words

        fillers = {

            "uh",

            "um",

            "hmm",

            "mmm",

            "ah",

            "oh"

        }

        words = [

            word

            for word in text.split()

            if word not in fillers

        ]

        text = " ".join(words)

        # ---------------------------------
        # Whisper Corrections
        # ---------------------------------

        text = (
            text
            .replace("bdf", "pdf")
            .replace("estaday", "yesterday")
            .replace("study", "today")
            .replace("you tube", "youtube")
            .replace("you to", "youtube")
            .replace("g mail", "gmail")
            .replace("power point", "powerpoint")
            .replace("note pad", "notepad")
            .replace("command promt", "command prompt")
            .replace("vs code", "vscode")
            .replace("chrome browser", "chrome")
            .replace("google chrome browser", "chrome")
            .replace("u tube", "youtube")
            .replace("you too", "youtube")
            .replace("excel sheet", "excel")
            .replace("power point presentation", "powerpoint")
            .replace("visual studio", "vscode")
            .replace("c plus plus", "c++")
            .replace("artificial intelligent", "artificial intelligence")
        )

        # remove duplicate spaces
        text = " ".join(text.split())

        for old, new in self.tanglish_command_map.items():

            text = text.replace(old, new)

        # ---------------------------------
        # Voice / Whisper Punctuation Cleanup
        # ---------------------------------
        #
        # Whisper may return:
        #
        #   create, file
        #   create. file
        #   create - file
        #
        # Convert punctuation into spaces so
        # filesystem commands are detected
        # reliably.
        # ---------------------------------

        import re

        text = re.sub(
            r"[,\.;:!?]+",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        # ==================================================
        # HIGH PRIORITY FILE SYSTEM COMMANDS
        # ==================================================
        #
        # These commands must be detected BEFORE:
        #
        #   - application detection
        #   - folder special-name detection
        #   - search detection
        #   - fuzzy intent matching
        #
        # This prevents commands such as:
        #
        #   create, file demo
        #   create a file demo
        #   make a file demo
        #
        # from being incorrectly classified as
        # open_file or another intent.
        # ==================================================

        # ---------------------------------
        # STRUCTURAL FILE COMMANDS
        # ---------------------------------
        #
        # Voice commands often omit the literal word "file":
        #
        #   copy astro test to desktop
        #   move resume to documents
        #
        # Also, the filename can appear between the verb and
        # the word "file":
        #
        #   rename astra file 2 astra demo
        #
        # These must be detected before generic "open/file"
        # handling and before clipboard "copy".
        # ---------------------------------

        # RENAME FILE
        if (
            text.startswith("rename ")
            and (
                " to " in f" {text} "
                or " 2 " in f" {text} "
                or " into " in f" {text} "
            )
            and (
                "file" in text
                or "document" in text
            )
        ):
            return "rename_file"

        # COPY FILE
        if (
            text.startswith("copy ")
            and (
                " to " in f" {text} "
                or " into " in f" {text} "
                or " 2 " in f" {text} "
            )
            and "folder" not in text
        ):
            return "copy_file"

        # MOVE FILE
        if (
            text.startswith("move ")
            and (
                " to " in f" {text} "
                or " into " in f" {text} "
                or " 2 " in f" {text} "
            )
            and "folder" not in text
        ):
            return "move_file"

        # ---------------------------------
        # CREATE FILE
        # ---------------------------------
        #
        # Supports:
        #
        # create file demo
        # create a file demo
        # create the file demo
        # create a test file demo
        # create a new file demo
        # make file demo
        # make a file demo
        # make a test file demo
        # new file demo
        # new a file demo
        #
        # IMPORTANT:
        # The command must start with create/make/new
        # and contain the word "file".
        #
        # This prevents unrelated sentences such as:
        #
        #   open file demo
        #   find file demo
        #
        # from becoming create_file.
        # ---------------------------------

        create_file_starters = (
            "create ",
            "make ",
            "new ",
        )

        if (
            text.startswith(create_file_starters)
            and
            "file" in text.split()
        ):

            return "create_file"

        # ---------------------------------
        # DELETE FILE
        # ---------------------------------

        if (
            "delete file" in text
            or
            "delete a file" in text
            or
            "delete the file" in text
            or
            "remove file" in text
            or
            "remove a file" in text
            or
            "remove the file" in text
        ):

            return "delete_file"

        # ---------------------------------
        # RENAME FILE
        # ---------------------------------

        if (
            (
                text.startswith("rename ")
                and (
                    " to " in f" {text} "
                    or " 2 " in f" {text} "
                    or " into " in f" {text} "
                )
            )
            or
            "rename file" in text
            or
            "rename a file" in text
            or
            "rename the file" in text
        ):

            return "rename_file"

        # ---------------------------------
        # COPY FILE
        # ---------------------------------

        if (
            (
                text.startswith("copy ")
                and (
                    " to " in f" {text} "
                    or " into " in f" {text} "
                    or " 2 " in f" {text} "
                )
                and "folder" not in text
            )
            or
            "copy file" in text
            or
            "copy a file" in text
            or
            "copy the file" in text
            or
            "copy this file" in text
            or
            "copy document" in text
            or
            "copy pdf" in text
        ):

            return "copy_file"

        # ---------------------------------
        # MOVE FILE
        # ---------------------------------

        if (
            (
                text.startswith("move ")
                and (
                    " to " in f" {text} "
                    or " into " in f" {text} "
                    or " 2 " in f" {text} "
                )
                and "folder" not in text
            )
            or
            "move file" in text
            or
            "move a file" in text
            or
            "move the file" in text
            or
            "move this file" in text
            or
            "move document" in text
            or
            "move pdf" in text
        ):

            return "move_file"

        # ---------------------------------
        # CREATE FOLDER
        # ---------------------------------

        if (
            "create folder" in text
            or
            "create a folder" in text
            or
            "create the folder" in text
            or
            "create your folder" in text
            or
            "make folder" in text
            or
            "make a folder" in text
            or
            "make the folder" in text
            or
            "make your folder" in text
            or
            "new folder" in text
            or
            "new a folder" in text
            or
            "new the folder" in text
            or
            "new your folder" in text
        ):

            return "create_folder"

        # ---------------------------------
        # RENAME FOLDER
        # ---------------------------------

        if (
            "rename folder" in text
            or
            "rename a folder" in text
            or
            "rename the folder" in text
            or
            "rename your folder" in text
        ):

            return "rename_folder"

        # ---------------------------------
        # DELETE FOLDER
        # ---------------------------------

        if (
            "delete folder" in text
            or
            "delete a folder" in text
            or
            "delete the folder" in text
            or
            "delete your folder" in text
            or
            "remove folder" in text
            or
            "remove a folder" in text
            or
            "remove the folder" in text
            or
            "remove your folder" in text
        ):

            return "delete_folder"

        # ---------------------------------
        # MOVE FOLDER
        # ---------------------------------

        if (
            "move folder" in text
            or
            "move a folder" in text
            or
            "move the folder" in text
            or
            "move your folder" in text
        ):

            return "move_folder"

        # ---------------------------------
        # COPY FOLDER
        # ---------------------------------

        if (
            "copy folder" in text
            or
            "copy a folder" in text
            or
            "copy the folder" in text
            or
            "copy your folder" in text
        ):

            return "copy_folder"

        # ---------------------------------
        # System Automation Priority
        # ---------------------------------

        # Exact Volume Control

        if (
            "set volume" in text
            or
            "volume to" in text
            or
            "volume at" in text
            or
            "volume level" in text
        ):

            return "set_volume"

        # Brightness Up

        if (
            "brightness up" in text
            or
            "increase brightness" in text
            or
            "raise brightness" in text
            or
            "brighten screen" in text
            or
            "brighten display" in text
        ):

            return "brightness_up"

        # Brightness Down

        if (
            "brightness down" in text
            or
            "decrease brightness" in text
            or
            "lower brightness" in text
            or
            "dim screen" in text
            or
            "dim display" in text
        ):

            return "brightness_down"

        # Exact Brightness Control

        if (
            "set brightness" in text
            or
            "brightness to" in text
            or
            "brightness at" in text
            or
            "brightness level" in text
        ):

            return "set_brightness"

        # Shutdown

        if (
            "shutdown" in text
            or
            "shut down" in text
            or
            "turn off computer" in text
            or
            "turn off pc" in text
            or
            "power off computer" in text
            or
            "power off pc" in text
        ):

            return "shutdown"

        # Restart

        if (
            "restart computer" in text
            or
            "restart pc" in text
            or
            "restart system" in text
            or
            "reboot computer" in text
            or
            "reboot pc" in text
            or
            "reboot system" in text
        ):

            return "restart"

        # Sleep

        if (
            "sleep computer" in text
            or
            "sleep pc" in text
            or
            "sleep system" in text
            or
            "put computer to sleep" in text
            or
            "put pc to sleep" in text
            or
            "go to sleep" in text
        ):

            return "sleep"

        # Sign Out

        if (
            "sign out" in text
            or
            "signout" in text
            or
            "log out" in text
            or
            "logout" in text
        ):

            return "sign_out"

        # Open Settings

        if (
            "open settings" in text
            or
            "open windows settings" in text
            or
            "windows settings" in text
            or
            "system settings" in text
        ):

            return "open_settings"

        # Open CMD

        if (
            "open cmd" in text
            or
            "launch cmd" in text
            or
            "start cmd" in text
            or
            "open command prompt" in text
            or
            "launch command prompt" in text
            or
            "start command prompt" in text
        ):

            return "open_cmd"

        # Open PowerShell

        if (
            "open powershell" in text
            or
            "launch powershell" in text
            or
            "start powershell" in text
            or
            "open power shell" in text
            or
            "launch power shell" in text
            or
            "start power shell" in text
        ):

            return "open_powershell"

        # Open Control Panel

        if (
            "open control panel" in text
            or
            "launch control panel" in text
            or
            "start control panel" in text
        ):

            return "open_control_panel"

        # ---------------------------------
        # Start Screen Recording
        # ---------------------------------

        if (
            "start screen recording" in text
            or
            "start screen record" in text
            or
            "begin screen recording" in text
            or
            "begin screen record" in text
            or
            "record screen" in text
            or
            "record my screen" in text
            or
            "start recording screen" in text
            or
            "start screen capture" in text
        ):

            return "start_screen_recording"

        # ---------------------------------
        # Stop Screen Recording
        # ---------------------------------

        if (
            "stop screen recording" in text
            or
            "stop screen record" in text
            or
            "end screen recording" in text
            or
            "end screen record" in text
            or
            "finish screen recording" in text
            or
            "stop recording screen" in text
            or
            "stop screen capture" in text
        ):

            return "stop_screen_recording"

        # Open Camera

        if (
            "open camera" in text
            or
            "launch camera" in text
            or
            "start camera" in text
            or
            "open webcam" in text
            or
            "launch webcam" in text
        ):

            return "open_camera"

        # Capture Photo

        if (
            "take photo" in text
            or
            "take a photo" in text
            or
            "capture photo" in text
            or
            "capture a photo" in text
            or
            "take picture" in text
            or
            "take a picture" in text
            or
            "capture picture" in text
            or
            "capture a picture" in text
            or
            "take selfie" in text
            or
            "capture selfie" in text
        ):

            return "capture_photo"

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
            # Exact Browser Commands
            # ---------------------------------

            if text in ("youtube", "open youtube"):
                return "open_youtube"

            if text in ("google", "open google"):
                return "open_google"

            if text in ("gmail", "open gmail"):
                return "open_website"

            if text in ("github", "open github"):
                return "open_website"

            # ---------------------------------
            # Browser Website Detection
            # ---------------------------------

            if any(
                site in text
                for site in [
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
                ]
            ):

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

        # ---------------------------------
        # Folder Commands
        # ---------------------------------
        #
        # IMPORTANT:
        # Specific folder actions MUST be checked
        # before generic special-folder detection.
        #
        # This must support natural speech such as:
        #
        #   create folder
        #   create a folder
        #   create the folder
        #   create your folder
        #   make a folder
        #   make the folder
        #   new folder
        #   create folder as test
        #   create a folder named test
        #   create the folder called test
        #
        # Generic "folder" detection MUST NOT run
        # before these checks.
        # ---------------------------------

        # ---------------------------------
        # CREATE FOLDER
        # ---------------------------------

        if (
            "create folder" in text
            or
            "create a folder" in text
            or
            "create the folder" in text
            or
            "create your folder" in text
            or
            "make folder" in text
            or
            "make a folder" in text
            or
            "make the folder" in text
            or
            "make your folder" in text
            or
            "new folder" in text
            or
            "new a folder" in text
            or
            "new the folder" in text
            or
            "new your folder" in text
        ):

            return "create_folder"


        # ---------------------------------
        # RENAME FOLDER
        # ---------------------------------

        if (
            "rename folder" in text
            or
            "rename a folder" in text
            or
            "rename the folder" in text
            or
            "rename your folder" in text
        ):

            return "rename_folder"


        # ---------------------------------
        # DELETE FOLDER
        # ---------------------------------

        if (
            "delete folder" in text
            or
            "delete a folder" in text
            or
            "delete the folder" in text
            or
            "delete your folder" in text
            or
            "remove folder" in text
            or
            "remove a folder" in text
            or
            "remove the folder" in text
            or
            "remove your folder" in text
        ):

            return "delete_folder"


        # ---------------------------------
        # MOVE FOLDER
        # ---------------------------------

        if (
            "move folder" in text
            or
            "move a folder" in text
            or
            "move the folder" in text
            or
            "move your folder" in text
        ):

            return "move_folder"


        # ---------------------------------
        # COPY FOLDER
        # ---------------------------------

        if (
            "copy folder" in text
            or
            "copy a folder" in text
            or
            "copy the folder" in text
            or
            "copy your folder" in text
        ):

            return "copy_folder"


        # ---------------------------------
        # EMPTY RECYCLE BIN
        # ---------------------------------

        if (
            "empty recycle bin" in text
            or
            "clear recycle bin" in text
        ):

            return "empty_recycle_bin"


        # ---------------------------------
        # OPEN FOLDER
        # ---------------------------------
        #
        # Generic folder opening is checked
        # ONLY after all specific folder actions.
        # ---------------------------------

        if (
            "open folder" in text
            or
            "open a folder" in text
            or
            "open the folder" in text
            or
            "open your folder" in text
        ):

            return "open_folder"


        # ---------------------------------
        # Special Folders
        # ---------------------------------
        #
        # Examples:
        #
        #   open desktop
        #   open documents
        #   open downloads
        #   open pictures
        #   open videos
        #   open music
        #   open recycle bin
        #
        # These are checked AFTER specific
        # folder commands.
        # ---------------------------------

        for folder in self.folder_open_keywords:

            if folder in text:

                return "open_folder"


        # ---------------------------------
        # Website
        # ---------------------------------

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

                if (
                    app == text
                    or
                    f"open {app}" in text
                    or
                    f"launch {app}" in text
                    or
                    f"run {app}" in text
                    or
                    f"start {app}" in text
                ):

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

        if (
            "rename file" in text
            or
            (
                text.startswith("rename ")
                and (
                    " to " in f" {text} "
                    or " 2 " in f" {text} "
                    or " into " in f" {text} "
                )
            )
        ):

            return "rename_file"

        if (
            (
                text.startswith("copy ")
                and (
                    " to " in f" {text} "
                    or " into " in f" {text} "
                    or " 2 " in f" {text} "
                )
                and "folder" not in text
            )
            or
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
            (
                text.startswith("move ")
                and (
                    " to " in f" {text} "
                    or " into " in f" {text} "
                    or " 2 " in f" {text} "
                )
                and "folder" not in text
            )
            or
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

        # ---------------------------------
        # Volume Up
        # ---------------------------------

        if (
            "volume up" in text
            or "increase volume" in text
            or "raise volume" in text
        ):

            return "volume_up"


        # ---------------------------------
        # Volume Down
        # ---------------------------------

        if (
            "volume down" in text
            or "decrease volume" in text
            or "lower volume" in text
        ):

            return "volume_down"


        # ---------------------------------
        # Mute
        # ---------------------------------

        if (
            "mute" in text
            or "mute audio" in text
            or "turn off sound" in text
        ):

            return "mute"


        # ---------------------------------
        # Lock Screen
        # ---------------------------------

        if (
            "lock screen" in text
            or "lock computer" in text
            or "lock my pc" in text
            or "lock system" in text
        ):

            return "lock_screen"


        # ---------------------------------
        # Screenshot
        # ---------------------------------

        if (
            "take screenshot" in text
            or "screen shot" in text
            or "capture screen" in text
            or "take screen shot" in text
        ):

            return "take_screenshot"


        # ---------------------------------
        # Task Manager
        # ---------------------------------

        if "task manager" in text:

            return "open_task_manager"


        # ---------------------------------
        # File Explorer
        # ---------------------------------

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
        # Natural AI Questions
        # ---------------------------------

        question_patterns = (

            "what is",

            "who is",

            "where is",

            "when is",

            "why is",

            "how to",

            "how does",

            "tell me",

            "can you explain",

            "please explain",

            "explain",

            "define",

            "difference between",

            "compare",

            "python pathi",

            "java pathi",

            "ai pathi",

            "machine learning pathi",

            "deep learning pathi",

            "enna",

            "epdi",

            "yen"

        )

        if any(pattern in text for pattern in question_patterns):

            return "ai_chat"

        # ---------------------------------
        # AI Conversation
        # ---------------------------------

        if any(
            keyword in text
            for keyword in self.ai_keywords
        ):
            return "ai_chat"

        automation_words = {

            "open",
            "close",
            "launch",
            "run",
            "start",
            "delete",
            "create",
            "rename",
            "copy",
            "move",
            "search",
            "find",
            "show",
            "list",
            "compress",
            "extract",
            "play",

            "browser",

            "youtube",

            "google",

            "chrome",

            "edge",

            "folder",

            "file",

            "notepad",

            "word",

            "excel",

            "powerpoint",

            "desktop",

            "downloads",

            "documents",

            "calculator",

            "paint",

            "explorer"

        }

        if (

            len(text.split()) >= 5

            and

            text.endswith("?")

            or

            any(

                word in text

                for word in (

                    "explain",

                    "describe",

                    "why",

                    "what",

                    "how",

                    "meaning",

                    "compare",

                    "difference"

                )

            )

        ):

            return "ai_chat"

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

            scorer=fuzz.ratio

        )

        if best_match:

            keyword, score, _ = best_match

            if score >= 92:

                print(

                    f"Intent Fuzzy Match : "

                    f"{keyword} ({score:.1f}%)"

                )

                return self.intent_keywords[keyword]

        # ---------------------------------
        # No Match
        # ---------------------------------

        # Very small unknown text

        if len(text.split()) <= 2:

            return None

        return "ai_chat"