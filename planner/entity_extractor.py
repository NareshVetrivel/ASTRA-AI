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

            " 2 ": " to ",

            " too ": " to ",

            " in to ": " into ",

            " jpd ": " pdf ",

            " p d f ": " pdf ",

            " doc x ": " docx ",

            " power point ": " powerpoint ",

            " esther day ": " yesterday ",

            " yesterdaye ": " yesterday ",

            " last v ": " last week ",

            " this weak ": " this week ",

            "arch": "search",

            "herch": "search",

            "reach": "search",

            "serch": "search",

            "fined": "find",

            "fence": "files",

            "finds": "find",

            "word fence": "word files",

            "excel fence": "excel files",

            "ppt fence": "ppt files",

            "modified study": "modified today",

            "modified estaday": "modified yesterday",

            "node pad":"notepad",

            "note that":"notepad",

            "north pad":"notepad",

            "ms word":"word",

            "m s word":"word",

            "power point":"powerpoint",

            "excel sheet":"excel",

            "excel file":"excel",

            "word file":"word",

            "ppt file":"ppt",

            "reach":"search",

            "herch":"search",

            "serch":"search",

            "arch":"search",

            "fence":"files",

            "study":"today",

            "estaday":"yesterday"

        }

        for old, new in replacements.items():

            text = text.replace(old, new)

        return text.strip()

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

            print(

                f"Fuzzy Match : "

                f"{app_name} ({score:.1f}%)"

            )

            if score >= 75:

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

            print(

                f"Folder Match : "

                f"{folder} ({score:.1f}%)"

            )

            if score >= 75:

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

        for name, url in self.websites.items():

            # Don't treat browser launch
            # as website open.

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

            print(

                f"Website Match : {name} ({score:.1f}%)"

            )

            if score >= 75:

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

        text = text.lower()

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

        text = text.lower()

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

        text = text.lower()

        if "edge" in text:

            return "edge"

        if "chrome" in text:

            return "chrome"

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

        text = text.lower()

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

            print(

                f"Profile Match : {profile} ({score:.1f}%)"

            )

            if score >= 75:

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

        words = text.lower().split()

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