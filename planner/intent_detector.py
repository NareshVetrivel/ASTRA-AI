"""
Intent Detection Module

This module identifies the user's intent
from the recognized speech text using
keyword and fuzzy matching.
"""

import re

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

    # ==================================================
    # CONTEXT-AWARE AI CHAT ROUTING
    # ==================================================

    def _is_explicit_automation_command(self, text):
        """
        Return True only when the message clearly asks ASTRA
        to perform a desktop action.

        This protects normal conversation from being routed to
        automation merely because words such as "open",
        "close", "copy" or "search" appear inside a
        question or explanation.
        """

        if not text:
            return False

        text = text.strip().lower()

        explicit_patterns = (
            r"^(open|start|run|launch)\b",
            r"^(close|exit|quit|terminate)\b",
            r"^(type|write|copy|paste|cut|undo|redo)\b",
            r"^(click|double click|right click|scroll)\b",
            r"^(minimize|maximize|restore)\b",
            r"^(mute|lock|shutdown|restart|reboot|sleep|logout|signout)\b",
            r"^(take )?screenshot\b",
            r"^(set|increase|decrease|turn) (the )?(volume|brightness)\b",
            r"^(create|delete|rename|move|copy|compress|extract)\b.*\b(file|folder|document|zip|archive)\b",
            r"^(search|google|youtube|play)\b",
            r"^(new tab|close tab|next tab|previous tab|refresh|go back|go forward)\b",
            r"^(press )?(enter|tab|backspace|delete|escape|esc|space|home|end)\b",
            r"^(open )?(settings|task manager|file explorer|camera|control panel|cmd|powershell)\b",
            r"^(start|stop) (screen )?recording\b",
        )

        return any(re.search(pattern, text) for pattern in explicit_patterns)

    def _is_conversational_message(self, text):
        """
        Detect questions, follow-ups and natural conversation.

        The detector intentionally does not need to resolve the
        previous topic itself. Returning ``ai_chat`` sends the message
        to GeminiClient, where the temporary conversation history
        resolves references such as "that", "it", "continue"
        and "what about this?".
        """

        if not text:
            return False

        text = text.strip().lower()

        # Clear questions must never accidentally execute an action.
        question_patterns = (
            r"^(what|who|why|when|where|which|whose|whom|how)\b",
            r"^(enna|enna da|ethu|edhu|yaaru|yaru|yen|en|epdi|eppadi|eppo|engae|enga|ethuku|etharku)\b",
            r"\b(can|could|would|should|is|are|do|does|did|will)\s+(you|i|we|this|that|it)\b",
            r"\b(meaning|difference|compare|explain|describe|define|teach|guide|summary|summarize)\b",
        )

        if any(re.search(pattern, text) for pattern in question_patterns):
            return True

        # Time / date / day queries belong to AI chat so the model can
        # answer directly instead of searching the desktop UI.
        temporal_terms = (
            "time", "date", "day", "today", "tomorrow",
            "yesterday", "kannum", "innaiku", "innikku",
            "naalai", "netru",
        )

        if any(term in text for term in temporal_terms):
            if any(token in text for token in (
                "what", "enna", "ethu", "edhu", "tell",
                "sollu", "solunga", "sollunga", "current",
                "now", "ippo", "ippa", "innaiku", "today",
            )):
                return True

        # Short acknowledgements and follow-ups must retain the active
        # topic through GeminiClient conversation history.
        follow_ups = {
            "why", "how", "then", "continue", "go on",
            "tell me more", "explain more", "what about that",
            "what about this", "and then", "after that",
            "okay then", "seri then", "appo", "aprm",
            "apram", "athuku apram", "idhu enna",
            "athu enna", "adhula enna", "idha explain pannu",
            "atha explain pannu", "continue da",
        }

        if text in follow_ups:
            return True

        # Natural identity, greeting and knowledge requests.
        conversational_phrases = (
            "who are you", "your name", "who created you",
            "creator", "astra-ai", "dheepthi", "hello",
            "hi ", "thanks", "thank you", "nandri",
            "pathi", "pati", "puriyala", "puriya",
            "sollu", "solunga", "sollunga", "detail ah",
            "full detail", "example", "examples",
        )

        return any(phrase in text for phrase in conversational_phrases)

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

        # ==================================================
        # CONTEXT-AWARE CONVERSATION PRIORITY
        # ==================================================
        #
        # Explicit desktop commands keep automation priority.
        # Questions, follow-ups and natural conversation are routed
        # to Gemini so the existing temporary history can resolve
        # the active topic and previous entities.
        # ==================================================

        if not self._is_explicit_automation_command(text):

            if self._is_conversational_message(text):

                return "ai_chat"

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
        # IMPORTANT:
        #
        # Folder operations MUST be detected before
        # generic file operations.
        #
        # This prevents:
        #
        #   rename test folder to demo folder
        #
        # from becoming:
        #
        #   rename_file
        #
        # It must become:
        #
        #   rename_folder
        #
        # ==================================================

        # ==================================================
        # FOLDER OPERATIONS
        # ==================================================

        # ---------------------------------
        # CREATE FOLDER
        # ---------------------------------

        if (
            (
                text.startswith("create ")
                or
                text.startswith("make ")
                or
                text.startswith("new ")
            )
            and
            "folder" in text
        ):

            return "create_folder"

        # ---------------------------------
        # RENAME FOLDER
        # ---------------------------------
        #
        # Supports:
        #
        # rename folder test to demo
        # rename test folder to demo folder
        # rename the test folder to demo folder
        # rename folder test into demo
        # rename test folder 2 demo folder
        # rename folder, test folder, 2 demo folder
        #
        # ---------------------------------

        if (
            "rename" in text
            and
            "folder" in text
            and
            (
                " to " in f" {text} "
                or
                " into " in f" {text} "
                or
                " 2 " in f" {text} "
            )
        ):

            return "rename_folder"

        # ---------------------------------
        # DELETE FOLDER
        # ---------------------------------

        if (
            (
                text.startswith("delete ")
                or
                text.startswith("remove ")
            )
            and
            "folder" in text
        ):

            return "delete_folder"

        # ---------------------------------
        # MOVE FOLDER
        # ---------------------------------
        #
        # Supports:
        #
        # move folder source to destination
        # move source folder to destination
        # move the source folder into destination
        #
        # ---------------------------------

        if (
            text.startswith("move ")
            and
            "folder" in text
            and
            (
                " to " in f" {text} "
                or
                " into " in f" {text} "
                or
                " 2 " in f" {text} "
            )
        ):

            return "move_folder"

        # ---------------------------------
        # COPY FOLDER
        # ---------------------------------
        #
        # Supports:
        #
        # copy folder source to destination
        # copy source folder to destination
        # copy the source folder into destination
        #
        # ---------------------------------

        if (
            text.startswith("copy ")
            and
            "folder" in text
            and
            (
                " to " in f" {text} "
                or
                " into " in f" {text} "
                or
                " 2 " in f" {text} "
            )
        ):

            return "copy_folder"

        # ---------------------------------
        # OPEN FOLDER
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

        # ==================================================
        # FILE OPERATIONS
        # ==================================================

        # ---------------------------------
        # RENAME FILE
        # ---------------------------------

        if (
            text.startswith("rename ")
            and
            (
                " to " in f" {text} "
                or
                " into " in f" {text} "
                or
                " 2 " in f" {text} "
            )
            and
            "folder" not in text
        ):

            return "rename_file"

        # Explicit file rename

        if (
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
            text.startswith("copy ")
            and
            (
                " to " in f" {text} "
                or
                " into " in f" {text} "
                or
                " 2 " in f" {text} "
            )
            and
            "folder" not in text
        ):

            return "copy_file"

        if (
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
            text.startswith("move ")
            and
            (
                " to " in f" {text} "
                or
                " into " in f" {text} "
                or
                " 2 " in f" {text} "
            )
            and
            "folder" not in text
        ):

            return "move_file"

        if (
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
        # CREATE FILE
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
            and
            "folder" not in text
        ):

            return "create_file"

        # ---------------------------------
        # DELETE FILE
        # ---------------------------------

        if (
            (
                text.startswith("delete ")
                or
                text.startswith("remove ")
            )
            and
            "file" in text
            and
            "folder" not in text
        ):

            return "delete_file"

        # ==================================================
        # ZIP / FILE ARCHIVE OPERATIONS
        # ==================================================

        # ---------------------------------
        # EXTRACT ZIP
        # ---------------------------------

        if (
            "extract zip" in text
            or
            "extract file" in text
            or
            "extract archive" in text
            or
            "unzip" in text
            or
            "un zip" in text
            or
            "open zip" in text
        ):

            return "extract_zip"

        # ---------------------------------
        # COMPRESS FILE
        # ---------------------------------

        if (
            "compress file" in text
            or
            "compress " in text
            or
            text == "compress"
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

        # ==================================================
        # EMPTY RECYCLE BIN
        # ==================================================

        if (
            "empty recycle bin" in text
            or
            "clear recycle bin" in text
        ):

            return "empty_recycle_bin"

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

        # ==================================================
        # MICROSOFT WORD V1 INTENT DETECTION
        # ==================================================
        #
        # WordAgent owns the actual Word automation. IntentDetector
        # only converts natural-language commands into the operation
        # identifiers defined in productivity_agent.word.commands.
        #
        # IMPORTANT:
        # - Word-specific phrases are checked before generic commands.
        # - Generic "type", "copy", "paste", etc. are NOT hijacked unless
        #   the user clearly refers to a Word document/content operation.
        # - "open word" remains a WordAgent operation.
        # ==================================================

        word_context = any(
            token in text
            for token in (
                "word",
                "ms word",
                "microsoft word",
                "word document",
                "word file",
                "document",
                "docx",
            )
        )

        # --------------------------------------------------
        # Word application lifecycle
        # --------------------------------------------------

        if word_context:
            if (
                text in {
                    "word",
                    "ms word",
                    "microsoft word",
                    "open word",
                    "open ms word",
                    "open microsoft word",
                    "launch word",
                    "launch ms word",
                    "launch microsoft word",
                    "start word",
                    "start ms word",
                    "start microsoft word",
                }
            ):
                return "open_word"

            if any(
                phrase in text
                for phrase in (
                    "close word",
                    "close ms word",
                    "close microsoft word",
                    "exit word",
                    "quit word",
                    "terminate word",
                )
            ):
                return "close_word"

        # --------------------------------------------------
        # Create / open / save / close document
        # --------------------------------------------------

        if (
            word_context
            and
            (
                "new document" in text
                or "create document" in text
                or "create a document" in text
                or "create the document" in text
                or "blank document" in text
                or "new word document" in text
                or "create word document" in text
                or "create a word document" in text
            )
        ):
            return "create_blank_document"

        if (
            word_context
            and
            (
                "open existing document" in text
                or "open existing word document" in text
                or "open document" in text
                or "open a document" in text
                or "open the document" in text
                or "open docx" in text
            )
        ):
            return "open_existing_document"

        if word_context:
            if (
                text in {"save", "save document", "save the document",
                         "save word document", "save this document"}
                or "save current document" in text
            ):
                return "save"

            if (
                "save as" in text
                or "save document as" in text
                or "save the document as" in text
            ):
                return "save_as"

            if (
                "save docx" in text
                or "save as docx" in text
                or "save document as docx" in text
                or "save word document as docx" in text
            ):
                return "save_docx"

            if (
                "save pdf" in text
                or "save as pdf" in text
                or "save document as pdf" in text
                or "export document to pdf" in text
                or "export as pdf" in text
            ):
                return "save_pdf"

            if (
                "close current document" in text
                or "close the current document" in text
                or "close document" in text
                or "close the document" in text
            ):
                return "close_current_document"

            if (
                "create document named" in text
                or "create document called" in text
                or "create word file named" in text
                or "create word file called" in text
                or "create specified filename" in text
            ):
                return "create_specified_filename"

            if (
                "read existing document" in text
                or "read the existing document" in text
                or "read existing word document" in text
            ):
                return "read_existing_document"

        # --------------------------------------------------
        # Word content operations
        # --------------------------------------------------

        if word_context:
            if (
                "add text at cursor" in text
                or "add text to cursor" in text
                or "insert text at cursor" in text
                or "type at cursor" in text
            ):
                return "add_text_at_cursor"

            if (
                "replace content" in text
                or "replace the content" in text
                or "replace document content" in text
                or "replace all content" in text
            ):
                return "replace_content"

            if (
                "read document" in text
                or "read the document" in text
                or "read word document" in text
                or "read this document" in text
            ):
                return "read_document"

            if (
                "clear document" in text
                or "clear the document" in text
                or "clear document content" in text
                or "clear all document content" in text
            ):
                return "clear_document"

            if (
                "select all in word" in text
                or "select all text in word" in text
                or "select all document text" in text
                or "select all in document" in text
            ):
                return "select_all"

            if "copy text from document" in text or "copy selected text in word" in text:
                return "copy"

            if "cut text from document" in text or "cut selected text in word" in text:
                return "cut"

            if "paste into document" in text or "paste into word" in text:
                return "paste"

            if (
                text.startswith("type ")
                and word_context
            ):
                return "type_text"

            if (
                text.startswith("write ")
                and word_context
            ):
                return "type_text"

        # --------------------------------------------------
        # Word formatting
        # --------------------------------------------------

        if word_context:
            if "strikethrough" in text or "strike through" in text:
                return "strikethrough"

            if "underline" in text or "underlined" in text:
                return "underline"

            if "italic" in text or "italics" in text:
                return "italic"

            if (
                "bold" in text
                or "make it bold" in text
                or "make this bold" in text
            ):
                return "bold"

            if "font size" in text or "text size" in text:
                return "font_size"

            if (
                "font " in f" {text} "
                or "change font" in text
                or "set font" in text
            ):
                return "font"

            if (
                "text color" in text
                or "font color" in text
                or "change text colour" in text
                or "font colour" in text
            ):
                return "text_color"

            if "highlight" in text or "highlight text" in text:
                return "highlight"

            if "align left" in text or "left align" in text:
                return "align_left"

            if "align center" in text or "align centre" in text or "center align" in text:
                return "align_center"

            if "align right" in text or "right align" in text:
                return "align_right"

            if "justify" in text or "justify text" in text:
                return "justify"

            if "line spacing" in text:
                return "line_spacing"

            if "paragraph spacing" in text:
                return "paragraph_spacing"

            if (
                "indentation" in text
                or "indent paragraph" in text
                or "indent the paragraph" in text
            ):
                return "indentation"

            if "bullets" in text or "bullet list" in text or "make bullets" in text:
                return "bullets"

            if "numbering" in text or "numbered list" in text or "make numbered list" in text:
                return "numbering"

        # --------------------------------------------------
        # Word styles
        # --------------------------------------------------

        if word_context:
            if (
                text == "title"
                or "apply title style" in text
                or "make it title" in text
                or "make this title" in text
            ):
                return "title"

            if (
                "heading 1" in text
                or "heading one" in text
                or "apply heading 1" in text
                or "make it heading 1" in text
            ):
                return "heading_1"

            if (
                text == "normal"
                or "normal style" in text
                or "apply normal style" in text
            ):
                return "normal"

            if "document style" in text or "change document style" in text:
                return "document_style"

        # --------------------------------------------------
        # Word tables
        # --------------------------------------------------

        if word_context:
            if (
                "read table data" in text
                or "read the table" in text
                or "read table" in text
            ):
                return "read_table_data"

            if (
                "create table" in text
                or "insert table" in text
                or "make a table" in text
                or "make table" in text
            ):
                return "create_table"

            if re.search(r"\brows?\b", text) and re.search(r"\bcolumns?\b", text):
                if "table" in text:
                    return "create_table"

        # --------------------------------------------------
        # Word find / replace
        # --------------------------------------------------

        if word_context:
            if (
                "find and replace" in text
                or "find replace" in text
                or "replace text" in text
                or "replace word" in text
            ):
                return "replace"

            if (
                "find text" in text
                or "find in document" in text
                or "find in word" in text
                or "search document" in text
            ):
                return "find"

        # --------------------------------------------------
        # Word insert operations
        # --------------------------------------------------

        if word_context:
            if (
                "insert image" in text
                or "add image" in text
                or "insert picture" in text
                or "add picture" in text
            ):
                return "image"

            if (
                "insert hyperlink" in text
                or "add hyperlink" in text
                or "insert link" in text
                or "add link to document" in text
            ):
                return "hyperlink"

        # --------------------------------------------------
        # Word document structure
        # --------------------------------------------------

        if word_context:
            if "page break" in text or "insert page break" in text:
                return "page_break"

            if "new page" in text or "insert new page" in text:
                return "new_page"

            if "header" in text or "insert header" in text:
                return "header"

            if "footer" in text or "insert footer" in text:
                return "footer"

            if (
                "page number" in text
                or "insert page number" in text
                or "add page number" in text
            ):
                return "page_number"

            if "margin" in text or "margins" in text or "set margins" in text:
                return "margins"

        # ==================================================
        # END MICROSOFT WORD V1 INTENT DETECTION
        # ==================================================

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