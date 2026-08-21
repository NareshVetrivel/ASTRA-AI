"""
Entity Extraction Module

This module identifies application names
from the SQLite database using
RapidFuzz matching.

It also extracts file search queries
for File Finder.

ASTRA-AI V1
"""

import re

from rapidfuzz import process, fuzz

from database.database_manager import DatabaseManager


class EntityExtractor:
    """
    Extract application names
    and file names.
    """

    def __init__(self):

        self.database = DatabaseManager()

        # ---------------------------------
        # Special Folders
        # ---------------------------------

        self.special_folders = {

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
        # Common Websites
        # ---------------------------------

        self.websites = {

            "google": "google.com",

            "youtube": "youtube.com",

            "gmail": "gmail.com",

            "github": "github.com",

            "stackoverflow": "stackoverflow.com",

            "chatgpt": "chat.openai.com",

            "wikipedia": "wikipedia.org",

            "amazon": "amazon.in",

            "flipkart": "flipkart.com",

            "linkedin": "linkedin.com",

            "instagram": "instagram.com",

            "facebook": "facebook.com",

            "twitter": "x.com"

        }

        # ---------------------------------
        # Chrome Profiles
        # ---------------------------------

        self.chrome_profiles = {

            "naresh": "Default",

            "naresh s": "Default",

            "nares": "Default",

            "nareesh": "Default",

            "naresh profile": "Default",

            "naresh senthil": "Profile 1",

            "college": "Profile 1",

            "college profile": "Profile 1",

            "ragxii": "Profile 12",

            "ragxii profile": "Profile 12"
        }

        # ---------------------------------
        # System Application Aliases
        # ---------------------------------

        self.system_applications = {

            "camera": "WindowsCamera.exe",
            "camera app": "WindowsCamera.exe",
            "camera application": "WindowsCamera.exe",

            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "command prompt application": "cmd.exe",

            "powershell": "powershell.exe",
            "power shell": "powershell.exe",
            "windows powershell": "powershell.exe",

            "task manager": "Taskmgr.exe",
            "taskmanager": "Taskmgr.exe",

            "file explorer": "explorer.exe",
            "windows explorer": "explorer.exe",
            "explorer": "explorer.exe",

            "settings": "SystemSettings.exe",
            "settings app": "SystemSettings.exe",

        }

    def normalize_text(
        self,
        text
    ):
        """
        Normalize common STT mistakes.
        """

        if not text:

            return text

        text = f" {text.lower().strip()} "

        replacements = {

            # ---------------------------------
            # Numbers / STT
            # ---------------------------------

            # IMPORTANT:
            # Do NOT globally convert numeric "2" to "to".
            #
            # "2" can be a real part of a filename/folder name:
            # test 2
            # project 2
            # folder 2
            #
            # Rename/copy/move extractors handle STT "2" contextually.

            " too ": " to ",
            " tu ": " to ",

            # ---------------------------------
            # Common Whisper Mistakes
            # ---------------------------------

            "reach": "search",
            "serch": "search",
            "herch": "search",
            "arch": "search",
            "searchh": "search",

            "fined": "find",
            "finds": "find",

            "fence": "files",
            "filess": "files",

            "jpd": "pdf",
            "p d f": "pdf",

            "doc x": "docx",

            "power point": "powerpoint",

            "node pad": "notepad",
            "north pad": "notepad",
            "note pad": "notepad",
            "note that": "notepad",

            "m s word": "word",
            "ms word": "word",

            "excel sheet": "excel",
            "excel file": "excel",

            "ppt file": "ppt",
            "word file": "word",

            "study": "today",
            "estaday": "yesterday",
            "yesterdaye": "yesterday",
            "esther day": "yesterday",

            "this weak": "this week",
            "last v": "last week",

            # ---------------------------------
            # Browser
            # ---------------------------------

            "google chrome": "chrome",
            "chrome browser": "chrome",
            "edge browser": "edge",

            # ---------------------------------
            # Tanglish Browser
            # ---------------------------------

            "kurom": "chrome",
            "krom": "chrome",
            "kuroam": "chrome",

            # ---------------------------------
            # Tanglish Applications
            # ---------------------------------

            "note book": "notepad",
            "note padu": "notepad",
            "notepadu": "notepad",

            "power pointu": "powerpoint",
            "powerpointu": "powerpoint",

            "excelu": "excel",
            "excel ah": "excel",

            "wordu": "word",
            "word ah": "word",

            "chromeu": "chrome",
            "chromela": "chrome",

            "edgeu": "edge",

            "youtubeu": "youtube",

            "googleu": "google",

            # ---------------------------------
            # Tanglish Commands
            # ---------------------------------

            "thorakka": "open",
            "thorak": "open",
            "thorakanum": "open",

            "open pannu": "open",
            "open panra": "open",
            "open pannunga": "open",
            "open pannu da": "open",

            "moodu": "close",
            "moodunga": "close",
            "close pannu": "close",
            "close pannu da": "close",

            "thedu": "search",
            "theda": "search",
            "thedunga": "search",
            "search pannu": "search",
            "search pannu da": "search",
            "search panni kudu": "search",
            "thedi kudu": "search",
            "thedi paaru": "search",

            "kaatu": "show",
            "kaamika": "show",
            "kaaminga": "show",

            "create pannu": "create",

            "delete pannu": "delete",

            "copy pannu": "copy",

            "move pannu": "move",

            "rename pannu": "rename",

            "play pannu": "play",
            "play pannu da": "play",

            "download pannu": "download",

            "install pannu": "install",

            "launch pannu": "launch",

            "start pannu": "start",

            "stop pannu": "stop",

            "poi open": "open",
            "poi open pannu": "open",

            "vechu open": "open",

            "podu": "play",
            "podunga": "play",

            # ---------------------------------
            # Tanglish File Words
            # ---------------------------------

            "pail": "file",
            "payil": "file",

            "foldera": "folder",
            "folder ah": "folder",

            # ---------------------------------
            # Tanglish Websites
            # ---------------------------------

            "youtube la": "youtube",
            "youtube le": "youtube",

            "google la": "google",
            "google le": "google",

            "chrome la": "chrome",
            "chrome le": "chrome",

            "edge la": "edge",
            "edge le": "edge",

            "github la": "github",

            "gmail la": "gmail",

            "instagram la": "instagram",

            "facebook la": "facebook",

            # ---------------------------------
            # Noise Words
            # ---------------------------------

            "please da": "",
            "please dee": "",
            "please di": "",
            "please": "",

            "machi": "",
            "machi da": "",

            "bro": "",
            "nanba": "",

            "appa": "",
            "amma": "",

            "konjam": "",

            "venum": "",
            "venum da": "",
            "venum dee": "",

            "iruku": "",
            "irukka": "",
        }

        for old, new in replacements.items():

            pattern = (
                r"(?<!\w)"
                + re.escape(old)
                + r"(?!\w)"
            )

            text = re.sub(
                pattern,
                new,
                text
            )

        text = " ".join(text.split()).strip()

        # ---------------------------------
        # Remove Common Tamil Particles
        # ---------------------------------

        particles = (
            " la",
            " le",
            " oda",
            " kitta",
            " kuda",
            " ah",
            " va",
            " da",
            " di",
            " pa",
            " ma",
            " nu",
            " ku",
        )

        for particle in particles:

            if text.endswith(particle):

                text = text[:-len(particle)].strip()

        return text

    # --------------------------------------------------
    # Load Applications
    # --------------------------------------------------

    def load_applications(self):
        """
        Load all stored applications.
        """

        applications = {}

        rows = self.database.get_all_applications()

        for name, exe_name, _ in rows:

            applications[name] = exe_name

        return applications

    # --------------------------------------------------
    # Extract Application
    # --------------------------------------------------

    def extract_application(
        self,
        text
    ):
        """
        Extract application name.

        Supports both database applications
        and Windows system applications.
        """

        if not text:

            return None

        # ==============================================================
        # IMPORTANT FILE/FOLDER OPERATION GUARD
        # ==============================================================
        #
        # File-management commands must NEVER be fuzzy-matched against
        # installed applications.
        #
        # Example:
        #     create file demo
        #
        # If the application database contains an application whose
        # name happens to be similar to "demo" (for example V8), the
        # old fuzzy matcher could incorrectly return that application.
        # The dispatcher could then treat the command as an application
        # operation and attempt to open it.
        #
        # For create-file/create-folder commands, application extraction
        # must therefore return None. The dedicated file/folder extractor
        # will handle the actual entity.
        # ==============================================================

        raw_text = str(text).lower().strip()

        normalized_for_guard = self.normalize_text(raw_text)

        file_folder_operation_patterns = (

            # File creation
            r"\\bcreate\\s+(?:a|an|the|my|your|new\\s+)?file\\b",
            r"\\bmake\\s+(?:a|an|the|my|your|new\\s+)?file\\b",
            r"\\bnew\\s+file\\b",

            # Folder creation
            r"\\bcreate\\s+(?:a|an|the|my|your|new\\s+)?folder\\b",
            r"\\bmake\\s+(?:a|an|the|my|your|new\\s+)?folder\\b",
            r"\\bnew\\s+folder\\b",

            # Directory creation
            r"\\bcreate\\s+(?:a|an|the|my|your|new\\s+)?directory\\b",
            r"\\bmake\\s+(?:a|an|the|my|your|new\\s+)?directory\\b",

        )

        for pattern in file_folder_operation_patterns:

            if re.search(
                pattern,
                normalized_for_guard,
                flags=re.IGNORECASE
            ):

                print(
                    "Application Extraction Skipped : "
                    "file/folder creation command detected."
                )

                return None

        text = normalized_for_guard

        # ---------------------------------
        # System Application Aliases
        # ---------------------------------

        system_text = text

        # Remove common command words
        # before checking system aliases.

        command_words = {

            "open",
            "close",
            "launch",
            "start",
            "run",
            "stop",
            "kill",
            "terminate",
            "exit",

        }

        words = [

            word

            for word in system_text.split()

            if word not in command_words

        ]

        system_text = " ".join(words).strip()

        # ---------------------------------
        # Direct System Application Match
        # ---------------------------------

        for alias, executable in (
            self.system_applications.items()
        ):

            if (
                system_text == alias
                or alias in system_text
            ):

                print(
                    f"System Application Match : "
                    f"{alias} -> {executable}"
                )

                return executable

        # ---------------------------------
        # Remove Command Words
        # ---------------------------------

        words = [

            word

            for word in text.split()

            if word not in {

                "open",
                "close",
                "launch",
                "start",
                "run",
                "search",
                "show",
                "find",
                "create",
                "delete",
                "copy",
                "move",
                "rename",
                "play",

            }

        ]

        text = " ".join(words).strip()

        # ---------------------------------
        # Load Database Applications
        # ---------------------------------

        applications = self.load_applications()

        if not applications:

            return None

        # ---------------------------------
        # Exact Match
        # ---------------------------------

        for app_name in applications:

            if app_name in text:

                # Ignore file search commands

                if any(

                    word in text

                    for word in (

                        "find",
                        "search",
                        "show",
                        "locate",
                        "filter"

                    )

                ):

                    continue

                return applications[app_name]

        # ---------------------------------
        # Alias Match
        # ---------------------------------

        words = text.split()

        for word in words:

            alias = self.database.get_alias(
                word
            )

            if alias:

                application = (
                    self.database.get_application(
                        alias[0]
                    )
                )

                if application:

                    return application[1]

        # ---------------------------------
        # Fuzzy Match
        # ---------------------------------

        best_match = process.extractOne(

            text,

            applications.keys(),

            scorer=fuzz.token_set_ratio

        )

        if best_match:

            app_name, score, _ = best_match

            if score >= 75:

                print(

                    f"Application Match : "

                    f"{app_name} ({score:.1f}%)"

                )

                return applications[app_name]

        return None

    # --------------------------------------------------
    # Extract Folder
    # --------------------------------------------------

    def extract_folder(
        self,
        text
    ):
        """
        Extract folder name from voice command.

        Supports:

            create folder as Trot Test
            create a folder as Trot Test
            create the folder as Trot Test
            create your folder as Trot Test

            create folder named Trot Test
            create a folder named Trot Test
            create the folder named Trot Test

            create folder called Trot Test
            create a folder called Trot Test
            create the folder called Trot Test

            make folder Trot Test
            make a folder Trot Test
            make the folder Trot Test

            new folder Trot Test
            new a folder Trot Test
            new the folder Trot Test

        Also supports existing special folders:

            open desktop
            open documents
            open downloads
            open pictures
            open videos
            open music
            open recycle bin
            open this pc
        """

        if not text:

            return None

        # ---------------------------------
        # Normalize STT text
        # ---------------------------------

        text = self.normalize_text(
            text
        )

        if not text:

            return None

        # Remove trailing punctuation.
        text = text.strip().rstrip(
            ".,!?;:"
        )

        # ==================================================
        # USER-CREATED FOLDER COMMANDS
        # ==================================================

        create_patterns = (

            # create
            "create the folder",
            "create a folder",
            "create your folder",
            "create folder",

            # make
            "make the folder",
            "make a folder",
            "make your folder",
            "make folder",

            # new
            "new the folder",
            "new a folder",
            "new your folder",
            "new folder",

            # directory
            "create the directory",
            "create a directory",
            "create directory",

            "make the directory",
            "make a directory",
            "make directory",

        )

        folder_name = text

        # ---------------------------------
        # Remove command phrase
        #
        # IMPORTANT:
        # Longest phrases are checked first.
        # ---------------------------------

        for pattern in create_patterns:

            if folder_name.startswith(
                pattern
            ):

                folder_name = folder_name[
                    len(pattern):
                ].strip()

                break

        # ==================================================
        # REMOVE NAMING CONNECTORS
        # ==================================================
        #
        # Examples:
        #
        # create folder as Trot Test
        # create folder named Trot Test
        # create folder called Trot Test
        # create folder with name Trot Test
        #
        # ==================================================

        naming_connectors = (

            "as ",
            "named ",
            "called ",
            "with name ",
            "with the name ",
            "name ",

        )

        for connector in naming_connectors:

            if folder_name.startswith(
                connector
            ):

                folder_name = folder_name[
                    len(connector):
                ].strip()

                break

        # ==================================================
        # REMOVE FILLER WORDS
        # ==================================================
        #
        # Handles:
        #
        # create the folder
        # create a folder
        # create my folder
        #
        # ==================================================

        filler_prefixes = (

            "the ",
            "a ",
            "an ",
            "my ",
            "your ",

        )

        changed = True

        while changed:

            changed = False

            for prefix in filler_prefixes:

                if folder_name.startswith(
                    prefix
                ):

                    folder_name = folder_name[
                        len(prefix):
                    ].strip()

                    changed = True

                    break

        # ==================================================
        # CLEAN FOLDER NAME
        # ==================================================

        folder_name = (
            folder_name
            .strip()
            .strip("\"'")
            .rstrip(".,!?;:")
            .strip()
        )

        # ==================================================
        # REMOVE TRAILING FILLER WORDS
        # ==================================================

        trailing_words = (

            "please",
            "please da",
            "please dee",
            "please di",

        )

        for word in trailing_words:

            if folder_name.lower().endswith(
                " " + word
            ):

                folder_name = (
                    folder_name[
                        :-(len(word) + 1)
                    ]
                    .strip()
                )

        # ==================================================
        # RETURN USER-CREATED FOLDER NAME
        # ==================================================

        if folder_name:

            invalid_names = {

                "folder",
                "directory",
                "new",
                "create",
                "make",
                "the",
                "a",
                "an",
                "my",
                "your",

            }

            if folder_name.lower() not in (
                invalid_names
            ):

                return folder_name

        # ==================================================
        # SPECIAL FOLDER DETECTION
        # ==================================================

        for folder in self.special_folders:

            if folder in text:

                return folder

        # ==================================================
        # FUZZY MATCH FOR SPECIAL FOLDERS
        # ==================================================

        best_match = process.extractOne(

            text,

            self.special_folders,

            scorer=fuzz.partial_ratio

        )

        if best_match:

            folder, score, _ = best_match

            if score >= 75:

                print(
                    f"Folder Match : "
                    f"{folder} "
                    f"({score:.1f}%)"
                )

                return folder

        return None

    # --------------------------------------------------
    # Extract Website
    # --------------------------------------------------

    def extract_website(
        self,
        text
    ):
        """
        Extract website from command.
        """

        if not text:

            return None

        text = self.normalize_text(text)

        # Exact Match

        aliases = {

            "youtube": ("youtube", "youtube la", "youtube le"),
            "google": ("google", "google la", "google le"),
            "gmail": ("gmail", "gmail la"),
            "github": ("github", "github la"),
            "instagram": ("instagram", "instagram la"),
            "facebook": ("facebook", "facebook la"),
        }

        for key, values in aliases.items():

            if any(v in text for v in values):

                return self.websites[key]

            # Don't treat browser launch
            # as website open.

        for name, url in self.websites.items():

            if (

                f"open {name}" in text

                and

                "chrome" not in text

                and

                "edge" not in text

                and

                "browser" not in text

            ):

                return url

            if f"{name} website" in text:

                return url

            if text == name:

                return url

        # URL Detection

        words = text.split()

        valid_domains = {

            "com",

            "org",

            "net",

            "in",

            "io",

            "edu",

            "gov"

        }

        for word in words:

            word = word.strip(".,!?")

            if "." not in word:

                continue

            extension = word.split(".")[-1]

            if extension in valid_domains:

                return word

        # Fuzzy Match

        best_match = process.extractOne(

            text,

            self.websites.keys(),

            scorer=fuzz.partial_ratio

        )

        if best_match:

            name, score, _ = best_match

            if score >= 75:

                print(

                    f"Website Match : "

                    f"{name} ({score:.1f}%)"

                )

                return self.websites[name]

        return None

    # --------------------------------------------------
    # Extract Google Search Query
    # --------------------------------------------------

    def extract_search_query(
        self,
        text
    ):
        """
        Extract Google search query.
        """

        if not text:

            return None

        text = self.normalize_text(text)

        remove_words = {

            "search",

            "searching",

            "google",

            "for",

            "on",

            "please",

            "chrome",

            "edge",

            "find",

            "show",

            "open",

            "look",

            "lookup",

            "website"

        }

        words = [

            word

            for word in text.split()

            if word not in remove_words

        ]

        query = " ".join(words).strip()

        return query if query else None

    # --------------------------------------------------
    # Extract YouTube Query
    # --------------------------------------------------

    def extract_youtube_query(
        self,
        text
    ):
        """
        Extract YouTube search query.
        """

        if not text:

            return None

        text = self.normalize_text(text)

        remove_words = {

            "play",

            "search",

            "youtube",

            "video",

            "song",

            "music",

            "official",

            "audio",

            "lyrical",

            "on",

            "in",

            "please"
        }

        words = [

            word

            for word in text.split()

            if word not in remove_words

        ]

        query = " ".join(words).strip()

        return query if query else None

    # --------------------------------------------------
    # Extract Browser
    # --------------------------------------------------

    def extract_browser(
        self,
        text
    ):
        """
        Detect browser name.
        """

        if not text:

            return "chrome"

        text = self.normalize_text(text)

        browser_aliases = {

            "chrome": "chrome",
            "chromela": "chrome",
            "chromeu": "chrome",
            "kurom": "chrome",
            "krom": "chrome",

            "edge": "edge",
            "edgeu": "edge",
        }

        for alias, browser in browser_aliases.items():

            if alias in text:

                return browser

        return "chrome"

    # --------------------------------------------------
    # Extract Chrome Profile
    # --------------------------------------------------

    def extract_profile(
        self,
        text
    ):
        """
        Detect Chrome profile name.
        """

        if not text:

            return None

        text = self.normalize_text(text)

        # Exact Match

        for profile, chrome_profile in self.chrome_profiles.items():

            if profile in text:

                return chrome_profile

        # Fuzzy Match

        best_match = process.extractOne(

            text,

            self.chrome_profiles.keys(),

            scorer=fuzz.partial_ratio

        )

        if best_match:

            profile, score, _ = best_match

            if score >= 75:

                print(

                    f"Profile Match : "

                    f"{profile} ({score:.1f}%)"

                )

                return self.chrome_profiles[profile]

        return None

    # --------------------------------------------------
    # Extract File Query
    # --------------------------------------------------

    def extract_file_query(
        self,
        text
    ):
        """
        Extract filename from voice command.

        Supports:

            create file demo
            create a file demo
            create a test file demo
            create a new file demo
            make file sample
            make a file sample
            new file resume

        Also supports existing file operations:

            open file resume
            delete file resume
            rename file resume
            copy file resume to desktop
            move file resume to documents
            compress file resume
            extract zip demo
        """

        if not text:

            return None

        # ---------------------------------
        # Normalize STT text
        # ---------------------------------

        text = self.normalize_text(
            text
        )

        if not text:

            return None

        # ---------------------------------
        # Remove punctuation
        # ---------------------------------

        text = (
            text
            .strip()
            .strip("\"'")
            .rstrip(".,!?;:")
            .strip()
        )

        # ==================================================
        # CREATE FILE COMMAND
        # ==================================================
        #
        # CREATE HAS PRIORITY OVER APPLICATION NAME MATCHING.
        #
        # Whatever filename Whisper/entity extraction produces here
        # belongs to the create-file operation. It must not be resolved
        # as an existing application/file before this point.
        #
        # Examples:
        #
        # create file demo
        # create a file demo
        # create a test file demo
        # create a new file demo
        # make file sample
        # make a file sample
        # new file resume
        #
        # IMPORTANT:
        # "test" is NOT removed because it may be
        # part of the actual filename.
        # ==================================================

        create_prefixes = (

            "create a ",
            "create an ",
            "create the ",
            "create my ",
            "create your ",
            "create ",

            "make a ",
            "make an ",
            "make the ",
            "make my ",
            "make your ",
            "make ",

            "new a ",
            "new an ",
            "new the ",
            "new my ",
            "new your ",
            "new ",

        )

        create_text = text

        for prefix in create_prefixes:

            if create_text.startswith(prefix):

                create_text = create_text[
                    len(prefix):
                ].strip()

                break

        # ---------------------------------
        # Remove naming connectors
        #
        # Example:
        #   create a file as demo test
        #   create file named demo test
        #   create file called demo test
        # ---------------------------------

        for connector in (
            "as ",
            "named ",
            "called ",
            "with name ",
            "with the name ",
            "name ",
        ):
            if create_text.startswith(connector):
                create_text = create_text[len(connector):].strip()
                break

        # ---------------------------------
        # Remove "file" from create command
        # ---------------------------------

        if "file" in create_text.split():

            words = create_text.split()

            file_index = words.index(
                "file"
            )

            # Everything after "file" is
            # considered the filename.
            #
            # Example:
            # create a test file demo
            #
            # after removing prefix:
            # test file demo
            #
            # filename:
            # demo

            if file_index < len(words) - 1:

                query = " ".join(
                    words[file_index + 1:]
                )

                query = (
                    query
                    .strip()
                    .strip("\"'")
                    .rstrip(".,!?;:")
                    .strip()
                )

                if query:

                    return query

        # ==================================================
        # GENERAL FILE COMMANDS
        # ==================================================

        remove_words = {

            "open",

            "file",

            "files",

            "document",

            "documents",

            "folder",

            "create",

            "make",

            "new",

            "rename",

            "delete",

            "move",

            "copy",

            "compress",

            "zip",

            "extract",

            "archive",

            "unzip",

            "please",

            "my",

            "the",

            "a",

            "an",

            "your",

            "named",

            "called",

            "to",

            "into",

            "in",

            "from",

            "using",

            "with",

            "browser",

            "chrome",

            "edge",

            "find",

            "search",

            "show",

            "locate",

            "by",

            "name"

        }

        words = [

            word

            for word in text.split()

            if word not in remove_words

        ]

        # ---------------------------------
        # Handle "2" -> "to"
        # ---------------------------------

        if "2" in words:

            words = [

                "to"
                if word == "2"
                else word

                for word in words

            ]

        # ---------------------------------
        # Build filename
        # ---------------------------------

        query = " ".join(
            words
        ).strip()

        # ---------------------------------
        # Remove punctuation
        # ---------------------------------

        query = (
            query
            .strip("\"'")
            .rstrip(".,!?;:")
            .strip()
        )

        if not query:

            return None

        return query

    # --------------------------------------------------
    # Extract Search Keyword
    # --------------------------------------------------

    def extract_search_keyword(
        self,
        text
    ):
        """
        Extract keyword from
        search command.

        Examples
        --------
        search python tutorial

        find resume

        show invoice

        Returns
        -------
        str | None
        """

        if not text:

            return None

        text = self.normalize_text(text)

        remove_words = {

            "find",

            "search",

            "searching",

            "show",

            "locate",

            "where",

            "is",

            "open",

            "file",

            "files",

            "please",

            "the",

            "my"

        }

        words = [

            word

            for word in text.split()

            if word not in remove_words

        ]

        keyword = " ".join(words).strip()

        if not keyword:

            return None

        return keyword

    # --------------------------------------------------
    # Extract Search Result Index
    # --------------------------------------------------

    def extract_result_index(
        self,
        text
    ):
        """
        Extract file result number.

        Example
        -------
        open first file

        delete second file

        copy third file
        """

        if not text:

            return None

        text = text.lower()

        mapping = {

            "first":0,

            "1st":0,

            "one":0,

            "second":1,

            "2nd":1,

            "two":1,

            "third":2,

            "3rd":2,

            "three":2,

            "fourth":3,

            "4th":3,

            "fifth":4,

            "5th":4,

            "last":-1

        }

        for word, index in mapping.items():

            if word in text:

                return index

        return None

    # --------------------------------------------------
    # Extract Rename File
    # --------------------------------------------------

    def extract_rename_file(
        self,
        text
    ):
        """
        Extract old and new filename.

        Supports:
            rename notes to project
            rename notes 2 project
            rename astra file 2 astra demo
            rename astra file to astra demo
            rename a file notes to project
            rename the file notes into project

        Returns
        -------
        dict | None
        """

        if not text:
            return None

        text = self.normalize_text(text)

        text = (
            text
            .strip()
            .strip("\"'")
            .rstrip(".,!?;:")
            .strip()
        )

        # Remove command/filler words without removing the actual
        # filename words.
        words = text.split()

        removable_prefixes = (
            "rename",
        )

        if words and words[0] in removable_prefixes:
            words = words[1:]

        while words and words[0] in {
            "a",
            "an",
            "the",
            "my",
            "your",
            "file",
            "document",
        }:
            words.pop(0)

        # "rename astra file 2 astra demo" may normalize 2 -> to.
        if "to" not in words and "into" not in words:
            if "2" in words:
                words = [
                    "to" if word == "2" else word
                    for word in words
                ]

        separator = None

        if "to" in words:
            separator = "to"
        elif "into" in words:
            separator = "into"

        if separator is None:
            return None

        index = words.index(separator)

        old_words = words[:index]
        new_words = words[index + 1:]

        # Remove "file/document" only when it is acting as a command
        # connector, not as part of the actual filename.
        old_words = [
            word
            for word in old_words
            if word not in {"file", "document"}
        ]

        new_words = [
            word
            for word in new_words
            if word not in {"file", "document"}
        ]

        old_name = " ".join(old_words).strip().rstrip(".,!?;:")
        new_name = " ".join(new_words).strip().rstrip(".,!?;:")

        if not old_name or not new_name:
            return None

        return {
            "old_name": old_name,
            "new_name": new_name
        }

    # --------------------------------------------------
    # Extract Copy File
    # --------------------------------------------------

    def extract_copy_file(
        self,
        text
    ):
        """
        Extract filename and destination.

        Supports:
            copy report to desktop
            copy astra test to desktop
            copy file resume to documents
            copy resume into documents
            copy report 2 desktop

        Returns
        -------
        dict | None
        """

        if not text:
            return None

        text = self.normalize_text(text)

        text = (
            text
            .strip()
            .strip("\"'")
            .rstrip(".,!?;:")
            .strip()
        )

        words = text.split()

        if words and words[0] == "copy":
            words = words[1:]

        while words and words[0] in {
            "a",
            "an",
            "the",
            "my",
            "your",
        }:
            words.pop(0)

        if "2" in words and "to" not in words and "into" not in words:
            words = [
                "to" if word == "2" else word
                for word in words
            ]

        separator = None

        if "to" in words:
            separator = "to"
        elif "into" in words:
            separator = "into"

        if separator is None:
            return None

        index = words.index(separator)

        filename_words = words[:index]
        destination_words = words[index + 1:]

        if filename_words and filename_words[0] in {
            "file",
            "document",
        }:
            filename_words = filename_words[1:]

        filename = " ".join(filename_words).strip()
        destination = " ".join(destination_words).strip()

        filename = filename.rstrip(".,!?;:")
        destination = destination.rstrip(".,!?;:")

        if not filename or not destination:
            return None

        return {
            "filename": filename,
            "destination": destination
        }

    # --------------------------------------------------
    # Extract Move File
    # --------------------------------------------------

    def extract_move_file(
        self,
        text
    ):
        """
        Extract filename and destination.

        Supports:
            move report to desktop
            move astra test to desktop
            move file resume to documents
            move resume into documents
            move report 2 desktop

        Returns
        -------
        dict | None
        """

        if not text:
            return None

        text = self.normalize_text(text)

        text = (
            text
            .strip()
            .strip("\"'")
            .rstrip(".,!?;:")
            .strip()
        )

        words = text.split()

        if words and words[0] == "move":
            words = words[1:]

        while words and words[0] in {
            "a",
            "an",
            "the",
            "my",
            "your",
        }:
            words.pop(0)

        if "2" in words and "to" not in words and "into" not in words:
            words = [
                "to" if word == "2" else word
                for word in words
            ]

        separator = None

        if "to" in words:
            separator = "to"
        elif "into" in words:
            separator = "into"

        if separator is None:
            return None

        index = words.index(separator)

        filename_words = words[:index]
        destination_words = words[index + 1:]

        if filename_words and filename_words[0] in {
            "file",
            "document",
        }:
            filename_words = filename_words[1:]

        filename = " ".join(filename_words).strip()
        destination = " ".join(destination_words).strip()

        filename = filename.rstrip(".,!?;:")
        destination = destination.rstrip(".,!?;:")

        if not filename or not destination:
            return None

        return {
            "filename": filename,
            "destination": destination
        }

    # --------------------------------------------------
    # Extract Rename Folder
    # --------------------------------------------------

    def extract_rename_folder(
        self,
        text
    ):
        """
        Extract old and new folder names.

        Supports:

            rename folder test to demo
            rename folder test into demo
            rename test folder to demo
            rename test 2 demo

        Important:
            Numeric "2" can be part of the folder name.

        Examples:

            rename folder test 2 demo

            becomes:

            old_name = "test 2"
            new_name = "demo"
        """

        if not text:

            return None

        text = self.normalize_text(
            text
        )

        text = (
            text
            .strip()
            .strip("\"'")
            .rstrip(".,!?;:")
            .strip()
        )

        if not text:

            return None

        words = text.split()

        # ---------------------------------------------
        # Remove rename command
        # ---------------------------------------------

        if words and words[0] == "rename":

            words = words[1:]

        # ---------------------------------------------
        # Remove leading filler words
        # ---------------------------------------------

        while words and words[0] in {

            "a",
            "an",
            "the",
            "my",
            "your",
            "folder",
            "directory",

        }:

            words.pop(0)

        if not words:

            return None

        # ---------------------------------------------
        # Explicit separator
        #
        # rename folder test 2 to demo
        #
        # Here "2" is part of old folder name.
        # ---------------------------------------------

        separator = None

        if "to" in words:

            separator = "to"

        elif "into" in words:

            separator = "into"

        # ---------------------------------------------
        # Normal explicit command
        # ---------------------------------------------

        if separator is not None:

            index = words.index(
                separator
            )

            old_words = words[:index]

            new_words = words[
                index + 1:
            ]

        else:

            # -----------------------------------------
            # STT fallback
            #
            # Example:
            #
            # rename folder test 2 demo
            #
            # We MUST NOT treat "2" as "to".
            #
            # Therefore:
            #
            # old folder = test 2
            # new folder = demo
            #
            # Last word becomes the new folder name.
            # -----------------------------------------

            if len(words) < 2:

                return None

            old_words = words[:-1]

            new_words = words[-1:]

        # ---------------------------------------------
        # Remove folder/directory connector words
        # ---------------------------------------------

        old_words = [

            word

            for word in old_words

            if word not in {
                "folder",
                "directory",
            }

        ]

        new_words = [

            word

            for word in new_words

            if word not in {
                "folder",
                "directory",
            }

        ]

        old_name = (
            " ".join(old_words)
            .strip()
            .strip("\"'")
            .rstrip(".,!?;:")
            .strip()
        )

        new_name = (
            " ".join(new_words)
            .strip()
            .strip("\"'")
            .rstrip(".,!?;:")
            .strip()
        )

        if not old_name:

            return None

        if not new_name:

            return None

        print(
            "\n========== FOLDER RENAME ENTITY =========="
        )

        print(
            f"Old Folder : {old_name}"
        )

        print(
            f"New Folder : {new_name}"
        )

        print(
            "==========================================\n"
        )

        return {

            "old_name": old_name,

            "new_name": new_name,

            # Compatibility keys
            "source": old_name,

            "folder": old_name,

            "destination_name": new_name,

        }


    # --------------------------------------------------
    # Extract Copy Folder
    # --------------------------------------------------

    def extract_copy_folder(
        self,
        text
    ):
        """
        Extract folder name and destination.

        Supports:

            copy folder project to desktop
            copy project folder to desktop
            copy the project folder into documents
            copy folder project 2 desktop
        """

        if not text:
            return None

        text = self.normalize_text(text)

        text = (
            text
            .strip()
            .strip("\"'")
            .rstrip(".,!?;:")
            .strip()
        )

        words = text.split()

        # Remove copy
        if words and words[0] == "copy":
            words = words[1:]

        # Remove leading fillers
        while words and words[0] in {
            "a",
            "an",
            "the",
            "my",
            "your",
        }:
            words.pop(0)

        # ---------------------------------------------
        # STT fallback
        #
        # "2" is treated as "to" ONLY when there is
        # no explicit separator.
        #
        # Example:
        #
        # copy folder project 2 desktop
        #
        # -> project to desktop
        #
        # Numeric folder names remain supported when
        # an explicit "to"/"into" separator exists.
        # ---------------------------------------------

        if "to" not in words and "into" not in words:

            if "2" in words:

                index = words.index("2")

                # Only treat "2" as the separator if
                # something exists after it.

                if index < len(words) - 1:

                    words[index] = "to"

        separator = None

        if "to" in words:
            separator = "to"

        elif "into" in words:
            separator = "into"

        if separator is None:
            return None

        index = words.index(separator)

        folder_words = words[:index]
        destination_words = words[index + 1:]

        # Remove folder/directory words
        folder_words = [
            word
            for word in folder_words
            if word not in {
                "folder",
                "directory",
            }
        ]

        destination_words = [
            word
            for word in destination_words
            if word not in {
                "folder",
                "directory",
            }
        ]

        folder_name = " ".join(
            folder_words
        ).strip()

        destination = " ".join(
            destination_words
        ).strip()

        folder_name = folder_name.rstrip(
            ".,!?;:"
        )

        destination = destination.rstrip(
            ".,!?;:"
        )

        if not folder_name or not destination:
            return None

        return {
            "foldername": folder_name,
            "destination": destination
        }


    # --------------------------------------------------
    # Extract Move Folder
    # --------------------------------------------------

    def extract_move_folder(
        self,
        text
    ):
        """
        Extract folder name and destination.

        Supports:

            move folder project to desktop
            move project folder to documents
            move folder project into downloads
            move project folder 2 desktop
        """

        if not text:
            return None

        text = self.normalize_text(text)

        text = (
            text
            .strip()
            .strip("\"'")
            .rstrip(".,!?;:")
            .strip()
        )

        words = text.split()

        # Remove move
        if words and words[0] == "move":
            words = words[1:]

        # Remove leading fillers
        while words and words[0] in {
            "a",
            "an",
            "the",
            "my",
            "your",
        }:
            words.pop(0)

        # ---------------------------------------------
        # STT fallback
        #
        # move folder project 2 desktop
        #
        # -> project to desktop
        # ---------------------------------------------

        if "to" not in words and "into" not in words:

            if "2" in words:

                index = words.index("2")

                if index < len(words) - 1:

                    words[index] = "to"

        separator = None

        if "to" in words:
            separator = "to"

        elif "into" in words:
            separator = "into"

        if separator is None:
            return None

        index = words.index(separator)

        folder_words = words[:index]
        destination_words = words[index + 1:]

        # Remove folder/directory words
        folder_words = [
            word
            for word in folder_words
            if word not in {
                "folder",
                "directory",
            }
        ]

        destination_words = [
            word
            for word in destination_words
            if word not in {
                "folder",
                "directory",
            }
        ]

        folder_name = " ".join(
            folder_words
        ).strip()

        destination = " ".join(
            destination_words
        ).strip()

        folder_name = folder_name.rstrip(
            ".,!?;:"
        )

        destination = destination.rstrip(
            ".,!?;:"
        )

        if not folder_name or not destination:
            return None

        return {
            "foldername": folder_name,
            "destination": destination
        }


    # --------------------------------------------------
    # Extract Delete Folder
    # --------------------------------------------------

    def extract_delete_folder(
        self,
        text
    ):
        """
        Extract folder name.

        Supports:

            delete folder project
            delete the project folder
            remove folder project
            remove project folder
        """

        if not text:
            return None

        text = self.normalize_text(text)

        text = (
            text
            .strip()
            .strip("\"'")
            .rstrip(".,!?;:")
            .strip()
        )

        words = text.split()

        # Remove command
        if words and words[0] in {
            "delete",
            "remove",
        }:
            words = words[1:]

        # Remove fillers
        while words and words[0] in {
            "a",
            "an",
            "the",
            "my",
            "your",
        }:
            words.pop(0)

        # Remove folder/directory keyword
        words = [
            word
            for word in words
            if word not in {
                "folder",
                "directory",
            }
        ]

        folder_name = " ".join(
            words
        ).strip()

        folder_name = folder_name.rstrip(
            ".,!?;:"
        )

        if not folder_name:
            return None

        return folder_name

    # --------------------------------------------------
    # Extract Compress File
    # --------------------------------------------------

    def extract_compress_file(
        self,
        text
    ):
        """
        Extract filename for ZIP.
        """

        return self.extract_file_query(
            text
        )

    # --------------------------------------------------
    # Extract Extract ZIP
    # --------------------------------------------------

    def extract_extract_zip(
        self,
        text
    ):
        """
        Extract ZIP filename.
        """

        return self.extract_file_query(
            text
        )

    # --------------------------------------------------
    # Extract Search Extension
    # --------------------------------------------------

    def extract_search_extension(
        self,
        text
    ):
        """
        Extract file extension.

        Example
        -------
        search pdf files
        find txt files

        Returns
        -------
        str | None
        """

        if not text:

            return None

        extensions = {

            "txt",

            "text",

            "pdf",

            "doc",

            "docx",

            "word",

            "ppt",

            "pptx",

            "powerpoint",

            "xls",

            "xlsx",

            "excel",

            "csv",

            "png",

            "jpg",

            "jpeg",

            "gif",

            "zip",

            "mp3",

            "wav",

            "mp4",

            "avi",

            "py",

            "bmp",

            "webp",

            "mov",

            "mkv",

            "flac",

            "aac",

            "json",

            "xml"

        }

        text = self.normalize_text(text)

        words = text.split()

        for word in words:

            word = word.replace(".", "")

            mapping = {

                "text":"txt",

                "texts":"txt",

                "word":"docx",

                "words":"docx",

                "document":"docx",

                "documents":"docx",

                "excel":"xlsx",

                "excels":"xlsx",

                "spreadsheet":"xlsx",

                "powerpoint":"pptx",

                "presentation":"pptx",

                "presentations":"pptx",

                "image":"jpg",

                "images":"jpg",

                "photo":"jpg",

                "photos":"jpg",

                "video":"mp4",

                "videos":"mp4",

                "audio":"mp3",

                "audios":"mp3",

                "jpd":"pdf",

                "pdf file":"pdf",

                "pdf files":"pdf",

                "word file":"docx",

                "excel file":"xlsx",

                "ppt":"pptx",

                "ppt file":"pptx",

                "zip file":"zip",

                "text file":"txt",

                "jpeg image":"jpg",

                "png image":"png",

                "python":"py",

                "python file":"py",

                "json file":"json",

                "xml file":"xml",

                "audio file":"mp3",

                "video file":"mp4",

                "document":"docx",

                "documents":"docx",

                "spreadsheet":"xlsx",

                "presentation":"pptx",

                "presentations":"pptx",

                "movie":"mp4",

                "movies":"mp4",

                "songs":"mp3",

                "music":"mp3",

                "pictures":"jpg",

                "photos":"jpg"

            }

            if word in mapping:

                return mapping[word]

            if word in extensions:

                return word

        return None

    # --------------------------------------------------
    # Extract Search Size
    # --------------------------------------------------

    def extract_search_size(
        self,
        text
    ):
        """
        Extract minimum file size in MB.

        Example
        -------
        files larger than 100 mb

        Returns
        -------
        int | None
        """

        if not text:

            return None

        words = text.lower().split()

        for word in words:

            if word.isdigit():

                return int(word)

        return None
    
    # --------------------------------------------------
    # Extract Search Date
    # --------------------------------------------------

    def extract_search_date(
        self,
        text
    ):
        """
        Extract search period.

        Returns
        -------
        int
        """

        if not text:

            return None

        text = text.lower()

        if "this week" in text:

            return 7

        if "this month" in text:

            return 30

        if "this year" in text:

            return 365

        if "today" in text:

            return 0

        if "yesterday" in text:

            return 1

        if "last week" in text:

            return 7

        if "last month" in text:

            return 30

        if "recent" in text:

            return 7

        words = text.split()

        for word in words:

            if word.isdigit():

                return int(word)

        return None

    # --------------------------------------------------
    # Extract Percentage
    # --------------------------------------------------

    def extract_percentage(
        self,
        text
    ):
        """
        Extract volume or brightness percentage.

        Supports commands such as:

        set volume to 50
        set volume 50
        volume at 50
        volume 50 percent
        volume 50%

        set brightness to 70
        set brightness 70
        brightness at 70
        brightness 70 percent
        brightness 70%

        Returns
        -------
        int | None
            Value from 0 to 100.
        """

        if not text:

            return None

        import re

        text = self.normalize_text(text)

        # ---------------------------------
        # Explicit Percentage
        # ---------------------------------

        match = re.search(

            r"\b(\d{1,3})\s*"
            r"(?:%|percent|percentage)\b",

            text

        )

        if match:

            value = int(
                match.group(1)
            )

            if 0 <= value <= 100:

                return value

            return None

        # ---------------------------------
        # "to 50"
        # "at 50"
        # "level 50"
        # ---------------------------------

        match = re.search(

            r"\b(?:to|at|level)\s+"
            r"(\d{1,3})\b",

            text

        )

        if match:

            value = int(
                match.group(1)
            )

            if 0 <= value <= 100:

                return value

            return None

        # ---------------------------------
        # Direct Value
        #
        # "set volume 50"
        # "set brightness 10"
        # "volume 70"
        # "brightness 80"
        # ---------------------------------

        match = re.search(

            r"\b(?:volume|brightness)"
            r"(?:\s+(?:to|at|level))?"
            r"\s+(\d{1,3})\b",

            text

        )

        if match:

            value = int(
                match.group(1)
            )

            if 0 <= value <= 100:

                return value

            return None

        return None

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close(self):
        """
        Close database connection.
        """

        self.database.close()