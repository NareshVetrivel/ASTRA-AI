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

        "windows",

        "program files",

        "programdata",

        "steam",

        "steamapps",

        "epic",

        "riot",

        "valorant",

        "minecraft",

        "origin",

        "ubisoft",

        "rockstar",

        "fitgirl",

        "dodi",

        "repack",

        "game",

        "games",

        "assets",

        "resource",

        "resources",

        "cache",

        "temp",

        "tmp",

        "node_modules",

        ".venv",

        "__pycache__",

        ".git",

        ".idea",

        ".vscode",

        # Game Engines

        "age of empires",
        "ageofempires",

        "gta",
        "counter strike",
        "csgo",
        "dota",
        "pubg",

        # Installers

        "crack",
        "trainer",
        "mods",
        "mod",

        # Assets

        "audio",
        "video",
        "movies",
        "movie",

        "voice",
        "voices",

        "cutscene",
        "cutscenes",

        "soundtrack",
        "soundtracks",

        "sfx",

        "wav",

        "bgm",

        "textures",

        "sprites",

        "models",

        "movies",

        # IDE

        "android",
        "gradle",
        ".gradle",

        # Python

        "site-packages",

        "eula",

        "intro",

        "outro",

        "theme",

        "ambient",

        "battle",

        "wind",

        "rain",

        "thunder",

        "missile",

        "tank",

        "heli",

        "helicopter",

        "train",

        "truck",

        "plane",

        "bird",

        "machinery",

        "base",

        "engine",

        "voice",

        "sound",

        "effect",

        "texture",

        "sprite",

        "shader",

        "movie",

        "cut",

        "menu"

    }

    # ----------------------------------
    # File Size Limits
    # ----------------------------------

    MINIMUM_SIZE = 20 * 1024

    MAXIMUM_SIZE = 2 * 1024 * 1024 * 1024

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

        if any(

            folder in parent_folder

            for folder

            in cls.IGNORE_FOLDER_KEYWORDS

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