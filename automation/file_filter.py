"""
File Filter Module

Determines whether a file
should be indexed into the
ASTRA-AI database.

ASTRA-AI V1
"""

import re
from pathlib import Path


class FileFilter:
    """
    Smart File Filter.
    """

    # ----------------------------------
    # Allowed Extensions
    # ----------------------------------

    ALLOWED_EXTENSIONS = {

        # Documents

        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",

        # Office

        ".ppt",
        ".pptx",

        ".xls",
        ".xlsx",

        # Images

        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".gif",
        ".webp",

        # Videos

        ".mp4",
        ".mkv",
        ".avi",
        ".mov",

        # Audio

        ".mp3",
        ".wav",
        ".flac",

        # Archives

        ".zip",
        ".rar",
        ".7z"

    }

    # ----------------------------------
    # Ignore Extensions
    # ----------------------------------

    IGNORE_EXTENSIONS = {

        ".py",
        ".pyc",
        ".pyo",

        ".java",
        ".class",
        ".jar",

        ".c",
        ".cpp",
        ".h",

        ".cs",

        ".html",
        ".css",
        ".js",
        ".json",
        ".xml",

        ".exe",
        ".dll",
        ".sys",
        ".bat",
        ".cmd",
        ".msi",

        ".db",
        ".sqlite",
        ".sqlite3",

        ".ini",
        ".cab",
        ".drv",
        ".mui",

        ".iso",
        ".img",
        ".bin",

        ".log",
        ".tmp",
        ".cache"

    }

    # ----------------------------------
    # Ignore Files
    # ----------------------------------

    IGNORE_FILES = {

        "desktop.ini",

        "thumbs.db",

        ".ds_store",

        "autorun.inf"

    }

    # ----------------------------------
    # Ignore Keywords
    # ----------------------------------

    IGNORE_KEYWORDS = {

        "readme",
        "license",
        "copying",
        "setup",
        "install",
        "uninstall",
        "password",
        "serial",
        "keygen",

        "sample",
        "demo",
        "example",
        "backup",
        "old",
        "copy"

    }

    # ----------------------------------
    # Ignore Folder Keywords
    # ----------------------------------

    IGNORE_FOLDER_KEYWORDS = {

        # -----------------------------
        # Windows System
        # -----------------------------

        "windows",
        "program files",
        "program files (x86)",
        "programdata",
        "$recycle.bin",
        "system volume information",
        "recovery",
        "boot",

        # -----------------------------
        # Python
        # -----------------------------

        ".venv",
        "venv",
        "__pycache__",
        "site-packages",
        ".pytest_cache",
        ".mypy_cache",

        # -----------------------------
        # Git / IDE
        # -----------------------------

        ".git",
        ".github",
        ".idea",
        ".vscode",
        ".vs",

        # -----------------------------
        # Build
        # -----------------------------

        "build",
        "dist",
        "debug",
        "release",
        "obj",
        "bin",
        "target",

        # -----------------------------
        # Node
        # -----------------------------

        "node_modules",
        ".next",
        ".nuxt",

        # -----------------------------
        # Cache
        # -----------------------------

        "cache",
        "temp",
        "tmp",
        "logs",
        "log",
        "shadercache",

        # -----------------------------
        # NVIDIA / AMD
        # -----------------------------

        "nvidia",
        "amd",
        "intel",

        # -----------------------------
        # Game Launchers
        # -----------------------------

        "steam",
        "steamapps",
        "epic",
        "epic games",
        "riot",
        "riot games",
        "origin",
        "ubisoft",
        "rockstar",
        "ea games",
        "battle.net",

        # -----------------------------
        # Android
        # -----------------------------

        "android",
        "gradle",
        ".gradle",

        # -----------------------------
        # Unreal / Unity
        # -----------------------------

        "unity",
        "unityhub",
        "unreal",
        "unreal engine",

        # -----------------------------
        # Assets
        # -----------------------------

        "assets",
        "resource",
        "resources",
        "textures",
        "texture",
        "sprites",
        "models",
        "animations",
        "animation",
        "movies",
        "movie",
        "cutscene",
        "cutscenes",
        "soundtrack",
        "music",
        "voice",
        "voices",
        "audio",
        "video",
        "videos",
        "shader",
        "shaders",
        "effects",
        "effect",
        "ambient",

        # -----------------------------
        # Large Game Content
        # -----------------------------

        "games",
        "game",
        "mods",
        "mod",
        "crack",
        "trainer",
        "fitgirl",
        "dodi"

    }

    # ----------------------------------
    # File Size Limits
    # ----------------------------------

    MINIMUM_SIZE = 20 * 1024

    MAXIMUM_SIZE = 2 * 1024 * 1024 * 1024

    # ----------------------------------
    # Skip Directory
    # ----------------------------------

    @classmethod
    def should_skip_directory(
        cls,
        directory
    ):
        """
        Return True if an entire directory
        should be skipped.
        """

        directory = str(directory).lower()

        return any(

            keyword in directory

            for keyword in cls.IGNORE_FOLDER_KEYWORDS

        )

    # ----------------------------------
    # Check Valid File
    # ----------------------------------

    @classmethod
    def is_valid_file(cls, full_path):
        """
        Return True if the file
        should be indexed.
        """

        file_path = Path(full_path)

        filename = file_path.name.lower()

        extension = file_path.suffix.lower()

        parent_folder = str(
            file_path.parent
        ).lower()

        # -----------------------------
        # Skip Windows System Folders
        # -----------------------------

        if "$recycle.bin" in parent_folder:

            return False

        if "system volume information" in parent_folder:

            return False

        if "recovery" in parent_folder:

            return False

        # -----------------------------
        # Hidden Files
        # -----------------------------

        if filename.startswith("."):

            return False

        if filename.startswith("~$"):

            return False

        # -----------------------------
        # Ignore File Names
        # -----------------------------

        if filename in cls.IGNORE_FILES:

            return False

        # -----------------------------
        # Ignore Keywords
        # -----------------------------

        if any(

            keyword in filename

            for keyword

            in cls.IGNORE_KEYWORDS

        ):

            return False

        # -----------------------------
        # Ignore Folder Keywords
        # -----------------------------

        if cls.should_skip_directory(
            parent_folder
        ):

            return False

        # -----------------------------
        # Ignore Extensions
        # -----------------------------

        if extension in cls.IGNORE_EXTENSIONS:

            return False

        # -----------------------------
        # Allowed Extensions
        # -----------------------------

        if extension not in cls.ALLOWED_EXTENSIONS:

            return False

        # -----------------------------
        # Random Filename
        # -----------------------------

        if cls.is_random_filename(

            file_path.stem

        ):

            return False

        # -----------------------------
        # File Size
        # -----------------------------

        try:

            size = file_path.stat().st_size

        except Exception:

            return False

        if size < cls.MINIMUM_SIZE:

            return False

        if size > cls.MAXIMUM_SIZE:

            return False

        # -----------------------------
        # Meaningful Filename
        # -----------------------------

        if not cls.is_meaningful_name(

            file_path.stem

        ):

            return False

        return True

    # ----------------------------------
    # Random Filename Detection
    # ----------------------------------

    @staticmethod
    def is_random_filename(name):
        """
        Detect game assets or
        meaningless filenames.
        """

        name = name.lower()

        # Very short names

        if len(name) <= 2:

            return True

        # Examples:
        #
        # b1a
        # w4g
        # tf2
        # x9
        #

        patterns = [

            r"^[a-z]\d[a-z]?$",

            r"^[a-z]{1,2}\d{1,3}$",

            r"^[a-z]{1,3}\d[a-z0-9]*$",

            r"^m\d+.*",

            r"^wave\d+$",

            r"^wind\d+$",

            r"^rain_\d+$",

            r"^thunder_\d+$",

            r"^bird_\d+$",

            r"^car_\d+$",

            r"^plane_.*",

            r"^train_.*",

            r"^missile_.*",

            r"^_cut.*",

            r"^_out.*"

        ]

        for pattern in patterns:

            if re.fullmatch(

                pattern,

                name

            ):

                return True

        return False
    
    # ----------------------------------
    # Game Asset Detection
    # ----------------------------------

    @staticmethod
    def is_game_asset(name):
        """
        Detect common game asset names.
        """

        name = name.lower()

        game_keywords = {

            "intro",
            "outro",
            "credits",
            "voice",
            "voices",
            "ambient",
            "effect",
            "effects",
            "sound",
            "sounds",
            "music",
            "theme",
            "battle",
            "mission",
            "level",
            "resource",
            "asset",
            "texture",
            "sprite",
            "engine",
            "shader",
            "terrain",
            "heli",

            "wind",

            "rain",

            "thunder",

            "truck",

            "plane",

            "car",

            "bird",

            "wave",

            "missile",

            "tank",

            "weapon",

            "gun",

            "shot",

            "explosion",

            "explo",

            "fire",

            "footstep",

            "walk",

            "run",

            "jump",

            "snow",

            "forest",

            "office",

            "factory",

            "bridge",

            "airport"

        }

        return any(

            keyword in name

            for keyword in game_keywords

        )

    # ----------------------------------
    # Too Many Numbers
    # ----------------------------------

    @staticmethod
    def has_too_many_numbers(name):
        """
        Ignore filenames that are
        mostly numbers.
        """

        digits = sum(

            character.isdigit()

            for character in name

        )

        return digits >= 5

    # ----------------------------------
    # Repeated Characters
    # ----------------------------------

    @staticmethod
    def has_repeated_characters(name):
        """
        Detect filenames like
        aaaaaaaa.txt
        """

        if len(name) < 6:

            return False

        return len(set(name)) <= 2

    # ----------------------------------
    # Meaningful Filename
    # ----------------------------------

    @classmethod
    def is_meaningful_name(
        cls,
        name
    ):
        """
        Return True if filename
        looks meaningful.
        """

        name = name.lower()

        if cls.is_random_filename(name):

            return False

        if cls.is_game_asset(name):

            return False

        if cls.has_too_many_numbers(name):

            return False

        if cls.has_repeated_characters(name):

            return False

        return True