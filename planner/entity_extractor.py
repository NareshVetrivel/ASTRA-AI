"""
Entity Extraction Module

This module identifies application names
from the SQLite database using
RapidFuzz matching.

It also extracts file search queries
for File Finder.

ASTRA-AI V1
"""

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
            # Numbers
            # ---------------------------------

            " 2 ": " to ",
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

            text = text.replace(old, new)

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
        """

        if not text:

            return None

        text = self.normalize_text(text)

        # ---------------------------------
        # Remove Command Words
        # ---------------------------------

        command_words = {

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

        words = [

            word

            for word in text.split()

            if word not in command_words

        ]

        text = " ".join(words)

        applications = self.load_applications()

        if not applications:

            return None

        # -------------------------
        # Exact Match
        # -------------------------

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

        # -------------------------
        # Alias Match
        # -------------------------

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

        # -------------------------
        # Fuzzy Match
        # -------------------------

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
        Extract folder name from
        voice command.
        """

        if not text:

            return None

        text = self.normalize_text(text)

        # -------------------------
        # Exact Match
        # -------------------------

        for folder in self.special_folders:

            if folder in text:

                return folder

        # -------------------------
        # Fuzzy Match
        # -------------------------

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

                    f"{folder} ({score:.1f}%)"

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
        Extract filename from
        voice command.
        """

        if not text:

            return None

        text = self.normalize_text(text)

        remove_words = {

            "open",

            "file",

            "files",

            "document",

            "documents",

            "folder",

            "create",

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

            "named",

            "called",

            "called as",

            "by",

            "name"

        }

        words = [

            word

            for word in text.split()

            if word not in remove_words

        ]

        query = " ".join(words).strip()

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

        Example
        -------
        rename notes to project

        Returns
        -------
        dict | None
        """

        if not text:

            return None

        text = self.normalize_text(text)

        remove_words = {

            "rename",

            "file",

            "document",

            "please",

            "my",

            "the",

            "called",

            "named"

        }

        words = [

            word

            for word in text.split()

            if word not in remove_words

        ]

        if "2" in words:

            words = [

                "to"

                if word == "2"

                else word

                for word in words

            ]

        if "to" not in words and "into" not in words:

            return None

        separator = "to"

        if "into" in words:

            separator = "into"

        index = words.index(separator)

        old_name = (
            " ".join(
                words[:index]
            )
            .strip()
            .rstrip(".,!?")
        )

        new_name = (
            " ".join(
                words[index + 1:]
            )
            .strip()
            .rstrip(".,!?")
        )

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
        """

        if not text:

            return None

        text = self.normalize_text(text)

        remove_words = {

            "copy",

            "file",

            "document",

            "please",

            "my",

            "the"

        }

        words = [

            word

            for word in text.split()

            if word not in remove_words

        ]

        if "2" in words:

            words = [

                "to"

                if word == "2"

                else word

                for word in words

            ]

        if "to" not in words and "into" not in words:

            return None

        separator = "to"

        if "into" in words:

            separator = "into"

        index = words.index(separator)

        filename = " ".join(

            words[:index]

        ).strip()

        destination = (
            " ".join(words[index + 1:])
            .strip()
            .rstrip(".,!?")
        )

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
        """

        if not text:

            return None

        text = self.normalize_text(text)

        remove_words = {

            "move",

            "file",

            "document",

            "please",

            "my",

            "the"

        }

        words = [

            word

            for word in text.split()

            if word not in remove_words

        ]

        if "2" in words:

            words = [

                "to"

                if word == "2"

                else word

                for word in words

            ]

        if "to" not in words and "into" not in words:

            return None

        separator = "to"

        if "into" in words:

            separator = "into"

        index = words.index(separator)

        filename = " ".join(

            words[:index]

        ).strip()

        destination = (
            " ".join(words[index + 1:])
            .strip()
            .rstrip(".,!?")
        )

        if not filename or not destination:

            return None

        return {

            "filename": filename,

            "destination": destination

        }

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
    # Close
    # --------------------------------------------------

    def close(self):
        """
        Close database connection.
        """

        self.database.close()